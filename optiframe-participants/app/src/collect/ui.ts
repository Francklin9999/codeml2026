// The collect page. All services come in through `Deps` so a test can walk each mode with fakes.
import { OptiError, type Eye, type LensMeasurement, type Photo } from '../contracts';
import { messageFor } from '../quality';
import { buildExportParts, ExportError, type ExportPart } from './exporter';
import { inconsistent, ownLensesColumns, parseDecimal, refValue, signedError, spread, type Meta, type Readings } from './manifest';
import {
  conditionGrid, CONDITIONS, extensionFor, finalId, freeName, guessPhone, isValidId, MODE_LABEL, MODES, nextFreeIndex, nextRep,
  POSITIONS, sanitizeId, trainingName, validationName, type Condition, type Mode,
} from './naming';
import { StorageError, type PhotoStore, type StoredMeta } from './storage';

export interface Deps {
  store: PhotoStore;
  /** Opens the native camera (or gallery). Rejects with OptiError when cancelled or failed. */
  chooseFile(camera: boolean): Promise<File>;
  decode(file: File): Promise<Photo>;
  measure(photo: Photo, eye: Eye): Promise<LensMeasurement>;
  checkSheet(photo: Photo): Promise<{ nMarkers?: number }>;
  makeThumb(file: File): Promise<ArrayBuffer | undefined>;
  /** Web Share when allowed, otherwise a download. */
  save(data: Uint8Array, fileName: string): Promise<'shared' | 'saved' | 'cancelled'>;
  confirm(message: string): boolean;
  storage?: { persist?(): Promise<boolean>; estimate?(): Promise<{ usage?: number; quota?: number }> };
  local: { getItem(k: string): string | null; setItem(k: string, v: string): void };
  url: { create(b: Blob): string; revoke(u: string): void };
  userAgent: string;
  appVersion: string;
  now(): Date;
  /** Text of data/own_lenses.template.csv when the build included it. */
  ownLensesTemplate?: string;
}

const PRIVACY = "Pas de visages, pas de noms, pas d'ordonnances sur les photos.";
const PAIRED_RULE = 'Ne bougez ni le verre ni le téléphone entre deux photos.';
const GALLERY_PAGE = 60;
const WARN_RATIO = 0.8;

/** What a shot is for, before the file exists. */
interface Plan {
  mode: Mode; lensId: string; label?: string; tags?: string[]; eye?: Eye; phone: string;
  rep?: number; position?: number; condition?: string;
  description?: string; A?: Readings; B?: Readings; edgeThickness?: number | null; tint?: string; notes?: string;
  checkSheet: boolean;
}

const fr = (n: number, d = 2) => n.toFixed(d).replace('.', ',');
const signed = (n: number) => (n >= 0 ? '+' : '−') + fr(Math.abs(n));
const mb = (n: number) => fr(n / 1e6, 1);

