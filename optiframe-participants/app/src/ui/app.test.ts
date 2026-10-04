// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { OptiError, type Eye, type LensMeasurement } from '../contracts';
import { messageFor } from '../quality';
import { ERROR_CODES, demoMeasurement } from './demo';
import { startApp, type App, type Deps } from './app';
import { initialState, restoreState, saveState } from './state';

let root: HTMLElement;
let saved: { data: BlobPart; name: string; mime: string }[];

const q = (sel: string) => root.querySelector(sel) as HTMLElement | null;
const button = (label: string) => [...root.querySelectorAll('button')].find((b) => b.textContent?.trim().startsWith(label)) as HTMLButtonElement | undefined;
const click = (label: string) => {
  const b = button(label);
  if (!b) throw new Error(`no button "${label}" on ${q('[data-screen]')?.getAttribute('data-screen')}`);
  b.click();
};
const screen = () => q('[data-screen]')?.getAttribute('data-screen');
const waitScreen = (name: string) => vi.waitFor(() => expect(screen()).toBe(name), { timeout: 5000 });

/** The real generateFrame, with the page-only branch of loadManifold switched off (jsdom has a `location`, Node does not). */
async function realGenerate(...args: Parameters<Deps['generate']>) {
  vi.stubGlobal('location', undefined);
  try {
    return await (await import('../frame')).generateFrame(...args);
  } finally {
    vi.unstubAllGlobals();
  }
}

function start(search: string, override: Partial<Deps> = {}): App {
  return startApp(root, search, { save: (data, name, mime) => saved.push({ data, name, mime }), generate: realGenerate, ...override });
}

beforeEach(() => {
  root = document.createElement('main');
  document.body.replaceChildren(root);
  saved = [];
  window.scrollTo = () => {};
  sessionStorage.clear();
});
afterEach(() => { document.body.replaceChildren(); });

