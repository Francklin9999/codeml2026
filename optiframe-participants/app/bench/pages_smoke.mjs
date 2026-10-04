// Every page of the BUILT app opens in a real Chromium at phone size without a page error or a failed request,
// and every error code of ?demo=1&error=CODE shows a French sentence, never a code or a stack trace.
//   node bench/pages_smoke.mjs [--url http://localhost:4173/] [--out <dir>]   (puppeteer-core via NODE_PATH, see e2e_browser.mjs)
import { existsSync, mkdirSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { join, resolve } from 'node:path';

const require = createRequire(import.meta.url);
const puppeteer = require('puppeteer-core');
const arg = (k, d) => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : d; };
const base = arg('--url', 'http://localhost:4173/');
const out = resolve(arg('--out', 'bench/e2e_out'));
const chrome = arg('--chrome', ['C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', '/usr/bin/google-chrome'].find((p) => existsSync(p)));
mkdirSync(out, { recursive: true });

const CODES = ['NO_REFERENCE', 'REFERENCE_TILTED', 'BLURRY', 'NO_LENS', 'LENS_OUT_OF_WINDOW', 'GLARE', 'INCONSISTENT_SHOTS',
  'LENS_ROTATED', 'CAMERA_DENIED', 'LOAD_FAILED'];
const pages = [['index.html', ''], ['index.html', '?demo=1'], ['eval.html', ''], ['collect.html', ''], ['lightbox.html', '']];
const results = [];
const browser = await puppeteer.launch({ executablePath: chrome, headless: true, args: ['--no-sandbox'] });
try {
  for (const [p, q] of [...pages, ...CODES.map((c) => ['index.html', `?demo=1&error=${c}`])]) {
    const page = await browser.newPage();
    await page.emulate({ viewport: { width: 390, height: 844, deviceScaleFactor: 3, isMobile: true, hasTouch: true },
      userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1' });
    const errors = [];
    page.on('pageerror', (e) => errors.push('pageerror: ' + e));
    page.on('response', (r) => { if (r.status() >= 400) errors.push(`HTTP ${r.status()} ${r.url()}`); });
    await page.goto(base + p + q, { waitUntil: 'networkidle0', timeout: 60_000 });
    let text = '';
    if (q.includes('error=')) {
      // Walk to the capture screen and take a photo: the forced error shows on the first failure path.
      await page.click('button[data-eye="R"]').catch(() => {});
      await page.waitForSelector('[data-screen="capture"]', { timeout: 5000 }).catch(() => {});
      await page.evaluate(() => [...document.querySelectorAll('button')].find((b) => /Prendre la photo/.test(b.textContent))?.click());
      await new Promise((r) => setTimeout(r, 800));
      text = await page.evaluate(() => [...document.querySelectorAll('.hint, [role="alert"], .error')].map((e) => e.textContent.trim()).join(' | '));
    }
    const hscroll = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
    const name = (p + q).replace(/[^a-z0-9]+/gi, '_');
    await page.screenshot({ path: join(out, `page_${name}.png`) });
    const leaked = /[A-Z]{2,}_[A-Z_]{2,}|Error|at \w+ \(/.test(text);
    results.push({ page: p + q, errors, hscroll, message: text || undefined, leaked: text ? leaked : undefined });
    await page.close();
  }
} finally {
  await browser.close();
}
writeFileSync(join(out, 'pages_report.json'), JSON.stringify(results, null, 2));
for (const r of results) console.log(r.errors.length || r.hscroll || r.leaked ? 'FAIL' : 'ok  ', r.page, r.errors.join('; '), r.hscroll ? 'HORIZONTAL SCROLL' : '', r.message ?? '');
process.exit(results.some((r) => r.errors.length || r.hscroll || r.leaked) ? 1 : 0);
