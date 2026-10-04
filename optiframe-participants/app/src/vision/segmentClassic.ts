import { OptiError, type Mask, type Rectified } from '../contracts';

// Classical lens segmentation on the rectified grey image. Pure typed arrays (no OpenCV), so the
// same code runs in the worker and in Node tests. All sizes are in mm and converted with pxPerMm.

const FLAT_BLUR_RADIUS_MM = 8;
const BLACKHAT_DISC_MM = 1.5; // diameter, radius rounded down at half resolution (1.4 mm at 10 px/mm): wider than the 1 mm rim
const CLOSE_DISC_MM = 1; // diameter, applied at half resolution by closeGaps
const MIN_COMPONENT_MM2 = 5;
const AREA_MM2 = { min: 600, max: 4000 };
const WIDTH_MM = { min: 30, max: 75 };
const MIN_SOLIDITY = 0.9;
const GLARE_LEVEL = 250; // raw grey value counted as saturated
const GLARE_FRACTION = 0.05;
const MIN_PARTIAL_EXTENT_MM = 15; // a border-touching blob shorter than this is dust, not a cut lens

const FLAT_BG = 200; // flat-fielded background level (leaves headroom above the background)
const SHADOW_FRACTION = 0.8; // pixels darker than this share of the local mean are left out of the illumination estimate
const MIN_ILLUMINATION_WEIGHT = 0.05;
/** Minimum rim darkness, as a share of the local background. Below it the rim is indistinguishable
 *  from noise and the shot is refused (NO_LENS). Real-world value: TO MEASURE. */
export const MIN_RIM_CONTRAST = 0.1;
/** Rim contrast that maps to score 1. Real-world value: TO MEASURE. */
const RIM_CONTRAST_FULL = 0.5;

const px = (mm: number, ppm: number) => Math.max(1, Math.round(mm * ppm));

function toGrey(data: Uint8ClampedArray, n: number): Uint8Array {
  const g = new Uint8Array(n);
  for (let i = 0, j = 0; i < n; i++, j += 4) g[i] = (data[j] * 299 + data[j + 1] * 587 + data[j + 2] * 114 + 500) / 1000;
  return g;
}

/** Box blur of half-width r with the window clipped at the borders. */
function boxBlur(src: Float32Array, w: number, h: number, r: number): Float32Array {
  const tmp = new Float32Array(w * h);
  for (let y = 0; y < h; y++) {
    const o = y * w;
    let sum = 0;
    for (let x = 0; x <= Math.min(r, w - 1); x++) sum += src[o + x];
    for (let x = 0; x < w; x++) {
      const lo = Math.max(0, x - r), hi = Math.min(w - 1, x + r);
      tmp[o + x] = sum / (hi - lo + 1);
      if (x + r + 1 < w) sum += src[o + x + r + 1];
      if (x - r >= 0) sum -= src[o + x - r];
    }
  }
  const out = new Float32Array(w * h);
  for (let x = 0; x < w; x++) {
    let sum = 0;
    for (let y = 0; y <= Math.min(r, h - 1); y++) sum += tmp[y * w + x];
    for (let y = 0; y < h; y++) {
      const lo = Math.max(0, y - r), hi = Math.min(h - 1, y + r);
      out[y * w + x] = sum / (hi - lo + 1);
      if (y + r + 1 < h) sum += tmp[(y + r + 1) * w + x];
      if (y - r >= 0) sum -= tmp[(y - r) * w + x];
    }
  }
  return out;
}

/** Mean of k x k cells (partial cells at the right and bottom edges are averaged over what exists). */
function downsample(src: ArrayLike<number>, w: number, h: number, k: number): { data: Float32Array; w: number; h: number } {
  const cw = Math.ceil(w / k), ch = Math.ceil(h / k), data = new Float32Array(cw * ch);
  for (let cy = 0; cy < ch; cy++) {
    const y1 = Math.min(h, (cy + 1) * k);
    for (let cx = 0; cx < cw; cx++) {
      const x1 = Math.min(w, (cx + 1) * k);
      let sum = 0;
      for (let y = cy * k; y < y1; y++) for (let x = cx * k; x < x1; x++) sum += src[y * w + x];
      data[cy * cw + cx] = sum / ((y1 - cy * k) * (x1 - cx * k));
    }
  }
  return { data, w: cw, h: ch };
}