describe('?demo=1 walks the five screens', () => {
  it('home -> capture -> result -> (twice) -> frame -> steps, and downloads a valid STL', async () => {
    const app = start('?demo=1');
    expect(screen()).toBe('home');
    expect(root.textContent).toContain('Comment installer le dispositif');
    expect(q('a[href="./lightbox.html"]')?.textContent).toBe('Page de rétro-éclairage');
    expect(q('a[href="./collect.html"]')?.textContent).toBe('Collecte de données (équipe)');
    expect(q('[data-eye="L"]')?.textContent).toContain('Verre gauche');
    expect(q('[data-eye="R"]')?.textContent).toContain('Verre droit');
    expect(q('[data-eye="L"]')?.textContent).toContain('à faire');
    expect(button('Créer la monture')).toBeUndefined();

    for (const eye of ['L', 'R'] as Eye[]) {
      q(`[data-eye="${eye}"]`)!.click();
      expect(screen()).toBe('capture');
      expect(q('.picto svg')?.getAttribute('aria-label')).toContain(eye === 'R' ? 'droite' : 'gauche');
      for (let n = 1; n <= 3; n++) {
        click('Prendre la photo');
        await vi.waitFor(() => expect(app.state.shots).toHaveLength(n));
        if (n < 3) {
          await vi.waitFor(() => expect(q('.count')?.textContent).toBe(`photo ${n} sur 3`));
          expect(root.textContent).toContain('Bougez légèrement le téléphone');
          if (n >= 2) expect(q('.spread')?.textContent).toMatch(/^Écart entre les photos : A \d+,\d mm, B \d+,\d mm$/);
        }
      }
      await waitScreen('result');
      expect(button('Exporter le contour (SVG 1:1)')).toBeTruthy();
      expect(button('Reprendre')).toBeTruthy();
      const m = app.state.fused!;
      expect(q('[data-value="A"]')?.textContent).toBe(`${m.A.toFixed(1).replace('.', ',')} mm`);
      expect(q('[data-value="perimeter"]')?.textContent).toMatch(/^\d+,\d mm$/);
      click('Exporter le contour (SVG 1:1)');
      expect(saved.at(-1)!.name).toBe(eye === 'L' ? 'contour-gauche.svg' : 'contour-droit.svg');
      expect(String(saved.at(-1)!.data)).toContain('<svg');
      click('Valider');
      expect(screen()).toBe('home');
      expect(q(`[data-eye="${eye}"]`)?.textContent).toContain('fait');
    }

    click('Pas à pas');
    expect(screen()).toBe('steps');
    expect(root.querySelectorAll('figure')).toHaveLength(4);
    click('Retour');

    click('Créer la monture');
    await waitScreen('frame');
    expect((q('#bridge') as HTMLInputElement).min).toBe('14');
    expect((q('#bridge') as HTMLInputElement).max).toBe('22');
    expect((q('#bridge') as HTMLInputElement).value).toBe('18');
    await vi.waitFor(() => expect(app.state.frame).not.toBeNull(), { timeout: 30_000 });
    expect(q('.overlay svg path')).toBeTruthy();
    expect(q('.gap')?.textContent).toBe('Jeu entre le verre et son logement : 0,2 mm');
    expect(button('Télécharger monture.stl')!.disabled).toBe(false);

    click('Télécharger monture.stl');
    const stl = saved.at(-1)!;
    expect(stl.name).toBe('monture.stl');
    const buf = stl.data as ArrayBuffer;
    const n = new DataView(buf).getUint32(80, true);
    expect(n).toBeGreaterThan(100);
    expect(buf.byteLength).toBe(84 + 50 * n); // binary STL: 80-byte header, count, 50 bytes per triangle
    expect(n).toBe(app.state.frame!.indices.length / 3);

    click('Télécharger les mesures');
    const json = JSON.parse(String(saved.at(-1)!.data));
    expect(saved.at(-1)!.name).toBe('mesures.json');
    expect(json.frameParams.bridgeMm).toBe(18);
    expect(json.left.eye).toBe('L');
  }, 60_000);

  it('a new bridge width rebuilds the frame', async () => {
    const generate = vi.fn(realGenerate);
    const app = start('?demo=1', { generate });
    app.state.lenses = { L: demoMeasurement('L', 0), R: demoMeasurement('R', 0) };
    app.render();
    click('Créer la monture');
    await vi.waitFor(() => expect(app.state.frame).not.toBeNull(), { timeout: 30_000 });
    const slider = q('#bridge') as HTMLInputElement;
    slider.value = '20';
    slider.dispatchEvent(new Event('input'));
    await vi.waitFor(() => expect(generate).toHaveBeenLastCalledWith(expect.anything(), expect.anything(), expect.objectContaining({ bridgeMm: 20 })), { timeout: 30_000 });
    expect(q('output')?.textContent).toBe('20,0 mm');
  }, 60_000);

  it('stopping after one photo is allowed', async () => {
    const app = start('?demo=1');
    q('[data-eye="R"]')!.click();
    click('Prendre la photo');
    await vi.waitFor(() => expect(app.state.shots).toHaveLength(1));
    await vi.waitFor(() => expect(button('Terminer avec 1 photo')).toBeTruthy());
    click('Terminer avec 1 photo');
    expect(screen()).toBe('result');
    expect(root.textContent).toContain('1 photo : pas d’écart à afficher.');
  });

  it('a rotated lens gives a non-blocking hint, not an error', async () => {
    const app = start('?demo=1');
    const rotated: LensMeasurement = demoMeasurement('R', 0);
    const t = Math.PI / 6; // an ellipse turned by 30 degrees
    rotated.contourMm = rotated.contourMm.map(([x, y]) => { const dx = x - 40, dy = y - 32.5; return [40 + dx * Math.cos(t) - dy * Math.sin(t), 32.5 + dx * Math.sin(t) + dy * Math.cos(t)]; });
    app.deps.measure = async () => ({ result: rotated, steps: { markers: [], rectified: new ImageData(8, 8), mask: { data: new Uint8Array(64), width: 8, height: 8, method: 'classic', score: 1 } } });
    q('[data-eye="R"]')!.click();
    click('Prendre la photo');
    await vi.waitFor(() => expect(app.state.hint).toBe('LENS_ROTATED'));
    expect(app.state.error).toBeNull();
    await vi.waitFor(() => expect(q('.hint')?.textContent).toBe(messageFor('LENS_ROTATED')));
    expect(q('.banner')).toBeNull();
  });
});

