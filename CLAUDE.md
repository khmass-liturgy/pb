# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Workflow preference (owner's standing instruction)

After finishing a change, the owner wants it shipped without asking each time: commit and push to the
session's designated branch, open a PR against `main`, and merge it (this overrides the default
"don't create a PR unless asked" rule for this repo). Merging to `main` is what publishes the site
(GitHub Pages) and the JSON the dashboard reads, so still run quick sanity checks before merging and
don't merge if something looks broken.

## What this is

A single-page static dashboard (`index.html`, ~4300 lines, no build step) for livestock/poultry
farm consulting: market prices (egg, chicken, pig, cattle), stocks/FX/grain futures, industry news,
and association notices. It's a Korean-language site (농장동물 컨설팅) deployed as a static GitHub
Pages site — `index.html` fetches its own JSON data files straight from
`raw.githubusercontent.com/khmass-liturgy/pb/main/...` at runtime (see the `*_JSON_URL` constants
around index.html:420-530).

**Custom domain**: `polcon.cc`, registered and DNS-managed through **Cloudflare** (not the GitHub
Pages default `khmass-liturgy.github.io`). DNS is 4 `A` records at the apex pointing at GitHub
Pages' IPs (185.199.108-111.153), proxied (orange cloud) through Cloudflare. If HTTPS or the
custom-domain check on the GitHub Pages settings page ever breaks after a DNS change, the fix is to
temporarily flip those records to "DNS only" (grey cloud) until GitHub finishes issuing/renewing the
Let's Encrypt cert — Cloudflare's proxy can block GitHub's validation — then switch back to proxied.

The data those JSON files contain is **not** produced at page-load time by the browser for most
panels. Instead, scheduled GitHub Actions workflows run Python scripts on a cron, which scrape/call
external sources server-side and commit the resulting JSON back into this repo. The browser just
reads the committed JSON. A few panels (news RSS, some board scraping) still fetch directly from the
browser through public CORS proxies — see `CORS_PROXIES` in index.html.

Two pieces are **not** static, both Firebase, both under the 유료서비스 tab:

- `functions/` holds two Cloud Functions (`resetMemberAccount`, `deleteMemberAccount`) used only by
  the admin-only 회원관리 (member management) screen, because deleting *another* user's Firebase
  Auth account requires Admin SDK privileges the browser's client SDK doesn't have. Guarded by
  checking the caller's verified Firebase ID token email against `ADMIN_EMAILS` in
  `functions/index.js` — no separate secret. Deploy with `firebase deploy --only functions`.
  It also holds the admin-only AI helpers for the 관리 screens: `generateAiDraft` (Claude writes a
  draft FAQ answer / study-card back / study-deck description into the form — never publishes) and
  `findCardImage` (Claude picks Commons search terms, `functions/commons.js` gathers free-license
  CC0/PD/CC BY/CC BY-SA candidates from Wikimedia Commons, then Claude looks at the thumbnails and
  picks the one that shows the card's representative sign — Commons results are noisy, e.g. "MD"
  matches MD-82 airliners, which is why the vision step exists). Cards store the pick as
  `backImage` with artist/license/source so the back face can show the attribution CC BY requires;
  the 온라인 자가진단 screen calls the same function with `kind:"selfcheck"` (disease name + organ)
  and stores the admin's pick as each disease's `image`. Self-check items 21–26 (벼슬·정강이·
  깃털·활력·임상증상·분변상태) have no hotspot on the anatomy picture (`sign:true` in `BODY_PARTS`) and ship
  a default disease list in `SELF_CHECK_SEED` that shows until an admin publishes it.
  These need the Firebase secret `ANTHROPIC_API_KEY` (a separate key from the GitHub Actions secret
  of the same name used by `fetch_research_papers.py`; set with
  `firebase functions:secrets:set ANTHROPIC_API_KEY --project chicken-dx`).
  It also holds `sendDirectSms` — the 📤 바로 보내기 button on the 점등/환우 program SMS boxes (index.html
  `renderSmsBox`/`bindSmsBox`): approved, non-expired members (checked against `member_registry/approved.json`,
  not just the claim) send the site-generated program text (header + no links/phone numbers) from the fixed
  sender 010-9150-8844 through the same sms-relay as the SMS job, max 5 recipients and 20/day per member
  (quota in private `sms_direct_usage/`, audit log in `sms_direct_log/`). Needs Firebase secrets
  `SMS_RELAY_URL` and `SMS_RELAY_SECRET` (same values as the GitHub Actions secrets of the same name).
  It also holds read proxies for Storage JSON (`getPremiumContent`, `getPublicContent`,
  `getApprovedMembers`, `getMemberProfiles`, `getSmsSubscriptions`, `getFeatureRequests`,
  `getBoardPosts`): the browser can't `fetch()` a private Storage file's download URL
  cross-origin (the served response is a redirect without CORS headers), so reads go through
  functions while writes still go straight from the client SDK under `storage.rules`. Don't add
  new client-side `getDownloadURL()`+`fetch()` reads of JSON — that pattern "saves but vanishes
  on reload" (it's what broke 회원관리 names and 자동 문자 발송 신청 until they were moved to
  functions). `<img src>` with a download URL is fine.
