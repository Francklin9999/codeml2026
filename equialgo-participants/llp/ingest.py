"""Lit les blocs de résultat HxBuddy collés (texte brut) et les ajoute à hxbuddy_resultats.csv."""
import os, re, sys, glob
import pandas as pd
import engine as E


def trouver(nom):
    hits = [p for p in glob.glob(E.ROOT + 'sondes/**/' + nom, recursive=True)]
    assert len(hits) == 1, (nom, hits)
    return hits[0].replace(os.sep, '/').replace(E.ROOT, '')


def analyser(texte):
    """Retourne [(fichier, accuracy, f1_macro)] : un nom en .csv suivi d'une ligne avec au moins deux pourcentages."""
    out, courant = [], None
    for ligne in texte.splitlines():
        m = re.search(r'([\w\-.() ]+\.csv)', ligne)
        if m:
            courant = m.group(1).strip()
        pcts = re.findall(r'(\d{1,3}(?:[.,]\d+)?)\s*%', ligne)
        if courant and len(pcts) >= 2:
            out.append((courant, float(pcts[0].replace(',', '.')), float(pcts[1].replace(',', '.'))))
            courant = None
    return out


def ajouter(texte, log=None):
    log = log or E.ROOT + 'hxbuddy_resultats.csv'
    res = pd.read_csv(log)
    for nom, acc, f1 in analyser(texte):
        chemin = trouver(nom)
        res = res[res.fichier != chemin]
        res.loc[len(res)] = [chemin, acc, f1]
    res.reset_index(drop=True).to_csv(log, index=False)
    return res


if __name__ == '__main__':
    print(ajouter(open(sys.argv[1], encoding='utf-8').read()).to_string())
