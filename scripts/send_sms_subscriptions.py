#!/usr/bin/env python3
"""자동 문자 발송 신청(index.html의 "자동 문자 발송 신청" 메뉴) 구독자 중
발송 주기가 된 사람에게 신청한 메뉴의 최신 정보를 문자로 보낸다.

알리고 SMS API는 관리자 페이지에 등록해둔 고정 IP에서 온 요청만 허용하는데,
GitHub Actions 러너는 실행할 때마다 IP가 달라져 알리고를 직접 호출할 수 없다.
그래서 이미 다른 프로젝트(farm-pro)에 배포해둔 고정 IP 중계 서버(sms-relay,
Oracle Cloud VM)를 그대로 재사용한다 — 그 서버 앞단 인증은 RELAY_SECRET
공유 비밀값 하나뿐이라 어디서 호출하든 상관없다(자세한 구조는 farm-pro
저장소의 sms-relay/README.md 참고).

구독 설정과 발행된 콘텐츠(계절별 패키지·상황별 처방)는 Firebase Storage에
있고 보안 규칙상 승인된 회원 본인+관리자만 읽을 수 있다 — GitHub Actions는
로그인 세션이 없으므로, Firebase 보안 규칙을 그대로 우회하는 서비스 계정
(Admin SDK)으로 접근한다.

필요한 GitHub Actions Secrets (저장소 Settings → Secrets and variables → Actions):
- FIREBASE_SERVICE_ACCOUNT_JSON : Firebase 콘솔 > 프로젝트 설정 > 서비스 계정 >
  "새 비공개 키 생성"으로 받은 JSON 파일 내용을 그대로 붙여넣는다 (chicken-dx 프로젝트).
- SMS_RELAY_URL    : sms-relay 서버의 /send-sms 엔드포인트 (farm-pro와 동일한 값)
- SMS_RELAY_SECRET : 그 서버의 RELAY_SECRET과 동일한 값 (farm-pro와 동일한 값)
셋 중 하나라도 없으면 조용히 종료한다(다른 fetch 스크립트들과 달리 이 작업은
"아직 설정 전"이 정상 상태일 수 있어 CI를 실패시키지 않는다).
"""
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

import firebase_admin
from firebase_admin import credentials, storage

KST = timezone(timedelta(hours=9))
INTERVAL_DAYS = {"daily": 1, "weekly": 7, "monthly": 30}
SENDER_PHONE = "01091508844"  # 최동명 수의사 대표번호 (010-9150-8844)
RESEARCH_PAPERS_URL = "https://raw.githubusercontent.com/khmass-liturgy/pb/main/research_papers/latest.json"
POULTRY_PRICE_URL = "https://raw.githubusercontent.com/khmass-liturgy/pb/main/poultry_price/latest.json"
BROILER_PRICE_TODAY_URL = "https://raw.githubusercontent.com/khmass-liturgy/pb/main/broiler_price_today/latest.json"
BRIEFING_NEWS_URL = "https://raw.githubusercontent.com/khmass-liturgy/pb/main/news/briefing.json"
SEASON_LABELS = {"spring": "🌸 봄", "summer": "☀️ 여름", "fall": "🍂 가을", "winter": "❄️ 겨울"}


def load_json_blob(bucket, path):
    blob = bucket.blob(path)
    if not blob.exists():
        return None
    try:
        return json.loads(blob.download_as_text())
    except (ValueError, UnicodeDecodeError):
        return None


def save_json_blob(bucket, path, data):
    bucket.blob(path).upload_from_string(
        json.dumps(data, ensure_ascii=False), content_type="application/json"
    )


def is_due(cfg, today):
    days = INTERVAL_DAYS.get(cfg.get("interval"), 7)
    last = cfg.get("lastSentAt")
    if not last:
        return True
    try:
        last_dt = datetime.fromisoformat(last.replace("Z", "+00:00")).astimezone(KST)
    except ValueError:
        return True
    return today >= last_dt + timedelta(days=days)


def current_season():
    month = datetime.now(KST).month
    if 3 <= month <= 5:
        return "spring"
    if 6 <= month <= 8:
        return "summer"
    if 9 <= month <= 11:
        return "fall"
    return "winter"


