# OptiFrame · Strategy 10: In-browser web app delivery (HTTPS, QR, camera, error messages, device matrix)

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 (put it online in the first hour, per the brief) |
| **Effort** | 5–7 h spread over the day |
| **Depends on** | nothing to start; integrates strategies 2, 3/5/6, 7, 8, 9 |
| **Rubric lines** | Mobile web app (15), Robustness (10: "sans plantage"), Code (5), Presentation (10); enables everything else to be scored |
| **Work folder** | `optiframe-participants/work/strat10/` (the app itself, e.g. `work/strat10/app/`) |

---

## 1. Context you need

Mandatory format: **public HTTPS URL** (browsers block the camera without HTTPS) + **QR code**; no install, no account, no API key; mobile-first, one-handed, recent **Chrome (Android)** and **Safari (iOS)**, ~6-inch screens; built-in camera with **file-upload fallback**; in-browser processing recommended (JS / WebAssembly), Python server allowed if it stays up until deliberations end; free hosting (GitHub Pages, Netlify, Vercel, Cloudflare Pages, Hugging Face Spaces, Render); tunnels tolerated during evaluation; **< 30 s per pair** on a mid-range phone; **SVG 1:1 export button**; **clear messages** (not technical errors) when the reference object is missing, the photo is blurry or the lens is misplaced. Deliverables also include a step-by-step page with intermediate images and a downloadable `monture.stl` for the demo pair.

## 2. The idea

A static Progressive Web App (no server to keep alive) running the whole pipeline in the browser: OpenCV.js for markers and classical vision, ONNX Runtime Web for any model, Clipper + manifold-3d + three.js for the frame. Deploy continuously from the first hour, test on real phones all day, and keep a pre-recorded backup video.

## 3. Why it could score

15 points are for the app itself and 10 for robustness; more importantly, if the app fails on the jury's phone, the 30 accuracy points are lost too. A static, cached, tested PWA minimises that risk.

## 4. Implementation plan

### 4.1 Stack and layout

```
work/strat10/app/
  index.html            # single page: steps 1–4
  lightbox.html         # white / pattern screen for the rig (strategies 1, 4)
  src/camera.js         # getUserMedia, ImageCapture, upload fallback
  src/pipeline.js       # orchestrates: rectify → segment → measure → fuse
  src/vision/opencv-loader.js, aruco.js, segment.js, measure.js
  src/model/onnx.js     # optional model (strategy 5 / 6)
  src/frame/            # strategy 9 module
  src/ui/messages.js    # user-facing messages FR/EN
  sw.js                 # service worker: cache OpenCV.js, models, assets
  vendor/               # opencv.js (≈ 8–10 MB), onnxruntime-web, manifold, three (self-hosted, no CDN at runtime)
  manifest.webmanifest
```

Hosting: GitHub Pages or Cloudflare Pages from the repo (HTTPS by default). QR: generate once for the final URL (e.g. `qrcode` npm or Python `qrcode`), print it.

### 4.2 Camera

```js
const stream = await navigator.mediaDevices.getUserMedia({
  video: { facingMode: { ideal: "environment" }, width: { ideal: 4032 }, height: { ideal: 3024 } }, audio: false });
// Chrome Android: new ImageCapture(track).takePhoto() → full-res Blob
// iOS Safari: no ImageCapture; draw the video frame to a canvas at the track's settings resolution
// Fallback: <input type="file" accept="image/*" capture="environment"> (gives the original camera photo)
```

Known pitfalls to test: iOS requires a user gesture and `playsinline` on `<video>`; resolution caps on iOS video streams (prefer the file-input path for full resolution on iOS if stream resolution is low); EXIF orientation on uploaded files (`createImageBitmap(file, {imageOrientation: "from-image"})`).

### 4.3 Pipeline and performance

- Run heavy work in a **Web Worker** (OpenCV.js + ONNX) so the UI stays responsive; show progress per step.
- Downscale for detection, full resolution only in the window region for edge refinement.
- Budget per lens: markers 1 s, rectify 1 s, segment 1–8 s, refine 1 s, fuse 1 s → ≤ 12 s; two lenses ≤ 25 s.

### 4.4 Screens (one-handed, large buttons)

1. Choose eye (Gauche / Droit) + "Comment installer le dispositif" (link to the rig steps with photos).
2. Capture with live overlay: board detected (green), lens in window, sharpness OK → shutter or auto-capture.
3. Result: A, B, perimeter, control image (contour over photo), spread across shots (strategy 7), buttons "Exporter SVG 1:1", "Reprendre".
4. After both lenses: bridge width slider (default 18 mm), 3D preview, "Télécharger monture.stl", overlay contour vs rim with gap in mm.
5. "Pas à pas" page: reference detection, rectified image, mask, contour (deliverable).

### 4.5 Error messages (map each failure to a sentence and an action)

| Condition | Message |
|---|---|
| < 4 markers / no homography | "Je ne vois pas le cadre de référence en entier. Reculez un peu et cadrez toute la feuille." |
| Reprojection error too high | "Le cadre est trop incliné ou flou. Tenez le téléphone à plat au-dessus." |
| Blur (variance of Laplacian low) | "La photo est floue. Tenez le téléphone immobile et touchez l'écran pour faire la mise au point." |
| No lens / lens touches window border | "Je ne trouve pas le verre entier. Placez-le au centre de la fenêtre." |
| Glare | "Reflet détecté. Éteignez le flash ou inclinez légèrement le téléphone." |
| Shot spread too large | "Mesures incohérentes entre les photos. Reprenons une photo." |
| Camera permission denied | "Accès caméra refusé. Vous pouvez importer une photo à la place." + upload button |
| WASM / model load failure | "Chargement impossible. Vérifiez la connexion puis rechargez." (cached after first load) |

## 5. How to test it

### 5.1 Device matrix (at least)

| Device | Browser | Tests |
|---|---|---|
| Mid-range Android (2–3 years old) | Chrome | full flow, timing, ImageCapture path |
| Recent iPhone | Safari | full flow, file-input path, orientation |
| Any phone | Firefox / Samsung Internet | opens, upload fallback works |
| Laptop | Chrome | `/lightbox` page full screen |

### 5.2 Test cases

| # | Test | Pass if |
|---|---|---|
| T1 | Fresh-phone open via QR (no cache) | app usable in < 10 s on 4G |
| T2 | End-to-end two lenses | < 30 s total processing, STL downloads, SVG exports |
| T3 | Each error condition in 4.5 reproduced on purpose | the right message, no crash, no stack trace |
| T4 | Offline after first load (service worker) | reload works in airplane mode |
| T5 | Accuracy parity | in-browser A/B equal to the Python reference within 0.05 mm on the same photo |
| T6 | Stranger test | someone outside the team scans the QR, sets up the rig from instructions, gets a result without help |
| T7 | Backup | a recorded demo video exists and plays offline |

### 5.3 Continuous deployment

Every merge to the main branch redeploys; keep a "last known good" URL (tag) so a bad push cannot kill the demo.

## 6. Risks

- OpenCV.js size (~8–10 MB): self-host, cache with the service worker, show a loading bar.
- iOS camera quirks: test on a real iPhone early (hour 1–2), not at hour 22.

## 7. Combines with

All other strategies (it is the delivery vehicle); strategy 1 uses the `/lightbox` page; strategy 7 the burst capture; strategy 9 the 3D preview.

## 8. Results log

| Date | Who | Device / browser | T1–T7 results | Timing (pair) | Notes |
|---|---|---|---|---|---|
| | | | | | |