/** Bilinear upsampling of a coarse grid to w x h; cell centres sit at (c + 0.5) * k. */
function upsample(coarse: Float32Array, cw: number, ch: number, k: number, w: number, h: number): Float32Array {
  const out = new Float32Array(w * h);
  const xa = new Int32Array(w), xb = new Int32Array(w), tx = new Float32Array(w);
  for (let x = 0; x < w; x++) {
    const fx = Math.min(cw - 1, Math.max(0, (x + 0.5) / k - 0.5)), x0 = Math.floor(fx);
    xa[x] = x0; xb[x] = Math.min(cw - 1, x0 + 1); tx[x] = fx - x0;
  }
  for (let y = 0; y < h; y++) {
    const fy = Math.min(ch - 1, Math.max(0, (y + 0.5) / k - 0.5)), y0 = Math.floor(fy), ty = fy - y0;
    const ra = y0 * cw, rb = Math.min(ch - 1, y0 + 1) * cw;
    for (let x = 0; x < w; x++) {
      const t = tx[x];
      const top = coarse[ra + xa[x]] * (1 - t) + coarse[ra + xb[x]] * t;
      const bot = coarse[rb + xa[x]] * (1 - t) + coarse[rb + xb[x]] * t;
      out[y * w + x] = top * (1 - ty) + bot * ty;
    }
  }
  return out;
}

const ILLUMINATION_CELL_MM = 0.4; // the illumination is smooth: estimate it on cells this size

/** Divide by the illumination estimate. Dark pixels (rim, tinted lens) are masked out of the
 *  estimate on a second pass, otherwise a dark lens would be flattened away. */
function flatField(grey: Uint8Array, w: number, h: number, ppm: number): Uint8Array {
  const k = Math.max(1, Math.round(ILLUMINATION_CELL_MM * ppm));
  const c = downsample(grey, w, h, k), n = c.w * c.h;
  const r = Math.max(1, Math.round((FLAT_BLUR_RADIUS_MM * ppm) / k));
  const b1 = boxBlur(c.data, c.w, c.h, r);
  const wgt = new Float32Array(n), fw = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    const keep = c.data[i] >= SHADOW_FRACTION * b1[i] ? 1 : 0;
    wgt[i] = keep;
    fw[i] = keep * c.data[i];
  }
  const bw = boxBlur(wgt, c.w, c.h, r), bf = boxBlur(fw, c.w, c.h, r);
  const bg = new Float32Array(n);
  for (let i = 0; i < n; i++) bg[i] = bw[i] > MIN_ILLUMINATION_WEIGHT ? bf[i] / bw[i] : b1[i];
  const full = upsample(bg, c.w, c.h, k, w, h);
  const out = new Uint8Array(w * h);
  for (let i = 0; i < out.length; i++) {
    const v = (grey[i] / Math.max(full[i], 1)) * FLAT_BG;
    out[i] = v > 255 ? 255 : v < 0 ? 0 : v + 0.5;
  }
  return out;
}

function smooth3(src: Uint8Array, w: number, h: number): Uint8Array {
  const tmp = new Uint16Array(w * h), out = new Uint8Array(w * h);
  for (let y = 0; y < h; y++) {
    const o = y * w;
    for (let x = 0; x < w; x++) tmp[o + x] = src[o + Math.max(0, x - 1)] + src[o + x] + src[o + Math.min(w - 1, x + 1)];
  }
  for (let y = 0; y < h; y++) {
    const a = Math.max(0, y - 1) * w, b = y * w, c = Math.min(h - 1, y + 1) * w;
    for (let x = 0; x < w; x++) out[b + x] = (tmp[a + x] + tmp[b + x] + tmp[c + x]) / 9 + 0.5;
  }
  return out;
}