- `storage.rules` guards Firebase Storage, used for two things that can't go through the
  public-GitHub-commit pattern below because the data is private, not public content:
  - the 온라인 진단/상담/컨설팅 boards (`PREMIUM_BOARDS` in index.html) store member-submitted
    posts, photos and the vet's replies under `premium_board/{boardType}/{uid}/{postId}/`, readable
    only by that post's owner and admins.
  - `premium_members/{email}/info.json` holds each member's name/phone/join date — admin-only
    read/write. The approval list itself (`email`/`expires` only — whatever `isPremiumApproved()`
    needs) is `member_registry/approved.json`, also admin-only; the browser reads it through the
    `getApprovedMembers` Cloud Function, which returns the whole list to admins and only the
    caller's own entry to everyone else. It used to be `premium/approved.json` in this public repo
    (readable by anyone) and was deleted once the list had been migrated, so there is no fallback
    source any more. Because every save rewrites the whole list and Firebase Storage keeps no
    history, `publishMembers()` and the 회원관리 save/delete handlers refuse to run unless
    `premiumState.status === "done"` — saving after a failed load would otherwise overwrite the
    registry with an empty (or one-member) list and silently drop every other member.
  - `premium_content/{dataset}/latest.json` holds the four premium-only datasets (상황별 처방,
    계절별 패키지, 농장 맞춤 찾기, 온라인 자가진단— `treatment_packages`/`seasonal_packages`/
    `farm_finder`/`self_check`). These used to be public GitHub files like everything else in this
    repo, which meant anyone who found the raw URL could read paid content without logging in —
    moved here so only approved members (or admins) can read it, and only admins can write it.
    Approval is checked via a Firebase Auth **custom claim** (`request.auth.token.approved`), since
    Storage rules can't query the approval list's contents directly. The
    `setMemberApproval` Cloud Function sets that claim, called from index.html's member-save handler
    every time a member is added or edited — so a membership's `expires` field only actually takes
    effect at the Storage layer the next time that member's record is saved (not automatically at
    midnight on the expiry date; whoever edits members should re-save a lapsed member to revoke
    Storage access, or delete them outright). The claim only applies on the member's next token
    refresh (up to ~1h) unless index.html forces one via `getIdToken(true)`, which it does right
    after a login is found to be approved.
  - `public_content/{dataset}/latest.json` is the same shape but **world-readable** (admin-only
    write) — for admin-authored content shown without login: AI 관련 소식 (`hpai_news`, photos under
    `public_content/hpai_news_images/`), 이달의 질병 (`monthly_pick`) and the 유료서비스 menu
    editor's saved menu (`premium_menu`). All three used to be committed to this repo through the
    GitHub Contents API with a personal access token kept in the admin's browser, until that kept
    failing with 403s; there is no GitHub-token publishing left in index.html. Reads go through the
    unauthenticated `getPublicContent` Cloud Function (same CORS reason as `getPremiumContent`),
    and `fetchPublicContentOrLegacy()` falls back to the old file in this repo
    (`hpai_news/news.json`, `monthly_pick/picks.json`, `premium_menu/items.json`) until the first
    Firebase publish of each.
  - Every write above (and all the admin "⚙ 관리" UI) is gated on `isBoardAdmin()` — the logged-in
    Firebase account's email being in `BOARD_ADMIN_EMAILS` — so the admin has to be logged in on the
    유료서비스 tab even to manage content on the free tabs.
  Both paths check the caller's email against a hardcoded admin list — keep it in sync with
  `functions/index.js`'s `ADMIN_EMAILS` when adding/removing an admin. Deploy with
  `firebase deploy --only storage`.

Both need `firebase-tools` and `firebase login` once; nothing else in this repo needs a build/deploy
step.

