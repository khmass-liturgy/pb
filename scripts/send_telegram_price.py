#!/usr/bin/env python3
"""
poultry_price/latest.json 을 텔레그램 메시지로 요약해 보낸다.

축산산지시세 탭에 실제로 뜨는 항목(계란·육계 대/중/소)만 담는다 — 양계
컨설팅용 화면이라 양돈·한우는 이미 화면에서 뺀 상태이고(2026-09 결정),
알림도 화면과 같은 범위로 맞춘다. 데이터 자체는 여전히 poultry_price에
있으니 필요해지면 이 스크립트에도 쉽게 추가할 수 있다.

표준 라이브러리(urllib)만 쓴다 — 다른 fetch 스크립트와 같은 이유로, CI에서
pip install 없이 바로 돈다.
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

PRICE_PATH = Path("poultry_price/latest.json")
LAYER_PATH = Path("layer_stats/latest.json")
API_URL_TMPL = "https://api.telegram.org/bot{token}/sendMessage"
PRODUCER_URL = "https://www.ekapepia.com/v3/web/main.do?userGroup=producer"


def won(v):
    return f"{v:,}원" if isinstance(v, int) else "-"


def build_message():
    if not PRICE_PATH.exists():
        return None, "poultry_price/latest.json 이 없습니다."
    data = json.loads(PRICE_PATH.read_text(encoding="utf-8"))

    egg = data.get("egg") or {}
    chicken = data.get("chicken") or {}
    grades = ((data.get("chicken_grades") or {}).get("items")) or {}
    stale = data.get("stale") or {}

    lines = ["🐔 오늘의 축산산지시세", ""]

    if egg.get("latest") is not None:
        d = (egg.get("rows") or [{}])[0].get("date", "")
        mark = " (이전값)" if stale.get("egg") else ""
        lines.append(f"🥚 계란(특란 XL) {won(egg['latest'])}/10개{mark} · {d}")

    if chicken.get("latest") is not None:
        d = (chicken.get("rows") or [{}])[0].get("date", "")
        mark = " (이전값)" if stale.get("chicken") else ""
        lines.append(f"🐔 육계 생계유통(대) {won(chicken['latest'])}/kg{mark} · {d}")

    # 대/중/소 중 거래가 있었던 규격만 — 화면 표시 방식과 동일
    grade_bits = []
    for key in ("large", "medium", "small"):
        g = grades.get(key) or {}
        if g.get("value") is not None:
            grade_bits.append(f"{g.get('label', key)} {won(g['value'])}({g.get('date', '')})")
    if grade_bits:
        lines.append("   ㄴ 규격별: " + " / ".join(grade_bits))

    # 산란계·육계 사육 통계(분기)도 있으면 함께 — 매일 바뀌진 않지만 참고용
    if LAYER_PATH.exists():
        try:
            ls = json.loads(LAYER_PATH.read_text(encoding="utf-8"))
            layer, broiler = ls.get("layer") or {}, ls.get("broiler") or {}
            if layer.get("birds"):
                lines.append("")
                lines.append(f"📊 {ls.get('period', '')} 사육통계")
                lines.append(f"   산란계 {layer['birds']:,}마리 / {layer.get('farms', 0):,}농가")
                if broiler.get("birds"):
                    lines.append(f"   육계   {broiler['birds']:,}마리 / {broiler.get('farms', 0):,}농가")
        except Exception:
            pass  # 사육통계는 참고용 보조 정보라, 못 읽어도 시세 알림 자체는 보낸다

    if len(lines) <= 2:
        return None, "표시할 시세 값이 하나도 없습니다."

    lines.append("")
    lines.append(f"수집: {data.get('updated', '-')}")
    lines.append(PRODUCER_URL)
    return "\n".join(lines), None


def send(token, chat_id, text):
    url = API_URL_TMPL.format(token=token)
    body = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.status, r.read().decode("utf-8", "replace")


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        print("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID 이 설정되지 않아 건너뜁니다.")
        return 0  # 워크플로 자체를 실패로 만들지 않는다 — telegram-notify.yml과 동일한 원칙

    text, err = build_message()
    if err:
        print("메시지 구성 실패:", err)
        return 1

    print("전송할 메시지:\n" + text)
    try:
        status, body = send(token, chat_id, text)
        print(f"텔레그램 응답: HTTP {status} {body[:200]}")
        return 0 if status == 200 else 1
    except urllib.error.URLError as e:
        print("전송 실패:", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