/** Horizontal sliding max/min of half-width hw (van Herk), neutral padding outside the image. */
function rowExtremum(src: Uint8Array, w: number, h: number, hw: number, isMax: boolean): Uint8Array {
  if (hw === 0) return src;
  const out = new Uint8Array(w * h), k = 2 * hw + 1, n = w + 2 * hw, neutral = isMax ? 0 : 255;
  const line = new Uint8Array(n).fill(neutral), g = new Uint8Array(n), s = new Uint8Array(n);
  for (let y = 0; y < h; y++) {
    line.set(src.subarray(y * w, y * w + w), hw);
    let c = 0;
    if (isMax) {
      for (let i = 0; i < n; i++) { g[i] = c === 0 || line[i] > g[i - 1] ? line[i] : g[i - 1]; if (++c === k) c = 0; }
      c = n % k;
      for (let i = n - 1; i >= 0; i--) { s[i] = i === n - 1 || c === 0 || line[i] > s[i + 1] ? line[i] : s[i + 1]; c = c === 0 ? k - 1 : c - 1; }
      for (let x = 0; x < w; x++) out[y * w + x] = s[x] > g[x + k - 1] ? s[x] : g[x + k - 1];
    } else {
      for (let i = 0; i < n; i++) { g[i] = c === 0 || line[i] < g[i - 1] ? line[i] : g[i - 1]; if (++c === k) c = 0; }
      c = n % k;
      for (let i = n - 1; i >= 0; i--) { s[i] = i === n - 1 || c === 0 || line[i] < s[i + 1] ? line[i] : s[i + 1]; c = c === 0 ? k - 1 : c - 1; }
      for (let x = 0; x < w; x++) out[y * w + x] = s[x] < g[x + k - 1] ? s[x] : g[x + k - 1];
    }
  }
  return out;
}

/** Grey dilation (isMax) or erosion with a disc of radius r px, as a union of horizontal runs. */
function discMorph(src: Uint8Array, w: number, h: number, r: number, isMax: boolean): Uint8Array {
  const out = new Uint8Array(src);
  const runs = new Map<number, Uint8Array>();
  for (let dy = -r; dy <= r; dy++) {
    const hw = Math.floor(Math.sqrt(r * r - dy * dy));
    let run = runs.get(hw);
    if (!run) runs.set(hw, (run = rowExtremum(src, w, h, hw, isMax)));
    const y0 = Math.max(0, -dy), y1 = Math.min(h, h - dy);
    for (let y = y0; y < y1; y++) {
      const a = y * w, b = (y + dy) * w;
      if (isMax) for (let x = 0; x < w; x++) { if (run[b + x] > out[a + x]) out[a + x] = run[b + x]; }
      else for (let x = 0; x < w; x++) { if (run[b + x] < out[a + x]) out[a + x] = run[b + x]; }
    }
  }
  return out;
}

const close = (src: Uint8Array, w: number, h: number, r: number) =>
  discMorph(discMorph(src, w, h, r, true), w, h, r, false);

/** Binary (0/1) dilation with a disc of radius r px: per-row runs through running counts, combined
 *  four pixels at a time. Outside the image counts as 0. */
function binDilate(src: Uint8Array, w: number, h: number, r: number): Uint8Array {
  const stride = (w + 3) & ~3; // rows padded to whole 32-bit words
  const hws: number[] = [];
  for (let dy = 0; dy <= r; dy++) {
    const hw = Math.floor(Math.sqrt(r * r - dy * dy));
    if (!hws.includes(hw)) hws.push(hw);
  }
  const runs = new Map<number, Uint8Array>(hws.map((hw) => [hw, new Uint8Array(stride * h)]));
  const cum = new Int32Array(w + 1);
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) cum[x + 1] = cum[x] + src[y * w + x];
    for (const hw of hws) {
      const run = runs.get(hw)!, o = y * stride;
      for (let x = 0; x < w; x++) {
        const hi = x + hw + 1 > w ? w : x + hw + 1, lo = x - hw < 0 ? 0 : x - hw;
        run[o + x] = cum[hi] > cum[lo] ? 1 : 0;
      }
    }
  }
  const out32 = new Uint32Array((stride * h) / 4);
  const wordsPerRow = stride / 4;
  for (let dy = -r; dy <= r; dy++) {
    const run32 = new Uint32Array(runs.get(Math.floor(Math.sqrt(r * r - dy * dy)))!.buffer);
    const y0 = Math.max(0, -dy), y1 = Math.min(h, h - dy);
    for (let y = y0; y < y1; y++) {
      const a = y * wordsPerRow, b = (y + dy) * wordsPerRow;
      for (let i = 0; i < wordsPerRow; i++) out32[a + i] |= run32[b + i];
    }
  }
  const outB = new Uint8Array(out32.buffer), out = new Uint8Array(w * h);
  for (let y = 0; y < h; y++) out.set(outB.subarray(y * stride, y * stride + w), y * w);
  return out;
}

