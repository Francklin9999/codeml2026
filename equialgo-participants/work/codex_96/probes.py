"""Prepare scored subset probes and decode only logically certified corrections.

If a probe flips s decisions relative to a baseline with E errors, its error
count is E + s - 2*t, where t is the number of baseline errors in that subset.
Measured accuracies therefore supply exact integer subset counts. A binary
integer program checks which candidate errors are forced by those counts.

These probes target the fixed competition evaluation set; they are not a model
that has been validated for future applicants. No unknown label is assumed true.
"""
from pathlib import Path
from itertools import combinations
import argparse
import hashlib
import json
import sys
import numpy as np
import pandas as pd
from scipy.optimize import milp, Bounds, LinearConstraint

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'work/codex_conditioned'))
from condition import load,Projection,reference_prior


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def solver(A,counts,objective=None,exclude=None,fixed=None,seconds=5.):
    n=A.shape[1]
    lower=np.zeros(n);upper=np.ones(n)
    if fixed:
        for i,value in fixed.items():
            lower[i]=upper[i]=value
    C=A.copy().astype(float);lo=np.asarray(counts,float).copy();hi=lo.copy()
    if exclude is not None:
        C=np.vstack([C,1-2*exclude])
        lo=np.r_[lo,1-exclude.sum()];hi=np.r_[hi,np.inf]
    return milp(np.zeros(n) if objective is None else objective,
                integrality=np.ones(n),bounds=Bounds(lower,upper),
                constraints=LinearConstraint(C,lo,hi),
                options={'time_limit':seconds,'mip_rel_gap':0.0})