export function mountCollect(root: HTMLElement, deps: Deps): { ready: Promise<void> } {
  const doc = root.ownerDocument;
  const el = <T extends HTMLElement>(sel: string): T => root.querySelector(sel) as T;
  const get = (k: string): string => { try { return deps.local.getItem('optiframe.collect.' + k) ?? ''; } catch { return ''; } };
  const set = (k: string, v: string) => { try { deps.local.setItem('optiframe.collect.' + k, v); } catch { /* private mode */ } };

  root.innerHTML = `
<header>
  <h1>Collecte de données</h1>
  <p class="fixed" id="privacy"></p>
  <p id="storageLine" aria-live="polite"></p>
  <p id="storageWarn" class="warn" hidden></p>
</header>
<nav role="tablist" id="tabs"></nav>

<section id="p-validation" data-mode="validation" hidden>
  <label>Verre <input id="v-lens" autocapitalize="characters" autocomplete="off" maxlength="32" placeholder="L01"></label>
  <label>Œil <select id="v-eye"><option value="R">Droit (R)</option><option value="L">Gauche (L)</option></select></label>
  <label>Téléphone <input id="v-phone" autocomplete="off" maxlength="32"></label>
  <label>Description <input id="v-desc" autocomplete="off" placeholder="ovale, clair"></label>
  <fieldset><legend>Pied à coulisse, A en mm (3 lectures)</legend>
    <div class="row3"><input id="v-a1" inputmode="decimal" aria-label="A1"><input id="v-a2" inputmode="decimal" aria-label="A2"><input id="v-a3" inputmode="decimal" aria-label="A3"></div>
    <p id="v-aspread" class="hint"></p></fieldset>
  <fieldset><legend>Pied à coulisse, B en mm (3 lectures)</legend>
    <div class="row3"><input id="v-b1" inputmode="decimal" aria-label="B1"><input id="v-b2" inputmode="decimal" aria-label="B2"><input id="v-b3" inputmode="decimal" aria-label="B3"></div>
    <p id="v-bspread" class="hint"></p></fieldset>
  <label>Épaisseur du bord (mm) <input id="v-edge" inputmode="decimal"></label>
  <label>Teinte <input id="v-tint" autocomplete="off" placeholder="clair, teinté, solaire"></label>
  <label>Notes <textarea id="v-notes" rows="2"></textarea></label>
  <button type="button" class="primary" id="v-shoot">Prendre la photo</button>
  <button type="button" id="v-gallery">Choisir dans la galerie</button>
</section>

<section id="p-training" data-mode="training" hidden>
  <p class="fixed" id="pairedRule"></p>
  <label>Verre <input id="t-lens" autocapitalize="characters" autocomplete="off" maxlength="32" placeholder="L01"></label>
  <label>Position du verre <select id="t-pos"></select></label>
  <p id="t-warn" class="warn" hidden></p>
  <div id="t-grid" class="grid"></div>
</section>

<section id="p-free" data-mode="free" hidden>
  <label>Étiquette <input id="f-label" autocomplete="off" maxlength="32" placeholder="SN-SF-paire3"></label>
  <label>Tags (séparés par des virgules) <input id="f-tags" autocomplete="off"></label>
  <label>Notes <textarea id="f-notes" rows="2"></textarea></label>
  <label class="check"><input type="checkbox" id="f-sheet"> Vérifier la feuille</label>
  <button type="button" class="primary" id="f-shoot">Prendre la photo</button>
  <button type="button" id="f-gallery">Choisir dans la galerie</button>
</section>

<section id="resultBox" class="result" aria-live="polite" hidden></section>

<section>
  <h2>Séance</h2>
  <p id="counts"></p>
  <div id="gallery" class="thumbs"></div>
  <button type="button" id="more" hidden>Afficher plus</button>
  <div id="detail" class="detail" hidden></div>
</section>

<section>
  <h2>Export</h2>
  <label class="check"><input type="checkbox" id="x-all"> Inclure les photos déjà exportées</label>
  <button type="button" class="primary" id="x-build">Exporter en ZIP</button>
  <div id="x-parts"></div>
  <p id="x-msg" aria-live="polite"></p>
  <button type="button" class="danger" id="x-clear">Vider les photos exportées</button>
</section>`;

  el('#privacy').textContent = PRIVACY;
  el('#pairedRule').textContent = PAIRED_RULE;

  // ---------- state ----------
  let records: StoredMeta[] = [];
  let mode: Mode = (MODES as readonly string[]).includes(get('mode')) ? (get('mode') as Mode) : 'validation';
  let busy = false;
  let shown = GALLERY_PAGE;
  let selected: string | null = null;
  let parts: { part: ExportPart; done: boolean }[] = [];
  let thumbUrls: string[] = [];

  // ---------- helpers ----------
  const input = (id: string) => el<HTMLInputElement>('#' + id);
  const text = (id: string, v: string) => { el('#' + id).textContent = v; };
  function remember(id: string, key: string, sanitise = false) {
    const i = input(id);
    const saved = get(key);
    if (saved) i.value = saved;
    i.addEventListener('input', () => {
      if (sanitise) {
        const s = sanitizeId(i.value);
        if (s !== i.value) i.value = s;
      }
      set(key, i.value);
    });
  }

  function showResult(lines: string[], kind: 'ok' | 'bad' | 'warn' = 'ok') {
    const box = el('#resultBox');
    box.hidden = false;
    box.className = 'result ' + kind;
    box.replaceChildren(...lines.map((l) => { const p = doc.createElement('p'); p.textContent = l; return p; }));
  }

  function errorCode(e: unknown): string {
    return e instanceof OptiError ? e.code : 'LOAD_FAILED';
  }

  // ---------- tabs ----------
  const tabs = el('#tabs');
  for (const m of MODES) {
    const b = doc.createElement('button');
    b.type = 'button';
    b.setAttribute('role', 'tab');
    b.dataset.mode = m;
    b.textContent = MODE_LABEL[m];
    b.addEventListener('click', () => setMode(m));
    tabs.append(b);
  }
  function setMode(m: Mode) {
    mode = m;
    set('mode', m);
    for (const b of tabs.querySelectorAll<HTMLElement>('button')) b.setAttribute('aria-selected', String(b.dataset.mode === m));
    for (const s of root.querySelectorAll<HTMLElement>('section[data-mode]')) s.hidden = s.dataset.mode !== m;
    el('#resultBox').hidden = true;
  }

  // ---------- fields ----------
  remember('v-lens', 'v.lens', true);
  remember('v-eye', 'v.eye');
  remember('v-phone', 'phone', true);
  if (!input('v-phone').value) input('v-phone').value = guessPhone(deps.userAgent);
  remember('t-lens', 't.lens', true);
  remember('f-label', 'f.label', true);
  const posSel = el<HTMLSelectElement>('#t-pos');
  for (const p of POSITIONS) posSel.append(new Option(String(p), String(p)));
  if (get('t.pos')) posSel.value = get('t.pos');
  posSel.addEventListener('change', () => { set('t.pos', posSel.value); renderGrid(); });
  input('t-lens').addEventListener('input', renderGrid);

  const readings = (ids: string[]): Readings => ids.map((id) => parseDecimal(input(id).value));
  const A_IDS = ['v-a1', 'v-a2', 'v-a3'], B_IDS = ['v-b1', 'v-b2', 'v-b3'];
  function renderSpread() {
    for (const [ids, out, name] of [[A_IDS, 'v-aspread', 'A'], [B_IDS, 'v-bspread', 'B']] as const) {
      const r = readings([...ids]);
      const s = spread(r.filter((x): x is number => x !== null));
      const p = el('#' + out);
      p.classList.toggle('warn', inconsistent(r));
      p.textContent = s === null ? '' : inconsistent(r)
        ? `${name} : écart ${fr(s)} mm, lectures incohérentes, refaire`
        : `${name} : écart ${fr(s)} mm, médiane ${fr(refValue(r)!)} mm`;
    }
  }
  for (const id of [...A_IDS, ...B_IDS]) input(id).addEventListener('input', renderSpread);

  // ---------- plans ----------
  function planValidation(): Plan | string {
    const lensId = finalId(input('v-lens').value);
    if (!isValidId(lensId)) return 'Identifiant du verre : lettres, chiffres et tirets seulement (pas de tiret bas).';
    const phone = finalId(input('v-phone').value);
    if (!isValidId(phone)) return 'Nom du téléphone : lettres, chiffres et tirets seulement.';
    return {
      mode: 'validation', lensId, phone, eye: el<HTMLSelectElement>('#v-eye').value as Eye,
      description: input('v-desc').value.trim(), A: readings(A_IDS), B: readings(B_IDS),
      edgeThickness: parseDecimal(input('v-edge').value), tint: input('v-tint').value.trim(), notes: el<HTMLTextAreaElement>('#v-notes').value.trim(),
      checkSheet: false,
    };
  }
  function planTraining(cond: Condition): Plan | string {
    const lensId = finalId(input('t-lens').value);
    if (!isValidId(lensId)) return 'Identifiant du verre : lettres, chiffres et tirets seulement (pas de tiret bas).';
    return { mode: 'training', lensId, phone: finalId(input('v-phone').value) || 'phone', position: Number(posSel.value), condition: cond, checkSheet: true };
  }
  function planFree(): Plan | string {
    const label = finalId(input('f-label').value);
    if (!isValidId(label)) return "Étiquette : lettres, chiffres et tirets seulement (pas de tiret bas).";
    return {
      mode: 'free', lensId: '', label, phone: finalId(input('v-phone').value) || 'phone',
      tags: input('f-tags').value.split(',').map((t) => t.trim()).filter(Boolean),
      notes: el<HTMLTextAreaElement>('#f-notes').value.trim(), checkSheet: input('f-sheet').checked,
    };
  }
  const planOf = (m: StoredMeta): Plan => ({
    mode: m.mode, lensId: m.lensId, label: m.label, tags: m.tags, eye: m.eye, phone: m.phone, rep: m.rep, position: m.position, condition: m.condition,
    description: m.description, A: m.A, B: m.B, edgeThickness: m.edgeThickness, tint: m.tint, notes: m.notes, checkSheet: !!m.sheet?.checked,
  });

  function fileNameFor(p: Plan, ext: string): string {
    if (p.mode === 'validation') return validationName(p.lensId, p.phone, p.rep!, ext);
    if (p.mode === 'training') return trainingName(p.lensId, p.position!, p.condition as Condition, ext);
    return freeName(p.label!, p.rep!, ext);
  }

  // ---------- the shot ----------
  /** First await is the file chooser: it must run inside the tap (iOS). */
  async function shoot(camera: boolean, plan: Plan | string, retake?: StoredMeta) {
    if (busy) return;
    if (typeof plan === 'string') return showResult([plan], 'bad');
    busy = true;
    try {
      let file: File;
      try { file = await deps.chooseFile(camera); }
      catch (e) {
        const c = errorCode(e);
        return showResult([c === 'LOAD_FAILED' ? "Aucune photo reçue (prise de vue annulée ?)." : messageFor(c as never)], 'warn');
      }
      showResult(['Analyse de la photo…'], 'warn');
      await processFile(file, plan, retake);
    } catch (e) {
      showResult([e instanceof StorageError ? e.message : "L'enregistrement a échoué. Réessayez."], 'bad');
    } finally {
      busy = false;
    }
  }

  async function processFile(file: File, plan: Plan, retake?: StoredMeta) {
    const ext = extensionFor(file.type);
    const p = { ...plan };
    if (p.rep === undefined && p.mode === 'validation') p.rep = nextRep(records, p.lensId, p.phone);
    if (p.rep === undefined && p.mode === 'free') p.rep = nextFreeIndex(records, p.label!);
    const name = fileNameFor(p, ext);
    const bytes = await file.arrayBuffer();

    const meta: StoredMeta = {
      name, mode: p.mode, lensId: p.lensId, label: p.label, tags: p.tags, eye: p.eye, phone: p.phone, rep: p.rep, position: p.position,
      condition: p.condition, description: p.description, A: p.A, B: p.B, edgeThickness: p.edgeThickness, tint: p.tint, notes: p.notes,
      takenAt: deps.now().toISOString(), bytes: bytes.byteLength, mime: file.type || 'image/jpeg', userAgent: deps.userAgent, appVersion: deps.appVersion, ok: false,
    };
    const lines: string[] = [];
    let kind: 'ok' | 'bad' | 'warn' = 'ok';
    let photo: Photo | null = null;
    try {
      photo = await deps.decode(file);
      meta.width = photo.image.width;
      meta.height = photo.image.height;
      meta.focal35mm = photo.focal35mm;
    } catch (e) {
      meta.errorCode = errorCode(e);
    }

    if (photo && p.mode === 'validation') {
      try {
        const m = await deps.measure(photo, p.eye!);
        meta.ok = true;
        meta.measured = { A: m.A, B: m.B, perimeter: m.perimeter, method: m.method, reprojErrMm: m.quality.reprojErrMm, sharpness: m.quality.sharpness };
        meta.sheet = { checked: true, ok: true };
        lines.push(`A ${fr(m.A)} mm · B ${fr(m.B)} mm · périmètre ${fr(m.perimeter)} mm`);
        const eA = signedError(m.A, p.A ?? []), eB = signedError(m.B, p.B ?? []);
        if (eA === null && eB === null) lines.push("Pas de lecture au pied à coulisse : erreur non calculée.");
        else lines.push(`Erreur (mesuré − pied à coulisse) : A ${eA === null ? 'n/a' : signed(eA) + ' mm'} · B ${eB === null ? 'n/a' : signed(eB) + ' mm'}`);
      } catch (e) {
        meta.errorCode = errorCode(e);
        meta.sheet = { checked: true, ok: false };
      }
    } else if (photo && p.checkSheet) {
      try {
        const s = await deps.checkSheet(photo);
        meta.ok = true;
        meta.sheet = { checked: true, ok: true, markers: s.nMarkers };
        lines.push(s.nMarkers === undefined ? 'Feuille détectée' : `Feuille détectée (${s.nMarkers} marqueurs)`);
      } catch (e) {
        meta.errorCode = errorCode(e);
        meta.sheet = { checked: true, ok: false };
      }
    } else if (photo) {
      meta.ok = true;
      meta.sheet = { checked: false, ok: false };
      lines.push('Photo enregistrée.');
    }
    if (meta.errorCode) {
      kind = 'bad';
      lines.push(messageFor(meta.errorCode as never), 'La photo est quand même conservée : un échec est une donnée.');
    }
    if (p.mode === 'training' && p.condition !== 'easy' && !hasCondition(p.lensId, p.position!, 'easy')) {
      kind = kind === 'ok' ? 'warn' : kind;
      lines.push("Attention : « easy » (rétro-éclairé) n'a pas été pris avant cette condition pour ce verre et cette position.");
    }
    lines.push('Enregistré : ' + name);

    const thumb = await deps.makeThumb(file).catch(() => undefined);
    if (thumb) meta.thumb = thumb;
    const existing = records.find((r) => r.name.toLowerCase() === name.toLowerCase());
    await deps.store.put(meta, bytes, !!existing || !!retake);
    if (retake && retake.name !== name) await deps.store.delete(retake.name);
    showResult(lines, kind);
    await refresh();
  }

  const hasCondition = (lensId: string, pos: number, cond: string) =>
    records.some((r) => r.mode === 'training' && r.lensId.toLowerCase() === lensId.toLowerCase() && r.position === pos && r.condition === cond);

  // ---------- training grid ----------
  function renderGrid() {
    const lensId = finalId(input('t-lens').value), pos = Number(posSel.value);
    const done = new Set(CONDITIONS.filter((c) => hasCondition(lensId, pos, c)));
    const grid = el('#t-grid');
    grid.replaceChildren();
    for (const g of conditionGrid(done)) {
      const b = doc.createElement('button');
      b.type = 'button';
      b.dataset.cond = g.cond;
      b.className = 'cond' + (g.done ? ' done' : '') + (g.cond === 'easy' ? ' primary' : '');
      b.textContent = (g.done ? '✓ ' : '') + g.cond;
      b.addEventListener('click', () => {
        const plan = planTraining(g.cond);
        if (typeof plan !== 'string' && g.done && !deps.confirm(`« ${g.cond} » existe déjà pour ce verre et cette position. La reprendre ?`)) return;
        void shoot(true, plan);
      });
      grid.append(b);
    }
    const warn = el('#t-warn');
    warn.hidden = done.has('easy') || !lensId;
    warn.textContent = "Prenez d'abord « easy » (écran blanc, rétro-éclairage) pour ce verre et cette position.";
  }

  // ---------- gallery ----------
  function renderGallery() {
    for (const u of thumbUrls) deps.url.revoke(u);
    thumbUrls = [];
    const g = el('#gallery');
    g.replaceChildren();
    const list = [...records].sort((a, b) => b.takenAt.localeCompare(a.takenAt));
    for (const m of list.slice(0, shown)) {
      const b = doc.createElement('button');
      b.type = 'button';
      b.className = 'thumb' + (m.ok ? '' : ' fail');
      b.dataset.name = m.name;
      if (m.thumb) {
        const img = doc.createElement('img');
        const u = deps.url.create(new Blob([m.thumb], { type: 'image/jpeg' }));
        thumbUrls.push(u);
        img.src = u;
        img.alt = m.name;
        img.width = 160;
        b.append(img);
      }
      const cap = doc.createElement('span');
      cap.textContent = m.name + (m.exportedAt ? ' · exporté' : '') + (m.ok ? '' : ' · échec');
      b.append(cap);
      b.addEventListener('click', () => { selected = m.name; renderDetail(); });
      g.append(b);
    }
    el('#more').hidden = list.length <= shown;

    const per = (key: (m: StoredMeta) => string) => {
      const c = new Map<string, number>();
      for (const m of records) c.set(key(m), (c.get(key(m)) ?? 0) + 1);
      return [...c.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([k, n]) => `${k} ${n}`).join(' · ');
    };
    const byMode = MODES.map((m) => `${MODE_LABEL[m]} ${records.filter((r) => r.mode === m).length}`).join(' · ');
    const byLens = per((m) => m.lensId || m.label || '?');
    text('counts', `${records.length} photo(s) · ${byMode}` + (byLens ? ` · Par verre : ${byLens}` : ''));
    renderDetail();
  }

  function renderDetail() {
    const d = el('#detail');
    const m = records.find((r) => r.name === selected);
    d.hidden = !m;
    d.replaceChildren();
    if (!m) return;
    const p = doc.createElement('p');
    p.textContent = `${m.name} · ${MODE_LABEL[m.mode]} · ${m.ok ? 'mesure ou feuille OK' : 'échec ' + (m.errorCode ?? '')}`;
    const mk = (label: string, cls: string, fn: () => void) => {
      const b = doc.createElement('button');
      b.type = 'button';
      b.textContent = label;
      b.className = cls;
      b.addEventListener('click', fn);
      return b;
    };
    d.append(
      p,
      mk('Reprendre cette photo', 'primary', () => void shoot(true, planOf(m), m)),
      mk('Supprimer', 'danger', async () => {
        if (!deps.confirm(`Supprimer ${m.name} ? Cette action est définitive.`)) return;
        await deps.store.delete(m.name);
        selected = null;
        await refresh();
      }),
      mk('Fermer', '', () => { selected = null; renderDetail(); }),
    );
  }
  el('#more').addEventListener('click', () => { shown += GALLERY_PAGE; renderGallery(); });

  // ---------- storage line ----------
  async function renderStorage() {
    const info: string[] = [`${records.length} photo(s)`];
    let warn = '';
    try {
      const e = await deps.storage?.estimate?.();
      if (e?.usage !== undefined && e.quota) {
        info.push(`${mb(e.usage)} Mo utilisés sur ${mb(e.quota)} Mo`);
        if (e.usage / e.quota > WARN_RATIO) warn = "Le stockage du téléphone est presque plein (plus de 80 %). Exportez puis videz les photos exportées.";
      }
    } catch { /* estimate is optional */ }
    text('storageLine', info.join(' · ') + (persisted === undefined ? '' : persisted ? ' · stockage persistant' : ' · stockage non persistant'));
    const w = el('#storageWarn');
    w.hidden = !warn;
    w.textContent = warn;
  }
  let persisted: boolean | undefined;

  async function refresh() {
    records = await deps.store.list();
    renderGrid();
    renderGallery();
    await renderStorage();
    el('#x-build').textContent = `Exporter en ZIP (${records.filter((r) => !r.exportedAt).length} nouvelle(s))`;
  }

  // ---------- buttons ----------
  el('#v-shoot').addEventListener('click', () => void shoot(true, planValidation()));
  el('#v-gallery').addEventListener('click', () => void shoot(false, planValidation()));
  el('#f-shoot').addEventListener('click', () => void shoot(true, planFree()));
  el('#f-gallery').addEventListener('click', () => void shoot(false, planFree()));

  // ---------- export ----------
  function renderParts() {
    const box = el('#x-parts');
    box.replaceChildren();
    parts.forEach((entry, i) => {
      const b = doc.createElement('button');
      b.type = 'button';
      b.className = 'part';
      b.textContent = `${entry.done ? '✓ ' : ''}Enregistrer ou partager la partie ${i + 1}/${parts.length} (${mb(entry.part.data.length)} Mo)`;
      b.addEventListener('click', async () => {
        try {
          const r = await deps.save(entry.part.data, entry.part.fileName);
          if (r === 'cancelled') return;
          await deps.store.markExported(entry.part.photoNames, deps.now().toISOString());
          entry.done = true;
          text('x-msg', `Partie ${i + 1} ${r === 'shared' ? 'partagée' : 'enregistrée'}. Les photos sont marquées exportées.`);
          renderParts();
          await refresh();
        } catch {
          text('x-msg', "L'enregistrement du ZIP a échoué.");
        }
      });
      box.append(b);
    });
  }
  el('#x-build').addEventListener('click', async () => {
    if (busy) return;
    busy = true;
    try {
      const all = input('x-all').checked;
      const list = records.filter((r) => all || !r.exportedAt);
      text('x-msg', 'Préparation du ZIP…');
      parts = (await buildExportParts(list, (n) => deps.store.getBytes(n), { ownLensesColumns: ownLensesColumns(deps.ownLensesTemplate), now: deps.now() })).map((part) => ({ part, done: false }));
      text('x-msg', `${list.length} photo(s) en ${parts.length} ZIP. Enregistrez chaque partie.`);
      renderParts();
    } catch (e) {
      parts = [];
      renderParts();
      text('x-msg', e instanceof ExportError ? (records.length ? "Rien à exporter : tout est déjà exporté (cochez la case pour tout réexporter)." : e.message) : "La préparation du ZIP a échoué.");
    } finally {
      busy = false;
    }
  });
  el('#x-clear').addEventListener('click', async () => {
    const n = records.filter((r) => r.exportedAt).length;
    if (!n) return text('x-msg', 'Aucune photo exportée à vider.');
    if (!deps.confirm(`Supprimer ${n} photo(s) déjà exportée(s) de ce téléphone ? Les ZIP doivent être copiés sur l'ordinateur. Cette action est définitive.`)) return;
    try {
      const k = await deps.store.deleteExported();
      text('x-msg', `${k} photo(s) supprimée(s).`);
      await refresh();
    } catch (e) {
      text('x-msg', e instanceof StorageError ? e.message : 'La suppression a échoué.');
    }
  });

  // ---------- start ----------
  setMode(mode);
  renderSpread();
  const ready = (async () => {
    try { persisted = await deps.storage?.persist?.(); } catch { persisted = undefined; }
    try { await refresh(); } catch (e) { text('storageLine', e instanceof StorageError ? e.message : 'Stockage indisponible.'); }
  })();
  return { ready };
}
