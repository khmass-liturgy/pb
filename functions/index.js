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
const admin = require("firebase-admin");

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
