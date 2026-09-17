#!/usr/bin/env node
// 산란계 중추가격 이미지에서 표(연도별·월별 가격) 영역만 OCR로 읽어 구조화한다.
// fetch_jungchu_price.py가 이미지를 내려받은 뒤 이 스크립트를 서브프로세스로
// 호출해 표준출력의 JSON 한 줄을 받아 쓴다.
//
// 왜 Node/tesseract.js인가: 이 저장소의 다른 수집 스크립트는 전부 Python이지만,
// OCR은 시스템에 tesseract 바이너리가 있어야 하는 pytesseract 대신, 바이너리
// 설치 없이 npm만으로 도는 tesseract.js(같은 Tesseract 엔진의 WASM 빌드)로
// 먼저 정확도를 실측 검증한 뒤 그 결과를 그대로 채택했다. 표 영역만 잘라
// OCR했을 때 6개 연도 × 최대 12개월 값과 "평균" 칸까지 전부 정확히 읽혔다.
//
// 신뢰성 확보 방법: association이 표에 같이 인쇄해 둔 "평균" 값을 체크섬으로
// 쓴다 — OCR로 읽은 월별 숫자들의 평균을 직접 계산해 OCR로 읽은 "평균" 칸과
// 대조하고, 어긋나는 행이 하나라도 있으면 전체 결과를 버린다. 시세 데이터에서
// 오독한 숫자를 보여주는 것이 아예 안 보여주는 것보다 나쁘다고 보기 때문이다.

const { createWorker } = require("tesseract.js");
const sharp = require("sharp");

const YEAR_LINE = /^\s*(20\d{2})\b(.*)$/;
// 콤마가 점(.)이나 콜론(:)으로 오독되는 경우까지 같은 토큰으로 흡수한다.
const NUM_TOKEN = /\d{1,3}(?:[.,:]\d{3})+|\d{4,6}/g;
const MIN_VALID_ROWS = 3; // 표는 항상 6행이지만, 여유를 두고 최소 기준만 둔다.
const VALUE_RANGE = [1000, 20000]; // 원 — 과거 실측치(4,038~7,400)에 여유를 둔 범위
const AVG_TOLERANCE = 5; // 평균 체크섬 허용 오차(원)

function parseRow(line) {
  const m = line.match(YEAR_LINE);
  if (!m) return null;
  const year = parseInt(m[1], 10);
  const nums = (m[2].match(NUM_TOKEN) || []).map(s => parseInt(s.replace(/[.,:]/g, ""), 10));
  if (nums.length < 2) return null; // 최소 1개월 값 + 평균
  return { year, months: nums.slice(0, -1), average: nums[nums.length - 1] };
}

function isRowValid(row) {
  if (row.year < 2015 || row.year > 2035) return false;
  if (row.months.length < 1 || row.months.length > 12) return false;
  const [lo, hi] = VALUE_RANGE;
  for (const v of [...row.months, row.average]) if (v < lo || v > hi) return false;
  const mean = Math.floor(row.months.reduce((a, b) => a + b, 0) / row.months.length);
  return Math.abs(mean - row.average) <= AVG_TOLERANCE;
}

async function ocrTableRows(imagePath) {
  const meta = await sharp(imagePath).metadata();
  // 표는 항상 이미지 하단부에 있다(위쪽은 그래프). 넉넉하게 하단 30%를 잘라
  // OCR 정확도를 높인다 — 위쪽 그래프 범례가 섞여 들어와도 아래 파싱 단계의
  // "연도로 시작 + 콤마숫자 2개 이상" 조건이 걸러낸다.
  const top = Math.floor(meta.height * 0.70);
  const cropped = await sharp(imagePath)
    .extract({ left: 0, top, width: meta.width, height: meta.height - top })
    .toBuffer();

  const worker = await createWorker("eng");
  let text;
  try {
    ({ data: { text } } = await worker.recognize(cropped));
  } finally {
    await worker.terminate();
  }

  const rows = [];
  for (const line of text.split("\n")) {
    const row = parseRow(line);
    if (row && isRowValid(row)) rows.push(row);
  }
  return rows;
}

async function main() {
  const imagePath = process.argv[2];
  if (!imagePath) {
    console.log(JSON.stringify({ ok: false, reason: "usage: ocr_jungchu_table.js <image>" }));
    process.exit(0);
  }

  let rows;
  try {
    rows = await ocrTableRows(imagePath);
  } catch (e) {
    console.log(JSON.stringify({ ok: false, reason: String(e) }));
    return;
  }

  if (rows.length < MIN_VALID_ROWS) {
    console.log(JSON.stringify({ ok: false, reason: `검증 통과한 행이 ${rows.length}개뿐 (최소 ${MIN_VALID_ROWS}개 필요)` }));
    return;
  }

  rows.sort((a, b) => b.year - a.year);
  const latestRow = rows[0];
  // months 배열은 1월부터 빈칸 없이 채워지므로(association이 매달 그 시점까지의
  // 누적 표를 갱신), 길이가 곧 "몇 월까지 나왔는지"와 같다.
  console.log(JSON.stringify({
    ok: true,
    rows,
    latest: latestRow.months[latestRow.months.length - 1],
    latest_year: latestRow.year,
    latest_month: latestRow.months.length,
  }));
}

main();
