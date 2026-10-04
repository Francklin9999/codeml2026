"""Meilleurs plans de test non adaptatifs pour une cellule de 7 candidats dont on sait que k sont des erreurs de U.

Un test = un sous-ensemble ; résultat = nb d'erreurs dedans. Décision finale : inverser chaque candidat dont la
probabilité d'erreur a posteriori dépasse 1/2. On maximise le gain espéré (nb de bons gagnés).
"""
import itertools, sys
import numpy as np

n = 7
def best(k, t, top=3):
    configs = [sum(1 << i for i in c) for c in itertools.combinations(range(n), k)]
    C = len(configs)
    cnt = {m: [bin(m & c).count('1') for c in configs] for m in range(1, 1 << n)}
    wrong = np.array([[(c >> i) & 1 for i in range(n)] for c in configs])      # [config, candidat]
    res = []
    for tests in itertools.combinations(range(1, 1 << n), t):
        keys = {}
        for ci in range(C):
            keys.setdefault(tuple(cnt[m][ci] for m in tests), []).append(ci)
        gain = 0.0; garanti = 10 ** 9
        for grp in keys.values():
            w = wrong[grp].sum(0); flip = 2 * w > len(grp)
            g_cfg = (2 * wrong[grp][:, flip] - 1).sum(1) if flip.any() else np.zeros(len(grp))
            gain += g_cfg.sum(); garanti = min(garanti, g_cfg.min())
        res.append((gain / C, garanti, tests))
    res.sort(key=lambda x: (-x[0], -x[1]))
    return res[:top]

if __name__ == '__main__':
    for k in (1, 2, 3, 4):
        for t in (1, 2, 3):
            if t == 3 and len(sys.argv) < 2:
                continue
            b = best(k, t, top=1)[0]
            print(f'k={k} erreurs, {t} test(s) : gain espéré {b[0]:.3f} | gain garanti {b[1]:+.0f} | tests', [[i for i in range(n) if (m >> i) & 1] for m in b[2]])