def build_digest(bucket, menu):
    if menu == "seasonal":
        data = load_json_blob(bucket, "premium_content/seasonal_packages/latest.json") or {}
        season = current_season()
        label = SEASON_LABELS[season]
        items = [p for p in data.get("packages", []) if p.get("season") == season]
        if not items:
            return f"[{label} 계절별 패키지]\n아직 등록된 내용이 없습니다."
        lines = [f"[{label} 계절별 투약·관리 패키지]"]
        for p in items:
            lines.append("")
            lines.append("▶ " + p.get("title", ""))
            for s in (p.get("medication") or [])[:2]:
                lines.append(f"- {s.get('step','')}: {s.get('detail','')}")
        return "\n".join(lines)

    if menu == "research":
        try:
            with urllib.request.urlopen(RESEARCH_PAPERS_URL, timeout=10) as r:
                data = json.loads(r.read().decode("utf-8"))
        except Exception:
            data = {}
        cats = data.get("categories") or {}
        if not cats:
            return "[기술탐구]\n아직 수집된 논문이 없습니다."
        lines = ["[이번 주 기술탐구 요약]"]
        for cat in cats.values():
            papers = cat.get("papers") or []
            if papers:
                lines.append("")
                lines.append(f"▶ {cat.get('label','')} — {papers[0].get('title_ko','')}")
        return "\n".join(lines)

    if menu == "treatment":
        data = load_json_blob(bucket, "premium_content/treatment_packages/latest.json") or {}
        items = data.get("packages", [])
        if not items:
            return "[상황별 처방 패키지]\n아직 등록된 상황이 없습니다."
        lines = ["[상황별 처방(투약) 패키지 목록]"]
        for species, label in (("broiler", "🐔 육계"), ("layer", "🥚 산란계")):
            sub = [p for p in items if p.get("species") == species]
            if sub:
                lines.append("")
                lines.append(label)
                lines.extend("- " + p.get("title", "") for p in sub)
        return "\n".join(lines)

    if menu == "poultry_price":
        lines = ["[📊 양계 산지시세]"]
        try:
            with urllib.request.urlopen(POULTRY_PRICE_URL, timeout=10) as r:
                pp = json.loads(r.read().decode("utf-8"))
            egg = pp.get("egg") or {}
            if isinstance(egg.get("latest"), int):
                lines.append(f"🥚 계란({egg.get('grade','특란')}): {egg['latest']:,}{egg.get('unit','원/10개')}")
        except Exception:
            pass
        try:
            with urllib.request.urlopen(BROILER_PRICE_TODAY_URL, timeout=10) as r:
                bt = json.loads(r.read().decode("utf-8"))
            rows = bt.get("rows") or []
            if rows:
                lines.append(f"🐔 육계 금일시세({bt.get('date_label','')})")
                for row in rows:
                    today = row.get("today")
                    val = f"{today:,}" if isinstance(today, int) else "-"
                    spec = f"({row['spec']})" if row.get("spec") else ""
                    lines.append(f"- {row.get('grade','')}{spec}: {val}{row.get('unit','')}")
        except Exception:
            pass
        if len(lines) == 1:
            return "[📊 양계 산지시세]\n아직 수집된 시세가 없습니다."
        return "\n".join(lines)

    if menu == "briefing":
        try:
            with urllib.request.urlopen(BRIEFING_NEWS_URL, timeout=10) as r:
                nb = json.loads(r.read().decode("utf-8"))
        except Exception:
            nb = {}
        sources = nb.get("sources") or {}
        lines = ["[📋 뉴스정보 브리핑]"]
        found = False
        for key, label in (("chuksan", "축산신문"), ("econ", "경제"), ("policy", "정책")):
            items = (sources.get(key) or {}).get("items") or []
            if items:
                found = True
                lines.append("")
                lines.append(f"▶ {label} — {items[0].get('title','')}")
        if not found:
            return "[📋 뉴스정보 브리핑]\n아직 수집된 뉴스가 없습니다."
        return "\n".join(lines)

    return ""



def send_sms(relay_url, relay_secret, phone, content):
    body = json.dumps({"from": SENDER_PHONE, "content": content, "targets": [{"to": phone}]}).encode("utf-8")
    req = urllib.request.Request(
        relay_url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {relay_secret}"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    sa_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
    relay_url = os.environ.get("SMS_RELAY_URL")
    relay_secret = os.environ.get("SMS_RELAY_SECRET")
    if not sa_json or not relay_url or not relay_secret:
        print("FIREBASE_SERVICE_ACCOUNT_JSON / SMS_RELAY_URL / SMS_RELAY_SECRET 중 아직 "
              "설정되지 않은 값이 있습니다 — 저장소 Settings > Secrets에서 추가한 뒤 다시 실행하세요.")
        sys.exit(0)

    cred = credentials.Certificate(json.loads(sa_json))
    firebase_admin.initialize_app(cred, {"storageBucket": "chicken-dx.firebasestorage.app"})
    bucket = storage.bucket()

    today = datetime.now(KST)
    sent = failed = skipped = 0
    for blob in bucket.list_blobs(prefix="premium_board/sms_sub/"):
        if not blob.name.endswith("/settings/config.json"):
            continue
        try:
            cfg = json.loads(blob.download_as_text())
        except (ValueError, UnicodeDecodeError):
            continue
        if not cfg.get("active") or not cfg.get("menu") or not cfg.get("interval") or not cfg.get("phone"):
            skipped += 1
            continue
        if not is_due(cfg, today):
            skipped += 1
            continue

        digest = build_digest(bucket, cfg["menu"])
        text = "[농장동물 컨설팅 안내]\n" + digest + "\n\n자세히 보기: https://polcon.cc"
        try:
            result = send_sms(relay_url, relay_secret, cfg["phone"], text)
            print(f"발송 완료: {cfg.get('email','?')} ({cfg['menu']}) -> {result}")
            cfg["lastSentAt"] = today.isoformat()
            save_json_blob(bucket, blob.name, cfg)
            sent += 1
        except urllib.error.HTTPError as e:
            print(f"발송 실패: {cfg.get('email','?')} - HTTP {e.code}: {e.read().decode('utf-8','ignore')}")
            failed += 1
        except Exception as e:
            print(f"발송 실패: {cfg.get('email','?')} - {e}")
            failed += 1

    print(f"완료 — 발송 {sent}건, 대기 {skipped}건, 실패 {failed}건")


if __name__ == "__main__":
    main()
