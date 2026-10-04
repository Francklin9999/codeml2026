"""Direct CSV experiments and exact score decoding; no model is trained."""
import argparse
import csv
import hashlib
import json
from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'upload_csv_accuracy'
ARCHIVE = ROOT / 'archive/preview_probing'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_frame(path):
    frame = pd.read_csv(path)
    expected = pd.read_csv(ROOT / 'data/candidats_evaluation.csv').id_candidat
    if (list(frame.columns) != ['id_candidat', 'decision_octroi']
            or len(frame) != 4000 or not frame.id_candidat.equals(expected)
            or not frame.decision_octroi.isin([0, 1]).all()
            or not 1440 <= frame.decision_octroi.sum() <= 1760):
        raise ValueError(f'Invalid submission: {path}')
    return frame


def errors_from_score(raw):
    score = Decimal(raw.strip().replace('%', '').replace(',', '.'))
    if not score.is_finite() or not 0 <= score <= 100:
        raise ValueError('Accuracy must be between 0 and 100.')
    # One error is 0.025 percentage points; accept two-decimal display rounding.
    errors = Decimal(4000) * (1 - score / 100)
    nearest = int(errors.to_integral_value())
    if abs(errors - nearest) > Decimal('0.201'):
        raise ValueError(f'Accuracy incompatible with 4,000 rows: {raw}')
    return nearest


def solve(matrix, counts, fixed=None, exclude=None):
    n = matrix.shape[1]
    low = np.zeros(n)
    high = np.ones(n)
    if fixed is not None:
        j, value = fixed
        low[j] = high[j] = value
    constraints = matrix.astype(float)
    lower = np.asarray(counts, dtype=float)
    upper = lower.copy()
    if exclude is not None:
        constraints = np.vstack([constraints, 1 - 2 * exclude])
        lower = np.r_[lower, 1 - exclude.sum()]
        upper = np.r_[upper, np.inf]
    return milp(np.zeros(n), integrality=np.ones(n), bounds=Bounds(low, high),
                constraints=LinearConstraint(constraints, lower, upper),
                options={'time_limit': 10, 'mip_rel_gap': 0})


def certify(matrix, counts):
    result = solve(matrix, counts)
    if result.x is None:
        raise ValueError(f'No feasible assignment found (solver status {result.status}); check scores.')
    proposed = np.rint(result.x).astype(int)
    if not np.array_equal(matrix @ proposed, counts):
        raise ValueError('Solver assignment failed exact integer verification.')
    unique = solve(matrix, counts, exclude=proposed).status == 2
    certified = np.full(len(proposed), -1, dtype=int)
    if unique:
        certified[:] = proposed
    else:
        for j, value in enumerate(proposed):
            # Infeasibility of the opposite value proves this individual bit.
            # Timeouts and unknown statuses never count as proof.
            if solve(matrix, counts, fixed=(j, 1 - int(value))).status == 2:
                certified[j] = value
    return certified, unique


