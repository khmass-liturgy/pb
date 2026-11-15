# Graph Report - pb  (2026-11-15)

## Corpus Check
- 129 files · ~941,073 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 6 file(s) not represented in the graph (top: (none) 4, .glb 1, .rules 1)

## Summary
- 3257 nodes · 7553 edges · 137 communities (130 shown, 7 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 312 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `463e28b4`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- index.inline.js
- ibTag
- attachEvents
- index.js
- hzNearBox
- fetch_animal_drug_news.py
- renderIbTeamPanel
- render
- time
- esc
- fetchPremiumContentJson
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
- fetch_feed_production.py
- isPremiumApproved
- json
- renderHpaiTab
- steps
- switchTab
- fetch_h5n1_human.py
- fetchQiaSearch
- renderVaccinePanel
- renderFeedGrainFlow
- send_sms_subscriptions.py
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
- Architecture: the fetch-script → JSON → dashboard pipeline
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
- hg
- pfTabSpecies
- steps
- renderDisinfectPanel
- steps
- steps
- steps
- gmVirus
- hzBind
- ocr_jungchu_table.js
- renderSelfCheckPanel
- renderWeatherTab
- fetchNotices
- tradeItem
- fetch_hpai_risk.py
- renderHpaiZeroPanel
- What this is
- callClaude
- pfBind
- publishPublicContent
- phFig
- vcFigPress
- fetch_poultry_diseases.py
- requests
- commons.js
- renderGrainPriceCard
- sgBind
- renderPremiumTab
- renderSeasonalPanel
- fetch_weather_news.py
- gmT
- pfBuildModel
- fetch_taxfree_fuel.py
- authDialog
- fetch_notices.py
- fetch_usda_crop_progress.py
- farmGameCall
- urllib_parse
- What this is
- currentSelfCheckDiseases
- hzBox
- os
- renderHpaiKrCard
- pfSeries
- gmHome
- fetchWeather
- renderMonthlyPick
- fetchStockPrices
- translation_glossary.py
- dzAutoFig
- renderSmsAdminPanel
- attachDzCustomEvents
- fetchPortalNews
- renderDrugSearchPanel
- CLAUDE.md
- renderColiEasy
- 작업 인계 노트 (2026-10-13)
- hgPositions
- rmBind
- renderBroilerOutlookPanel
- gmBind
- pfGrade
- renderPhPanel
- setupTabArrows
- sgBase

## God Nodes (most connected - your core abstractions)
1. `esc()` - 205 edges
2. `attachEvents()` - 161 edges
3. `Architecture: the fetch-script → JSON → dashboard pipeline` - 129 edges
4. `render()` - 123 edges
5. `renderPremiumTab()` - 85 edges
6. `gmT()` - 69 edges
7. `gmSvg()` - 66 edges
8. `gmBox()` - 58 edges
9. `fetchWithTimeout()` - 50 edges
10. `ibTag()` - 50 edges

## Surprising Connections (you probably didn't know these)
- `graphify (토큰 절약용 코드 지식 그래프)` --references--> `renderHpaiKrLiveStrip()`  [INFERRED]
  CLAUDE.md → graphify-src/index.inline.js
- `Architecture: the fetch-script → JSON → dashboard pipeline` --references--> `fetchWeatherData()`  [INFERRED]
  CLAUDE.md → functions/index.js
- `Working in index.html` --references--> `fetchPoultryPrices()`  [INFERRED]
  CLAUDE.md → graphify-src/index.inline.js
- `Architecture: the fetch-script → JSON → dashboard pipeline` --references--> `premiumMenuItemsFull()`  [INFERRED]
  CLAUDE.md → graphify-src/index.inline.js
- `Architecture: the fetch-script → JSON → dashboard pipeline` --references--> `premiumMenuCats()`  [INFERRED]
  CLAUDE.md → graphify-src/index.inline.js

## Import Cycles
- None detected.

## Communities (137 total, 7 thin omitted)

### Community 0 - "index.inline.js"
Cohesion: 0.00
Nodes (408): RFC-822, ANOM_MD_START, anomState, ARBORACRES_DATA, AUTUMN_BR_DAILY, AUTUMN_BR_DISEASES, AUTUMN_BR_HUSB, AUTUMN_BR_SYM (+400 more)

### Community 1 - "ibTag"
Cohesion: 0.28
Nodes (62): 1. 전염성기관지염(IB) 차단 AI공동연구팀 (유료서비스 최상단 `ibteam`), ibBox(), ibChecklist(), ibField(), ibFlow(), ibGenomeBar(), ibH(), ibLecture1() (+54 more)

### Community 2 - "attachEvents"
Cohesion: 0.04
Nodes (66): ageDays(), attachEvents(), calcProductionIndex(), calcRequiredAdg(), callMemberFunction(), coliBind(), coliSave(), createFirebaseMemberAccount() (+58 more)

### Community 3 - "index.js"
Cohesion: 0.09
Nodes (29): admin, ADMIN_EMAILS, AI_DRAFT_KINDS, ANTHROPIC_API_KEY, BOARD_TYPES, casUsage(), { defineSecret }, fetchRssItems() (+21 more)

### Community 4 - "hzNearBox"
Cohesion: 0.22
Nodes (24): hkAllFarms(), hkAllWild(), hzAddDays(), hzBacktest(), hzBacktest2(), hzBtDates(), hzDaysAgo(), hzDensBacktest() (+16 more)

### Community 5 - "fetch_animal_drug_news.py"
Cohesion: 0.07
Nodes (43): Conventions shared across all fetch scripts, build_item(), category_guess(), claude(), collect(), friday_of(), main(), parse_json() (+35 more)

### Community 6 - "renderIbTeamPanel"
Cohesion: 0.17
Nodes (20): ibBind(), ibData(), ibEffStage(), ibHash(), ibLectureList(), ibLossBind(), ibLossCalc(), ibLossHtml() (+12 more)

### Community 7 - "render"
Cohesion: 0.10
Nodes (41): Data is also mirrored to Firebase Storage (so the repo can go private), getPublicContent(), dataDatasetOf(), emergAnalyze(), emergEsearch(), emergEsummary(), emergFmtDate(), emergLoad() (+33 more)

### Community 8 - "time"
Cohesion: 0.15
Nodes (15): customs_get(), customs_variants(), fetch_comtrade(), fetch_customs(), http_get(), main(), month_list(), convert() (+7 more)

### Community 9 - "esc"
Cohesion: 0.07
Nodes (44): allSites(), boardStatusBadge(), currentBoardCfg(), disinfectFlowHtml(), esc(), fetchInboxBoardPosts(), fetchMyBoardPosts(), lmEggSvg() (+36 more)

### Community 10 - "fetchPremiumContentJson"
Cohesion: 0.09
Nodes (27): fetchDiseaseDisinfectants(), fetchFarmFaq(), fetchFarmFinderCases(), fetchIbContent(), fetchMagazineNotes(), fetchNewProducts(), fetchPremiumContentJson(), fetchSeasonalPackages() (+19 more)

### Community 11 - "attachDiseaseEvents"
Cohesion: 0.18
Nodes (13): attachDiseaseEvents(), currentHpaiAuto(), currentHpaiNews(), hgClone(), hgNormalizeDraft(), newHpaiNewsId(), newPickId(), publishHpaiNews() (+5 more)

### Community 12 - "renderConsultTab"
Cohesion: 0.07
Nodes (38): broilerEquivDay(), calcDewPointC(), calcHumidityRatio(), calcVentilationRate(), fcAlertOn(), fcInputBox(), fcNum(), fcResultCard() (+30 more)

### Community 13 - "re"
Cohesion: 0.11
Nodes (26): ai_extract(), _candidates(), clean_quick(), clean_wild(), _date(), fetch_news(), fetch_quick_news(), fetch_table_data() (+18 more)

### Community 14 - "fetch_poultry_price.py"
Cohesion: 0.06
Nodes (30): load(), main(), v(), merge_rows(), fetch_window(), main(), parse_window(), cell_number() (+22 more)

### Community 15 - "fetch_briefing_news.py"
Cohesion: 0.10
Nodes (15): clean_text(), fetch_source(), get_with_proxy_fallback(), kst_label(), main(), parse_aflnews(), parse_chuksan(), parse_handon() (+7 more)

### Community 16 - "coliFigFor"
Cohesion: 0.07
Nodes (37): autumnFig(), autumnSvgChain(), autumnSvgEggRule(), autumnSvgLayerSign(), autumnSvgResp(), coliBox(), coliFig(), coliFig2For() (+29 more)

### Community 17 - "renderHusbandryPointsCard"
Cohesion: 0.08
Nodes (24): anomIsCold(), anomIsHot(), anomPointsHtml(), anomTodayJudge(), anomTodayLine(), aviagenTargetTemp(), calcHeatStressIndex(), calcWetBulbC() (+16 more)

### Community 18 - "withStorageTimeout"
Cohesion: 0.10
Nodes (25): boardPostPath(), deleteFeatureRequest(), deleteMemberProfile(), featureRequestPostPath(), featureRequestRepliesPrefix(), fetchFeatureRequests(), fetchMemberProfiles(), fetchMySmsSubscription() (+17 more)

### Community 19 - "steps"
Cohesion: 0.06
Nodes (34): concurrency, cancel-in-progress, group, ANTHROPIC_API_KEY, FIREBASE_SERVICE_ACCOUNT_JSON, FORCE, ONCE_KEYWORD, default (+26 more)

### Community 20 - "steps"
Cohesion: 0.06
Nodes (33): description, required, CUSTOMS_ONLY, DATA_GO_KR_KEY, FIREBASE_SERVICE_ACCOUNT_JSON, FULL, SMS_RELAY_SECRET, SMS_RELAY_URL (+25 more)

### Community 21 - "fetch_feed_production.py"
Cohesion: 0.15
Nodes (12): list_all_posts(), main(), _candidates(), fetch_year(), find_attachment(), _get(), group_series(), keep_previous() (+4 more)

### Community 22 - "isPremiumApproved"
Cohesion: 0.10
Nodes (29): fmtLunar(), isEmbedded(), isPremiumApproved(), kkokoBumpUsage(), kkokoCharacterBlock(), kkokoDailyLimit(), kkokoDisplayName(), kkokoGreeting() (+21 more)

### Community 23 - "json"
Cohesion: 0.08
Nodes (25): _diag_dump(), download_pdf(), _extract_board_nos(), fetch_detail(), find_latest_board_no_from_list(), find_latest_board_no_via_browser(), get_latest(), load_previous() (+17 more)

### Community 24 - "renderHpaiTab"
Cohesion: 0.15
Nodes (20): flySrcLinks(), h5hYearChart(), hgAdminBar(), hgFmt(), hgSelOptions(), hpaiBadge(), hpaiLocTags(), hpaiPhotoStrip() (+12 more)

### Community 25 - "steps"
Cohesion: 0.07
Nodes (29): ANTHROPIC_API_KEY, FIREBASE_SERVICE_ACCOUNT_JSON, QUICK_EXTRA_URLS, SMS_RELAY_SECRET, SMS_RELAY_URL, runs-on, steps, urls (+21 more)

### Community 26 - "switchTab"
Cohesion: 0.11
Nodes (21): buildDiseaseSearch(), buildSmsDigestTextAsync(), dzCustomToEntry(), dzMergeCustom(), emergSendToNews(), fetchDiseases(), fetchHpaiGuide(), fetchHpaiNews() (+13 more)

### Community 27 - "fetch_h5n1_human.py"
Cohesion: 0.17
Nodes (11): download(), main(), read_csv_bytes(), to_int(), build(), _clean_name(), find_table_page(), _int() (+3 more)

### Community 28 - "fetchQiaSearch"
Cohesion: 0.06
Nodes (45): attachDrugDetails(), bindDrugPickerEvents(), choseongMatchIndex(), closeDrugPicker(), dropExportOnly(), drugPickerOverlayHtml(), drugSymptomSuggestions(), drugUseBind() (+37 more)

### Community 29 - "renderVaccinePanel"
Cohesion: 0.12
Nodes (28): currentFinderCases(), currentVaccinePrograms(), finderCasesForCategory(), finderCasesForSpecies(), finderCategoriesFor(), finderSpeciesLabel(), pkgCardHtml(), pkgCautionHtml() (+20 more)

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
Cohesion: 0.14
Nodes (21): bbChartSvg(), bbDelta(), bbMan(), bbMonth(), bbPctOf(), bbYm(), fpBirds(), fpChart() (+13 more)

### Community 37 - "renderLightCalc"
Cohesion: 0.11
Nodes (25): bindSmsBox(), brClock(), brDark(), brFmtDate(), brLux(), brSchedule(), brSmsText(), lgChartSvg() (+17 more)

### Community 38 - "fetch_jungchu_price.py"
Cohesion: 0.13
Nodes (9): find_image_url(), find_post_url(), _get_bytes(), _get_text(), main(), run_ocr(), collect(), dataset_of() (+1 more)

### Community 39 - "fetch_broiler_breeder.py"
Cohesion: 0.05
Nodes (40): ask_claude(), build_forecast(), clean_outlook(), fit_adult(), _img_b64(), kreI_get(), _lstsq2(), main() (+32 more)

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

### Community 49 - "Architecture: the fetch-script → JSON → dashboard pipeline"
Cohesion: 0.07
Nodes (44): Architecture: the fetch-script → JSON → dashboard pipeline, boardShrinkPhoto(), farmGameBind(), farmGameCloseWin(), farmGameOpenWin(), ibCardify(), ibIsHead(), ibSlim() (+36 more)

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

### Community 69 - "hg"
Cohesion: 0.33
Nodes (7): hg(), hgDefaults(), hgHtml2Md(), hgPlain(), hpaiEarlyCheck(), hpaiTelHref(), renderHpaiCheckResult()

### Community 70 - "pfTabSpecies"
Cohesion: 0.18
Nodes (23): pfBar(), pfChips(), pfControls(), pfHz(), pfImportBrief(), pfInsufficientHtml(), pfKpi(), pfPct1() (+15 more)

### Community 71 - "steps"
Cohesion: 0.10
Nodes (19): FIREBASE_SERVICE_ACCOUNT_JSON, SMS_RELAY_SECRET, SMS_RELAY_URL, jobs, send, name, on, schedule (+11 more)

### Community 72 - "renderDisinfectPanel"
Cohesion: 0.16
Nodes (20): currentDiseaseDisinfectants(), dilBind(), dilCalc(), dilFmt(), dilResultHtml(), disinfectProductsToText(), dsBanner(), dsBasic() (+12 more)

### Community 73 - "steps"
Cohesion: 0.11
Nodes (17): runs-on, steps, SMS_RELAY_SECRET, SMS_RELAY_URL, jobs, backfill-feed, name, on (+9 more)

### Community 74 - "steps"
Cohesion: 0.11
Nodes (17): FIREBASE_SERVICE_ACCOUNT_JSON, jobs, sync-storage, name, on, push, workflow_dispatch, branches (+9 more)

### Community 75 - "steps"
Cohesion: 0.11
Nodes (17): TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, jobs, send, name, on, schedule, workflow_dispatch (+9 more)

### Community 76 - "gmVirus"
Cohesion: 0.17
Nodes (22): dsBug(), dsFigTypes(), dzFigCauseIcon(), gmAb(), gmCellInner(), gmCoccus(), gmFigGrow(), gmFigHistory() (+14 more)

### Community 77 - "hzBind"
Cohesion: 0.16
Nodes (18): 1-2. HPAI ZERO FARM (유료서비스 · AI공동연구팀, `hpaizero`), hzBind(), hzBtSummary(), hzBtSummaryLine(), hzLift(), hzLocate(), hzNearestSgg(), hzNearLevel1() (+10 more)

### Community 78 - "ocr_jungchu_table.js"
Cohesion: 0.17
Nodes (15): sharp, tesseract.js, { createWorker }, isRowValid(), main(), ocrTableRows(), parseRow(), sharp (+7 more)

### Community 79 - "renderSelfCheckPanel"
Cohesion: 0.16
Nodes (20): bodyPartByKey(), bodyPartLabel(), commonsImageCredit(), organFunctionFor(), pkgBoxStyle(), pkgChip(), pkgIconCircle(), renderDiseaseBriefPanel() (+12 more)

### Community 80 - "renderWeatherTab"
Cohesion: 0.15
Nodes (14): renderAnomalyPanel(), renderHeaderSolarTerm(), renderSolarTermPanel(), renderWeatherNewsCard(), renderWeatherSobakCard(), renderWeatherTab(), solarTermInfo(), stBisect() (+6 more)

### Community 81 - "fetchNotices"
Cohesion: 0.26
Nodes (13): Working in index.html, fetchDabomPrices(), fetchEconNews(), fetchNotices(), fetchOneSite(), fetchPolicyNews(), fmtKST(), loadNoticeCache() (+5 more)

### Community 82 - "tradeItem"
Cohesion: 0.20
Nodes (14): pfFmtN(), pfTon(), tradeBadge(), tradeItem(), tradeKpi(), tradeMoney(), tradeOverview(), tradePartnerBar() (+6 more)

### Community 83 - "fetch_hpai_risk.py"
Cohesion: 0.22
Nodes (8): build(), day(), fetch_events(), get_json(), is_hpai(), is_wild(), keep_previous(), main()

### Community 84 - "renderHpaiZeroPanel"
Cohesion: 0.17
Nodes (16): hzCard(), hzGrid(), hzHomeStatus(), hzSection(), hzStageProgress(), hzSteps(), hzTabs(), hzTaskId() (+8 more)

### Community 85 - "What this is"
Cohesion: 0.23
Nodes (14): What this is, assertAdmin(), deleteMemberAccount(), getApprovedMembers(), getBoardPosts(), getMemberProfiles(), getSmsSubscriptions(), readJsonFile() (+6 more)

### Community 86 - "callClaude"
Cohesion: 0.24
Nodes (11): analyzeNecropsyPhotos(), Anthropic, callClaude(), chickenChat(), chickenChatLength(), chickenChatPersona(), extractMagazineText(), generateAiDraft() (+3 more)

### Community 87 - "pfBind"
Cohesion: 0.17
Nodes (15): pfApplyLocal(), pfBind(), pfBindCharts(), pfDownload(), pfIngest(), pfLog(), pfMergeRows(), pfNormDate() (+7 more)

### Community 88 - "publishPublicContent"
Cohesion: 0.25
Nodes (8): hgNewKey(), hgPublish(), publicContentPath(), publishPicks(), publishPremiumMenuItems(), publishPublicContent(), saveDiseaseCustom(), writePublicContentJson()

### Community 89 - "phFig"
Cohesion: 0.40
Nodes (10): phArrow(), phFig(), phFigCirc(), phFigDigest(), phFigExcrete(), phFigHormone(), phFigNeuro(), phFigRepro() (+2 more)

### Community 90 - "vcFigPress"
Cohesion: 0.13
Nodes (25): vcChick(), vcFan(), vcFig(), vcFigHouse(), vcFigInlet(), vcFigModes(), vcFigPress(), vcFigWhy() (+17 more)

### Community 91 - "fetch_poultry_diseases.py"
Cohesion: 0.12
Nodes (10): get(), load_extra(), load_previous(), main(), merge_only(), parse_detail(), parse_index(), save() (+2 more)

### Community 92 - "requests"
Cohesion: 0.13
Nodes (19): call_api(), diff(), get_api_key(), ival(), main(), filter_type(), probe_url(), sval() (+11 more)

### Community 93 - "commons.js"
Cohesion: 0.43
Nodes (7): fetchCandidateImage(), findCommonsCandidates(), IMAGE_MIME, searchCommons(), stripHtml(), thumbAt(), findCardImage()

### Community 94 - "renderGrainPriceCard"
Cohesion: 0.48
Nodes (7): gpCol(), gpDir(), gpPct(), gpRange(), gpSpark(), renderGrainPriceCard(), renderGrainPricePanel()

### Community 95 - "sgBind"
Cohesion: 0.18
Nodes (11): sgBind(), sgDraftToGuide(), sgHusbToText(), sgIssuesToText(), sgOpenEdit(), sgParseHusb(), sgParseIssues(), sgParseRows() (+3 more)

### Community 96 - "renderPremiumTab"
Cohesion: 0.07
Nodes (40): currentPremiumMenuItems(), drugUseAllKinds(), drugUseForm(), drugUseSearchLinks(), emergTrendBadge(), featureBoardAuthorLabel(), featureBoardReplyLabel(), isAdmin() (+32 more)

### Community 97 - "renderSeasonalPanel"
Cohesion: 0.20
Nodes (15): buildSmsDigestText(), currentSeasonalPackages(), currentTreatmentPackages(), pkgEmptyHtml(), pkgSectionTitle(), renderSeasonalPanel(), renderSeasonGuide(), seasonalPackagesFor() (+7 more)

### Community 98 - "fetch_weather_news.py"
Cohesion: 0.23
Nodes (10): ai_summary(), cap_items(), enrich(), main(), order_tags(), relevant(), search(), tags_for() (+2 more)

### Community 99 - "gmT"
Cohesion: 0.16
Nodes (51): dsFigBirds(), dsFigFlow(), dsFigFume(), gmArrow(), gmBox(), gmE(), gmFigAbAg(), gmFigAst() (+43 more)

### Community 100 - "pfBuildModel"
Cohesion: 0.50
Nodes (4): pfBuildModel(), pfClip(), pfProbs(), pfYoY()

### Community 101 - "fetch_taxfree_fuel.py"
Cohesion: 0.25
Nodes (6): fetch_html(), main(), parse(), day(), parse_day(), year_ago()

### Community 102 - "authDialog"
Cohesion: 0.67
Nodes (3): authDialog(), premiumResetPassword(), premiumSignInEmail()

### Community 103 - "fetch_notices.py"
Cohesion: 0.25
Nodes (8): clean(), fetch_board(), get_html(), main(), parse_chicken_assoc(), parse_dailyvet(), parse_gnuboard(), parse_news_site()

### Community 104 - "fetch_usda_crop_progress.py"
Cohesion: 0.23
Nodes (9): fetch_text(), history_point(), list_releases(), main(), _num(), parse_report(), split_sections(), table_rows() (+1 more)

### Community 105 - "farmGameCall"
Cohesion: 0.39
Nodes (8): farmGameCall(), farmGameErrMsg(), farmGameNickKey(), farmGameUser(), list(), load(), remove(), save()

### Community 106 - "urllib_parse"
Cohesion: 0.09
Nodes (9): fetch_html(), main(), parse_price_table(), PriceTableParser, fetch_html(), main(), normalize_date(), parse_egg_price_html() (+1 more)

### Community 107 - "What this is"
Cohesion: 0.19
Nodes (13): diseaseListing(), diseaseMatches(), diseaseSnippet(), dzCategories(), dzCatOf(), dzExtraFigs(), dzExtraRefs(), dzFigSpec() (+5 more)

### Community 108 - "currentSelfCheckDiseases"
Cohesion: 0.22
Nodes (13): cardCandToBackImage(), currentOrganFunctions(), currentSelfCheckDiseases(), findCardImage(), newSelfCheckKey(), publishOrganFunction(), publishSelfCheckContent(), publishSelfCheckDiseases() (+5 more)

### Community 109 - "hzBox"
Cohesion: 0.23
Nodes (12): hzBacktestBox(), hzBacktestBox2(), hzBox(), hzBt2Table(), hzClass(), hzDensEnsure(), hzDensityBox(), hzFarmReport() (+4 more)

### Community 110 - "os"
Cohesion: 0.31
Nodes (3): fetch_channel(), main(), parse_date()

### Community 113 - "renderHpaiKrCard"
Cohesion: 0.31
Nodes (13): hkCount(), hkFarms(), hkFmt(), hkInPeriod(), hkMonth(), hkNumLabel(), hkProvFill(), hkSeq() (+5 more)

### Community 114 - "pfSeries"
Cohesion: 0.19
Nodes (18): pfBanner(), pfClean(), pfEvidence(), pfFeedMonths(), pfHeatmaps(), pfImportHtml(), pfImportItem(), pfImportStatsHtml() (+10 more)

### Community 115 - "gmHome"
Cohesion: 0.22
Nodes (11): dsBind(), GM_DIRT(), gmFigFarm(), gmFinal(), gmLesson(), gmLessonKey(), gmPartDone(), gmPartHome() (+3 more)

### Community 116 - "fetchWeather"
Cohesion: 0.19
Nodes (13): anomCompute(), anomDoy(), anomLoadClimatology(), anomLoadEnsemble(), anomMean(), anomPct(), anomRun(), anomSd() (+5 more)

### Community 117 - "renderMonthlyPick"
Cohesion: 0.25
Nodes (8): countPicks(), currentPicks(), findPick(), localOnlyPicks(), monthKey(), monthLabel(), normalizePicks(), renderMonthlyPick()

### Community 118 - "fetchStockPrices"
Cohesion: 0.25
Nodes (8): fetchStockPrices(), fetchUpbitData(), fetchYahooQuote(), loadQuoteCache(), proxyRoutes(), saveCustomStocks(), saveQuoteCache(), sleep()

### Community 119 - "translation_glossary.py"
Cohesion: 0.43
Nodes (4): _ends_in_rieul(), _fix_trailing_particle(), _has_batchim(), _is_hangul_syllable()

### Community 120 - "dzAutoFig"
Cohesion: 0.33
Nodes (7): dzAutoFig(), dzFigTiles(), dzFigWrap(), dzFigWrapN(), wyFigMap(), wyHen(), wyNum()

### Community 121 - "renderSmsAdminPanel"
Cohesion: 0.33
Nodes (7): fetchAllSmsSubscriptions(), renderSmsAdminPanel(), renderSmsSubPanel(), smsIntervalLabel(), smsIsDue(), smsMenuLabel(), smsNextDueDate()

### Community 122 - "attachDzCustomEvents"
Cohesion: 0.33
Nodes (6): attachDiseaseResultEvents(), attachDzCustomEvents(), dzFormRead(), dzParseAiDraft(), generateAiDraft(), updateDiseaseResults()

### Community 124 - "fetchPortalNews"
Cohesion: 0.33
Nodes (6): emergNewsSearch(), fetchPortalNews(), fetchRssFallback(), fetchRssViaFunction(), parseRssXml(), searchHpaiPortalNews()

### Community 125 - "renderDrugSearchPanel"
Cohesion: 0.29
Nodes (8): drugEfficacySnippet(), drugFormCategory(), drugModePlaceholder(), drugStandardPacks(), drugWithdrawalForPoultry(), renderDrugKindSelect(), renderDrugSearchPanel(), renderDrugUseForm()

### Community 126 - "CLAUDE.md"
Cohesion: 0.40
Nodes (3): Commands, graphify (토큰 절약용 코드 지식 그래프), Workflow preference (owner's standing instruction)

### Community 127 - "renderColiEasy"
Cohesion: 0.39
Nodes (8): easyBtn(), easyCard(), easyHero(), easyList(), easyStep(), easyTwo(), renderColiEasy(), renderHzEasy()

### Community 128 - "작업 인계 노트 (2026-10-13)"
Cohesion: 0.40
Nodes (4): 0. 이어받는 세션이 먼저 할 일, 2. 최근 완료된 기능(이 세션, 2026-10-08 ~ 10-13, 모두 main 병합), 3. 환경 메모, 작업 인계 노트 (2026-10-13)

### Community 129 - "hgPositions"
Cohesion: 0.40
Nodes (5): hgCircled(), hgItemLocs(), hgPosByKey(), hgPositions(), hpaiAnatomyImg()

### Community 130 - "rmBind"
Cohesion: 0.67
Nodes (4): flyBind(), flyCensusTxt(), flyLoadLeaflet(), rmBind()

### Community 131 - "renderBroilerOutlookPanel"
Cohesion: 0.50
Nodes (4): olNum(), olPct(), olPriceChart(), renderBroilerOutlookPanel()

### Community 132 - "gmBind"
Cohesion: 0.67
Nodes (3): gmBind(), gmDilBox(), gmDilOut()

## Knowledge Gaps
- **1 isolated node(s):** `RFC-822`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1154 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Architecture: the fetch-script → JSON → dashboard pipeline` connect `Architecture: the fetch-script → JSON → dashboard pipeline` to `ibTag`, `attachEvents`, `index.js`, `gmBind`, `fetch_animal_drug_news.py`, `renderIbTeamPanel`, `render`, `time`, `esc`, `fetchPremiumContentJson`, `renderConsultTab`, `re`, `coliFigFor`, `renderHpaiTab`, `switchTab`, `fetchQiaSearch`, `renderVaccinePanel`, `renderFeedGrainFlow`, `send_sms_subscriptions.py`, `fetch_broiler_breeder.py`, `pfForecast`, `renderDisinfectPanel`, `gmVirus`, `What this is`, `callClaude`, `pfBind`, `vcFigPress`, `renderPremiumTab`, `gmT`, `pfBuildModel`, `renderHpaiKrCard`, `pfSeries`, `gmHome`, `fetchWeather`, `dzAutoFig`, `fetchPortalNews`, `CLAUDE.md`?**
  _High betweenness centrality (0.177) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `esc()` (e.g. with `dzFigTiles()` and `renderBizFooterLine()`) actually correct?**
  _`esc()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `RFC-822` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `index.inline.js` be split into smaller, more focused modules?**
  _Cohesion score 0.004694835680751174 - nodes in this community are weakly interconnected._
- **Why does `decode_google_url()` connect `fetch_animal_drug_news.py` to `fetch_weather_news.py`, `re`, `Architecture: the fetch-script → JSON → dashboard pipeline`, `json`, `requests`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Are the 125 inferred relationships involving `Architecture: the fetch-script → JSON → dashboard pipeline` (e.g. with `analyzeNecropsyPhotos()` and `fetchRssItems()`) actually correct?**
  _`Architecture: the fetch-script → JSON → dashboard pipeline` has 125 INFERRED edges - model-reasoned connections that need verification._
- **Should `attachEvents` be split into smaller, more focused modules?**
  _Cohesion score 0.035431235431235435 - nodes in this community are weakly interconnected._