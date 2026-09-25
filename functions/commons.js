// Wikimedia Commons(위키미디어 공용 — 자유 이용 사진 저장소) 검색.
// 학습 카드 뒷면의 대표 증상 사진 후보를 찾는 데 쓴다(findCardImage in index.js).
// 저작권 때문에 CC0·퍼블릭 도메인·CC BY·CC BY-SA 사진만 후보로 남기고, 화면에는
// 작성자·라이선스·출처를 함께 표시한다(CC BY 계열의 저작자 표시 조건).

const COMMONS_API = "https://commons.wikimedia.org/w/api.php";
// Wikimedia는 연락처(사이트 주소)가 담긴 User-Agent를 요구한다 — 없으면 차단될 수 있다.
const COMMONS_UA = "polcon-pb/1.0 (https://polcon.cc)";
const FREE_LICENSE = /^(cc0|cc[ -]by|public domain|pd\b)/i;
// Claude가 읽을 수 있는 형식만(gif는 움짤이 섞여 제외).
const IMAGE_MIME = ["image/jpeg", "image/png", "image/webp"];
// Commons 표준 섬네일 폭 — 화면 표시 960px, 후보 목록 330px, AI 판독 500px.
const FULL_WIDTH = 960;

function stripHtml(s) {
  return String(s || "")
    .replace(/<[^>]*>/g, " ")
    .replace(/&nbsp;/g, " ").replace(/&amp;/g, "&").replace(/&quot;/g, "\"")
    .replace(/&#0?39;/g, "'").replace(/&lt;/g, "<").replace(/&gt;/g, ">")
    .replace(/\s+/g, " ").trim();
}

// 960px 섬네일 주소를 다른 표준 폭으로 바꾼다. 원본이 960px보다 작아 섬네일이
// 아닌 원본 주소가 온 경우엔 그대로 둔다.
function thumbAt(fullUrl, width) {
  return fullUrl.replace(`/${FULL_WIDTH}px-`, `/${width}px-`);
}

async function searchCommons(query, limit) {
  const params = new URLSearchParams({
    action: "query", format: "json",
    generator: "search", gsrsearch: `${query} filetype:bitmap`, gsrnamespace: "6", gsrlimit: String(limit),
    prop: "imageinfo", iiprop: "url|mime|extmetadata",
    iiextmetadatafilter: "LicenseShortName|LicenseUrl|Artist", iiurlwidth: String(FULL_WIDTH),
  });
  const res = await fetch(`${COMMONS_API}?${params}`, {
    headers: { "User-Agent": COMMONS_UA }, signal: AbortSignal.timeout(15000),
  });
  if (!res.ok) throw new Error(`Commons 검색 실패(${res.status})`);
  const j = await res.json();
  const pages = Object.values((j.query && j.query.pages) || {}).sort((a, b) => (a.index || 0) - (b.index || 0));
  const out = [];
  for (const p of pages) {
    const ii = (p.imageinfo || [])[0];
    if (!ii || !IMAGE_MIME.includes(ii.mime)) continue;
    const m = ii.extmetadata || {};
    const license = stripHtml(m.LicenseShortName && m.LicenseShortName.value);
    if (!FREE_LICENSE.test(license)) continue;
    // 주소 끝의 추적용 꼬리표(?utm_source=...)는 떼고 저장한다.
    const full = String(ii.thumburl || ii.url || "").split("?")[0];
    if (!full) continue;
    out.push({
      title: String(p.title || "").replace(/^File:/, ""),
      page: String(ii.descriptionurl || "").split("?")[0],
      full,
      thumb: thumbAt(full, 330),
      license,
      licenseUrl: (m.LicenseUrl && m.LicenseUrl.value) || "",
      artist: stripHtml(m.Artist && m.Artist.value).slice(0, 80),
    });
  }
  return out;
}

// 검색어 여러 개로 찾은 결과를 순위별로 번갈아 담는다 — 첫 검색어가 후보를
// 독차지하지 않게. 한 검색어가 실패해도 나머지 결과는 쓴다.
async function findCommonsCandidates(queries, max = 8) {
  const lists = await Promise.all(queries.map((q) => searchCommons(q, 10).catch(() => [])));
  const seen = new Set();
  const out = [];
  for (let rank = 0; out.length < max && lists.some((l) => rank < l.length); rank++) {
    for (const l of lists) {
      const c = l[rank];
      if (c && !seen.has(c.title) && out.length < max) { seen.add(c.title); out.push(c); }
    }
  }
  return out;
}

// AI 판독용 — 500px 섬네일을 base64로 받는다.
async function fetchCandidateImage(candidate) {
  const res = await fetch(thumbAt(candidate.full, 500), {
    headers: { "User-Agent": COMMONS_UA }, signal: AbortSignal.timeout(15000),
  });
  if (!res.ok) throw new Error(`이미지 받기 실패(${res.status})`);
  const type = (res.headers.get("content-type") || "").split(";")[0].trim();
  if (!IMAGE_MIME.includes(type)) throw new Error(`지원하지 않는 이미지 형식(${type})`);
  const buf = Buffer.from(await res.arrayBuffer());
  if (buf.length > 4 * 1024 * 1024) throw new Error("이미지가 너무 큽니다");
  return { media_type: type, data: buf.toString("base64") };
}

module.exports = { findCommonsCandidates, fetchCandidateImage };
