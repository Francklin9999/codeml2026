// Size report of the built app (run `npm run build` first): node scripts/size-report.mjs
// Prints the initial JavaScript (what the browser must download to show the first screen: the entry script of
// index.html, its modulepreload links and everything they import statically), raw and gzip, then every file of dist/
// over 0.3 MB. Exits 1 when the initial JavaScript exceeds 250 kB gzip, or when a heavy library (three.js, the frame
// generator, onnxruntime, OpenCV) has slipped into it.
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { dirname, join, posix, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { gzipSync } from 'node:zlib';

const BUDGET_GZIP_KB = 250;
const BIG_ASSET_MB = 0.3;
// Chunks that must stay behind a dynamic import (frame screen, model fallback) or inside the worker.
const LAZY_ONLY = /^(three|OrbitControls|frame|manifold|ort|segmentModel|worker|rectify|segmentClassic|opencv)[.-]/i;

const dist = resolve(dirname(fileURLToPath(import.meta.url)), '..', process.argv[2] ?? 'dist');
const page = join(dist, 'index.html');
if (!existsSync(page)) {
  console.error(`size-report: ${page} not found. Run "npm run build" first.`);
  process.exit(1);
}

const kb = (bytes) => (bytes / 1000).toFixed(2);
const gzipSize = (buf) => gzipSync(buf, { level: 9 }).length;

// Entry scripts and modulepreload links of index.html.
const html = readFileSync(page, 'utf8');
const entries = [];
for (const tag of html.match(/<(?:script|link)\b[^>]*>/g) ?? []) {
  const ref = /\b(?:src|href)="([^"]+\.js)"/.exec(tag)?.[1];
  if (!ref || /^[a-z]+:\/\//i.test(ref)) continue;
  if (tag.startsWith('<script') || /rel="modulepreload"/.test(tag)) entries.push(posix.normalize(ref));
}

// Static import closure. Dynamic imports are `import("./x.js")`: the regular expression needs `import` or `from` directly
// followed by the quoted path, which a call never has.
const STATIC_IMPORT = /(?:\bimport|\bfrom)\s*["'](\.{1,2}\/[^"']+\.js)["']/g;
const DYNAMIC_IMPORT = /\bimport\(\s*["'](\.{1,2}\/[^"']+\.js)["']/g;
const initial = new Map(); // path relative to dist -> Buffer
const lazy = new Set();
const todo = [...entries];
while (todo.length) {
  const rel = todo.pop();
  if (initial.has(rel)) continue;
  const file = join(dist, rel);
  if (!existsSync(file)) { console.error(`size-report: ${rel} is referenced but missing`); process.exit(1); }
  const buf = readFileSync(file);
  initial.set(rel, buf);
  const src = buf.toString('utf8');
  for (const m of src.matchAll(STATIC_IMPORT)) todo.push(posix.join(posix.dirname(rel), m[1]));
  for (const m of src.matchAll(DYNAMIC_IMPORT)) lazy.add(posix.join(posix.dirname(rel), m[1]));
}

let raw = 0, gz = 0;
console.log('Initial JavaScript (index.html entry, modulepreload, static imports):');
for (const [rel, buf] of [...initial].sort((a, b) => b[1].length - a[1].length)) {
  const g = gzipSize(buf);
  raw += buf.length; gz += g;
  console.log(`  ${rel.padEnd(44)} ${kb(buf.length).padStart(9)} kB   gzip ${kb(g).padStart(8)} kB`);
}
console.log(`  ${'TOTAL'.padEnd(44)} ${kb(raw).padStart(9)} kB   gzip ${kb(gz).padStart(8)} kB   (budget ${BUDGET_GZIP_KB} kB gzip)`);

const walk = (dir) => readdirSync(dir, { withFileTypes: true }).flatMap((e) => (e.isDirectory() ? walk(join(dir, e.name)) : [join(dir, e.name)]));
const big = walk(dist).map((f) => ({ rel: relative(dist, f).replaceAll('\\', '/'), bytes: statSync(f).size }))
  .filter((f) => f.bytes > BIG_ASSET_MB * 1e6).sort((a, b) => b.bytes - a.bytes);
console.log(`\nFiles over ${BIG_ASSET_MB} MB (none is part of the initial JavaScript unless marked):`);
for (const f of big) console.log(`  ${f.rel.padEnd(44)} ${(f.bytes / 1e6).toFixed(2).padStart(9)} MB${initial.has(f.rel) ? '   INITIAL' : ''}`);
if (!big.length) console.log('  none');

const lazyOnly = [...lazy].filter((rel) => !initial.has(rel)).sort();
console.log('\nChunks loaded on demand from the initial JavaScript (dynamic import):');
for (const rel of lazyOnly) console.log(`  ${rel.padEnd(44)} ${kb(statSync(join(dist, rel)).size).padStart(9)} kB`);
if (!lazyOnly.length) console.log('  none');

const failures = [];
if (gz > BUDGET_GZIP_KB * 1000) failures.push(`initial JavaScript is ${kb(gz)} kB gzip, over the ${BUDGET_GZIP_KB} kB budget`);
for (const rel of initial.keys()) {
  if (LAZY_ONLY.test(posix.basename(rel))) failures.push(`${rel} is in the initial JavaScript: it must stay behind a dynamic import or in the worker`);
}
// three.js and the frame generator must exist as chunks of their own (frame screen only).
const chunks = existsSync(join(dist, 'assets')) ? readdirSync(join(dist, 'assets')) : [];
for (const [name, re] of [['three.js', /^three[.-].*\.js$/], ['frame generator', /^frame-.*\.js$/]]) {
  if (!chunks.some((c) => re.test(c))) failures.push(`no separate chunk for ${name} in dist/assets`);
}
if (failures.length) {
  console.error('\nFAILED:\n' + failures.map((f) => '  ' + f).join('\n'));
  process.exit(1);
}
console.log('\nOK: initial JavaScript within budget; three.js, the frame generator and the vision code are separate chunks.');
