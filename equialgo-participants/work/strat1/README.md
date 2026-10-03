# Run the five counterfactual model variants

From the repository root, using the existing environment:

```powershell
.\.venv\Scripts\python.exe equialgo-participants\work\strat1\neutralise.py
```

The default seed is 42. Candidate predictions and diagnostic CSVs go to ignored `work/_local/strat1/`; a compact measured report is written to `work/strat1/report_01.md`. `--output-dir` overrides the generated-data directory. The shared validator checks each candidate file for the exact candidate ID order, binary decisions and budget.

The parent audit independently reproduced the runner: all five candidates grant exactly 1,600 of 4,000 scholarships. V4's mean pairwise Jaccard stability is 0.917, below the plan's 0.95 target; its lower conditional gap does not establish that it should be adopted. Logistic variants have Jaccard means around 0.979–0.982. None is selected as an official submission.

The five-refit experiment is smaller than the proposed 25 refits. Selected-C AUC reuses the tuning folds, and simulated references partly share model families with the predictions. Those scores are sensitivity estimates, not independent accuracy or official scores. Full acceptance, additional seeds and hidden-reference calibration remain unfinished.
