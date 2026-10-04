# Interface hors ligne NOVA

L'application dans `app/` est une coquille statique, sans dépendance externe. Elle s'ouvre directement avec `file://` et ne fait aucun appel réseau.

## Injection des données

Le générateur doit produire `nova-data.js` avant de copier `app/` dans `dist/` :

```js
window.NOVA_DATA = {
  meta: { asOf: "…", version: "…", toolDisclosure: "…" },
  brief: {
    owner: { text: "…", evidence: [{ label: "…", evidenceHref: "evidence/….html#…" }] },
    dateConditions: { text: "…", evidence: [] },
    scope: { text: "…", evidence: [] },
    budget: { text: "…", evidence: [] },
    priorities: ["…"],
    uncertainties: ["…"]
  },
  answers: {
    Q01: { question: "…", answer: "…", nuance: ["…"], sources: [{ label: "…", evidenceHref: "evidence/….html#…" }] }
  },
  timeline: [], decisions: [], contradictions: [], actions: [], risks: [],
  sources: [], limits: [], facts: [],
  versions: { baseline: {}, current: {}, changes: [], unchanged: [] }
};
```

Les tableaux et objets indexés par identifiant sont tous deux acceptés. Les preuves peuvent être dans `evidence`, `sources` ou `proofs`, mais le lien attendu est toujours `evidenceHref`. Seuls les chemins locaux relatifs et les fragments sont rendus cliquables; les URL absolues, protocoles et chemins Windows sont refusés.

Le fichier `app/nova-data.js` livré dans le dépôt est volontairement vide : l'interface présente alors des états vides explicites et n'invente aucun fait.

## Recherche

La recherche construit son index en mémoire à partir de `facts`, `answers`, `timeline`, `decisions`, `contradictions`, `actions`, `risks` et `sources`. Elle normalise les accents, applique une petite liste fixe de synonymes français et trie par score puis type et identifiant. Elle affiche des passages et leurs preuves, jamais une synthèse générée. Sans correspondance, la réponse est « Non documenté dans le corpus ».

## Accessibilité et impression

- navigation par liens et ordre de tabulation natif;
- lien d'évitement, focus visible, titres focalisés au changement de vue et zones `aria-live`;
- navigation horizontale sur petit écran;
- aucune couleur n'est le seul porteur d'information;
- le bouton « Imprimer le brief » active une feuille A4 compacte. Le générateur doit vérifier que le contenu réel tient sur une page après injection.

## Vérifications manuelles de livraison

1. Ouvrir `dist/index.html` avec le réseau désactivé.
2. Parcourir chaque vue au clavier et tester le lien d'évitement.
3. Depuis chaque question, ouvrir au moins une preuve et vérifier l'ancre `:target`.
4. Imprimer le brief en A4 et confirmer une seule page, à une taille lisible.
5. Rechercher un fait connu, une paraphrase et une question absente du corpus.