/** Binary erosion; outside the image counts as 1 so shapes touching the border are not eaten. */
function binErode(src: Uint8Array, w: number, h: number, r: number): Uint8Array {
  const inv = new Uint8Array(src.length);
  for (let i = 0; i < inv.length; i++) inv[i] = 1 - src[i];
  const d = binDilate(inv, w, h, r);
  for (let i = 0; i < d.length; i++) d[i] = 1 - d[i];
  return d;
}

/** Rim map: black-hat (thin dark structures, on a half-resolution copy: it is a smooth blob
 *  response) plus gradient magnitude on the dark side of each edge (full resolution). */
function rimMap(flat: Uint8Array, w: number, h: number, ppm: number): Uint8Array {
  const half = downsample(flat, w, h, 2);
  const hs = new Uint8Array(half.data.length);
  for (let i = 0; i < hs.length; i++) hs[i] = half.data[i] + 0.5;
  const closed = close(hs, half.w, half.h, Math.max(1, Math.floor((BLACKHAT_DISC_MM * ppm) / 4)));
  const bh = new Float32Array(hs.length);
  for (let i = 0; i < bh.length; i++) bh[i] = closed[i] - hs[i];
  const full = upsample(bh, half.w, half.h, 2, w, h);

  const s = smooth3(flat, w, h);
  const e = new Uint8Array(w * h);
  for (let i = 0; i < e.length; i++) e[i] = full[i] + 0.5;
  for (let y = 1; y < h - 1; y++) {
    for (let x = 1; x < w - 1; x++) {
      const i = y * w + x;
      // flat areas have no gradient worth computing
      const d1 = s[i + 1] - s[i - 1], d2 = s[i + w] - s[i - w];
      if (d1 < 3 && d1 > -3 && d2 < 3 && d2 > -3) continue;
      const gx = s[i - w + 1] + 2 * s[i + 1] + s[i + w + 1] - s[i - w - 1] - 2 * s[i - 1] - s[i + w - 1];
      const gy = s[i + w - 1] + 2 * s[i + w] + s[i + w + 1] - s[i - w - 1] - 2 * s[i - w] - s[i - w + 1];
      const g = ((gx < 0 ? -gx : gx) + (gy < 0 ? -gy : gy)) >> 2; // about the step height
      if (s[i] + g / 2 <= FLAT_BG) e[i] = Math.min(255, e[i] + g);
    }
  }
  return e;
}

function otsu(values: Uint8Array): number {
  const hist = new Float64Array(256);
  for (let i = 0; i < values.length; i++) hist[values[i]]++;
  let total = values.length, sumAll = 0;
  for (let t = 0; t < 256; t++) sumAll += t * hist[t];
  let wB = 0, sumB = 0, best = -1, bestT = 0;
  for (let t = 0; t < 256; t++) {
    wB += hist[t];
    if (wB === 0) continue;
    const wF = total - wB;
    if (wF === 0) break;
    sumB += t * hist[t];
    const d = sumB / wB - (sumAll - sumB) / wF;
    const v = wB * wF * d * d;
    if (v > best) { best = v; bestT = t; }
  }
  return bestT;
}

interface Comps { labels: Int32Array; area: number[]; minX: number[]; maxX: number[]; minY: number[]; maxY: number[] }

