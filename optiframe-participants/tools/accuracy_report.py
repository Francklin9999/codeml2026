"""Accuracy report: python accuracy_report.py results.csv own_lenses.csv [--out DIR] [--seed N].

results.csv comes from eval.html (file,lensId,phone,rep,A,B,perimeter,method,reprojErrMm,sharpness,error).
own_lenses.csv holds three calliper readings per axis; reference = their median.
Writes accuracy_report.md and bias.json into DIR (default: next to results.csv). numpy only.
Run the eval with the identity bias.json: the fit below corrects the raw measurement.
"""
import argparse
import csv
import datetime
import json
import os
import sys

import numpy as np

AXES = ('A', 'B')
NOT_EST = 'not estimable'


def score_from_mae(mae: float) -> float:
    """Rubric: 30 points up to 1 mm MAE, linear down to 0 at 4 mm."""
    return 30.0 if mae <= 1 else max(0.0, 30.0 * (4 - mae) / 3)


def _num(s):
    try:
        v = float(s)
    except (TypeError, ValueError):
        return None
    return v if np.isfinite(v) else None


def load_reference(path: str) -> dict:
    """lensId -> {'A': median, 'B': median}; axes with no readings are left out."""
    ref = {}
    with open(path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            lid = (row.get('lensId') or '').strip()
            if not lid or lid.upper().startswith('EXAMPLE'):
                continue
            vals = {}
            for ax in AXES:
                v = [x for x in (_num(row.get(f'{ax}_mm_{i}')) for i in (1, 2, 3)) if x is not None]
                if v:
                    vals[ax] = float(np.median(v))
            if vals:
                ref[lid] = vals
    return ref


def load_results(path: str, ref: dict):
    """Returns (ok_rows, n_total, n_failed, unmatched_lens_ids). A row fails if it has an error or no A/B."""
    ok, total, failed, unmatched = [], 0, 0, set()
    with open(path, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            lid = (r.get('lensId') or '').strip()
            if lid not in ref:
                unmatched.add(lid)
                continue
            total += 1
            a, b = _num(r.get('A')), _num(r.get('B'))
            if (r.get('error') or '').strip() or a is None or b is None:
                failed += 1
                continue
            ok.append({'lens': lid, 'phone': (r.get('phone') or '').strip(), 'rep': (r.get('rep') or '').strip(),
                       'A': a, 'B': b})
    return ok, total, failed, sorted(unmatched)


def _errors(rows, ref, ax):
    return np.array([r[ax] - ref[r['lens']][ax] for r in rows if ax in ref[r['lens']]])


def bland_altman(meas, refv):
    d = np.asarray(meas) - np.asarray(refv)
    m = (np.asarray(meas) + np.asarray(refv)) / 2
    if len(d) < 2:
        return None
    sd = float(d.std(ddof=1))
    slope = float(np.polyfit(m, d, 1)[0]) if len(d) > 2 and np.ptp(m) > 0 else None
    return {'bias': float(d.mean()), 'sd': sd, 'loa_lo': float(d.mean() - 1.96 * sd),
            'loa_hi': float(d.mean() + 1.96 * sd), 'slope': slope}


def repeatability(rows, ax):
    """Pooled SD across repetitions of the same lens and phone."""
    cells = {}
    for r in rows:
        cells.setdefault((r['lens'], r['phone']), []).append(r[ax])
    ss = df = 0.0
    for v in cells.values():
        if len(v) > 1:
            ss += float(np.sum((np.array(v) - np.mean(v)) ** 2))
            df += len(v) - 1
    return float(np.sqrt(ss / df)) if df else None


def variance_components(rows, ax):
    """Random-effects ANOVA, lens + phone + residual (interaction pooled in the residual), balanced data.
    Cells are trimmed to the smallest repetition count and lenses missing a phone are dropped.
    Returns variances in mm2 and their share of the total, or None when not estimable."""
    cells = {}
    for r in rows:
        cells.setdefault((r['lens'], r['phone']), []).append(r[ax])
    phones = sorted({p for _, p in cells})
    lenses = sorted({l for l, _ in cells if all((l, p) in cells for p in phones)})
    if len(lenses) < 2 or len(phones) < 2:
        return None
    n = min(len(cells[(l, p)]) for l in lenses for p in phones)
    y = np.array([[cells[(l, p)][:n] for p in phones] for l in lenses], float)  # lens x phone x rep
    a, b = len(lenses), len(phones)
    df_e = a * b * n - a - b + 1
    if df_e <= 0:
        return None
    g = y.mean()
    ss_l = b * n * np.sum((y.mean(axis=(1, 2)) - g) ** 2)
    ss_p = a * n * np.sum((y.mean(axis=(0, 2)) - g) ** 2)
    ss_e = max(0.0, float(np.sum((y - g) ** 2) - ss_l - ss_p))  # clamp rounding noise
    ms_l, ms_p, ms_e = ss_l / (a - 1), ss_p / (b - 1), ss_e / df_e
    comp = {'lens': float(max(0.0, (ms_l - ms_e) / (b * n))), 'phone': float(max(0.0, (ms_p - ms_e) / (a * n))),
            'residual': float(ms_e)}
    tot = sum(comp.values())
    comp['share'] = {k: (comp[k] / tot if tot > 0 else 0.0) for k in ('lens', 'phone', 'residual')}
    comp['design'] = f'{a} lenses x {b} phones x {n} rep(s)'
    return comp


def _fit(x, y):
    a1, a0 = np.polyfit(x, y, 1)
    return float(a0), float(a1)


def loo_bias(rows, ref, ax):
    """Leave-one-lens-out: fit ref = a0 + a1*measured on the other lenses, predict the held-out one.
    Returns (a0, a1, mae_before, mae_after) or None when fewer than 4 lenses or no spread in x."""
    rr = [r for r in rows if ax in ref[r['lens']]]
    lenses = sorted({r['lens'] for r in rr})
    if len(lenses) < 4:
        return None
    x = np.array([r[ax] for r in rr])
    y = np.array([ref[r['lens']][ax] for r in rr])
    who = np.array([r['lens'] for r in rr])
    if np.ptp(x) == 0:
        return None
    before, after = [], []
    for l in lenses:
        tr, te = who != l, who == l
        if np.ptp(x[tr]) == 0:
            return None
        a0, a1 = _fit(x[tr], y[tr])
        before.extend(np.abs(x[te] - y[te]))
        after.extend(np.abs(a0 + a1 * x[te] - y[te]))
    a0, a1 = _fit(x, y)
    return a0, a1, float(np.mean(before)), float(np.mean(after))


def predicted_score(rows, ref, seed=0, draws=10000):
    """Per-lens error = mean |error| over its rows and both axes; the jury measures two lenses, so draw pairs."""
    per = {}
    for r in rows:
        for ax in AXES:
            if ax in ref[r['lens']]:
                per.setdefault(r['lens'], []).append(abs(r[ax] - ref[r['lens']][ax]))
    e = np.array([np.mean(v) for v in per.values()])
    if len(e) < 2:
        return None
    rng = np.random.default_rng(seed)
    first = rng.integers(0, len(e), size=draws)
    second = (first + rng.integers(1, len(e), size=draws)) % len(e)  # a different lens
    maes = (e[first] + e[second]) / 2
    sc = np.array([score_from_mae(m) for m in maes])
    return {'median': float(np.median(sc)), 'p5': float(np.percentile(sc, 5)), 'mae_median': float(np.median(maes)),
            'n': len(e)}


def analyse(results_path, ref_path, seed=0):
    ref = load_reference(ref_path)
    rows, total, failed, unmatched = load_results(results_path, ref)
    out = {'nRows': total, 'nFailed': failed, 'failureRate': (failed / total if total else None),
           'unmatched': unmatched, 'rows': rows, 'ref': ref}
    err = {ax: _errors(rows, ref, ax) for ax in AXES}
    allerr = np.concatenate([err['A'], err['B']])
    out['mae'] = {ax: (float(np.abs(err[ax]).mean()) if len(err[ax]) else None) for ax in AXES}
    out['mae']['overall'] = float(np.abs(allerr).mean()) if len(allerr) else None
    out['maePhone'] = {}
    for p in sorted({r['phone'] for r in rows}):
        sub = [r for r in rows if r['phone'] == p]
        ea, eb = _errors(sub, ref, 'A'), _errors(sub, ref, 'B')
        out['maePhone'][p] = {'A': float(np.abs(ea).mean()) if len(ea) else None,
                              'B': float(np.abs(eb).mean()) if len(eb) else None,
                              'overall': float(np.abs(np.concatenate([ea, eb])).mean()), 'n': len(sub)}
    out['ba'] = {}
    for ax in AXES:
        sub = [r for r in rows if ax in ref[r['lens']]]
        out['ba'][ax] = bland_altman([r[ax] for r in sub], [ref[r['lens']][ax] for r in sub])
    out['repeat'] = {ax: repeatability(rows, ax) for ax in AXES}
    out['vc'] = {ax: variance_components(rows, ax) for ax in AXES}
    out['loo'] = {ax: loo_bias(rows, ref, ax) for ax in AXES}
    out['score'] = predicted_score(rows, ref, seed)
    out['phones'] = sorted({r['phone'] for r in rows})
    out['nLenses'] = len({r['lens'] for r in rows})
    return out


def make_bias(res, today=None):
    """bias.json content: fitted values for an axis only when its leave-one-lens-out MAE improves, else identity."""
    b = {'a0': 0.0, 'a1': 1.0, 'b0': 0.0, 'b1': 1.0}
    helps = {}
    for ax, k0, k1 in (('A', 'a0', 'a1'), ('B', 'b0', 'b1')):
        loo = res['loo'][ax]
        helps[ax] = bool(loo and loo[3] < loo[2] and loo[1] > 0)
        if helps[ax]:
            b[k0], b[k1] = loo[0], loo[1]
    b.update({
        'fittedOn': today or datetime.date.today().isoformat(),
        'nLenses': res['nLenses'], 'phones': res['phones'],
        'loMaeBefore': {ax: (res['loo'][ax][2] if res['loo'][ax] else None) for ax in AXES},
        'loMaeAfter': {ax: (res['loo'][ax][3] if res['loo'][ax] else None) for ax in AXES},
        'helps': helps['A'] or helps['B'], 'helpsA': helps['A'], 'helpsB': helps['B'],
    })
    return b


def decision_line(res):
    sc = res['score']
    if not sc:
        return 'Decision: predicted score not estimable (fewer than 2 lenses).'
    if sc['median'] >= 25:
        return f"Decision: predicted median score {sc['median']:.1f} >= 25, no accuracy action required."
    comp = {}
    for ax in AXES:
        if res['ba'][ax]:
            comp.setdefault('bias', []).append(abs(res['ba'][ax]['bias']))
        if res['repeat'][ax] is not None:
            comp.setdefault('repeatability', []).append(res['repeat'][ax])
        if res['vc'][ax]:
            comp.setdefault('between-phone', []).append(float(np.sqrt(res['vc'][ax]['phone'])))
    comp = {k: float(np.mean(v)) for k, v in comp.items()}
    if not comp:
        return f"Decision: predicted median score {sc['median']:.1f} < 25 but no component is estimable."
    top = max(comp, key=comp.get)
    fix = {'bias': 'strategy 8 (bias calibration, boxing orientation) and strategy 13 (parallax)',
           'repeatability': 'strategy 7 (multi-shot fusion) and strategy 11 (capture fixture)',
           'between-phone': 'strategy 2 (per-phone calibration, error budget) and strategy 13 (parallax)'}[top]
    parts = ', '.join(f'{k} {v:.2f} mm' for k, v in comp.items())
    return (f"Decision: predicted median score {sc['median']:.1f} < 25. Dominant component: {top} "
            f"({parts}). Follow-up: {fix}.")


def _f(v, nd=2, unit=''):
    return NOT_EST if v is None else f'{v:.{nd}f}{unit}'


def render(res, bias):
    L = ['# Accuracy report', '',
         f"{res['nRows']} measurements, {res['nLenses']} lenses with a result, phones: {', '.join(res['phones']) or 'none'}. "
         'Reference = median of the three calliper readings. Errors are measured minus reference, in mm.', '']
    if res['unmatched']:
        L += [f"Ignored (lensId not in the calliper file): {', '.join(map(repr, res['unmatched']))}.", '']
    fr = res['failureRate']
    L += ['## Failure rate', '', f"{res['nFailed']} of {res['nRows']} measurements failed "
          f"({_f(None if fr is None else 100 * fr, 1, ' %')}). Failures are excluded from every figure below.", '']
    L += ['## MAE', '', '| | A | B | A and B |', '|---|---|---|---|',
          f"| all phones | {_f(res['mae']['A'])} | {_f(res['mae']['B'])} | {_f(res['mae']['overall'])} |"]
    for p, m in res['maePhone'].items():
        L.append(f"| {p} (n={m['n']}) | {_f(m['A'])} | {_f(m['B'])} | {_f(m['overall'])} |")
    L += ['', '## Bland-Altman (measured - reference vs mean)', '',
          '| axis | bias | SD | 95 % limits of agreement | slope of difference on mean |', '|---|---|---|---|---|']
    for ax in AXES:
        b = res['ba'][ax]
        L.append(f'| {ax} | ' + (NOT_EST + ' | | | |' if not b else
                 f"{b['bias']:+.2f} | {b['sd']:.2f} | [{b['loa_lo']:+.2f}, {b['loa_hi']:+.2f}] | {_f(b['slope'], 3)} |"))
    L += ['', '## Repeatability and reproducibility', '',
          'Repeatability = pooled SD across repetitions of the same lens and phone. Variance components by random-effects '
          'ANOVA on the measured values (lens, phone, residual; the lens x phone interaction is in the residual).', '',
          '| axis | repeatability SD | lens SD | phone SD | residual SD | share lens / phone / residual | design |',
          '|---|---|---|---|---|---|---|']
    for ax in AXES:
        v = res['vc'][ax]
        if v:
            sh = v['share']
            L.append(f"| {ax} | {_f(res['repeat'][ax])} mm | {np.sqrt(v['lens']):.2f} mm | {np.sqrt(v['phone']):.2f} mm | "
                     f"{np.sqrt(v['residual']):.2f} mm | {100*sh['lens']:.0f} / {100*sh['phone']:.0f} / "
                     f"{100*sh['residual']:.0f} % | {v['design']} |")
        else:
            L.append(f"| {ax} | {_f(res['repeat'][ax])} mm | {NOT_EST} | {NOT_EST} | {NOT_EST} | {NOT_EST} | |")
    L += ['', '## Bias correction (ref = a0 + a1 x measured)', '',
          '| axis | a0 | a1 | leave-one-lens-out MAE before | after | helps |', '|---|---|---|---|---|---|']
    for ax in AXES:
        o = res['loo'][ax]
        L.append(f'| {ax} | ' + (NOT_EST + ' (needs 4 lenses with different sizes) | | | | |' if not o else
                 f"{o[0]:+.3f} | {o[1]:.4f} | {o[2]:.3f} | {o[3]:.3f} | {'yes' if o[3] < o[2] else 'no'} |"))
    if bias['helps']:
        which = [ax for ax in AXES if bias['helps' + ax]]
        L += ['', f"The correction helps on {' and '.join(which)}: its fitted values are in bias.json (identity on the other axis). "
              'Copy bias.json to app/public/bias.json only after checking it on lenses that were not used for the fit.']
    else:
        L += ['', 'The correction does not help (or cannot be fitted): bias.json holds the identity. Do not apply a correction.']
    L += ['', '## Predicted rubric score', '',
          'Score = 30 if MAE <= 1 mm, else max(0, 30 x (4 - MAE) / 3). MAE per lens = mean |error| over its measurements and '
          'both axes; the bootstrap draws 10 000 random pairs of lenses.', '']
    sc = res['score']
    if sc:
        L += [f"- Median predicted score: {sc['median']:.1f} / 30 (median pair MAE {sc['mae_median']:.2f} mm, {sc['n']} lenses)",
              f"- 5th percentile: {sc['p5']:.1f} / 30"]
    else:
        L.append(f'- {NOT_EST} (fewer than 2 lenses)')
    L += ['', decision_line(res), '']
    return '\n'.join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('results')
    ap.add_argument('lenses')
    ap.add_argument('--out', help='output directory (default: folder of results.csv)')
    ap.add_argument('--seed', type=int, default=0)
    a = ap.parse_args(argv)
    res = analyse(a.results, a.lenses, a.seed)
    bias = make_bias(res)
    out = a.out or os.path.dirname(os.path.abspath(a.results))
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, 'bias.json'), 'w', encoding='utf-8') as f:
        json.dump(bias, f, indent=2)
        f.write('\n')
    text = render(res, bias)
    with open(os.path.join(out, 'accuracy_report.md'), 'w', encoding='utf-8') as f:
        f.write(text)
    print(text)
    return 0


if __name__ == '__main__':
    sys.exit(main())
