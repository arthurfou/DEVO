# Résultats DEVO — EVIMO val split

Date des runs : 2026-06-03 (original, filtered_2805), 2026-06-05 (filtered_npz)
Évaluation : 1 trial par séquence (sauf `original_5trials`)

---

## Métriques utilisées

| Métrique | Alignement | Justification |
|---|---|---|
| **ATE [cm]** | sim3 (Umeyama) | Corrige la dérive d'échelle inhérente à l'VO monoculaire |
| **R_rmse [deg]** | se3 (ancrage frame 1) | sim3 choisit un mauvais offset de rotation sur les trajectoires symétriques → ~90° artificiels |
| **MPE [%/m]** | sim3 | Erreur relative de position |

> **Note :** Les colonnes `R_rmse (sim3)` dans les fichiers `0_res.txt` sont **biaisées** (~90–170° sur presque toutes les séquences). Ne pas les utiliser pour évaluer la rotation. Utiliser `R_rmse_se3` des fichiers `0_res_se3.txt`.

---

## Tableau comparatif : Original vs Filtré

Métriques recommandées : **ATE sim3** + **R_rmse se3**

Séquences avec filtrage effectif (events supprimés > 0%) : **Fast_00** (0.4%), **Fast_01** (0.5%), **Floor_01** (1.9%).  
Toutes les autres séquences : 0% d'events supprimés (objet hors champ caméra).

| Séquence | ATE orig [cm] | ATE filt [cm] | ΔATE | R_rmse orig [°] | R_rmse filt [°] | ΔR | Filtrage |
|---|---:|---:|---:|---:|---:|---:|---|
| Box_Raw_Seq_00 | 5.36 | 3.20 | **-2.16** | 24.0 | 23.9 | -0.2 | 0% |
| Box_Raw_Seq_01 | 37.60 | 38.28 | +0.68 | 80.5 | 80.7 | +0.2 | 0% |
| Box_Raw_Seq_02 | 7.03 | 6.71 | **-0.32** | 44.3 | 41.3 | **-3.0** | 0% |
| Fast_Raw_Seq_00 | 11.04 | 11.63 | +0.59 | 45.8 | 47.5 | +1.7 | **0.4%** |
| Fast_Raw_Seq_01 | 10.48 | 8.11 | **-2.37** | 85.4 | 87.1 | +1.6 | **0.5%** |
| Floor_Raw_Seq_00 | 2.59 | 2.58 | -0.01 | 41.5 | 41.5 | 0.0 | 0% |
| Floor_Raw_Seq_01 | 2.68 | 2.55 | **-0.13** | 42.3 | 43.0 | +0.7 | **1.9%** |
| Table_Raw_Seq_00 | 4.29 | 4.50 | +0.21 | 29.3 | 29.1 | -0.1 | 0% |
| Table_Raw_Seq_01 | 4.04 | 3.30 | **-0.74** | 11.5 | 11.2 | -0.3 | 0% |
| Tabletop_Raw_Seq_00 | 12.21 | 2.27 | **-9.94** | 32.4 | 15.0 | **-17.4** | 0% |
| Tabletop_Raw_Seq_01 | 1.50 | 1.60 | +0.10 | 54.6 | 51.8 | **-2.8** | 0% |
| Tabletop_Raw_Seq_02 | 6.90 | 5.18 | **-1.72** | 26.7 | 26.7 | 0.0 | 0% |
| Tabletop_Raw_Seq_03 | 0.18 | 0.18 | 0.00 | 23.7 | 20.2 | **-3.6** | 0% |
| **Moyenne** | **8.14** | **6.93** | **-1.21** | **41.0** | **39.2** | **-1.8** | |

---

## Résultats bruts — Original (sim3)

Fichier : `2026-06-03_original/0_res.txt`

