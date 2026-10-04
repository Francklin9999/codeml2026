import { OptiError, type LensMeasurement, type Pt } from '../contracts';
import { requireFinite } from './check';

const MARGIN = 10;
const BAR_MM = 50;
const TEXT_BLOCK = 28; // room under the box for bar and text lines
const n2 = (v: number) => (Math.round(v * 100) / 100).toFixed(2);
const n1 = (v: number) => v.toFixed(1);

function bounds(pts: Pt[]) {
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const [x, y] of pts) { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); }
  return { x0, y0, x1, y1 };
}

/** True-scale outline: user units are mm, the file prints at 100 %. */
export function contourToSvg(m: LensMeasurement): string {
  if (m.contourMm.length === 0) throw new OptiError('NO_LENS', 'export: non-finite or empty contour');
  requireFinite(m.contourMm.flat(), 'contour coordinate');
  requireFinite([m.A, m.B], 'A or B');
  const b = bounds(m.contourMm);
  const w = b.x1 - b.x0, h = b.y1 - b.y0;
  const W = Math.max(w + 2 * MARGIN, BAR_MM + 2 * MARGIN);
  const H = h + 2 * MARGIN + TEXT_BLOCK;
  const ox = MARGIN + (W - 2 * MARGIN - w) / 2; // centre the box when the bar is wider
  const oy = MARGIN;
  const d = m.contourMm.map(([x, y], i) => `${i ? 'L' : 'M'}${n2(x - b.x0 + ox)} ${n2(y - b.y0 + oy)}`).join(' ') + ' Z';
  const by = oy + h + 10; // bar y
  const bx = MARGIN;
  const eye = m.eye === 'L' ? 'Œil gauche' : 'Œil droit';
  const t = (y: number, s: string) => `<text x="${n2(MARGIN)}" y="${n2(y)}" font-family="sans-serif" font-size="3.5" fill="black">${s}</text>`;
  return [
    `<svg xmlns="http://www.w3.org/2000/svg" width="${n2(W)}mm" height="${n2(H)}mm" viewBox="0 0 ${n2(W)} ${n2(H)}">`,
    `<rect x="${n2(ox)}" y="${n2(oy)}" width="${n2(w)}" height="${n2(h)}" fill="none" stroke="black" stroke-width="0.1" stroke-dasharray="2 1"/>`,
    `<path d="${d}" fill="none" stroke="black" stroke-width="0.2"/>`,
    `<path id="scale-bar" d="M${n2(bx)} ${n2(by)} L${n2(bx + BAR_MM)} ${n2(by)} M${n2(bx)} ${n2(by - 1.5)} L${n2(bx)} ${n2(by + 1.5)} M${n2(bx + BAR_MM)} ${n2(by - 1.5)} L${n2(bx + BAR_MM)} ${n2(by + 1.5)}" fill="none" stroke="black" stroke-width="0.2"/>`,
    t(by + 6, '50 mm'),
    t(by + 11, 'Imprimer à 100 % (taille réelle)'),
    t(by + 15, `A = ${n1(m.A)} mm  B = ${n1(m.B)} mm`),
    t(by + 19, eye),
    '</svg>',
  ].join('\n');
}
