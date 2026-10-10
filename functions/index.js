// 회원관리 화면(index.html)에서 부르는 관리자 전용 Cloud Functions.
//
// 왜 필요한가: 브라우저의 Firebase 클라이언트 SDK는 "지금 로그인한 계정
// 본인"만 삭제할 수 있고, 남의 계정(다른 회원)을 삭제할 권한이 없다.
// 그 권한(Admin SDK)은 서버에서만 쓸 수 있어, 이 두 함수를 그 서버 역할로
// 둔다.
//
// 인증: 별도 비밀키 대신 "호출한 사람이 Firebase에 로그인한 계정의
// 이메일"을 그대로 쓴다 — onCall 함수는 Firebase가 검증한 ID 토큰을
// request.auth로 넘겨주므로 위조할 수 없다. 그 이메일이 ADMIN_EMAILS에
// 있을 때만 실행을 허용한다. 관리자를 늘리려면 이 배열에 이메일만 추가하면
// 된다(재배포 필요).

const { onCall, HttpsError } = require("firebase-functions/v2/https");
const { defineSecret } = require("firebase-functions/params");
const admin = require("firebase-admin");
const Anthropic = require("@anthropic-ai/sdk");
const { findCommonsCandidates, fetchCandidateImage } = require("./commons");

// Claude API 키는 Firebase 비밀값으로만 둔다(브라우저에 절대 노출되지 않게).
// 등록: firebase functions:secrets:set ANTHROPIC_API_KEY
const ANTHROPIC_API_KEY = defineSecret("ANTHROPIC_API_KEY");

admin.initializeApp();

const ADMIN_EMAILS = ["trsumun@gmail.com", "trsumun@daum.net"];
const STORAGE_BUCKET = "chicken-dx.firebasestorage.app";

function assertAdmin(request) {
  const email = request.auth && request.auth.token && request.auth.token.email;
  if (!email || !ADMIN_EMAILS.includes(String(email).toLowerCase())) {
    throw new HttpsError("permission-denied", "관리자만 사용할 수 있습니다.");
  }
}

function isApprovedOrAdmin(request) {
  const token = request.auth && request.auth.token;
  if (!token) return false;
  if (token.approved === true) return true;
  const email = token.email;
  return !!(email && ADMIN_EMAILS.includes(String(email).toLowerCase()));
}

// 기존 계정이 있으면 지우고, 새 비밀번호로 다시 만든다. "🔑 비밀번호 재설정"
// 버튼이 부른다 — Firebase 콘솔에서 미리 지울 필요가 없어진다.
exports.resetMemberAccount = onCall(async (request) => {
  assertAdmin(request);
  const { email, password } = request.data || {};
  if (!email || typeof email !== "string") {
    throw new HttpsError("invalid-argument", "이메일이 필요합니다.");
  }
  if (!password || String(password).length < 6) {
    throw new HttpsError("invalid-argument", "비밀번호는 6자 이상이어야 합니다.");
  }
  try {
    const existing = await admin.auth().getUserByEmail(email).catch(() => null);
    if (existing) await admin.auth().deleteUser(existing.uid);
    await admin.auth().createUser({ email, password });
    return { ok: true, recreated: !!existing };
  } catch (e) {
    throw new HttpsError("internal", e.message || String(e));
  }
});

// 회원 명부에서 회원을 삭제할 때 Firebase 계정도 함께 지운다 — 안 그러면
// 명부에는 없는데 로그인은 계속 되는(그냥 승인만 안 된) 계정이 남는다.
// 계정이 애초에 없어도(이미 지워졌거나 한 번도 안 만들었어도) 에러로 보지
// 않는다 — 회원 삭제 자체는 계속 진행돼야 하므로.
exports.deleteMemberAccount = onCall(async (request) => {
  assertAdmin(request);
  const { email } = request.data || {};
  if (!email || typeof email !== "string") {
    throw new HttpsError("invalid-argument", "이메일이 필요합니다.");
  }
  try {
    const existing = await admin.auth().getUserByEmail(email).catch(() => null);
    if (existing) await admin.auth().deleteUser(existing.uid);
    return { ok: true, deleted: !!existing };
  } catch (e) {
    throw new HttpsError("internal", e.message || String(e));
  }
});

// 유료 콘텐츠(상황별 처방·계절별 패키지·농장 맞춤 찾기·자가진단)는 공개
// GitHub 저장소 대신 Firebase Storage에 두고, storage.rules에서
// "request.auth.token.approved == true"인 사람만 읽을 수 있게 막는다.
// 그런데 승인 여부는 승인 명부(member_registry/approved.json)에 있지, Firebase
// 계정 자체에는 없다 — 그래서 회원을 추가/수정할 때마다 이 함수로 그 계정의
// ID 토큰에 approved 커스텀 클레임을 심어준다(index.html의 mm-save
// 핸들러가 호출). 클레임은 다음 로그인/토큰 갱신 때 반영된다(즉시 반영이
// 필요하면 클라이언트에서 getIdToken(true)로 강제 갱신).
exports.setMemberApproval = onCall(async (request) => {
  assertAdmin(request);
  const { email, approved } = request.data || {};
  if (!email || typeof email !== "string") {
    throw new HttpsError("invalid-argument", "이메일이 필요합니다.");
  }
  try {
    const user = await admin.auth().getUserByEmail(email).catch(() => null);
    if (!user) return { ok: true, skipped: true };
    await admin.auth().setCustomUserClaims(user.uid, { approved: !!approved });
    return { ok: true };
  } catch (e) {
    throw new HttpsError("internal", e.message || String(e));
  }
});

// 브라우저에서 firebase.storage()의 getDownloadURL()+fetch()로 비공개 파일을
// 직접 읽으면, 인증(Authorization 헤더)까지는 성공해도 Firebase가 실제 파일
// 내용을 storage.googleapis.com의 서명된 URL로 리다이렉트하는데 그 응답에는
// CORS 허용 헤더가 없어 브라우저가 항상 막아버린다 — 권한 문제가 아니라
// 브라우저 CORS 정책 자체의 한계라 클라이언트 코드로는 우회할 수 없다.
// 그래서 승인회원 전용 JSON은 서버(Admin SDK, CORS·rules 둘 다 적용 안 받음)
// 에서 대신 읽어 내용을 응답으로 그대로 돌려준다.

// 유료회원 기능요청 게시판 전체(글+답글)를 읽어 돌려준다.
exports.getFeatureRequests = onCall(async (request) => {
  if (!isApprovedOrAdmin(request)) {
    throw new HttpsError("permission-denied", "승인된 회원만 볼 수 있습니다.");
  }
  const bucket = admin.storage().bucket(STORAGE_BUCKET);
  const [files] = await bucket.getFiles({ prefix: "feature_requests/" });
  const posts = {};
  for (const file of files) {
    const parts = file.name.split("/");
    if (parts.length === 4 && parts[3] === "post.json") {
      const uid = parts[1], postId = parts[2];
      try {
        const [buf] = await file.download();
        const post = JSON.parse(buf.toString("utf-8"));
        posts[uid + "/" + postId] = Object.assign({}, post, { uid, postId, replies: [] });
      } catch (e) { /* 손상된 글은 건너뛴다 */ }
    }
  }
  for (const file of files) {
    const parts = file.name.split("/");
    if (parts.length === 5 && parts[3] === "replies") {
      const key = parts[1] + "/" + parts[2];
      if (!posts[key]) continue;
      try {
        const [buf] = await file.download();
        posts[key].replies.push(JSON.parse(buf.toString("utf-8")));
      } catch (e) { /* 손상된 답글은 건너뛴다 */ }
    }
  }
  const list = Object.values(posts);
  list.forEach((p) => p.replies.sort((a, b) => (a.at || "").localeCompare(b.at || "")));
  list.sort((a, b) => (b.createdAt || "").localeCompare(a.createdAt || ""));
  return { posts: list };
});