/** 8-connected components; label 0 is background. Index 0 of the stat arrays is unused. */
function components(bin: Uint8Array, w: number, h: number): Comps {
  const labels = new Int32Array(w * h), stack = new Int32Array(w * h);
  const c: Comps = { labels, area: [0], minX: [0], maxX: [0], minY: [0], maxY: [0] };
  for (let start = 0; start < bin.length; start++) {
    if (!bin[start] || labels[start]) continue;
    const id = c.area.length;
    let sp = 0, area = 0, minX = w, maxX = 0, minY = h, maxY = 0;
    stack[sp++] = start;
    labels[start] = id;
    while (sp) {
      const p = stack[--sp], x = p % w, y = (p - x) / w;
      area++;
      if (x < minX) minX = x;
      if (x > maxX) maxX = x;
      if (y < minY) minY = y;
      if (y > maxY) maxY = y;
      for (let dy = -1; dy <= 1; dy++) {
        const yy = y + dy;
        if (yy < 0 || yy >= h) continue;
        for (let dx = -1; dx <= 1; dx++) {
          const xx = x + dx;
          if (xx < 0 || xx >= w) continue;
          const q = yy * w + xx;
          if (bin[q] && !labels[q]) { labels[q] = id; stack[sp++] = q; }
        }
      }
    }
    c.area.push(area); c.minX.push(minX); c.maxX.push(maxX); c.minY.push(minY); c.maxY.push(maxY);
  }
  return c;
}

function dropSmall(bin: Uint8Array, w: number, h: number, minPx: number): Uint8Array {
  const c = components(bin, w, h), out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) if (bin[i] && c.area[c.labels[i]] >= minPx) out[i] = 1;
  return out;
}

/** Everything the border cannot reach (4-connected flood through non-rim pixels) is lens. */
function fillHoles(rim: Uint8Array, w: number, h: number): Uint8Array {
  const reached = new Uint8Array(w * h), stack = new Int32Array(w * h);
  let sp = 0;
  const seed = (p: number) => { if (!rim[p] && !reached[p]) { reached[p] = 1; stack[sp++] = p; } };
  for (let x = 0; x < w; x++) { seed(x); seed((h - 1) * w + x); }
  for (let y = 0; y < h; y++) { seed(y * w); seed(y * w + w - 1); }
  while (sp) {
    const p = stack[--sp], x = p % w;
    if (x > 0) seed(p - 1);
    if (x < w - 1) seed(p + 1);
    if (p >= w) seed(p - w);
    if (p < w * (h - 1)) seed(p + w);
  }
  const out = new Uint8Array(w * h);
  for (let i = 0; i < out.length; i++) out[i] = reached[i] ? 0 : 1;
  return out;
}

interface Blob { mask: Uint8Array; area: number; minX: number; maxX: number; minY: number; maxY: number }

function largestBlob(bin: Uint8Array, w: number, h: number): Blob | null {
  const c = components(bin, w, h);
  let best = 0;
  for (let i = 1; i < c.area.length; i++) if (c.area[i] > c.area[best]) best = i;
  if (best === 0) return null;
  const mask = new Uint8Array(w * h);
  for (let i = 0; i < mask.length; i++) if (c.labels[i] === best) mask[i] = 1;
  return { mask, area: c.area[best], minX: c.minX[best], maxX: c.maxX[best], minY: c.minY[best], maxY: c.maxY[best] };
}

/** Area over convex hull area, hull taken on pixel corners so a full rectangle gives exactly 1. */
function solidity(b: Blob, w: number, h: number): number {
  const pts: [number, number][] = [];
  for (let y = b.minY; y <= b.maxY; y++) {
    let lo = -1, hi = -1;
    for (let x = b.minX; x <= b.maxX; x++) if (b.mask[y * w + x]) { if (lo < 0) lo = x; hi = x; }
    if (lo >= 0) pts.push([lo, y], [lo, y + 1], [hi + 1, y], [hi + 1, y + 1]);
  }
  pts.sort((p, q) => p[0] - q[0] || p[1] - q[1]);
  const cross = (o: number[], a: number[], p: number[]) => (a[0] - o[0]) * (p[1] - o[1]) - (a[1] - o[1]) * (p[0] - o[0]);
  const half = (seq: [number, number][]) => {
    const st: [number, number][] = [];
    for (const p of seq) {
      while (st.length >= 2 && cross(st[st.length - 2], st[st.length - 1], p) <= 0) st.pop();
      st.push(p);
    }
    st.pop();
    return st;
  };
  const hull = half(pts).concat(half(pts.slice().reverse()));
  let a2 = 0;
  for (let i = 0; i < hull.length; i++) {
    const p = hull[i], q = hull[(i + 1) % hull.length];
    a2 += p[0] * q[1] - q[0] * p[1];
  }
  const hullArea = Math.abs(a2) / 2;
  return hullArea > 0 ? b.area / hullArea : 0;
}

