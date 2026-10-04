"""Le recensement (lot 3) + les mesures existantes permettent-ils un candidat meilleur que U ? Étalons simulés."""
import sys, time, numpy as np, pandas as pd
import engine as E, eng2, sim as S, lot3 as L3
from engine import N, g, r, h, li, fg
U = L3.U
cel2 = pd.read_csv(E.ROOT + 'sondes/lot2/cellules.csv'); idx_de = {c: i for i, c in enumerate(E.cand.id_candidat)}
RC = [np.array([idx_de[c] for c in cel2[cel2.cellule == f'R{j:02d}'].id_candidat]) for j in range(1, 11)]
CC = L3.lot()
dist = E.cand.distance_domicile_campus_km.to_numpy()
TRUTHS = {
    'pur (règle de U), bruit .5': (r + 0.1525 * h, 0.5, 0.0),
    'heures 0.11, bruit .5': (r + 0.11 * h, 0.5, 0.0),
    'H1 éloignée -0.2, a=.18': (r + 0.18 * h - 0.2 * g, 0.5, 0.0),
    'H2 prem. gen -0.4': (r + 0.15 * h - 0.4 * fg, 0.45, 0.0),
    'H3 revenu +0.2': (r + 0.15 * h + 0.2 * li, 0.5, 0.0),
    'bruit .25 + 3 % inversions': (r + 0.1525 * h, 0.25, 0.03),
}

def obs(y, avec_census):
    Wr, zr = [], []
    for p in (S.P1, S.PNEED, U):
        Wr.append(2 * p - 1); zr.append((p == y).sum() - (N - p.sum()))
    for ids in RC:
        w = np.zeros(N); w[ids] = 1; Wr.append(w); zr.append(y[ids].sum())
    if avec_census:
        for cell in CC.values():
            Wr.append(cell.copy()); zr.append((y * cell).sum())
    return np.array(Wr), np.array(zr, float)

M = eng2.Model(names=('base5', 'prog'), sig_lo=0.2)
rng = np.random.default_rng(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
rows = []
for nom, (s, sig, lapse) in TRUTHS.items():
    for rep in range(int(sys.argv[2]) if len(sys.argv) > 2 else 5):
        lat = s + sig * rng.standard_normal(N); y = np.zeros(N); y[np.argsort(-lat)[:1595]] = 1
        if lapse:
            fl = rng.random(N) < lapse; y[fl] = 1 - y[fl]
        out = dict(verite=nom, bons_U=int((U == y).sum()))
        for tag, cens in (('sans', False), ('avec', True)):
            W, z = obs(y, cens)
            th, f = M.fit(W, z, n_starts=8, seed=rep, tau2=0.25)
            p = M.proba(th)
            b = eng2.blup(p, W, z, 0.25)
            out[f'gain_modele_{tag}'] = int(((p > 0.5) == y).sum() - (U == y).sum())
            out[f'gain_blup_{tag}'] = int(((b > 0.5) == y).sum() - (U == y).sum())
            out[f'sigma_{tag}'] = round(float(np.exp(th[M.K + 1])), 2)
        rows.append(out)
df = pd.DataFrame(rows); pd.set_option('display.width', 220)
print(df.groupby('verite', sort=False).agg(bons_U=('bons_U', 'mean'), modele_sans=('gain_modele_sans', 'mean'), blup_sans=('gain_blup_sans', 'mean'),
      modele_avec=('gain_modele_avec', 'mean'), blup_avec=('gain_blup_avec', 'mean'), blup_avec_min=('gain_blup_avec', 'min'), blup_avec_max=('gain_blup_avec', 'max'),
      sigma_avec=('sigma_avec', 'mean')).round(1).to_string())