// premium_content/{dataset}/latest.json(상황별 처방·계절별 패키지·농장 맞춤
// 찾기·자가진단·질병별 소독제·온라인 학습 카드 등)도 같은 이유로 대신 읽어준다.
exports.getPremiumContent = onCall(async (request) => {
  if (!isApprovedOrAdmin(request)) {
    throw new HttpsError("permission-denied", "승인된 회원만 볼 수 있습니다.");
  }
  const { dataset } = request.data || {};
  if (!dataset || typeof dataset !== "string" || !/^[a-zA-Z0-9_]+$/.test(dataset)) {
    throw new HttpsError("invalid-argument", "dataset이 필요합니다.");
  }
  const bucket = admin.storage().bucket(STORAGE_BUCKET);
  const file = bucket.file("premium_content/" + dataset + "/latest.json");
  const [exists] = await file.exists();
  if (!exists) throw new HttpsError("not-found", "아직 발행된 내용이 없습니다.");
  try {
    const [buf] = await file.download();
    return { data: JSON.parse(buf.toString("utf-8")) };
  } catch (e) {
    throw new HttpsError("internal", "저장된 내용을 읽지 못했습니다.");
  }
});

// public_content/{dataset}/latest.json(AI 관련 소식·이달의 질병·유료서비스 메뉴
// 편집본)도 같은 CORS 이유로 대신 읽어준다. 무료 탭·로그인 전 화면에 보이는
// 공개 내용이라 로그인을 요구하지 않는다(쓰기는 storage.rules에서 관리자만).
exports.getPublicContent = onCall(async (request) => {
  const { dataset } = request.data || {};
  if (!dataset || typeof dataset !== "string" || !/^[a-zA-Z0-9_]+$/.test(dataset)) {
    throw new HttpsError("invalid-argument", "dataset이 필요합니다.");
  }
  const file = admin.storage().bucket(STORAGE_BUCKET).file("public_content/" + dataset + "/latest.json");
  const [exists] = await file.exists();
  if (!exists) throw new HttpsError("not-found", "아직 발행된 내용이 없습니다.");
  try {
    const [buf] = await file.download();
    return { data: JSON.parse(buf.toString("utf-8")) };
  } catch (e) {
    throw new HttpsError("internal", "저장된 내용을 읽지 못했습니다.");
  }
});

// 유료서비스 승인 명부(member_registry/approved.json — 이메일·만료일만).
// 예전엔 공개 GitHub 저장소(premium/approved.json)라 누구나 명단 전체를 볼 수
// 있었다. 이제 관리자에게만 전체를 주고, 일반 로그인 사용자에게는 본인 항목만
// 준다 — 브라우저(isPremiumApproved)가 알아야 하는 건 "나는 승인됐나"뿐이다.
exports.getApprovedMembers = onCall(async (request) => {
  const email = request.auth && request.auth.token && request.auth.token.email;
  if (!email) throw new HttpsError("unauthenticated", "로그인이 필요합니다.");
  const file = admin.storage().bucket(STORAGE_BUCKET).file("member_registry/approved.json");
  const [exists] = await file.exists();
  if (!exists) throw new HttpsError("not-found", "아직 발행된 명부가 없습니다.");
  let members;
  try {
    const [buf] = await file.download();
    members = JSON.parse(buf.toString("utf-8")).members || [];
  } catch (e) {
    throw new HttpsError("internal", "명부를 읽지 못했습니다.");
  }
  const me = String(email).toLowerCase().trim();
  if (ADMIN_EMAILS.includes(me)) return { members };
  return { members: members.filter((m) => String(m.email || "").toLowerCase().trim() === me) };
});

async function readJsonFile(file) {
  try {
    const [buf] = await file.download();
    return JSON.parse(buf.toString("utf-8"));
  } catch (e) {
    return null; // 깨진 파일 하나 때문에 목록 전체가 실패하지 않게 건너뛴다
  }
}

// 회원관리 화면의 이름·전화번호·가입일(premium_members/{email}/info.json) —
// 관리자 전용. 쓰기는 브라우저가 직접 하지만, 읽기는 위와 같은 CORS 이유로
// 브라우저에서 막히므로 대신 읽어준다. { profiles: { email: {name,phone,joined} } }
exports.getMemberProfiles = onCall(async (request) => {
  assertAdmin(request);
  const bucket = admin.storage().bucket(STORAGE_BUCKET);
  const [files] = await bucket.getFiles({ prefix: "premium_members/" });
  const profiles = {};
  await Promise.all(files.filter((f) => f.name.endsWith("/info.json")).map(async (f) => {
    const email = f.name.slice("premium_members/".length, -"/info.json".length);
    const profile = await readJsonFile(f);
    if (profile) profiles[email] = profile;
  }));
  return { profiles };
});

// 자동 문자 발송 신청 설정(premium_board/sms_sub/{uid}/settings/config.json).
// 기본은 호출한 회원 본인 설정만({ mine }), 관리자가 all:true로 부르면 전체
// 신청자 목록({ list })을 준다 — 발송관리 화면용.
exports.getSmsSubscriptions = onCall(async (request) => {
  const uid = request.auth && request.auth.uid;
  if (!uid) throw new HttpsError("unauthenticated", "로그인이 필요합니다.");
  const bucket = admin.storage().bucket(STORAGE_BUCKET);
  if (request.data && request.data.all) {
    assertAdmin(request);
    const [files] = await bucket.getFiles({ prefix: "premium_board/sms_sub/" });
    const list = [];
    await Promise.all(files.filter((f) => f.name.endsWith("/settings/config.json")).map(async (f) => {
      const cfg = await readJsonFile(f);
      if (cfg) list.push(Object.assign({ uid: f.name.split("/")[2] }, cfg));
    }));
    return { list };
  }
  const file = bucket.file("premium_board/sms_sub/" + uid + "/settings/config.json");
  const [exists] = await file.exists();
  return { mine: exists ? await readJsonFile(file) : null };
});