## Architecture: the fetch-script → JSON → dashboard pipeline

Each data domain has this shape:

1. `scripts/fetch_*.py` — stdlib-only or `requests`-based script, runs in CI, writes one JSON file.
2. `.github/workflows/fetch-*.yml` — cron schedule (KST times expressed as UTC cron), runs the
   script, commits+pushes the output directory if it changed.
3. `index.html` — loads the raw JSON URL client-side and renders it.

| Domain | Script | Output | Workflow | Schedule (KST) |
|---|---|---|---|---|
| Chicken/egg/pig/cattle farm prices (ekapepia) | `scripts/fetch_poultry_price.py` | `poultry_price/latest.json` | fetch-poultry-price.yml | daily 09:00 |
| Chicken/egg via KAPE public API | `scripts/fetch_prices.py` | `prices/prices.json` | fetch-prices.yml | weekdays 08:00 |
| Egg weekly supply/demand report (PDF) | `scripts/fetch_egg_report.py` | `egg_report/latest.json` (+ `.pdf`) | fetch-egg-report.yml | daily 10:00 |
| Chicken price board (chicken.or.kr) | `scripts/fetch_egg_price.py` | `chicken_price/latest.json` | — | — |
| Stocks/FX/grain futures (Yahoo Finance) | `scripts/fetch_market.py` | `market/quotes.json` | fetch-market.yml | weekdays hourly during KR+US market hours, weekends 1x |
| Briefing news (multi-outlet scrape) | `scripts/fetch_briefing_news.py` | `news/briefing.json` | fetch-briefing-news.yml | weekdays every 2h, weekends 08:00 |
| General news (RSS) | `scripts/fetch_news.py` | `news/news.json` | fetch-news.yml | daily 08:00 |
| Association notices | `scripts/fetch_notices.py` | `notices/notices.json` | fetch-notices.yml | daily 08:00 |
| 금일 육계시세(대한양계협회 poultry.or.kr) | `scripts/fetch_broiler_price_today.py` | `broiler_price_today/latest.json` | fetch-broiler-price-today.yml | daily 13:20 |
| 기술탐구 논문(PubMed → Claude API 번역·요약, 유료서비스 전용) | `scripts/fetch_research_papers.py` | `research_papers/latest.json` | fetch-research-papers.yml | weekly Sun 07:10 |
| 배합사료 생산실적(농식품부 월별 .xls → 육계·산란계 생산잠재력 마릿수 추정) | `scripts/fetch_feed_production.py` | `feed_production/latest.json` | fetch-feed-production.yml | daily 10:30 (commits only when a new month is posted, ~20th) |
| 국내 고병원성 AI 가금농장 발생·야생조류 검출(농식품부 「발생·검출 현황」 .hwp 표 + Google 뉴스 RSS 최근 3일 보도) | `scripts/fetch_hpai_kr.py` | `hpai_kr/latest.json` | fetch-hpai-kr.yml | daily 09:30·18:30 (commits only when the table or news changed) |
| 사료곡물 가격동향·전망(CBOT 옥수수·대두박·대두·밀 + 환율·달러지수·유가·운임 + grain_quality 기상 → 6요인 가중점수 1·3개월 전망, 유료서비스 전용 카드) | `scripts/fetch_grain_price.py` | `grain_price/latest.json` | fetch-grain-price.yml | Tue–Sat 08:00 (US close; commits only when numbers changed) |
| 양계 업계 소식(Google 뉴스 국내판에서 계란·조류인플루엔자·AI·육계·방역·양계 질병 키워드 24개 검색, 최근 14일 누적, 유료서비스 「양계 업계관련 핵심키워드 검색소식」 카드; 원문 주소는 Google 뉴스 링크를 batchexecute로 풀고, 본문 요약은 Claude Haiku(ANTHROPIC_API_KEY, 없으면 본문 앞부분 발췌)) | `scripts/fetch_industry_news.py` | `industry_news/latest.json` | fetch-industry-news.yml | daily 07:30 |
| 동물약품 주간 소식(Google 뉴스 국내판·해외판에서 동물용의약품 신제품·백신·항생제·허가·제약업계 소식 후보를 모아 Claude Haiku가 가금 현장에 중요한 3~5건을 고르고 요약·번역, 유료서비스 「동물약품 주간 소식」 카드; 최근 12주 보관, 키가 없으면 키워드 점수·본문 발췌) | `scripts/fetch_animal_drug_news.py` | `animal_drug_news/latest.json` | fetch-animal-drug-news.yml | weekly Fri 07:00 |
| 가금 질병·백신 주간 브리핑(PubMed 최근 3주 논문 + Google 뉴스 site: 검색으로 WOAH·EFSA·APHIS·APHA·FAO·검역본부·The Poultry Site 등 후보를 모아 Claude가 현장 컨설팅에 중요한 3건을 고르고 ①새 내용 ②현장 중요성 ③주의점·한계 + 주간 체크포인트를 한국어로 정리, 원문 제목·기관·날짜·링크는 원자료 그대로; 최근 26주 보관, 이전 주 자료는 후보에서 제외, API 키가 없으면 이전 값 유지) | `scripts/fetch_poultry_disease_brief.py` | `poultry_disease_brief/latest.json` | fetch-poultry-disease-brief.yml | weekly Mon 07:00 |
| AI 관련 소식 자동 등록(검색어 「조류인플루엔자」 Google 뉴스 최근 3일 → 가금 방역 맥락 기사 중 이미 올라온 소식·삭제된 자동 등록 기사·제목이 거의 같은 기사를 뺀 1건을 요약·원문 링크와 함께 `public_content/hpai_news/latest.json`에 Admin SDK로 추가; 켜고 끄기·마지막 등록은 같은 파일의 `auto` 필드, 화면 관리 상자의 「자동 등록」 버튼; `FIREBASE_SERVICE_ACCOUNT_JSON` 필요) | `scripts/post_hpai_news_daily.py` | Firebase Storage `public_content/hpai_news/latest.json` (저장소 파일 없음) | post-hpai-news-daily.yml | daily 08:20 |