interface Box { x0: number; y0: number; cw: number; ch: number }

/** Bounding box grown by a margin and clipped to the image. */
function boxAround(minX: number, maxX: number, minY: number, maxY: number, margin: number, w: number, h: number): Box {
  const x0 = Math.max(0, minX - margin), y0 = Math.max(0, minY - margin);
  return { x0, y0, cw: Math.min(w, maxX + 1 + margin) - x0, ch: Math.min(h, maxY + 1 + margin) - y0 };
}

function crop(src: Uint8Array, w: number, b: Box): Uint8Array {
  const out = new Uint8Array(b.cw * b.ch);
  for (let y = 0; y < b.ch; y++) out.set(src.subarray((b.y0 + y) * w + b.x0, (b.y0 + y) * w + b.x0 + b.cw), y * b.cw);
  return out;
}

/** Share by which the outer 1 mm of the mask is darker than the flat-field background. The band is
 *  found on a half-resolution copy: its exact width does not matter for a mean. */
function rimContrast(b: Blob, flat: Uint8Array, w: number, h: number, ppm: number): number {
  const r = px(1, ppm), box = boxAround(b.minX, b.maxX, b.minY, b.maxY, r + 2, w, h);
  const sub = crop(b.mask, w, box);
  const hw = (box.cw + 1) >> 1, hh = (box.ch + 1) >> 1, small = new Uint8Array(hw * hh);
  for (let y = 0; y < hh; y++) for (let x = 0; x < hw; x++) small[y * hw + x] = sub[2 * y * box.cw + 2 * x];
  const inner = binErode(small, hw, hh, Math.max(1, r >> 1));
  let sum = 0, n = 0;
  for (let y = 0; y < box.ch; y++) {
    for (let x = 0; x < box.cw; x++) {
      if (sub[y * box.cw + x] && !inner[(y >> 1) * hw + (x >> 1)]) { sum += flat[(box.y0 + y) * w + box.x0 + x]; n++; }
    }
  }
  return n ? Math.max(0, 1 - sum / n / FLAT_BG) : 0;
}

/** Closing with a 1 mm disc, computed on a half-resolution copy and added to the rim only where the
 *  rim has no pixel of its own: it bridges gaps but never moves the outer edge of the rim. */
function closeGaps(rim: Uint8Array, w: number, h: number, ppm: number): Uint8Array {
  const hw = (w + 1) >> 1, hh = (h + 1) >> 1, small = new Uint8Array(hw * hh);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) if (rim[y * w + x]) small[(y >> 1) * hw + (x >> 1)] = 1;
  const r = Math.max(1, Math.floor((CLOSE_DISC_MM * ppm) / 4));
  const closed = binErode(binDilate(small, hw, hh, r), hw, hh, r);
  const out = new Uint8Array(rim);
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const c = (y >> 1) * hw + (x >> 1);
      if (closed[c] && !small[c]) out[y * w + x] = 1;
    }
  }
  return out;
}

/** Rim pixels -> solid lens blob: drop specks, close gaps, fill, keep the largest. The work is done
 *  on the bounding box of what is left, since the lens only fills part of the window. */
function lensFromRim(rim: Uint8Array, w: number, h: number, ppm: number): Blob | null {
  const clean = dropSmall(rim, w, h, Math.round(MIN_COMPONENT_MM2 * ppm * ppm));
  let minX = w, maxX = -1, minY = h, maxY = -1;
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      if (!clean[y * w + x]) continue;
      if (x < minX) minX = x;
      if (x > maxX) maxX = x;
      if (y < minY) minY = y;
      maxY = y;
    }
  }
  if (maxX < 0) return null;
  const box = boxAround(minX, maxX, minY, maxY, px(CLOSE_DISC_MM, ppm) + 2, w, h);
  const closed = closeGaps(crop(clean, w, box), box.cw, box.ch, ppm);
  const b = largestBlob(fillHoles(closed, box.cw, box.ch), box.cw, box.ch);
  if (!b) return null;
  const mask = new Uint8Array(w * h);
  for (let y = 0; y < box.ch; y++) mask.set(b.mask.subarray(y * box.cw, (y + 1) * box.cw), (box.y0 + y) * w + box.x0);
  return { mask, area: b.area, minX: b.minX + box.x0, maxX: b.maxX + box.x0, minY: b.minY + box.y0, maxY: b.maxY + box.y0 };
}

