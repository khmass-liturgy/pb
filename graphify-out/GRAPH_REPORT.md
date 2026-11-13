# Graph Report - pb  (2026-11-13)

## Corpus Check
- 125 files · ~837,642 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 6 file(s) not represented in the graph (top: (none) 4, .glb 1, .rules 1)

## Summary
- 3051 nodes · 6809 edges · 113 communities (109 shown, 4 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 215 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9addb07b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- index.inline.js
- ibTag
- attachEvents
- index.js
- hzNearBox
- fetch_animal_drug_news.py
- Architecture: the fetch-script → JSON → dashboard pipeline
- render
- pathlib
- esc
- fetch_broiler_breeder.py
- attachDiseaseEvents
- renderConsultTab
- re
- fetch_poultry_price.py
- fetch_briefing_news.py
- coliFigFor
- renderHusbandryPointsCard
- withStorageTimeout
- steps
- steps
- sys
- isPremiumApproved
- fetch_egg_report.py
- requests
- steps
- fetch_egg_price.py
- fetch_h5n1_human.py
- fetchQiaSearch
- renderSeasonalPanel
- renderFeedGrainFlow
- send_sms_subscriptions.py
- steps
- steps
- steps
- env
- renderFeedPotentialPanel
- renderLightCalc
- urllib_parse
- fetch_grain_quality.py
- steps
- steps
- steps
- steps
- steps
- steps
- steps
- steps
- renderHusbandryPointsCard
- renderPremiumTab
- pfForecast
- steps
- steps
- steps
- steps
- steps
- steps
- steps
- json
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
- renderHpaiSymptomCard
- pfTabSpecies
- steps
- fetchNotices
- steps
- steps
- steps
- fetch_poultry_diseases.py
- pfSeries
- ocr_jungchu_table.js
- renderSelfCheckPanel
- fetch_weather_news.py
- renderHpaiKrCard
- tradeItem
- fetch_hpai_risk.py
- fetch_notices.py
- fetch_usda_crop_progress.py
- renderSeasonalPanel
- pfBind
- renderDrugUsePanel
- phFig
- vcNeed
- attachDzCustomEvents
- renderDrugSearchPanel
- renderColiEasy
- renderGrainPriceCard
- sgBind
- anomLoadClimatology
- currentSelfCheckDiseases
- isBoardAdmin
- dilResultHtml
- pfBuildModel
- fetch_prices.py
- authDialog
- vcFigPress
- fetch_taxfree_fuel.py
- farmGameCall
- PriceTableParser
- RowParser
- rmBind
- kkokoMount3d
- kkokoTouchCharacter

## God Nodes (most connected - your core abstractions)
1. `esc()` - 191 edges
2. `attachEvents()` - 158 edges
3. `render()` - 120 edges
4. `Architecture: the fetch-script → JSON → dashboard pipeline` - 91 edges
5. `renderPremiumTab()` - 83 edges
6. `ibTag()` - 50 edges
7. `fetchWithTimeout()` - 50 edges
8. `ibChecklist()` - 49 edges
9. `ibP()` - 49 edges
10. `ibTable()` - 49 edges

## Surprising Connections (you probably didn't know these)
- `Conventions shared across all fetch scripts` --references--> `apply_glossary()`  [INFERRED]
  CLAUDE.md → scripts/translation_glossary.py
- `graphify (토큰 절약용 코드 지식 그래프)` --references--> `renderHpaiKrLiveStrip()`  [INFERRED]
  CLAUDE.md → graphify-src/index.inline.js
- `What this is` --references--> `getApprovedMembers()`  [INFERRED]
  CLAUDE.md → functions/index.js
- `What this is` --references--> `getPublicContent()`  [INFERRED]
  CLAUDE.md → functions/index.js
- `What this is` --references--> `attachDzCustomEvents()`  [INFERRED]
  CLAUDE.md → graphify-src/index.inline.js

## Import Cycles
- None detected.

## Communities (113 total, 4 thin omitted)

### Community 0 - "index.inline.js"
Cohesion: 0.00
Nodes (400): RFC-822, ANOM_MD_START, anomState, ARBORACRES_DATA, AUTUMN_BR_DAILY, AUTUMN_BR_DISEASES, AUTUMN_BR_HUSB, AUTUMN_BR_SYM (+392 more)

### Community 1 - "ibTag"
Cohesion: 0.28
Nodes (62): 1. 전염성기관지염(IB) 차단 AI공동연구팀 (유료서비스 최상단 `ibteam`), ibBox(), ibChecklist(), ibField(), ibFlow(), ibGenomeBar(), ibH(), ibLecture1() (+54 more)

### Community 2 - "attachEvents"
Cohesion: 0.03
Nodes (81): ageDays(), attachEvents(), calcProductionIndex(), calcRequiredAdg(), callMemberFunction(), createFirebaseMemberAccount(), currentDiseaseDisinfectants(), currentFarmFaq() (+73 more)

### Community 3 - "index.js"
Cohesion: 0.05
Nodes (70): What this is, fetchCandidateImage(), findCommonsCandidates(), IMAGE_MIME, searchCommons(), stripHtml(), thumbAt(), admin (+62 more)

### Community 4 - "hzNearBox"
Cohesion: 0.06
Nodes (74): 0. 이어받는 세션이 먼저 할 일, 1-2. HPAI ZERO FARM (유료서비스 · AI공동연구팀, `hpaizero`), 2. 최근 완료된 기능(이 세션, 2026-10-08 ~ 10-13, 모두 main 병합), 3. 환경 메모, 작업 인계 노트 (2026-10-13), hkAllFarms(), hkAllWild(), hzAddDays() (+66 more)

### Community 5 - "fetch_animal_drug_news.py"
Cohesion: 0.07
Nodes (42): build_item(), category_guess(), claude(), collect(), friday_of(), main(), parse_json(), pick_with_claude() (+34 more)

### Community 6 - "Architecture: the fetch-script → JSON → dashboard pipeline"
Cohesion: 0.06
Nodes (49): Architecture: the fetch-script → JSON → dashboard pipeline, Commands, Conventions shared across all fetch scripts, graphify (토큰 절약용 코드 지식 그래프), Workflow preference (owner's standing instruction), boardShrinkPhoto(), farmGameBind(), farmGameCloseWin() (+41 more)

### Community 7 - "render"
Cohesion: 0.08
Nodes (50): Data is also mirrored to Firebase Storage (so the repo can go private), Working in index.html, getPublicContent(), anomLoadEnsemble(), anomRun(), dataDatasetOf(), fetchBroilerBreeder(), fetchBroilerPriceToday() (+42 more)

### Community 8 - "pathlib"
Cohesion: 0.13
Nodes (14): fetch_window(), main(), parse_window(), customs_get(), customs_variants(), fetch_comtrade(), fetch_customs(), http_get() (+6 more)

### Community 9 - "esc"
Cohesion: 0.07
Nodes (44): allSites(), boardStatusBadge(), currentBoardCfg(), diseaseSnippet(), esc(), fetchInboxBoardPosts(), fetchMyBoardPosts(), googleImageBtn() (+36 more)

### Community 10 - "fetch_broiler_breeder.py"
Cohesion: 0.13
Nodes (16): ask_claude(), build_forecast(), clean_outlook(), fit_adult(), _img_b64(), kreI_get(), _lstsq2(), main() (+8 more)

### Community 11 - "attachDiseaseEvents"
Cohesion: 0.06
Nodes (47): attachDiseaseEvents(), attachDiseaseResultEvents(), countPicks(), currentHpaiAuto(), currentHpaiNews(), currentPicks(), diseaseListing(), diseaseMatches() (+39 more)

### Community 12 - "renderConsultTab"
Cohesion: 0.10
Nodes (30): broilerEquivDay(), calcDewPointC(), fcAlertOn(), fcInputBox(), fcNum(), fcResultCard(), fcVerdict(), feedPotentialStandards() (+22 more)

### Community 13 - "re"
Cohesion: 0.11
Nodes (26): ai_extract(), _candidates(), clean_quick(), clean_wild(), _date(), fetch_news(), fetch_quick_news(), fetch_table_data() (+18 more)

### Community 14 - "fetch_poultry_price.py"
Cohesion: 0.11
Nodes (19): cell_number(), fetch_page(), latest_metric(), load_previous(), main(), normalize_date(), normalize_week_start(), normalize_year_month() (+11 more)

### Community 15 - "fetch_briefing_news.py"
Cohesion: 0.10
Nodes (15): clean_text(), fetch_source(), get_with_proxy_fallback(), kst_label(), main(), parse_aflnews(), parse_chuksan(), parse_handon() (+7 more)

### Community 16 - "coliFigFor"
Cohesion: 0.08
Nodes (34): autumnFig(), autumnSvgChain(), autumnSvgResp(), coliBox(), coliFig(), coliFig2For(), coliFigFor(), coliLinks() (+26 more)

### Community 17 - "renderHusbandryPointsCard"
Cohesion: 0.08
Nodes (27): anomIsCold(), anomIsHot(), anomTodayJudge(), anomTodayLine(), determineHumidityStage(), determineVentStage(), renderAnomalyPanel(), renderHeaderSolarTerm() (+19 more)

### Community 18 - "withStorageTimeout"
Cohesion: 0.09
Nodes (26): boardPostPath(), deleteFeatureRequest(), deleteMemberProfile(), featureRequestPostPath(), featureRequestRepliesPrefix(), fetchFeatureRequests(), fetchMemberProfiles(), fetchMySmsSubscription() (+18 more)

### Community 19 - "steps"
Cohesion: 0.06
Nodes (34): concurrency, cancel-in-progress, group, ANTHROPIC_API_KEY, FIREBASE_SERVICE_ACCOUNT_JSON, FORCE, ONCE_KEYWORD, default (+26 more)

### Community 20 - "steps"
Cohesion: 0.06
Nodes (33): description, required, CUSTOMS_ONLY, DATA_GO_KR_KEY, FIREBASE_SERVICE_ACCOUNT_JSON, FULL, SMS_RELAY_SECRET, SMS_RELAY_URL (+25 more)

### Community 21 - "sys"
Cohesion: 0.08
Nodes (18): list_all_posts(), main(), _candidates(), fetch_year(), find_attachment(), _get(), group_series(), keep_previous() (+10 more)

### Community 22 - "isPremiumApproved"
Cohesion: 0.13
Nodes (24): fmtLunar(), isEmbedded(), isPremiumApproved(), kkokoBumpUsage(), kkokoCharacterBlock(), kkokoDailyLimit(), kkokoDisplayName(), kkokoGreeting() (+16 more)

### Community 23 - "fetch_egg_report.py"
Cohesion: 0.13
Nodes (11): _diag_dump(), download_pdf(), _extract_board_nos(), fetch_detail(), find_latest_board_no_from_list(), find_latest_board_no_via_browser(), get_latest(), load_previous() (+3 more)

### Community 24 - "requests"
Cohesion: 0.20
Nodes (10): build_category(), efetch_articles(), esearch_pmids(), fallback_translation(), google_translate(), load_previous(), main(), _text() (+2 more)

### Community 25 - "steps"
Cohesion: 0.07
Nodes (29): ANTHROPIC_API_KEY, FIREBASE_SERVICE_ACCOUNT_JSON, QUICK_EXTRA_URLS, SMS_RELAY_SECRET, SMS_RELAY_URL, runs-on, steps, urls (+21 more)

### Community 26 - "fetch_egg_price.py"
Cohesion: 0.15
Nodes (7): fetch_html(), main(), parse_price_table(), fetch_html(), main(), normalize_date(), parse_egg_price_html()

### Community 27 - "fetch_h5n1_human.py"
Cohesion: 0.21
Nodes (11): download(), main(), read_csv_bytes(), to_int(), build(), _clean_name(), find_table_page(), _int() (+3 more)

### Community 28 - "fetchQiaSearch"
Cohesion: 0.10
Nodes (29): attachDrugDetails(), bindDrugPickerEvents(), choseongMatchIndex(), closeDrugPicker(), dropExportOnly(), drugPickerOverlayHtml(), fetchQiaSearch(), fuzzySearchDrug() (+21 more)

### Community 29 - "renderSeasonalPanel"
Cohesion: 0.10
Nodes (36): buildSmsDigestText(), currentFinderCases(), currentTreatmentPackages(), currentVaccinePrograms(), disinfectFlowHtml(), disinfectProductsToText(), finderCasesForCategory(), finderCasesForSpecies() (+28 more)

### Community 30 - "renderFeedGrainFlow"
Cohesion: 0.08
Nodes (28): fgBadge(), fgDetailRows(), fgImplication(), fgLevelOf(), fgMeter(), fgMoldLevel(), fgMoldStrip(), fgMoldType() (+20 more)

### Community 31 - "send_sms_subscriptions.py"
Cohesion: 0.15
Nodes (22): The SMS dispatch job (not the fetch-script shape above), _arrow(), build_digest(), current_season(), digest_egg_report(), digest_feed_production(), digest_grain_quality(), digest_hpai_kr() (+14 more)

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
Nodes (27): bbChartSvg(), bbDelta(), bbMan(), bbMonth(), bbPctOf(), bbYm(), fpBirds(), fpChart() (+19 more)

### Community 37 - "renderLightCalc"
Cohesion: 0.10
Nodes (26): bindSmsBox(), brClock(), brDark(), brFmtDate(), brLux(), brSchedule(), brSmsText(), lgChartSvg() (+18 more)

### Community 38 - "urllib_parse"
Cohesion: 0.13
Nodes (9): find_image_url(), find_post_url(), _get_bytes(), _get_text(), main(), run_ocr(), collect(), dataset_of() (+1 more)

### Community 39 - "fetch_grain_quality.py"
Cohesion: 0.08
Nodes (24): annual_vol(), build_grain(), change(), clamp(), fetch(), fetch_news(), main(), pct() (+16 more)

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

### Community 48 - "renderHusbandryPointsCard"
Cohesion: 0.10
Nodes (21): anomPointsHtml(), aviagenTargetTemp(), calcHeatStressIndex(), calcHumidityRatio(), calcVentilationRate(), calcWetBulbC(), comfortActions(), getFeedIntakeFor() (+13 more)

### Community 49 - "renderPremiumTab"
Cohesion: 0.09
Nodes (39): buildSmsDigestTextAsync(), currentPremiumMenuItems(), fetchAllSmsSubscriptions(), fetchDiseaseDisinfectants(), fetchDrugUse(), fetchFarmFaq(), fetchFarmFinderCases(), fetchIbContent() (+31 more)

### Community 50 - "pfForecast"
Cohesion: 0.13
Nodes (26): pfBacktestDaily(), pfBacktestMonthly(), pfCalibrate(), pfCalibrationTable(), pfContrib(), pfDailyX(), pfFitDaily(), pfFitMonthly() (+18 more)

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

### Community 58 - "json"
Cohesion: 0.15
Nodes (15): load(), main(), v(), merge_rows(), base_params(), build(), slot(), species() (+7 more)

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

### Community 69 - "renderHpaiSymptomCard"
Cohesion: 0.18
Nodes (18): hg(), hgAdminBar(), hgCircled(), hgFmt(), hgItemLocs(), hgPosByKey(), hgPositions(), hgSelOptions() (+10 more)

### Community 70 - "pfTabSpecies"
Cohesion: 0.17
Nodes (25): pfBar(), pfChips(), pfControls(), pfHz(), pfImportBrief(), pfInsufficientHtml(), pfKpi(), pfPct1() (+17 more)

### Community 71 - "steps"
Cohesion: 0.10
Nodes (19): FIREBASE_SERVICE_ACCOUNT_JSON, SMS_RELAY_SECRET, SMS_RELAY_URL, jobs, send, name, on, schedule (+11 more)

### Community 72 - "fetchNotices"
Cohesion: 0.29
Nodes (11): fetchEconNews(), fetchNotices(), fetchOneSite(), fetchPolicyNews(), fmtKST(), loadNoticeCache(), parseAflRSS(), parseChuksanHTML() (+3 more)

### Community 73 - "steps"
Cohesion: 0.11
Nodes (17): runs-on, steps, SMS_RELAY_SECRET, SMS_RELAY_URL, jobs, backfill-feed, name, on (+9 more)

### Community 74 - "steps"
Cohesion: 0.11
Nodes (17): FIREBASE_SERVICE_ACCOUNT_JSON, jobs, sync-storage, name, on, push, workflow_dispatch, branches (+9 more)

### Community 75 - "steps"
Cohesion: 0.11
Nodes (17): TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, jobs, send, name, on, schedule, workflow_dispatch (+9 more)

### Community 76 - "fetch_poultry_diseases.py"
Cohesion: 0.11
Nodes (11): get(), load_previous(), main(), parse_detail(), parse_index(), save(), translate(), _ends_in_rieul() (+3 more)

### Community 77 - "pfSeries"
Cohesion: 0.20
Nodes (16): pfBanner(), pfClean(), pfEvidence(), pfFeedMonths(), pfHeatmaps(), pfImportHtml(), pfImportItem(), pfImportStatsHtml() (+8 more)

### Community 78 - "ocr_jungchu_table.js"
Cohesion: 0.17
Nodes (15): sharp, tesseract.js, { createWorker }, isRowValid(), main(), ocrTableRows(), parseRow(), sharp (+7 more)

### Community 79 - "renderSelfCheckPanel"
Cohesion: 0.26
Nodes (14): bodyPartByKey(), bodyPartLabel(), organFunctionFor(), pkgBoxStyle(), pkgChip(), pkgIconCircle(), renderDiseaseBriefPanel(), renderDrugNewsPanel() (+6 more)

### Community 80 - "fetch_weather_news.py"
Cohesion: 0.23
Nodes (10): ai_summary(), cap_items(), enrich(), main(), order_tags(), relevant(), search(), tags_for() (+2 more)

### Community 81 - "renderHpaiKrCard"
Cohesion: 0.16
Nodes (22): flySrcLinks(), h5hYearChart(), hkCount(), hkFarms(), hkFmt(), hkInPeriod(), hkMonth(), hkProvFill() (+14 more)

### Community 82 - "tradeItem"
Cohesion: 0.17
Nodes (16): pfFmtN(), pfTon(), renderTradePanel(), tradeBadge(), tradeItem(), tradeKpi(), tradeModel(), tradeMoney() (+8 more)

### Community 83 - "fetch_hpai_risk.py"
Cohesion: 0.22
Nodes (8): build(), day(), fetch_events(), get_json(), is_hpai(), is_wild(), keep_previous(), main()

### Community 84 - "fetch_notices.py"
Cohesion: 0.25
Nodes (8): clean(), fetch_board(), get_html(), main(), parse_chicken_assoc(), parse_dailyvet(), parse_gnuboard(), parse_news_site()

### Community 85 - "fetch_usda_crop_progress.py"
Cohesion: 0.23
Nodes (9): fetch_text(), history_point(), list_releases(), main(), _num(), parse_report(), split_sections(), table_rows() (+1 more)

### Community 86 - "renderSeasonalPanel"
Cohesion: 0.20
Nodes (14): autumnSvgEggRule(), autumnSvgLayerSign(), currentSeasonalPackages(), pkgEmptyHtml(), renderAutumnLayer(), renderSeasonalPanel(), renderSeasonGuide(), seasonalPackagesFor() (+6 more)

### Community 87 - "pfBind"
Cohesion: 0.19
Nodes (13): pfApplyLocal(), pfBind(), pfDownload(), pfIngest(), pfMergeRows(), pfMonthly(), pfNormDate(), pfNum() (+5 more)

### Community 88 - "renderDrugUsePanel"
Cohesion: 0.15
Nodes (16): drugUseAllKinds(), drugUseBind(), drugUseCard(), drugUseForm(), drugUseItems(), drugUseKindBadge(), drugUseKindColor(), drugUseNewDraft() (+8 more)

### Community 89 - "phFig"
Cohesion: 0.40
Nodes (10): phArrow(), phFig(), phFigCirc(), phFigDigest(), phFigExcrete(), phFigHormone(), phFigNeuro(), phFigRepro() (+2 more)

### Community 90 - "vcNeed"
Cohesion: 0.20
Nodes (14): vcFmt(), vcInletOut(), vcInterp(), vcKg(), vcNeed(), vcPerOut(), vcR100(), vcRange() (+6 more)

### Community 91 - "attachDzCustomEvents"
Cohesion: 0.12
Nodes (18): attachDzCustomEvents(), buildDiseaseSearch(), dzCustomToEntry(), dzFormRead(), dzMergeCustom(), dzParseAiDraft(), emergSendToNews(), fetchDiseases() (+10 more)

### Community 92 - "renderDrugSearchPanel"
Cohesion: 0.29
Nodes (8): drugEfficacySnippet(), drugFormCategory(), drugModePlaceholder(), drugStandardPacks(), drugWithdrawalForPoultry(), renderDrugKindSelect(), renderDrugSearchPanel(), renderDrugUseForm()

### Community 93 - "renderColiEasy"
Cohesion: 0.39
Nodes (8): easyBtn(), easyCard(), easyHero(), easyList(), easyStep(), easyTwo(), renderColiEasy(), renderHzEasy()

### Community 94 - "renderGrainPriceCard"
Cohesion: 0.48
Nodes (7): gpCol(), gpDir(), gpPct(), gpRange(), gpSpark(), renderGrainPriceCard(), renderGrainPricePanel()

### Community 95 - "sgBind"
Cohesion: 0.18
Nodes (11): sgBind(), sgDraftToGuide(), sgHusbToText(), sgIssuesToText(), sgOpenEdit(), sgParseHusb(), sgParseIssues(), sgParseRows() (+3 more)

### Community 96 - "anomLoadClimatology"
Cohesion: 0.47
Nodes (6): anomCompute(), anomDoy(), anomLoadClimatology(), anomMean(), anomPct(), anomSd()

### Community 97 - "currentSelfCheckDiseases"
Cohesion: 0.22
Nodes (13): cardCandToBackImage(), currentOrganFunctions(), currentSelfCheckDiseases(), findCardImage(), newSelfCheckKey(), publishOrganFunction(), publishSelfCheckContent(), publishSelfCheckDiseases() (+5 more)

### Community 98 - "isBoardAdmin"
Cohesion: 0.11
Nodes (19): commonsImageCredit(), currentStudyDecks(), emergTrendBadge(), featureBoardAuthorLabel(), featureBoardReplyLabel(), isAdmin(), isBoardAdmin(), pfAdminHtml() (+11 more)

### Community 99 - "dilResultHtml"
Cohesion: 0.50
Nodes (5): dilBind(), dilCalc(), dilFmt(), dilResultHtml(), renderDilutionCard()

### Community 100 - "pfBuildModel"
Cohesion: 0.50
Nodes (4): pfBuildModel(), pfClip(), pfProbs(), pfYoY()

### Community 101 - "fetch_prices.py"
Cohesion: 0.29
Nodes (9): call_api(), diff(), get_api_key(), ival(), main(), filter_type(), probe_url(), sval() (+1 more)

### Community 102 - "authDialog"
Cohesion: 0.67
Nodes (3): authDialog(), premiumResetPassword(), premiumSignInEmail()

### Community 103 - "vcFigPress"
Cohesion: 0.38
Nodes (11): vcChick(), vcFan(), vcFig(), vcFigHouse(), vcFigInlet(), vcFigModes(), vcFigPress(), vcFigWhy() (+3 more)

### Community 104 - "fetch_taxfree_fuel.py"
Cohesion: 0.25
Nodes (6): fetch_html(), main(), parse(), day(), parse_day(), year_ago()

### Community 105 - "farmGameCall"
Cohesion: 0.39
Nodes (8): farmGameCall(), farmGameErrMsg(), farmGameNickKey(), farmGameUser(), list(), load(), remove(), save()

### Community 108 - "rmBind"
Cohesion: 0.67
Nodes (4): flyBind(), flyCensusTxt(), flyLoadLeaflet(), rmBind()

### Community 109 - "kkokoMount3d"
Cohesion: 0.50
Nodes (4): kkokoImgUrl(), kkokoLoadViewerLib(), kkokoMount3d(), kkokoPlace3d()

### Community 110 - "kkokoTouchCharacter"
Cohesion: 0.67
Nodes (3): kkokoReactions(), kkokoSpin3d(), kkokoTouchCharacter()

## Knowledge Gaps
- **1 isolated node(s):** `RFC-822`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1112 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Architecture: the fetch-script → JSON → dashboard pipeline` connect `Architecture: the fetch-script → JSON → dashboard pipeline` to `ibTag`, `attachEvents`, `index.js`, `fetch_animal_drug_news.py`, `render`, `esc`, `fetch_broiler_breeder.py`, `attachDiseaseEvents`, `renderConsultTab`, `re`, `coliFigFor`, `isPremiumApproved`, `fetchQiaSearch`, `renderSeasonalPanel`, `renderFeedGrainFlow`, `send_sms_subscriptions.py`, `renderFeedPotentialPanel`, `renderPremiumTab`, `pfForecast`, `pfTabSpecies`, `renderHpaiKrCard`, `tradeItem`, `renderSeasonalPanel`, `renderDrugUsePanel`, `vcNeed`, `isBoardAdmin`, `pfBuildModel`?**
  _High betweenness centrality (0.209) - this node is a cross-community bridge._
- **What connects `RFC-822` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `index.inline.js` be split into smaller, more focused modules?**
  _Cohesion score 0.004876867736579967 - nodes in this community are weakly interconnected._
- **Why does `decode_google_url()` connect `fetch_animal_drug_news.py` to `fetch_weather_news.py`, `json`, `re`, `Architecture: the fetch-script → JSON → dashboard pipeline`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Should `attachEvents` be split into smaller, more focused modules?**
  _Cohesion score 0.03148148148148148 - nodes in this community are weakly interconnected._
- **Why does `ai_extract()` connect `re` to `json`, `fetch_animal_drug_news.py`, `Architecture: the fetch-script → JSON → dashboard pipeline`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Should `index.js` be split into smaller, more focused modules?**
  _Cohesion score 0.050351721584598295 - nodes in this community are weakly interconnected._