// 관리 화면의 AI 초안 두 가지 — "농장에서 많이 궁금해 하는 질문"(faq) 답변과
// "최수의사의 온라인 학습"(card) 카드 뒷면. 초안은 수의사가 검토·수정한 뒤에만
// 발행되므로(index.html은 폼에 채워 넣기만 하고 발행하지 않는다) 여기서는 문체와
// 안전선(처방·신고대상 질병)만 잡아 준다.
const FAQ_SYSTEM_PROMPT = `당신은 현장 양계 전문 수의사가 운영하는 농장동물 컨설팅 서비스(유료회원 대상)의 "농장에서 많이 궁금해 하는 질문" 답변 초안을 씁니다. 초안은 수의사가 검토·수정한 뒤 게시되고, 읽는 사람은 육계·산란계·토종닭 농장주입니다.

답변 방식
- 한국어 존댓말로, 농장에서 바로 확인하고 실행할 수 있는 내용을 3~5문장 정도로 씁니다. 원인이 여러 가지면 먼저 확인할 순서대로 짚어 줍니다.
- 화면에 그대로 표시되는 평문이라 마크다운(제목, 굵게, 목록 기호)은 쓰지 않습니다. 순서를 나열할 때는 ①②③ 정도만 씁니다.
- 질문을 다시 옮겨 적거나 인사말을 붙이지 말고 답변 본문만 씁니다.

지켜야 할 것
- 항생제 등 동물용의약품은 계열·성분군 수준까지만 언급하고 제품명·용량을 정해 주지 않습니다. 약이 필요한 상황이면 담당 수의사의 진단·처방을 받도록 안내합니다(국내 수의사처방제 대상).
- 고병원성 AI·뉴캣슬병 등 가축전염병예방법상 신고대상 질병이 의심되는 상황이면 즉시 가축방역기관에 신고하도록 안내합니다.
- 확실하지 않은 수치는 지어내지 말고, 품종·일령·계사 환경에 따라 달라진다고 밝힙니다.
- 농장동물 사양·질병·방역과 관계없는 질문이면 이 서비스에서 다루는 범위가 아니라고 한 문장으로만 답합니다.

답변 예시(문체 참고)
질문: 산란율이 며칠 사이 급격히 떨어졌어요. 어떤 원인을 의심해야 하나요?
답변: 전염성기관지염(IB)·산란저하증후군(EDS) 등 바이러스성 질병, 스트레스(온도 급변·소음·백신 접종), 사료 배합 변경, 조명시간 변화 등을 순서대로 점검하세요. 동시에 폐사·호흡기 증상이 함께 있는지도 확인이 필요합니다.`;

const CARD_SYSTEM_PROMPT = `당신은 현장 양계 전문 수의사가 만든 온라인 학습용 플래시카드의 뒷면을 씁니다. 앞면에는 질문이나 용어가 있고, 뒷면에는 그 답이나 설명이 들어갑니다. 읽는 사람은 양계 농장주와 농장 관리자입니다.

- 한국어로 간단명료하게, 1~3문장이나 짧은 핵심어 나열로 씁니다. 카드 한 장을 보고 바로 기억할 수 있을 만큼 짧아야 합니다.
- 화면에 그대로 표시되는 평문이라 마크다운은 쓰지 않습니다. 앞면을 다시 옮겨 적지 말고 답만 씁니다.
- 약품은 계열·성분군 수준까지만 쓰고 제품명·용량은 쓰지 않습니다.
- 확실하지 않은 수치는 지어내지 않습니다.
- 덱 주제가 주어지면 그 맥락에 맞춰 답합니다.

예시
앞면: 뉴캣슬병의 대표 증상은?
뒷면: 호흡기 증상(기침·헐떡임), 신경 증상(목 비틀림·마비), 산란율 급감, 녹색 설사`;

const DECK_SYSTEM_PROMPT = `당신은 현장 양계 전문 수의사가 만든 온라인 학습용 플래시카드 덱(카드 묶음)의 설명을 씁니다. 덱 목록 화면에서 제목 아래에 보이는 짧은 소개글이고, 읽는 사람은 양계 농장주와 농장 관리자입니다.

- 한국어 존댓말로 1~2문장만 씁니다. 이 덱으로 무엇을 익히게 되는지, 농장에서 어떤 때 도움이 되는지를 담습니다.
- 화면에 그대로 표시되는 평문이라 마크다운은 쓰지 않습니다. 제목을 다시 옮겨 적지 말고 설명만 씁니다.
- 덱에 이미 들어 있는 카드 앞면 목록이 주어지면 그 내용을 반영하고, 목록에 없는 내용을 다룬다고 쓰지 않습니다.

예시
덱 제목: 호흡기 질병 기초
설명: 뉴캣슬병·전염성기관지염·마이코플라스마 등 닭 호흡기 질병의 대표 증상과 구별 포인트를 카드로 익힙니다. 계군에서 기침·콧물이 보일 때 먼저 의심할 질병을 빠르게 떠올리는 데 도움이 됩니다.`;

// contextLabel: 함께 넘기는 참고 정보의 이름(없으면 안 붙인다). contextMax: 그 길이 한도.
const AI_DRAFT_KINDS = {
  faq:  { system: FAQ_SYSTEM_PROMPT,  label: "질문",    contextLabel: "",               contextMax: 0 },
  card: { system: CARD_SYSTEM_PROMPT, label: "앞면",    contextLabel: "덱 주제",         contextMax: 200 },
  deck: { system: DECK_SYSTEM_PROMPT, label: "덱 제목", contextLabel: "이 덱의 카드 앞면", contextMax: 1500 },
};

// Claude 호출 공통부. 안전 분류기가 거절하면 서버가 권장 모델로 자동 재시도하고
// (fallbacks: "default"), SDK 오류는 관리 화면에 그대로 보여 줄 한국어 메시지로 바꾼다.
async function callClaude(params) {
  const client = new Anthropic({ apiKey: ANTHROPIC_API_KEY.value() });
  let response;
  try {
    response = await client.beta.messages.create({
      model: "claude-opus-5",
      max_tokens: 16000,
      betas: ["server-side-fallback-2026-07-01"],
      fallbacks: "default",
      ...params,
    });
  } catch (e) {
    if (e instanceof Anthropic.AuthenticationError) {
      throw new HttpsError("failed-precondition", "Claude API 키가 올바르지 않습니다 — Firebase 비밀값 ANTHROPIC_API_KEY를 확인하세요.");
    }
    if (e instanceof Anthropic.RateLimitError) {
      throw new HttpsError("resource-exhausted", "요청이 많아 잠시 뒤 다시 시도해 주세요.");
    }
    if (e instanceof Anthropic.APIError) {
      throw new HttpsError("internal", `Claude API 오류(${e.status ?? "연결"}): ${e.message}`);
    }
    throw new HttpsError("internal", e.message || String(e));
  }
  if (response.stop_reason === "refusal") {
    throw new HttpsError("failed-precondition", "AI가 이 내용은 처리하지 않았습니다. 직접 작성해 주세요.");
  }
  return response;
}

function responseText(response) {
  return response.content.filter((b) => b.type === "text").map((b) => b.text).join("").trim();
}

// output_config.format(json_schema)으로 받은 응답을 객체로 읽는다.
function responseJson(response) {
  try {
    return JSON.parse(responseText(response));
  } catch (e) {
    throw new HttpsError("internal", "AI 응답을 읽지 못했습니다. 다시 시도해 주세요.");
  }
}

exports.generateAiDraft = onCall({ secrets: [ANTHROPIC_API_KEY], timeoutSeconds: 120 }, async (request) => {
  assertAdmin(request);
  const data = request.data || {};
  const kind = AI_DRAFT_KINDS[data.kind];
  if (!kind) throw new HttpsError("invalid-argument", "kind는 faq, card, deck 중 하나여야 합니다.");
  const text = String(data.text || "").trim();
  const context = String(data.context || "").trim().slice(0, kind.contextMax);
  if (!text) throw new HttpsError("invalid-argument", `${kind.label}을 입력하세요.`);
  if (text.length > 500) throw new HttpsError("invalid-argument", `${kind.label}이 너무 깁니다(500자 이내).`);

  const userContent = (context && kind.contextLabel ? `${kind.contextLabel}: ${context}\n` : "") + `${kind.label}: ${text}`;
  const response = await callClaude({ system: kind.system, messages: [{ role: "user", content: userContent }] });
  const draft = responseText(response);
  if (!draft) throw new HttpsError("internal", "AI 초안이 비어 있습니다. 다시 시도해 주세요.");
  return { text: draft, model: response.model };
});

