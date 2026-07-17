# `results/` — résultats d'évaluation DEVO

## `central_table*/` — tableau central du papier (5 configs × 21 scènes val EVIMO)

Produit par `evals/eval_evs/eval_evimo_central_table.py` via `scripts/slurm/slurm_m4_central_table.sh`.

| dossier | seed | checkpoints MS utilisés | date |
|---|---|---|---|
| `central_table/` | 1234 (défaut) | `results_coupled/m{2,3}/ms_final.pt` (initial) | 2026-07-17 |
| `central_table_seed1/` ... `central_table_seed5/` | 1..5 | `results_coupled/m{2,3}_seed{1..5}/ms_final.pt` | 2026-07-17+ |

Chaque `central_table*/` contient :
- `central_table.md` — tableau lisible (Markdown, ATE moyen + Δ vs vanilla par config)
- `central_table.csv` — même chose en CSV pour import LaTeX ou pandas
- `evimo_evs/2026-*/` — sous-dossiers avec trajectoires estimées, plots, saved_results/
  RPG par scène (21 dossiers × 5 configs = 105 sous-runs par tableau)

## `evimo_evs/YYYY-MM-DD_<expname>/` — résultats bruts par scène

Chaque run individuel produit un dossier daté avec un expname explicite :

- `2026-07-15_m0_vanilla/` — passe vanilla M0 v13 (13 scènes, avant extension)
- `2026-07-15_m0_oracle/` — passe oracle M0 v13
- `2026-07-15_m1_vanilla/`, `2026-07-15_m1_learned/`, `2026-07-15_m1_oracle/` — M1 v13
- `2026-07-16_m0_vanilla/`, `_m0_oracle/` — M0 v21 (val split étendu)
- `2026-07-16_m1_*` — M1 v21
- `2026-07-16_central_*` — sous-runs du premier M4 (via central_table_seed... indirection)

Chaque sous-dossier contient :
- `<scene_name>_Trial<N>_step_DEVO/` — un par scène
  - `stamped_traj_estimate.txt` — trajectoire estimée (RPG format)
  - `stamped_groundtruth.txt` — GT (RPG format)
  - `saved_results/traj_est/` — analyses RPG (relative/absolute error stats)
  - `map.ply` — carte de points (si `--map_path` était passé)
- `0_res.txt` — résumé ATE/MPE/R_rmse pour toutes les scènes du run
- `raw_results/` — historique des raw ATE

## Fichier CSV agrégé (à produire)

Pour produire un tableau de variance des 5 seeds :

```bash
python -c "
import pandas as pd, glob
dfs = []
for seed in range(1, 6):
    p = f'results/central_table_seed{seed}/central_table.csv'
    if not glob.glob(p): continue
    df = pd.read_csv(p); df['seed'] = seed
    dfs.append(df)
agg = pd.concat(dfs).groupby('config').agg(
    ate_mean=('ate_mean', 'mean'),
    ate_std=('ate_mean', 'std'),
    delta_mean=('delta_pct_vs_vanilla', 'mean'),
    delta_std=('delta_pct_vs_vanilla', 'std'),
)
print(agg.to_markdown())
"
```
