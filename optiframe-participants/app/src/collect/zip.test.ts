import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { buildExportParts, ExportError } from './exporter';
import { MANIFEST_COLUMNS, type Meta } from './manifest';
import { MAX_PART_BYTES, buildZip, crc32, planParts } from './zip';

// ---- independent reader: written here, does not share code with zip.ts ----
function slowCrc(d: Uint8Array): number {
  let c = ~0;
  for (const b of d) {
    c ^= b;
    for (let k = 0; k < 8; k++) c = (c >>> 1) ^ (0xedb88320 & -(c & 1));
  }
  return ~c >>> 0;
}
interface Parsed { name: string; data: Uint8Array; crcOk: boolean; method: number }
function readZip(z: Uint8Array): Parsed[] {
  const dv = new DataView(z.buffer, z.byteOffset, z.byteLength);
  let e = z.length - 22;
  while (e >= 0 && dv.getUint32(e, true) !== 0x06054b50) e--;
  expect(e).toBeGreaterThanOrEqual(0);
  const n = dv.getUint16(e + 10, true);
  let p = dv.getUint32(e + 16, true);
  expect(dv.getUint32(e + 12, true)).toBe(e - p); // central directory size
  const out: Parsed[] = [];
  for (let i = 0; i < n; i++) {
    expect(dv.getUint32(p, true)).toBe(0x02014b50);
    const method = dv.getUint16(p + 10, true), crc = dv.getUint32(p + 16, true), csize = dv.getUint32(p + 20, true), usize = dv.getUint32(p + 24, true);
    const nl = dv.getUint16(p + 28, true), xl = dv.getUint16(p + 30, true), cl = dv.getUint16(p + 32, true), lo = dv.getUint32(p + 42, true);
    const name = new TextDecoder().decode(z.subarray(p + 46, p + 46 + nl));
    expect(dv.getUint32(lo, true)).toBe(0x04034b50);
    const lnl = dv.getUint16(lo + 26, true), lxl = dv.getUint16(lo + 28, true);
    expect(dv.getUint32(lo + 14, true)).toBe(crc);
    const start = lo + 30 + lnl + lxl;
    const data = z.subarray(start, start + csize);
    expect(csize).toBe(usize);
    out.push({ name, data, crcOk: slowCrc(data) === crc, method });
    p += 46 + nl + xl + cl;
  }
  return out;
}

describe('crc32', () => {
  it('matches the known check value and the bitwise version', () => {
    expect(crc32(new TextEncoder().encode('123456789'))).toBe(0xcbf43926);
    expect(crc32(new Uint8Array(0))).toBe(0);
    const d = Uint8Array.from({ length: 1000 }, (_, i) => (i * 37) & 255);
    expect(crc32(d)).toBe(slowCrc(d));
  });
});

describe('buildZip', () => {
  it('writes entries an independent parser reads back, sizes and CRC right, empty file included', () => {
    const a = Uint8Array.from({ length: 5000 }, (_, i) => (i * 7) & 255);
    const z = buildZip([{ name: 'photos/a.jpg', data: a }, { name: 'empty.txt', data: new Uint8Array(0) }, { name: 'é.csv', data: new TextEncoder().encode('x') }]);
    const r = readZip(z);
    expect(r.map((x) => x.name)).toEqual(['photos/a.jpg', 'empty.txt', 'é.csv']);
    expect(r.every((x) => x.crcOk && x.method === 0)).toBe(true);
    expect(Buffer.from(r[0].data).equals(Buffer.from(a))).toBe(true);
    expect(r[1].data.length).toBe(0);
  });
  it('refuses an empty list, backslashes and duplicate names', () => {
    expect(() => buildZip([])).toThrow();
    expect(() => buildZip([{ name: 'a\\b', data: new Uint8Array(1) }])).toThrow();
    expect(() => buildZip([{ name: 'a', data: new Uint8Array(1) }, { name: 'a', data: new Uint8Array(1) }])).toThrow();
  });
});

describe('planParts', () => {
  it('splits so that every part stays under the limit', () => {
    const items = Array.from({ length: 5 }, (_, i) => ({ name: `photos/${i}.jpg`, size: 20_000_000 }));
    const parts = planParts(items, MAX_PART_BYTES, 1000);
    expect(parts.map((p) => p.length)).toEqual([2, 2, 1]);
    expect(parts.flat()).toEqual([0, 1, 2, 3, 4]);
  });
  it('a 49 MB file fits one part alone; two 49 MB files make two parts; a 0 byte file costs only its headers', () => {
    expect(planParts([{ name: 'photos/a.jpg', size: 49_000_000 }])).toHaveLength(1);
    expect(planParts([{ name: 'photos/a.jpg', size: 49_000_000 }, { name: 'photos/b.jpg', size: 49_000_000 }])).toHaveLength(2);
    expect(planParts([{ name: 'photos/a.jpg', size: 0 }, { name: 'photos/b.jpg', size: 49_000_000 }])).toHaveLength(1);
  });
});