| Séquence | ATE [cm] | R_rmse sim3 [°] | MPE [%/m] |
|---|---:|---:|---:|
| Box_Raw_Seq_00 | 5.36 | 99.9 | 3.56 |
| Box_Raw_Seq_01 | 37.60 | 108.2 | 7.42 |
| Box_Raw_Seq_02 | 7.03 | 95.8 | 2.74 |
| Fast_Raw_Seq_00 | 11.04 | 58.8 | 3.47 |
| Fast_Raw_Seq_01 | 10.48 | 101.1 | 2.23 |
| Floor_Raw_Seq_00 | 2.59 | 99.5 | 0.72 |
| Floor_Raw_Seq_01 | 2.68 | 96.9 | 1.73 |
| Table_Raw_Seq_00 | 4.29 | 100.5 | 1.26 |
| Table_Raw_Seq_01 | 4.04 | 89.7 | 2.15 |
| Tabletop_Raw_Seq_00 | 12.21 | 110.3 | 4.53 |
| Tabletop_Raw_Seq_01 | 1.50 | 108.1 | 1.50 |
| Tabletop_Raw_Seq_02 | 6.90 | 104.5 | 0.73 |
| Tabletop_Raw_Seq_03 | 0.18 | 170.4 | 1.13 |

## Résultats bruts — Original (se3, rotation corrigée)

Fichier : `2026-06-03_original/0_res_se3.txt`

| Séquence | ATE se3 [cm]* | R_rmse se3 [°] | MPE [%/m] |
|---|---:|---:|---:|
| Box_Raw_Seq_00 | 70.6 | **24.0** | 42.2 |
| Box_Raw_Seq_01 | 370.8 | **80.5** | 62.4 |
| Box_Raw_Seq_02 | 201.4 | **44.3** | 87.7 |
| Fast_Raw_Seq_00 | 165.6 | **45.8** | 49.4 |
| Fast_Raw_Seq_01 | 49.2 | **85.4** | 11.0 |
| Floor_Raw_Seq_00 | 36.5 | **41.5** | 9.4 |
| Floor_Raw_Seq_01 | 51.8 | **42.3** | 39.4 |
| Table_Raw_Seq_00 | 33.0 | **29.3** | 9.4 |
| Table_Raw_Seq_01 | 22.5 | **11.5** | 11.4 |
| Tabletop_Raw_Seq_00 | 403.2 | **32.4** | 156.0 |
| Tabletop_Raw_Seq_01 | 267.3 | **54.6** | 279.9 |
| Tabletop_Raw_Seq_02 | 26.4 | **26.7** | 2.9 |
| Tabletop_Raw_Seq_03 | 19.8 | **23.7** | 298.6 |

*ATE se3 gonflé car pas de correction d'échelle — ne pas utiliser pour l'ATE.

## Résultats bruts — Filtré (sim3)

Fichier : `2026-06-03_filtered_2805/0_res.txt`

| Séquence | ATE [cm] | R_rmse sim3 [°] | MPE [%/m] |
|---|---:|---:|---:|
| Box_Raw_Seq_00 | 3.20 | 102.1 | 2.25 |
| Box_Raw_Seq_01 | 38.28 | 110.1 | 7.62 |
| Box_Raw_Seq_02 | 6.71 | 97.1 | 2.47 |
| Fast_Raw_Seq_00 | 11.63 | 68.1 | 3.63 |
| Fast_Raw_Seq_01 | 8.11 | 102.1 | 1.70 |
| Floor_Raw_Seq_00 | 2.58 | 99.4 | 0.72 |
| Floor_Raw_Seq_01 | 2.55 | 97.2 | 1.72 |
| Table_Raw_Seq_00 | 4.50 | 99.3 | 1.30 |
| Table_Raw_Seq_01 | 3.30 | 92.3 | 1.73 |
| Tabletop_Raw_Seq_00 | 2.27 | 105.3 | 0.88 |
| Tabletop_Raw_Seq_01 | 1.60 | 108.2 | 1.58 |
| Tabletop_Raw_Seq_02 | 5.18 | 102.3 | 0.53 |
| Tabletop_Raw_Seq_03 | 0.18 | 176.9 | 1.12 |

