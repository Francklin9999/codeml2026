"""Test de bout en bout : étalon simulé -> scores affichés des 20 retouches -> texte collé -> ingest -> bilan. Le score prédit est-il exact ?"""
import os, shutil, numpy as np, pandas as pd
import engine as E, sim as S, ingest, bilan_retouches as B, retouches as R
from engine import N
rng = np.random.default_rng(5)
for essai, (nom, (s, sig, w)) in enumerate(R.HYP.items()):
    lat = s + sig * rng.standard_normal(N); y = np.zeros(N); y[np.argsort(-lat)[:1595]] = 1
    U = R.U; bonsU = int((U == y).sum())
    B.BONS_U = bonsU
    texte = ''
    for j in range(1, 21):
        F = pd.read_csv(E.ROOT + f'sondes/lot2/R{j:02d}.csv').decision_octroi.to_numpy().astype(float)
        tp = (F * y).sum(); P = F.sum(); Q = y.sum(); tn = N - P - Q + tp
        acc = np.floor(100 * (tp + tn) / N * 100 + 0.5 + 1e-9) / 100
        f1 = np.floor(100 * (2 * tp / (P + Q) + 2 * tn / (2 * N - P - Q)) / 2 * 100 + 0.5 + 1e-9) / 100
        texte += f'File\nR{j:02d}.csv\nPrediction\nTeam Name\tAccuracy\tF1 macro\tIndicative score (F1)\nDROP DATABASE codeml;\t{acc:g} %\t{f1:g} %\t{f1:g} %\n'
    log = 'test_log.csv'; shutil.copy(E.ROOT + 'hxbuddy_resultats.csv', log)
    ingest.ajouter(texte, log)
    t, F, total = B.bilan(log, ecrire=False)
    vrai = int((F == y).sum())
    print(f'{nom:18s} U {bonsU} -> assemblé : prédit {total}, réel {vrai} ({"OK" if total == vrai else "ECART"}) | gain {total - bonsU:+d} | cellules retenues {int(t.retenue.sum())}/20 | 9 premières : {int(t.delta[:9].clip(lower=0).sum()):+d}, 14 premières : {int(t.delta[:14].clip(lower=0).sum()):+d}')
    os.remove(log)