// ── 대표 증상 사진(학습 카드 뒷면 · 온라인 자가진단 질병) ────────────────────
// kind "card"는 학습 카드(앞면·뒷면·덱 주제), "selfcheck"는 자가진단 질병(질병명·
// 주요 증상·장기)을 front/back/context로 받는다.
// ① AI가 내용으로 Commons 영어 검색어를 정하고 ② Commons에서 자유 이용 사진
// 후보를 모은 뒤 ③ AI가 후보 사진을 직접 보고 대표 증상이 보이는 한 장을 고른다.
// Commons 검색 결과에는 이름만 비슷한 엉뚱한 사진(예: "MD" → 비행기 MD-82)이 섞이기
// 때문에 ③을 거친다. 결과는 관리 화면에 후보로 보여 주고, 발행은 관리자가 한다.
const IMAGE_QUERY_SYSTEM = `양계(닭) 교육 자료 — 온라인 학습 플래시카드나 온라인 자가진단의 질병 설명 — 에 붙일 "대표 증상·병변 사진"을 Wikimedia Commons에서 찾기 위한 영어 검색어를 정합니다.

- 내용이 질병·증상·병변·기생충·해충처럼 사진 한 장으로 보여 줄 수 있는 것이면 visual을 true로 하고, 영어 검색어를 2~3개 씁니다.
- 첫 검색어는 질병이나 대상의 영어 이름과 축종(예: "Newcastle disease chicken"), 나머지는 내용에 나온 대표 증상·병변을 구체적으로 씁니다(예: "chicken torticollis", "Newcastle disease conjunctiva"). 검색어마다 2~4단어로 짧게 씁니다.
- 장기(부위)가 주어지면 그 장기의 병변을 검색어 하나에 넣습니다(예: "fatty liver hemorrhagic syndrome liver").
- 약어는 풀어 씁니다(MD → Marek's disease, IB → infectious bronchitis). 약어만 쓰면 엉뚱한 사진이 검색됩니다.
- 사양관리 수치, 법규·제도, 경영, 약품 계열처럼 사진으로 보여 줄 대표 증상이 없는 내용이면 visual을 false로 하고 queries는 빈 배열로 둡니다.
- 닭이 아닌 축종(돼지·소 등)에 관한 내용이면 그 축종의 영어 이름을 붙입니다.`;

const IMAGE_PICK_SYSTEM = `양계 전문 수의사가 만든 교육 자료(온라인 학습 플래시카드 또는 온라인 자가진단의 질병 설명)에 붙일 "대표 증상·병변 사진"을 후보 중에서 한 장 고릅니다. 각 후보 사진 앞에 번호와 Wikimedia Commons 파일 이름이 있고, 마지막에 자료 내용이 있습니다.

- 자료가 말하는 질병·증상의 대표 소견이 실제로 눈에 보이는 사진을 고릅니다. 살아 있는 개체의 증상 사진을 먼저, 없으면 부검 병변 사진을 고릅니다.
- 장기(부위)가 주어지면 그 장기의 병변이나 그 장기와 관련된 증상이 보이는 사진을 우선합니다.
- 내용이 병원체 자체의 모양에 관한 것이 아니라면 전자현미경 사진이나 생활사·구조 도식은 고르지 않습니다. 지도, 사람이 주인공인 사진, 자료와 관계없는 사진도 고르지 않습니다.
- 파일 이름보다 사진에 실제로 보이는 내용을 기준으로 판단합니다.
- 알맞은 사진이 없으면 choice를 -1로 둡니다. 억지로 고르지 않습니다.
- reason에는 고른 사진에 무엇이 보이는지(고르지 않았다면 그 이유)를 한국어 한 문장으로 씁니다.`;

const IMAGE_QUERY_SCHEMA = {
  type: "object",
  properties: {
    visual: { type: "boolean" },
    queries: { type: "array", items: { type: "string" } },
  },
  required: ["visual", "queries"],
  additionalProperties: false,
};

const IMAGE_PICK_SCHEMA = {
  type: "object",
  properties: {
    choice: { type: "integer" },
    reason: { type: "string" },
  },
  required: ["choice", "reason"],
  additionalProperties: false,
};

exports.findCardImage = onCall({ secrets: [ANTHROPIC_API_KEY], timeoutSeconds: 180, memory: "512MiB" }, async (request) => {
  assertAdmin(request);
  const data = request.data || {};
  const front = String(data.front || "").trim().slice(0, 500);
  const back = String(data.back || "").trim().slice(0, 1000);
  const context = String(data.context || "").trim().slice(0, 200);
  const selfcheck = data.kind === "selfcheck";
  if (!front) throw new HttpsError("invalid-argument", selfcheck ? "질병명을 먼저 입력하세요." : "앞면을 먼저 입력하세요.");
  const cardText = selfcheck
    ? (context ? `장기(부위): ${context}\n` : "") + `질병: ${front}` + (back ? `\n주요 증상·특징: ${back}` : "")
    : (context ? `덱 주제: ${context}\n` : "") + `앞면: ${front}` + (back ? `\n뒷면: ${back}` : "");

  const plan = responseJson(await callClaude({
    system: IMAGE_QUERY_SYSTEM,
    messages: [{ role: "user", content: cardText }],
    output_config: { format: { type: "json_schema", schema: IMAGE_QUERY_SCHEMA } },
  }));
  const queries = (Array.isArray(plan.queries) ? plan.queries : []).map((q) => String(q).trim()).filter(Boolean).slice(0, 3);
  if (!plan.visual || !queries.length) return { visual: false, queries: [], candidates: [], chosen: -1, reason: "" };

  const candidates = await findCommonsCandidates(queries, 8);
  if (!candidates.length) return { visual: true, queries, candidates: [], chosen: -1, reason: "" };

  // 받아지지 않은 사진은 AI 판독에서만 빼고, 후보 목록에는 남겨 관리자가 직접 고를 수 있게 한다.
  const images = await Promise.all(candidates.map((c) => fetchCandidateImage(c).catch(() => null)));
  const content = [];
  candidates.forEach((c, i) => {
    if (!images[i]) return;
    content.push({ type: "text", text: `후보 ${i}: ${c.title}` });
    content.push({ type: "image", source: { type: "base64", media_type: images[i].media_type, data: images[i].data } });
  });
  if (!content.length) return { visual: true, queries, candidates, chosen: -1, reason: "후보 사진을 불러오지 못했습니다." };
  content.push({ type: "text", text: `자료 내용\n${cardText}` });

  const pick = responseJson(await callClaude({
    system: IMAGE_PICK_SYSTEM,
    messages: [{ role: "user", content }],
    output_config: { format: { type: "json_schema", schema: IMAGE_PICK_SCHEMA } },
  }));
  const chosen = Number.isInteger(pick.choice) && images[pick.choice] ? pick.choice : -1;
  return { visual: true, queries, candidates, chosen, reason: String(pick.reason || "").slice(0, 200) };
});

