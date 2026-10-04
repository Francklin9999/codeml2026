"""Generate an exact six-case search from two scored, four-decision variants.

Both source files scored 94.95% on the same 4,000 rows, hence 202 errors each.
They differ on four binary decisions, so precisely two of the four changes
correct errors and two create errors. Every two-change subset is materialized.
One of these six files has exactly 200 errors, four have 202, and one has 204.
The three pairs containing A plus a losing pair's complement need <=4 previews.
"""
from pathlib import Path
from itertools import combinations
import hashlib
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).parent
OUT=ROOT/'upload_95'
SOURCE_A=ROOT/'upload_codex_v2/03_conservative_changes.csv'
SOURCE_B=ROOT/'upload_codex_v2/04_half_strength.csv'
HASH_A='94c9df6bc0addda08d81e0d76be3894244ba45ed02b583e820e30a68a99d64a7'
HASH_B='08a5dcafb439729d5a2329526c3a2cbe692c89c9bab21c5075aaf40429f8d359'


def main():
    if OUT.exists():
        raise FileExistsError(f'Preserve existing submissions: {OUT}')
    assert hashlib.sha256(SOURCE_A.read_bytes()).hexdigest()==HASH_A
    assert hashlib.sha256(SOURCE_B.read_bytes()).hexdigest()==HASH_B
    candidates=pd.read_csv(ROOT/'data/candidats_evaluation.csv')
    first=pd.read_csv(SOURCE_A)
    second=pd.read_csv(SOURCE_B)
    assert first.id_candidat.equals(candidates.id_candidat)
    assert second.id_candidat.equals(candidates.id_candidat)
    assert len(first)==4000
    baseline=first.decision_octroi.to_numpy()
    alternate=second.decision_octroi.to_numpy()
    differences=np.flatnonzero(baseline!=alternate)
    assert len(differences)==4
    # The ordering only chooses which pair to preview first. It does not affect
    # exhaustive coverage or the exact arithmetic proof.
    keys={'A':'C007342','B':'C004931','C':'C010924','D':'C007053'}
    positions={k:int(np.flatnonzero(candidates.id_candidat==v)[0]) for k,v in keys.items()}
    assert set(positions.values())==set(differences)
    pairs=['AB','AC','AD','CD','BD','BC']
    files={pair:f'{i:02d}_pair_{pair}.csv' for i,pair in enumerate(pairs,1)}
    complements={'AB':'CD','AC':'BD','AD':'BC','CD':'AB','BD':'AC','BC':'AD'}
    OUT.mkdir()
    manifest=[]
    for pair in pairs:
        pred=baseline.copy()
        chosen=[positions[key] for key in pair]
        pred[chosen]=1-pred[chosen]
        assert (pred!=baseline).sum()==2
        assert np.isin(pred,[0,1]).all() and 1440<=pred.sum()<=1760
        frame=pd.DataFrame({'id_candidat':candidates.id_candidat,'decision_octroi':pred})
        path=OUT/files[pair]
        frame.to_csv(path,index=False)
        manifest.append({'file':path.name,'pair':pair,'changed_ids':[keys[key] for key in pair],
                         'grants':int(pred.sum()),'if_accuracy_94_90_upload':files[complements[pair]],
                         'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})

    # Exhaustive verification of the only six possible truth assignments on
    # these four rows: two changes help, two hurt.
    cases=[]
    for helpful in combinations('ABCD',2):
        helpful=set(helpful)
        errors={pair:202+2-2*len(set(pair)&helpful) for pair in pairs}
        assert sorted(errors.values())==[200,202,202,202,202,204]
        visited=[]
        for pair in ['AB','AC','AD']:
            visited.append(pair)
            if errors[pair]==200:
                break
            if errors[pair]==204:
                pair=complements[pair]
                visited.append(pair)
                assert errors[pair]==200
                break
        assert errors[visited[-1]]==200 and len(visited)<=4
        cases.append({'helpful_pair':''.join(sorted(helpful)),
                      'errors_by_pair':errors,'preview_path':visited})
    (HERE/'finish95_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (HERE/'finish95_exhaustive_check.json').write_text(json.dumps(cases,indent=2)+'\n')
    (OUT/'README.md').write_text('''# Reach 95.00%: an exact paired search

Start with **01_pair_AB.csv**.

| File just tested | If Accuracy is 95.00% | If Accuracy is 94.95% | If Accuracy is 94.90% |
|---|---|---|---|
| 01_pair_AB.csv | Keep this file | Test 02_pair_AC.csv | Test 04_pair_CD.csv; it must reach 95.00% |
| 02_pair_AC.csv | Keep this file | Test 03_pair_AD.csv | Test 05_pair_BD.csv; it must reach 95.00% |
| 03_pair_AD.csv | Keep this file | Stop and check the source results | Test 06_pair_BC.csv; it must reach 95.00% |

Follow this table: at most four previews are needed. Stop after reaching 95.00%.
If a displayed score differs from these cases, report it before continuing.

## Why this works

`upload_codex_v2/03_conservative_changes.csv` and
`upload_codex_v2/04_half_strength.csv` both scored 94.95%: 202 errors out of 4,000.
Their predictions differ on exactly four applicants. Of those four changes,
exactly two correct mistakes and two introduce mistakes.

These six files cover every pair of those four changes, starting from file 03.
One therefore removes exactly two errors: 200 errors, or 95.00%. Four preserve
202 errors, and one introduces two errors. The complement of a losing pair is
the winning pair. This is exact score arithmetic, not a model estimate, assuming
the same fixed 4,000 reference labels and accuracy scoring used for the source
files. It does not establish accuracy on future applicants.

All files have 4,000 candidate IDs in original order, binary decisions, and a
grant rate within 36–44%. Their source hashes were checked. All six possible
assignments and the four-preview procedure were verified exhaustively.
''')
    print(pd.DataFrame(manifest).drop(columns='sha256').to_string(index=False))
    print('All six truth cases pass; at most four previews to 95.00% with the same scorer.')


if __name__=='__main__':
    main()
