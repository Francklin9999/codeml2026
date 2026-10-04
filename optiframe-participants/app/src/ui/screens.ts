import { DEFAULT_FRAME, type Eye, type FrameResult, type LensMeasurement, type Pt } from '../contracts';
import { messageFor } from '../quality';
import { rotationWarningDeg } from '../measure';
import { canvasOf, fmt1, h, maskImage, paintImage, strokePolygon } from './dom';
import { BRIDGE_MAX_MM, BRIDGE_MIN_MM, SHOTS_PER_LENS, type State } from './state';

export interface Actions {
  chooseEye(eye: Eye): void;
  takePhoto(): void;
  importPhoto(): void;
  finishShots(): void;
  exportSvg(): void;
  retake(): void;
  validate(): void;
  goHome(): void;
  showSteps(): void;
  openFrame(): void;
  setBridge(mm: number): void;
  downloadStl(): void;
  downloadJson(): void;
}

const eyeName = (e: Eye) => (e === 'L' ? 'Verre gauche' : 'Verre droit');
const btn = (label: string, onclick: () => void, kind = '', disabled = false) =>
  h('button', { type: 'button', class: ('btn ' + kind).trim(), onclick, disabled }, label);

/** Spread of a list of values: max minus min. */
const range = (v: number[]) => (v.length ? Math.max(...v) - Math.min(...v) : 0);

export function homeView(s: State, a: Actions): HTMLElement {
  const eyeButton = (eye: Eye) => {
    const done = !!s.lenses[eye];
    return h('button', { type: 'button', class: 'btn eye' + (done ? ' done' : ''), 'data-eye': eye, onclick: () => a.chooseEye(eye) },
      h('span', null, eyeName(eye)), h('span', { class: 'status' }, done ? 'fait ✓' : 'à faire'));
  };
  return h('section', { class: 'screen', 'data-screen': 'home' },
    h('h1', null, 'OptiFrame'),
    h('p', { class: 'lead' }, 'Photographiez un verre de lunettes posé sur la feuille de référence : l’application mesure son contour et prépare une monture à imprimer en 3D.'),
    h('details', { class: 'install' },
      h('summary', null, 'Comment installer le dispositif'),
      h('ol', null,
        h('li', null, 'Imprimez la feuille de référence à 100 % (taille réelle, jamais « ajuster à la page »).'),
        h('li', null, 'Découpez la fenêtre, ou laissez-la blanche sur un film transparent.'),
        h('li', null, 'Ouvrez la page de rétro-éclairage sur un ordinateur ou une tablette, en plein écran, luminosité au maximum.'),
        h('li', null, 'Posez la feuille à plat sur l’écran, la fenêtre au centre, puis le verre dans la fenêtre.')),
      h('p', null, h('a', { href: './lightbox.html' }, 'Page de rétro-éclairage'))),
    h('div', { class: 'stack' }, eyeButton('L'), eyeButton('R')),
    s.lenses.L && s.lenses.R ? btn('Créer la monture', a.openFrame, 'primary') : null,
    s.last ? btn('Pas à pas (dernière photo)', a.showSteps, 'secondary') : null,
    h('p', { class: 'tiny' }, h('a', { href: './collect.html' }, 'Collecte de données (équipe)')));
}

/** Where the nose goes for this eye: right eye +x (right of the sheet), left eye -x. */
function nosePictogram(eye: Eye): HTMLElement {
  const right = eye === 'R';
  const x0 = right ? 112 : 48;
  const x1 = right ? 148 : 12;
  const head = right ? `${x1 - 8},44 ${x1},50 ${x1 - 8},56` : `${x1 + 8},44 ${x1},50 ${x1 + 8},56`;
  const label = right ? 'à droite' : 'à gauche';
  const wrap = h('div', { class: 'picto' });
  wrap.innerHTML = `<svg viewBox="0 0 160 100" role="img" aria-label="Côté du nez ${label} de la fenêtre" xmlns="http://www.w3.org/2000/svg">
    <rect x="6" y="6" width="148" height="88" rx="6" fill="#fff" stroke="#333" stroke-width="2"/>
    <ellipse cx="80" cy="50" rx="32" ry="26" fill="#e8eef9" stroke="#0b5fff" stroke-width="3"/>
    <line x1="${x0}" y1="50" x2="${x1}" y2="50" stroke="#c4380b" stroke-width="3"/>
    <polygon points="${head}" fill="#c4380b"/>
    <text x="${right ? 146 : 14}" y="38" text-anchor="${right ? 'end' : 'start'}" font-size="11" fill="#c4380b" font-family="system-ui, sans-serif">nez</text>
  </svg>`;
  return wrap;
}