// ── 양계잡지 학습정보 — 지면 사진에서 글자만 옮겨 적기(OCR) ───────────────────
// 관리자가 양계 전문지 지면을 사진으로 찍어 올리면, 사진은 그대로 두고
// 글자만 옮겨 적어 제목·본문으로 나눠 돌려준다. 관리자가 그 결과를 확인·
// 수정한 뒤 발행하면(index.html 쪽에서 premium_content/magazine_notes에
// 저장) 승인된 회원 전체가 사진+본문을 게시판처럼 목록에서 본다.
const MAGAZINE_OCR_SYSTEM = `양계 전문지(잡지) 지면을 찍은 사진 1~10장을 보고, 그 지면에 인쇄된 글자를 그대로 옮겨 적습니다. 사진이 여러 장이면 같은 기사의 연속된 페이지(또는 같은 페이지의 다른 부분)이니, 주어진 순서대로 이어 붙여 하나의 글로 옮겨 적습니다.

- title에는 기사·코너 제목을 넣습니다. 제목이 여러 개 보이면 가장 큰(주된) 제목 하나만 고릅니다(사진이 여러 장이어도 title은 하나만).
- text에는 본문 글자를 실제 인쇄된 순서대로 옮겨 적습니다. 사진이 여러 장이면 페이지 순서대로 이어서 적고, 사진 설명(캡션)은 해당 위치에 "[사진설명] ..." 형식으로 붙입니다.
- 광고·목차·페이지 번호처럼 기사 본문이 아닌 요소는 옮기지 않습니다.
- 글자가 흐리거나 잘려서 정확히 읽을 수 없는 부분은 지어내지 말고 "(판독 불가)"로 표시합니다.
- summary에는 text의 핵심만 아주 짧게 골라냅니다. 완전한 문장이 아니라 헤드라인(제목)처럼 짧은 구(句)로, 요점 2~4개만 추립니다(문장이 길어지지 않게 각 줄은 한글 기준 12~20자 내외로 짧게). 전문용어는 쉬운 말로 바꾸되 서술어를 다 갖춘 문장으로 풀지 말고 핵심 단어 중심으로 씁니다. 각 줄 맨 앞에 "- "를 붙여 줄바꿈으로 구분합니다. 원문에 없는 내용을 지어내지 않습니다.
- 사진들에 읽을 만한 글자가 거의 없으면(사진 위주 지면 등) ok를 false로 하고 title·text·summary는 모두 빈 문자열로 둡니다.`;

const MAGAZINE_OCR_SCHEMA = {
  type: "object",
  properties: {
    ok: { type: "boolean" },
    title: { type: "string" },
    text: { type: "string" },
    summary: { type: "string" },
  },
  required: ["ok", "title", "text", "summary"],
  additionalProperties: false,
};

exports.extractMagazineText = onCall({ secrets: [ANTHROPIC_API_KEY], timeoutSeconds: 300, memory: "1GiB" }, async (request) => {
  assertAdmin(request);
  const data = request.data || {};
  const images = Array.isArray(data.images) ? data.images : [];
  if (!images.length) throw new HttpsError("invalid-argument", "사진을 먼저 선택하세요.");
  if (images.length > 10) throw new HttpsError("invalid-argument", "사진은 10장까지만 올릴 수 있습니다.");

  const content = [];
  images.forEach((img, i) => {
    const base64 = String((img && img.base64) || "");
    if (!base64) throw new HttpsError("invalid-argument", (i + 1) + "번째 사진을 읽지 못했습니다.");
    if (base64.length > 8_000_000) throw new HttpsError("invalid-argument", (i + 1) + "번째 사진 용량이 너무 큽니다.");
    const mediaType = String((img && img.mediaType) || "image/jpeg");
    if (images.length > 1) content.push({ type: "text", text: (i + 1) + "번째 사진" });
    content.push({ type: "image", source: { type: "base64", media_type: mediaType, data: base64 } });
  });
  content.push({ type: "text", text: "이 지면(들)의 글자를 옮겨 적어 주세요." });

  const result = responseJson(await callClaude({
    system: MAGAZINE_OCR_SYSTEM,
    messages: [{ role: "user", content }],
    output_config: { format: { type: "json_schema", schema: MAGAZINE_OCR_SCHEMA } },
  }));
  return {
    ok: !!result.ok,
    title: String(result.title || "").slice(0, 200),
    text: String(result.text || "").slice(0, 8000),
    summary: String(result.summary || "").slice(0, 1000),
  };
});

const BOARD_TYPES = ["diagnosis", "consult", "consulting", "specimen"];

// 온라인 상담·진단·컨설팅(premium_board/{boardType}/{uid}/{postId}/
// post.json·reply.json) — 회원용("mine": 내 글만)과 관리자용("inbox":
// 전체 회원 글) 둘 다 이 함수 하나로 처리한다. 사진 파일(photos/*)은
// post.json 안의 getDownloadURL() 링크를 <img src>로 그대로 쓰는데,
// <img> 태그는 fetch()와 달리 CORS 없이도 렌더링되므로 여기서 같이
// 내려줄 필요는 없다 — post.json·reply.json 본문만 이 문제(리다이렉트
// CORS)를 겪는다.
exports.getBoardPosts = onCall(async (request) => {
  if (!request.auth) throw new HttpsError("unauthenticated", "로그인이 필요합니다.");
  const { boardType, scope } = request.data || {};
  if (!BOARD_TYPES.includes(boardType)) {
    throw new HttpsError("invalid-argument", "잘못된 게시판입니다.");
  }
  const email = request.auth.token && request.auth.token.email;
  const isAdmin = !!(email && ADMIN_EMAILS.includes(String(email).toLowerCase()));
  const bucket = admin.storage().bucket(STORAGE_BUCKET);

  async function readJsonFile(path) {
    const file = bucket.file(path);
    const [exists] = await file.exists();
    if (!exists) return null;
    try {
      const [buf] = await file.download();
      return JSON.parse(buf.toString("utf-8"));
    } catch (e) {
      return null;
    }
  }

  const prefix = scope === "inbox"
    ? `premium_board/${boardType}/`
    : `premium_board/${boardType}/${request.auth.uid}/`;
  if (scope === "inbox" && !isAdmin) {
    throw new HttpsError("permission-denied", "관리자만 볼 수 있습니다.");
  }

  const [files] = await bucket.getFiles({ prefix });
  const posts = {};
  for (const file of files) {
    const parts = file.name.split("/"); // premium_board/{boardType}/{uid}/{postId}/post.json
    if (parts.length === 5 && parts[4] === "post.json") {
      const key = parts[2] + "/" + parts[3];
      const post = await readJsonFile(file.name);
      if (post) posts[key] = Object.assign({}, post, { uid: parts[2] });
    }
  }
  for (const file of files) {
    const parts = file.name.split("/");
    if (parts.length === 5 && parts[4] === "reply.json") {
      const key = parts[2] + "/" + parts[3];
      if (!posts[key]) continue;
      const reply = await readJsonFile(file.name);
      if (reply) posts[key].reply = reply;
    }
  }
  const list = Object.values(posts);
  list.sort((a, b) => (b.createdAt || "").localeCompare(a.createdAt || ""));
  return { posts: list };
});

