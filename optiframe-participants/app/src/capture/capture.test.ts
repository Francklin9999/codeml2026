import { describe, expect, it } from 'vitest';
import { OptiError } from '../contracts';
import { capturePhoto, pickFile, type CaptureEnv } from './index';
import { parseExif } from './exif';
import { fitSize, orientationMatrix } from './geometry';

// ---- hand-built JPEG header -------------------------------------------------------------
function jpeg(opts: { orientation?: number; focal?: number; le?: boolean; w?: number; h?: number }): Uint8Array {
  const le = opts.le ?? true;
  const u16 = (v: number) => (le ? [v & 255, v >> 8] : [v >> 8, v & 255]);
  const u32 = (v: number) => (le ? [v & 255, (v >> 8) & 255, (v >> 16) & 255, v >>> 24] : [v >>> 24, (v >> 16) & 255, (v >> 8) & 255, v & 255]);
  const entry = (tag: number, type: number, val: number) => [...u16(tag), ...u16(type), ...u32(1), ...u16(val), 0, 0];
  const ifd0: number[][] = [];
  if (opts.orientation !== undefined) ifd0.push(entry(0x0112, 3, opts.orientation));
  const ifd0Len = 2 + (ifd0.length + (opts.focal !== undefined ? 1 : 0)) * 12 + 4;
  if (opts.focal !== undefined) ifd0.push([...u16(0x8769), ...u16(4), ...u32(1), ...u32(8 + ifd0Len)]);
  const tiff = [...(le ? [0x49, 0x49] : [0x4d, 0x4d]), ...u16(42), ...u32(8), ...u16(ifd0.length), ...ifd0.flat(), ...u32(0)];
  if (opts.focal !== undefined) tiff.push(...u16(1), ...entry(0xa405, 3, opts.focal), ...u32(0));
  const body = [0x45, 0x78, 0x69, 0x66, 0, 0, ...tiff];
  const app1 = [0xff, 0xe1, ...[(body.length + 2) >> 8, (body.length + 2) & 255], ...body];
  const w = opts.w ?? 4000, h = opts.h ?? 3000;
  const sof = [0xff, 0xc0, 0, 11, 8, h >> 8, h & 255, w >> 8, w & 255, 1, 1, 0x11, 0];
  return Uint8Array.from([0xff, 0xd8, ...app1, ...sof, 0xff, 0xd9]);
}

describe('parseExif', () => {
  for (const le of [true, false]) {
    for (const o of [1, 3, 6, 8]) {
      it(`orientation ${o} (${le ? 'II' : 'MM'})`, () => {
        expect(parseExif(jpeg({ orientation: o, le })).orientation).toBe(o);
      });
    }
  }
  it('reads the focal length in 35 mm when present', () => {
    const r = parseExif(jpeg({ orientation: 6, focal: 26 }));
    expect(r.focal35mm).toBe(26);
    expect(r.orientation).toBe(6);
  });
  it('leaves focal undefined when absent', () => {
    expect(parseExif(jpeg({ orientation: 1 })).focal35mm).toBeUndefined();
  });
  it('reads the raw size from the SOF marker', () => {
    const r = parseExif(jpeg({ w: 4032, h: 3024 }));
    expect([r.width, r.height]).toEqual([4032, 3024]);
  });
  it('defaults on garbage and truncation without throwing', () => {
    expect(parseExif(new Uint8Array([1, 2, 3])).orientation).toBe(1);
    const j = jpeg({ orientation: 6, focal: 26 });
    expect(parseExif(j.slice(0, 20)).orientation).toBeGreaterThan(0);
  });
});

describe('downscale rule', () => {
  it('keeps 4032x3024', () => expect(fitSize(4032, 3024)).toEqual({ w: 4032, h: 3024 }));
  it('reduces 8000x6000 and keeps the aspect ratio', () => {
    const { w, h } = fitSize(8000, 6000);
    expect(Math.max(w, h)).toBeLessThanOrEqual(4096);
    expect(w * h).toBeLessThanOrEqual(16_000_000);
    expect(w / h).toBeCloseTo(4 / 3, 3);
  });
  it('caps the area even when the long side is below 4096', () => {
    const { w, h } = fitSize(4096, 4096);
    expect(w * h).toBeLessThanOrEqual(16_000_000);
  });
});

describe('orientation matrix', () => {
  const apply = (m: number[], x: number, y: number) => [m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5]];
  it('maps the raw top-left pixel to the right corner', () => {
    expect(apply(orientationMatrix(6, 40, 30), 0, 0)).toEqual([30, 0]); // top-right
    expect(apply(orientationMatrix(8, 40, 30), 0, 0)).toEqual([0, 40]); // bottom-left
    expect(apply(orientationMatrix(3, 40, 30), 0, 0)).toEqual([40, 30]); // bottom-right
  });
});

