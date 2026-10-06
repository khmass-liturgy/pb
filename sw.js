// 앱 설치(PWA)는 쓰지 않는다 — 예전에 등록된 서비스워커가 남아 있으면 스스로 해제한다.
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", e => e.waitUntil(self.registration.unregister().then(() => self.clients.matchAll()).then(cs => cs.forEach(c => c.navigate(c.url)))));