// ── 🐔 최꼬꼬랑 대화 — 뉴스정보 옆의 닭 캐릭터 채팅 ────────────────────────────
// "최꼬꼬"라는 닭 캐릭터와 대화하며 사양관리·질병 지식을 재미있게 배우는
// 기능이다. 뉴스정보처럼 로그인 없이 누구나 쓰는 무료 탭이라 이 함수도
// 인증을 요구하지 않는다 — 다른 AI 함수(generateAiDraft 등)는 전부
// assertAdmin인 것과 다른 점. 로그인 없는 공개 엔드포인트라 누구나 무제한
// 호출하면 Claude API 비용이 새어나갈 수 있으므로, 대화 길이·메시지 길이·
// 답변 길이(max_tokens)를 짧게 제한해 둔다(본격적인 악용 방지가 필요해지면
// Firebase App Check 추가를 검토할 것).
//
// 승인된 유료회원(또는 관리자)이 호출한 경우엔 더 좋은 모델(claude-sonnet-5-5)과
// 더 긴 답변 한도로 올려 준다 — isApprovedOrAdmin(request)는 클라이언트가
// 보내는 값이 아니라 Firebase가 검증한 로그인 토큰(request.auth)을 그대로
// 보는 것이라 위조할 수 없다(유료서비스 메뉴를 통해 들어왔든, 무료 탭을 직접
// 눌러 들어왔든 — 같은 화면이라 로그인 여부로만 가른다).
// 승인된 유료회원에게는 캐릭터 이름 자체도 더 전문가다운 "최꼬박사"로
// 바뀐다(무료는 "최꼬꼬") — index.html의 kkokoDisplayName()과 같은 기준으로
// 화면 표시 이름을 맞춘다.
function chickenChatPersona(name, premium){
  const toneBlock = premium
    ? `당신은 "${name}"라는 이름의 양계 전문가 닭 캐릭터입니다. 이 사이트는 양계 농가를 위한 컨설팅 사이트이고, 당신은 이 농장에서 오래 살며 스스로도 많이 공부한 "박사" 캐릭터로서, 유료회원인 방문자(농장주·수의사·학생 등)에게 더 깊이 있고 전문적인 설명을 제공하는 역할을 맡고 있습니다.

말투와 태도
- 항상 닭 "${name}"의 1인칭 입장에서, 친절하지만 전문가답게 차분하고 믿음직한 말투로 대답합니다. 애교 섞인 "~꼬!" 말투는 아주 가끔만 살짝 섞고, 전체적으로는 신뢰감 있는 전문가 톤을 우선합니다.`
    : `당신은 "${name}"라는 이름의 쾌활한 닭 캐릭터입니다. 이 사이트는 양계 농가를 위한 컨설팅 사이트이고, 당신은 그 농장에 사는 닭의 입장에서 방문자(농장주·수의사·학생 등)와 대화하며 양계 지식을 재미있게 배우고 가르쳐 주는 역할을 맡고 있습니다.

말투와 태도
- 항상 닭 "${name}"의 1인칭 입장에서 대답합니다. 문장 끝에 가끔 "~꼬!", "꼬꼬~" 같은 말투를 자연스럽게 섞어 귀엽게 말하되, 정보 전달이 우선이므로 매 문장마다 과하게 넣지 않습니다.
- 친근하고 쾌활하되 가볍지 않게, 실제로 도움이 되는 내용을 말합니다.`;

  return `${toneBlock}

핵심 역할 — 사양관리·질병 상담
- 온도·습도·환기·사료·사육밀도·위생·깔짚 상태 같은 사육환경 조건을 알려주면, 그 조건이 닭(${name}) 입장에서 왜 좋은지/나쁜지와, 그런 조건에서 특히 잘 걸리는 질병이 무엇인지 실제 가금 사양관리·질병학 지식에 근거해 구체적으로 설명합니다.
- 모르는 내용은 추측해서 지어내지 않고 솔직히 모른다고 말합니다.
- 구체적인 약물 처방·투약량은 알려주지 않고, 치료나 정확한 진단이 필요한 질문에는 "그건 담당 수의사 선생님과 상의해야 할 것 같아요"처럼 짧게 안내합니다.
- 대화가 자연스럽게 이어지도록, 가끔 상대방의 농장 상황을 되묻는 짧은 질문을 던져 서로 배우는 느낌을 줍니다(매번 그럴 필요는 없습니다).
- 양계와 무관한 질문에는 ${name}답게 재치있게 양계 이야기로 화제를 돌립니다.`;
}

function chickenChatLength(name, premium){
  return premium
    ? `

답변 분량 (유료회원 — 더 자세한 설명 모드)
- 교과서식 나열이 아니라 여전히 ${name}의 입담으로 말하되, 짧게 끊지 말고 충분히 풀어서 설명합니다 — 필요하면 5문장 이상, 단락을 나눠도 좋습니다.
- 단, 답변은 반드시 중간에 끊기지 않고 마무리 문장까지 완결되어야 합니다. 분량은 공백 포함 약 700자 이내로 잡고, 내용이 많으면 중요한 순서대로 핵심만 추려 요약해서 그 안에 끝맺으세요(나머지는 "더 궁금하면 이어서 물어보세요"로 마무리).
- 왜 그런지 원리, 구체적인 수치·기준, 현장에서 바로 적용할 수 있는 실전 팁까지 한 번에 챙겨서 답합니다.
- 관련된 다른 위험 요인이나 함께 점검하면 좋은 항목이 있으면 덧붙여 알려줍니다.`
    : `

답변 분량
- 답변은 2~4문장 정도로 짧고 대화체로 합니다 — 교과서처럼 길게 늘어놓지 않습니다. 문장이 중간에 끊기지 않게 항상 끝까지 마무리합니다.`;
}

const CHICKEN_CHAT_FREE_MAX_TOKENS = 400;
const CHICKEN_CHAT_PREMIUM_MAX_TOKENS = 2400;       // 답변 분량은 프롬프트로 제한하고, 이 값은 생각 토큰까지 포함한 여유 한도
const CHICKEN_CHAT_FREE_MSG_CHARS = 300;
const CHICKEN_CHAT_PREMIUM_MSG_CHARS = 600;
const CHICKEN_CHAT_FREE_HISTORY = 12;
const CHICKEN_CHAT_PREMIUM_HISTORY = 20;

exports.chickenChat = onCall({ secrets: [ANTHROPIC_API_KEY], timeoutSeconds: 90 }, async (request) => {
  const premium = isApprovedOrAdmin(request);
  const msgChars = premium ? CHICKEN_CHAT_PREMIUM_MSG_CHARS : CHICKEN_CHAT_FREE_MSG_CHARS;
  const maxHistory = premium ? CHICKEN_CHAT_PREMIUM_HISTORY : CHICKEN_CHAT_FREE_HISTORY;

  const data = request.data || {};
  const incoming = Array.isArray(data.messages) ? data.messages : [];
  if (!incoming.length) throw new HttpsError("invalid-argument", "메시지가 없습니다.");
  if (incoming.length > maxHistory) throw new HttpsError("invalid-argument", "대화가 길어졌어요 — 대화를 새로 시작해 주세요.");

  const messages = incoming.map((m) => {
    const role = m && m.role === "assistant" ? "assistant" : "user";
    const content = String((m && m.text) || "").trim().slice(0, msgChars);
    return { role, content };
  }).filter((m) => m.content);
  if (!messages.length) throw new HttpsError("invalid-argument", "메시지가 비어 있습니다.");
  if (messages[messages.length - 1].role !== "user") {
    throw new HttpsError("invalid-argument", "마지막 메시지는 질문이어야 합니다.");
  }

  const name = premium ? "최꼬박사" : "최꼬꼬";
  const response = await callClaude({
    // 다른 AI 기능(generateAiDraft 등)은 기본값인 claude-opus-5를 그대로 쓰지만,
    // 이 캐릭터 대화 기능은 호출이 잦아 비용이 커지므로 모델을 낮춰 둔다 — 무료 이용자는
    // 훨씬 저렴한 Haiku, 승인된 유료회원은 Sonnet 5.5(Opus 5의 5분의 2 단가).
    // 유료회원 대화는 effort를 "low"로 두어 생각(thinking)에 쓰는 토큰을 줄인다(잡담·설명 위주라 충분).
    model: premium ? "claude-sonnet-5-5" : "claude-haiku-4-5-20251001",
    system: chickenChatPersona(name, premium) + chickenChatLength(name, premium),
    messages,
    max_tokens: premium ? CHICKEN_CHAT_PREMIUM_MAX_TOKENS : CHICKEN_CHAT_FREE_MAX_TOKENS,
    ...(premium ? { output_config: { effort: "low" } } : {}),
  });
  let reply = responseText(response);
  if (!reply) throw new HttpsError("internal", `${name}가 대답을 못 찾았어요 — 다시 물어봐 주세요.`);
  // 프롬프트로 분량을 줄였어도 토큰 한도에 걸려 잘렸다면, 마지막 미완성 문장을
  // 떼어내고 이어서 물어보라는 안내로 자연스럽게 닫는다.
  if (response.stop_reason === "max_tokens") {
    const cut = Math.max(reply.lastIndexOf("."), reply.lastIndexOf("!"), reply.lastIndexOf("?"), reply.lastIndexOf("요"), reply.lastIndexOf("다"));
    if (cut > reply.length * 0.5) reply = reply.slice(0, cut + 1);
    reply += "\n\n(여기까지 정리했어요 — 더 궁금한 부분은 이어서 물어보세요!)";
  }
  return { reply };
});


