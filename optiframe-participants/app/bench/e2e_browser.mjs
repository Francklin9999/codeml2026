// End-to-end check of the BUILT app in a real Chromium (headless Chrome or Edge), phone viewport, no mocks:
// home -> right lens -> import a fixture photo -> result -> validate -> left lens -> same -> frame -> STL download.
// The photo goes through the file chooser exactly as "Importer une photo" does on a phone; OpenCV.js runs in
// the real worker. Not part of `npm test` (needs a browser and a running server).
//
//   npm run build && npx vite preview --port 4173 &
//   node bench/e2e_browser.mjs [--url http://localhost:4173/] [--chrome <path>] [--out <dir>]
//        [--photo-r <png>] [--photo-l <png>] [--cpu 4] [--net 4g]
// --cpu N slows the page's CPU N times (DevTools emulation; NOT the Web Worker where the processing runs);
// --net 4g|3g throttles the network (4g: 9 Mbit/s down, 60 ms; 3g: 1.6 Mbit/s, 150 ms). Emulation, not a phone.
//
// puppeteer-core is not an app dependency: install it anywhere and point NODE_PATH at it, e.g.
//   npm i --prefix <scratch> puppeteer-core && NODE_PATH=<scratch>/node_modules node bench/e2e_browser.mjs
import { existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { join, resolve } from 'node:path';

const require = createRequire(import.meta.url);
const puppeteer = require('puppeteer-core');

const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
const url = arg('--url', 'http://localhost:4173/');
const out = resolve(arg('--out', 'bench/e2e_out'));
const chrome = arg('--chrome', [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  '/usr/bin/google-chrome', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
].find((p) => existsSync(p)));
const fixtureDir = resolve(import.meta.dirname, '../../rig/out/fixtures');
const photoR = arg('--photo-r', join(fixtureDir, 'fixture_04_ellipse_medium.png'));
const photoL = arg('--photo-l', join(fixtureDir, 'fixture_02_rrect_thick_band.png'));
const cpu = Number(arg('--cpu', '1'));
const net = arg('--net', '');
const NETS = { '4g': { downloadThroughput: 9e6 / 8, uploadThroughput: 1.5e6 / 8, latency: 60 }, '3g': { downloadThroughput: 1.6e6 / 8, uploadThroughput: 0.75e6 / 8, latency: 150 } };
mkdirSync(out, { recursive: true });

const report = { url, chrome, cpu, net: net || 'none', steps: [], console: [], pageErrors: [], ok: false };
const step = (name, extra = {}) => { const s = { name, t: Date.now(), ...extra }; report.steps.push(s); console.log('·', name, JSON.stringify(extra)); };

const browser = await puppeteer.launch({ executablePath: chrome, headless: true, args: ['--no-sandbox'] });
try {
  const page = await browser.newPage();
  // A mid-range Android phone (Pixel 7 class): 412 x 915 CSS px, DPR 2.6, touch.
  await page.emulate({
    viewport: { width: 412, height: 915, deviceScaleFactor: 2.625, isMobile: true, hasTouch: true },
    userAgent: 'Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Mobile Safari/537.36',
  });
  page.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') report.console.push(`${m.type()}: ${m.text()}`); });
  page.on('pageerror', (e) => report.pageErrors.push(String(e)));
  page.on('response', (r) => { if (r.status() >= 400) report.console.push(`HTTP ${r.status()} ${r.url()}`); });
  const cdp = await page.createCDPSession();
  await cdp.send('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: out, eventsEnabled: true });
  // Slows the page only: Chrome refuses CPU throttling on workers ("only supported for pages, not workers"), and OpenCV,
  // the model and the measurement run in the Web Worker. So --cpu says nothing about phone processing times.
  if (cpu > 1) await cdp.send('Emulation.setCPUThrottlingRate', { rate: cpu });
  if (net) { await cdp.send('Network.enable'); await cdp.send('Network.emulateNetworkConditions', { offline: false, ...NETS[net] }); }

  const t0 = Date.now();
  await page.goto(url, { waitUntil: 'networkidle0', timeout: 120_000 });
  step('home loaded', { ms: Date.now() - t0 });
  await page.screenshot({ path: join(out, '01_home.png') });

  const clickText = async (text, timeout = 30_000) => {
    const el = await page.waitForFunction((t) => [...document.querySelectorAll('button')].find((b) => b.textContent.trim().startsWith(t) && !b.disabled), { timeout }, text);
    await el.asElement().click();
  };
  const screen = () => page.$eval('[data-screen]', (e) => e.getAttribute('data-screen')).catch(() => null);

  async function measureLens(eye, photo, label) {
    await page.click(`button[data-eye="${eye}"]`);
    await page.waitForSelector('[data-screen="capture"]');
    const ts = Date.now();
    const [chooser] = await Promise.all([page.waitForFileChooser({ timeout: 30_000 }), clickText('Importer une photo')]);
    await chooser.accept([photo]);
    // Done when the counter shows a photo, or an error hint appears.
    await page.waitForFunction(() => document.querySelector('.count') || document.querySelector('.hint'), { timeout: 180_000 });
    const hint = await page.$eval('.hint', (e) => e.textContent).catch(() => null);
    step(`${label}: photo processed`, { ms: Date.now() - ts, hint });
    await page.screenshot({ path: join(out, `02_capture_${eye}.png`) });
    if (hint && !(await page.$('.count'))) throw new Error(`${label}: refused with "${hint}"`);
    await clickText('Terminer avec');
    await page.waitForSelector('[data-screen="result"]');
    const values = await page.$$eval('dd[data-value]', (els) => Object.fromEntries(els.map((e) => [e.getAttribute('data-value'), e.textContent])));
    const truth = JSON.parse(readFileSync(photo.replace(/\.png$/, '.json'), 'utf8'));
    step(`${label}: result`, { values, truth: { A: truth.widthMm, B: truth.heightMm } });
    await page.screenshot({ path: join(out, `03_result_${eye}.png`), fullPage: true });
    // SVG 1:1 export
    await clickText('Exporter le contour');
    await clickText('Valider');
    await page.waitForSelector('[data-screen="home"]');
  }

  await measureLens('R', photoR, 'right lens');
  await measureLens('L', photoL, 'left lens');
  await clickText('Créer la monture');
  await page.waitForFunction(() => document.querySelector('[data-screen]')?.getAttribute('data-screen') !== 'home', { timeout: 60_000 });
  const ts = Date.now();
  await page.waitForFunction(() => [...document.querySelectorAll('button')].some((b) => /monture.stl/i.test(b.textContent) && !b.disabled), { timeout: 180_000 });
  step('frame ready', { ms: Date.now() - ts, screen: await screen() });
  await new Promise((r) => setTimeout(r, 1500)); // let the 3D preview draw
  await page.screenshot({ path: join(out, '04_frame.png'), fullPage: true });
  const before = new Set(readdirSync(out));
  await page.evaluate(() => [...document.querySelectorAll('button')].find((b) => /monture.stl/i.test(b.textContent)).click());
  const deadline = Date.now() + 30_000;
  let stl = null;
  while (Date.now() < deadline && !stl) {
    stl = readdirSync(out).find((f) => !before.has(f) && f.toLowerCase().endsWith('.stl')) ?? null;
    await new Promise((r) => setTimeout(r, 300));
  }
  if (!stl) throw new Error('no STL downloaded');
  const svg = readdirSync(out).filter((f) => f.toLowerCase().endsWith('.svg'));
  step('downloads', { stl, stlBytes: statSync(join(out, stl)).size, svg });
  report.ok = report.pageErrors.length === 0;
} catch (e) {
  report.error = String(e && e.stack || e);
  console.error(report.error);
} finally {
  writeFileSync(join(out, 'report.json'), JSON.stringify(report, null, 2));
  await browser.close();
}
console.log(report.ok ? 'E2E OK' : 'E2E FAILED', '-', join(out, 'report.json'));
process.exit(report.ok ? 0 : 1);
