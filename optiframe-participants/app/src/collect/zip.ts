// STORE-only ZIP writer: no compression, no dependency. Local headers, central directory, end record.
// No ZIP64: a part is at most 50 MB.

export const MAX_PART_BYTES = 50 * 1000 * 1000;

export interface ZipEntry { name: string; data: Uint8Array }

let TABLE: Uint32Array | null = null;
export function crc32(data: Uint8Array): number {
  if (!TABLE) {
    TABLE = new Uint32Array(256);
    for (let n = 0; n < 256; n++) {
      let c = n;
      for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
      TABLE[n] = c >>> 0;
    }
  }
  let c = 0xffffffff;
  for (let i = 0; i < data.length; i++) c = TABLE[(c ^ data[i]) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

const enc = new TextEncoder();

/** Bytes a stored entry adds besides its data: local header + central record (the name appears in both). */
export function entryOverhead(name: string): number {
  return 30 + 46 + 2 * enc.encode(name).length;
}

function dosDateTime(d: Date): { time: number; date: number } {
  const y = Math.max(1980, d.getFullYear());
  return { time: (d.getHours() << 11) | (d.getMinutes() << 5) | (d.getSeconds() >> 1), date: ((y - 1980) << 9) | ((d.getMonth() + 1) << 5) | d.getDate() };
}

export function buildZip(entries: ZipEntry[], when: Date = new Date()): Uint8Array {
  if (!entries.length) throw new Error('ZIP vide');
  const seen = new Set<string>();
  const files = entries.map((e) => {
    if (e.name.includes('\\') || e.name.startsWith('/')) throw new Error(`Nom invalide dans le ZIP : ${e.name}`);
    if (seen.has(e.name)) throw new Error(`Nom en double dans le ZIP : ${e.name}`);
    seen.add(e.name);
    return { name: enc.encode(e.name), data: e.data, crc: crc32(e.data) };
  });
  if (files.length > 0xffff) throw new Error('Trop de fichiers pour un ZIP');
  const total = files.reduce((s, f) => s + 30 + f.name.length + f.data.length + 46 + f.name.length, 22);
  if (total > 0xffffffff) throw new Error('ZIP trop gros');
  const out = new Uint8Array(total);
  const dv = new DataView(out.buffer);
  const { time, date } = dosDateTime(when);
  let p = 0;
  const offsets: number[] = [];
  for (const f of files) {
    offsets.push(p);
    dv.setUint32(p, 0x04034b50, true);
    dv.setUint16(p + 4, 20, true);
    dv.setUint16(p + 6, 0x0800, true); // UTF-8 names
    dv.setUint16(p + 8, 0, true); // stored
    dv.setUint16(p + 10, time, true);
    dv.setUint16(p + 12, date, true);
    dv.setUint32(p + 14, f.crc, true);
    dv.setUint32(p + 18, f.data.length, true);
    dv.setUint32(p + 22, f.data.length, true);
    dv.setUint16(p + 26, f.name.length, true);
    dv.setUint16(p + 28, 0, true);
    out.set(f.name, p + 30);
    out.set(f.data, p + 30 + f.name.length);
    p += 30 + f.name.length + f.data.length;
  }
  const cdStart = p;
  files.forEach((f, i) => {
    dv.setUint32(p, 0x02014b50, true);
    dv.setUint16(p + 4, 20, true);
    dv.setUint16(p + 6, 20, true);
    dv.setUint16(p + 8, 0x0800, true);
    dv.setUint16(p + 10, 0, true);
    dv.setUint16(p + 12, time, true);
    dv.setUint16(p + 14, date, true);
    dv.setUint32(p + 16, f.crc, true);
    dv.setUint32(p + 20, f.data.length, true);
    dv.setUint32(p + 24, f.data.length, true);
    dv.setUint16(p + 28, f.name.length, true);
    dv.setUint32(p + 42, offsets[i], true);
    out.set(f.name, p + 46);
    p += 46 + f.name.length;
  });
  dv.setUint32(p, 0x06054b50, true);
  dv.setUint16(p + 8, files.length, true);
  dv.setUint16(p + 10, files.length, true);
  dv.setUint32(p + 12, p - cdStart, true);
  dv.setUint32(p + 16, cdStart, true);
  return out;
}

/** Greedy split into groups whose archive stays under `limit`. `fixed` = bytes every part spends on its non-photo files.
 *  A single item larger than the room left still gets a part of its own (it cannot be cut). */
export function planParts(items: { name: string; size: number }[], limit = MAX_PART_BYTES, fixed = 0): number[][] {
  const parts: number[][] = [];
  let cur: number[] = [];
  let used = fixed + 22;
  items.forEach((it, i) => {
    const cost = it.size + entryOverhead(it.name);
    if (cur.length && used + cost > limit) {
      parts.push(cur);
      cur = [];
      used = fixed + 22;
    }
    cur.push(i);
    used += cost;
  });
  if (cur.length) parts.push(cur);
  return parts;
}
