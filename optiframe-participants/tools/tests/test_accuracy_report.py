import csv
import json

import numpy as np
import pytest

import accuracy_report as ar

HEAD = ['file', 'lensId', 'phone', 'rep', 'A', 'B', 'perimeter', 'method', 'reprojErrMm', 'sharpness', 'error']


def write_lenses(path, refs):
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['lensId', 'description', 'A_mm_1', 'A_mm_2', 'A_mm_3', 'B_mm_1', 'B_mm_2', 'B_mm_3',
                    'edge_thickness_mm', 'tint', 'notes'])
        for lid, (a, b) in refs.items():
            w.writerow([lid, '', a - 0.1, a, a + 0.1, b + 0.1, b, b - 0.1, '', '', ''])  # medians are a and b


def write_results(path, rows):
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(HEAD)
        for lid, phone, rep, a, b, err in rows:
            w.writerow([f'{lid}_{phone}_{rep}.jpg', lid, phone, rep, a, b, '', 'classic', '', '', err])


def refs(n=10):
    return {f'L{i:02d}': (48 + 1.7 * i, 36 + 1.1 * i) for i in range(n)}


def make(tmp_path, refs_, fn):
    rp, lp = tmp_path / 'results.csv', tmp_path / 'own.csv'
    write_lenses(lp, refs_)
    rows = [(lid, ph, rep, *fn(lid, ph, rep, a, b), '') for lid, (a, b) in refs_.items()
            for ph in ('P1', 'P2') for rep in (1, 2, 3)]
    write_results(rp, rows)
    return str(rp), str(lp)


@pytest.mark.parametrize('mae,pts', [(0.5, 30), (1, 30), (2.5, 15), (4, 0), (6, 0)])
def test_score_formula(mae, pts):
    assert ar.score_from_mae(mae) == pytest.approx(pts)


def test_known_bias_mae_and_score(tmp_path):
    # error is +0.3 on one phone, +0.5 on the other: bias 0.4, MAE 0.4
    rp, lp = make(tmp_path, refs(), lambda l, p, r, a, b: (a + (0.3 if p == 'P1' else 0.5), b + (0.5 if p == 'P1' else 0.3)))
    res = ar.analyse(rp, lp)
    assert res['ba']['A']['bias'] == pytest.approx(0.4, abs=0.02)
    assert res['ba']['B']['bias'] == pytest.approx(0.4, abs=0.02)
    assert res['mae']['overall'] == pytest.approx(0.4, abs=0.02)
    assert res['score']['median'] == 30 and res['score']['p5'] == 30
    assert res['failureRate'] == 0


@pytest.mark.parametrize('mae,pts', [(0.5, 30), (1, 30), (2.5, 15), (4, 0)])
def test_predicted_score_at_constant_mae(tmp_path, mae, pts):
    rp, lp = make(tmp_path, refs(), lambda l, p, r, a, b: (a + mae, b - mae))
    res = ar.analyse(rp, lp)
    assert res['mae']['overall'] == pytest.approx(mae)
    assert res['score']['median'] == pytest.approx(pts)
    assert res['score']['p5'] == pytest.approx(pts)


def test_failures_per_phone_and_cli(tmp_path):
    rp, lp = tmp_path / 'r.csv', tmp_path / 'o.csv'
    write_lenses(lp, refs(5))
    rows = [('L00', 'P1', 1, 48.0, 36.0, ''), ('L00', 'P1', 2, '', '', 'NO_LENS'), ('L01', 'P2', 1, 50.7, 37.1, ''),
            ('GHOST', 'P1', 1, 1, 1, '')]
    write_results(rp, rows)
    res = ar.analyse(str(rp), str(lp))
    assert res['nRows'] == 3 and res['nFailed'] == 1 and res['failureRate'] == pytest.approx(1 / 3)
    assert res['unmatched'] == ['GHOST']
    assert set(res['maePhone']) == {'P1', 'P2'}
    assert ar.main([str(rp), str(lp), '--out', str(tmp_path / 'out')]) == 0
    assert (tmp_path / 'out' / 'accuracy_report.md').read_text().startswith('# Accuracy report')


def test_repeatability(tmp_path):
    rng = np.random.default_rng(1)
    noise = {}
    rp, lp = make(tmp_path, refs(), lambda l, p, r, a, b: (a + noise.setdefault((l, p, r), rng.normal(0, 0.2)), b))
    res = ar.analyse(rp, lp)
    assert res['repeat']['A'] == pytest.approx(0.2, rel=0.25)
    assert res['repeat']['B'] == pytest.approx(0.0, abs=1e-9)


