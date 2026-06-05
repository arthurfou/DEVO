# Résultats DEVO — EVIMO val split

Date des runs : 2026-06-03  
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

### Conclusion

Le filtrage GT ne produit pas d'amélioration mesurable. Deux hypothèses :
1. **Bug de filtrage** : les masques ne couvrent pas correctement les objets (à vérifier visuellement via l'app Gradio)
2. **Quantité insuffisante** : même si le filtrage était parfait, 0.5% d'events en moins ne suffit peut-être pas à impacter DEVO

La **prochaine étape** est de vérifier visuellement les masques via l'interface Gradio (tab "Filtrage EVIMO").
