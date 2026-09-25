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
// 그런데 승인 여부는 premium/approved.json(누가 회원인지)에 있지, Firebase
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

const AI_DRAFT_KINDS = {
  faq:  { system: FAQ_SYSTEM_PROMPT,  label: "질문" },
  card: { system: CARD_SYSTEM_PROMPT, label: "앞면" },
};

exports.generateAiDraft = onCall({ secrets: [ANTHROPIC_API_KEY], timeoutSeconds: 120 }, async (request) => {
  assertAdmin(request);
  const data = request.data || {};
  const kind = AI_DRAFT_KINDS[data.kind];
  if (!kind) throw new HttpsError("invalid-argument", "kind는 faq 또는 card여야 합니다.");
  const text = String(data.text || "").trim();
  const context = String(data.context || "").trim().slice(0, 200);
  if (!text) throw new HttpsError("invalid-argument", `${kind.label}을 입력하세요.`);
  if (text.length > 500) throw new HttpsError("invalid-argument", `${kind.label}이 너무 깁니다(500자 이내).`);

  const userContent = (context ? `덱 주제: ${context}\n` : "") + `${kind.label}: ${text}`;
  const client = new Anthropic({ apiKey: ANTHROPIC_API_KEY.value() });
  let response;
  try {
    // 안전 분류기가 거절하면 서버가 권장 모델로 자동 재시도(fallbacks: "default").
    response = await client.beta.messages.create({
      model: "claude-opus-5",
      max_tokens: 16000,
      betas: ["server-side-fallback-2026-07-01"],
      fallbacks: "default",
      system: kind.system,
      messages: [{ role: "user", content: userContent }],
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
    throw new HttpsError("failed-precondition", "AI가 이 내용에는 초안을 만들지 않았습니다. 직접 작성해 주세요.");
  }
  const draft = response.content.filter((b) => b.type === "text").map((b) => b.text).join("").trim();
  if (!draft) throw new HttpsError("internal", "AI 초안이 비어 있습니다. 다시 시도해 주세요.");
  return { text: draft, model: response.model };
});

const BOARD_TYPES = ["diagnosis", "consult", "consulting"];

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
