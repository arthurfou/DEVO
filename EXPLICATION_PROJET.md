# DEVO — Deep Event Visual Odometry : Explication Complète du Projet

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Structure des fichiers](#structure-des-fichiers)
3. [Architecture du modèle](#architecture-du-modèle)
4. [Flux de données](#flux-de-données)
5. [Composants principaux](#composants-principaux)
6. [Configuration](#configuration)
7. [Scripts et utilitaires](#scripts-et-utilitaires)
8. [Entraînement](#entraînement)
9. [Inférence](#inférence)
10. [Innovations clés](#innovations-clés)
11. [Dépendances et extensions CUDA](#dépendances-et-extensions-cuda)

---

## Vue d'ensemble

DEVO (*Deep Event Visual Odometry*) est un système d'odométrie visuelle basée sur des **caméras événementielles** (*event cameras*). Contrairement aux caméras classiques qui capturent des images à fréquence fixe, une caméra événementielle enregistre chaque changement de luminosité pixel par pixel avec une précision temporelle de l'ordre de la microseconde.

L'objectif de DEVO est d'estimer la **trajectoire 3D d'une caméra** dans l'espace (poses + profondeurs) en temps réel à partir de ce flux d'événements, sans capteur IMU ni caméra stéréo. Il s'agit donc d'odométrie **monoculaire** basée sur des événements.

Le système combine :
- Des **réseaux de neurones profonds** (CNN, GRU) pour extraire des features et prédire le flux optique
- Une **optimisation géométrique différentiable** (Bundle Adjustment) pour affiner les poses et profondeurs
- Des **opérations sur les groupes de Lie** (SE3) pour représenter les transformations rigides

---

## Structure des fichiers

```
DEVO/
├── devo/                          # Package Python principal
│   ├── devo.py                   # Pipeline d'inférence temps réel
│   ├── enet.py                   # Réseau de neurones (eVONet)
│   ├── config.py                 # Paramètres d'inférence
│   ├── ba.py                     # Bundle Adjustment différentiable
│   ├── blocks.py                 # Blocs de réseaux de neurones
│   ├── selector.py               # Sélection de patches
│   ├── extractor.py              # Encodeurs d'extraction de features
│   ├── projective_ops.py         # Opérations de projection géométrique
│   ├── logger.py                 # Logging pour l'entraînement
│   ├── utils.py                  # Utilitaires généraux
│   ├── plot_utils.py             # Visualisation
│   ├── altcorr/                  # Extension CUDA : corrélation croisée
│   ├── fastba/                   # Extension CUDA/C++ : Bundle Adjustment rapide
│   ├── lietorch/                 # Extension CUDA/C++ : groupes de Lie
│   └── data_readers/             # Chargement et prétraitement des datasets
│       ├── base.py
│       ├── tartan.py
│       ├── factory.py
│       └── augmentation.py
│
├── evals/eval_evs/               # Scripts d'évaluation par dataset
│   ├── eval_rpg_evs.py
│   ├── eval_tartan_evs.py
│   ├── eval_mvsec_evs.py
│   └── eval_evimo_evs.py
│
├── utils/                        # Utilitaires partagés
│   ├── event_utils.py           # Traitement des événements
│   ├── eval_utils.py            # Métriques d'évaluation
│   ├── voxel_utils.py           # Voxel grids d'événements
│   ├── pose_utils.py            # Manipulations de poses
│   └── viz_utils.py             # Visualisation de trajectoires
│
├── scripts/                      # Prétraitement des datasets
│   ├── pp_rpg.py                # Dataset RPG
│   ├── pp_mvsec.py              # Dataset MVSEC
│   ├── pp_tumvie.py             # Dataset TUM-VIE
│   ├── pp_evimo.py              # Dataset EVIMO
│   ├── filter_evimo_objects.py  # Filtrage d'objets en mouvement
│   ├── preprocess_evimo.py
│   └── e2v/                     # Event-to-video
│
├── config/                       # Fichiers de configuration
│   ├── DEVO_base.conf           # Config d'entraînement principale
│   ├── default_evs.yaml         # Config d'inférence par défaut
│   └── eval_*.yaml              # Configs d'évaluation par dataset
│
├── splits/                       # Listes train/val par dataset
│   ├── tartan/
│   ├── rpg/
│   ├── mvsec/
│   └── evimo/
│
├── train.py                      # Script d'entraînement principal
├── setup.py                      # Build du package + extensions CUDA
├── environment.yml              # Environnement Conda
├── download_model.sh            # Téléchargement du modèle pré-entraîné
└── thirdparty/                   # Bibliothèques tierces
    ├── eigen-3.4.0              # Algèbre linéaire C++
    ├── rpg_trajectory_evaluation/
    └── tartanair_tools/
```

---

## Architecture du modèle

Le cœur du système est **eVONet** (`devo/enet.py`), composé de plusieurs modules :

### 1. Encodeurs de features (`extractor.py`)

**BasicEncoder4Evs** — Encodeur pour données événementielles :
- Entrée : grille de voxels d'événements `(B, bins, H, W)` avec `bins = 5` canaux temporels
- Sortie : cartes de features à résolution 1/4
- Deux variantes parallèles :
  - `fnet` (matching features, 128 dimensions) : utilisé pour le calcul de corrélation croisée
  - `inet` (context features, 384 dimensions) : contexte pour le module de mise à jour
- Utilise de la normalisation d'instance (*instance normalization*)

### 2. Patchifier — Extraction de patches

Extrait des patches locaux depuis les cartes de features :
- **fmap** : features pour le flux optique (128-dim, utilisé dans la corrélation)
- **imap** : features de contexte (384-dim, utilisé dans le GRU)
- **gmap** : templates de matching (128-dim)

**Nombre de patches** : 80 par frame par défaut (96 en inférence)

### 3. Sélection de patches (`selector.py`)

Trois modes de sélection :

| Mode | Description |
|------|-------------|
| `random` | Échantillonnage uniforme aléatoire |
| `gradient` | Favorise les régions à fort gradient |
| `scorer` (défaut) | Réseau CNN appris qui prédit une carte de saillance |

Le **scorer** apprend quels patches sont trackables et informatifs. En inférence, il utilise un échantillonnage multinomial pondéré (`multi` mode) pour diversifier la sélection tout en favorisant les patches de haute confiance.

### 4. Opérateur de mise à jour (*Update Operator*)

Module itératif (18 itérations par séquence) qui raffine le flux optique :

```
Entrées :
  - Volume de corrélation (corrélation croisée entre patches de frames adjacentes)
  - Features de contexte (imap)
  - Estimations précédentes (flow, poses, profondeurs)

Traitements :
  - MLPs pour traiter les features
  - SoftAgg : agrégation pondérée sur les patches et frames voisins
  - GatedResidual (GRU-like) : récurrence pour mémoire temporelle

Sorties :
  - Delta de flux optique (B, edges, 2)
  - Poids de confiance pour le Bundle Adjustment (B, edges, 2)
```

### 5. Bundle Adjustment différentiable (`ba.py`)

Optimisation géométrique qui raffine poses et profondeurs :
- Formule le problème comme des **moindres carrés pondérés**
- Construit la **matrice Hessienne** à partir des résidus de flux optique et des poids de confiance
- Résout avec une **décomposition de Cholesky** (implémentée en CUDA)
- Opère sur un fenêtre glissante de 12 frames (optimization window)
- **Différentiable** : les gradients peuvent traverser l'optimisation pour l'entraînement end-to-end

---

## Flux de données

### Entraînement

```
Dataset TartanAir (RGB-D)
        ↓
Génération d'événements synthétiques (vid2e)
        ↓
Batch de séquences :
  images    : (B, T, bins, H, W)   — voxels d'événements, T=15 frames
  poses     : (B, T, 7)             — [tx, ty, tz, qx, qy, qz, qw]
  disps     : (B, T, H, W)          — cartes de profondeur inverse (ground truth)
  intrinsics: (B, T, 4)             — [fx, fy, cx, cy]
        ↓
[eVONet forward]
  1. Normalisation des voxels (rescale / std / none)
  2. Augmentation aléatoire (flips, permutations temporelles)
  3. Extraction des features : fmap, imap, gmap (via BasicEncoder4Evs)
  4. Sélection de patches (scorer ou random)
  5. 18 itérations de l'Update Operator :
     - Reprojection des patches dans la frame suivante
     - Calcul du volume de corrélation
     - Prédiction du delta de flux + poids de confiance
     - Bundle Adjustment différentiable (mise à jour poses + disps)
        ↓
Calcul des pertes (sur toutes les itérations, avec pondération croissante) :
  - Flow loss   : ||flow_pred - flow_gt||² × 0.1
  - Pose loss   : distance SE3 log × 10.0
  - Scores loss : régularisation du scorer × 0.05
        ↓
Rétropropagation → mise à jour AdamW
```

### Inférence (temps réel)

```
Flux de la caméra événementielle
        ↓
[Accumulation d'événements par tranche temporelle]
        ↓
Grille de voxels (bins=5, H, W) normalisée
        ↓
[DEVO.__call__ — devo/devo.py]
        ↓
[Patchifier]
  - Extraction des features fmap, imap, gmap
  - Sélection des 96 meilleurs patches (scorer)
        ↓
[Update Operator] × itérations :
  - Corrélation croisée entre patches et frames de référence
  - Prédiction du flux optique δ
  - Mise à jour incrémentale des poses
        ↓
[Bundle Adjustment] sur la fenêtre glissante (10 frames)
        ↓
[Gestion des keyframes] :
  - Si mouvement < seuil (15 px) → suppression de la frame redondante
  - Maintient max 2048 keyframes en mémoire
        ↓
Trajectoire finale : poses horodatées (T, 7)
```

---

## Composants principaux

### `devo/devo.py` — Pipeline d'inférence

Classe `DEVO` : système complet de traitement en streaming.

**Attributs d'état** (mis à jour à chaque frame) :
- `poses` : transformations SE3 de toutes les keyframes
- `patches` : coordonnées 3D des patches dans les frames de référence
- `imap` / `gmap` : features stockées pour chaque patch
- `correlation_volumes` : corrélations pré-calculées pour chaque frame

**Méthodes principales** :
- `__call__(tstamp, image, intrinsics)` : traite une nouvelle frame
- `terminate()` : déclenche une optimisation finale et retourne la trajectoire complète
- `_remove_keyframe(ix)` : supprime une keyframe redondante

**Normalisation** (paramètre `NORM`) :
| Valeur | Comportement |
|--------|-------------|
| `rescale` | Redimensionne dans [-1, 1] |
| `std` | Normalisation par écart-type (frame par frame) |
| `std2` | Normalisation par écart-type (séquence entière) |
| `none` | Pas de normalisation |

### `devo/enet.py` — eVONet

Classe principale `VONet` (entraînement) et `eVONet` (inférence) :

```python
class VONet(nn.Module):
    def __init__(self):
        self.fnet = BasicEncoder4Evs(128)   # matching features
        self.inet = BasicEncoder4Evs(384)   # context features
        self.update = UpdateModule()         # GRU iteratif
        self.scorer = ScorerNet()            # sélection de patches
```

### `devo/ba.py` — Bundle Adjustment

Implémente `BA` (différentiable, PyTorch) et appelle `FastBA` (CUDA/C++) :
- Prend en entrée : patches, poses, flux optique prédit, poids de confiance, intrinsèques
- Produit : corrections de poses δξ et de profondeurs δd
- Utilise les **jacobiennes** du modèle de projection pour construire le système linéaire

---

## Configuration

### `config/DEVO_base.conf` — Entraînement

```ini
evs = True                    # Mode événementiel (vs RGB)
patch_selector = "scorer"     # Sélection apprise
norm = "std2"                 # Normalisation séquence entière
patches_per_image = 80        # Patches par frame
iters = 18                    # Itérations de l'update operator
batch_size = 1
steps = 240000
lr = 0.00008
pose_weight = 10.0
flow_weight = 0.1
scores_weight = 0.05
```

### `config/default_evs.yaml` — Inférence

```yaml
PATCHES_PER_FRAME: 96
OPTIMIZATION_WINDOW: 10       # Fenêtre BA : 10 frames
PATCH_LIFETIME: 13            # Durée de vie max d'un patch
PATCH_SELECTOR: 'scorer'
NORM: 'std'
SCORER_EVAL_MODE: 'multi'     # Échantillonnage multinomial
KEYFRAME_THRESH: 15           # Seuil de suppression en pixels
```

### `devo/config.py`

Valeurs par défaut pour l'inférence, surchargées par le fichier YAML :
```python
PATCHES_PER_FRAME = 80
REMOVAL_WINDOW = 20
OPTIMIZATION_WINDOW = 12
PATCH_LIFETIME = 13
KEYFRAME_THRESH = 15.0
PATCH_SELECTOR = 'scorer'
NORM = 'std'
```

---

## Scripts et utilitaires

### Prétraitement des datasets (`scripts/pp_*.py`)

Chaque script suit le même pattern pour un dataset donné :
1. Lecture des données brutes (events, images, calibration)
2. Rectification (correction de la distorsion optique)
3. Extraction des timestamps
4. Sauvegarde au format HDF5 ou NumPy

| Script | Dataset |
|--------|---------|
| `pp_rpg.py` | RPG Event Camera Dataset |
| `pp_mvsec.py` | MVSEC (Multi Vehicle Stereo Event Camera) |
| `pp_tumvie.py` | TUM-VIE |
| `pp_evimo.py` | EVIMO (événements avec objets mobiles) |

### `scripts/filter_evimo_objects.py`

Script spécialisé pour EVIMO : filtre les événements générés par des **objets en mouvement** (qui perturbent l'odométrie ego-motion) :
1. Lit les poses Vicon depuis des bags ROS
2. Projette les objets 3D dans l'espace image à chaque timestamp
3. Crée des masques binaires avec dilatation morphologique
4. Filtre vectoriellement les événements qui tombent dans les masques

### `utils/event_utils.py`

- **`EventSlicer`** : lecture efficace depuis HDF5 par tranche temporelle
- **`to_voxel_grid`** : conversion événements → grille de voxels tensorielle
- **`RemoveHotPixelsVoxel`** : suppression des pixels bruyants permanents (hot pixels)

---

## Entraînement

### Données

DEVO est entraîné sur **TartanAir** (dataset synthétique RGB-D avec variété de scènes). Les événements sont synthétisés à partir des images RGB via **vid2e**.

Trois modes de dataset (`data_readers/tartan.py`) :
- `TartanAir` : RGB natif
- `TartanAirEVS` : événements synthétiques
- `TartanAirE2VID` : reconstruction E2VID (events → pseudo-images)

### Commande d'entraînement

```bash
python train.py \
  -c config/DEVO_base.conf \
  --name mon_experience \
  --datapath /path/to/tartan \
  --steps 240000 \
  --batch 1 \
  --ddp --gpu_num 4
```

### Boucle d'entraînement (`train.py`)

1. Initialisation du modèle `eVONet` + optimizer `AdamW` + scheduler `OneCycleLR`
2. Support DDP (Distributed Data Parallel) multi-GPU
3. Pour chaque batch :
   - Forward pass → prédictions de flux, poses, profondeurs (× 18 itérations)
   - Calcul des 3 pertes (flow, pose, scores)
   - `loss.backward()` + gradient clipping (max norm = 25)
   - `optimizer.step()` + `scheduler.step()`
4. Sauvegarde checkpoint tous les 10k steps
5. Validation périodique optionnelle

---

## Inférence

### Installation

```bash
# Cloner avec sous-modules
git clone https://github.com/tum-vision/DEVO.git --recursive
cd DEVO

# Dépendances C++
wget https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.zip
unzip eigen-3.4.0.zip -d thirdparty

# Environnement Conda
conda env create -f environment.yml
conda activate devofou

# Compilation des extensions CUDA
pip install .
```

### Téléchargement du modèle pré-entraîné

```bash
./download_model.sh
```

### Prétraitement du dataset

```bash
python scripts/pp_rpg.py --datapath /path/to/rpg_dataset
```

### Évaluation

```bash
python evals/eval_evs/eval_rpg_evs.py \
  --datapath /path/to/rpg \
  --weights DEVO.pth \
  --val_split splits/rpg/rpg_val.txt \
  --plot \
  --save_trajectory \
  --expname mon_run
```

Les résultats (métriques ATE/RPE, trajectoires, courbes) sont sauvegardés dans `results/rpg_evs/mon_run/`.

---

## Innovations clés

### 1. Sélection apprise de patches (Scorer Network)
Les méthodes classiques utilisent une sélection aléatoire ou basée sur le gradient. DEVO apprend quel patches sont les plus trackables et informatifs via un petit CNN. En entraînement, il sélectionne le top-k parmi 3× plus de candidats. En inférence, l'échantillonnage multinomial assure la diversité spatiale.

### 2. Bundle Adjustment différentiable
L'optimisation géométrique est intégrée dans le graphe de calcul PyTorch. Le réseau apprend à produire des flux optiques dont les résidus se réduisent efficacement lors du BA. Cela ferme la boucle entre apprentissage et optimisation géométrique.

### 3. Normalisation adaptée aux événements
Les voxels d'événements ont une distribution très différente des images RGB. La normalisation séquence-entière (`std2`) préserve la structure temporelle tout en homogénéisant les magnitudes entre scènes.

### 4. Tracking sparse par patches
Au lieu de calculer un flux dense (coûteux), DEVO ne tracke que ~80-96 patches par frame. Cela permet un traitement temps réel (~25 FPS sur GPU V100) tout en maintenant une précision élevée.

### 5. Odométrie monoculaire pure
Contrairement à la plupart des méthodes événementielles antérieures qui nécessitaient stéréo ou IMU, DEVO fonctionne avec une seule caméra événementielle. La profondeur est estimée implicitement par cohérence photométrique multi-vues.

---

## Dépendances et extensions CUDA

### LieTorch (`devo/lietorch/`)
Bibliothèque CUDA/C++ pour opérations sur les groupes de Lie :
- **SE3** : transformations rigides (translation + rotation) — représentation des poses caméra
- **Sim3** : transformations similaires (avec échelle)
- Opérations de batch efficaces pour le calcul de jacobienne

### FastBA (`devo/fastba/`)
Kernel CUDA pour le Bundle Adjustment rapide :
- Factorisation creuse (sparse factorization)
- Décomposition de Cholesky sur GPU
- Gère des milliers d'observations (patches × frames)

### AltCorr (`devo/altcorr/`)
Calcul efficace du volume de corrélation croisée :
- Corrélation multi-niveaux (pyramide de features)
- Implémentation GPU optimisée pour le flux optique

### Eigen (`thirdparty/eigen-3.4.0/`)
Bibliothèque C++ d'algèbre linéaire, utilisée par FastBA et LieTorch pour les calculs matriciels côté CPU.

---

## Résumé du pipeline complet

```
Caméra événementielle
        │
        ▼
  Grille de voxels (5 bins temporels)
        │
        ▼
  Normalisation (std / rescale)
        │
        ▼
  BasicEncoder4Evs ──► fmap (128d) ──► Corrélation croisée ─┐
                   └──► imap (384d) ──► Contexte GRU        │
                   └──► gmap (128d) ──► Templates matching  │
        │                                                    │
        ▼                                                    │
  Scorer Network ──► Sélection de 96 patches                │
        │                                                    │
        ▼            ◄──────────────────────────────────────┘
  Update Operator (×18 itérations) :
    GRU + MLP + SoftAgg
        │
        ▼ (flux optique δ + poids confiance)
  Bundle Adjustment (CUDA) :
    Cholesky → δξ (correction poses) + δd (correction profondeurs)
        │
        ▼
  Gestion keyframes (fenêtre glissante de 10 frames)
        │
        ▼
  Trajectoire horodatée : poses SE3 (N, 7)
```

Ce pipeline combine élégamment apprentissage profond et optimisation géométrique pour obtenir une odométrie visuelle précise, robuste aux conditions difficiles (faible éclairage, flou de mouvement rapide) inhérentes aux caméras événementielles.