// ---- fakes ----------------------------------------------------------------------------
class FakeEl {
  listeners = new Set<string>();
  attrs: Record<string, string> = {};
  style: Record<string, string> = {};
  files?: File[];
  type = ''; accept = ''; muted = false; srcObject: unknown = null; videoWidth = 0; videoHeight = 0;
  constructor(public tag: string, public log: Log) {}
  setAttribute(k: string, v: string) { this.attrs[k] = v; }
  addEventListener(t: string, f: () => void) { this.log.listeners++; this.handlers[t] = f; this.listeners.add(t); }
  removeEventListener(t: string) { if (this.listeners.delete(t)) this.log.listeners--; delete this.handlers[t]; }
  handlers: Record<string, () => void> = {};
  remove() { this.log.attached.delete(this); }
  click() { this.log.onClick?.(this); }
  play() { return this.log.playRejects ? Promise.reject(new Error('play')) : Promise.resolve(); }
}
interface Log {
  listeners: number; attached: Set<FakeEl>; streams: number; tracksStopped: number; bitmaps: number; closed: number;
  urls: number; onClick?: (el: FakeEl) => void; playRejects?: boolean;
  transforms: number[][]; canvases: { w: number; h: number }[]; elements: FakeEl[];
}

function makeEnv(opts: { bitmap?: { w: number; h: number }; fromImageThrows?: boolean; ignoreFromImage?: boolean; gum?: (c?: any) => Promise<unknown>; imageCapture?: boolean } = {}) {
  const log: Log = { listeners: 0, attached: new Set(), streams: 0, tracksStopped: 0, bitmaps: 0, closed: 0, urls: 0, transforms: [], canvases: [], elements: [] };
  const doc = {
    createElement: (tag: string) => { const e = new FakeEl(tag, log); log.elements.push(e); return e; },
    body: { appendChild: (e: FakeEl) => { log.attached.add(e); } },
  };
  const bm = opts.bitmap ?? { w: 4032, h: 3024 };
  const env: CaptureEnv = {
    document: doc as unknown as Document,
    createImageBitmap: async (_f: Blob, o?: { imageOrientation?: string }) => {
      if (o && opts.fromImageThrows) throw new TypeError('invalid enum');
      log.bitmaps++;
      let { w, h } = bm;
      if (!opts.ignoreFromImage && !opts.fromImageThrows) [w, h] = [w, h]; // already upright
      return { width: w, height: h, close: () => { log.closed++; } } as unknown as ImageBitmap;
    },
    makeCanvas: (w, h) => {
      log.canvases.push({ w, h });
      return { getContext: () => ({
        setTransform: (...m: number[]) => { log.transforms.push(m); },
        drawImage: () => {},
        getImageData: (_x: number, _y: number, ww: number, hh: number) => new ImageData(ww, hh),
      }) };
    },
    mediaDevices: opts.gum ? { getUserMedia: opts.gum as MediaDevices['getUserMedia'] } : undefined,
  };
  if (opts.imageCapture) {
    env.ImageCapture = class { constructor(public t: unknown) {} async takePhoto() { return fileOf(jpeg({})); } } as unknown as CaptureEnv['ImageCapture'];
  }
  return { env, log };
}

const fileOf = (bytes: Uint8Array) => new File([bytes as BlobPart], 'p.jpg', { type: 'image/jpeg' });

/** Make the next input.click() choose `file` (or cancel). */
function chooser(log: Log, file: File | null) {
  log.onClick = (el) => {
    queueMicrotask(() => {
      if (file) { el.files = [file]; el.handlers.change?.(); } else el.handlers.cancel?.();
    });
  };
}

