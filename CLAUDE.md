# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-page static dashboard (`index.html`, ~4300 lines, no build step) for livestock/poultry
farm consulting: market prices (egg, chicken, pig, cattle), stocks/FX/grain futures, industry news,
and association notices. It's a Korean-language site (농장동물 컨설팅) deployed as a static GitHub
Pages-style site — `index.html` fetches its own JSON data files straight from
`raw.githubusercontent.com/khmass-liturgy/pb/main/...` at runtime (see the `*_JSON_URL` constants
around index.html:420-530).

The data those JSON files contain is **not** produced at page-load time by the browser for most
panels. Instead, scheduled GitHub Actions workflows run Python scripts on a cron, which scrape/call
external sources server-side and commit the resulting JSON back into this repo. The browser just
reads the committed JSON. A few panels (news RSS, some board scraping) still fetch directly from the
browser through public CORS proxies — see `CORS_PROXIES` in index.html.

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
| Egg weekly supply/demand report (PDF) | `scripts/fetch_egg_report.py` | `egg_report/latest.json` (+ `.pdf`, `debug.html`) | — | — |
| Chicken price board (chicken.or.kr) | `scripts/fetch_egg_price.py` | `chicken_price/latest.json` | — | — |
| Stocks/FX/grain futures (Yahoo Finance) | `scripts/fetch_market.py` | `market/quotes.json` | fetch-market.yml | weekdays hourly during KR+US market hours, weekends 1x |
| Briefing news (multi-outlet scrape) | `scripts/fetch_briefing_news.py` | `news/briefing.json` | fetch-briefing-news.yml | weekdays every 2h, weekends 08:00 |
| General news (RSS) | `scripts/fetch_news.py` | `news/news.json` | fetch-news.yml | daily 08:00 |
| Association notices | `scripts/fetch_notices.py` | `notices/notices.json` | fetch-notices.yml | daily 08:00 |

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
  (they use `requests`).

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
