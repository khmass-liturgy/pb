# Graph Report - pb  (2026-11-22)

## Corpus Check
- 130 files · ~972,823 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 6 file(s) not represented in the graph (top: (none) 4, .glb 1, .rules 1)

## Summary
- 3341 nodes · 7880 edges · 140 communities (133 shown, 7 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 373 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `fc12f6b5`
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
- send_sms_subscriptions.py
- dzAutoFig
- esc
- sys
- attachDiseaseEvents
- renderConsultTab
- re
- fetch_poultry_price.py
- fetch_briefing_news.py
- coliFigFor
- renderVentTab
- Architecture: the fetch-script → JSON → dashboard pipeline
- steps
- steps
- fetch_feed_production.py
- fetch_grain_quality.py
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
- renderHpaiZeroPanel
- time
- steps
- isBoardAdmin
- steps
- steps
- steps
- fetch_research_papers.py
- render
- ocr_jungchu_table.js
- gmVirus
- fetch_h5n1_human.py
- render
- tradeItem
- fetch_weather_news.py
- anomLoadClimatology
- What this is
- fetchDiseases
- renderSeasonalPanel
- renderDzStatsPanel
- phFig
- vcFigPress
- fetch_poultry_diseases.py
- hzBox
- commons.js
- renderGrainPriceCard
- renderVentFinderPanel
- renderVaccinePanel
- renderHusbandryPointsCard
- switchTab
- gmT
- fetchQiaSearch
- renderWelfareResult
- authDialog
- fetch_notices.py
- fetch_hpai_risk.py
- farmGameCall
- urllib_parse
- drugUseBind
- renderFarmFinderPanel
- PriceTableParser
- fetch_taxfree_fuel.py
- renderHpaiKrCard
- renderStudyPanel
- hzToday
- dryWarnBox
- sgOpenEdit
- pfBind
- pfSeries
- isPremiumApproved
- callClaude
- renderDisinfectPanel
- renderWeatherNewsCard
- gmFig
- renderHaccpPanel
- attachDzCustomEvents
- renderDrugSearchPanel
- renderColiEasy
- renderWeatherBody
- RowParser
- CLAUDE.md
- sortVaccineSchedule
- isBoardAdmin
- renderProductionIndexPanel
- renderHzTasks
- renderPremiumLoginHints
- metConvert
- sgDraftToGuide

## God Nodes (most connected - your core abstractions)
1. `esc()` - 215 edges
2. `Architecture: the fetch-script → JSON → dashboard pipeline` - 184 edges
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
- `Architecture: the fetch-script → JSON → dashboard pipeline` --references--> `premiumMenuItemsFull()`  [INFERRED]
  CLAUDE.md → graphify-src/index.inline.js
- `Architecture: the fetch-script → JSON → dashboard pipeline` --references--> `premiumMenuCats()`  [INFERRED]
  CLAUDE.md → graphify-src/index.inline.js

## Import Cycles
- None detected.

## Communities (140 total, 7 thin omitted)

### Community 0 - "index.inline.js"
Cohesion: 0.00
Nodes (429): RFC-822, ANOM_MD_START, anomState, ARBORACRES_DATA, AUTUMN_BR_DAILY, AUTUMN_BR_DISEASES, AUTUMN_BR_HUSB, AUTUMN_BR_SYM (+421 more)

### Community 1 - "ibTag"
Cohesion: 0.28
Nodes (62): 1. 전염성기관지염(IB) 차단 AI공동연구팀 (유료서비스 최상단 `ibteam`), ibBox(), ibChecklist(), ibField(), ibFlow(), ibGenomeBar(), ibH(), ibLecture1() (+54 more)

### Community 2 - "attachEvents"
Cohesion: 0.03
Nodes (81): attachEvents(), bodyPartLabel(), callMemberFunction(), cardCandToBackImage(), coliBind(), coliSave(), createFirebaseMemberAccount(), currentDiseaseDisinfectants() (+73 more)

### Community 3 - "index.js"
Cohesion: 0.09
Nodes (32): admin, ADMIN_EMAILS, AI_DRAFT_KINDS, ANTHROPIC_API_KEY, BOARD_TYPES, casUsage(), chickenChat(), chickenChatLength() (+24 more)

### Community 4 - "hzNearBox"
Cohesion: 0.23
Nodes (23): hkAllFarms(), hkAllWild(), hzAddDays(), hzBacktest(), hzBacktest2(), hzBtDates(), hzDensBacktest(), hzDensityPoints() (+15 more)

### Community 5 - "fetch_animal_drug_news.py"
Cohesion: 0.06
Nodes (48): build_item(), category_guess(), claude(), collect(), friday_of(), main(), parse_json(), pick_with_claude() (+40 more)

### Community 6 - "withStorageTimeout"
Cohesion: 0.06
Nodes (38): attachDzPhotoEvents(), boardPostPath(), boardShrinkPhoto(), currentBoardCfg(), deleteFeatureRequest(), deleteMemberProfile(), featureRequestPostPath(), featureRequestRepliesPrefix() (+30 more)

### Community 7 - "send_sms_subscriptions.py"
Cohesion: 0.15
Nodes (22): The SMS dispatch job (not the fetch-script shape above), _arrow(), build_digest(), current_season(), digest_egg_report(), digest_feed_production(), digest_grain_quality(), digest_hpai_kr() (+14 more)

### Community 8 - "dzAutoFig"
Cohesion: 0.18
Nodes (14): dzAutoFig(), dzFigTiles(), dzFigWrap(), dzFigWrapN(), lcCard(), renderWyPanel(), wyFigMap(), wyHen() (+6 more)

### Community 9 - "esc"
Cohesion: 0.07
Nodes (48): allSites(), boardStatusBadge(), disinfectFlowHtml(), esc(), flySrcLinks(), hpaiBadge(), hpaiSplitBar(), hpaiTagline() (+40 more)

### Community 10 - "sys"
Cohesion: 0.11
Nodes (16): day_key(), fetch_one(), main(), call_api(), diff(), get_api_key(), ival(), main() (+8 more)

### Community 11 - "attachDiseaseEvents"
Cohesion: 0.06
Nodes (42): attachDiseaseEvents(), countPicks(), currentPicks(), dzStatsBind(), emergAnalyze(), emergEsearch(), emergEsummary(), emergFmtDate() (+34 more)

### Community 12 - "renderConsultTab"
Cohesion: 0.16
Nodes (19): broilerEquivDay(), fcAlertOn(), fcInputBox(), fcNum(), fcResultCard(), fcVerdict(), feedPotentialStandards(), fmtWaterCell() (+11 more)

### Community 13 - "re"
Cohesion: 0.08
Nodes (35): ai_extract(), _candidates(), clean_quick(), clean_wild(), _date(), fetch_news(), fetch_quick_news(), fetch_table_data() (+27 more)

### Community 14 - "fetch_poultry_price.py"
Cohesion: 0.11
Nodes (19): cell_number(), fetch_page(), latest_metric(), load_previous(), main(), normalize_date(), normalize_week_start(), normalize_year_month() (+11 more)

### Community 15 - "fetch_briefing_news.py"
Cohesion: 0.10
Nodes (15): clean_text(), fetch_source(), get_with_proxy_fallback(), kst_label(), main(), parse_aflnews(), parse_chuksan(), parse_handon() (+7 more)

### Community 16 - "coliFigFor"
Cohesion: 0.07
Nodes (37): autumnFig(), autumnSvgChain(), autumnSvgEggRule(), autumnSvgLayerSign(), autumnSvgResp(), coliBox(), coliFig(), coliFig2For() (+29 more)

### Community 17 - "renderVentTab"
Cohesion: 0.20
Nodes (16): anomIsCold(), anomIsHot(), anomTodayJudge(), calcDewPointC(), determineHumidityStage(), determineVentStage(), dryUpcomingLine(), humAlert() (+8 more)

### Community 18 - "Architecture: the fetch-script → JSON → dashboard pipeline"
Cohesion: 0.11
Nodes (33): Architecture: the fetch-script → JSON → dashboard pipeline, Conventions shared across all fetch scripts, farmGameBind(), farmGameCloseWin(), farmGameOpenWin(), ibCardify(), ibIsHead(), ibSlim() (+25 more)

### Community 19 - "steps"
Cohesion: 0.06
Nodes (34): concurrency, cancel-in-progress, group, ANTHROPIC_API_KEY, FIREBASE_SERVICE_ACCOUNT_JSON, FORCE, ONCE_KEYWORD, default (+26 more)

### Community 20 - "steps"
Cohesion: 0.06
Nodes (33): description, required, CUSTOMS_ONLY, DATA_GO_KR_KEY, FIREBASE_SERVICE_ACCOUNT_JSON, FULL, SMS_RELAY_SECRET, SMS_RELAY_URL (+25 more)

### Community 21 - "fetch_feed_production.py"
Cohesion: 0.13
Nodes (12): list_all_posts(), main(), _candidates(), fetch_year(), find_attachment(), _get(), group_series(), keep_previous() (+4 more)

### Community 22 - "fetch_grain_quality.py"
Cohesion: 0.14
Nodes (12): build_baseline(), build_region(), ensure_baseline(), fetch_rows(), load_json(), main(), mean_sd(), mold_scores() (+4 more)

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
Cohesion: 0.12
Nodes (18): load(), main(), v(), merge_rows(), base_params(), build(), slot(), species() (+10 more)

### Community 28 - "pfTabSpecies"
Cohesion: 0.19
Nodes (23): pfBar(), pfChips(), pfControls(), pfHz(), pfImportBrief(), pfInsufficientHtml(), pfKpi(), pfPct1() (+15 more)

### Community 29 - "renderSelfCheckPanel"
Cohesion: 0.19
Nodes (17): bodyPartByKey(), newProductItemImages(), pkgBoxStyle(), pkgChip(), pkgIconCircle(), renderDiseaseBriefPanel(), renderDrugNewsPanel(), renderDrugNewsSites() (+9 more)

### Community 30 - "renderFeedGrainFlow"
Cohesion: 0.08
Nodes (28): fgBadge(), fgDetailRows(), fgImplication(), fgLevelOf(), fgMeter(), fgMoldLevel(), fgMoldStrip(), fgMoldType() (+20 more)

### Community 31 - "gmVirus"
Cohesion: 0.17
Nodes (20): ibBind(), ibData(), ibEffStage(), ibHash(), ibLectureList(), ibLossBind(), ibLossCalc(), ibLossHtml() (+12 more)

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
Cohesion: 0.15
Nodes (15): bindSmsBox(), brClock(), brDark(), brFmtDate(), brLux(), brSchedule(), brSmsText(), moltSmsText() (+7 more)

### Community 38 - "fetch_jungchu_price.py"
Cohesion: 0.13
Nodes (9): find_image_url(), find_post_url(), _get_bytes(), _get_text(), main(), run_ocr(), collect(), dataset_of() (+1 more)

### Community 39 - "fetch_broiler_breeder.py"
Cohesion: 0.09
Nodes (28): ask_claude(), build_forecast(), clean_outlook(), fit_adult(), _img_b64(), kreI_get(), _lstsq2(), main() (+20 more)

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
Cohesion: 0.16
Nodes (21): lgChartSvg(), lgClk(), lgClockSvg(), lgCompute(), lgDayLength(), lgDaySchedule(), lgDur(), lgEffectiveLat() (+13 more)

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

### Community 69 - "renderHpaiZeroPanel"
Cohesion: 0.14
Nodes (17): 0. 이어받는 세션이 먼저 할 일, 1-2. HPAI ZERO FARM (유료서비스 · AI공동연구팀, `hpaizero`), 2. 최근 완료된 기능(이 세션, 2026-10-08 ~ 10-13, 모두 main 병합), 3. 환경 메모, 작업 인계 노트 (2026-10-13), hzCard(), hzGrid(), hzHomeStatus() (+9 more)

### Community 70 - "time"
Cohesion: 0.11
Nodes (18): fetch_window(), main(), parse_window(), customs_get(), customs_variants(), fetch_comtrade(), fetch_customs(), http_get() (+10 more)

### Community 71 - "steps"
Cohesion: 0.10
Nodes (19): FIREBASE_SERVICE_ACCOUNT_JSON, SMS_RELAY_SECRET, SMS_RELAY_URL, jobs, send, name, on, schedule (+11 more)

### Community 72 - "isBoardAdmin"
Cohesion: 0.13
Nodes (22): attachDiseaseResultEvents(), diseaseListing(), diseaseMatches(), diseaseSnippet(), dzCategories(), dzCatOf(), dzExtraFigs(), dzExtraRefs() (+14 more)

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
Cohesion: 0.10
Nodes (44): buildSmsDigestTextAsync(), fetchAllSmsSubscriptions(), fetchDiseaseBrief(), fetchDiseaseDisinfectants(), fetchDrugUse(), fetchFarmFaq(), fetchFarmFinderCases(), fetchGrainPrice() (+36 more)

### Community 78 - "ocr_jungchu_table.js"
Cohesion: 0.17
Nodes (15): sharp, tesseract.js, { createWorker }, isRowValid(), main(), ocrTableRows(), parseRow(), sharp (+7 more)

### Community 79 - "gmVirus"
Cohesion: 0.22
Nodes (17): dzFigCauseIcon(), gmAb(), gmCellInner(), gmCoccus(), gmFigGrow(), gmFigHistory(), gmFigMode(), gmFigOrganic() (+9 more)

### Community 80 - "fetch_h5n1_human.py"
Cohesion: 0.21
Nodes (11): download(), main(), read_csv_bytes(), to_int(), build(), _clean_name(), find_table_page(), _int() (+3 more)

### Community 81 - "render"
Cohesion: 0.07
Nodes (44): Data is also mirrored to Firebase Storage (so the repo can go private), Working in index.html, getPublicContent(), dataDatasetOf(), fetchBroilerBreeder(), fetchBroilerPriceToday(), fetchChickenPrices(), fetchDabomPrices() (+36 more)

### Community 82 - "tradeItem"
Cohesion: 0.17
Nodes (16): pfTon(), renderTradeInPriceTab(), renderTradePanel(), tradeBadge(), tradeItem(), tradeKpi(), tradeModel(), tradeMoney() (+8 more)

### Community 83 - "fetch_weather_news.py"
Cohesion: 0.23
Nodes (10): ai_summary(), cap_items(), enrich(), main(), order_tags(), relevant(), search(), tags_for() (+2 more)

### Community 84 - "anomLoadClimatology"
Cohesion: 0.47
Nodes (6): anomCompute(), anomDoy(), anomLoadClimatology(), anomMean(), anomPct(), anomSd()

### Community 85 - "What this is"
Cohesion: 0.26
Nodes (12): What this is, assertAdmin(), deleteMemberAccount(), getApprovedMembers(), getBoardPosts(), getMemberProfiles(), getSmsSubscriptions(), readJsonFile() (+4 more)

### Community 86 - "fetchDiseases"
Cohesion: 0.43
Nodes (7): buildDiseaseSearch(), dzCustomToEntry(), dzMergeCustom(), fetchDiseases(), fetchPublicContentJson(), loadDiseaseCustom(), loadDzPhotos()

### Community 87 - "renderSeasonalPanel"
Cohesion: 0.21
Nodes (14): buildSmsDigestText(), currentSeasonalPackages(), currentTreatmentPackages(), fetchSeasonGuides(), pkgEmptyHtml(), renderSeasonalPanel(), renderSeasonGuide(), seasonalPackagesFor() (+6 more)

### Community 88 - "renderDzStatsPanel"
Cohesion: 0.40
Nodes (6): dzN(), dzStatsBars(), dzStatsCell(), dzStatsLastMonth(), dzStatsSum(), renderDzStatsPanel()

### Community 89 - "phFig"
Cohesion: 0.40
Nodes (10): phArrow(), phFig(), phFigCirc(), phFigDigest(), phFigExcrete(), phFigHormone(), phFigNeuro(), phFigRepro() (+2 more)

### Community 90 - "vcFigPress"
Cohesion: 0.17
Nodes (16): vcBind(), vcFmt(), vcInletOut(), vcInterp(), vcKg(), vcNeed(), vcPerOut(), vcR100() (+8 more)

### Community 91 - "fetch_poultry_diseases.py"
Cohesion: 0.12
Nodes (10): get(), load_extra(), load_previous(), main(), merge_only(), parse_detail(), parse_index(), save() (+2 more)

### Community 92 - "hzBox"
Cohesion: 0.20
Nodes (14): hzBacktestBox(), hzBacktestBox2(), hzBox(), hzBt2Table(), hzClass(), hzDaysAgo(), hzDensEnsure(), hzDensityBox() (+6 more)

### Community 93 - "commons.js"
Cohesion: 0.43
Nodes (7): fetchCandidateImage(), findCommonsCandidates(), IMAGE_MIME, searchCommons(), stripHtml(), thumbAt(), findCardImage()

### Community 94 - "renderGrainPriceCard"
Cohesion: 0.48
Nodes (7): gpCol(), gpDir(), gpPct(), gpRange(), gpSpark(), renderGrainPriceCard(), renderGrainPricePanel()

### Community 95 - "renderVentFinderPanel"
Cohesion: 0.29
Nodes (10): calcHumidityRatio(), calcVentilationRate(), getFeedIntakeFor(), getFeedIntakeForCurrent(), getTargetTempForAge(), parseAgeRangeLabel(), renderVentCalcPanel(), renderVentFinderPanel() (+2 more)

### Community 96 - "renderVaccinePanel"
Cohesion: 0.17
Nodes (17): currentVaccinePrograms(), pkgCardHtml(), pkgColor(), pkgColorOf(), pkgColorPickerHtml(), pkgReadColor(), pkgValidColor(), renderVaccineGuide() (+9 more)

### Community 97 - "renderHusbandryPointsCard"
Cohesion: 0.14
Nodes (15): anomPointsHtml(), anomTodayLine(), aviagenTargetTemp(), calcHeatStressIndex(), calcWetBulbC(), comfortActions(), dryRhOfDay(), getTodayClimate() (+7 more)

### Community 98 - "switchTab"
Cohesion: 0.15
Nodes (18): anomLoadEnsemble(), anomRun(), consultEnsureWeather(), consultWxBind(), consultWxGate(), fetchNews(), fetchWeather(), fetchWeatherNews() (+10 more)

### Community 99 - "gmT"
Cohesion: 0.15
Nodes (53): dsFigBirds(), dsFigFlow(), dsFigFume(), gmArrow(), gmBox(), gmE(), gmFigAbAg(), gmFigAst() (+45 more)

### Community 100 - "fetchQiaSearch"
Cohesion: 0.11
Nodes (26): attachDrugDetails(), bindDrugPickerEvents(), choseongMatchIndex(), closeDrugPicker(), dropExportOnly(), drugPickerOverlayHtml(), drugSymptomSuggestions(), fetchQiaSearch() (+18 more)

### Community 101 - "renderWelfareResult"
Cohesion: 0.43
Nodes (7): renderWelfarePanel(), renderWelfareResult(), wfBroilerRows(), wfFmt(), wfLayerRows(), wfNum(), wfRow()

### Community 102 - "authDialog"
Cohesion: 0.67
Nodes (3): authDialog(), premiumResetPassword(), premiumSignInEmail()

### Community 103 - "fetch_notices.py"
Cohesion: 0.25
Nodes (8): clean(), fetch_board(), get_html(), main(), parse_chicken_assoc(), parse_dailyvet(), parse_gnuboard(), parse_news_site()

### Community 104 - "fetch_hpai_risk.py"
Cohesion: 0.22
Nodes (8): build(), day(), fetch_events(), get_json(), is_hpai(), is_wild(), keep_previous(), main()

### Community 105 - "farmGameCall"
Cohesion: 0.39
Nodes (8): farmGameCall(), farmGameErrMsg(), farmGameNickKey(), farmGameUser(), list(), load(), remove(), save()

### Community 106 - "urllib_parse"
Cohesion: 0.18
Nodes (7): fetch_html(), main(), parse_price_table(), fetch_html(), main(), normalize_date(), parse_egg_price_html()

### Community 107 - "drugUseBind"
Cohesion: 0.09
Nodes (28): drugUseAllKinds(), drugUseBind(), drugUseCard(), drugUseForm(), drugUseItems(), drugUseKindBadge(), drugUseKindColor(), drugUseNewDraft() (+20 more)

### Community 108 - "renderFarmFinderPanel"
Cohesion: 0.23
Nodes (13): currentFinderCases(), finderCasesForCategory(), finderCasesForSpecies(), finderCategoriesFor(), finderSpeciesLabel(), pkgCautionHtml(), pkgSectionTitle(), pkgStepsHtml() (+5 more)

### Community 110 - "fetch_taxfree_fuel.py"
Cohesion: 0.25
Nodes (6): fetch_html(), main(), parse(), day(), parse_day(), year_ago()

### Community 113 - "renderHpaiKrCard"
Cohesion: 0.31
Nodes (13): hkCount(), hkFarms(), hkFmt(), hkInPeriod(), hkMonth(), hkNumLabel(), hkProvFill(), hkSeq() (+5 more)

### Community 114 - "renderStudyPanel"
Cohesion: 0.40
Nodes (5): commonsImageCredit(), currentStudyDecks(), renderStudyPanel(), studyBackImageCredit(), studyThemeFor()

### Community 115 - "hzToday"
Cohesion: 0.22
Nodes (13): hzBtSummary(), hzBtSummaryLine(), hzLift(), hzNearLevel1(), hzReportHtml(), hzReportPrintDoc(), hzReportText(), hzToday() (+5 more)

### Community 116 - "dryWarnBox"
Cohesion: 0.36
Nodes (9): dryWarnBox(), humAlertName(), humChips(), humGaugeSvg(), humIndexNote(), humIndexTable(), humLevels(), humPics() (+1 more)

### Community 117 - "sgOpenEdit"
Cohesion: 0.29
Nodes (7): sgAutumnSeed(), sgBase(), sgEffective(), sgHusbToText(), sgIssuesToText(), sgOpenEdit(), sgRowsToText()

### Community 118 - "pfBind"
Cohesion: 0.21
Nodes (13): pfApplyLocal(), pfBind(), pfDownload(), pfIngest(), pfLog(), pfMergeRows(), pfNormDate(), pfNum() (+5 more)

### Community 119 - "pfSeries"
Cohesion: 0.11
Nodes (26): pfBanner(), pfBuildModel(), pfClean(), pfClip(), pfDemoData(), pfDiagram(), pfEvidence(), pfFeedMonths() (+18 more)

### Community 120 - "isPremiumApproved"
Cohesion: 0.07
Nodes (38): fmtLunar(), isEmbedded(), isPremiumApproved(), kkokoBumpUsage(), kkokoCharacterBlock(), kkokoDailyLimit(), kkokoDisplayName(), kkokoGreeting() (+30 more)

### Community 121 - "callClaude"
Cohesion: 0.32
Nodes (8): analyzeNecropsyPhotos(), Anthropic, callClaude(), extractMagazineText(), generateAiDraft(), necropsyMediaType(), responseJson(), responseText()

### Community 122 - "renderDisinfectPanel"
Cohesion: 0.16
Nodes (20): dilBind(), dilCalc(), dilFmt(), dilResultHtml(), disinfectProductsToText(), dsBanner(), dsBasic(), dsBug() (+12 more)

### Community 124 - "renderWeatherNewsCard"
Cohesion: 0.40
Nodes (5): renderWeatherNewsCard(), wnAgo(), wnCard(), wnLink(), wnThin()

### Community 125 - "gmFig"
Cohesion: 0.17
Nodes (16): dsBind(), GM_DIRT(), gmBind(), gmDilBox(), gmDilOut(), gmFig(), gmFigFarm(), gmFinal() (+8 more)

### Community 127 - "attachDzCustomEvents"
Cohesion: 0.15
Nodes (13): attachDzCustomEvents(), dzFormRead(), dzParseAiDraft(), dzPhotosPublish(), generateAiDraft(), hgNewKey(), hgPublish(), publicContentPath() (+5 more)

### Community 128 - "renderDrugSearchPanel"
Cohesion: 0.29
Nodes (8): drugEfficacySnippet(), drugFormCategory(), drugModePlaceholder(), drugStandardPacks(), drugWithdrawalForPoultry(), renderDrugKindSelect(), renderDrugSearchPanel(), renderDrugUseForm()

### Community 129 - "renderColiEasy"
Cohesion: 0.39
Nodes (8): easyBtn(), easyCard(), easyHero(), easyList(), easyStep(), easyTwo(), renderColiEasy(), renderHzEasy()

### Community 130 - "renderWeatherBody"
Cohesion: 0.29
Nodes (7): isDryRh(), renderLivestockWeatherPanel(), renderWeatherBody(), windLevel(), wxFeelLevel(), wxFeelTemp(), wxStaleBanner()

### Community 132 - "CLAUDE.md"
Cohesion: 0.40
Nodes (3): Commands, graphify (토큰 절약용 코드 지식 그래프), Workflow preference (owner's standing instruction)

### Community 133 - "sortVaccineSchedule"
Cohesion: 0.40
Nodes (5): ageDays(), resetVaccineForm(), sortVaccineSchedule(), vaccineAgeDays(), vaccineSameAge()

### Community 134 - "isBoardAdmin"
Cohesion: 0.10
Nodes (22): currentFarmFaq(), currentHpaiAuto(), currentHpaiNews(), currentPremiumMenuItems(), emergTrendBadge(), featureBoardAuthorLabel(), featureBoardReplyLabel(), getVaccinePrograms() (+14 more)

### Community 135 - "renderProductionIndexPanel"
Cohesion: 0.50
Nodes (4): calcProductionIndex(), calcRequiredAdg(), productionIndexGrade(), renderProductionIndexPanel()

### Community 136 - "renderHzTasks"
Cohesion: 0.83
Nodes (4): hzStageProgress(), hzTaskId(), renderHzTaskCard(), renderHzTasks()

### Community 138 - "metConvert"
Cohesion: 0.50
Nodes (4): metConvert(), metEntryPrecip(), metEntrySymbol(), metSymbolToWmo()

### Community 139 - "sgDraftToGuide"
Cohesion: 0.50
Nodes (4): sgDraftToGuide(), sgParseHusb(), sgParseIssues(), sgParseRows()

## Knowledge Gaps
- **1 isolated node(s):** `RFC-822`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1170 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Architecture: the fetch-script → JSON → dashboard pipeline` connect `Architecture: the fetch-script → JSON → dashboard pipeline` to `index.inline.js`, `ibTag`, `attachEvents`, `index.js`, `CLAUDE.md`, `sortVaccineSchedule`, `withStorageTimeout`, `send_sms_subscriptions.py`, `isBoardAdmin`, `dzAutoFig`, `metConvert`, `attachDiseaseEvents`, `renderConsultTab`, `esc`, `re`, `coliFigFor`, `renderVentTab`, `fetch_animal_drug_news.py`, `renderFeedGrainFlow`, `gmVirus`, `renderFeedPotentialPanel`, `fetch_broiler_breeder.py`, `renderLightClock`, `pfForecast`, `time`, `isBoardAdmin`, `render`, `gmVirus`, `render`, `tradeItem`, `What this is`, `renderDzStatsPanel`, `vcFigPress`, `renderVentFinderPanel`, `renderVaccinePanel`, `renderHusbandryPointsCard`, `switchTab`, `gmT`, `fetchQiaSearch`, `drugUseBind`, `renderHpaiKrCard`, `dryWarnBox`, `pfSeries`, `isPremiumApproved`, `callClaude`, `renderDisinfectPanel`, `gmFig`?**
  _High betweenness centrality (0.188) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `esc()` (e.g. with `dzFigTiles()` and `renderBizFooterLine()`) actually correct?**
  _`esc()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `RFC-822` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `index.inline.js` be split into smaller, more focused modules?**
  _Cohesion score 0.004534464943168708 - nodes in this community are weakly interconnected._
- **Why does `decode_google_url()` connect `fetch_animal_drug_news.py` to `fetch_weather_news.py`, `Architecture: the fetch-script → JSON → dashboard pipeline`, `json`, `re`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Are the 180 inferred relationships involving `Architecture: the fetch-script → JSON → dashboard pipeline` (e.g. with `analyzeNecropsyPhotos()` and `fetchRssItems()`) actually correct?**
  _`Architecture: the fetch-script → JSON → dashboard pipeline` has 180 INFERRED edges - model-reasoned connections that need verification._
- **Should `attachEvents` be split into smaller, more focused modules?**
  _Cohesion score 0.0345679012345679 - nodes in this community are weakly interconnected._