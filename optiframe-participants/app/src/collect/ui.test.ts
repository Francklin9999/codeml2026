// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { OptiError, type Eye, type LensMeasurement, type Photo } from '../contracts';
import { messageFor } from '../quality';
import { fakeIndexedDB } from './fakeIdb.testutil';
import { openStore, type PhotoStore } from './storage';
import { mountCollect, type Deps } from './ui';

const jpeg = (n: number, seed: number) => Uint8Array.from({ length: n }, (_, i) => (i * 13 + seed) & 255);
const fileOf = (bytes: Uint8Array, name = 'IMG_0001.jpg') => new File([bytes as BlobPart], name, { type: 'image/jpeg' });
const meas = (A: number, B: number): LensMeasurement => ({
  eye: 'R', contourMm: [], A, B, perimeter: 190.5, boxCentre: [0, 0], method: 'classic', quality: { reprojErrMm: 0.1, sharpness: 0.001, nShots: 1, spreadA: 0, spreadB: 0 },
});

interface Rig {
  root: HTMLElement; deps: Deps; store: PhotoStore; saved: string[]; ls: Map<string, string>;
  next: { file?: File; measure?: () => LensMeasurement; sheet?: () => { nMarkers?: number }; confirm: boolean };
}

async function rig(ua = 'Mozilla/5.0 (Linux; Android 14; Pixel 7 Build/UP1A) Chrome/120', estimate = { usage: 10e6, quota: 1000e6 }): Promise<Rig> {
  document.body.innerHTML = '<main id="app"></main>';
  const root = document.getElementById('app')!;
  const store = await openStore(fakeIndexedDB());
  const ls = new Map<string, string>();
  const saved: string[] = [];
  const next: Rig['next'] = { confirm: true };
  const deps: Deps = {
    store,
    chooseFile: async () => { if (!next.file) throw new OptiError('LOAD_FAILED', 'cancelled'); const f = next.file; next.file = undefined; return f; },
    decode: async (): Promise<Photo> => ({ image: new ImageData(4, 3), source: 'camera', focal35mm: 26 }),
    measure: async (_p: Photo, _e: Eye) => { if (!next.measure) throw new OptiError('NO_LENS'); return next.measure(); },
    checkSheet: async () => { if (!next.sheet) throw new OptiError('NO_REFERENCE'); return next.sheet(); },
    makeThumb: async () => Uint8Array.from([1, 2, 3]).buffer as ArrayBuffer,
    save: async (_d, name) => { saved.push(name); return 'saved'; },
    confirm: () => next.confirm,
    storage: { persist: async () => true, estimate: async () => estimate },
    local: { getItem: (k) => ls.get(k) ?? null, setItem: (k, v) => void ls.set(k, v) },
    url: { create: () => 'blob:fake', revoke: () => undefined },
    userAgent: ua, appVersion: '9.9.9', now: () => new Date('2026-03-01T12:00:00Z'),
  };
  await mountCollect(root, deps).ready;
  return { root, deps, store, next, saved, ls };
}

const q = <T extends HTMLElement>(root: HTMLElement, sel: string) => root.querySelector(sel) as T;
function type(root: HTMLElement, sel: string, v: string) {
  const i = q<HTMLInputElement>(root, sel);
  i.value = v;
  i.dispatchEvent(new Event('input', { bubbles: true }));
}
const click = (root: HTMLElement, sel: string) => q(root, sel).click();
const result = (root: HTMLElement) => q(root, '#resultBox').textContent ?? '';
const settle = async (root: HTMLElement, text: string) => vi.waitFor(() => expect(result(root)).toContain(text));
const tab = (root: HTMLElement, mode: string) => q(root, `#tabs button[data-mode="${mode}"]`).click();
const pause = () => new Promise((res) => setTimeout(res, 30));
const stored = async (r: Rig) => (await r.store.list()).sort((a, b) => a.name.localeCompare(b.name));
const bytesOf = async (r: Rig, name: string) => new Uint8Array((await r.store.getBytes(name))!);

beforeEach(() => { document.body.innerHTML = ''; });

