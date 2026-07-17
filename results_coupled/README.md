# `results_coupled/` — checkpoints des entraînements couplés

Chaque sous-dossier correspond à un run d'entraînement couplé (M2 supervisé ou M3
auto-supervisé). Contient les poids MS + DEVO + un `coupled_*.pt` (combo pour reprise),
sauvés tous les 2000 steps + un `*_final.*` en fin.

## Convention de nommage

| dossier | run | seed | date |
|---|---|---|---|
| `m2/` | **M2 initial** (avant sweep de variance) | non-seeded | 2026-07-16 |
| `m3/` | **M3 initial** (avant sweep de variance) | non-seeded | 2026-07-16 |
| `m2_seed1/` ... `m2_seed5/` | M2 sweep variance | seed=1..5 (torch/numpy/random/DataLoader) | 2026-07-17+ |
| `m3_seed1/` ... `m3_seed5/` | M3 sweep variance | seed=1..5 | 2026-07-17+ |

**Le premier run (`m2/` et `m3/`) n'est pas écrasé** : c'est la référence historique
utilisée pour le premier tableau `results/central_table/`.

## Contenu de chaque dossier

- `ms_final.pt` (~4 MB) — poids finaux du modèle MS convlstm (à brancher dans
  `LearnedDynMaskProvider` pour évaluation)
- `devo_final.pth` (~13.6 MB) — poids finaux de DEVO fine-tuné conjointement
- `coupled_final.pt` (~53 MB) — combo MS + DEVO + optimizer, pour reprise
- `ms_step{N}.pt`, `devo_step{N}.pth`, `coupled_step{N}.pt` — checkpoints tous les
  2000 steps (N = 2000, 4000, ..., 18000)

## Reproductibilité

Les runs seedés (`*_seed{N}/`) initialisent `torch.manual_seed(N)`,
`np.random.seed(N)`, `random.seed(N)`, `torch.cuda.manual_seed_all(N)`, et
`DataLoader worker_init_fn` seedé en cascade `N + worker_id`. Le générateur
`torch.Generator()` du DataLoader est aussi seedé pour l'ordre de shuffle.

Sources de non-déterminisme restantes :
- Kernels CUDA non-déterministes (Cholesky, scatter_add) — variance résiduelle attendue
  malgré le seeding.
- `torch.use_deterministic_algorithms(True)` n'est pas activé (ferait crasher certaines
  ops PyTorch 1.12 utilisées par DEVO).

## Fichiers produits en aval

Les évaluations M4 correspondantes sont dans `../results/central_table_seed{N}/`.