type Verdict = { kind: 'ok'; mask: Mask } | { kind: 'out' } | { kind: 'none' };

function judge(b: Blob | null, grey: Uint8Array, flat: Uint8Array, w: number, h: number, ppm: number): Verdict {
  if (!b) return { kind: 'none' };
  const contrast = rimContrast(b, flat, w, h, ppm);
  if (contrast < MIN_RIM_CONTRAST) return { kind: 'none' };
  const bw = (b.maxX - b.minX + 1) / ppm, bh = (b.maxY - b.minY + 1) / ppm;
  const touches = b.minX === 0 || b.minY === 0 || b.maxX === w - 1 || b.maxY === h - 1;
  if (touches) return Math.max(bw, bh) >= MIN_PARTIAL_EXTENT_MM ? { kind: 'out' } : { kind: 'none' };
  const area = b.area / (ppm * ppm);
  if (area < AREA_MM2.min || area > AREA_MM2.max || bw < WIDTH_MM.min || bw > WIDTH_MM.max) return { kind: 'none' };
  if (solidity(b, w, h) <= MIN_SOLIDITY) return { kind: 'none' };
  let sat = 0;
  for (let y = b.minY; y <= b.maxY; y++) for (let x = b.minX; x <= b.maxX; x++) if (b.mask[y * w + x] && grey[y * w + x] >= GLARE_LEVEL) sat++;
  if (sat > GLARE_FRACTION * b.area) throw new OptiError('GLARE', `${((100 * sat) / b.area).toFixed(1)} % saturated`);
  return { kind: 'ok', mask: { data: b.mask, width: w, height: h, method: 'classic', score: Math.min(1, contrast / RIM_CONTRAST_FULL) } };
}

/** Tinted lens: the flat-fielded image itself is darker than the background. */
function darkRegion(flat: Uint8Array, w: number, h: number): Uint8Array {
  const s = smooth3(flat, w, h), t = otsu(s), out = new Uint8Array(w * h);
  let sumD = 0, nD = 0, sumB = 0, nB = 0;
  for (let i = 0; i < s.length; i++) { if (s[i] <= t) { sumD += s[i]; nD++; } else { sumB += s[i]; nB++; } }
  if (!nD || !nB || (sumB / nB - sumD / nD) / FLAT_BG < MIN_RIM_CONTRAST) return out;
  for (let i = 0; i < s.length; i++) if (s[i] <= t) out[i] = 1;
  return out;
}

function run(r: Rectified): Mask {
  const { width: w, height: h } = r.image;
  const ppm = r.pxPerMm;
  if (!(ppm > 0) || r.image.data.length !== w * h * 4) throw new OptiError('LOAD_FAILED', 'bad rectified image');
  const grey = toGrey(r.image.data, w * h);
  const flat = flatField(grey, w, h, ppm);

  const e = rimMap(flat, w, h, ppm);
  const floor = (MIN_RIM_CONTRAST * FLAT_BG) / 2;
  const thr = Math.max(otsu(e), floor);
  const rim = new Uint8Array(w * h);
  for (let i = 0; i < rim.length; i++) if (e[i] > thr) rim[i] = 1;

  let sawOut = false;
  const first = judge(lensFromRim(rim, w, h, ppm), grey, flat, w, h, ppm);
  if (first.kind === 'ok') return first.mask;
  if (first.kind === 'out') sawOut = true;

  const second = judge(lensFromRim(darkRegion(flat, w, h), w, h, ppm), grey, flat, w, h, ppm);
  if (second.kind === 'ok') return second.mask;
  if (second.kind === 'out') sawOut = true;

  throw sawOut
    ? new OptiError('LENS_OUT_OF_WINDOW', 'lens touches the window border')
    : new OptiError('NO_LENS', 'no plausible lens outline');
}

export function segmentClassic(r: Rectified): Mask {
  try {
    return run(r);
  } catch (err) {
    if (err instanceof OptiError) throw err;
    throw new OptiError('LOAD_FAILED', err instanceof Error ? err.message : String(err));
  }
}