describe('collect page', () => {
  it('shows the fixed privacy line, French labels, and the training rule', async () => {
    const { root } = await rig();
    expect(root.textContent).toContain("Pas de visages, pas de noms, pas d'ordonnances sur les photos.");
    expect(root.textContent).toContain('Ne bougez ni le verre ni le téléphone entre deux photos.');
    expect(root.querySelectorAll('#tabs button')).toHaveLength(3);
    expect(q<HTMLInputElement>(root, '#v-phone').value).toBe('Pixel-7');
    expect(q(root, '#v-a1').getAttribute('inputmode')).toBe('decimal');
  });

  it('validation: stores the original bytes with metadata, shows A, B, perimeter and the signed error, rep counts up', async () => {
    const r = await rig();
    const { root, next } = r;
    type(root, '#v-lens', 'L 01_x');
    expect(q<HTMLInputElement>(root, '#v-lens').value).toBe('L-01-x'); // sanitised as typed
    type(root, '#v-lens', 'L01');
    for (const [id, v] of [['#v-a1', '60,0'], ['#v-a2', '60.1'], ['#v-a3', '59.9'], ['#v-b1', '48'], ['#v-b2', '48.2'], ['#v-b3', '48.1']]) type(root, id, v);
    type(root, '#v-tint', 'clair');
    type(root, '#v-edge', '2,1');
    const bytes = jpeg(2000, 5);
    next.file = fileOf(bytes);
    next.measure = () => meas(60.5, 48.0);
    click(root, '#v-shoot');
    await settle(root, 'Enregistré : L01_Pixel-7_1.jpg');
    expect(result(root)).toContain('A 60,50 mm');
    expect(result(root)).toContain('B 48,00 mm');
    expect(result(root)).toContain('périmètre 190,50 mm');
    expect(result(root)).toContain('A +0,50 mm'); // median of the three A readings is 60,0
    expect(result(root)).toContain('B −0,10 mm'); // median of the three B readings is 48,1

    const [m] = await stored(r);
    expect(m).toMatchObject({
      name: 'L01_Pixel-7_1.jpg', mode: 'validation', lensId: 'L01', eye: 'R', phone: 'Pixel-7', rep: 1, ok: true, tint: 'clair', edgeThickness: 2.1,
      A: [60, 60.1, 59.9], B: [48, 48.2, 48.1], appVersion: '9.9.9', takenAt: '2026-03-01T12:00:00.000Z', bytes: 2000, width: 4, height: 3, focal35mm: 26,
    });
    expect(m.userAgent).toContain('Pixel 7');
    expect(m.measured).toMatchObject({ A: 60.5, B: 48, method: 'classic' });
    expect(await bytesOf(r, m.name)).toEqual(bytes); // original bytes untouched

    next.file = fileOf(jpeg(10, 1));
    click(root, '#v-shoot');
    await settle(root, 'Enregistré : L01_Pixel-7_2.jpg');
    expect((await stored(r)).map((x) => x.name)).toEqual(['L01_Pixel-7_1.jpg', 'L01_Pixel-7_2.jpg']);
    expect(q(root, '#counts').textContent).toContain('Validation 2');
    expect(q(root, '#counts').textContent).toContain('L01 2');
  });

  it('validation: a failed shot is kept with its code and shown with the messageFor sentence; no readings means no error figure', async () => {
    const r = await rig();
    type(r.root, '#v-lens', 'L02');
    r.next.file = fileOf(jpeg(50, 2));
    click(r.root, '#v-shoot'); // measure not set: throws NO_LENS
    await settle(r.root, messageFor('NO_LENS'));
    const [m] = await stored(r);
    expect(m).toMatchObject({ name: 'L02_Pixel-7_1.jpg', ok: false, errorCode: 'NO_LENS' });
    expect(await bytesOf(r, m.name)).toEqual(jpeg(50, 2));

    r.next.file = fileOf(jpeg(50, 3));
    r.next.measure = () => meas(50, 40);
    click(r.root, '#v-shoot');
    await settle(r.root, 'erreur non calculée');
  });

  it('validation: an unknown exception shows the LOAD_FAILED sentence', async () => {
    const r = await rig();
    type(r.root, '#v-lens', 'L03');
    r.next.file = fileOf(jpeg(5, 2));
    r.next.measure = () => { throw new Error('boom'); };
    click(r.root, '#v-shoot');
    await settle(r.root, messageFor('LOAD_FAILED'));
    expect((await stored(r))[0].errorCode).toBe('LOAD_FAILED');
  });

  it('validation: refuses a missing identifier without opening the camera, and flags incoherent readings', async () => {
    const r = await rig();
    r.next.file = fileOf(jpeg(5, 2));
    click(r.root, '#v-shoot');
    await settle(r.root, 'Identifiant du verre');
    expect(r.next.file).toBeDefined(); // chooser never called
    expect(await stored(r)).toHaveLength(0);
    type(r.root, '#v-a1', '60');
    type(r.root, '#v-a2', '60.4');
    expect(q(r.root, '#v-aspread').textContent).toContain('lectures incohérentes, refaire');
    type(r.root, '#v-a2', '60.1');
    expect(q(r.root, '#v-aspread').textContent).not.toContain('incohérentes');
  });

  it('training: easy first, names follow the protocol, sheet result shown, a late condition warns', async () => {
    const r = await rig();
    tab(r.root, 'training');
    type(r.root, '#t-lens', 'L07');
    expect(q(r.root, '#t-warn').hasAttribute('hidden')).toBe(false); // easy not shot yet
    const buttons = [...r.root.querySelectorAll<HTMLElement>('#t-grid button')].map((b) => b.dataset.cond);
    expect(buttons[0]).toBe('easy');
    expect(buttons).toHaveLength(8);

    r.next.file = fileOf(jpeg(30, 1));
    r.next.sheet = () => ({ nMarkers: 14 });
    click(r.root, '#t-grid button[data-cond="easy"]');
    await settle(r.root, 'Feuille détectée (14 marqueurs)');
    expect(result(r.root)).toContain('Enregistré : L07_1_easy.jpg');
    expect(q(r.root, '#t-warn').hasAttribute('hidden')).toBe(true);
    expect(q(r.root, '#t-grid button[data-cond="easy"]').textContent).toContain('✓');

    r.next.file = fileOf(jpeg(30, 2));
    click(r.root, '#t-grid button[data-cond="lampL"]');
    await settle(r.root, 'Enregistré : L07_1_lampL.jpg');
    expect(result(r.root)).not.toContain('Attention');

    type(r.root, '#t-lens', 'L08'); // no easy for L08
    r.next.file = fileOf(jpeg(30, 3));
    r.next.sheet = undefined; // sheet check fails
    click(r.root, '#t-grid button[data-cond="flash"]');
    await settle(r.root, 'Enregistré : L08_1_flash.jpg');
    expect(result(r.root)).toContain("« easy » (rétro-éclairé) n'a pas été pris");
    expect(result(r.root)).toContain(messageFor('NO_REFERENCE'));
    const all = await stored(r);
    expect(all.map((m) => m.name)).toEqual(['L07_1_easy.jpg', 'L07_1_lampL.jpg', 'L08_1_flash.jpg']);
    expect(all[0]).toMatchObject({ mode: 'training', position: 1, condition: 'easy', sheet: { checked: true, ok: true, markers: 14 } });
    expect(all[2]).toMatchObject({ ok: false, errorCode: 'NO_REFERENCE' });
  });

  it('training: retaking a done condition asks first and replaces the same file', async () => {
    const r = await rig();
    tab(r.root, 'training');
    type(r.root, '#t-lens', 'L07');
    r.next.sheet = () => ({});
    r.next.file = fileOf(jpeg(30, 1));
    click(r.root, '#t-grid button[data-cond="easy"]');
    await settle(r.root, 'Feuille détectée');
    expect(result(r.root)).not.toContain('marqueurs');

    r.next.confirm = false;
    r.next.file = fileOf(jpeg(30, 9));
    click(r.root, '#t-grid button[data-cond="easy"]');
    await pause();
    expect(r.next.file).toBeDefined(); // not taken
    r.next.confirm = true;
    click(r.root, '#t-grid button[data-cond="easy"]');
    await vi.waitFor(async () => expect(await bytesOf(r, 'L07_1_easy.jpg')).toEqual(jpeg(30, 9)));
    expect(await stored(r)).toHaveLength(1);
  });

  it('free: label_n naming, sheet check optional, tags kept', async () => {
    const r = await rig();
    tab(r.root, 'free');
    type(r.root, '#f-label', 'SN SF paire3');
    expect(q<HTMLInputElement>(r.root, '#f-label').value).toBe('SN-SF-paire3');
    type(r.root, '#f-tags', 'monté, reflet');
    r.next.file = fileOf(jpeg(30, 1));
    click(r.root, '#f-shoot');
    await settle(r.root, 'Enregistré : SN-SF-paire3_1.jpg');
    expect(result(r.root)).toContain('Photo enregistrée.');
    q<HTMLInputElement>(r.root, '#f-sheet').click();
    r.next.file = fileOf(jpeg(30, 2));
    r.next.sheet = () => ({ nMarkers: 18 });
    click(r.root, '#f-shoot');
    await settle(r.root, 'Enregistré : SN-SF-paire3_2.jpg');
    expect(result(r.root)).toContain('Feuille détectée (18 marqueurs)');
    const all = await stored(r);
    expect(all.map((m) => m.name)).toEqual(['SN-SF-paire3_1.jpg', 'SN-SF-paire3_2.jpg']);
    expect(all[0]).toMatchObject({ mode: 'free', label: 'SN-SF-paire3', tags: ['monté', 'reflet'], sheet: { checked: false } });
    expect(all[0].measured).toBeUndefined();
  });

  it('remembers the tab and the identifiers', async () => {
    const a = await rig();
    tab(a.root, 'free');
    type(a.root, '#f-label', 'abc');
    type(a.root, '#v-phone', 'Galaxy S9');
    const ls = a.ls;
    document.body.innerHTML = '<main id="app"></main>';
    const root = document.getElementById('app')!;
    await mountCollect(root, { ...a.deps, local: { getItem: (k) => ls.get(k) ?? null, setItem: () => undefined } }).ready;
    expect(q(root, '#tabs button[aria-selected="true"]').textContent).toBe('Libre');
    expect(q<HTMLInputElement>(root, '#f-label').value).toBe('abc');
    expect(q<HTMLInputElement>(root, '#v-phone').value).toBe('Galaxy-S9');
  });

  it('gallery: retake replaces the photo under the same name; delete asks for confirmation', async () => {
    const r = await rig();
    type(r.root, '#v-lens', 'L01');
    r.next.measure = () => meas(60, 48);
    r.next.file = fileOf(jpeg(20, 1));
    click(r.root, '#v-shoot');
    await settle(r.root, 'Enregistré : L01_Pixel-7_1.jpg');
    click(r.root, '#gallery button[data-name="L01_Pixel-7_1.jpg"]');
    expect(q(r.root, '#detail').hasAttribute('hidden')).toBe(false);

    r.next.file = fileOf(jpeg(20, 7));
    r.next.measure = () => meas(61, 49);
    q(r.root, '#detail button.primary').click();
    await vi.waitFor(async () => expect(await bytesOf(r, 'L01_Pixel-7_1.jpg')).toEqual(jpeg(20, 7)));
    expect(await stored(r)).toHaveLength(1);
    expect((await stored(r))[0].measured!.A).toBe(61);

    click(r.root, '#gallery button[data-name="L01_Pixel-7_1.jpg"]');
    r.next.confirm = false;
    q(r.root, '#detail button.danger').click();
    await pause();
    expect(await stored(r)).toHaveLength(1);
    r.next.confirm = true;
    q(r.root, '#detail button.danger').click();
    await vi.waitFor(async () => expect(await stored(r)).toHaveLength(0));
  });

  it('export: marks exported only after saving, empty export refused, clear removes only exported ones after confirmation', async () => {
    const r = await rig();
    expect(q(r.root, '#x-build').textContent).toContain('0 nouvelle');
    click(r.root, '#x-build');
    await vi.waitFor(() => expect(q(r.root, '#x-msg').textContent).toBeTruthy());
    expect(r.root.querySelectorAll('#x-parts button')).toHaveLength(0);

    r.next.measure = () => meas(60, 48);
    for (const lens of ['L01', 'L02']) {
      type(r.root, '#v-lens', lens);
      r.next.file = fileOf(jpeg(40, 1));
      click(r.root, '#v-shoot');
      await settle(r.root, `Enregistré : ${lens}_Pixel-7_1.jpg`);
    }
    click(r.root, '#x-build');
    await vi.waitFor(() => expect(r.root.querySelectorAll('#x-parts button')).toHaveLength(1));
    expect((await stored(r)).every((m) => !m.exportedAt)).toBe(true); // built, not yet saved
    click(r.root, '#x-parts button');
    await vi.waitFor(async () => expect((await stored(r)).every((m) => m.exportedAt)).toBe(true));
    expect(r.saved).toHaveLength(1);
    expect(r.saved[0]).toMatch(/^optiframe-collecte_.*\.zip$/);

    // a new photo is not exported: clearing keeps it
    type(r.root, '#v-lens', 'L03');
    r.next.file = fileOf(jpeg(40, 1));
    click(r.root, '#v-shoot');
    await settle(r.root, 'Enregistré : L03_Pixel-7_1.jpg');
    r.next.confirm = false;
    click(r.root, '#x-clear');
    await pause();
    expect(await stored(r)).toHaveLength(3);
    r.next.confirm = true;
    click(r.root, '#x-clear');
    await vi.waitFor(async () => expect((await stored(r)).map((m) => m.name)).toEqual(['L03_Pixel-7_1.jpg']));
  });

  it('warns above 80 % of the quota and shows persistence', async () => {
    const r = await rig(undefined, { usage: 85e6, quota: 100e6 });
    expect(q(r.root, '#storageWarn').hasAttribute('hidden')).toBe(false);
    expect(q(r.root, '#storageLine').textContent).toContain('stockage persistant');
    expect(q(r.root, '#storageLine').textContent).toContain('85,0 Mo');
    const ok = await rig();
    expect(q(ok.root, '#storageWarn').hasAttribute('hidden')).toBe(true);
  });

  it('a cancelled camera shows a sentence and stores nothing', async () => {
    const r = await rig();
    type(r.root, '#v-lens', 'L01');
    click(r.root, '#v-shoot'); // no file: the chooser rejects
    await settle(r.root, 'Aucune photo reçue');
    expect(await stored(r)).toHaveLength(0);
  });
});
