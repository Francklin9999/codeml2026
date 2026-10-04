import type { Pt } from '../contracts';

type Kid = Node | string | null | false | undefined;

/** Tiny element builder. Props starting with "on" are event listeners; the rest are attributes. */
export function h<K extends keyof HTMLElementTagNameMap>(
  tag: K, props: Record<string, string | number | boolean | EventListener | undefined> | null = null, ...kids: Kid[]
): HTMLElementTagNameMap[K] {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(props ?? {})) {
    if (v === undefined || v === false) continue;
    if (k.startsWith('on') && typeof v === 'function') el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v === true ? '' : String(v));
  }
  for (const kid of kids) if (kid) el.append(kid);
  return el;
}

/** French decimal comma, one decimal: 52,4 */
export const fmt1 = (x: number): string => x.toFixed(1).replace('.', ',');

/** Draws an ImageData scaled to the canvas width. Does nothing where there is no 2D canvas (jsdom). */
export function paintImage(canvas: HTMLCanvasElement, img: ImageData, maxWidth = 800): CanvasRenderingContext2D | null {
  const scale = Math.min(1, maxWidth / img.width);
  canvas.width = Math.max(1, Math.round(img.width * scale));
  canvas.height = Math.max(1, Math.round(img.height * scale));
  const ctx = canvas.getContext('2d');
  if (!ctx) return null;
  if (scale === 1) {
    ctx.putImageData(img, 0, 0);
  } else {
    const tmp = document.createElement('canvas');
    tmp.width = img.width;
    tmp.height = img.height;
    tmp.getContext('2d')?.putImageData(img, 0, 0);
    ctx.drawImage(tmp, 0, 0, canvas.width, canvas.height);
  }
  return ctx;
}

/** Strokes a closed polygon given in source pixels (scaled by canvas.width / srcWidth). */
export function strokePolygon(ctx: CanvasRenderingContext2D, poly: Pt[], k: number, colour: string, width: number): void {
  if (poly.length < 2) return;
  ctx.beginPath();
  poly.forEach(([x, y], i) => (i ? ctx.lineTo(x * k, y * k) : ctx.moveTo(x * k, y * k)));
  ctx.closePath();
  ctx.strokeStyle = colour;
  ctx.lineWidth = width;
  ctx.stroke();
}

export function canvasOf(label: string): HTMLCanvasElement {
  return h('canvas', { role: 'img', 'aria-label': label, class: 'pic' });
}

/** Grey image of a mask (lens white) as ImageData, for the step-by-step screen. */
export function maskImage(data: Uint8Array, width: number, height: number): ImageData {
  const px = new Uint8ClampedArray(width * height * 4);
  for (let i = 0; i < data.length; i++) {
    const v = data[i] ? 255 : 30;
    px[i * 4] = px[i * 4 + 1] = px[i * 4 + 2] = v;
    px[i * 4 + 3] = 255;
  }
  return new ImageData(px, width, height);
}