`fetch_hpai_kr.py` reads the MAFRA HWP table (olefile) through the same domestic relay as the feed-production job —
the relay's `MAFRA_ALLOWED_PATH` (farm-pro `sms-relay/server.js`) must include `bbs/FMD-AI2/851`, and the VM needs the
updated server.js deployed or the workflow fails. The board is updated only now and then (25/26 season: 12.30 then
3.22), so the JSON also carries recent news headlines. index.html's 발생지도 merges rows confirmed on/after
2026-09-01 (`HPAI_KR_NEW_SEASON`) from that JSON on top of the built-in 25/26 season data (`HPAI_KR_FARMS`/`HPAI_KR_WILD`)
and draws them in purple/teal.

The 유료서비스 「육계·계란 시세예측」(`priceforecast`, index.html `PF` 상수·`pfBuildModel`) has no fetch script of its own: it
reads the existing JSON (`feed_production`, `poultry_price`, `broiler_price_today`, `layer_stats`, `egg_report`) in the browser.
Supply pressure = 배합사료 월 생산량의 전년 대비 증감(육계 사료 → 마릿수, 산란계는 산란 중 + 육성 병아리 가중), demand pull = 월별
계절지수(`PF.seasonal`, 경험값) + 최근 한 달 가격 흐름, 둘의 차를 3상태(상승/보합/하락) softmax로 1·2·3개월 확률로 바꾼다. It is a
rule-based reference model, not backtested — keep that disclaimer in the UI, and tune the assumptions only through the `PF` constants.

`fetch_egg_report.py` and `fetch_egg_price.py` currently have no workflow wired up — check before
assuming their output is refreshed automatically.

### Conventions shared across all fetch scripts

- **Partial failure never wipes good data.** If a script pulls N sub-values (e.g. egg/chicken/pig/cow)
  and one fails, only that one falls back to the previous committed JSON value and gets marked
  `"stale": true`; the others still update. Preserve this pattern when touching any fetch script —
  don't let one failing source blank out the whole output file.
- **Direct request first, public CORS proxy as fallback**, for sources that are flaky or geo/rate
  limited (`api.allorigins.win`, `api.codetabs.com`, etc). See `PROXY_FACTORIES`/`PROXY_TEMPLATES`/
  `PROXY_URLS` in the individual scripts, and `CORS_PROXIES` in index.html for the browser-side list.
- **All timestamps are KST** (`timezone(timedelta(hours=9))`), independent of the UTC runner clock.
  Workflow cron schedules are UTC and the comments above each cron line document the KST equivalent
  — when changing a schedule, update both the cron expression and its KST comment.
- Workflows commit only their own output directory (`git add market/`, `git add news/`, etc.) and
  most retry `git pull --rebase --autostash && git push` a few times to survive races between
  concurrently-running workflows (they share this repo and can finish close together).
