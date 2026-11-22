# Graph Report - pb  (2026-11-22)

## Corpus Check
- 130 files · ~970,732 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 6 file(s) not represented in the graph (top: (none) 4, .glb 1, .rules 1)

## Summary
- 3340 nodes · 7871 edges · 133 communities (124 shown, 9 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 371 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `bc48eeaf`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- index.inline.js
- ibTag
- attachEvents
- index.js
- hzNearBox
- fetch_animal_drug_news.py
- withStorageTimeout
- fetch_broiler_breeder.py
- dryWarnBox
- esc
- fetch_prices.py
- attachDiseaseEvents
- renderConsultTab
- re
- fetch_poultry_price.py
- fetch_briefing_news.py
- coliFigFor
- renderHusbandryPointsCard
- Architecture: the fetch-script → JSON → dashboard pipeline
- steps
- steps
- fetch_feed_production.py
- gmVirus
- fetch_egg_report.py
- renderHpaiSymptomCard
- steps
- vcFigPress
- json
- pfTabSpecies
- renderSelfCheckPanel
- renderFeedGrainFlow
- gmVirus
- steps
- steps
- steps
- env
- renderFeedPotentialPanel
- renderBroilerCalc
- fetch_jungchu_price.py
- fetch_broiler_breeder.py
- steps
- steps
- steps
- steps
- steps
- steps
- steps
- steps
- steps
- renderLightClock
- pfForecast
- steps
- steps
- steps
- steps
- steps
- steps
- steps
- functions/package.json
- steps
- steps
- steps
- steps
- steps
- steps
- steps
- steps
- steps
- fmtFull
- gmR
- time
- steps
- isBoardAdmin
- steps
- steps
- steps
- fetch_research_papers.py
- render
- ocr_jungchu_table.js
- fetch_usda_crop_progress.py
- fetch_h5n1_human.py
- render
- tradeItem
- fetchNotices
- anomLoadClimatology
- What this is
- callClaude
- curate
- renderDzStatsPanel
- phFig
- vcFigPress
- fetch_poultry_diseases.py
- renderVaccinePanel
- commons.js
- renderGrainPriceCard
- renderVentFinderPanel
- renderSeasonalPanel
- renderVentTab
- switchTab
- gmT
- fetchQiaSearch
- renderWelfareResult
- authDialog
- fetch_notices.py
- drugUseCard
- farmGameCall
- urllib_parse
- isBoardAdmin
- pfSeries
- PriceTableParser
- fetch_taxfree_fuel.py
- renderHpaiKrCard
- getTodayClimate
- renderColiEasy
- rmBind
- sgBind
- pfBind
- pfBuildModel
- isPremiumApproved
- metConvert
- renderDisinfectPanel
- renderWeatherNewsCard
- gmHome
- renderHaccpPanel
- attachDzCustomEvents
- pfGrade
- renderPhPanel
- setupTabArrows
- shareSite
- CLAUDE.md

## God Nodes (most connected - your core abstractions)
1. `esc()` - 215 edges
2. `Architecture: the fetch-script → JSON → dashboard pipeline` - 182 edges
3. `attachEvents()` - 165 edges
4. `render()` - 127 edges
5. `renderPremiumTab()` - 85 edges
6. `gmT()` - 69 edges
7. `gmSvg()` - 66 edges
8. `gmBox()` - 58 edges
9. `fetchWithTimeout()` - 51 edges
10. `ibTag()` - 50 edges

## Surprising Connections (you probably didn't know these)
- `graphify (토큰 절약용 코드 지식 그래프)` --references--> `renderHpaiKrLiveStrip()`  [INFERRED]
  CLAUDE.md → graphify-src/index.inline.js
- `Architecture: the fetch-script → JSON → dashboard pipeline` --references--> `fetchWeatherData()`  [INFERRED]
  CLAUDE.md → functions/index.js
- `Conventions shared across all fetch scripts` --references--> `apply_glossary()`  [INFERRED]
  CLAUDE.md → scripts/translation_glossary.py
- `Working in index.html` --references--> `fetchPoultryPrices()`  [INFERRED]
  CLAUDE.md → graphify-src/index.inline.js
- `Architecture: the fetch-script → JSON → dashboard pipeline` --references--> `premiumMenuItemsFull()`  [INFERRED]
  CLAUDE.md → graphify-src/index.inline.js

## Import Cycles
- None detected.

## Communities (133 total, 9 thin omitted)

### Community 0 - "index.inline.js"
Cohesion: 0.00
Nodes (419): RFC-822, ANOM_MD_START, anomState, ARBORACRES_DATA, AUTUMN_BR_DAILY, AUTUMN_BR_DISEASES, AUTUMN_BR_HUSB, AUTUMN_BR_SYM (+411 more)

### Community 1 - "ibTag"
Cohesion: 0.28
Nodes (62): 1. 전염성기관지염(IB) 차단 AI공동연구팀 (유료서비스 최상단 `ibteam`), ibBox(), ibChecklist(), ibField(), ibFlow(), ibGenomeBar(), ibH(), ibLecture1() (+54 more)

### Community 2 - "attachEvents"
Cohesion: 0.03
Nodes (81): ageDays(), attachEvents(), bodyPartLabel(), calcProductionIndex(), calcRequiredAdg(), callMemberFunction(), cardCandToBackImage(), coliBind() (+73 more)

### Community 3 - "index.js"
Cohesion: 0.09
Nodes (29): admin, ADMIN_EMAILS, AI_DRAFT_KINDS, ANTHROPIC_API_KEY, BOARD_TYPES, casUsage(), { defineSecret }, fetchRssItems() (+21 more)

### Community 4 - "hzNearBox"
Cohesion: 0.06
Nodes (74): 0. 이어받는 세션이 먼저 할 일, 1-2. HPAI ZERO FARM (유료서비스 · AI공동연구팀, `hpaizero`), 2. 최근 완료된 기능(이 세션, 2026-10-08 ~ 10-13, 모두 main 병합), 3. 환경 메모, 작업 인계 노트 (2026-10-13), hkAllFarms(), hkAllWild(), hzAddDays() (+66 more)

### Community 5 - "fetch_animal_drug_news.py"
Cohesion: 0.06
Nodes (52): build_item(), category_guess(), claude(), collect(), friday_of(), main(), parse_json(), pick_with_claude() (+44 more)

### Community 6 - "withStorageTimeout"
Cohesion: 0.07
Nodes (34): boardPostPath(), currentBoardCfg(), deleteFeatureRequest(), deleteMemberProfile(), featureRequestPostPath(), featureRequestRepliesPrefix(), fetchFeatureRequests(), fetchInboxBoardPosts() (+26 more)

### Community 7 - "fetch_broiler_breeder.py"
Cohesion: 0.15
Nodes (10): ask_claude(), clean_outlook(), _img_b64(), kreI_get(), main(), merge_report(), newest_report_id(), plausible() (+2 more)

### Community 8 - "dryWarnBox"
Cohesion: 0.26
Nodes (15): calcDewPointC(), dryWarnBox(), humAlert(), humAlertName(), humBadge(), humChips(), humGaugeSvg(), humIndexNote() (+7 more)

### Community 9 - "esc"
Cohesion: 0.06
Nodes (47): allSites(), boardStatusBadge(), disinfectFlowHtml(), esc(), inModeBar(), lmEggSvg(), lmPhotosHtml(), pfImportHtml() (+39 more)

### Community 10 - "fetch_prices.py"
Cohesion: 0.29
Nodes (9): call_api(), diff(), get_api_key(), ival(), main(), filter_type(), probe_url(), sval() (+1 more)

### Community 11 - "attachDiseaseEvents"
Cohesion: 0.07
Nodes (36): attachDiseaseEvents(), attachDiseaseResultEvents(), countPicks(), currentHpaiAuto(), currentHpaiNews(), currentPicks(), emergNewsSearch(), fetchMonthlyPicks() (+28 more)

### Community 12 - "renderConsultTab"
Cohesion: 0.16
Nodes (19): broilerEquivDay(), fcAlertOn(), fcInputBox(), fcNum(), fcResultCard(), fcVerdict(), feedPotentialStandards(), fmtWaterCell() (+11 more)

### Community 13 - "re"
Cohesion: 0.10
Nodes (26): ai_extract(), _candidates(), clean_quick(), clean_wild(), _date(), fetch_news(), fetch_quick_news(), fetch_table_data() (+18 more)

### Community 14 - "fetch_poultry_price.py"
Cohesion: 0.05
Nodes (45): The SMS dispatch job (not the fetch-script shape above), merge_rows(), fetch_window(), main(), parse_window(), cell_number(), fetch_page(), latest_metric() (+37 more)

### Community 15 - "fetch_briefing_news.py"
Cohesion: 0.10
Nodes (15): clean_text(), fetch_source(), get_with_proxy_fallback(), kst_label(), main(), parse_aflnews(), parse_chuksan(), parse_handon() (+7 more)

### Community 16 - "coliFigFor"
Cohesion: 0.07
Nodes (37): autumnFig(), autumnSvgChain(), autumnSvgEggRule(), autumnSvgLayerSign(), autumnSvgResp(), coliBox(), coliFig(), coliFig2For() (+29 more)

### Community 17 - "renderHusbandryPointsCard"
Cohesion: 0.16
Nodes (16): aviagenTargetTemp(), comfortActions(), dryRhOfDay(), dryUpcomingLine(), hsiInRange(), hsiLevel(), humRhOfDay(), isDryRh() (+8 more)

### Community 18 - "Architecture: the fetch-script → JSON → dashboard pipeline"
Cohesion: 0.08
Nodes (43): Architecture: the fetch-script → JSON → dashboard pipeline, Conventions shared across all fetch scripts, anomPointsHtml(), anomTodayLine(), farmGameBind(), farmGameCloseWin(), farmGameOpenWin(), ibCardify() (+35 more)

### Community 19 - "steps"
Cohesion: 0.06
Nodes (34): concurrency, cancel-in-progress, group, ANTHROPIC_API_KEY, FIREBASE_SERVICE_ACCOUNT_JSON, FORCE, ONCE_KEYWORD, default (+26 more)

### Community 20 - "steps"
Cohesion: 0.06
Nodes (33): description, required, CUSTOMS_ONLY, DATA_GO_KR_KEY, FIREBASE_SERVICE_ACCOUNT_JSON, FULL, SMS_RELAY_SECRET, SMS_RELAY_URL (+25 more)

### Community 21 - "fetch_feed_production.py"
Cohesion: 0.15
Nodes (12): list_all_posts(), main(), _candidates(), fetch_year(), find_attachment(), _get(), group_series(), keep_previous() (+4 more)

### Community 22 - "gmVirus"
Cohesion: 0.25
Nodes (15): dsBug(), dsFigTypes(), dzFigCauseIcon(), gmCoccus(), gmFigGrow(), gmFigMode(), gmFigOrganic(), gmFigShapes() (+7 more)

### Community 23 - "fetch_egg_report.py"
Cohesion: 0.13
Nodes (11): _diag_dump(), download_pdf(), _extract_board_nos(), fetch_detail(), find_latest_board_no_from_list(), find_latest_board_no_via_browser(), get_latest(), load_previous() (+3 more)

### Community 24 - "renderHpaiSymptomCard"
Cohesion: 0.16
Nodes (19): hg(), hgAdminBar(), hgCircled(), hgFmt(), hgItemLocs(), hgPlain(), hgPosByKey(), hgPositions() (+11 more)

### Community 25 - "steps"
Cohesion: 0.07
Nodes (29): ANTHROPIC_API_KEY, FIREBASE_SERVICE_ACCOUNT_JSON, QUICK_EXTRA_URLS, SMS_RELAY_SECRET, SMS_RELAY_URL, runs-on, steps, urls (+21 more)

### Community 26 - "vcFigPress"
Cohesion: 0.38
Nodes (11): vcChick(), vcFan(), vcFig(), vcFigHouse(), vcFigInlet(), vcFigModes(), vcFigPress(), vcFigWhy() (+3 more)

### Community 27 - "json"
Cohesion: 0.07
Nodes (29): load(), main(), v(), build(), day(), fetch_events(), get_json(), is_hpai() (+21 more)

### Community 28 - "pfTabSpecies"
Cohesion: 0.17
Nodes (25): pfBar(), pfChips(), pfControls(), pfHz(), pfImportBrief(), pfInsufficientHtml(), pfKpi(), pfPct1() (+17 more)

### Community 29 - "renderSelfCheckPanel"
Cohesion: 0.18
Nodes (17): commonsImageCredit(), newProductItemImages(), pkgBoxStyle(), pkgChip(), pkgIconCircle(), renderDiseaseBriefPanel(), renderDrugNewsPanel(), renderDrugNewsSites() (+9 more)

### Community 30 - "renderFeedGrainFlow"
Cohesion: 0.08
Nodes (28): fgBadge(), fgDetailRows(), fgImplication(), fgLevelOf(), fgMeter(), fgMoldLevel(), fgMoldStrip(), fgMoldType() (+20 more)

### Community 31 - "gmVirus"
Cohesion: 0.16
Nodes (21): ibBind(), ibData(), ibEffStage(), ibHash(), ibLectureList(), ibLossBind(), ibLossCalc(), ibLossHtml() (+13 more)

### Community 32 - "steps"
Cohesion: 0.07
Nodes (26): concurrency, cancel-in-progress, group, environment, runs-on, steps, name, url (+18 more)

### Community 33 - "steps"
Cohesion: 0.07
Nodes (26): ANTHROPIC_API_KEY, FIREBASE_SERVICE_ACCOUNT_JSON, SMS_RELAY_SECRET, SMS_RELAY_URL, runs-on, steps, timeout-minutes, jobs (+18 more)

### Community 34 - "steps"
Cohesion: 0.08
Nodes (25): concurrency, cancel-in-progress, group, ANTHROPIC_API_KEY, FIREBASE_SERVICE_ACCOUNT_JSON, runs-on, steps, timeout-minutes (+17 more)

### Community 35 - "env"
Cohesion: 0.09
Nodes (25): BOT_TOKEN, CHAT_ID, COMMIT_MSG, COMMIT_URL, WF_NAME, WF_URL, jobs, notify-failure (+17 more)

### Community 36 - "renderFeedPotentialPanel"
Cohesion: 0.11
Nodes (26): bbChartSvg(), bbDelta(), bbMan(), bbMonth(), bbPctOf(), bbYm(), fpBirds(), fpChart() (+18 more)

### Community 37 - "renderBroilerCalc"
Cohesion: 0.14
Nodes (16): bindSmsBox(), brClock(), brDark(), brFmtDate(), brLux(), brSchedule(), brSmsText(), moltSmsText() (+8 more)

### Community 38 - "fetch_jungchu_price.py"
Cohesion: 0.13
Nodes (9): find_image_url(), find_post_url(), _get_bytes(), _get_text(), main(), run_ocr(), collect(), dataset_of() (+1 more)

### Community 39 - "fetch_broiler_breeder.py"
Cohesion: 0.07
Nodes (30): build_forecast(), fit_adult(), _lstsq2(), ratio_estimators(), est(), shift(), annual_vol(), build_grain() (+22 more)

### Community 40 - "steps"
Cohesion: 0.08
Nodes (24): runs-on, steps, FROM_YEAR, TO_YEAR, description, required, from_year, to_year (+16 more)

### Community 41 - "steps"
Cohesion: 0.08
Nodes (24): concurrency, cancel-in-progress, group, ANTHROPIC_API_KEY, FIREBASE_SERVICE_ACCOUNT_JSON, runs-on, steps, jobs (+16 more)

### Community 42 - "steps"
Cohesion: 0.08
Nodes (24): concurrency, cancel-in-progress, group, ANTHROPIC_API_KEY, FIREBASE_SERVICE_ACCOUNT_JSON, permissions, runs-on, steps (+16 more)

### Community 43 - "steps"
Cohesion: 0.08
Nodes (24): concurrency, cancel-in-progress, group, FIREBASE_SERVICE_ACCOUNT_JSON, runs-on, steps, timeout-minutes, jobs (+16 more)

### Community 44 - "steps"
Cohesion: 0.08
Nodes (23): FIREBASE_SERVICE_ACCOUNT_JSON, runs-on, steps, timeout-minutes, jobs, fetch-h5n1-human, name, on (+15 more)

### Community 45 - "steps"
Cohesion: 0.08
Nodes (23): concurrency, cancel-in-progress, group, FIREBASE_SERVICE_ACCOUNT_JSON, permissions, runs-on, steps, jobs (+15 more)

### Community 46 - "steps"
Cohesion: 0.08
Nodes (23): FIREBASE_SERVICE_ACCOUNT_JSON, runs-on, steps, jobs, fetch-taxfree-fuel, name, on, push (+15 more)

### Community 47 - "steps"
Cohesion: 0.08
Nodes (23): FIREBASE_SERVICE_ACCOUNT_JSON, runs-on, steps, timeout-minutes, jobs, fetch-usda-crop-progress, name, on (+15 more)

### Community 48 - "steps"
Cohesion: 0.10
Nodes (20): FIREBASE_SERVICE_ACCOUNT_JSON, runs-on, steps, jobs, fetch-weather-cities, name, on, schedule (+12 more)

### Community 49 - "renderLightClock"
Cohesion: 0.18
Nodes (19): lgChartSvg(), lgClk(), lgClockSvg(), lgCompute(), lgDayLength(), lgDaySchedule(), lgDur(), lgEffectiveLat() (+11 more)

### Community 50 - "pfForecast"
Cohesion: 0.14
Nodes (25): pfBacktestDaily(), pfBacktestMonthly(), pfCalibrate(), pfCalibrationTable(), pfContrib(), pfDailyX(), pfFitDaily(), pfFitMonthly() (+17 more)

### Community 51 - "steps"
Cohesion: 0.09
Nodes (22): FIREBASE_SERVICE_ACCOUNT_JSON, SMS_RELAY_SECRET, SMS_RELAY_URL, runs-on, steps, jobs, fetch-feed-production, name (+14 more)

### Community 52 - "steps"
Cohesion: 0.09
Nodes (22): ANTHROPIC_API_KEY, FIREBASE_SERVICE_ACCOUNT_JSON, runs-on, steps, timeout-minutes, jobs, fetch-research-papers, name (+14 more)

### Community 53 - "steps"
Cohesion: 0.09
Nodes (21): ANTHROPIC_API_KEY, FIREBASE_SERVICE_ACCOUNT_JSON, runs-on, steps, jobs, fetch-industry-news, name, on (+13 more)

### Community 54 - "steps"
Cohesion: 0.09
Nodes (21): FIREBASE_SERVICE_ACCOUNT_JSON, runs-on, steps, jobs, fetch-jungchu-price, name, on, schedule (+13 more)

### Community 55 - "steps"
Cohesion: 0.09
Nodes (21): FIREBASE_SERVICE_ACCOUNT_JSON, runs-on, steps, timeout-minutes, jobs, fetch-poultry-diseases, name, on (+13 more)

### Community 56 - "steps"
Cohesion: 0.09
Nodes (21): EKAPE_API_KEY, FIREBASE_SERVICE_ACCOUNT_JSON, permissions, runs-on, steps, jobs, fetch-prices, name (+13 more)

### Community 57 - "steps"
Cohesion: 0.09
Nodes (21): ANTHROPIC_API_KEY, FIREBASE_SERVICE_ACCOUNT_JSON, runs-on, steps, jobs, fetch-weather-news, name, on (+13 more)

### Community 58 - "functions/package.json"
Cohesion: 0.18
Nodes (13): dependencies, @anthropic-ai/sdk@^0.128.0, firebase-admin@^12.6.0, firebase-functions@^6.0.1, description, engines, node, main (+5 more)

### Community 59 - "steps"
Cohesion: 0.10
Nodes (20): runs-on, steps, FIREBASE_SERVICE_ACCOUNT_JSON, jobs, accumulate, name, on, schedule (+12 more)

### Community 60 - "steps"
Cohesion: 0.10
Nodes (20): FIREBASE_SERVICE_ACCOUNT_JSON, runs-on, steps, jobs, fetch-broiler-price-today, name, on, schedule (+12 more)

### Community 61 - "steps"
Cohesion: 0.10
Nodes (20): FIREBASE_SERVICE_ACCOUNT_JSON, runs-on, steps, jobs, fetch-egg-report, name, on, schedule (+12 more)

### Community 62 - "steps"
Cohesion: 0.10
Nodes (20): FIREBASE_SERVICE_ACCOUNT_JSON, runs-on, steps, jobs, fetch-grain-price, name, on, schedule (+12 more)

### Community 63 - "steps"
Cohesion: 0.10
Nodes (20): FIREBASE_SERVICE_ACCOUNT_JSON, runs-on, steps, jobs, fetch-hpai-risk, name, on, schedule (+12 more)

### Community 64 - "steps"
Cohesion: 0.10
Nodes (20): FIREBASE_SERVICE_ACCOUNT_JSON, runs-on, steps, jobs, fetch-layer-stats, name, on, schedule (+12 more)

### Community 65 - "steps"
Cohesion: 0.10
Nodes (20): FIREBASE_SERVICE_ACCOUNT_JSON, permissions, runs-on, steps, jobs, fetch-news, name, on (+12 more)

### Community 66 - "steps"
Cohesion: 0.10
Nodes (20): FIREBASE_SERVICE_ACCOUNT_JSON, permissions, runs-on, steps, jobs, fetch-notices, name, on (+12 more)

### Community 67 - "steps"
Cohesion: 0.10
Nodes (20): FIREBASE_SERVICE_ACCOUNT_JSON, runs-on, steps, jobs, fetch-poultry-price, name, on, schedule (+12 more)

### Community 68 - "fmtFull"
Cohesion: 0.13
Nodes (21): allCoins(), allStocks(), fmtDate(), fmtFull(), genLivestock7(), genWeekData(), getLast7Days(), last7DayInfos() (+13 more)

### Community 69 - "gmR"
Cohesion: 0.20
Nodes (14): dzAutoFig(), dzFigTiles(), dzFigWrap(), dzFigWrapN(), gmAb(), gmCellInner(), gmFigHistory(), gmFlag() (+6 more)

### Community 70 - "time"
Cohesion: 0.15
Nodes (15): customs_get(), customs_variants(), fetch_comtrade(), fetch_customs(), http_get(), main(), month_list(), convert() (+7 more)

### Community 71 - "steps"
Cohesion: 0.10
Nodes (19): FIREBASE_SERVICE_ACCOUNT_JSON, SMS_RELAY_SECRET, SMS_RELAY_URL, jobs, send, name, on, schedule (+11 more)

### Community 72 - "isBoardAdmin"
Cohesion: 0.15
Nodes (17): diseaseListing(), diseaseMatches(), diseaseSnippet(), dzCategories(), dzCatOf(), dzExtraFigs(), dzExtraRefs(), dzFigSpec() (+9 more)

### Community 73 - "steps"
Cohesion: 0.11
Nodes (17): runs-on, steps, SMS_RELAY_SECRET, SMS_RELAY_URL, jobs, backfill-feed, name, on (+9 more)

### Community 74 - "steps"
Cohesion: 0.11
Nodes (17): FIREBASE_SERVICE_ACCOUNT_JSON, jobs, sync-storage, name, on, push, workflow_dispatch, branches (+9 more)

### Community 75 - "steps"
Cohesion: 0.11
Nodes (17): TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, jobs, send, name, on, schedule, workflow_dispatch (+9 more)

### Community 76 - "fetch_research_papers.py"
Cohesion: 0.13
Nodes (14): build_category(), efetch_articles(), esearch_pmids(), fallback_translation(), google_translate(), load_previous(), main(), _text() (+6 more)

### Community 77 - "render"
Cohesion: 0.11
Nodes (34): buildSmsDigestTextAsync(), currentPremiumMenuItems(), fetchAllSmsSubscriptions(), fetchDiseaseDisinfectants(), fetchDrugUse(), fetchFarmFaq(), fetchFarmFinderCases(), fetchIbContent() (+26 more)

### Community 78 - "ocr_jungchu_table.js"
Cohesion: 0.17
Nodes (15): sharp, tesseract.js, { createWorker }, isRowValid(), main(), ocrTableRows(), parseRow(), sharp (+7 more)

### Community 79 - "fetch_usda_crop_progress.py"
Cohesion: 0.23
Nodes (9): fetch_text(), history_point(), list_releases(), main(), _num(), parse_report(), split_sections(), table_rows() (+1 more)

### Community 80 - "fetch_h5n1_human.py"
Cohesion: 0.21
Nodes (11): download(), main(), read_csv_bytes(), to_int(), build(), _clean_name(), find_table_page(), _int() (+3 more)

### Community 81 - "render"
Cohesion: 0.07
Nodes (52): Data is also mirrored to Firebase Storage (so the repo can go private), getPublicContent(), anomLoadEnsemble(), anomRun(), dataDatasetOf(), dzStatsBind(), emergAnalyze(), emergEsearch() (+44 more)

### Community 82 - "tradeItem"
Cohesion: 0.17
Nodes (16): pfTon(), renderTradeInPriceTab(), renderTradePanel(), tradeBadge(), tradeItem(), tradeKpi(), tradeModel(), tradeMoney() (+8 more)

### Community 83 - "fetchNotices"
Cohesion: 0.26
Nodes (13): Working in index.html, fetchDabomPrices(), fetchEconNews(), fetchNotices(), fetchOneSite(), fetchPolicyNews(), fmtKST(), loadNoticeCache() (+5 more)

### Community 84 - "anomLoadClimatology"
Cohesion: 0.47
Nodes (6): anomCompute(), anomDoy(), anomLoadClimatology(), anomMean(), anomPct(), anomSd()

### Community 85 - "What this is"
Cohesion: 0.21
Nodes (15): What this is, assertAdmin(), deleteMemberAccount(), getApprovedMembers(), getBoardPosts(), getMemberProfiles(), getSmsSubscriptions(), readJsonFile() (+7 more)

### Community 86 - "callClaude"
Cohesion: 0.24
Nodes (11): analyzeNecropsyPhotos(), Anthropic, callClaude(), chickenChat(), chickenChatLength(), chickenChatPersona(), extractMagazineText(), generateAiDraft() (+3 more)

### Community 87 - "curate"
Cohesion: 0.15
Nodes (6): ai_picks(), cluster(), curate(), curate_only(), rule_pick(), title_tokens()

### Community 88 - "renderDzStatsPanel"
Cohesion: 0.40
Nodes (6): dzN(), dzStatsBars(), dzStatsCell(), dzStatsLastMonth(), dzStatsSum(), renderDzStatsPanel()

### Community 89 - "phFig"
Cohesion: 0.40
Nodes (10): phArrow(), phFig(), phFigCirc(), phFigDigest(), phFigExcrete(), phFigHormone(), phFigNeuro(), phFigRepro() (+2 more)

### Community 90 - "vcFigPress"
Cohesion: 0.20
Nodes (14): vcFmt(), vcInletOut(), vcInterp(), vcKg(), vcNeed(), vcPerOut(), vcR100(), vcRange() (+6 more)

### Community 91 - "fetch_poultry_diseases.py"
Cohesion: 0.12
Nodes (10): get(), load_extra(), load_previous(), main(), merge_only(), parse_detail(), parse_index(), save() (+2 more)

### Community 92 - "renderVaccinePanel"
Cohesion: 0.15
Nodes (19): bodyPartByKey(), currentVaccinePrograms(), pkgCardHtml(), pkgColor(), pkgColorOf(), pkgColorPickerHtml(), pkgReadColor(), pkgValidColor() (+11 more)

### Community 93 - "commons.js"
Cohesion: 0.43
Nodes (7): fetchCandidateImage(), findCommonsCandidates(), IMAGE_MIME, searchCommons(), stripHtml(), thumbAt(), findCardImage()

### Community 94 - "renderGrainPriceCard"
Cohesion: 0.48
Nodes (7): gpCol(), gpDir(), gpPct(), gpRange(), gpSpark(), renderGrainPriceCard(), renderGrainPricePanel()

### Community 95 - "renderVentFinderPanel"
Cohesion: 0.28
Nodes (9): calcHumidityRatio(), calcVentilationRate(), getFeedIntakeFor(), getFeedIntakeForCurrent(), getTargetTempForAge(), parseAgeRangeLabel(), renderVentCalcPanel(), renderVentFinderPanel() (+1 more)

### Community 96 - "renderSeasonalPanel"
Cohesion: 0.13
Nodes (26): buildSmsDigestText(), currentFinderCases(), currentSeasonalPackages(), currentTreatmentPackages(), finderCasesForCategory(), finderCasesForSpecies(), finderCategoriesFor(), finderSpeciesLabel() (+18 more)

### Community 97 - "renderVentTab"
Cohesion: 0.25
Nodes (8): anomIsCold(), anomIsHot(), anomTodayJudge(), determineHumidityStage(), determineVentStage(), renderVentTab(), st0name(), ventWinterStage()

### Community 98 - "switchTab"
Cohesion: 0.12
Nodes (22): consultEnsureWeather(), consultWxBind(), consultWxGate(), emergSendToNews(), fetchHpaiNews(), fetchStockPrices(), fetchUpbitData(), fetchWeather() (+14 more)

### Community 99 - "gmT"
Cohesion: 0.16
Nodes (51): dsFigBirds(), dsFigFlow(), dsFigFume(), gmArrow(), gmBox(), gmE(), gmFigAbAg(), gmFigAst() (+43 more)

### Community 100 - "fetchQiaSearch"
Cohesion: 0.06
Nodes (47): attachDrugDetails(), bindDrugPickerEvents(), choseongMatchIndex(), closeDrugPicker(), dropExportOnly(), drugEfficacySnippet(), drugFormCategory(), drugModePlaceholder() (+39 more)

### Community 101 - "renderWelfareResult"
Cohesion: 0.43
Nodes (7): renderWelfarePanel(), renderWelfareResult(), wfBroilerRows(), wfFmt(), wfLayerRows(), wfNum(), wfRow()

### Community 102 - "authDialog"
Cohesion: 0.67
Nodes (3): authDialog(), premiumResetPassword(), premiumSignInEmail()

### Community 103 - "fetch_notices.py"
Cohesion: 0.14
Nodes (11): fetch_channel(), main(), parse_date(), clean(), fetch_board(), get_html(), main(), parse_chicken_assoc() (+3 more)

### Community 104 - "drugUseCard"
Cohesion: 0.40
Nodes (5): drugUseCard(), drugUseKindBadge(), drugUseKindColor(), drugUseSafeUrl(), drugUseSection()

### Community 105 - "farmGameCall"
Cohesion: 0.39
Nodes (8): farmGameCall(), farmGameErrMsg(), farmGameNickKey(), farmGameUser(), list(), load(), remove(), save()

### Community 106 - "urllib_parse"
Cohesion: 0.12
Nodes (8): fetch_html(), main(), parse_price_table(), fetch_html(), main(), normalize_date(), parse_egg_price_html(), RowParser

### Community 107 - "isBoardAdmin"
Cohesion: 0.07
Nodes (31): currentFarmFaq(), currentMagazineNotes(), currentStudyDecks(), drugUseAllKinds(), drugUseBind(), drugUseForm(), drugUseItems(), drugUseNewDraft() (+23 more)

### Community 108 - "pfSeries"
Cohesion: 0.16
Nodes (19): pfAdminHtml(), pfBanner(), pfClean(), pfDemoData(), pfDiagram(), pfEvidence(), pfFeedMonths(), pfFmtN() (+11 more)

### Community 110 - "fetch_taxfree_fuel.py"
Cohesion: 0.25
Nodes (6): fetch_html(), main(), parse(), day(), parse_day(), year_ago()

### Community 113 - "renderHpaiKrCard"
Cohesion: 0.15
Nodes (23): flySrcLinks(), h5hYearChart(), hkCount(), hkFarms(), hkFmt(), hkInPeriod(), hkMonth(), hkNumLabel() (+15 more)

### Community 114 - "getTodayClimate"
Cohesion: 0.50
Nodes (4): calcHeatStressIndex(), calcWetBulbC(), getTodayClimate(), renderWetBulbPanel()

### Community 115 - "renderColiEasy"
Cohesion: 0.39
Nodes (8): easyBtn(), easyCard(), easyHero(), easyList(), easyStep(), easyTwo(), renderColiEasy(), renderHzEasy()

### Community 116 - "rmBind"
Cohesion: 0.67
Nodes (4): flyBind(), flyCensusTxt(), flyLoadLeaflet(), rmBind()

### Community 117 - "sgBind"
Cohesion: 0.14
Nodes (14): sgAutumnSeed(), sgBase(), sgBind(), sgDraftToGuide(), sgEffective(), sgHusbToText(), sgIssuesToText(), sgOpenEdit() (+6 more)

### Community 118 - "pfBind"
Cohesion: 0.19
Nodes (14): pfApplyLocal(), pfBind(), pfDownload(), pfIngest(), pfLog(), pfMergeRows(), pfMonthly(), pfNormDate() (+6 more)

### Community 119 - "pfBuildModel"
Cohesion: 0.50
Nodes (4): pfBuildModel(), pfClip(), pfProbs(), pfYoY()

### Community 120 - "isPremiumApproved"
Cohesion: 0.07
Nodes (38): fmtLunar(), isEmbedded(), isPremiumApproved(), kkokoBumpUsage(), kkokoCharacterBlock(), kkokoDailyLimit(), kkokoDisplayName(), kkokoGreeting() (+30 more)

### Community 121 - "metConvert"
Cohesion: 0.50
Nodes (4): metConvert(), metEntryPrecip(), metEntrySymbol(), metSymbolToWmo()

### Community 122 - "renderDisinfectPanel"
Cohesion: 0.18
Nodes (19): dilBind(), dilCalc(), dilFmt(), dilResultHtml(), disinfectProductsToText(), dsBanner(), dsBasic(), dsDisease() (+11 more)

### Community 124 - "renderWeatherNewsCard"
Cohesion: 0.40
Nodes (5): renderWeatherNewsCard(), wnAgo(), wnCard(), wnLink(), wnThin()

### Community 125 - "gmHome"
Cohesion: 0.16
Nodes (15): dsBind(), GM_DIRT(), gmBind(), gmDilBox(), gmDilOut(), gmFigFarm(), gmFinal(), gmHome() (+7 more)

### Community 127 - "attachDzCustomEvents"
Cohesion: 0.14
Nodes (18): attachDzCustomEvents(), attachDzPhotoEvents(), boardShrinkPhoto(), buildDiseaseSearch(), dzCustomToEntry(), dzFormRead(), dzMergeCustom(), dzParseAiDraft() (+10 more)

### Community 132 - "CLAUDE.md"
Cohesion: 0.40
Nodes (3): Commands, graphify (토큰 절약용 코드 지식 그래프), Workflow preference (owner's standing instruction)

## Knowledge Gaps
- **1 isolated node(s):** `RFC-822`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1170 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Architecture: the fetch-script → JSON → dashboard pipeline` connect `Architecture: the fetch-script → JSON → dashboard pipeline` to `ibTag`, `attachEvents`, `index.js`, `CLAUDE.md`, `fetch_animal_drug_news.py`, `fetch_broiler_breeder.py`, `dryWarnBox`, `esc`, `attachDiseaseEvents`, `renderConsultTab`, `re`, `fetch_poultry_price.py`, `coliFigFor`, `renderHusbandryPointsCard`, `gmVirus`, `pfTabSpecies`, `renderFeedGrainFlow`, `gmVirus`, `renderFeedPotentialPanel`, `renderLightClock`, `pfForecast`, `gmR`, `time`, `isBoardAdmin`, `render`, `render`, `tradeItem`, `What this is`, `callClaude`, `curate`, `renderDzStatsPanel`, `vcFigPress`, `renderVaccinePanel`, `renderVentFinderPanel`, `renderVentTab`, `switchTab`, `gmT`, `fetchQiaSearch`, `isBoardAdmin`, `pfSeries`, `renderHpaiKrCard`, `getTodayClimate`, `pfBuildModel`, `isPremiumApproved`, `metConvert`, `renderDisinfectPanel`, `gmHome`, `attachDzCustomEvents`?**
  _High betweenness centrality (0.194) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `esc()` (e.g. with `dzFigTiles()` and `renderBizFooterLine()`) actually correct?**
  _`esc()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `RFC-822` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `index.inline.js` be split into smaller, more focused modules?**
  _Cohesion score 0.0045871559633027525 - nodes in this community are weakly interconnected._
- **Why does `What this is` connect `What this is` to `index.js`, `CLAUDE.md`, `renderBroilerCalc`, `gmR`, `withStorageTimeout`, `isBoardAdmin`, `fetch_broiler_breeder.py`, `isBoardAdmin`, `render`, `callClaude`, `gmVirus`, `isPremiumApproved`, `fetch_poultry_diseases.py`, `attachDzCustomEvents`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Are the 178 inferred relationships involving `Architecture: the fetch-script → JSON → dashboard pipeline` (e.g. with `analyzeNecropsyPhotos()` and `fetchRssItems()`) actually correct?**
  _`Architecture: the fetch-script → JSON → dashboard pipeline` has 178 INFERRED edges - model-reasoned connections that need verification._
- **Should `attachEvents` be split into smaller, more focused modules?**
  _Cohesion score 0.0345679012345679 - nodes in this community are weakly interconnected._