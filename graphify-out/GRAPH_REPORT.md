# Graph Report - pb  (2026-11-22)

## Corpus Check
- 130 files · ~969,737 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 6 file(s) not represented in the graph (top: (none) 4, .glb 1, .rules 1)

## Summary
- 3331 nodes · 7823 edges · 132 communities (121 shown, 11 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 364 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3b2a4a68`
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
- ibCardify
- time
- esc
- fetch_poultry_disease_brief.py
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
- send_sms_subscriptions.py
- fetch_egg_report.py
- renderHpaiTab
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
- renderLightCalc
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
- xml_etree_elementtree
- time
- steps
- isBoardAdmin
- steps
- steps
- steps
- fetch_research_papers.py
- render
- ocr_jungchu_table.js
- renderDrugSearchPanel
- fetch_h5n1_human.py
- fetchWithTimeout
- tradeItem
- fetch_hpai_risk.py
- fetchWeather
- What this is
- callClaude
- sendDirectSms
- renderDzStatsPanel
- phFig
- vcFigPress
- fetch_poultry_diseases.py
- renderHpaiTab
- commons.js
- renderGrainPriceCard
- renderColiPanel
- renderSeasonalPanel
- renderWelfareResult
- switchTab
- gmT
- fetchQiaSearch
- RowParser
- authDialog
- fetch_notices.py
- renderStudyPanel
- farmGameCall
- urllib_parse
- drugUseCard
- pfSeries
- PriceTableParser
- renderDiseaseTab
- renderHpaiKrCard
- renderBroilerPriceTodayPanel
- renderNoticesSection
- ibLossBind
- sgBind
- pfBind
- pfBuildModel
- isPremiumApproved
- renderFeedStandardPanel
- dilResultHtml
- renderWeatherNewsCard
- gmBind
- coliBind
- renderHaccpPanel
- renderPremiumLoginHints
- pfGrade
- renderPhPanel
- setupTabArrows

## God Nodes (most connected - your core abstractions)
1. `esc()` - 212 edges
2. `Architecture: the fetch-script → JSON → dashboard pipeline` - 175 edges
3. `attachEvents()` - 164 edges
4. `render()` - 127 edges
5. `renderPremiumTab()` - 85 edges
6. `gmT()` - 69 edges
7. `gmSvg()` - 66 edges
8. `gmBox()` - 58 edges
9. `fetchWithTimeout()` - 51 edges
10. `ibTag()` - 50 edges

## Surprising Connections (you probably didn't know these)
- `What this is` --references--> `getApprovedMembers()`  [INFERRED]
  CLAUDE.md → functions/index.js
- `Architecture: the fetch-script → JSON → dashboard pipeline` --references--> `fetchWeatherData()`  [INFERRED]
  CLAUDE.md → functions/index.js
- `Conventions shared across all fetch scripts` --references--> `apply_glossary()`  [INFERRED]
  CLAUDE.md → scripts/translation_glossary.py
- `Architecture: the fetch-script → JSON → dashboard pipeline` --references--> `premiumMenuItemsFull()`  [INFERRED]
  CLAUDE.md → graphify-src/index.inline.js
- `Architecture: the fetch-script → JSON → dashboard pipeline` --references--> `renderPremiumMenuItems()`  [INFERRED]
  CLAUDE.md → graphify-src/index.inline.js

## Import Cycles
- None detected.

## Communities (132 total, 11 thin omitted)

### Community 0 - "index.inline.js"
Cohesion: 0.00
Nodes (416): RFC-822, ANOM_MD_START, anomState, ARBORACRES_DATA, AUTUMN_BR_DAILY, AUTUMN_BR_DISEASES, AUTUMN_BR_HUSB, AUTUMN_BR_SYM (+408 more)

### Community 1 - "ibTag"
Cohesion: 0.28
Nodes (62): 1. 전염성기관지염(IB) 차단 AI공동연구팀 (유료서비스 최상단 `ibteam`), ibBox(), ibChecklist(), ibField(), ibFlow(), ibGenomeBar(), ibH(), ibLecture1() (+54 more)

### Community 2 - "attachEvents"
Cohesion: 0.04
Nodes (68): ageDays(), attachEvents(), calcProductionIndex(), calcRequiredAdg(), callMemberFunction(), createFirebaseMemberAccount(), currentMagazineNotes(), currentNewProducts() (+60 more)

### Community 3 - "index.js"
Cohesion: 0.10
Nodes (20): admin, ADMIN_EMAILS, AI_DRAFT_KINDS, ANTHROPIC_API_KEY, BOARD_TYPES, { defineSecret }, fetchRssItems(), fetchWeatherData() (+12 more)

### Community 4 - "hzNearBox"
Cohesion: 0.05
Nodes (79): 0. 이어받는 세션이 먼저 할 일, 1-2. HPAI ZERO FARM (유료서비스 · AI공동연구팀, `hpaizero`), 2. 최근 완료된 기능(이 세션, 2026-10-08 ~ 10-13, 모두 main 병합), 3. 환경 메모, 작업 인계 노트 (2026-10-13), easyBtn(), easyCard(), easyHero() (+71 more)

### Community 5 - "fetch_animal_drug_news.py"
Cohesion: 0.06
Nodes (46): build_item(), category_guess(), claude(), collect(), friday_of(), main(), parse_json(), pick_with_claude() (+38 more)

### Community 6 - "withStorageTimeout"
Cohesion: 0.08
Nodes (31): boardPostPath(), currentBoardCfg(), deleteFeatureRequest(), deleteMemberProfile(), featureRequestPostPath(), featureRequestRepliesPrefix(), fetchInboxBoardPosts(), fetchMyBoardPosts() (+23 more)

### Community 7 - "ibCardify"
Cohesion: 0.18
Nodes (14): ibCardify(), ibIsHead(), ibSlim(), lcCard(), lcFold(), lcRows(), renderWyPanel(), wyBind() (+6 more)

### Community 8 - "time"
Cohesion: 0.14
Nodes (12): build_baseline(), build_region(), ensure_baseline(), fetch_rows(), load_json(), main(), mean_sd(), mold_scores() (+4 more)

### Community 9 - "esc"
Cohesion: 0.11
Nodes (26): allSites(), boardStatusBadge(), disinfectFlowHtml(), esc(), renderBizFooterLine(), renderBoardCreateForm(), renderBoardFieldInput(), renderBoardFields() (+18 more)

### Community 10 - "fetch_poultry_disease_brief.py"
Cohesion: 0.13
Nodes (16): analyze(), choose(), claude(), clean_list(), listing(), main(), monday_of(), parse_json() (+8 more)

### Community 11 - "attachDiseaseEvents"
Cohesion: 0.06
Nodes (44): attachDiseaseEvents(), countPicks(), currentHpaiAuto(), currentHpaiNews(), currentPicks(), emergNewsSearch(), fetchPortalNews(), fetchRssFallback() (+36 more)

### Community 12 - "renderConsultTab"
Cohesion: 0.09
Nodes (31): broilerEquivDay(), calcHeatStressIndex(), calcHumidityRatio(), calcVentilationRate(), calcWetBulbC(), fcAlertOn(), fcInputBox(), fcNum() (+23 more)

### Community 13 - "re"
Cohesion: 0.08
Nodes (35): ai_extract(), _candidates(), clean_quick(), clean_wild(), _date(), fetch_news(), fetch_quick_news(), fetch_table_data() (+27 more)

### Community 14 - "fetch_poultry_price.py"
Cohesion: 0.11
Nodes (20): parse_window(), cell_number(), fetch_page(), latest_metric(), load_previous(), main(), normalize_date(), normalize_week_start() (+12 more)

### Community 15 - "fetch_briefing_news.py"
Cohesion: 0.10
Nodes (15): clean_text(), fetch_source(), get_with_proxy_fallback(), kst_label(), main(), parse_aflnews(), parse_chuksan(), parse_handon() (+7 more)

### Community 16 - "coliFigFor"
Cohesion: 0.08
Nodes (29): autumnFig(), autumnSvgChain(), autumnSvgEggRule(), autumnSvgLayerSign(), autumnSvgResp(), coliFig(), coliFig2For(), coliFigFor() (+21 more)

### Community 17 - "renderHusbandryPointsCard"
Cohesion: 0.09
Nodes (38): anomIsCold(), anomIsHot(), anomPointsHtml(), anomTodayJudge(), anomTodayLine(), aviagenTargetTemp(), calcDewPointC(), comfortActions() (+30 more)

### Community 18 - "Architecture: the fetch-script → JSON → dashboard pipeline"
Cohesion: 0.09
Nodes (37): Architecture: the fetch-script → JSON → dashboard pipeline, Conventions shared across all fetch scripts, dzSeasonHidden(), farmGameBind(), farmGameCloseWin(), farmGameOpenWin(), inModeBar(), metConvert() (+29 more)

### Community 19 - "steps"
Cohesion: 0.06
Nodes (34): concurrency, cancel-in-progress, group, ANTHROPIC_API_KEY, FIREBASE_SERVICE_ACCOUNT_JSON, FORCE, ONCE_KEYWORD, default (+26 more)

### Community 20 - "steps"
Cohesion: 0.06
Nodes (33): description, required, CUSTOMS_ONLY, DATA_GO_KR_KEY, FIREBASE_SERVICE_ACCOUNT_JSON, FULL, SMS_RELAY_SECRET, SMS_RELAY_URL (+25 more)

### Community 21 - "fetch_feed_production.py"
Cohesion: 0.09
Nodes (15): list_all_posts(), main(), _candidates(), fetch_year(), find_attachment(), _get(), group_series(), keep_previous() (+7 more)

### Community 22 - "send_sms_subscriptions.py"
Cohesion: 0.15
Nodes (22): The SMS dispatch job (not the fetch-script shape above), _arrow(), build_digest(), current_season(), digest_egg_report(), digest_feed_production(), digest_grain_quality(), digest_hpai_kr() (+14 more)

### Community 23 - "fetch_egg_report.py"
Cohesion: 0.13
Nodes (11): _diag_dump(), download_pdf(), _extract_board_nos(), fetch_detail(), find_latest_board_no_from_list(), find_latest_board_no_via_browser(), get_latest(), load_previous() (+3 more)

### Community 24 - "renderHpaiTab"
Cohesion: 0.20
Nodes (14): hgAdminBar(), hgCircled(), hgFmt(), hgItemLocs(), hgPosByKey(), hgPositions(), hgSelOptions(), hpaiAnatomyImg() (+6 more)

### Community 25 - "steps"
Cohesion: 0.07
Nodes (29): ANTHROPIC_API_KEY, FIREBASE_SERVICE_ACCOUNT_JSON, QUICK_EXTRA_URLS, SMS_RELAY_SECRET, SMS_RELAY_URL, runs-on, steps, urls (+21 more)

### Community 26 - "vcFigPress"
Cohesion: 0.38
Nodes (11): vcChick(), vcFan(), vcFig(), vcFigHouse(), vcFigInlet(), vcFigModes(), vcFigPress(), vcFigWhy() (+3 more)

### Community 27 - "json"
Cohesion: 0.07
Nodes (32): base_params(), build(), slot(), species(), fetch_periods(), fetch_table(), keep_previous(), label_period() (+24 more)

### Community 28 - "pfTabSpecies"
Cohesion: 0.17
Nodes (24): pfBar(), pfChips(), pfControls(), pfHz(), pfImportBrief(), pfInsufficientHtml(), pfKpi(), pfPct1() (+16 more)

### Community 29 - "renderSelfCheckPanel"
Cohesion: 0.15
Nodes (22): bodyPartByKey(), bodyPartLabel(), cardCandToBackImage(), currentOrganFunctions(), currentSelfCheckDiseases(), findCardImage(), newSelfCheckKey(), organFunctionFor() (+14 more)

### Community 30 - "renderFeedGrainFlow"
Cohesion: 0.08
Nodes (28): fgBadge(), fgDetailRows(), fgImplication(), fgLevelOf(), fgMeter(), fgMoldLevel(), fgMoldStrip(), fgMoldType() (+20 more)

### Community 31 - "gmVirus"
Cohesion: 0.22
Nodes (16): ibBind(), ibData(), ibEffStage(), ibHash(), ibLectureList(), ibMarkRead(), ibPickLecture(), ibPublish() (+8 more)

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

### Community 69 - "xml_etree_elementtree"
Cohesion: 0.28
Nodes (9): call_api(), diff(), get_api_key(), ival(), main(), filter_type(), probe_url(), sval() (+1 more)

### Community 70 - "time"
Cohesion: 0.13
Nodes (13): load(), main(), v(), merge_rows(), fetch_window(), main(), customs_get(), customs_variants() (+5 more)

### Community 71 - "steps"
Cohesion: 0.10
Nodes (19): FIREBASE_SERVICE_ACCOUNT_JSON, SMS_RELAY_SECRET, SMS_RELAY_URL, jobs, send, name, on, schedule (+11 more)

### Community 72 - "isBoardAdmin"
Cohesion: 0.05
Nodes (56): What this is, attachDiseaseResultEvents(), attachDzCustomEvents(), attachDzPhotoEvents(), boardShrinkPhoto(), currentFarmFaq(), diseaseListing(), diseaseMatches() (+48 more)

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
Cohesion: 0.20
Nodes (10): build_category(), efetch_articles(), esearch_pmids(), fallback_translation(), google_translate(), load_previous(), main(), _text() (+2 more)

### Community 77 - "render"
Cohesion: 0.08
Nodes (51): currentPremiumMenuItems(), dzStatsBind(), fetchAllSmsSubscriptions(), fetchDiseaseBrief(), fetchDiseaseDisinfectants(), fetchDrugNews(), fetchDrugUse(), fetchDzStats() (+43 more)

### Community 78 - "ocr_jungchu_table.js"
Cohesion: 0.17
Nodes (15): sharp, tesseract.js, { createWorker }, isRowValid(), main(), ocrTableRows(), parseRow(), sharp (+7 more)

### Community 79 - "renderDrugSearchPanel"
Cohesion: 0.29
Nodes (8): drugEfficacySnippet(), drugFormCategory(), drugModePlaceholder(), drugStandardPacks(), drugWithdrawalForPoultry(), renderDrugKindSelect(), renderDrugSearchPanel(), renderDrugUseForm()

### Community 80 - "fetch_h5n1_human.py"
Cohesion: 0.21
Nodes (11): download(), main(), read_csv_bytes(), to_int(), build(), _clean_name(), find_table_page(), _int() (+3 more)

### Community 81 - "fetchWithTimeout"
Cohesion: 0.07
Nodes (46): Data is also mirrored to Firebase Storage (so the repo can go private), Working in index.html, getPublicContent(), dataDatasetOf(), emergAnalyze(), emergEsearch(), emergEsummary(), emergFmtDate() (+38 more)

### Community 82 - "tradeItem"
Cohesion: 0.16
Nodes (17): pfFmtN(), pfTon(), renderTradeInPriceTab(), renderTradePanel(), tradeBadge(), tradeItem(), tradeKpi(), tradeModel() (+9 more)

### Community 83 - "fetch_hpai_risk.py"
Cohesion: 0.22
Nodes (8): build(), day(), fetch_events(), get_json(), is_hpai(), is_wild(), keep_previous(), main()

### Community 84 - "fetchWeather"
Cohesion: 0.19
Nodes (13): anomCompute(), anomDoy(), anomLoadClimatology(), anomLoadEnsemble(), anomMean(), anomPct(), anomRun(), anomSd() (+5 more)

### Community 85 - "What this is"
Cohesion: 0.29
Nodes (8): assertAdmin(), deleteMemberAccount(), getBoardPosts(), getMemberProfiles(), getSmsSubscriptions(), readJsonFile(), resetMemberAccount(), setMemberApproval()

### Community 86 - "callClaude"
Cohesion: 0.24
Nodes (11): analyzeNecropsyPhotos(), Anthropic, callClaude(), chickenChat(), chickenChatLength(), chickenChatPersona(), extractMagazineText(), generateAiDraft() (+3 more)

### Community 87 - "sendDirectSms"
Cohesion: 0.22
Nodes (10): casUsage(), getFarmGameSaves(), getFeatureRequests(), getPremiumContent(), isApprovedOrAdmin(), kstDateString(), memberActiveToday(), sendDirectSms() (+2 more)

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

### Community 92 - "renderHpaiTab"
Cohesion: 0.24
Nodes (10): flySrcLinks(), h5hYearChart(), hpaiBadge(), hpaiSplitBar(), hpaiTagline(), renderFlywayCard(), renderHpaiDataCards(), renderHpaiHumanCard() (+2 more)

### Community 93 - "commons.js"
Cohesion: 0.43
Nodes (7): fetchCandidateImage(), findCommonsCandidates(), IMAGE_MIME, searchCommons(), stripHtml(), thumbAt(), findCardImage()

### Community 94 - "renderGrainPriceCard"
Cohesion: 0.48
Nodes (7): gpCol(), gpDir(), gpPct(), gpRange(), gpSpark(), renderGrainPriceCard(), renderGrainPricePanel()

### Community 95 - "renderColiPanel"
Cohesion: 0.36
Nodes (8): coliBox(), coliSvgTimeline(), coliSvgTreat(), coliTable(), renderColiCases(), renderColiCompare(), renderColiPanel(), renderColiTreat()

### Community 96 - "renderSeasonalPanel"
Cohesion: 0.08
Nodes (49): buildSmsDigestText(), currentFinderCases(), currentSeasonalPackages(), currentTreatmentPackages(), currentVaccinePrograms(), finderCasesForCategory(), finderCasesForSpecies(), finderCategoriesFor() (+41 more)

### Community 97 - "renderWelfareResult"
Cohesion: 0.53
Nodes (6): renderWelfareResult(), wfBroilerRows(), wfFmt(), wfLayerRows(), wfNum(), wfRow()

### Community 98 - "switchTab"
Cohesion: 0.09
Nodes (27): buildDiseaseSearch(), buildSmsDigestTextAsync(), dzCustomToEntry(), dzMergeCustom(), emergSendToNews(), fetchDiseases(), fetchHpaiGuide(), fetchHpaiNews() (+19 more)

### Community 99 - "gmT"
Cohesion: 0.07
Nodes (105): currentDiseaseDisinfectants(), disinfectProductsToText(), dsBanner(), dsBasic(), dsBug(), dsDisease(), dsFigBirds(), dsFigFlow() (+97 more)

### Community 100 - "fetchQiaSearch"
Cohesion: 0.07
Nodes (39): attachDrugDetails(), bindDrugPickerEvents(), choseongMatchIndex(), closeDrugPicker(), dropExportOnly(), drugPickerOverlayHtml(), drugSymptomSuggestions(), drugUseSearchLinks() (+31 more)

### Community 102 - "authDialog"
Cohesion: 0.67
Nodes (3): authDialog(), premiumResetPassword(), premiumSignInEmail()

### Community 103 - "fetch_notices.py"
Cohesion: 0.25
Nodes (8): clean(), fetch_board(), get_html(), main(), parse_chicken_assoc(), parse_dailyvet(), parse_gnuboard(), parse_news_site()

### Community 104 - "renderStudyPanel"
Cohesion: 0.40
Nodes (5): commonsImageCredit(), currentStudyDecks(), renderStudyPanel(), studyBackImageCredit(), studyThemeFor()

### Community 105 - "farmGameCall"
Cohesion: 0.39
Nodes (8): farmGameCall(), farmGameErrMsg(), farmGameNickKey(), farmGameUser(), list(), load(), remove(), save()

### Community 106 - "urllib_parse"
Cohesion: 0.17
Nodes (7): fetch_html(), main(), parse_price_table(), fetch_html(), main(), normalize_date(), parse_egg_price_html()

### Community 107 - "drugUseCard"
Cohesion: 0.40
Nodes (5): drugUseCard(), drugUseKindBadge(), drugUseKindColor(), drugUseSafeUrl(), drugUseSection()

### Community 108 - "pfSeries"
Cohesion: 0.16
Nodes (20): pfAdminHtml(), pfBanner(), pfClean(), pfEvidence(), pfFeedMonths(), pfHeatmaps(), pfImportHtml(), pfImportItem() (+12 more)

### Community 110 - "renderDiseaseTab"
Cohesion: 0.40
Nodes (5): lmEggSvg(), lmPhotosHtml(), renderDiseaseTab(), renderDzForm(), renderLifeMiracleCard()

### Community 113 - "renderHpaiKrCard"
Cohesion: 0.19
Nodes (16): Commands, graphify (토큰 절약용 코드 지식 그래프), Workflow preference (owner's standing instruction), hkCount(), hkFarms(), hkFmt(), hkInPeriod(), hkMonth() (+8 more)

### Community 114 - "renderBroilerPriceTodayPanel"
Cohesion: 0.40
Nodes (5): priceDeltaHtml(), renderBroilerPriceTodayPanel(), renderJungchuPriceCard(), renderPoultryPriceLine(), renderTaxfreeFuelBlock()

### Community 115 - "renderNoticesSection"
Cohesion: 0.40
Nodes (5): renderBriefingTab(), renderNoticesSection(), noticeList(), noticeListGlobal(), renderPolicySection()

### Community 116 - "ibLossBind"
Cohesion: 0.83
Nodes (4): ibLossBind(), ibLossCalc(), ibLossHtml(), ibLossLoad()

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
Nodes (39): fmtLunar(), isEmbedded(), isPremiumApproved(), kkokoBumpUsage(), kkokoCharacterBlock(), kkokoDailyLimit(), kkokoDisplayName(), kkokoGreeting() (+31 more)

### Community 121 - "renderFeedStandardPanel"
Cohesion: 0.67
Nodes (3): renderFeedSpecTable(), renderFeedStageRow(), renderFeedStandardPanel()

### Community 122 - "dilResultHtml"
Cohesion: 0.50
Nodes (5): dilBind(), dilCalc(), dilFmt(), dilResultHtml(), renderDilutionCard()

### Community 124 - "renderWeatherNewsCard"
Cohesion: 0.40
Nodes (5): renderWeatherNewsCard(), wnAgo(), wnCard(), wnLink(), wnThin()

### Community 125 - "gmBind"
Cohesion: 0.40
Nodes (5): dsBind(), gmBind(), gmDilBox(), gmDilOut(), gmSave()

## Knowledge Gaps
- **1 isolated node(s):** `RFC-822`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1170 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Architecture: the fetch-script → JSON → dashboard pipeline` connect `Architecture: the fetch-script → JSON → dashboard pipeline` to `ibTag`, `attachEvents`, `index.js`, `fetch_animal_drug_news.py`, `ibCardify`, `esc`, `attachDiseaseEvents`, `renderConsultTab`, `re`, `coliFigFor`, `renderHusbandryPointsCard`, `send_sms_subscriptions.py`, `json`, `renderFeedGrainFlow`, `gmVirus`, `renderFeedPotentialPanel`, `fetch_broiler_breeder.py`, `renderLightClock`, `pfForecast`, `isBoardAdmin`, `render`, `fetchWithTimeout`, `tradeItem`, `fetchWeather`, `What this is`, `callClaude`, `sendDirectSms`, `renderDzStatsPanel`, `vcFigPress`, `renderHpaiTab`, `renderColiPanel`, `renderSeasonalPanel`, `switchTab`, `gmT`, `fetchQiaSearch`, `pfSeries`, `renderHpaiKrCard`, `ibLossBind`, `pfBuildModel`, `isPremiumApproved`, `dilResultHtml`, `gmBind`?**
  _High betweenness centrality (0.177) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `esc()` (e.g. with `dzFigTiles()` and `renderBizFooterLine()`) actually correct?**
  _`esc()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `RFC-822` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `index.inline.js` be split into smaller, more focused modules?**
  _Cohesion score 0.004597701149425287 - nodes in this community are weakly interconnected._
- **Why does `ai_extract()` connect `re` to `Architecture: the fetch-script → JSON → dashboard pipeline`, `json`, `fetch_animal_drug_news.py`, `time`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Are the 171 inferred relationships involving `Architecture: the fetch-script → JSON → dashboard pipeline` (e.g. with `analyzeNecropsyPhotos()` and `fetchRssItems()`) actually correct?**
  _`Architecture: the fetch-script → JSON → dashboard pipeline` has 171 INFERRED edges - model-reasoned connections that need verification._
- **Should `attachEvents` be split into smaller, more focused modules?**
  _Cohesion score 0.03731343283582089 - nodes in this community are weakly interconnected._