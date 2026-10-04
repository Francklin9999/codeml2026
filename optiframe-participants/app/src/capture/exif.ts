// Minimal JPEG/EXIF reader: orientation (0x0112), FocalLengthIn35mmFilm (0xA405) and the raw pixel size.
// Never throws: any malformed input gives the defaults (orientation 1).
export interface ExifInfo { orientation: number; focal35mm?: number; width?: number; height?: number }

export function parseExif(b: Uint8Array): ExifInfo {
  const out: ExifInfo = { orientation: 1 };
  try {
    if (b.length < 4 || b[0] !== 0xff || b[1] !== 0xd8) return out;
    let p = 2;
    while (p + 4 <= b.length) {
      if (b[p] !== 0xff) { p++; continue; }
      const marker = b[p + 1];
      if (marker === 0xff) { p++; continue; }
      if (marker === 0xd8 || marker === 0x01 || (marker >= 0xd0 && marker <= 0xd7)) { p += 2; continue; }
      if (marker === 0xda || marker === 0xd9) break;
      const len = (b[p + 2] << 8) | b[p + 3];
      if (len < 2) break;
      const seg = p + 4;
      if (marker === 0xe1 && isExifHeader(b, seg)) readTiff(b, seg + 6, Math.min(b.length, p + 2 + len), out);
      else if (marker >= 0xc0 && marker <= 0xcf && marker !== 0xc4 && marker !== 0xc8 && marker !== 0xcc && seg + 5 <= b.length) {
        out.height = (b[seg + 1] << 8) | b[seg + 2];
        out.width = (b[seg + 3] << 8) | b[seg + 4];
      }
      p += 2 + len;
    }
  } catch { /* keep what was read */ }
  return out;
}

function isExifHeader(b: Uint8Array, at: number): boolean {
  return b[at] === 0x45 && b[at + 1] === 0x78 && b[at + 2] === 0x69 && b[at + 3] === 0x66 && b[at + 4] === 0 && b[at + 5] === 0;
}

function readTiff(b: Uint8Array, t: number, end: number, out: ExifInfo): void {
  const le = b[t] === 0x49 && b[t + 1] === 0x49;
  if (!le && !(b[t] === 0x4d && b[t + 1] === 0x4d)) return;
  const u16 = (o: number) => { if (o + 2 > end) throw new RangeError('exif'); return le ? b[o] | (b[o + 1] << 8) : (b[o] << 8) | b[o + 1]; };
  const u32 = (o: number) => {
    if (o + 4 > end) throw new RangeError('exif');
    return le ? (b[o] | (b[o + 1] << 8) | (b[o + 2] << 16) | (b[o + 3] << 24)) >>> 0
      : ((b[o] << 24) | (b[o + 1] << 16) | (b[o + 2] << 8) | b[o + 3]) >>> 0;
  };
  if (u16(t + 2) !== 42) return;
  // A SHORT value sits in the first two bytes of the 4-byte value field.
  const walk = (ifd: number, visit: (tag: number, type: number, valueAt: number) => void) => {
    const n = u16(ifd);
    for (let i = 0; i < n; i++) { const e = ifd + 2 + i * 12; visit(u16(e), u16(e + 2), e + 8); }
  };
  let exifIfd = 0;
  walk(t + u32(t + 4), (tag, type, v) => {
    if (tag === 0x0112 && type === 3) { const o = u16(v); if (o >= 1 && o <= 8) out.orientation = o; }
    else if (tag === 0x8769) exifIfd = u32(v);
  });
  if (exifIfd) {
    walk(t + exifIfd, (tag, type, v) => {
      if (tag === 0xa405 && type === 3) { const f = u16(v); if (f > 0) out.focal35mm = f; }
    });
  }
}
