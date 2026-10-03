# Strategy 1: neutralisation results

These are candidate outputs and sensitivity analyses only. Simulated scores compare predictions with hypotheses generated from the same supplied data and model families; they are not the hidden reference, independent ground truth, or official scores.

## Committee fit and stability

Five-fold AUC is on the committee label; selected-C AUC reuses the tuning folds and is optimistic, not an independent estimate. Logistic coefficients are standardized-pipeline coefficients. Stability uses five stratified 80/20 refits and pairwise Jaccard of each refit's top-1,600 candidate set. This is a lightweight proxy for the proposed 25 refits and does not establish sampling robustness.

| variant | family | C | grid_cv_auc | committee_cv_auc_fixed_C | mean_pairwise_jaccard | min_pairwise_jaccard | mean_vs_full_jaccard |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V1 | logit | 1.0 | 0.9570293111478492 | 0.9570293111478492 | 0.9821672946164771 | 0.9777503090234858 | 0.9888150788572931 |
| V2 | logit | 0.1 | 0.9569357055228401 | 0.9569357055228401 | 0.9794703757854372 | 0.9728729963008631 | 0.9863509219802638 |
| V3 | logit | 1.0 | 0.9569953448411297 | 0.9569953448411297 | 0.9820492617517619 | 0.9765287214329833 | 0.987827766111287 |
| V4 | gbm |  |  | 0.9530979354630608 | 0.9172208482198337 | 0.9036287923854849 | 0.9323944141862919 |
| V5 | logit | 0.1 | 0.9570013943740607 | 0.9570013943740607 | 0.9815528423718091 | 0.9765287214329833 | 0.9885689374905748 |

## Largest absolute logistic coefficients

| variant | feature | coefficient |
| --- | --- | --- |
| V3 | cote_r | 4.142791654583425 |
| V1 | cote_r | 4.128339164924578 |
| V5 | cote_r | 3.8683529731113846 |
| V2 | cote_r | 3.839270056346953 |
| V1 | remote | -1.0815796031438836 |
| V1 | heures | 0.7607287561332651 |
| V5 | heures | 0.7583192595777267 |
| V3 | heures | 0.7583158923295997 |
| V3 | log_rev | 0.7452282237122246 |
| V1 | log_rev | 0.737728033770709 |
| V2 | heures | 0.6939212778759943 |
| V2 | reg_Gaspesie-Iles-de-la-Madeleine | -0.6703098971292597 |
| V2 | reg_Bas-Saint-Laurent | -0.6598748951635292 |
| V2 | reg_Cote-Nord | -0.6378869452350217 |
| V2 | log_rev | 0.6320557584902305 |
| V5 | log_rev | 0.6293624137283718 |
| V3 | reg_Gaspesie-Iles-de-la-Madeleine | -0.5590911751621963 |
| V5 | remote | -0.5421052335369735 |
| V3 | cp_H2X | 0.2758006857038919 |
| V5 | remote_x_cote_r | -0.2593654919763301 |
| V3 | reg_Bas-Saint-Laurent | -0.255978330634299 |
| V3 | reg_Cote-Nord | -0.2485259601246868 |
| V3 | cp_H3T | 0.24221372488106377 |
| V5 | remote_x_heures | -0.21739746964273277 |
| V2 | rev | 0.11870657067005029 |
| V5 | rev | 0.11850815339774394 |
| V1 | dist | 0.0856586157642715 |
| V1 | log_dist | 0.07996823642654695 |
| V5 | dist | 0.06833110613455892 |
| V2 | dist | 0.0625899533000845 |
| V1 | rev | 0.06131104126379899 |
| V1 | prog_Sante | 0.024436229869529594 |

## Conditional parity

Rates are by candidate academic decile, comparing remote and central candidates. Committee rows are unneutralized top-1,600 selections; variant rows are neutralized selections. Summary shows mean absolute remote-central gap and number of deciles exceeding 3 percentage points.

| variant | mean_abs_gap | deciles_over_3pp |
| --- | --- | --- |
| V1 | 0.048 | 4 |
| V1_committee | 0.137 | 4 |
| V2 | 0.039 | 4 |
| V2_committee | 0.14 | 4 |
| V3 | 0.048 | 4 |
| V3_committee | 0.142 | 4 |
| V4 | 0.018 | 2 |
| V4_committee | 0.141 | 5 |
| V5 | 0.047 | 4 |
| V5_committee | 0.144 | 4 |

## Simulated score sensitivity

Fixed published baseline denominator (0.270), equal opportunity over Centre/Eloignee, accuracy agreement. All results are simulated only and inherit the assumptions and self-reference limitations above.

| variant | H1 | H1n10 | H1n5 | H2 | H3w0.25 | H3w0.5 | H3w1 | H4 | H5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V1 | 35.0 | 30.64 | 32.55 | 29.93 | 19.46 | 12.49 | 12.01 | 32.66 | 30.82 |
| V2 | 33.8 | 29.46 | 31.35 | 30.77 | 18.65 | 11.36 | 10.74 | 33.47 | 31.46 |
| V3 | 34.87 | 30.51 | 32.42 | 29.82 | 19.46 | 12.49 | 11.92 | 32.66 | 30.71 |
| V4 | 29.19 | 25.57 | 27.25 | 31.83 | 15.81 | 8.49 | 7.36 | 32.08 | 35.0 |
| V5 | 34.91 | 30.56 | 32.47 | 29.77 | 19.46 | 12.49 | 11.92 | 32.75 | 30.73 |

Detailed tables and named candidate CSVs are in `work/_local/strat1/`. No candidate is designated as the official submission.
