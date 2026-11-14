# Graph Report - pb  (2026-11-14)

## Corpus Check
- 128 files · ~902,339 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 6 file(s) not represented in the graph (top: (none) 4, .glb 1, .rules 1)

## Summary
- 3232 nodes · 7471 edges · 125 communities (121 shown, 4 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 299 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e353dd92`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- index.inline.js
- ibTag
- attachEvents
- index.js
- hzNearBox
- requests
- fetch_grain_quality.py
- render
- json
- esc
- renderHpaiZeroPanel
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
- fetch_egg_report.py
- fetch_research_papers.py
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
- fetch_poultry_disease_brief.py
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
- gmVirus
- pfSeries
- ocr_jungchu_table.js
- renderSelfCheckPanel
- fetchWeather
- renderHpaiKrCard
- tradeItem
- fetch_hpai_risk.py
- fetch_layer_stats.py
- fetch_usda_crop_progress.py
- vcFigPress
- pfBind
- drugUseBind
- phFig
- vcNeed
- fetch_poultry_diseases.py
- renderDrugSearchPanel
- renderColiEasy
- renderGrainPriceCard
- sgDraftToGuide
- anomLoadClimatology
- renderSmsAdminPanel
- renderPremiumTab
- gmT
- pfBuildModel
- sys
- authDialog
- hzToday
- attachDzCustomEvents
- farmGameCall
- PriceTableParser
- emergLoad
- renderDisinfectPanel
- CLAUDE.md
- switchTab
- sgOpenEdit
- metConvert
- gmHome
- renderWeatherTab
- fetch_taxfree_fuel.py
- kkokoTouchCharacter
- renderVaccinePanel
- pfSign
- dilResultHtml
- hzBox
- renderHzTasks

## God Nodes (most connected - your core abstractions)
1. `esc()` - 198 edges
2. `attachEvents()` - 161 edges
3. `Architecture: the fetch-script → JSON → dashboard pipeline` - 129 edges
4. `render()` - 123 edges
5. `renderPremiumTab()` - 85 edges
6. `gmT()` - 67 edges
7. `gmSvg()` - 65 edges
8. `gmBox()` - 56 edges
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

## Communities (125 total, 4 thin omitted)

### Community 0 - "index.inline.js"
Cohesion: 0.00
Nodes (411): RFC-822, ANOM_MD_START, anomState, ARBORACRES_DATA, AUTUMN_BR_DAILY, AUTUMN_BR_DISEASES, AUTUMN_BR_HUSB, AUTUMN_BR_SYM (+403 more)

### Community 1 - "ibTag"
Cohesion: 0.18
Nodes (81): 1. 전염성기관지염(IB) 차단 AI공동연구팀 (유료서비스 최상단 `ibteam`), ibBind(), ibBox(), ibChecklist(), ibData(), ibEffStage(), ibField(), ibFlow() (+73 more)

### Community 2 - "attachEvents"
Cohesion: 0.03
Nodes (87): ageDays(), attachEvents(), callMemberFunction(), cardCandToBackImage(), coliBind(), coliSave(), createFirebaseMemberAccount(), currentFarmFaq() (+79 more)

### Community 3 - "index.js"
Cohesion: 0.05
Nodes (71): What this is, fetchCandidateImage(), findCommonsCandidates(), IMAGE_MIME, searchCommons(), stripHtml(), thumbAt(), admin (+63 more)

### Community 4 - "hzNearBox"
Cohesion: 0.23
Nodes (23): hkAllFarms(), hkAllWild(), hzAddDays(), hzBacktest(), hzBacktest2(), hzBtDates(), hzDensBacktest(), hzDensityPoints() (+15 more)

### Community 5 - "requests"
Cohesion: 0.08
Nodes (40): build_item(), category_guess(), claude(), collect(), friday_of(), main(), parse_json(), pick_with_claude() (+32 more)

### Community 6 - "fetch_grain_quality.py"
Cohesion: 0.14
Nodes (12): build_baseline(), build_region(), ensure_baseline(), fetch_rows(), load_json(), main(), mean_sd(), mold_scores() (+4 more)

### Community 7 - "render"
Cohesion: 0.07
Nodes (54): Data is also mirrored to Firebase Storage (so the repo can go private), getPublicContent(), buildSmsDigestTextAsync(), dataDatasetOf(), emergToggleAbstract(), emergTranslate(), emergTranslateTitles(), fetchBroilerBreeder() (+46 more)

### Community 8 - "json"
Cohesion: 0.07
Nodes (29): load(), main(), v(), merge_rows(), fetch_window(), main(), parse_window(), customs_get() (+21 more)

### Community 9 - "esc"
Cohesion: 0.08
Nodes (42): allSites(), boardStatusBadge(), currentBoardCfg(), diseaseSnippet(), disinfectFlowHtml(), esc(), fetchInboxBoardPosts(), fetchMyBoardPosts() (+34 more)

### Community 10 - "renderHpaiZeroPanel"
Cohesion: 0.14
Nodes (17): 0. 이어받는 세션이 먼저 할 일, 1-2. HPAI ZERO FARM (유료서비스 · AI공동연구팀, `hpaizero`), 2. 최근 완료된 기능(이 세션, 2026-10-08 ~ 10-13, 모두 main 병합), 3. 환경 메모, 작업 인계 노트 (2026-10-13), hzCard(), hzGrid(), hzHomeStatus() (+9 more)

### Community 11 - "attachDiseaseEvents"
Cohesion: 0.06
Nodes (46): attachDiseaseEvents(), attachDiseaseResultEvents(), countPicks(), currentHpaiAuto(), currentHpaiNews(), currentPicks(), diseaseListing(), diseaseMatches() (+38 more)

### Community 12 - "renderConsultTab"
Cohesion: 0.06
Nodes (43): broilerEquivDay(), calcDewPointC(), calcHumidityRatio(), calcProductionIndex(), calcRequiredAdg(), calcVentilationRate(), calcWetBulbC(), fcAlertOn() (+35 more)

### Community 13 - "re"
Cohesion: 0.08
Nodes (34): ai_extract(), _candidates(), clean_quick(), clean_wild(), _date(), fetch_news(), fetch_quick_news(), fetch_table_data() (+26 more)

### Community 14 - "fetch_poultry_price.py"
Cohesion: 0.11
Nodes (19): cell_number(), fetch_page(), latest_metric(), load_previous(), main(), normalize_date(), normalize_week_start(), normalize_year_month() (+11 more)

### Community 15 - "fetch_briefing_news.py"
Cohesion: 0.10
Nodes (15): clean_text(), fetch_source(), get_with_proxy_fallback(), kst_label(), main(), parse_aflnews(), parse_chuksan(), parse_handon() (+7 more)

### Community 16 - "coliFigFor"
Cohesion: 0.07
Nodes (37): autumnFig(), autumnSvgChain(), autumnSvgEggRule(), autumnSvgLayerSign(), autumnSvgResp(), coliBox(), coliFig(), coliFig2For() (+29 more)

### Community 17 - "renderHusbandryPointsCard"
Cohesion: 0.09
Nodes (23): anomIsCold(), anomIsHot(), anomPointsHtml(), anomTodayJudge(), anomTodayLine(), aviagenTargetTemp(), calcHeatStressIndex(), comfortActions() (+15 more)

### Community 18 - "withStorageTimeout"
Cohesion: 0.08
Nodes (29): boardPostPath(), deleteFeatureRequest(), deleteMemberProfile(), featureRequestPostPath(), featureRequestRepliesPrefix(), fetchFeatureRequests(), fetchMemberProfiles(), fetchMySmsSubscription() (+21 more)

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
Cohesion: 0.09
Nodes (30): fmtLunar(), isEmbedded(), isPremiumApproved(), kkokoBumpUsage(), kkokoCharacterBlock(), kkokoDailyLimit(), kkokoDisplayName(), kkokoGreeting() (+22 more)

### Community 23 - "fetch_egg_report.py"
Cohesion: 0.13
Nodes (11): _diag_dump(), download_pdf(), _extract_board_nos(), fetch_detail(), find_latest_board_no_from_list(), find_latest_board_no_via_browser(), get_latest(), load_previous() (+3 more)

### Community 24 - "fetch_research_papers.py"
Cohesion: 0.18
Nodes (10): build_category(), efetch_articles(), esearch_pmids(), fallback_translation(), google_translate(), load_previous(), main(), _text() (+2 more)

### Community 25 - "steps"
Cohesion: 0.07
Nodes (29): ANTHROPIC_API_KEY, FIREBASE_SERVICE_ACCOUNT_JSON, QUICK_EXTRA_URLS, SMS_RELAY_SECRET, SMS_RELAY_URL, runs-on, steps, urls (+21 more)

### Community 26 - "fetch_egg_price.py"
Cohesion: 0.13
Nodes (8): fetch_html(), main(), parse_price_table(), fetch_html(), main(), normalize_date(), parse_egg_price_html(), RowParser

### Community 27 - "fetch_h5n1_human.py"
Cohesion: 0.21
Nodes (11): download(), main(), read_csv_bytes(), to_int(), build(), _clean_name(), find_table_page(), _int() (+3 more)

### Community 28 - "fetchQiaSearch"
Cohesion: 0.09
Nodes (31): attachDrugDetails(), bindDrugPickerEvents(), choseongMatchIndex(), closeDrugPicker(), dropExportOnly(), drugPickerOverlayHtml(), drugSymptomSuggestions(), fetchQiaSearch() (+23 more)

### Community 29 - "renderSeasonalPanel"
Cohesion: 0.12
Nodes (27): buildSmsDigestText(), currentFinderCases(), currentSeasonalPackages(), currentTreatmentPackages(), finderCasesForCategory(), finderCasesForSpecies(), finderCategoriesFor(), finderSpeciesLabel() (+19 more)

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
Cohesion: 0.11
Nodes (25): bindSmsBox(), brClock(), brDark(), brFmtDate(), brLux(), brSchedule(), brSmsText(), lgChartSvg() (+17 more)

### Community 38 - "urllib_parse"
Cohesion: 0.12
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

### Community 49 - "Architecture: the fetch-script → JSON → dashboard pipeline"
Cohesion: 0.09
Nodes (36): Architecture: the fetch-script → JSON → dashboard pipeline, boardShrinkPhoto(), farmGameBind(), farmGameCloseWin(), farmGameOpenWin(), ibCardify(), ibIsHead(), ibSlim() (+28 more)

### Community 50 - "pfForecast"
Cohesion: 0.13
Nodes (27): pfBacktestDaily(), pfBacktestMonthly(), pfCalibrate(), pfCalibrationTable(), pfContrib(), pfDailyX(), pfFitDaily(), pfFitMonthly() (+19 more)

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

### Community 58 - "fetch_poultry_disease_brief.py"
Cohesion: 0.12
Nodes (17): Conventions shared across all fetch scripts, analyze(), choose(), claude(), clean_list(), listing(), main(), monday_of() (+9 more)

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
Cohesion: 0.11
Nodes (29): flySrcLinks(), h5hYearChart(), hg(), hgAdminBar(), hgCircled(), hgFmt(), hgItemLocs(), hgPosByKey() (+21 more)

### Community 70 - "pfTabSpecies"
Cohesion: 0.18
Nodes (23): pfBar(), pfChips(), pfControls(), pfHz(), pfImportBrief(), pfInsufficientHtml(), pfKpi(), pfPct1() (+15 more)

### Community 71 - "steps"
Cohesion: 0.10
Nodes (19): FIREBASE_SERVICE_ACCOUNT_JSON, SMS_RELAY_SECRET, SMS_RELAY_URL, jobs, send, name, on, schedule (+11 more)

### Community 72 - "fetchNotices"
Cohesion: 0.23
Nodes (14): Working in index.html, fetchDabomPrices(), fetchEconNews(), fetchEggReport(), fetchNotices(), fetchOneSite(), fetchPolicyNews(), fmtKST() (+6 more)

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
Cohesion: 0.13
Nodes (24): dsFigTypes(), gmAb(), gmCellInner(), gmCoccus(), gmFigAbAg(), gmFigAttack(), gmFigBactInside(), gmFigGrow() (+16 more)

### Community 77 - "pfSeries"
Cohesion: 0.21
Nodes (14): pfAdminHtml(), pfBanner(), pfClean(), pfFeedMonths(), pfFmtN(), pfHeatmaps(), pfMA(), pfMethodHtml() (+6 more)

### Community 78 - "ocr_jungchu_table.js"
Cohesion: 0.17
Nodes (15): sharp, tesseract.js, { createWorker }, isRowValid(), main(), ocrTableRows(), parseRow(), sharp (+7 more)

### Community 79 - "renderSelfCheckPanel"
Cohesion: 0.22
Nodes (16): bodyPartByKey(), bodyPartLabel(), organFunctionFor(), pkgBoxStyle(), pkgChip(), pkgIconCircle(), renderDiseaseBriefPanel(), renderDrugNewsPanel() (+8 more)

### Community 80 - "fetchWeather"
Cohesion: 0.12
Nodes (17): anomLoadEnsemble(), anomRun(), fetchChickenPrices(), fetchStockPrices(), fetchUpbitData(), fetchWeather(), fetchYahooQuote(), loadQuoteCache() (+9 more)

### Community 81 - "renderHpaiKrCard"
Cohesion: 0.31
Nodes (13): hkCount(), hkFarms(), hkFmt(), hkInPeriod(), hkMonth(), hkNumLabel(), hkProvFill(), hkSeq() (+5 more)

### Community 82 - "tradeItem"
Cohesion: 0.22
Nodes (13): pfTon(), tradeBadge(), tradeItem(), tradeKpi(), tradeMoney(), tradeOverview(), tradePartnerBar(), tradePartners() (+5 more)

### Community 83 - "fetch_hpai_risk.py"
Cohesion: 0.22
Nodes (8): build(), day(), fetch_events(), get_json(), is_hpai(), is_wild(), keep_previous(), main()

### Community 84 - "fetch_layer_stats.py"
Cohesion: 0.25
Nodes (11): base_params(), build(), slot(), species(), fetch_periods(), fetch_table(), keep_previous(), label_period() (+3 more)

### Community 85 - "fetch_usda_crop_progress.py"
Cohesion: 0.23
Nodes (9): fetch_text(), history_point(), list_releases(), main(), _num(), parse_report(), split_sections(), table_rows() (+1 more)

### Community 86 - "vcFigPress"
Cohesion: 0.38
Nodes (11): vcChick(), vcFan(), vcFig(), vcFigHouse(), vcFigInlet(), vcFigModes(), vcFigPress(), vcFigWhy() (+3 more)

### Community 87 - "pfBind"
Cohesion: 0.19
Nodes (14): pfApplyLocal(), pfBind(), pfDownload(), pfIngest(), pfLog(), pfMergeRows(), pfMonthly(), pfNormDate() (+6 more)

### Community 88 - "drugUseBind"
Cohesion: 0.14
Nodes (17): drugUseAllKinds(), drugUseBind(), drugUseCard(), drugUseForm(), drugUseItems(), drugUseKindBadge(), drugUseKindColor(), drugUseNewDraft() (+9 more)

### Community 89 - "phFig"
Cohesion: 0.40
Nodes (10): phArrow(), phFig(), phFigCirc(), phFigDigest(), phFigExcrete(), phFigHormone(), phFigNeuro(), phFigRepro() (+2 more)

### Community 90 - "vcNeed"
Cohesion: 0.20
Nodes (14): vcFmt(), vcInletOut(), vcInterp(), vcKg(), vcNeed(), vcPerOut(), vcR100(), vcRange() (+6 more)

### Community 91 - "fetch_poultry_diseases.py"
Cohesion: 0.15
Nodes (7): get(), load_previous(), main(), parse_detail(), parse_index(), save(), translate()

### Community 92 - "renderDrugSearchPanel"
Cohesion: 0.25
Nodes (9): drugEfficacySnippet(), drugFormCategory(), drugModePlaceholder(), drugStandardPacks(), drugWithdrawalForPoultry(), renderDrugKindSelect(), renderDrugSearchPanel(), renderDrugSuggestions() (+1 more)

### Community 93 - "renderColiEasy"
Cohesion: 0.39
Nodes (8): easyBtn(), easyCard(), easyHero(), easyList(), easyStep(), easyTwo(), renderColiEasy(), renderHzEasy()

### Community 94 - "renderGrainPriceCard"
Cohesion: 0.48
Nodes (7): gpCol(), gpDir(), gpPct(), gpRange(), gpSpark(), renderGrainPriceCard(), renderGrainPricePanel()

### Community 95 - "sgDraftToGuide"
Cohesion: 0.50
Nodes (4): sgDraftToGuide(), sgParseHusb(), sgParseIssues(), sgParseRows()

### Community 96 - "anomLoadClimatology"
Cohesion: 0.47
Nodes (6): anomCompute(), anomDoy(), anomLoadClimatology(), anomMean(), anomPct(), anomSd()

### Community 97 - "renderSmsAdminPanel"
Cohesion: 0.29
Nodes (8): fetchAllSmsSubscriptions(), fetchResearchPapers(), renderSmsAdminPanel(), renderSmsSubPanel(), smsIntervalLabel(), smsIsDue(), smsMenuLabel(), smsNextDueDate()

### Community 98 - "renderPremiumTab"
Cohesion: 0.06
Nodes (41): commonsImageCredit(), currentPremiumMenuItems(), emergTrendBadge(), featureBoardAuthorLabel(), featureBoardReplyLabel(), isAdmin(), isBoardAdmin(), loadWeatherLocation() (+33 more)

### Community 99 - "gmT"
Cohesion: 0.17
Nodes (48): dsFigFlow(), dsFigFume(), gmArrow(), gmBox(), gmE(), gmFigAst(), gmFigBoost(), gmFigCastle() (+40 more)

### Community 100 - "pfBuildModel"
Cohesion: 0.50
Nodes (4): pfBuildModel(), pfClip(), pfProbs(), pfYoY()

### Community 101 - "sys"
Cohesion: 0.13
Nodes (12): day_key(), fetch_one(), main(), call_api(), diff(), get_api_key(), ival(), main() (+4 more)

### Community 102 - "authDialog"
Cohesion: 0.67
Nodes (3): authDialog(), premiumResetPassword(), premiumSignInEmail()

### Community 103 - "hzToday"
Cohesion: 0.20
Nodes (14): hzBtSummary(), hzBtSummaryLine(), hzLift(), hzNearLevel1(), hzReportHtml(), hzReportPrintDoc(), hzReportText(), hzToday() (+6 more)

### Community 104 - "attachDzCustomEvents"
Cohesion: 0.29
Nodes (7): attachDzCustomEvents(), dzFormRead(), dzParseAiDraft(), generateAiDraft(), publicContentPath(), saveDiseaseCustom(), writePublicContentJson()

### Community 105 - "farmGameCall"
Cohesion: 0.39
Nodes (8): farmGameCall(), farmGameErrMsg(), farmGameNickKey(), farmGameUser(), list(), load(), remove(), save()

### Community 107 - "emergLoad"
Cohesion: 0.40
Nodes (6): emergAnalyze(), emergEsearch(), emergEsummary(), emergFmtDate(), emergLoad(), emergSearchPapers()

### Community 108 - "renderDisinfectPanel"
Cohesion: 0.23
Nodes (16): currentDiseaseDisinfectants(), disinfectProductsToText(), dsBanner(), dsBasic(), dsBug(), dsDisease(), dsFigThree(), dsGeneral() (+8 more)

### Community 109 - "CLAUDE.md"
Cohesion: 0.40
Nodes (3): Commands, graphify (토큰 절약용 코드 지식 그래프), Workflow preference (owner's standing instruction)

### Community 110 - "switchTab"
Cohesion: 0.20
Nodes (12): buildDiseaseSearch(), dzCustomToEntry(), dzMergeCustom(), emergSendToNews(), fetchDiseases(), fetchNews(), hzBind(), hzLocate() (+4 more)

### Community 113 - "sgOpenEdit"
Cohesion: 0.50
Nodes (4): sgHusbToText(), sgIssuesToText(), sgOpenEdit(), sgRowsToText()

### Community 114 - "metConvert"
Cohesion: 0.50
Nodes (4): metConvert(), metEntryPrecip(), metEntrySymbol(), metSymbolToWmo()

### Community 115 - "gmHome"
Cohesion: 0.15
Nodes (16): dsBind(), dsFigBirds(), GM_DIRT(), gmBind(), gmDilBox(), gmDilOut(), gmFigFarm(), gmFinal() (+8 more)

### Community 116 - "renderWeatherTab"
Cohesion: 0.15
Nodes (14): renderAnomalyPanel(), renderHeaderSolarTerm(), renderSolarTermPanel(), renderWeatherNewsCard(), renderWeatherSobakCard(), renderWeatherTab(), solarTermInfo(), stBisect() (+6 more)

### Community 117 - "fetch_taxfree_fuel.py"
Cohesion: 0.25
Nodes (6): fetch_html(), main(), parse(), day(), parse_day(), year_ago()

### Community 118 - "kkokoTouchCharacter"
Cohesion: 0.67
Nodes (3): kkokoReactions(), kkokoSpin3d(), kkokoTouchCharacter()

### Community 119 - "renderVaccinePanel"
Cohesion: 0.18
Nodes (16): currentVaccinePrograms(), pkgCardHtml(), pkgColor(), pkgColorOf(), pkgColorPickerHtml(), pkgValidColor(), renderVaccineGuide(), renderVaccinePanel() (+8 more)

### Community 120 - "pfSign"
Cohesion: 0.25
Nodes (9): pfEvidence(), pfImportHtml(), pfImportItem(), pfImportStatsHtml(), pfRuleBody(), pfRuleSpeciesCard(), pfSafeUrl(), pfSign() (+1 more)

### Community 121 - "dilResultHtml"
Cohesion: 0.50
Nodes (5): dilBind(), dilCalc(), dilFmt(), dilResultHtml(), renderDilutionCard()

### Community 122 - "hzBox"
Cohesion: 0.20
Nodes (14): hzBacktestBox(), hzBacktestBox2(), hzBox(), hzBt2Table(), hzClass(), hzDaysAgo(), hzDensEnsure(), hzDensityBox() (+6 more)

### Community 125 - "renderHzTasks"
Cohesion: 0.83
Nodes (4): hzStageProgress(), hzTaskId(), renderHzTaskCard(), renderHzTasks()

## Knowledge Gaps
- **1 isolated node(s):** `RFC-822`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1146 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Architecture: the fetch-script → JSON → dashboard pipeline` connect `Architecture: the fetch-script → JSON → dashboard pipeline` to `ibTag`, `attachEvents`, `index.js`, `requests`, `render`, `json`, `esc`, `attachDiseaseEvents`, `renderConsultTab`, `re`, `coliFigFor`, `isPremiumApproved`, `fetchQiaSearch`, `renderFeedGrainFlow`, `send_sms_subscriptions.py`, `renderFeedPotentialPanel`, `fetch_broiler_breeder.py`, `pfForecast`, `fetch_poultry_disease_brief.py`, `renderHpaiSymptomCard`, `pfTabSpecies`, `gmVirus`, `fetchWeather`, `renderHpaiKrCard`, `drugUseBind`, `vcNeed`, `renderPremiumTab`, `gmT`, `pfBuildModel`, `renderDisinfectPanel`, `CLAUDE.md`, `metConvert`, `gmHome`, `renderVaccinePanel`, `dilResultHtml`?**
  _High betweenness centrality (0.161) - this node is a cross-community bridge._
- **Are the 125 inferred relationships involving `Architecture: the fetch-script → JSON → dashboard pipeline` (e.g. with `analyzeNecropsyPhotos()` and `fetchRssItems()`) actually correct?**
  _`Architecture: the fetch-script → JSON → dashboard pipeline` has 125 INFERRED edges - model-reasoned connections that need verification._
- **What connects `RFC-822` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `index.inline.js` be split into smaller, more focused modules?**
  _Cohesion score 0.004705574799032743 - nodes in this community are weakly interconnected._
- **Why does `decode_google_url()` connect `requests` to `json`, `Architecture: the fetch-script → JSON → dashboard pipeline`, `fetch_poultry_disease_brief.py`, `re`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Should `attachEvents` be split into smaller, more focused modules?**
  _Cohesion score 0.031542368350708366 - nodes in this community are weakly interconnected._
- **Why does `ai_extract()` connect `re` to `json`, `Architecture: the fetch-script → JSON → dashboard pipeline`, `requests`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._