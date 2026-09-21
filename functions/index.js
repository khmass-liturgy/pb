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

function assertAdmin(request) {
  const email = request.auth && request.auth.token && request.auth.token.email;
  if (!email || !ADMIN_EMAILS.includes(String(email).toLowerCase())) {
    throw new HttpsError("permission-denied", "관리자만 사용할 수 있습니다.");
  }
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
