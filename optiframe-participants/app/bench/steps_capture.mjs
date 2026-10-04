// Saves the four images of the app's own "Pas à pas" screen (and the result screen) for one photo, as PNG files,
// by driving the BUILT app in a real Chromium. Used for docs/PAS_A_PAS.md.
//   node bench/steps_capture.mjs --url <app url> --photo <png> --out <dir> [--prefix pas-a-pas]
// puppeteer-core via NODE_PATH, see e2e_browser.mjs.
import { existsSync, mkdirSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { join, resolve } from 'node:path';

const require = createRequire(import.meta.url);
const puppeteer = require('puppeteer-core');
const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
const url = arg('--url', 'http://localhost:4173/');
const photo = resolve(arg('--photo', ''));
const out = resolve(arg('--out', 'bench/steps_out'));
const prefix = arg('--prefix', 'pas-a-pas');
const chrome = arg('--chrome', ['C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', '/usr/bin/google-chrome'].find((p) => existsSync(p)));
mkdirSync(out, { recursive: true });

const browser = await puppeteer.launch({ executablePath: chrome, headless: true, args: ['--no-sandbox'] });
try {
  const page = await browser.newPage();
  await page.emulate({ viewport: { width: 412, height: 915, deviceScaleFactor: 2, isMobile: true, hasTouch: true },
    userAgent: 'Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Mobile Safari/537.36' });
  await page.goto(url, { waitUntil: 'networkidle0', timeout: 120_000 });
  const clickText = async (t) => {
    const el = await page.waitForFunction((s) => [...document.querySelectorAll('button')].find((b) => b.textContent.trim().startsWith(s) && !b.disabled), { timeout: 60_000 }, t);
    await el.asElement().click();
  };
  await page.click('button[data-eye="R"]');
  const [chooser] = await Promise.all([page.waitForFileChooser(), clickText('Importer une photo')]);
  await chooser.accept([photo]);
  await page.waitForFunction(() => document.querySelector('.count') || document.querySelector('.hint'), { timeout: 180_000 });
  await clickText('Terminer avec');
  await page.waitForSelector('[data-screen="result"]');
  await page.screenshot({ path: join(out, `${prefix}-5.png`), fullPage: true });
  const values = await page.$$eval('dd[data-value]', (els) => Object.fromEntries(els.map((e) => [e.getAttribute('data-value'), e.textContent])));
  await clickText('Pas à pas');
  await page.waitForSelector('[data-screen="steps"] canvas');
  const shots = await page.$$eval('[data-screen="steps"] figure', (figs) => figs.map((f) => ({
    png: f.querySelector('canvas').toDataURL('image/png'), caption: f.querySelector('figcaption').textContent })));
  shots.forEach((s, i) => writeFileSync(join(out, `${prefix}-${i + 1}.png`), Buffer.from(s.png.split(',')[1], 'base64')));
  const timings = await page.$$eval('[data-timing]', (els) => Object.fromEntries(els.map((e) => [e.getAttribute('data-timing'), e.textContent])));
  await page.screenshot({ path: join(out, `${prefix}-ecran.png`), fullPage: true });
  const info = { url, photo, values, captions: shots.map((s) => s.caption), timings };
  writeFileSync(join(out, `${prefix}.json`), JSON.stringify(info, null, 2));
  console.log(JSON.stringify(info, null, 2));
} finally {
  await browser.close();
}
