// Builds the export ZIP parts. Each part is self-contained: its photos plus the CSVs for those photos.
import { MANIFEST_COLUMNS, OWN_LENSES_COLUMNS, RESULTS_COLUMNS, manifestRow, ownLensesRows, resultsRow, toCsv, type Meta } from './manifest';
import { MAX_PART_BYTES, buildZip, entryOverhead, planParts, type ZipEntry } from './zip';

export class ExportError extends Error {}

export interface ExportPart { fileName: string; data: Uint8Array; photoNames: string[] }

export const README_LINES = [
  "OptiFrame, collecte de données : ce ZIP contient les photos originales (dossier photos/, octets non modifiés) et manifest.csv (une ligne par photo, toutes les métadonnées).",
  "own_lenses.csv : les lectures au pied à coulisse par verre ; results.csv : ce que l'app a mesuré sur les photos de validation (une ligne par photo).",
  "Sur l'ordinateur : décompresser les ZIP dans training/_local/raw/ (photos d'entraînement : training/data/autolabel.py).",
  "Validation : ouvrir eval.html avec les photos de validation et own_lenses.csv, ou lancer tools/accuracy_report.py results.csv own_lenses.csv.",
  "Attention : results.csv a été mesuré avec le bias.json en ligne au moment de la photo. Si ce fichier n'est plus l'identité (0, 1, 0, 1), ne pas ajuster un nouveau biais sur ce results.csv : refaire les mesures avec eval.html et le bias.json identité.",
  "Aucune donnée personnelle n'est écrite dans les fichiers ; le téléphone garde les photos tant que « Vider les photos exportées » n'a pas été utilisé.",
];

export interface ExportOptions {
  /** Columns of data/own_lenses.template.csv when it was read. */
  ownLensesColumns?: readonly string[];
  limit?: number;
  now?: Date;
}

const enc = new TextEncoder();
const stamp = (d: Date) => d.toISOString().slice(0, 16).replace(/[-:]/g, '').replace('T', '-');

/** Refuses an empty export. `getBytes` is called one photo at a time, in order. */
export async function buildExportParts(
  metas: Meta[],
  getBytes: (name: string) => Promise<ArrayBuffer | undefined>,
  opts: ExportOptions = {},
): Promise<ExportPart[]> {
  if (!metas.length) throw new ExportError('Aucune photo à exporter.');
  const limit = opts.limit ?? MAX_PART_BYTES;
  const now = opts.now ?? new Date();
  const ownCols = opts.ownLensesColumns ?? OWN_LENSES_COLUMNS;
  const sorted = [...metas].sort((a, b) => a.takenAt.localeCompare(b.takenAt) || a.name.localeCompare(b.name));

  const readme = enc.encode(README_LINES.join('\n') + '\n');
  const csvs = (group: Meta[]) => ({
    manifest: enc.encode(toCsv(MANIFEST_COLUMNS, group.map(manifestRow))),
    own: enc.encode(toCsv(ownCols, ownLensesRows(group))),
    results: enc.encode(toCsv(RESULTS_COLUMNS, group.filter((m) => m.mode === 'validation').map(resultsRow))),
  });
  // Upper bound for every part: the CSVs of the whole export.
  const all = csvs(sorted);
  const fixed = readme.length + all.manifest.length + all.own.length + all.results.length
    + ['LISEZMOI.txt', 'manifest.csv', 'own_lenses.csv', 'results.csv'].reduce((s, n) => s + entryOverhead(n), 0);

  const groups = planParts(sorted.map((m) => ({ name: 'photos/' + m.name, size: m.bytes })), limit, fixed);
  const parts: ExportPart[] = [];
  for (let g = 0; g < groups.length; g++) {
    const group = groups[g].map((i) => sorted[i]);
    const entries: ZipEntry[] = [];
    for (const m of group) {
      const buf = await getBytes(m.name);
      if (!buf) throw new ExportError(`Photo introuvable : ${m.name}`);
      entries.push({ name: 'photos/' + m.name, data: new Uint8Array(buf) });
    }
    const c = csvs(group);
    entries.push({ name: 'manifest.csv', data: c.manifest }, { name: 'own_lenses.csv', data: c.own }, { name: 'results.csv', data: c.results }, { name: 'LISEZMOI.txt', data: readme });
    const suffix = groups.length > 1 ? `_partie${g + 1}sur${groups.length}` : '';
    parts.push({ fileName: `optiframe-collecte_${stamp(now)}${suffix}.zip`, data: buildZip(entries, now), photoNames: group.map((m) => m.name) });
  }
  return parts;
}
