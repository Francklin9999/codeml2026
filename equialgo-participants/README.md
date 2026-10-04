# ÉquiAlgo (IVADO): fair student financing

A scholarship-scoring model grants awards to 48.4% of applicants from Montréal and the
Capitale-Nationale against 27.3% from three remote regions. The task: diagnose the bias, correct it,
and propose a monitoring plan. All data is synthetic. Full rules: `consignes-fr.pdf`, `consignes-en.pdf`.

## Constraints

- **Budget.** The grant rate on the 4,000 evaluation applicants must be between 36% and 44%, otherwise
  the technical section scores zero.
- **`decision_octroi` is not the target.** Scoring uses a hidden reference standard built independently
  of the historical committee.
- **Dropping `region_administrative` is not enough.** Distance, hours worked, income and postal code
  carry regional information.

| Section | Points | Judged by |
|---|---|---|
| Diagnostic rigour | 25 | jury |
| Technical solution (equity 20, utility 15) | 35 | automated scorer |
| Governance and ethics | 25 | jury |
| Pitch and code quality | 15 | jury |

## Our solution

A sparse-spline logistic model of the historical committee, scored counterfactually: each applicant
keeps their own cote R and working hours, every other feature is replaced by common reference profiles.
The score is averaged over 30 seeds and the top 40% is granted (1,600 of 4,000; remote and centre both
at 40.0%). Platform preview: 94.83% accuracy, 94.61% macro F1. Details, evidence and limits:
[`MODEL_LOGIC.md`](MODEL_LOGIC.md).

## Run

```bash
python -m venv venv
venv\Scripts\activate             # Linux / macOS: source venv/bin/activate
pip install -r requirements.txt
python model_corrige.py           # writes predictions.csv and pareto_front.png
```

## Files

| Path | Contents |
|---|---|
| `predictions.csv` | Submission: `id_candidat,decision_octroi`, 4,000 rows |
| `model_corrige.py` | Mitigation and Pareto front; uses `work/clean95/seeded_model.py` |
| `model_analysis.ipynb` | Audit, proxy variables, model selection, graphs |
| `MODEL_LOGIC.md` | What the model does and why, validation, monitoring plan |
| `model_ensemble.py` | Entry point of the model-selection experiments in `work/codex_model/` |
| `baseline_model.ipynb` | Organizers' production model and fairness audit |
| `data/` | Not in the repository. Put the organizers' `donnees_demandes.csv` (10,000 labelled) and `candidats_evaluation.csv` (4,000 to score) here before running |
| `work/clean95/` | Final seed-ensembled model, validation report, notebook builder |
| `work/codex_model/` | Candidate models, reports, preview results (`platform_results.csv`) |
| `work/agent_dgp/` | Analysis of how the synthetic data was generated |
