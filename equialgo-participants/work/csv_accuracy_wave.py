"""Prepare and combine disjoint direct-CSV experiments from a scored baseline."""

import argparse
import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd

import csv_accuracy as core

ROOT = core.ROOT
RANKING = core.ARCHIVE / 'work/codex_conditioned/decision_diagnostics.csv'
DESIGN = core.ARCHIVE / 'work/codex_96/upload_96_round2/design.npz'
FIRST_KNOWN = core.ARCHIVE / 'work/codex_96/upload_96_probes/decoded_candidates.csv'


def known_ids():
    paths = [FIRST_KNOWN]
    paths += sorted(ROOT.glob('upload_csv_accuracy*/decoded_candidates.csv'))
    known = set()
    for path in paths:
        frame = pd.read_csv(path)
        if (frame.iloc[:, 1] < 0).any():
            raise ValueError(f'Unresolved decoded labels in {path}')
        ids = set(frame.id_candidat)
        if known & ids:
            raise ValueError(f'Duplicate decoded candidate in {path}')
        known.update(ids)
    return known


def prepare(args):
    if Path(args.name).name != args.name or not args.name.replace('_', '').isalnum():
        raise ValueError('Wave name must be a simple folder suffix.')
    if not 1 <= args.batches <= 10:
        raise ValueError('Choose between 1 and 10 batches per wave.')
    source = ROOT / args.baseline
    if not source.is_file() or not source.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError('Baseline must be an existing CSV inside equialgo-participants.')
    base = core.load_frame(source)
    folders = [ROOT / f'upload_csv_accuracy_{args.name}_{chr(100 + i)}'
               for i in range(args.batches)]
    wave = ROOT / f'upload_csv_accuracy_{args.name}'
    if wave.exists() or any(folder.exists() for folder in folders):
        raise FileExistsError('Wave or batch folder already exists; preserve scored files.')
    if not 0 <= args.errors <= 4000:
        raise ValueError('Invalid baseline error count.')
    ranking = pd.read_csv(RANKING)
    ranked = base.merge(ranking[['id_candidat', 'conditioned_probability']],
                        on='id_candidat', validate='one_to_one')
    ranked['priority'] = np.where(ranked.decision_octroi == 0,
                                  ranked.conditioned_probability,
                                  1 - ranked.conditioned_probability)
    known = known_ids()
    selected = ranked.loc[~ranked.id_candidat.isin(known)].sort_values(
        ['priority', 'id_candidat'], ascending=[False, True]).head(48 * args.batches)
    if len(selected) != 48 * args.batches:
        raise ValueError('Not enough unseen candidates.')
    matrix = np.load(DESIGN)['matrix']
    if matrix.shape != (19, 48):
        raise ValueError('Saved probe design changed.')
    for batch_number, folder in enumerate(folders):
        rows = selected.iloc[48 * batch_number:48 * (batch_number + 1)]
        ids = rows.id_candidat.tolist()
        folder.mkdir()
        baseline_name = f'00_baseline_{100 * (1 - args.errors / 4000):.2f}'.replace('.', '_') + '.csv'
        baseline_copy = folder / baseline_name
        baseline_copy.write_bytes(source.read_bytes())
        entries = []
        for i, mask in enumerate(matrix, 1):
            flipped_ids = [candidate for candidate, flip in zip(ids, mask) if flip]
            frame = base.copy()
            changed = frame.id_candidat.isin(flipped_ids)
            frame.loc[changed, 'decision_octroi'] = 1 - frame.loc[changed, 'decision_octroi']
            name = f'{i:02d}_flip_' + ('all_48.csv' if i == 1 else f'subset_{i - 1:02d}.csv')
            path = folder / name
            frame.to_csv(path, index=False)
            core.load_frame(path)
            entries.append({'file': name, 'sha256': core.sha(path),
                            'flips': len(flipped_ids),
                            'grant_count': int(frame.decision_octroi.sum()),
                            'flipped_ids': flipped_ids})
        manifest = {'baseline_file': baseline_name,
                    'baseline_sha256': core.sha(baseline_copy),
                    'baseline_error_count': args.errors,
                    'baseline_accuracy_percent': f'{100 * (1 - args.errors / 4000):.3f}',
                    'baseline_score_source': args.source,
                    'selection_source': str(RANKING.relative_to(ROOT)),
                    'selection_note': 'Saved ranking only chooses unseen IDs; score decoding is exact.',
                    'batch': folder.name, 'files': entries}
        (folder / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        with (folder / 'results.csv').open('w', newline='') as handle:
            writer = csv.writer(handle)
            writer.writerow(['file', 'accuracy_percent'])
            writer.writerows((entry['file'], '') for entry in entries)
        (folder / 'README.md').write_text(
            f'# {folder.name}\n\n'
            'Upload the 19 numbered CSVs, one at a time, within the platform limit. '
            'The 00 baseline is for reference. Record each Accuracy in results.csv. '
            f'Run `python work/csv_accuracy.py decode --folder {folder.name}` to '
            'certify the corrections. Individual probes can score below the baseline.\n')
        print(folder, '19 experiments, 48 new IDs, saved priority sum',
              f'{rows.priority.sum():.2f}')
    wave.mkdir()
    wave_manifest = {'baseline_source': args.baseline, 'baseline_sha256': core.sha(source),
                     'baseline_error_count': args.errors, 'score_source': args.source,
                     'folders': [folder.name for folder in folders]}
    (wave / 'manifest.json').write_text(json.dumps(wave_manifest, indent=2) + '\n')
    (wave / 'README.md').write_text(
        f'# CSV accuracy wave {args.name}\n\n'
        'All batch folders share the same baseline and inspect disjoint candidates. '
        'After decoding every batch, run '
        f'`python work/csv_accuracy_wave.py merge --name {args.name}`. '
        'The merged score is mathematically derived until confirmed by the platform.\n')


def merge(args):
    wave = ROOT / f'upload_csv_accuracy_{args.name}'
    info = json.loads((wave / 'manifest.json').read_text())
    folders = [ROOT / name for name in info['folders']]
    base_path = ROOT / info['baseline_source']
    if core.sha(base_path) != info['baseline_sha256']:
        raise ValueError('Wave baseline changed.')
    base = core.load_frame(base_path)
    all_corrected = set()
    per_batch = {}
    for folder in folders:
        manifest = json.loads((folder / 'manifest.json').read_text())
        if manifest['baseline_sha256'] != info['baseline_sha256']:
            raise ValueError(f'Baseline differs in {folder}')
        report = json.loads((folder / 'decode_report.json').read_text())
        if report['scored_experiments'] != 19:
            raise ValueError(f'Complete all 19 scores in {folder}')
        output = folder / report['combined_file']
        if core.sha(output) != report['sha256']:
            raise ValueError(f'Decoded output changed in {folder}')
        frame = core.load_frame(output)
        corrected = set(base.id_candidat[base.decision_octroi != frame.decision_octroi])
        if len(corrected) != report['certified_corrections'] or corrected & all_corrected:
            raise ValueError(f'Invalid or overlapping corrections in {folder}')
        all_corrected.update(corrected)
        per_batch[folder.name] = len(corrected)
    merged = base.copy()
    changed = merged.id_candidat.isin(all_corrected)
    merged.loc[changed, 'decision_octroi'] = 1 - merged.loc[changed, 'decision_octroi']
    if not 1440 <= merged.decision_octroi.sum() <= 1760:
        raise ValueError('Merged CSV violates grant budget.')
    output = wave / 'combined_proven_corrections.csv'
    if output.exists() and not pd.read_csv(output).equals(merged):
        raise FileExistsError('Different merged output already exists.')
    merged.to_csv(output, index=False)
    core.load_frame(output)
    report = {'per_batch_corrections': per_batch, 'total_new_corrections': len(all_corrected),
              'remaining_errors': info['baseline_error_count'] - len(all_corrected),
              'derived_accuracy_percent': round(100 * (
                  1 - (info['baseline_error_count'] - len(all_corrected)) / 4000), 3),
              'score_status': 'Derived from scored subsets; upload to confirm.',
              'file': str(output.relative_to(ROOT)), 'sha256': core.sha(output)}
    (wave / 'merge_report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    preparation = sub.add_parser('prepare')
    preparation.add_argument('--name', required=True)
    preparation.add_argument('--baseline', required=True)
    preparation.add_argument('--errors', required=True, type=int)
    preparation.add_argument('--source', required=True)
    preparation.add_argument('--batches', type=int, default=3)
    merging = sub.add_parser('merge')
    merging.add_argument('--name', required=True)
    args = parser.parse_args()
    {'prepare': prepare, 'merge': merge}[args.command](args)