// ─── 문자 바로 보내기 (유료서비스 점등·환우 프로그램 등의 "📤 바로 보내기") ──────────────
// farm-pro의 send-sms(Supabase Edge Function)와 같은 구조다:
//   브라우저 → 이 함수(로그인·승인회원 확인, 검증, 하루 한도) → sms-relay(고정 IP) → 알리고
// 알리고 인증키는 sms-relay 서버에만 있고, 이 함수는 중계 서버 주소(SMS_RELAY_URL)와
// 그 서버 인증용 공유 비밀값(SMS_RELAY_SECRET)만 Firebase 비밀값으로 갖는다 — 둘 다 farm-pro와
// GitHub Actions(자동 문자 발송)가 쓰는 것과 같은 값이다. 등록:
//   firebase functions:secrets:set SMS_RELAY_URL     (예: https://….nip.io/send-sms)
//   firebase functions:secrets:set SMS_RELAY_SECRET
//
// 문자 요금이 실제로 나가는 기능이라 막아 두는 것:
//   - 승인된 유료회원(또는 관리자)만 호출 가능
//   - 발신번호는 클라이언트가 못 바꾼다(알리고에 등록된 대표번호 고정 — 자동 문자 발송 작업과 같은 번호)
//   - 사이트가 만든 프로그램 문자(머리말로 확인)만, 링크 금지 — 대표번호가 아무 글이나 보내는 통로가 되지 않게
//   - 받는 번호는 휴대폰(01X)만, 1회 최대 SMS_DIRECT_MAX_TARGETS명
//   - 승인 클레임과 별개로 승인 명부의 만료일을 직접 확인(기간 지난 회원 차단)
//   - 회원 1명당 하루(KST) SMS_DIRECT_DAILY_LIMIT건(받는 사람 수 기준), 관리자는 SMS_DIRECT_ADMIN_DAILY_LIMIT건
//   - 내용 끝에 출처 한 줄을 서버가 붙인다(받는 사람이 어디서 온 문자인지 알 수 있게)
//   - 보낸 기록은 Storage의 비공개 경로(sms_direct_log/, 클라이언트 접근 불가)에 남겨 관리자가 확인할 수 있다
const SMS_RELAY_URL = defineSecret("SMS_RELAY_URL");
const SMS_RELAY_SECRET = defineSecret("SMS_RELAY_SECRET");
const SMS_DIRECT_SENDER = "01091508844";       // 최동명 수의사 대표번호 — scripts/send_sms_subscriptions.py의 SENDER_PHONE과 같은 값
const SMS_DIRECT_MAX_TARGETS = 5;
const SMS_DIRECT_DAILY_LIMIT = 20;
const SMS_DIRECT_ADMIN_DAILY_LIMIT = 200;
const SMS_DIRECT_SMS_BYTES = 90;               // 단문(SMS) 한도 — 넘으면 장문(LMS)
const SMS_DIRECT_LMS_BYTES = 2000;             // 장문(LMS) 한도(알리고 기준)
const SMS_DIRECT_FOOTER = "\n- 농장동물 컨설팅(polcon.cc)";
// 바로 보내기로 보낼 수 있는 글 종류 — 대표번호로 아무 글이나 보내는 통로가 되지 않도록 사이트가 만든 글(머리말)만 받는다.
const SMS_DIRECT_KINDS = {
  light: ["[산란계 점등프로그램]", "[육계 점등프로그램]"],
  molt: ["[산란계 환우 프로그램]"],
};
// 링크·전화번호는 막는다(대표번호로 보내는 문자가 스미싱·광고 통로가 되지 않게). 사이트가 만드는 프로그램 문자에는
// polcon.cc 말고는 '글자.글자' 꼴의 주소나 전화번호가 나오지 않는다(환우·점등 문자 전체를 이 규칙으로 검사해 확인함).
const SMS_DIRECT_LINK_RE = /https?:|www\.|[a-z0-9가-힣-]\.[a-z가-힣]{2,}/i;
const SMS_DIRECT_PHONE_RE = /0\d{1,2}[-. ]?\d{3,4}[-. ]?\d{4}/;
function smsDirectSuspicious(body) {
  const norm = body.normalize("NFKC").replace(/[。．｡]/g, ".");
  const stripped = norm.replace(/(^|[^a-z0-9.-])polcon\.cc(?![a-z0-9.-])/gi, "$1");
  return SMS_DIRECT_LINK_RE.test(stripped) || SMS_DIRECT_PHONE_RE.test(stripped);
}

// EUC-KR 근사 바이트(ASCII 1, 그 외 2) — farm-pro의 js/sms.js·send-sms·sms-relay, index.html의 smsByteLength와 같은 방식
function smsByteLength(text) {
  let bytes = 0;
  for (const ch of text) bytes += ch.codePointAt(0) > 0x7f ? 2 : 1;
  return bytes;
}

function kstDateString(d) {
  return new Date(d.getTime() + 9 * 3600 * 1000).toISOString().slice(0, 10);
}

// 승인 명부에서 회원 기간이 오늘(KST)까지 유효한지 — 클레임(approved)은 관리자가 회원을 다시 저장할 때만 바뀌어
// 기간이 지난 회원에게도 남아 있을 수 있으므로, 요금이 나가는 기능은 명부를 직접 확인한다.
async function memberActiveToday(email) {
  const file = admin.storage().bucket(STORAGE_BUCKET).file("member_registry/approved.json");
  let members;
  try {
    const [buf] = await file.download();
    members = JSON.parse(buf.toString("utf-8")).members || [];
  } catch (e) {
    throw new HttpsError("failed-precondition", "회원 명부를 확인하지 못했습니다 — 잠시 후 다시 시도해 주세요.");
  }
  const me = members.find((m) => String(m.email || "").toLowerCase().trim() === email);
  if (!me) return false;
  return !me.expires || String(me.expires) >= kstDateString(new Date());
}