const meta = (i: number, bytes: number, o: Partial<Meta> = {}): Meta => ({
  name: `L0${i}_p_1.jpg`, mode: 'validation', lensId: `L0${i}`, phone: 'p', rep: 1, eye: 'R', A: [60, 60.1, 59.9], B: [48, 48, 48], notes: 'a, "b"\nc',
  takenAt: `2026-01-01T10:0${i}:00.000Z`, bytes, mime: 'image/jpeg', userAgent: 'UA, "x"', appVersion: '0.1.0', ok: true,
  measured: { A: 60.1, B: 48, perimeter: 190, method: 'classic', reprojErrMm: 0.1, sharpness: 0.001 }, ...o,
});
const jpegLike = (n: number, seed: number) => Uint8Array.from({ length: n }, (_, i) => (i * 31 + seed) & 255);
const sha = (b: Uint8Array) => createHash('sha256').update(b).digest('hex');

describe('buildExportParts', () => {
  it('refuses an empty export', async () => {
    await expect(buildExportParts([], async () => undefined)).rejects.toBeInstanceOf(ExportError);
  });
  it('builds one part with photos, manifest, own_lenses, results and LISEZMOI, bytes untouched', async () => {
    const files = new Map([['L01_p_1.jpg', jpegLike(3000, 1)], ['L02_p_1.jpg', jpegLike(0, 2)]]);
    const metas = [meta(1, 3000), meta(2, 0, { ok: false, measured: undefined, errorCode: 'NO_LENS' })];
    const parts = await buildExportParts(metas, async (n) => { const f = files.get(n)!; return f.buffer.slice(f.byteOffset, f.byteOffset + f.byteLength) as ArrayBuffer; });
    expect(parts).toHaveLength(1);
    const z = readZip(parts[0].data);
    expect(z.map((x) => x.name).sort()).toEqual(['LISEZMOI.txt', 'manifest.csv', 'own_lenses.csv', 'photos/L01_p_1.jpg', 'photos/L02_p_1.jpg', 'results.csv']);
    expect(z.every((x) => x.crcOk && !x.name.includes('\\'))).toBe(true);
    expect(sha(z.find((x) => x.name === 'photos/L01_p_1.jpg')!.data)).toBe(sha(files.get('L01_p_1.jpg')!));
    const readme = new TextDecoder().decode(z.find((x) => x.name === 'LISEZMOI.txt')!.data).trim().split('\n');
    expect(readme).toHaveLength(5);
    const manifest = new TextDecoder().decode(z.find((x) => x.name === 'manifest.csv')!.data);
    expect(manifest.split('\n')[0]).toBe(MANIFEST_COLUMNS.join(','));
  });
  it('splits a set into parts under 50 MB, every photo exactly once, each part with its own CSVs', async () => {
    const sizes = [30_000_000, 30_000_000, 100, 20_000_000];
    const metas = sizes.map((s, i) => meta(i + 1, s));
    const parts = await buildExportParts(metas, async (n) => new ArrayBuffer(sizes[Number(n[2]) - 1]));
    expect(parts.length).toBe(3);
    for (const p of parts) expect(p.data.length).toBeLessThanOrEqual(MAX_PART_BYTES);
    expect(parts.flatMap((p) => p.photoNames).sort()).toEqual(metas.map((m) => m.name).sort());
    expect(new Set(parts.map((p) => p.fileName)).size).toBe(3);
    for (const p of parts) expect(readZip(p.data).some((x) => x.name === 'manifest.csv')).toBe(true);
  });
  it('a ZIP produced here opens with Python zipfile, manifest.csv parses, photo bytes are identical', async () => {
    const orig = jpegLike(4096, 9);
    const m = meta(1, orig.length);
    const parts = await buildExportParts([m], async () => orig.buffer.slice(0) as ArrayBuffer);
    const dir = mkdtempSync(join(tmpdir(), 'optiframe-zip-'));
    try {
      const zipPath = join(dir, 'p.zip');
      writeFileSync(zipPath, parts[0].data);
      const script = join(dir, 'check.py');
      writeFileSync(script, [
        'import zipfile, csv, io, hashlib, json, sys',
        'z = zipfile.ZipFile(sys.argv[1])',
        'assert z.testzip() is None',
        'rows = list(csv.DictReader(io.TextIOWrapper(z.open("manifest.csv"), encoding="utf-8", newline="")))',
        'own = list(csv.DictReader(io.TextIOWrapper(z.open("own_lenses.csv"), encoding="utf-8", newline="")))',
        'print(json.dumps({"names": sorted(z.namelist()), "rows": rows, "own": own, "sha": hashlib.sha256(z.read("photos/L01_p_1.jpg")).hexdigest()}))',
      ].join('\n'));
      let out: string;
      try { out = execFileSync('python', [script, zipPath], { encoding: 'utf8' }); }
      catch (e) {
        if ((e as NodeJS.ErrnoException).code === 'ENOENT') return; // no Python on this machine: the independent parser above still checked the archive
        throw e;
      }
      const r = JSON.parse(out);
      expect(r.names).toContain('manifest.csv');
      expect(r.rows).toHaveLength(1);
      expect(r.rows[0].file).toBe('L01_p_1.jpg');
      expect(r.rows[0].notes).toBe('a, "b"\nc');
      expect(r.rows[0].user_agent).toBe('UA, "x"');
      expect(r.own[0].lensId).toBe('L01');
      expect(r.sha).toBe(sha(orig));
    } finally {
      rmSync(dir, { recursive: true, force: true });
    }
  }, 60_000); // spawns Python: slow under a loaded full-suite run
});