def make_matrix(n,m,seed):
    rng=np.random.default_rng(seed)
    rows=[np.ones(n,dtype=np.int8)]
    while len(rows)<m:
        row=np.zeros(n,dtype=np.int8)
        row[rng.choice(n,n//2,replace=False)]=1
        rows.append(row)
    A=np.asarray(rows)
    if len(np.unique(A.T,axis=0))!=n:
        return make_matrix(n,m,seed+100000)
    return A


def validate_matrix(A,n_trials,seed,seconds=.5):
    rng=np.random.default_rng(seed)
    rows=[]
    for i in range(n_trials):
        truth=rng.integers(0,2,A.shape[1])
        r=solver(A,A@truth,exclude=truth,seconds=seconds)
        rows.append({'trial':i,'status':int(r.status),'unique_proven':r.status==2,
                     'alternative_found':r.x is not None})
    return rows


def prepare(args):
    folder=ROOT/args.folder
    run=HERE/args.folder
    if folder.exists() or run.exists():
        raise FileExistsError('Use a new folder; scored probes must never be overwritten.')
    d,board,Y,E=load()
    best=int(E.argmin());baseline=Y[best].astype(int)
    baseline_path=ROOT/board.file.iloc[best]
    baseline_errors=int(E[best])
    baseline_source='Observed platform score'
    known_labels=np.full(len(d),-1,dtype=int)
    prior=reference_prior(d)
    previous=None
    if args.previous_batch:
        previous=HERE/args.previous_batch
        reports=sorted(previous.glob('decode_*_readings.json'))
        if not reports:
            raise ValueError('Decode the previous batch before preparing its successor.')
        report=json.loads(reports[-1].read_text())
        baseline_path=ROOT/report['file']
        if digest(baseline_path)!=report['sha256']:
            raise ValueError('Previously certified submission changed.')
        frame=pd.read_csv(baseline_path)
        assert frame.id_candidat.equals(d.id_candidat)
        baseline=frame.decision_octroi.to_numpy()
        baseline_errors=int(report['derived_error_count'])
        baseline_source=f'Derived from {args.previous_batch}: {report["certified_corrected_errors"]} certified corrections'
        old=np.load(previous/'design.npz')
        if 'known_labels' in old.files:
            known_labels=old['known_labels'].copy()
        certified=pd.read_csv(previous/'decoded_candidates.csv').certified_baseline_error_minus1_if_unknown.to_numpy()
        locations=old['selected_indices'][certified>=0]
        labels=old['baseline'][locations]^certified[certified>=0]
        assert np.all((known_labels[locations]<0)|(known_labels[locations]==labels))
        known_labels[locations]=labels
        assert np.array_equal(baseline[known_labels>=0],known_labels[known_labels>=0])
        prior[known_labels==0]=1e-10
        prior[known_labels==1]=1-1e-10
        Y=np.vstack([Y,baseline]);E=np.r_[E,baseline_errors]
    posterior,diag=Projection(Y).fit(prior,E,1599,max_iter=200)
    if diag['max_moment_residual']>1e-4:
        raise RuntimeError(diag)
    p_error=np.where(baseline==0,posterior,1-posterior)
    eligible=np.flatnonzero(known_labels<0)
    selected=eligible[np.argsort(-p_error[eligible],kind='stable')[:args.candidates]]
    print(f'Baseline {baseline_path.name}: {baseline_errors} errors ({baseline_source}); '
          f'{len(selected)} selected decisions, {p_error[selected].sum():.1f} model-estimated errors.',flush=True)

    # Select a coding matrix on synthetic cases; evaluate on a separate seed.
    if previous is not None and old['matrix'].shape==(args.previews,len(selected)):
        A=old['matrix'].copy()
        previous_info=json.loads((previous/'manifest.json').read_text())
        seed=previous_info['design_seed']
        holdout=pd.read_csv(previous/'synthetic_validation.csv').to_dict('records')
        print('Reused the independently tested subset design; selected new applicants.',flush=True)
    else:
        alternatives=[]
        for seed in [9601,9602,9603,9604]:
            A=make_matrix(len(selected),args.previews,seed)
            checks=validate_matrix(A,20,seed+90)
            successes=sum(row['unique_proven'] for row in checks)
            alternatives.append((successes,seed,A))
            print(f'Design {seed}: uniquely decoded {successes}/20 synthetic cases',flush=True)
        _,seed,A=max(alternatives,key=lambda x:x[0])
        holdout=validate_matrix(A,60,202696,seconds=1.)
        print(f'Held-out synthetic cases: {sum(r["unique_proven"] for r in holdout)}/60 uniquely decoded',flush=True)

    folder.mkdir();run.mkdir()
    board.to_csv(run/'leaderboard_snapshot.csv',index=False)
    pd.DataFrame(holdout).to_csv(run/'synthetic_validation.csv',index=False)
    np.savez_compressed(run/'design.npz',matrix=A,selected_indices=selected,
                        baseline=baseline,p_error=p_error[selected],known_labels=known_labels)
    pd.DataFrame({'id_candidat':d.id_candidat.iloc[selected].to_numpy(),
                  'baseline_decision':baseline[selected],
                  'estimated_error_probability_NOT_LABEL':p_error[selected]}).to_csv(run/'selected_candidates.csv',index=False)
    manifest=[]
    for i,mask in enumerate(A,1):
        pred=baseline.copy();positions=selected[mask.astype(bool)];pred[positions]=1-pred[positions]
        frame=pd.DataFrame({'id_candidat':d.id_candidat,'decision_octroi':pred})
        assert len(frame)==4000 and frame.id_candidat.is_unique
        assert frame.id_candidat.equals(d.id_candidat)
        assert frame.decision_octroi.isin([0,1]).all() and 1440<=pred.sum()<=1760
        file=folder/f'{args.prefix}_{i:02d}.csv';frame.to_csv(file,index=False)
        manifest.append({'file':file.name,'flips':int(mask.sum()),'grants':int(pred.sum()),'sha256':digest(file)})
    info={'baseline_file':str(baseline_path.relative_to(ROOT)),
          'baseline_sha256':digest(baseline_path),'baseline_error_count':baseline_errors,
          'baseline_accuracy_source':baseline_source,
          'previous_batch':args.previous_batch,
          'n_candidates':len(selected),'n_previews':len(A),'design_seed':seed,
          'hypothesized_errors_in_selection':float(p_error[selected].sum()),
          'files':manifest}
    (run/'manifest.json').write_text(json.dumps(info,indent=2)+'\n')
    pd.DataFrame({'file':[r['file'] for r in manifest],'accuracy_percent':['']*len(A)}).to_csv(run/'results.csv',index=False)
    (folder/'README.md').write_text(f'''# Diagnostic previews toward 96%

Preview `{args.prefix}_01.csv` through `{args.prefix}_{len(A):02d}.csv`, respecting the platform's
20-per-hour team limit. These are diagnostic files, not a claim of improved accuracy.
Baseline: `{baseline_path.relative_to(ROOT)}` with {baseline_errors} errors
({100*(1-baseline_errors/4000):.2f}%). Source: {baseline_source}.

Send the Accuracy for each file, for example `01: 95.00, 02: 94.95, ...`.
F1 is not needed to decode this batch. Keep every scored file unchanged.

The {len(A)} probes overlap across {len(selected)} uncertain decisions. Their scores tell
us exact counts of mistakes in each subset. An integer solver then identifies
which individual corrections are forced by those counts. Only those certified
corrections enter the resulting submission; no ambiguous bit is guessed.

This batch investigates new applicants; all previously certified decisions stay
unchanged. We need {max(baseline_errors-160,0)} additional corrections to reach 96%.
More previews may be needed; 96% is not guaranteed by this batch.
All files meet the 4,000-row format and 36–44% grant budget.

Results template and decoding metadata: `work/codex_96/{args.folder}/`.
After entering the percentages in its `results.csv`, run:

```bash
OPENBLAS_NUM_THREADS=1 python work/codex_96/probes.py decode --folder {args.folder}
```
''')
    print(f'Wrote {len(A)} valid probe CSVs to {folder}',flush=True)


def decode(args):
    folder=ROOT/args.folder;run=HERE/args.folder
    info=json.loads((run/'manifest.json').read_text())
    baseline_errors=info.get('baseline_error_count',info.get('baseline_observed_errors'))
    if digest(ROOT/info['baseline_file'])!=info['baseline_sha256']:
        raise ValueError('Baseline changed after probe generation.')
    results=pd.read_csv(run/'results.csv',dtype=str).fillna('')
    data=np.load(run/'design.npz');full_A=data['matrix'];base=data['baseline'];indices=data['selected_indices']
    A=[];counts=[];rows=[]
    for i,entry in enumerate(info['files']):
        if digest(folder/entry['file'])!=entry['sha256']:
            raise ValueError(f'Probe changed: {entry["file"]}')
        matching=results[results.file==entry['file']]
        if len(matching)!=1:
            raise ValueError(f'Require exactly one results row for {entry["file"]}')
        raw=matching.iloc[0].accuracy_percent.strip().replace('%','').replace(',','.')
        if not raw:
            continue
        accuracy=float(raw);unrounded=4000*(1-accuracy/100);errors=int(round(unrounded))
        if not 0<=accuracy<=100 or abs(errors-unrounded)>.201:
            raise ValueError(f'Accuracy incompatible with 4,000 rows: {entry["file"]} = {raw}')
        twice_count=baseline_errors+entry['flips']-errors
        if twice_count%2 or not 0<=twice_count<=2*entry['flips']:
            raise ValueError(f'Count/parity mismatch: recheck {entry["file"]} score {raw}')
        count=twice_count//2;A.append(full_A[i]);counts.append(count)
        rows.append({'file':entry['file'],'errors':errors,'baseline_errors_in_flipped_subset':count})
    if not A:
        raise ValueError('No scores entered yet.')
    A=np.asarray(A);counts=np.asarray(counts)
    prior=np.clip(data['p_error'],1e-6,1-1e-6)
    fitted=solver(A,counts,objective=np.log((1-prior)/prior),seconds=60.)
    if fitted.x is None:
        raise ValueError(f'No consistent binary assignment found; check scores (solver status {fitted.status}).')
    proposed=np.rint(fitted.x).astype(int)
    assert np.array_equal(A@proposed,counts)
    alternative=solver(A,counts,exclude=proposed,seconds=30.)
    certified=np.full(len(indices),-1,dtype=int)
    if alternative.status==2:
        certified=proposed.copy()
    else:
        for j in range(len(indices)):
            opposite=solver(A,counts,fixed={j:1-int(proposed[j])},seconds=3.)
            if opposite.status==2:
                certified[j]=proposed[j]
    pred=base.copy();fixed_rows=indices[certified==1];pred[fixed_rows]=1-pred[fixed_rows]
    corrected_errors=baseline_errors-len(fixed_rows)
    score=100*(1-corrected_errors/len(base))
    d=pd.read_csv(ROOT/'data/candidats_evaluation.csv')
    output=run/f'certified_{len(A):02d}_readings_{corrected_errors}_errors.csv'
    frame=pd.DataFrame({'id_candidat':d.id_candidat,'decision_octroi':pred})
    assert frame.id_candidat.equals(d.id_candidat) and len(frame)==4000
    assert frame.decision_octroi.isin([0,1]).all() and 1440<=pred.sum()<=1760
    if output.exists():
        old=pd.read_csv(output)
        if not old.equals(frame):
            raise FileExistsError('Different predictions already exist at output path.')
    else:
        frame.to_csv(output,index=False)
    report={'readings':len(A),'uniquely_decoded':alternative.status==2,
            'certified_corrected_errors':len(fixed_rows),'uncertain_decisions':int((certified<0).sum()),
            'derived_error_count':corrected_errors,'derived_accuracy_percent':score,
            'accuracy_source':'Mathematically derived from scored subsets, not yet submitted.',
            'file':str(output.relative_to(ROOT)),'sha256':digest(output)}
    (run/f'decode_{len(A):02d}_readings.json').write_text(json.dumps(report,indent=2)+'\n')
    pd.DataFrame({'id_candidat':d.id_candidat.iloc[indices].to_numpy(),
                  'certified_baseline_error_minus1_if_unknown':certified}).to_csv(run/'decoded_candidates.csv',index=False)
    pd.DataFrame(rows).to_csv(run/'decoded_counts.csv',index=False)
    print(json.dumps(report,indent=2),flush=True)


def selftest():
    # Known small matrix with exhaustive truth enumeration. Check the arithmetic
    # and uniqueness test independently of the competition's unknown labels.
    A=np.asarray([[1,1,1,1],[1,1,0,0],[1,0,1,0],[1,0,0,1]])
    for code in range(16):
        truth=np.array([(code>>j)&1 for j in range(4)])
        baseline_errors=truth.sum()+6
        for mask in A:
            observed=baseline_errors+mask.sum()-2*(mask@truth)
            assert (baseline_errors+mask.sum()-observed)//2==mask@truth
        sol=solver(A,A@truth)
        assert sol.x is not None and np.array_equal(np.rint(sol.x),truth)
        assert solver(A,A@truth,exclude=truth).status==2
    print('All 16 exhaustive arithmetic and binary-decoding cases passed.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('prepare');p.add_argument('--folder',default='upload_96_probes')
    p.add_argument('--previews',type=int,default=19);p.add_argument('--candidates',type=int,default=48)
    p.add_argument('--previous-batch');p.add_argument('--prefix',default='probe')
    p=sub.add_parser('decode');p.add_argument('--folder',default='upload_96_probes')
    sub.add_parser('selftest')
    args=parser.parse_args()
    if hasattr(args,'folder') and Path(args.folder).name!=args.folder:
        raise ValueError('Folder must be a plain name inside equialgo-participants.')
    if args.command=='prepare':
        if args.previous_batch and Path(args.previous_batch).name!=args.previous_batch:
            raise ValueError('Previous batch must be a plain folder name.')
        if not args.prefix or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789_' for c in args.prefix):
            raise ValueError('Probe prefix must contain only lowercase letters, digits or underscores.')
    if args.command=='prepare':prepare(args)
    elif args.command=='decode':decode(args)
    else:selftest()
