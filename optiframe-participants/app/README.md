# OptiFrame app

Static mobile web app (Vite + TypeScript strict, no UI framework). All processing runs in the browser.

## Run locally

```
cd optiframe-participants/app
npm ci            # first time (npm install is only for adding packages)
npm run dev       # http://localhost:5173 (camera needs HTTPS or localhost)
```

## Test, typecheck, build

```
npm run typecheck   # tsc --noEmit
npm test            # Vitest, node environment; a test that needs the DOM starts with // @vitest-environment jsdom
npm run build       # writes dist/ (base './', so it works from any sub-path)
npm run size        # after a build: initial JS (raw, gzip) and files over 0.3 MB; fails over 250 kB gzip
npm run preview     # serve dist/ locally
```

Timings: the "Pas à pas" screen lists the duration of every stage of the last photo (ms, on the device in hand).
`tests/perf/budget.test.ts` is a Node regression guard (under 3000 ms after OpenCV has loaded), not a phone figure.

`src/test/setup.ts` defines a minimal `ImageData` (Node and jsdom have none) for every test.

## Layout

- `src/contracts.ts`: shared types, never edit without telling every owner.
- `src/<module>/index.ts`: one entry point per brief (stubs throw `OptiError('LOAD_FAILED', 'not implemented')` until the owner replaces them).
- `src/worker.ts`: Web Worker; `handleMessage` is exported so tests can call it without a Worker. New message types go in `WorkerRequest` / `WorkerResponse`.
- `public/sw.js`, `public/manifest.webmanifest`, `src/swRegister.ts`: offline support (below).
- `index.html` is built; `eval.html` is built too as soon as the file exists. `public/` files are copied as they are.

## Offline (service worker)

`sw.js` caches the page and its assets at install, precaches `collect.html` and `eval.html` with their assets, serves `vendor/` cache-first, everything else (including `models/`, so a retrained model is picked up) network-first with cache fallback. Bump `VERSION` in `sw.js` when cached files change in a way the network-first rule would not pick up; old caches are deleted on activate. Open the app with `?nosw=1` to unregister the worker and clear its caches (use it if a phone keeps a stale version). Offline reload on a real phone: TO MEASURE.

## Deploy (GitHub Pages)

`.github/workflows/deploy.yml` (at the Git repository root) builds `optiframe-participants/app` and publishes `dist/` on every push to `main`.

1. One time: repository Settings > Pages > Source = GitHub Actions.
2. Push to `main`. The URL is `https://<user>.github.io/<repo>/` (shown in the workflow run).
3. Typecheck and tests run in the workflow but do not block the deploy (a red test must not stop a demo fix). Read the run log.
4. Last known good: tag a good commit (`git tag good-1 && git push --tags`), then Actions > Deploy OptiFrame > Run workflow > `ref` = `good-1`. The workflow runs from `main` and deploys that tag.

## QR code of the final URL

```
npm run qr -- https://<user>.github.io/<repo>/
```

Writes `public/qr.svg` (uses the `qrcode` package; the URL must start with `https://`). Rebuild so `dist/` contains it, and print the SVG.