- Scripts favor the stdlib (`urllib`, `html.parser.HTMLParser`) over `requests` where possible so
  CI doesn't need extra pip installs; `fetch_market.py` and `fetch_prices.py` are the exceptions
  (they use `requests`), and `fetch_feed_production.py` also needs `xlrd` because the source is
  a real BIFF `.xls` attachment, not HTML.
- Three scripts translate English source content to Korean:
  `fetch_briefing_news.py` (해외 양계질병 news titles, free Google Translate/MyMemory endpoints),
  `fetch_poultry_diseases.py` (The Poultry Site disease articles, same endpoints), and
  `fetch_research_papers.py` (PubMed abstracts, via the Claude API). All three import
  `scripts/translation_glossary.py` and pass every translated string through
  `apply_glossary()` before saving, so a fix to a mistranslated/non-standard term (e.g. "bird
  flu" → "조류독감" instead of the correct "조류인플루엔자") only needs to be added once in that
  file to apply everywhere. It also fixes the Korean particle right after a replaced term
  (이/가, 은/는, 을/를, 과/와, 으로/로, and the 이- copula contractions like 이다/이라는) to match
  the new word's 받침. This is the one place scripts import from each other — it works because
  each workflow invokes its script as `python scripts/fetch_*.py`, which puts `scripts/` itself
  on `sys.path`.

### The SMS dispatch job (not the fetch-script shape above)

`scripts/send_sms_subscriptions.py` + `.github/workflows/send-sms-subscriptions.yml` (daily 08:30
KST) is a different shape from the table above — it doesn't read an external source or write JSON
into this repo. It processes the 유료서비스 "자동 문자 발송 신청" subscriptions (member picks a
menu — 15 choices in 시세·경제 / 질병·방역 / 사양·정보 groups, see `SMS_SUBSCRIBABLE_MENUS` in index.html and `build_digest` in the script; most read this repo's public JSON, so a new menu = one digest function + one list entry — and an interval) stored in Firebase Storage under
`premium_board/sms_sub/{uid}/settings/config.json`, and for whichever subscribers are due, sends a
digest text via the **sms-relay** fixed-IP proxy already deployed for the sibling `farm-pro` project
(OneDrive `GitHub-daehan/farm-pro/sms-relay/`, an Oracle Cloud VM in front of the 알리고 SMS API —
알리고 only accepts calls from an IP it has allowlisted, which GitHub Actions runners don't have).
Requires three repo secrets that don't exist anywhere else in this repo — `FIREBASE_SERVICE_ACCOUNT_JSON`
(a `chicken-dx` Firebase service account key, since the script reads/writes Storage with Admin SDK
privileges that bypass `storage.rules` — there's no logged-in user in CI), `SMS_RELAY_URL` and
`SMS_RELAY_SECRET` (the same two values farm-pro's Supabase Edge Function secrets use for the same
relay). index.html's admin-only "자동 문자 발송 관리" screen is a monitoring/manual-backup view for
this job, not the primary send path.

## Commands

Run the one existing test suite:

```bash
python -m unittest tests/test_fetch_poultry_price.py -v
```

Run a single fetch script locally (writes into the matching output directory in the working tree):

```bash
python scripts/fetch_poultry_price.py
python scripts/fetch_market.py            # requires `pip install requests`
python scripts/fetch_prices.py            # requires EKAPE_API_KEY env var + `pip install requests`
```

There is no build step, package manager, or lint config — `index.html` is edited directly and
served as-is.

## Working in index.html

It's one large HTML file with inline `<script>`/`<style>`, organized as data constants
(`STOCK_DATA`, `GRAIN_DATA`, `OIL_DATA`, `FX_DATA`, `COIN_DATA`, `LIVESTOCK_DATA`, `COST_DATA`, ...)
followed by fetch/parse/render functions per panel (`fetchPoultryPrices`, `fetchDabomPrices`,
`fetchEggReport`, `fetchChickenPrices`, `fetchNotices`, `fetchEconNews`, `fetchPolicyNews`, ...).
User-editable state (custom watchlists, board list, weather location) persists to `localStorage`
(`poultry_custom_boards`, `custom_stocks`, `custom_coins`, notice cache with a 20-minute TTL). When
adding a new data panel, follow the existing pattern: a `*_JSON_URL` pointing at
`raw.githubusercontent.com/khmass-liturgy/pb/main/...`, an `async function fetch*()` that fetches it
with a proxy fallback list, and a render function — rather than inventing a new data-loading approach.
