#!/usr/bin/env python3
"""수집한 JSON을 Firebase Storage(public_content/{dataset}/latest.json)에도 올린다.

저장소를 비공개로 바꾸면 index.html이 raw.githubusercontent.com 에서 데이터를 읽을 수 없으므로,
화면은 Cloud Function(getPublicContent)을 통해 이 파일들을 읽는다(index.html의 fetchWithTimeout).
저장소 파일은 그대로 두고(스크립트의 "이전 값 유지" 로직과 변경 이력이 거기에 있다) 이 스크립트가
같은 내용을 Storage에 한 벌 더 올릴 뿐이다.

사용법:  python scripts/upload_to_storage.py <파일 또는 폴더> [...]
  · 폴더를 주면 그 안의 *.json 을 올린다(하위 폴더 제외).
  · 데이터셋 이름 규칙(index.html의 dataDatasetOf와 같다): 저장소 기준 경로에서 .json 을 떼고
    영문·숫자 이외 문자를 _ 로 바꾼다.  market/quotes.json → market_quotes
  · 내용이 이미 같으면 올리지 않는다(MD5 비교).
  · FIREBASE_SERVICE_ACCOUNT_JSON 이 없으면 아무것도 하지 않고 정상 종료한다.
  · 일부 파일이 실패해도 나머지는 계속 올리고, 하나라도 실패하면 종료 코드 1.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import sys
from pathlib import Path

BUCKET = "chicken-dx.firebasestorage.app"
ROOT = Path(__file__).resolve().parent.parent


def dataset_of(rel_path: str) -> str:
    """저장소 기준 경로 → 데이터셋 이름. index.html의 dataDatasetOf 와 같은 규칙."""
    p = re.sub(r"\.json$", "", rel_path.replace("\\", "/"))
    return re.sub(r"[^A-Za-z0-9_]", "_", p)


def collect(args: list[str]) -> list[Path]:
    out: list[Path] = []
    for a in args:
        p = (ROOT / a).resolve() if not Path(a).is_absolute() else Path(a)
        if p.is_dir():
            out.extend(sorted(x for x in p.glob("*.json") if x.is_file()))
        elif p.is_file() and p.suffix == ".json":
            out.append(p)
        else:
            print(f"건너뜀(없음/JSON 아님): {a}")
    return out


def main() -> int:
    files = collect(sys.argv[1:])
    if not files:
        print("올릴 JSON 파일이 없습니다.")
        return 0
    sa_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
    if not sa_json:
        print("FIREBASE_SERVICE_ACCOUNT_JSON 없음 — Storage 업로드를 건너뜁니다.")
        return 0

    import firebase_admin
    from firebase_admin import credentials, storage

    firebase_admin.initialize_app(credentials.Certificate(json.loads(sa_json)), {"storageBucket": BUCKET})
    bucket = storage.bucket()

    failed = 0
    for f in files:
        rel = f.relative_to(ROOT).as_posix()
        ds = dataset_of(rel)
        try:
            body = f.read_bytes()
            json.loads(body)  # 깨진 JSON을 올리지 않는다
            path = f"public_content/{ds}/latest.json"
            blob = bucket.get_blob(path)  # 없으면 None
            md5 = base64.b64encode(hashlib.md5(body).digest()).decode()
            if blob is not None and blob.md5_hash == md5:
                print(f"변경 없음  {rel}")
                continue
            blob = blob or bucket.blob(path)
            blob.cache_control = "no-cache"
            blob.upload_from_string(body, content_type="application/json")
            print(f"업로드     {rel} → public_content/{ds}/latest.json ({len(body):,} B)")
        except Exception as e:  # noqa: BLE001 — 한 파일 실패가 나머지를 막지 않게
            failed += 1
            print(f"실패       {rel}: {e}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
