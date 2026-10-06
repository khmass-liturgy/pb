// 최소 서비스워커 — 오프라인 캐시는 하지 않는다(시세·발생현황이 항상 최신이어야 함).
// 브라우저가 '앱 설치(바탕화면에 추가)'를 허용하려면 서비스워커가 등록돼 있어야 하는 경우가 있어 둔다.
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", e => e.waitUntil(self.clients.claim()));
self.addEventListener("fetch", () => {});
