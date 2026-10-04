// Service worker: offline after the first load.
// Bump VERSION on every release that changes cached files; old caches are deleted on activate.
const VERSION = 'v2';
const CACHE = 'optiframe-' + VERSION;

// Big, rarely-changing files: serve from cache first.
const isHeavy = (url) => /\/(vendor|models)\//.test(url.pathname);

// Needed by every measurement or frame: fetched at install so the app works offline after the first visit.
// (ort and the model are optional: they are cached on first use by the rule below.)
// Never add vendor/ort/ here: its 14 MB WASM must only be downloaded when models/lens_seg.onnx exists (segmentModel.ts).
const PRECACHE = ['./vendor/opencv/opencv.js', './vendor/manifold/manifold.wasm'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    (async () => {
      const cache = await caches.open(CACHE);
      try {
        // Cache the shell and the hashed assets it references, so a reload works offline
        // even though the page that registered us loaded them before we took control.
        const page = new URL('./', self.location);
        const res = await fetch(page, { cache: 'reload' });
        const html = await res.clone().text();
        await cache.put(page, res);
        const refs = [...html.matchAll(/(?:src|href)="(\.\/[^"]+)"/g)].map((m) => new URL(m[1], page).href);
        await Promise.all(refs.map((u) => cache.add(u).catch(() => {})));
        await Promise.all(PRECACHE.map((u) => cache.add(new URL(u, page)).catch(() => {})));
      } catch {
        // Offline at install time: runtime caching below still fills the cache.
      }
      await self.skipWaiting();
    })(),
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    (async () => {
      for (const key of await caches.keys()) if (key !== CACHE) await caches.delete(key);
      await self.clients.claim();
    })(),
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  // The model probe is a HEAD request. Network first, so a model deployed later is seen; offline, the cached file answers.
  if (req.method === 'HEAD' && isHeavy(url)) {
    event.respondWith(
      fetch(req).catch(async () => {
        const hit = await caches.match(url.href);
        return hit ? new Response(null, { status: 200, headers: hit.headers }) : Response.error();
      }),
    );
    return;
  }
  if (req.method !== 'GET') return;

  if (isHeavy(url)) {
    event.respondWith(
      caches.match(req).then(
        (hit) =>
          hit ||
          fetch(req).then((res) => {
            if (res.status === 200) {
              const copy = res.clone();
              event.waitUntil(caches.open(CACHE).then((c) => c.put(req, copy)));
            }
            return res;
          }),
      ),
    );
    return;
  }

  event.respondWith(
    fetch(req)
      .then((res) => {
        // 200 only: a 206 partial response must never be stored as if it were the whole file.
        if (res.status === 200) {
          const copy = res.clone();
          event.waitUntil(caches.open(CACHE).then((c) => c.put(req, copy)));
        }
        return res;
      })
      .catch(async () => {
        const hit = await caches.match(req, { ignoreSearch: true });
        if (hit) return hit;
        // Offline navigation to /index.html or any sub-path: serve the cached shell.
        if (req.mode === 'navigate') return (await caches.match(new URL('./', self.location))) || Response.error();
        return Response.error();
      }),
  );
});
