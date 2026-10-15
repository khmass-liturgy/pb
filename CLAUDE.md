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
  draft FAQ answer / study-card back / study-deck description / 상황별 처방 증상·원인·해결책 요점 (`kind:"treatment"`, parsed by `treatmentParseAiDraft`) into the form — never publishes) and
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
| 날씨 뉴스(Google 뉴스 국내판에서 날씨·기상 특보(폭염·한파·호우·태풍·대설·강풍)·황사·이상기후·농업/축산 기상 키워드 검색, 최근 3일 유지, 날씨예측 탭 「오늘의 날씨 뉴스」 카드; 원문 주소·본문 추출은 `fetch_industry_news.py` 함수 재사용, 요약은 Claude Haiku(ANTHROPIC_API_KEY, 없으면 본문 앞부분)) | `scripts/fetch_weather_news.py` | `weather_news/latest.json` | fetch-weather-news.yml | 6×/day (06:10·09:10·12:10·15:10·18:10·21:10) |
| AI 관련 소식 자동 등록(검색어 「조류인플루엔자」 Google 뉴스 최근 3일 → 가금 방역 맥락 기사 중 이미 올라온 소식·삭제된 자동 등록 기사·제목이 거의 같은 기사를 뺀 1건을 요약·원문 링크와 함께 `public_content/hpai_news/latest.json`에 Admin SDK로 추가; 켜고 끄기·마지막 등록은 같은 파일의 `auto` 필드, 화면 관리 상자의 「자동 등록」 버튼; `FIREBASE_SERVICE_ACCOUNT_JSON` 필요) | `scripts/post_hpai_news_daily.py` | Firebase Storage `public_content/hpai_news/latest.json` (저장소 파일 없음) | post-hpai-news-daily.yml | daily 08:20 |

`fetch_hpai_kr.py` reads the MAFRA HWP table (olefile) through the same domestic relay as the feed-production job —
the relay's `MAFRA_ALLOWED_PATH` (farm-pro `sms-relay/server.js`) must include `bbs/FMD-AI2/851`, and the VM needs the
updated server.js deployed or the workflow fails. The board is updated only now and then (25/26 season: 12.30 then
3.22), so the JSON also carries recent news headlines. index.html's 발생지도 merges rows confirmed on/after
2026-09-01 (`HPAI_KR_NEW_SEASON`) from that JSON on top of the built-in 25/26 season data (`HPAI_KR_FARMS`/`HPAI_KR_WILD`)
and draws them in purple/teal.