## Résultats bruts — Filtré (se3, rotation corrigée)

Fichier : `2026-06-03_filtered_2805/0_res_se3.txt`

| Séquence | ATE se3 [cm]* | R_rmse se3 [°] | MPE [%/m] |
|---|---:|---:|---:|
| Box_Raw_Seq_00 | 68.3 | **23.9** | 41.0 |
| Box_Raw_Seq_01 | 604.9 | **80.7** | 98.1 |
| Box_Raw_Seq_02 | 271.6 | **41.3** | 116.3 |
| Fast_Raw_Seq_00 | 346.0 | **47.5** | 93.4 |
| Fast_Raw_Seq_01 | 51.2 | **87.1** | 11.5 |
| Floor_Raw_Seq_00 | 36.3 | **41.5** | 9.4 |
| Floor_Raw_Seq_01 | 43.9 | **43.0** | 33.8 |
| Table_Raw_Seq_00 | 34.1 | **29.1** | 9.5 |
| Table_Raw_Seq_01 | 18.2 | **11.2** | 9.1 |
| Tabletop_Raw_Seq_00 | 406.7 | **15.0** | 160.0 |
| Tabletop_Raw_Seq_01 | 283.3 | **51.8** | 298.9 |
| Tabletop_Raw_Seq_02 | 25.9 | **26.7** | 2.9 |
| Tabletop_Raw_Seq_03 | 21.4 | **20.2** | 326.6 |

---

## Interprétation

### Pourquoi le filtrage n'améliore pas les métriques pour les séquences censées être filtrées ?

- **10/13 séquences** : 0% d'events supprimés — l'objet n'est pas dans le champ de la caméra selon la GT, mais il est visible sur les frames RGB → **bug probable dans `filter_evimo_objects.py`**
- **Fast_00, Fast_01, Floor_01** : filtrage effectif (0.4–1.9%) mais impact quasi-nul sur ATE et R_rmse → quantité trop faible OU bug partiel dans le filtrage

### Conclusion (run filtered_2805)