// 하루 사용량 파일을 "읽은 그 버전"에 조건을 걸고 고친다(compare-and-swap). 다른 요청이 사이에 고쳤으면 412가 나므로
// 다시 읽어 재시도한다. update(cur) 가 null 을 돌려주면 쓰지 않고 그 값을 그대로 돌려준다.
async function casUsage(file, update, tries = 4) {
  for (let i = 0; i < tries; i++) {
    let cur = 0;
    let generation = 0;
    try {
      const [meta] = await file.getMetadata();
      generation = Number(meta.generation) || 0;
      const [buf] = await file.bucket.file(file.name, { generation: meta.generation }).download();
      cur = Number(JSON.parse(buf.toString("utf8")).count) || 0;
    } catch (e) {
      if (e.code !== 404) throw e;   // 오늘 첫 발송이면 파일이 없다(generation 0 = "없을 때만 만들기")
    }
    const next = update(cur);
    if (next === null) return { cur, written: false };
    try {
      await file.save(JSON.stringify({ count: next, updatedAt: new Date().toISOString() }), {
        contentType: "application/json",
        resumable: false,
        preconditionOpts: { ifGenerationMatch: generation },
      });
      return { cur, next, written: true };
    } catch (e) {
      if (e.code !== 412 && e.code !== 404) throw e;   // 다른 요청이 먼저 고침 → 다시 읽고 재시도
    }
  }
  throw new HttpsError("aborted", "동시에 여러 번 보내기를 눌렀습니다 — 잠시 후 다시 시도해 주세요.");
}

exports.sendDirectSms = onCall({ secrets: [SMS_RELAY_URL, SMS_RELAY_SECRET], timeoutSeconds: 40 }, async (request) => {
  if (!request.auth) throw new HttpsError("unauthenticated", "로그인이 필요합니다.");
  if (!isApprovedOrAdmin(request)) throw new HttpsError("permission-denied", "유료서비스 승인 회원만 문자를 바로 보낼 수 있습니다.");
  const email = String(request.auth.token.email || "").toLowerCase().trim();
  const isAdmin = ADMIN_EMAILS.includes(email);

  const data = request.data || {};
  const kind = data.kind;
  if (!SMS_DIRECT_KINDS[kind]) throw new HttpsError("invalid-argument", "이 화면에서는 문자를 바로 보낼 수 없습니다.");
  const rawTo = Array.isArray(data.to) ? data.to : String(data.to || "").split(/[,;\/\n]+/);
  const targets = [...new Set(rawTo.map((s) => String(s || "").replace(/[^0-9]/g, "")).filter(Boolean))];
  if (!targets.length) throw new HttpsError("invalid-argument", "받는 사람 휴대폰 번호를 입력하세요.");
  if (targets.length > SMS_DIRECT_MAX_TARGETS) {
    throw new HttpsError("invalid-argument", `한 번에 최대 ${SMS_DIRECT_MAX_TARGETS}명까지 보낼 수 있습니다.`);
  }
  const badNumber = targets.find((n) => !/^01[016789]\d{7,8}$/.test(n));
  if (badNumber) throw new HttpsError("invalid-argument", `휴대폰 번호 형식이 아닙니다: ${badNumber}`);

  const body = String(data.content || "").replace(/\r\n?/g, "\n").trim();
  if (!body) throw new HttpsError("invalid-argument", "보낼 내용이 없습니다.");
  if (!SMS_DIRECT_KINDS[kind].some((h) => body.startsWith(h))) {
    throw new HttpsError("invalid-argument", "사이트에서 만든 프로그램 문자만 바로 보낼 수 있습니다.");
  }
  if (smsDirectSuspicious(body)) {
    throw new HttpsError("invalid-argument", "문자에 인터넷 주소나 전화번호를 넣어 보낼 수 없습니다.");
  }
  const content = body + SMS_DIRECT_FOOTER;
  const bytes = smsByteLength(content);
  if (bytes > SMS_DIRECT_LMS_BYTES) {
    throw new HttpsError("invalid-argument", `내용이 너무 깁니다(${bytes}byte, 최대 ${SMS_DIRECT_LMS_BYTES}byte). '요약'으로 바꿔 보내세요.`);
  }

  // 기간이 지난 회원 차단(관리자는 제외)
  if (!isAdmin && !(await memberActiveToday(email))) {
    throw new HttpsError("permission-denied", "유료서비스 이용 기간이 끝나 문자를 바로 보낼 수 없습니다.");
  }

  // 하루 한도(받는 사람 수 기준) — 비공개 Storage 파일에 날짜별로 센다. 보내기 전에 먼저 올려 둔다.
  const bucket = admin.storage().bucket(STORAGE_BUCKET);
  const now = new Date();
  const today = kstDateString(now);
  const limit = isAdmin ? SMS_DIRECT_ADMIN_DAILY_LIMIT : SMS_DIRECT_DAILY_LIMIT;
  const usageFile = bucket.file(`sms_direct_usage/${request.auth.uid}/${today}.json`);
  const reserved = await casUsage(usageFile, (cur) => (cur + targets.length > limit ? null : cur + targets.length));
  if (!reserved.written) {
    throw new HttpsError("resource-exhausted", `오늘 보낼 수 있는 문자(${limit}건)를 모두 썼습니다. 내일 다시 이용하거나 '문자 앱으로 열기'를 쓰세요.`);
  }
  const logFile = bucket.file(`sms_direct_log/${today.slice(0, 7)}/${now.toISOString().replace(/[:.]/g, "-")}_${request.auth.uid}.json`);
  const writeLog = (extra) => logFile.save(JSON.stringify({ at: now.toISOString(), email, kind, to: targets, bytes, ...extra }),
    { contentType: "application/json", resumable: false }).catch((e) => console.warn("sms log write failed:", e.message));

  // 중계 서버 호출. 결과를 셋으로 나눈다:
  //   성공 / 확실한 실패(중계 서버가 검증·인증에서 거절, 또는 알리고가 실패 코드로 응답 → 발송 안 됨, 한도 되돌림)
  //   / 결과 불명(시간 초과·연결 끊김·응답 해석 불가 → 이미 나갔을 수 있어 한도를 되돌리지 않고 다시 보내지 말라고 안내)
  let relayRes = null;
  let result = null;
  try {
    relayRes = await fetch(SMS_RELAY_URL.value(), {
      method: "POST",
      headers: { Authorization: `Bearer ${SMS_RELAY_SECRET.value()}`, "Content-Type": "application/json" },
      body: JSON.stringify({ from: SMS_DIRECT_SENDER, content, targets: targets.map((to) => ({ to })) }),
      signal: AbortSignal.timeout(25000),
    });
    result = await relayRes.json().catch(() => null);
  } catch (e) {
    relayRes = null;
  }
  if (relayRes && relayRes.ok && result && result.ok !== false) {
    await writeLog({ ok: true, messageType: result.messageType, successCount: result.successCount, errorCount: result.errorCount });
    return {
      ok: true,
      messageType: result.messageType || (bytes > SMS_DIRECT_SMS_BYTES ? "LMS" : "SMS"),
      bytes,
      successCount: Number(result.successCount) || 0,
      errorCount: Number(result.errorCount) || 0,
      remaining: Math.max(0, limit - reserved.next),
    };
  }
  const errText = (result && result.error) || (relayRes ? `중계 서버 오류 (HTTP ${relayRes.status})` : "중계 서버 연결 실패/시간 초과");
  const definiteFail = !!relayRes && !!result && (
    [400, 401, 403, 404, 405].includes(relayRes.status) ||
    (relayRes.status === 502 && /^알리고 발송 실패/.test(String(result.error || "")))
  );
  if (definiteFail) {
    await casUsage(usageFile, (cur) => Math.max(0, cur - targets.length)).catch(() => {});   // 되돌리기 실패는 한도가 조금 일찍 차는 것뿐
    await writeLog({ ok: false, error: errText });
    throw new HttpsError("unavailable", `문자 발송 실패: ${errText}`);
  }
  await writeLog({ ok: "unknown", error: errText });
  throw new HttpsError("deadline-exceeded", "발송 결과를 확인하지 못했습니다 — 이미 발송됐을 수 있으니 받는 분께 먼저 확인한 뒤 다시 보내세요.");
});
