"""Test : étalons simulés -> scores affichés des lots 2 et 3 -> ingest -> bilan. Le score réel est-il >= garanti ?"""
import os
import numpy as np
import pandas as pd
import engine as E
import ingest
import bilan as B
import retouches as R
from engine import N

rng = np.random.default_rng(11)
ecarts = []
fichiers = [f'lot2/R{j:02d}' for j in range(1, 11)] + [f'lot3/T{j:02d}' for j in range(1, 11)]
for rep in range(40):
    nom, (s, sig, w) = list(R.HYP.items())[rep % 5]
    lat = s + sig * rng.standard_normal(N)
    y = np.zeros(N)
    y[np.argsort(-lat)[:1595]] = 1
    bonsU = int((R.U == y).sum())
    texte = ''
    for f in fichiers:
        F = pd.read_csv(E.ROOT + f'sondes/{f}.csv').decision_octroi.to_numpy().astype(float)
        acc = np.floor(100 * (F == y).sum() / N * 100 + 0.5 + 1e-9) / 100
        texte += f'File\n{f.split("/")[1]}.csv\nPrediction\nDROP DATABASE codeml;\t{acc:g} %\t{acc - 0.2:g} %\t{acc - 0.2:g} %\n'
    log = 'test_log.csv'
    pd.read_csv(E.ROOT + 'hxbuddy_resultats.csv').iloc[:3].to_csv(log, index=False)
    ingest.ajouter(texte, log)
    t, F, garanti, esp = B.assembler(B.mesures(log, bons_u=bonsU), bons_u=bonsU)
    vrai = int((F == y).sum())
    ecarts.append((vrai - garanti, vrai - esp, vrai - bonsU))
    os.remove(log)
e = np.array(ecarts)
print(f'40 étalons simulés : réel >= garanti dans {int((e[:, 0] >= 0).sum())}/40 cas | réel - espéré : moyenne {e[:, 1].mean():+.2f} '
      f'| gain réel moyen {e[:, 2].mean():+.1f} (min {e[:, 2].min():+.0f}, max {e[:, 2].max():+.0f})')