`farm_density/sigun.json` — 가금 시·군별 사육 농가·마릿수(가축위생방역지원본부 「전국 시군별 ○○ 사육규모 현황」, data.go.kr 파일데이터 CSV, 연 1회 갱신, **일반 산란계 표는 이 시리즈에 없음**). `scripts/fetch_farm_density.py`를 수동 실행해 만든다(워크플로 없음 — data.go.kr이 해외 IP를 막는지 확인 안 됨). index.html의 HPAI ZERO FARM 「과거 대조」가 거리 규칙의 효과를 농장 밀도로 보정할 때 읽는다(밀도 = 반경 20km 상업 사육 마릿수, 토종닭·백세미 제외).
The 유료서비스 「약품별 사용요령 카드」(`drugusage`, index.html `drugUse*`/`renderDrugUsePanel`, Firebase `premium_content/drug_usage/latest.json` `{items:[…]}`) is one card per drug; admins add/edit/delete in the page. Basic info fills two ways: 「QIA에서 찾아 채우기」(`qiaFullDetail` parses the medi.qia.go.kr detail page: 효능효과 → 용법용량 → 주의사항(가~사, 휴약기간 포함) order, official text copied as-is, QIA link auto-added) and 「AI로 사용요령 정리」(`generateAiDraft` kind `drug`, `DRUG_SYSTEM_PROMPT` in functions/index.js — turns that official text into 분류/한줄요약/사용요령 lines; it must never invent doses or 휴약기간, only copy numbers from the supplied official text; marked “AI 초안” until an admin ticks 수의사 검토 완료). Product-info links are added by hand (search shortcuts for QIA/Google/Naver open in a new tab; only http(s) URLs are saved). The `drug` kind needs `firebase deploy --only functions` after the first merge.
The 유료서비스 「닭 대장균증 잡는 교실」(`coliclass`, category 최꼬 아카데미; index.html `COLI_*`/`coli*`/`renderColiPanel`) is a static 12-lesson course (기초→현장 판단→치료·재발 방지→최신 연구 읽기, 육계/산란계 split, inline-SVG figures `coliSvg*`, 가상 사례 4개 labelled as fictional, 대응계획서 template saved in localStorage `coli_v1`). Content comes from the owner-supplied curriculum (research citations as of 2026-10-15, not re-verified here); it never names drugs or doses — treatment is left to the vet and product labels. Add new lessons by editing `COLI_LESSONS`.
The 유료서비스 「계절별 사양관리,질병,투약(관리) 패키지」(`seasonal`) has per-season 육계/산란계 guides: default content is code (`SEASON_GUIDES` for 봄·여름·겨울, drafts marked 「초안(수의사 검토 전)」; 가을 uses the richer `renderAutumnBroiler`/`renderAutumnLayer`). Admins edit a guide on screen (「✏️ 이 가이드 편집」, text format `## 이름 | 아이콘 | 태그` + bullets, see `sg*` functions); the edit is stored in Firebase `premium_content/seasonal_guides/latest.json` `{guides:{"season-animal":cfg}}` and replaces the default (saving a 가을 guide drops its tables/figures; 「기본으로 되돌리기」 deletes the override). Packages the admin adds in the old form carry an `animal` tag.
The 유료서비스 「육계·계란 시세예측」(`priceforecast`, index.html `pf*`/`PF*` — engine, data, charts, 8 sub-tabs) runs entirely in the browser
(no server model). Inputs: `price_history/daily.json` (egg 특란 원/10개 and 육계 생계유통(대) 원/kg daily series + monthly feed tonnage;
**separate series per source, never mixed** — the 협회 broiler quote is its own `broiler_assoc` series), the existing JSON
(`feed_production`, `poultry_price`, `broiler_price_today`, `layer_stats`, `egg_report`), admin-published uploads in Firebase
`premium_content/price_forecast_data/latest.json` (members read it through `getPremiumContent`, admin writes with
`writePremiumContentJson`) and per-viewer CSV uploads kept in localStorage (`pf_uploads_v1`).
`scripts/accumulate_price_history.py` (workflow accumulate-price-history.yml, daily 09:40 + 14:40 KST) appends new days to
`price_history/daily.json` and folds `feed_production/history.json` into `feed_monthly`. One-off backfills (workflow_dispatch):
`backfill-price-history.yml` → `scripts/backfill_price_history.py` (ekapepia serves daily tables from 2018-03-01 when given
`radioChk=day&startYYMMDD&endYYMMDD&searchStartDate&searchEndDate`; date cells have **no year** ("01월 12일") and empty cells are "-",
so values are read **by cell position**, not by "n-th number" — the egg XL 원/10개 column is cell 2, 육계 생계유통(대) cell 1; before
2020-06 the 육계 cells are all "-"), and `backfill-feed-production.yml` → `scripts/backfill_feed_production.py` (MAFRA board keeps only
the last ~3 years of 배합사료 posts, so older years must come from an admin CSV upload).
Model (`pfForecast`): ridge regression of the log price change h months ahead (features: feed-based supply pressure, seasonal change,
1-month momentum, deviation from 12-month mean; 1·2 week horizons use daily features), rolling-origin backtest, forecast size shrunk
0–1× by the backtest slope, interval/probabilities from out-of-sample residuals, probabilities calibrated by reliability bins, grade
(높음/보통/낮음/검증 불가) from backtest skill vs "no change"/"same month last year". With too little price history it returns
`insufficient` and the UI shows **no price forecast** (only the rule-based direction indicator, `pfBuildModel`, labelled unverified).
Never fabricate forecasts: demo mode (`pfDemoData`, seeded synthetic series) must keep the red "데모 데이터 · 실제 시장 예측 아님" banner.
`scripts/fetch_import_stats.py` (workflow fetch-import-stats.yml, weekly Tue 10:20 KST, `FULL=1`/dispatch input `full` for the first 36-month pull) writes `import_status/stats.json` (monthly 닭고기 HS 0207 / 신선란 040721 / 종란 040711 import tonnage and top partners): UN Comtrade public preview API (no key; one month × one HS code per request — multiple periods or mixed HS digit lengths return 400; 429 backoff; Korea reports with a ~9-month lag so 2026 is empty) and, when the repo secret `DATA_GO_KR_KEY` is set, 관세청 (preferred; the key must be activated for exactly this API) 「품목별 국가별 수출입실적」 (data.go.kr `…/1220000/nitemtrade/getNitemtradeList`, verified 2026-10: params `strtYymm/endYymm/hsSgn` with 4/6-digit HS prefixes and 12-month ranges work, `cntyCd` optional; response rows carry `year` ("YYYY.MM", plus one "총계" total row that is skipped), `impWgt` kg, `impDlr` USD, `statCdCntnKor1` country; months with no imports are simply absent; customs values replace UN values and run `customs_only=1` as a quick connectivity check). Customs (apis.data.go.kr) does not answer GitHub runners (foreign IPs), so the job calls it through the same domestic relay as the feed job — `/fetch-customs` in farm-pro `sms-relay/server.js` (VM must be redeployed + restarted), reusing secrets `SMS_RELAY_URL`/`SMS_RELAY_SECRET`; without them or on no response it skips customs after one probe.
The 유료서비스 「계육·계란·종란 수출입 동향」 card (`tradestats`, category 게시판·기타; index.html `trade*`/`renderTradePanel`, own `tradeState` + `fetchTradeStats`) draws `stats.json` (monthly import/export tonnage via `t`/`ex_t`, USD via `kusd`/`ex_kusd`, partner shares via `by`/`ex_by`; export fields exist only on customs rows, so a `FULL=1` run backfills them; months missing inside the coverage window = 0 t). It reuses `pfSvgChart`/`pfBindCharts`.
The price-forecast engine links `import_status/stats.json` through `pfImportSeries` (3-month import tonnage YoY change ÷ assumed domestic monthly supply `PF.importDomesticT` → supply-pressure %p; months inside the stats coverage window with no row count as 0 t): `pfForecast` re-runs the same rolling backtest with the import term and adopts it **only if the nested WAPE drops** (`out.impEffect`: used / why / last); otherwise the KPI card just shows the latest import pressure as "not reflected". With imports only from 2023-11 the check is not yet possible, so it currently displays only. Never force it on without a passing check.
The 백신관리 프로그램 screen has a second view 「접종방법·백신 종류」 (`vaccineTabState.view === "guide"`, `renderVaccineGuide`/`vgBind`): default content lives in `VACCINE_GUIDE_SEED` and is replaced by the admin-published Firebase `premium_content/vaccine_guide/latest.json` (`methods`/`types` lists of `{key,name,icon,color,summary,features,vaccines,tips}`, multi-line fields = one item per line, `[태그]` prefix in `vaccines` renders a badge); admin edits it in the 「⚙ 관리」 box and 「기본 내용으로 되돌리기」 republishes the seed.
The 유료서비스 menu's first item 「전염성기관지염(IB)차단 AI공동연구팀」 (`ibteam`, category 최꼬 아카데미 (was 인공지능 공동연구팀; card title 「IB 닭기침 잡는 교실」); index.html `IB_*`/`ibLecture1`/`renderIbTeamPanel`/`ibBind`) is a static, step-by-step research course: 8 stages (`IB_STAGES`), only stages ≤ `IB_CURRENT_STAGE` open, each lecture split into sections ①–⑨ (목표·기초·전문 심화·육계/산란계·현장 사례·문헌·예방관리·요약/점검 질문·다음 제안). The owner drives it: publish the next lecture only when asked (add content to `IB_LECTURES` + `ready:true`) and raise `IB_CURRENT_STAGE` only on an explicit 「다음 단계」; 「더 깊이」/「논문 분석」/「현장 중심으로」 deepen the current lecture. Literature cards must be real works; each literature card carries its verification level (`ver`: `full` = full text read, `abs` = bibliography + abstract only, `cite` = bibliography only via other papers' reference lists) — never invent papers, PMIDs or results. The cloud environment allows PubMed E-utilities/PMC, doi.org, Crossref and woah.org (WOAH PDFs answer 403 unless a browser User-Agent is sent). Claims carry 확인된 사실/가설/논쟁 중/현장 추론 badges (`ibTag`). **Every lecture is designed field-first** (owner's instruction): each section ties the science to farm actions (`ibField` boxes, misconceptions, result-sheet reading, checklists via `ibChecklist`, record sheets, the 72-hour response flow, the `data-ib-widget="loss"` loss calculator filled by `ibLossBind`), answers the six farm questions, and keeps 육계/산란계 separate; literature cards use the shared `ibRef`/`ibPm` with Korean sources preferred. Admins can edit it on screen (`ibContentState`, Firebase `premium_content/ib_research/latest.json`): per-section HTML overrides `sections["stage-lecture-section"] = {html, seedHash}` (WYSIWYG contenteditable + HTML mode, cleaned by `ibSanitize`), lecture title/minutes/공개 overrides and added lectures in `lectures["stage-lecture"]`, and the open stage in `stage = {value, seed}` (ignored once `IB_CURRENT_STAGE` in code differs from `seed`). Code-side seed content still shows wherever no override exists; when a seed section changes after an admin edited it, admins see a 「기본 내용이 갱신」 notice (seedHash mismatch). Keep seed section HTML deterministic (no per-viewer state such as checkbox `checked`) or that notice fires falsely.
The scrolling 「NEW」 strip under the tab bar (`renderNewFeatureStrip`) is driven by the `NEW_FEATURES` list in index.html — add one line (key, date, label, where, `go`) at the top whenever a feature/menu ships; each entry shows for `NEW_FEATURE_DAYS` and disappears once the user clicks it or presses ✕ (remembered in localStorage `nf_seen_v1`).
`import_status/latest.json` is a **hand-researched** (news/MAFRA press releases, with source URLs and an `as_of` date) summary of 계란·닭고기 imports shown as the 📦 수입 card in the 공급·소비 tab — not a statistics feed (no customs/UNI-PASS API is connected); update it by editing the file when new reports appear.
Assumption constants live in `PF` (seasonal indices are 경험값, not consumption statistics; consumption data is only used if uploaded).

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