// ---- capturePhoto / pickFile ---------------------------------------------------------------
describe('capturePhoto (file input path)', () => {
  it('uses capture="environment" and returns a camera photo with focal35mm', async () => {
    const { env, log } = makeEnv();
    chooser(log, fileOf(jpeg({ orientation: 1, focal: 26 })));
    const p = await capturePhoto({}, env);
    const input = log.elements.find((e) => e.tag === 'input')!;
    expect(input.attrs.capture).toBe('environment');
    expect(input.accept).toBe('image/*');
    expect(p.source).toBe('camera');
    expect(p.focal35mm).toBe(26);
    expect([p.image.width, p.image.height]).toEqual([4032, 3024]);
  });

  it('pickFile has no capture attribute and is source "file"', async () => {
    const { env, log } = makeEnv();
    chooser(log, fileOf(jpeg({})));
    const p = await pickFile(env);
    expect(log.elements.find((e) => e.tag === 'input')!.attrs.capture).toBeUndefined();
    expect(p.source).toBe('file');
    expect(p.focal35mm).toBeUndefined();
  });

  it('downscales a 8000x6000 decode', async () => {
    const { env, log } = makeEnv({ bitmap: { w: 8000, h: 6000 } });
    chooser(log, fileOf(jpeg({})));
    const p = await capturePhoto({}, env);
    expect(Math.max(p.image.width, p.image.height)).toBeLessThanOrEqual(4096);
    expect(p.image.width * p.image.height).toBeLessThanOrEqual(16_000_000);
  });

  it('cancel gives LOAD_FAILED and leaves nothing behind', async () => {
    const { env, log } = makeEnv();
    chooser(log, null);
    await expect(capturePhoto({}, env)).rejects.toMatchObject({ code: 'LOAD_FAILED' });
    expect(log.listeners).toBe(0);
    expect(log.attached.size).toBe(0);
  });

  it('undecodable file gives LOAD_FAILED (no raw exception escapes)', async () => {
    const { env, log } = makeEnv();
    env.createImageBitmap = async () => { throw new Error('boom'); };
    chooser(log, fileOf(new Uint8Array([1, 2, 3])));
    const e = await capturePhoto({}, env).catch((x) => x);
    expect(e).toBeInstanceOf(OptiError);
    expect(e.code).toBe('LOAD_FAILED');
  });
});

describe('EXIF orientation', () => {
  it('trusts imageOrientation "from-image" when the browser applies it', async () => {
    const { env, log } = makeEnv({ bitmap: { w: 3024, h: 4032 } }); // already upright portrait
    chooser(log, fileOf(jpeg({ orientation: 6, w: 4032, h: 3024 })));
    const p = await capturePhoto({}, env);
    expect([p.image.width, p.image.height]).toEqual([3024, 4032]);
    expect(log.transforms[0]).toEqual([1, 0, 0, 1, 0, 0]);
  });

  it('rotates by hand when the option is unsupported (throws)', async () => {
    const { env, log } = makeEnv({ bitmap: { w: 4032, h: 3024 }, fromImageThrows: true });
    chooser(log, fileOf(jpeg({ orientation: 6, w: 4032, h: 3024 })));
    const p = await capturePhoto({}, env);
    expect([p.image.width, p.image.height]).toEqual([3024, 4032]);
    expect(log.transforms[0]).toEqual([0, 1, -1, 0, 3024, 0]);
  });

  it('rotates by hand when the browser ignores the option silently', async () => {
    const { env, log } = makeEnv({ bitmap: { w: 4032, h: 3024 }, ignoreFromImage: true });
    chooser(log, fileOf(jpeg({ orientation: 8, w: 4032, h: 3024 })));
    const p = await capturePhoto({}, env);
    expect([p.image.width, p.image.height]).toEqual([3024, 4032]);
    expect(log.transforms[0]).toEqual([0, -1, 1, 0, 0, 4032]);
  });
});

describe('live camera path', () => {
  const stream = (log: Log) => {
    log.streams++;
    const track = { stop: () => { log.tracksStopped++; } };
    return { getTracks: () => [track], getVideoTracks: () => [track] };
  };

  it('NotAllowedError throws CAMERA_DENIED', async () => {
    const { env } = makeEnv({ gum: async () => { throw Object.assign(new Error('x'), { name: 'NotAllowedError' }); } });
    await expect(capturePhoto({ useLiveCamera: true }, env)).rejects.toMatchObject({ code: 'CAMERA_DENIED' });
  });

  it('other getUserMedia errors are LOAD_FAILED', async () => {
    const { env } = makeEnv({ gum: async () => { throw Object.assign(new Error('x'), { name: 'NotFoundError' }); } });
    await expect(capturePhoto({ useLiveCamera: true }, env)).rejects.toMatchObject({ code: 'LOAD_FAILED' });
  });

  it('asks for the environment camera, plays inline and muted, stops the stream', async () => {
    let constraints: any;
    let log!: Log;
    const made = makeEnv({ gum: async (c) => { constraints = c; return stream(log); }, imageCapture: true });
    log = made.log;
    const p = await capturePhoto({ useLiveCamera: true }, made.env);
    expect(constraints.video.facingMode).toEqual({ ideal: 'environment' });
    expect(constraints.video.width).toEqual({ ideal: 4032 });
    const video = log.elements.find((e) => e.tag === 'video')!;
    expect(video.attrs.playsinline).toBe('');
    expect(video.muted).toBe(true);
    expect(p.source).toBe('camera');
    expect(log.tracksStopped).toBe(1);
    expect(log.attached.size).toBe(0);
  });

  it('falls back to a canvas frame without ImageCapture and still releases everything', async () => {
    let log!: Log;
    const made = makeEnv({ gum: async () => stream(log) });
    log = made.log;
    const orig = made.env.document.createElement.bind(made.env.document);
    made.env.document.createElement = ((t: string) => { const e = orig(t) as unknown as FakeEl; if (t === 'video') { e.videoWidth = 4032; e.videoHeight = 3024; } return e; }) as Document['createElement'];
    const p = await capturePhoto({ useLiveCamera: true }, made.env);
    expect([p.image.width, p.image.height]).toEqual([4032, 3024]);
    expect(log.tracksStopped).toBe(1);
  });

  it('releases the stream when video.play() fails', async () => {
    let log!: Log;
    const made = makeEnv({ gum: async () => stream(log) });
    log = made.log;
    log.playRejects = true;
    await expect(capturePhoto({ useLiveCamera: true }, made.env)).rejects.toMatchObject({ code: 'LOAD_FAILED' });
    expect(log.tracksStopped).toBe(1);
    expect(log.attached.size).toBe(0);
  });
});