describe('?demo=1&error=CODE', () => {
  for (const code of ERROR_CODES) {
    it(`${code}: banner with exactly the messageFor sentence, Reprendre and Fermer`, () => {
      start(`?demo=1&error=${code}`);
      const banner = q('.banner')!;
      expect(banner).toBeTruthy();
      expect(banner.getAttribute('data-code')).toBe(code);
      expect(banner.querySelector('p')!.textContent).toBe(messageFor(code));
      expect(banner.textContent).not.toMatch(/demo|Error|undefined|\[object/);
      expect(button('Reprendre')).toBeTruthy();
      button('Fermer')!.click();
      expect(q('.banner')).toBeNull();
    });
  }

  it('an unknown code shows no banner', () => {
    start('?demo=1&error=PAS_UN_CODE');
    expect(q('.banner')).toBeNull();
  });

  it('a failing photo shows the banner of that code, and Reprendre goes back to the capture screen', async () => {
    start('?demo=1&error=BLURRY');
    click('Reprendre'); // no eye chosen yet: stays on the home screen
    expect(screen()).toBe('home');
    q('[data-eye="L"]')!.click();
    click('Prendre la photo');
    await vi.waitFor(() => expect(q('.banner')?.getAttribute('data-code')).toBe('BLURRY'));
    expect(q('.banner p')!.textContent).toBe(messageFor('BLURRY'));
    click('Reprendre');
    expect(q('.banner')).toBeNull();
    expect(screen()).toBe('capture');
  });
});

describe('errors from the pipeline reach the screen only as messageFor', () => {
  it.each([
    ['an OptiError', new OptiError('GLARE', 'internal detail'), 'GLARE'],
    ['an Error', new Error('secret stack text'), 'LOAD_FAILED'],
    ['a string', 'oops', 'LOAD_FAILED'],
    ['undefined', undefined, 'LOAD_FAILED'],
  ] as const)('%s', async (_n, thrown, code) => {
    const app = start('?demo=1', { measure: async () => { throw thrown; } });
    q('[data-eye="R"]')!.click();
    click('Prendre la photo');
    await vi.waitFor(() => expect(q('.banner')).toBeTruthy());
    expect(q('.banner')!.getAttribute('data-code')).toBe(code);
    expect(root.textContent).toContain(messageFor(code));
    expect(root.textContent).not.toContain('secret');
    expect(root.textContent).not.toContain('internal detail');
    expect(app.state.busy).toBeNull();
  });

  it('INCONSISTENT_SHOTS from the fusion clears the shots on Reprendre', async () => {
    const app = start('?demo=1', { finish: () => { throw new OptiError('INCONSISTENT_SHOTS'); } });
    q('[data-eye="R"]')!.click();
    for (let n = 1; n <= 3; n++) {
      await vi.waitFor(() => expect(button('Prendre la photo')!.disabled).toBe(false));
      click('Prendre la photo');
      await vi.waitFor(() => expect(app.state.shots.length === n || app.state.error !== null).toBe(true));
    }
    await vi.waitFor(() => expect(q('.banner')?.getAttribute('data-code')).toBe('INCONSISTENT_SHOTS'));
    click('Reprendre');
    expect(app.state.shots).toHaveLength(0);
    expect(screen()).toBe('capture');
  });

  it('a failing start (board_spec.json missing) shows LOAD_FAILED', async () => {
    start('', { start: async () => { throw new OptiError('LOAD_FAILED', 'board_spec.json: 404'); } });
    await vi.waitFor(() => expect(q('.banner')?.getAttribute('data-code')).toBe('LOAD_FAILED'));
  });

  it('names the current step while measuring', async () => {
    let step: ((s: 'locate' | 'isolate' | 'measure') => void) | null = null;
    let release: () => void = () => {};
    const app = start('?demo=1', {
      onStep: (cb) => { step = cb as typeof step; },
      measure: async (_p, eye) => { step!('isolate'); await new Promise<void>((r) => { release = r; }); return { result: demoMeasurement(eye, 0), steps: { markers: [], rectified: new ImageData(8, 8), mask: { data: new Uint8Array(64), width: 8, height: 8, method: 'classic', score: 1 } } }; },
    });
    q('[data-eye="R"]')!.click();
    click('Prendre la photo');
    await vi.waitFor(() => expect(q('.progress')?.textContent).toBe('J\'isole le verre…'));
    expect(button('Prendre la photo')!.disabled).toBe(true);
    release();
    await vi.waitFor(() => expect(q('.progress')).toBeNull());
    expect(app.state.shots).toHaveLength(1);
  });
});

describe('measuring tool and timings', () => {
  it('the capture screen says the measuring tool is loading, until it is ready', () => {
    let emit: (s: 'loading' | 'ready' | 'failed') => void = () => {};
    const app = start('', { start: async () => {}, warm: (cb) => { emit = cb; cb('loading'); } });
    expect(q('[data-engine]')).toBeNull(); // home screen: nothing to say
    q('[data-eye="R"]')!.click();
    expect(q('[data-engine="loading"]')?.textContent).toContain('Je prépare l’outil de mesure');
    expect(q('[data-engine="loading"]')?.getAttribute('role')).toBe('status');
    expect(button('Prendre la photo')!.disabled).toBe(false); // a photo taken now waits for the tool
    emit('ready');
    expect(app.state.engine).toBe('ready');
    expect(q('[data-engine]')).toBeNull();
    expect(screen()).toBe('capture');
  });

  it('a failed load shows no line (the photo then fails with LOAD_FAILED) and the next lens tries again', () => {
    let calls = 0;
    start('', { start: async () => {}, warm: (cb) => { calls++; cb('failed'); } });
    expect(calls).toBe(1);
    q('[data-eye="L"]')!.click();
    expect(q('[data-engine]')).toBeNull();
    expect(calls).toBe(2);
  });

  it('the demo starts with the tool ready', () => {
    const app = start('?demo=1');
    expect(app.state.engine).toBe('ready');
  });

  it('"Pas à pas" lists the duration of every stage of the last photo, and of the fuse', async () => {
    const steps = { markers: [], rectified: new ImageData(8, 8), mask: { data: new Uint8Array(64), width: 8, height: 8, method: 'classic' as const, score: 1 } };
    const timings = { 'round-trip': 812.4, worker: 800, rectify: 500, 'opencv-load': 0.2, detect: 300, warp: 150, sharpness: 50, segment: 250, measure: 50 };
    start('?demo=1', { measure: async (_p, eye) => ({ result: demoMeasurement(eye, 0), steps, timings }) });
    q('[data-eye="R"]')!.click();
    click('Prendre la photo');
    await vi.waitFor(() => expect(button('Terminer avec 1 photo')).toBeTruthy());
    click('Terminer avec 1 photo');
    await waitScreen('result');
    click('Pas à pas');
    expect(screen()).toBe('steps');
    expect(root.textContent).toContain('Durées sur cet appareil');
    expect(q('[data-timing="round-trip"]')?.textContent).toBe('812 ms');
    expect(q('[data-timing="detect"]')?.textContent).toBe('300 ms');
    expect(q('[data-timing="opencv-load"]')?.textContent).toBe('0 ms');
    expect(q('[data-timing="fuse"]')?.textContent).toMatch(/^\d+ ms$/);
    expect([...root.querySelectorAll('[data-timing]')].map((e) => e.getAttribute('data-timing')))
      .toEqual(['round-trip', 'worker', 'rectify', 'opencv-load', 'detect', 'warp', 'sharpness', 'segment', 'measure', 'fuse']);
  });
});

describe('session storage', () => {
  it('keeps validated measurements only (no image) and restores them after a reload', async () => {
    const first = start('?demo=1', { storage: sessionStorage });
    q('[data-eye="R"]')!.click();
    first.state.fused = demoMeasurement('R', 0);
    first.state.eye = 'R';
    first.render();
    first.state.screen = 'result';
    first.render();
    click('Valider');
    const raw = sessionStorage.getItem('optiframe.v1')!;
    expect(raw).toBeTruthy();
    expect(raw).not.toMatch(/data:image|"data":|imageData|rectified|"mask"/);
    expect(JSON.parse(raw).lenses.R.A).toBeCloseTo(demoMeasurement('R', 0).A, 6);

    const second = start('?demo=1', { storage: sessionStorage });
    expect(second.state.lenses.R).toBeTruthy();
    expect(second.state.lenses.L).toBeUndefined();
    expect(q('[data-eye="R"]')?.textContent).toContain('fait');
  });

  it('ignores corrupt or blocked storage', () => {
    sessionStorage.setItem('optiframe.v1', '{not json');
    const s = initialState();
    expect(() => restoreState(s, sessionStorage)).not.toThrow();
    expect(s.lenses).toEqual({});
    sessionStorage.setItem('optiframe.v1', JSON.stringify({ lenses: { R: { eye: 'R', A: 'x' } }, bridgeMm: 99 }));
    restoreState(s, sessionStorage);
    expect(s.lenses.R).toBeUndefined();
    expect(s.bridgeMm).toBe(22);
    const blocked = { setItem() { throw new Error('quota'); }, getItem() { throw new Error('denied'); } } as unknown as Storage;
    expect(() => saveState(s, blocked)).not.toThrow();
    expect(() => restoreState(s, blocked)).not.toThrow();
  });
});

describe('layout at 360 px (reasoned from the CSS: jsdom computes no layout)', () => {
  it('the stylesheet keeps buttons at 48 px or more and nothing wider than the screen', async () => {
    const { readFileSync } = await import('node:fs');
    const css = readFileSync('src/ui/styles.css', 'utf8'); // vitest runs from app/
    expect(css).toMatch(/\.btn \{[^}]*min-height: 48px/);
    expect(css).toMatch(/input\[type=range\] \{[^}]*min-height: 48px/);
    expect(css).toMatch(/\*, \*::before, \*::after \{ box-sizing: border-box/);
    expect(css).toMatch(/img, canvas, svg \{ max-width: 100%/);
    expect(css).toMatch(/main \{[^}]*max-width: 32rem/);
    expect(css).not.toMatch(/overflow-x: scroll/);
    // no fixed pixel width above 360 px anywhere
    for (const m of css.matchAll(/(?<![a-z-])width: (\d+)px/g)) expect(Number(m[1])).toBeLessThanOrEqual(360);
  });
});

describe('fixes from the final audit', () => {
  it('closing the camera without a photo shows no error and leaves the capture screen usable', async () => {
    const app = start('?demo=1', { capture: async () => { throw new OptiError('LOAD_FAILED', 'cancelled'); } });
    q('[data-eye="L"]')!.click();
    click('Prendre la photo');
    await new Promise((r) => setTimeout(r, 20));
    expect(q('.banner')).toBeNull();
    expect(screen()).toBe('capture');
    expect(app.state.busy).toBeNull();
    expect(button('Prendre la photo')!.disabled).toBe(false);
  });

  it('the capture screen says which face is up and where the top goes', () => {
    start('?demo=1');
    q('[data-eye="R"]')!.click();
    expect(root.textContent).toContain('Face bombée vers le haut');
    expect(root.textContent).toContain('« HAUT »');
  });

  it('a small photo (resized by a messaging app) gets a hint, a full-size one does not', async () => {
    const app = start('?demo=1');
    q('[data-eye="L"]')!.click();
    click('Prendre la photo');
    await vi.waitFor(() => expect(app.state.shots).toHaveLength(1));
    const setSize = (width: number) => { Object.defineProperty(app.state.last!.photo, 'image', { value: { width, height: 600 }, configurable: true }); app.render(); };
    expect(q('[data-hint="small-photo"]')).toBeNull(); // demo placeholder
    setSize(1280);
    expect(q('[data-hint="small-photo"]')).toBeTruthy();
    setSize(4032);
    expect(q('[data-hint="small-photo"]')).toBeNull();
  });

  it('the frame screen exports the outline of each validated lens', async () => {
    const app = start('?demo=1');
    app.state.lenses = { L: demoMeasurement('L', 0), R: demoMeasurement('R', 0) };
    app.render();
    click('Créer la monture');
    await waitScreen('frame');
    click('Contour gauche (SVG 1:1)');
    expect(saved.at(-1)!.name).toBe('contour-gauche.svg');
    click('Contour droit (SVG 1:1)');
    expect(saved.at(-1)!.name).toBe('contour-droit.svg');
    expect(String(saved.at(-1)!.data)).toContain('<svg');
  }, 60_000);
});