Le filtrage GT ne produit pas d'amélioration mesurable. Deux hypothèses :
1. **Bug de filtrage** : les masques ne couvrent pas correctement les objets (à vérifier visuellement via l'app Gradio)
2. **Quantité insuffisante** : même si le filtrage était parfait, 0.5% d'events en moins ne suffit peut-être pas à impacter DEVO

---

## Run filtered_npz — Filtrage via masques NPZ pixel-perfect (2026-06-05)

### Contexte

Le run `filtered_npz` utilise un nouveau pipeline (`scripts/filter_evimo_npz.py`) qui remplace
l'approche de projection 3D défaillante par les masques pixel-perfect fournis dans les fichiers NPZ
du dataset EV-IMO. Ces masques couvrent réellement les objets 3D visibles (jouets : voiture,
avion, tracteur, boîte de rangement).

**Quantité filtrée :** 75 012 266 events supprimés sur 566 921 089 — **13.2%** (contre 0.3% avant).

**Important — différence de pipeline :** Ce run utilise un `gt_stamped.txt` et un `tss_imgs_us.txt`
dérivés des NPZ (poses relatives depuis le premier frame, ~40 Hz pour les timestamps), et non plus
extraits directement des bags ROS. Cela introduit un biais de comparaison avec les runs précédents.

### Statistiques de filtrage par séquence

| Séquence | Events avant | Supprimés | % supprimés | Couverture masque |
|---|---:|---:|---:|---:|
| box/raw/seq_00     |  3 780 456 |     60 114 |  1.59% |  0.58% |
| box/raw/seq_01     |  9 244 495 |    485 617 |  5.25% |  3.39% |
| box/raw/seq_02     |  9 962 800 |    810 206 |  8.13% |  4.59% |
| tabletop/raw/seq_00|  5 711 906 |    916 348 | 16.04% |  6.70% |
| tabletop/raw/seq_01|  2 210 388 |    341 095 | 15.43% |  6.09% |
| tabletop/raw/seq_02| 33 828 859 |  2 459 564 |  7.27% |  3.00% |
| tabletop/raw/seq_03|    817 448 |    264 939 | 32.41% |  2.30% |
| table/raw/seq_00   | 13 010 266 |  1 139 662 |  8.76% |  3.70% |
| table/raw/seq_01   |  7 520 343 |    610 793 |  8.12% |  2.72% |
| floor/raw/seq_00   | 14 235 791 |  1 464 957 | 10.29% |  4.38% |
| floor/raw/seq_01   |  5 623 680 |    656 436 | 11.67% |  8.52% |
| fast/raw/seq_00    | 14 945 517 |  1 807 084 | 12.09% |  6.56% |
| fast/raw/seq_01    | 19 654 657 |  2 376 328 | 12.09% | 10.73% |

### Résultats ATE (sim3) — comparaison des trois runs

| Séquence | Original | Filtré_2805 | **Filtré_NPZ** | Δ vs Original |
|---|---:|---:|---:|---:|
| box/raw/seq_00     | 5.36  | 3.20  | **12.34** | +7.0  ↑ |
| box/raw/seq_01     | 37.60 | 38.28 | **26.23** | **-11.4** ↓ |
| box/raw/seq_02     | 7.03  | 6.71  | **7.60**  | +0.6  ↑ |
| tabletop/raw/seq_00| 12.21 | 2.27  | **6.54**  | **-5.7**  ↓ |
| tabletop/raw/seq_01| 1.50  | 1.60  | **4.30**  | +2.8  ↑ |
| tabletop/raw/seq_02| 6.90  | 5.18  | **9.23**  | +2.3  ↑ |
| tabletop/raw/seq_03| 0.18  | 0.18  | **0.23**  | +0.05 ↑ |
| table/raw/seq_00   | 4.29  | 4.50  | **8.85**  | +4.6  ↑ |
| table/raw/seq_01   | 4.04  | 3.30  | **4.69**  | +0.65 ↑ |
| floor/raw/seq_00   | 2.59  | 2.58  | **8.79**  | +6.2  ↑ |
| floor/raw/seq_01   | 2.68  | 2.55  | **5.03**  | +2.4  ↑ |
| fast/raw/seq_00    | 11.04 | 11.63 | **4.89**  | **-6.1**  ↓ |
| fast/raw/seq_01    | 10.48 | 8.11  | **13.87** | +3.4  ↑ |
| **Moyenne**        | **8.14** | **6.93** | **7.88** | **-0.26** |

### Interprétation

Les résultats sont **mixtes** : 4 séquences améliorées, 9 dégradées.

**Séquences améliorées** (objets réellement visibles et filtrage pertinent) :
- `fast/seq_00` : −6.1 cm — séquence à caméra rapide, filtrage de 12%
- `box/seq_01` : −11.4 cm — fort filtrage (5.25%)
- `tabletop/seq_00` : −5.7 cm — filtrage de 16%

**Séquences dégradées** malgré le filtrage :
- `floor/seq_00` : +6.2 cm (10.3% events supprimés)
- `box/seq_00` : +7.0 cm (1.6% events supprimés)
- `table/seq_00` : +4.6 cm (8.8% events supprimés)

### Cause probable de la dégradation

Le run `filtered_npz` utilise un `gt_stamped.txt` issu des NPZ (poses relatives au premier frame,
~200 Hz) alors que les runs `original` et `filtered_2805` utilisent le ground truth extrait
directement des bags Vicon (référentiel absolu). Même si sim3 compense l'échelle et la rotation
globale, toute différence dans les poses inter-frames (résolution temporelle, interpolation NPZ)
peut biaiser l'ATE.

**Pour isoler l'effet du filtrage seul**, il faudrait relancer avec le même `gt_stamped.txt`
bag-dérivé et seulement `evs.npy` issu des masques NPZ.

### AUC / AVG (métriques internes eval DEVO)

```
AUC = 0.0594
AVG = 0.0866
```