// iOS Safari grants user activation only to the synchronous part of a tap handler. An `await` before
// input.click() or getUserMedia() would silently lose it. We cannot fake activation here, so we guard
// the proxy: the call that needs the gesture must run in the same tick as capturePhoto().
describe('user gesture proxy (no await before click() / getUserMedia())', () => {
  it('file path: input.click() has run before capturePhoto() returns', async () => {
    const { env, log } = makeEnv();
    chooser(log, fileOf(jpeg({})));
    const chooserRun = log.onClick!;
    let clicked = false;
    log.onClick = (el) => { clicked = true; chooserRun(el); };
    const pending = capturePhoto({}, env);
    expect(clicked).toBe(true); // synchronous: no await or microtask ran in between
    await pending;
  });

  it('pickFile: input.click() also runs synchronously', async () => {
    const { env, log } = makeEnv();
    chooser(log, fileOf(jpeg({})));
    const chooserRun = log.onClick!;
    let clicked = false;
    log.onClick = (el) => { clicked = true; chooserRun(el); };
    const pending = pickFile(env);
    expect(clicked).toBe(true);
    await pending;
  });

  it('live path: getUserMedia() has been called before capturePhoto() returns', async () => {
    let called = false;
    let log!: Log;
    const made = makeEnv({
      gum: async () => {
        called = true;
        log.streams++;
        const t = { stop: () => { log.tracksStopped++; } };
        return { getTracks: () => [t], getVideoTracks: () => [t] };
      },
      imageCapture: true,
    });
    log = made.log;
    const pending = capturePhoto({ useLiveCamera: true }, made.env);
    expect(called).toBe(true);
    await pending;
    expect(log.tracksStopped).toBe(1);
  });
});

describe('repeated calls do not leak (three shots per lens)', () => {
  it('file path: listeners, DOM nodes, bitmaps and object URLs all return to zero', async () => {
    const { env, log } = makeEnv();
    const urlCalls: string[] = [];
    const realCreate = URL.createObjectURL;
    URL.createObjectURL = (b: Blob | MediaSource) => { urlCalls.push('create'); return realCreate(b); };
    try {
      for (let i = 0; i < 5; i++) {
        chooser(log, fileOf(jpeg({ orientation: 6 })));
        await capturePhoto({}, env);
      }
      chooser(log, null);
      await capturePhoto({}, env).catch(() => {});
    } finally {
      URL.createObjectURL = realCreate;
    }
    expect(log.listeners).toBe(0);
    expect(log.attached.size).toBe(0);
    expect(log.closed).toBe(log.bitmaps);
    expect(urlCalls).toHaveLength(0); // blobs go straight to createImageBitmap
  });

  it('live path: every stream opened is stopped', async () => {
    let log!: Log;
    const made = makeEnv({
      gum: async () => { log.streams++; const t = { stop: () => { log.tracksStopped++; } }; return { getTracks: () => [t], getVideoTracks: () => [t] }; },
      imageCapture: true,
    });
    log = made.log;
    for (let i = 0; i < 3; i++) await capturePhoto({ useLiveCamera: true }, made.env);
    expect(log.streams).toBe(3);
    expect(log.tracksStopped).toBe(3);
    expect(log.attached.size).toBe(0);
    expect(log.closed).toBe(log.bitmaps);
  });
});