export function captureView(s: State, a: Actions): HTMLElement {
  const eye = s.eye!;
  const taken = s.shots.length;
  const spread = taken >= 2 ? { A: range(s.shots.map((m) => m.A)), B: range(s.shots.map((m) => m.B)) } : null;
  const busy = !!s.busy;
  return h('section', { class: 'screen', 'data-screen': 'capture' },
    h('h1', null, eyeName(eye)),
    nosePictogram(eye),
    h('p', null, eye === 'R'
      ? 'Posez le verre à plat au centre de la fenêtre, le côté du nez (flèche) à droite.'
      : 'Posez le verre à plat au centre de la fenêtre, le côté du nez (flèche) à gauche.'),
    taken ? h('div', { class: 'counter' },
      h('p', { class: 'count' }, `photo ${taken} sur ${SHOTS_PER_LENS}`),
      h('p', null, 'Bougez légèrement le téléphone avant la photo suivante.'),
      spread ? h('p', { class: 'spread' }, `Écart entre les photos : A ${fmt1(spread.A)} mm, B ${fmt1(spread.B)} mm`) : null) : null,
    s.hint ? h('p', { class: 'hint', role: 'note' }, messageFor(s.hint)) : null,
    h('div', { class: 'stack' },
      btn('Prendre la photo', a.takePhoto, 'primary', busy),
      btn('Importer une photo', a.importPhoto, 'secondary', busy),
      taken ? btn(`Terminer avec ${taken} photo${taken > 1 ? 's' : ''}`, a.finishShots, '', busy) : null,
      btn('Retour', a.goHome, 'link', busy)));
}

export function resultView(s: State, a: Actions): HTMLElement {
  const m = s.fused!;
  const control = canvasOf('Image redressée avec le contour mesuré');
  const rect = s.last?.steps.rectified;
  if (rect) {
    const ctx = paintImage(control, rect);
    if (ctx) strokePolygon(ctx, m.contourMm, control.width / (rect.width / 10), '#e0115f', 2);
  }
  const rotation = rotationWarningDeg(m);
  const spreadLine = m.quality.nShots > 1
    ? h('p', { class: 'spread' }, `Écart entre les ${m.quality.nShots} photos : A ${fmt1(m.quality.spreadA)} mm, B ${fmt1(m.quality.spreadB)} mm`)
    : h('p', { class: 'spread' }, '1 photo : pas d’écart à afficher.');
  return h('section', { class: 'screen', 'data-screen': 'result' },
    h('h1', null, `${eyeName(m.eye)} : résultat`),
    rect ? control : null,
    h('dl', { class: 'values' },
      h('dt', null, 'A (largeur)'), h('dd', { 'data-value': 'A' }, `${fmt1(m.A)} mm`),
      h('dt', null, 'B (hauteur)'), h('dd', { 'data-value': 'B' }, `${fmt1(m.B)} mm`),
      h('dt', null, 'Périmètre'), h('dd', { 'data-value': 'perimeter' }, `${fmt1(m.perimeter)} mm`)),
    spreadLine,
    rotation !== null ? h('p', { class: 'hint', role: 'note' }, messageFor('LENS_ROTATED')) : null,
    h('div', { class: 'stack' },
      btn('Exporter le contour (SVG 1:1)', a.exportSvg, 'secondary'),
      btn('Valider', a.validate, 'primary'),
      btn('Reprendre', a.retake),
      s.last ? btn('Pas à pas', a.showSteps, 'link') : null));
}

export function stepsView(s: State, a: Actions): HTMLElement {
  const root = h('section', { class: 'screen', 'data-screen': 'steps' }, h('h1', null, 'Pas à pas'));
  const last = s.last;
  if (!last) {
    root.append(h('p', null, 'Pas encore de photo mesurée.'));
  } else {
    const { photo, steps } = last;
    const fig = (n: string, caption: string, c: HTMLCanvasElement) => h('figure', null, c, h('figcaption', null, `${n}. ${caption}`));
    const original = canvasOf('Photo d’origine avec les marqueurs');
    const ctx = paintImage(original, photo.image);
    if (ctx) for (const quad of steps.markers) strokePolygon(ctx, quad, original.width / photo.image.width, '#14a44d', 3);
    const rectified = canvasOf('Image redressée');
    paintImage(rectified, steps.rectified);
    const mask = canvasOf('Masque du verre');
    paintImage(mask, maskImage(steps.mask.data, steps.mask.width, steps.mask.height));
    const contour = canvasOf('Contour mesuré sur l’image redressée');
    const cctx = paintImage(contour, steps.rectified);
    if (cctx) strokePolygon(cctx, last.result.contourMm, contour.width / (steps.rectified.width / 10), '#e0115f', 2);
    root.append(
      fig('1', 'Photo d’origine, marqueurs de la feuille placés avec la matrice calculée', original),
      fig('2', 'Image redressée (10 px par mm)', rectified),
      fig('3', `Masque du verre (méthode ${steps.mask.method === 'model' ? 'modèle' : 'classique'})`, mask),
      fig('4', 'Contour mesuré', contour));
  }
  root.append(btn('Retour', a.goHome, 'link'));
  return root;
}

