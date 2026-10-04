"""Lot 1 : 10 sondes (comptes exacts) + test du décodage (accuracy/F1 affichés -> comptes exacts)."""
import os, numpy as np, pandas as pd
import engine as E, sim as S
from engine import N, g, r, h, li, fg, ld

OUT = E.ROOT + 'sondes/lot1/'
os.makedirs(OUT, exist_ok=True)
B = ((r >= 26.5) & (r <= 30.5)).astype(float)
LOT = {
    '01_eloignees': g.copy(),
    '02_base': S.base,
    '03_base_eloignees': S.base * g,
    '04_bande': B,
    '05_bande_eloignees': B * g,
    '06_bande_coteR_haut': B * (r >= 28.5),
    '07_bande_heures_haut': B * S.med_haut(h),
    '08_bande_revenu_haut': B * S.med_haut(li),
    '09_bande_premiere_gen': B * fg,
    '10_bande_distance_haut': B * S.med_haut(ld),
}
for nom, p in LOT.items():
    pd.DataFrame({'id_candidat': E.cand.id_candidat, 'decision_octroi': p.astype(int)}).to_csv(OUT + nom + '.csv', index=False)
    chk = pd.read_csv(OUT + nom + '.csv')
    assert len(chk) == N and list(chk.columns) == ['id_candidat', 'decision_octroi'] and set(chk.decision_octroi) <= {0, 1}
    print(f'{nom:26s} positifs {int(p.sum()):5d} ({p.mean():.1%}) | centres {int((p*(1-g)).sum()):5d} eloignees {int((p*g).sum()):5d}')

# --- décodage : (accuracy %, F1 macro %) affichés à 2 décimales -> nb exact de bons, Q compatibles
def rnd2(x):
    return np.floor(x * 100 + 0.5 + 1e-9) / 100

def affiche(pred, y):
    tp = (pred * y).sum(); P = pred.sum(); Q = y.sum(); tn = N - P - Q + tp
    f1p = 2 * tp / (P + Q) if P + Q > 0 else 0.0
    f1n = 2 * tn / (2 * N - P - Q)
    return rnd2(100 * (tp + tn) / N), rnd2(100 * (f1p + f1n) / 2)

def decoder(acc, f1, P):
    ks = [k for k in range(N + 1) if abs(100 * k / N - acc) <= 0.005 + 1e-9]
    out = []
    for k in ks:
        for Q in range(1500, 1700):
            tp2 = k - N + P + Q
            if tp2 % 2 or tp2 < 0 or tp2 > 2 * min(P, Q):
                continue
            tp = tp2 // 2; tn = N - P - Q + tp
            f = 100 * (2 * tp / (P + Q) + 2 * tn / (2 * N - P - Q)) / 2
            if abs(f - f1) <= 0.005 + 1e-9:
                out.append((k, Q))
    return out

# test sur 3 étalons simulés : le lot détermine-t-il Q de façon unique ?
for seed in (range(3) if __name__ == "__main__" else []):
    V = S.verite(np.random.default_rng(100 + seed)); y = V['y']
    Qs = None
    for nom, p in {'P1': S.P1, 'PNEED': S.PNEED, **LOT}.items():
        acc, f1 = affiche(p, y)
        sol = decoder(acc, f1, int(p.sum()))
        assert any(k == int((p == y).sum()) and Q == V['Q'] for k, Q in sol), (nom, acc, f1, sol[:3])
        qs = {Q for _, Q in sol}; Qs = qs if Qs is None else Qs & qs
    print('etalon simule', seed, 'vrai Q', V['Q'], '-> Q compatibles apres le lot :', sorted(Qs))