def test_variance_components_known_phone_offset(tmp_path):
    offsets = {'P1': -0.6, 'P2': -0.2, 'P3': 0.2, 'P4': 0.6}
    rng = np.random.default_rng(7)
    lens_ref = {f'L{i:02d}': (45 + 2.3 * i, 30 + 1.0 * i) for i in range(12)}
    rp, lp = tmp_path / 'r.csv', tmp_path / 'o.csv'
    write_lenses(lp, lens_ref)
    rows = [(l, p, rep, a + off + rng.normal(0, 0.05), b, '') for l, (a, b) in lens_ref.items()
            for p, off in offsets.items() for rep in (1, 2, 3)]
    write_results(rp, rows)
    res = ar.analyse(str(rp), str(lp))
    vc = res['vc']['A']
    # random-effect phone variance = sample variance of the four offsets
    assert vc['phone'] == pytest.approx(np.var(list(offsets.values()), ddof=1), rel=0.1)
    assert vc['residual'] == pytest.approx(0.05 ** 2, rel=0.25)
    assert vc['lens'] == pytest.approx(np.var([a for a, _ in lens_ref.values()], ddof=1), rel=0.15)
    assert sum(vc['share'].values()) == pytest.approx(1)
    assert res['vc']['B']['phone'] == pytest.approx(0, abs=1e-3)  # axis B has no phone effect


def test_variance_components_not_estimable_with_one_phone(tmp_path):
    rp, lp = tmp_path / 'r.csv', tmp_path / 'o.csv'
    write_lenses(lp, refs(5))
    write_results(rp, [(l, 'P1', r, a, b, '') for l, (a, b) in refs(5).items() for r in (1, 2)])
    res = ar.analyse(str(rp), str(lp))
    assert res['vc']['A'] is None
    assert 'not estimable' in ar.render(res, ar.make_bias(res))


def test_bias_json_written_when_loo_improves(tmp_path):
    rp, lp = make(tmp_path, refs(), lambda l, p, r, a, b: ((a - 3) / 0.9 + 0.01 * r, (b + 1.5) * 1.05))
    res = ar.analyse(rp, lp)
    bias = ar.make_bias(res, today='2026-01-01')
    assert bias['helps'] and bias['helpsA'] and bias['helpsB']
    assert bias['a1'] == pytest.approx(0.9, abs=0.01) and bias['a0'] == pytest.approx(3.0, abs=0.2)
    assert bias['b1'] == pytest.approx(1 / 1.05, abs=0.01)
    assert bias['loMaeAfter']['A'] < bias['loMaeBefore']['A']
    assert bias['nLenses'] == 10 and bias['phones'] == ['P1', 'P2'] and bias['fittedOn'] == '2026-01-01'
    assert ar.main([rp, lp, '--out', str(tmp_path / 'o')]) == 0
    written = json.loads((tmp_path / 'o' / 'bias.json').read_text())
    assert written['a1'] == pytest.approx(bias['a1'])
    assert 'The correction helps on A and B' in (tmp_path / 'o' / 'accuracy_report.md').read_text()


def test_bias_json_identity_when_loo_does_not_improve(tmp_path):
    # exact measurements: nothing to correct, so the fit cannot beat the raw error
    rp, lp = make(tmp_path, refs(), lambda l, p, r, a, b: (a, b))
    res = ar.analyse(rp, lp)
    bias = ar.make_bias(res)
    assert not bias['helps']
    assert (bias['a0'], bias['a1'], bias['b0'], bias['b1']) == (0.0, 1.0, 0.0, 1.0)
    assert ar.main([rp, lp, '--out', str(tmp_path / 'o')]) == 0
    assert json.loads((tmp_path / 'o' / 'bias.json').read_text())['a1'] == 1.0
    assert 'does not help' in (tmp_path / 'o' / 'accuracy_report.md').read_text()


def test_bias_not_fitted_with_few_lenses(tmp_path):
    rp, lp = make(tmp_path, refs(3), lambda l, p, r, a, b: (a + 1, b + 1))
    res = ar.analyse(rp, lp)
    assert res['loo']['A'] is None and not ar.make_bias(res)['helps']


def test_decision_line_names_dominant_component(tmp_path):
    rp, lp = make(tmp_path, refs(), lambda l, p, r, a, b: (a + 3, b + 3))  # constant bias
    res = ar.analyse(rp, lp)
    assert res['score']['median'] < 25
    line = ar.decision_line(res)
    assert 'Dominant component: bias' in line and 'strategy 8' in line
    # +4 mm on one phone, -4 mm on the other: mean bias 0, between-phone dominates
    rp, lp = make(tmp_path, refs(), lambda l, p, r, a, b: (a + (4 if p == 'P1' else -4), b + (4 if p == 'P1' else -4)))
    line = ar.decision_line(ar.analyse(rp, lp))
    assert 'Dominant component: between-phone' in line
    # good accuracy: no action
    rp, lp = make(tmp_path, refs(), lambda l, p, r, a, b: (a + 0.2, b))
    assert 'no accuracy action required' in ar.decision_line(ar.analyse(rp, lp))