// ---- Frame screen -----------------------------------------------------------------------------

export interface FrameView {
  el: HTMLElement;
  preview: HTMLElement;
  /** Replaces the 2D overlay and the numbers once a frame is ready. */
  showFrame(f: FrameResult): void;
  setBusy(on: boolean): void;
}

function bbox(p: Pt[]) {
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const [x, y] of p) { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); }
  return { x0, y0, x1, y1, cx: (x0 + x1) / 2, cy: (y0 + y1) / 2 };
}
const path = (p: Pt[], dx = 0, dy = 0) => 'M' + p.map(([x, y]) => `${(x + dx).toFixed(2)} ${(y + dy).toFixed(2)}`).join('L') + 'Z';

/** Static 2D check, in mm: outer rim, seat and measured contour (moved onto its seat). */
export function overlayMarkup(f: FrameResult, lenses: Partial<Record<Eye, LensMeasurement>>, rimMm: number): string {
  const seats: [Eye, Pt[]][] = [['R', f.seatR], ['L', f.seatL]];
  const all = bbox([...f.seatR, ...f.seatL]);
  const pad = rimMm + 2;
  const vb = `${(all.x0 - pad).toFixed(1)} ${(all.y0 - pad).toFixed(1)} ${(all.x1 - all.x0 + 2 * pad).toFixed(1)} ${(all.y1 - all.y0 + 2 * pad).toFixed(1)}`;
  let rim = '', seat = '', contour = '';
  for (const [eye, s] of seats) {
    // The outer rim is the seat grown by the rim width: a stroke of twice that width centred on the seat edge.
    rim += `<path d="${path(s)}" fill="none" stroke="#9aa3b2" stroke-width="${(2 * rimMm).toFixed(2)}" stroke-linejoin="round"/>`;
    seat += `<path d="${path(s)}" fill="#fff" stroke="#333" stroke-width="0.4"/>`;
    const m = lenses[eye];
    if (m) {
      const b = bbox(s), c = bbox(m.contourMm);
      contour += `<path d="${path(m.contourMm, b.cx - c.cx, b.cy - c.cy)}" fill="none" stroke="#e0115f" stroke-width="0.5"/>`;
    }
  }
  return `<svg viewBox="${vb}" role="img" aria-label="Contours mesurés, logements et bord extérieur de la monture" xmlns="http://www.w3.org/2000/svg">${rim}${seat}${contour}</svg>`;
}

export function frameView(s: State, a: Actions): FrameView {
  const preview = h('div', { class: 'preview', 'aria-label': 'Aperçu 3D de la monture' });
  const overlay = h('div', { class: 'overlay' });
  const gap = h('p', { class: 'gap' });
  const value = h('output', { for: 'bridge' }, `${fmt1(s.bridgeMm)} mm`);
  const slider = h('input', {
    id: 'bridge', type: 'range', min: BRIDGE_MIN_MM, max: BRIDGE_MAX_MM, step: 0.5, value: s.bridgeMm,
    oninput: (e: Event) => { const v = Number((e.target as HTMLInputElement).value); value.textContent = `${fmt1(v)} mm`; a.setBridge(v); },
  });
  const stl = btn('Télécharger monture.stl', a.downloadStl, 'primary', true);
  const json = btn('Télécharger les mesures', a.downloadJson, 'secondary');
  const busy = h('p', { class: 'note', role: 'status' }, 'Je génère la monture…');
  const el = h('section', { class: 'screen', 'data-screen': 'frame' },
    h('h1', null, 'Monture'),
    h('label', { for: 'bridge', class: 'slider' }, 'Largeur du pont : ', value),
    slider,
    preview,
    h('h2', null, 'Vérifier'),
    overlay,
    h('p', { class: 'legend tiny' }, 'Rouge : contour mesuré. Blanc : logement du verre. Gris : bord extérieur de la monture.'),
    gap,
    busy,
    h('div', { class: 'stack' }, stl, json, btn('Retour', a.goHome, 'link')));
  return {
    el, preview,
    showFrame(f) {
      overlay.innerHTML = overlayMarkup(f, s.lenses, DEFAULT_FRAME.rimWidthMm);
      gap.textContent = `Jeu entre le verre et son logement : ${fmt1(f.gapMm)} mm`;
      stl.disabled = false;
    },
    setBusy(on) { busy.hidden = !on; },
  };
}