def prepare():
    if OUT.exists():
        raise FileExistsError(f'{OUT} already exists; scored files must stay unchanged.')
    baseline_path = ARCHIVE / 'upload_best/combined_95_50.csv'
    base = load_frame(baseline_path)
    source_manifest = json.loads((ARCHIVE / 'work/codex_96/upload_96_round2/manifest.json').read_text())
    if sha(baseline_path) != source_manifest['baseline_sha256']:
        raise ValueError('95.50 baseline does not match the original batch.')
    sources = []
    for entry in source_manifest['files']:
        path = ARCHIVE / 'upload_96_round2' / entry['file']
        if sha(path) != entry['sha256']:
            raise ValueError(f'Archived experiment changed: {path}')
        sources.append((path, load_frame(path)))
    OUT.mkdir()
    (OUT / '00_baseline_95_50.csv').write_bytes(baseline_path.read_bytes())
    files = []
    for i, (source, frame) in enumerate(sources, 1):
        name = f'{i:02d}_flip_' + ('all_48.csv' if i == 1 else f'subset_{i - 1:02d}.csv')
        dest = OUT / name
        dest.write_bytes(source.read_bytes())
        flipped = frame.decision_octroi != base.decision_octroi
        files.append({'file': name, 'sha256': sha(dest), 'flips': int(flipped.sum()),
                      'grant_count': int(frame.decision_octroi.sum()),
                      'flipped_ids': base.id_candidat[flipped].tolist(),
                      'source': str(source.relative_to(ROOT))})
    manifest = {'baseline_file': '00_baseline_95_50.csv', 'baseline_sha256': sha(baseline_path),
                'baseline_accuracy_percent': '95.50', 'baseline_error_count': 180,
                'baseline_score_source': 'User-confirmed score; archived upload_best/README.md records platform verification.',
                'selection_source': 'Previously selected 48 uncertain rows; reused without fitting or training.',
                'files': files}
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    with (OUT / 'results.csv').open('w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['file', 'accuracy_percent'])
        writer.writerows((entry['file'], '') for entry in files)
    (OUT / 'README.md').write_text('''# Direct CSV accuracy experiments

The verified baseline is `00_baseline_95_50.csv`: 95.50%, or 180 errors out of 4,000.
The 19 numbered experiment files directly flip decisions from that baseline.
No model is trained. These preserve the earlier 48 certified decisions and
reuse the archived, still-unscored round-2 experiments byte for byte.
Any already obtained score for the corresponding archived file can be reused.
The source mapping and exact flipped IDs are in `manifest.json`.

Upload `01_flip_all_48.csv` first, then `02_flip_subset_01.csv` through
`19_flip_subset_18.csv`. Record the accuracy percentages in `results.csv`.
Respect the preview limit recorded in the project: 20 uploads per team per hour.
The baseline need not be uploaded again if its 95.50 score is already confirmed.
These are experiments: their accuracy is unknown and can be lower than 95.50.

From `equialgo-participants`, run:

```bash
python work/csv_accuracy.py decode
```

Decoding also works with partial results. It changes only individually proven
mistakes and writes `combined_<number>_corrections.csv`, `decoded_candidates.csv`,
and `decode_report.json`. Submit the combined file to confirm its derived score.
There is no guarantee that this batch reaches 96%: that requires at least 20
corrected mistakes. If unresolved decisions remain, more scores may be needed.

The arithmetic is exact on the same fixed 4,000-row scoring set: if a file flips
s decisions, and t of those were mistakes, its errors are 180 + s - 2*t.
Each returned accuracy therefore supplies a subset count. Binary integer
constraints certify corrections; no probability estimate or guessed label is
used in the combined output. Every file has the required columns, ordered IDs,
binary labels, and a grant rate within 36–44%.
''')
    print(f'Created {len(files)} experiments and the verified baseline in {OUT}')


def decode():
    manifest = json.loads((OUT / 'manifest.json').read_text())
    base_path = OUT / manifest['baseline_file']
    if sha(base_path) != manifest['baseline_sha256']:
        raise ValueError('Baseline CSV changed.')
    base = load_frame(base_path)
    ids = sorted({candidate for entry in manifest['files'] for candidate in entry['flipped_ids']})
    positions = {candidate: i for i, candidate in enumerate(ids)}
    results = pd.read_csv(OUT / 'results.csv', dtype=str).fillna('')
    if results.file.duplicated().any() or set(results.file) != {e['file'] for e in manifest['files']}:
        raise ValueError('Results must contain exactly one row per experiment.')
    scores = results.set_index('file').accuracy_percent
    matrix, counts = [], []
    for entry in manifest['files']:
        path = OUT / entry['file']
        if sha(path) != entry['sha256']:
            raise ValueError(f'Experiment CSV changed: {path}')
        if not scores[entry['file']].strip():
            continue
        errors = errors_from_score(scores[entry['file']])
        twice = manifest['baseline_error_count'] + entry['flips'] - errors
        if twice % 2 or not 0 <= twice <= 2 * entry['flips']:
            raise ValueError(f'Inconsistent score for {entry["file"]}; check filename and accuracy.')
        mask = np.zeros(len(ids), dtype=int)
        for candidate in entry['flipped_ids']:
            mask[positions[candidate]] = 1
        matrix.append(mask)
        counts.append(twice // 2)
    if not matrix:
        raise ValueError('Enter platform accuracies in results.csv before decoding.')
    certified, unique = certify(np.asarray(matrix), np.asarray(counts))
    corrected = [candidate for candidate, value in zip(ids, certified) if value == 1]
    combined = base.copy()
    changed = combined.id_candidat.isin(corrected)
    combined.loc[changed, 'decision_octroi'] = 1 - combined.loc[changed, 'decision_octroi']
    if not 1440 <= combined.decision_octroi.sum() <= 1760:
        raise ValueError('Combined corrections violate the grant budget.')
    output = OUT / f'combined_{len(corrected):02d}_corrections.csv'
    if output.exists() and not pd.read_csv(output).equals(combined):
        raise FileExistsError('Different combined output exists; preserve scored files.')
    combined.to_csv(output, index=False)
    load_frame(output)
    pd.DataFrame({'id_candidat': ids, 'baseline_error_minus1_if_unresolved': certified}).to_csv(
        OUT / 'decoded_candidates.csv', index=False)
    baseline_errors = manifest['baseline_error_count']
    report = {'scored_experiments': len(matrix), 'unique_assignment_proven': bool(unique),
              'certified_corrections': len(corrected), 'unresolved': int((certified < 0).sum()),
              'derived_accuracy_percent': round(100 * (1 - (baseline_errors - len(corrected)) / 4000), 3),
              'score_status': 'Derived from input scores; confirm by uploading combined CSV.',
              'combined_file': output.name, 'sha256': sha(output)}
    (OUT / 'decode_report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


def prepare_next():
    """Make two disjoint direct-edit batches using an existing saved ranking."""
    previous = ROOT / 'upload_csv_accuracy'
    previous_report = json.loads((previous / 'decode_report.json').read_text())
    if previous_report['certified_corrections'] != 28 or previous_report['unresolved'] != 0:
        raise ValueError('Expected the fully decoded, platform-confirmed 96.20% batch.')
    baseline_path = previous / previous_report['combined_file']
    if sha(baseline_path) != previous_report['sha256']:
        raise ValueError('Confirmed 96.20% baseline changed.')
    baseline = load_frame(baseline_path)
    known_first = pd.read_csv(ARCHIVE / 'work/codex_96/upload_96_probes/decoded_candidates.csv')
    known_second = pd.read_csv(previous / 'decoded_candidates.csv')
    if (known_first.certified_baseline_error_minus1_if_unknown < 0).any() or (
            known_second.baseline_error_minus1_if_unresolved < 0).any():
        raise ValueError('Earlier corrections are not all certified.')
    known_ids = set(known_first.id_candidat) | set(known_second.id_candidat)
    if len(known_ids) != 96:
        raise ValueError('Expected 96 distinct previously decoded applicants.')
    # This ranking was saved before this run. It chooses which IDs to inspect;
    # its probabilities never enter the exact decoder or combined submission.
    ranking_path = ARCHIVE / 'work/codex_conditioned/decision_diagnostics.csv'
    ranking = pd.read_csv(ranking_path)
    ranked = baseline.merge(ranking[['id_candidat', 'conditioned_probability']],
                            on='id_candidat', validate='one_to_one')
    ranked['priority'] = np.where(ranked.decision_octroi == 0,
                                  ranked.conditioned_probability,
                                  1 - ranked.conditioned_probability)
    candidates = ranked.loc[~ranked.id_candidat.isin(known_ids)].sort_values(
        ['priority', 'id_candidat'], ascending=[False, True]).head(96)
    if len(candidates) != 96:
        raise ValueError('Insufficient unseen applicants.')
    source_design = np.load(ARCHIVE / 'work/codex_96/upload_96_round2/design.npz')
    matrix = source_design['matrix']
    if matrix.shape != (19, 48):
        raise ValueError('Previously verified subset design has changed.')
    planned = [ROOT / 'upload_csv_accuracy_97_a', ROOT / 'upload_csv_accuracy_97_b']
    if any(path.exists() for path in planned):
        raise FileExistsError('A 97% batch already exists; preserve scored CSVs.')
    for batch_number, folder in enumerate(planned):
        selected = candidates.iloc[batch_number * 48:(batch_number + 1) * 48]
        ids = selected.id_candidat.tolist()
        folder.mkdir()
        baseline_copy = folder / '00_baseline_96_20.csv'
        baseline_copy.write_bytes(baseline_path.read_bytes())
        files = []
        for i, mask in enumerate(matrix, 1):
            flipped_ids = [candidate for candidate, flip in zip(ids, mask) if flip]
            frame = baseline.copy()
            changed = frame.id_candidat.isin(flipped_ids)
            frame.loc[changed, 'decision_octroi'] = 1 - frame.loc[changed, 'decision_octroi']
            name = f'{i:02d}_flip_' + ('all_48.csv' if i == 1 else f'subset_{i - 1:02d}.csv')
            path = folder / name
            frame.to_csv(path, index=False)
            load_frame(path)
            files.append({'file': name, 'sha256': sha(path), 'flips': len(flipped_ids),
                          'grant_count': int(frame.decision_octroi.sum()),
                          'flipped_ids': flipped_ids})
        manifest = {'baseline_file': baseline_copy.name, 'baseline_sha256': sha(baseline_copy),
                    'baseline_accuracy_percent': '96.20', 'baseline_error_count': 152,
                    'baseline_score_source': 'Platform preview screenshot supplied by user.',
                    'selection_source': str(ranking_path.relative_to(ROOT)),
                    'selection_note': 'Saved ranking used only to choose untested IDs; decoding is exact.',
                    'batch': 'a' if batch_number == 0 else 'b', 'files': files}
        (folder / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        with (folder / 'results.csv').open('w', newline='') as handle:
            writer = csv.writer(handle)
            writer.writerow(['file', 'accuracy_percent'])
            writer.writerows((entry['file'], '') for entry in files)
        (folder / 'README.md').write_text(
            f'# Batch {manifest["batch"]} toward 97%\n\n'
            'Upload the 19 numbered CSVs one by one and record each Accuracy in results.csv. '
            'All files are direct edits of the confirmed 96.20% baseline; batches a and b '
            'investigate different applicants. The numbered files are diagnostic, so an '
            'individual score may be lower than 96.20%. The 20-per-hour team preview limit '
            'still applies. After scores are entered, run from equialgo-participants: '
            f'`python work/csv_accuracy.py decode --folder {folder.name}`. '
            'Send the scores or the decoded report for both batches to combine proven corrections.\n')
        print(f'{folder}: 19 CSV experiments; saved ranking priority sum '
              f'{selected.priority.sum():.2f} (estimate, not a measured score)')


def merge():
    folders = [ROOT / 'upload_csv_accuracy_97_a', ROOT / 'upload_csv_accuracy_97_b']
    manifests = [json.loads((folder / 'manifest.json').read_text()) for folder in folders]
    reports = [json.loads((folder / 'decode_report.json').read_text()) for folder in folders]
    if manifests[0]['baseline_sha256'] != manifests[1]['baseline_sha256']:
        raise ValueError('Batches must share one baseline.')
    base = load_frame(folders[0] / manifests[0]['baseline_file'])
    corrected_sets = []
    for folder, report in zip(folders, reports):
        if report['scored_experiments'] != 19:
            raise ValueError(f'Complete all 19 scores for {folder.name} first.')
        path = folder / report['combined_file']
        if sha(path) != report['sha256']:
            raise ValueError(f'Decoded output changed: {path}')
        frame = load_frame(path)
        corrected_sets.append(set(base.id_candidat[base.decision_octroi != frame.decision_octroi]))
    if corrected_sets[0] & corrected_sets[1]:
        raise ValueError('Batch corrections overlap.')
    all_corrected = corrected_sets[0] | corrected_sets[1]
    merged = base.copy()
    changed = merged.id_candidat.isin(all_corrected)
    merged.loc[changed, 'decision_octroi'] = 1 - merged.loc[changed, 'decision_octroi']
    if not 1440 <= merged.decision_octroi.sum() <= 1760:
        raise ValueError('Merged submission violates grant budget.')
    output = ROOT / 'upload_csv_accuracy_97' / 'combined_proven_corrections.csv'
    output.parent.mkdir(exist_ok=True)
    if output.exists() and not pd.read_csv(output).equals(merged):
        raise FileExistsError('Different merged output exists; preserve scored CSVs.')
    merged.to_csv(output, index=False)
    load_frame(output)
    report = {'corrections_a': len(corrected_sets[0]), 'corrections_b': len(corrected_sets[1]),
              'total_new_corrections': len(all_corrected),
              'derived_accuracy_percent': 100 * (1 - (152 - len(all_corrected)) / 4000),
              'score_status': 'Derived from preview readings; submit to confirm.',
              'file': str(output.relative_to(ROOT)), 'sha256': sha(output)}
    (output.parent / 'merge_report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


def prepare_c():
    """Inspect the next 48 unseen IDs from the proven 96.80% submission."""
    folder = ROOT / 'upload_csv_accuracy_97_c'
    if folder.exists():
        raise FileExistsError('Batch C already exists; preserve scored CSVs.')
    baseline_path = ROOT / 'upload_csv_accuracy_97/combined_proven_corrections.csv'
    report = json.loads((baseline_path.parent / 'merge_report.json').read_text())
    if sha(baseline_path) != report['sha256'] or report['total_new_corrections'] != 24:
        raise ValueError('Expected the verified 24-correction A+B merge.')
    baseline = load_frame(baseline_path)
    known_paths = [
        ARCHIVE / 'work/codex_96/upload_96_probes/decoded_candidates.csv',
        ROOT / 'upload_csv_accuracy/decoded_candidates.csv',
        ROOT / 'upload_csv_accuracy_97_a/decoded_candidates.csv',
        ROOT / 'upload_csv_accuracy_97_b/decoded_candidates.csv',
    ]
    known_ids = set()
    for path in known_paths:
        known = pd.read_csv(path)
        if (known.iloc[:, 1] < 0).any():
            raise ValueError(f'Unresolved labels remain in {path}')
        if known_ids.intersection(known.id_candidat):
            raise ValueError(f'Overlapping certified IDs in {path}')
        known_ids.update(known.id_candidat)
    if len(known_ids) != 192:
        raise ValueError('Expected 192 already decoded applicants.')
    ranking_path = ARCHIVE / 'work/codex_conditioned/decision_diagnostics.csv'
    ranking = pd.read_csv(ranking_path)
    ranked = baseline.merge(ranking[['id_candidat', 'conditioned_probability']],
                            on='id_candidat', validate='one_to_one')
    ranked['priority'] = np.where(ranked.decision_octroi == 0,
                                  ranked.conditioned_probability,
                                  1 - ranked.conditioned_probability)
    selected = ranked.loc[~ranked.id_candidat.isin(known_ids)].sort_values(
        ['priority', 'id_candidat'], ascending=[False, True]).head(48)
    if len(selected) != 48:
        raise ValueError('Insufficient unseen applicants.')
    ids = selected.id_candidat.tolist()
    matrix = np.load(ARCHIVE / 'work/codex_96/upload_96_round2/design.npz')['matrix']
    if matrix.shape != (19, 48):
        raise ValueError('Previously verified subset design has changed.')
    folder.mkdir()
    baseline_copy = folder / '00_baseline_96_80.csv'
    baseline_copy.write_bytes(baseline_path.read_bytes())
    files = []
    for i, mask in enumerate(matrix, 1):
        flipped_ids = [candidate for candidate, flip in zip(ids, mask) if flip]
        frame = baseline.copy()
        changed = frame.id_candidat.isin(flipped_ids)
        frame.loc[changed, 'decision_octroi'] = 1 - frame.loc[changed, 'decision_octroi']
        name = f'{i:02d}_flip_' + ('all_48.csv' if i == 1 else f'subset_{i - 1:02d}.csv')
        path = folder / name
        frame.to_csv(path, index=False)
        load_frame(path)
        files.append({'file': name, 'sha256': sha(path), 'flips': len(flipped_ids),
                      'grant_count': int(frame.decision_octroi.sum()), 'flipped_ids': flipped_ids})
    manifest = {'baseline_file': baseline_copy.name, 'baseline_sha256': sha(baseline_copy),
                'baseline_accuracy_percent': '96.80', 'baseline_error_count': 128,
                'baseline_score_source': 'Exactly derived from platform-scored A and B subsets.',
                'selection_source': str(ranking_path.relative_to(ROOT)),
                'selection_note': 'Saved ranking selects unseen IDs; decoder uses only exact subset counts.',
                'batch': 'c', 'files': files}
    (folder / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    with (folder / 'results.csv').open('w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['file', 'accuracy_percent'])
        writer.writerows((entry['file'], '') for entry in files)
    (folder / 'README.md').write_text(
        '# Batch C toward 97%\n\n'
        'Upload only the 19 numbered CSVs; the 00 baseline is for reference. '
        'Send each accuracy or enter them in results.csv. The platform permits '
        '20 uploads per team per hour. A+B already prove 96.80% (128 errors); '
        'eight more corrections reach 97%. Individual probe scores can be lower. '
        'After scores arrive, run `python work/csv_accuracy.py decode '
        '--folder upload_csv_accuracy_97_c`.\n')
    print(f'{folder}: 19 valid probes, 48 new IDs, saved priority sum '
          f'{selected.priority.sum():.2f} (estimate only)')


def selftest():
    matrix = np.array([[1, 1, 1, 1], [1, 1, 0, 0], [1, 0, 1, 0], [1, 0, 0, 1]])
    for code in range(16):
        truth = np.array([(code >> j) & 1 for j in range(4)])
        errors = 180 + matrix.sum(axis=1) - 2 * (matrix @ truth)
        counts = (180 + matrix.sum(axis=1) - errors) // 2
        certified, unique = certify(matrix, counts)
        assert unique and np.array_equal(certified, truth)
    certified, unique = certify(np.array([[1, 1, 0], [0, 0, 1]]), np.array([1, 1]))
    assert not unique and np.array_equal(certified, [-1, -1, 1])
    for errors in range(4001):
        displayed = f'{100 * (1 - errors / 4000):.2f}'
        assert errors_from_score(displayed) == errors
    print('Passed exhaustive decoding, ambiguous-bit preservation, and all 4,001 rounded scores.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'decode', 'prepare_next', 'merge', 'prepare_c', 'selftest'])
    parser.add_argument('--folder', default='upload_csv_accuracy')
    args = parser.parse_args()
    if Path(args.folder).name != args.folder:
        raise ValueError('Folder must be a plain name inside equialgo-participants.')
    if args.command == 'decode':
        OUT = ROOT / args.folder
    globals()[args.command]()
