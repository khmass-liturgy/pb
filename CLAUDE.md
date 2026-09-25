# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
  `backImage` with artist/license/source so the back face can show the attribution CC BY requires.
  These need the Firebase secret `ANTHROPIC_API_KEY` (a separate key from the GitHub Actions secret
  of the same name used by `fetch_research_papers.py`; set with
  `firebase functions:secrets:set ANTHROPIC_API_KEY --project chicken-dx`).
- `storage.rules` guards Firebase Storage, used for two things that can't go through the
  public-GitHub-commit pattern below because the data is private, not public content:
  - the 온라인 진단/상담/컨설팅 boards (`PREMIUM_BOARDS` in index.html) store member-submitted
    posts, photos and the vet's replies under `premium_board/{boardType}/{uid}/{postId}/`, readable
    only by that post's owner and admins.
  - `premium_members/{email}/info.json` holds each member's name/phone/join date — admin-only
    read/write. `premium/approved.json` (public GitHub repo) intentionally keeps only
    `email`/`expires` (whatever `isPremiumApproved()` needs client-side); it used to also hold
    name/phone until that was recognized as a PII leak (anyone can read a public repo's files
    without logging in) and split out here.
  - `premium_content/{dataset}/latest.json` holds the four premium-only datasets (상황별 처방,
    계절별 패키지, 농장 맞춤 찾기, 온라인 자가진단— `treatment_packages`/`seasonal_packages`/
    `farm_finder`/`self_check`). These used to be public GitHub files like everything else in this
    repo, which meant anyone who found the raw URL could read paid content without logging in —
    moved here so only approved members (or admins) can read it, and only admins can write it.
    Approval is checked via a Firebase Auth **custom claim** (`request.auth.token.approved`), since
    Storage rules can't query `premium/approved.json`'s dynamic member list directly. The
    `setMemberApproval` Cloud Function sets that claim, called from index.html's member-save handler
    every time a member is added or edited — so a membership's `expires` field only actually takes
    effect at the Storage layer the next time that member's record is saved (not automatically at
    midnight on the expiry date; whoever edits members should re-save a lapsed member to revoke
    Storage access, or delete them outright). The claim only applies on the member's next token
    refresh (up to ~1h) unless index.html forces one via `getIdToken(true)`, which it does right
    after a login is found to be approved.
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

### The SMS dispatch job (not the fetch-script shape above)

`scripts/send_sms_subscriptions.py` + `.github/workflows/send-sms-subscriptions.yml` (daily 08:30
KST) is a different shape from the table above — it doesn't read an external source or write JSON
into this repo. It processes the 유료서비스 "자동 문자 발송 신청" subscriptions (member picks a
menu — 계절별 패키지/기술탐구/상황별 처방 — and an interval) stored in Firebase Storage under
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
