# EVIMO Filtré — Guide complet

## C'est quoi ce dataset ?

`/home/i/i0002573/datasets/evimo_filtered_2805/eval/` est une copie du dataset EVIMO
original (`/home/i/i0002573/datasets/evimo/eval/`) dans laquelle les événements générés
par les **objets en mouvement** ont été supprimés.

**Pourquoi ?** DEVO est un système d'odométrie : il estime la trajectoire de la *caméra*.
Les événements des objets mobiles ne correspondent à aucune structure statique de la scène —
ils bruitent le flux d'événements et peuvent biaiser les estimations de pose.

**Ce qui a changé :** uniquement les fichiers `evs.npy`. Tous les autres fichiers
(`gt_stamped.txt`, `tss_imgs_us.txt`, `rectify_map.h5`, `calib.txt`, `extrinsics.txt`,
`config.txt`, `.bag`) sont copiés à l'identique. Le dataset filtré est un
**drop-in replacement** du dataset original.

**Résultat du filtrage (28 mai 2025) :**
1 459 631 événements supprimés sur 566 921 089 au total (**0.3 %**) — sur 21 séquences.

---

## Utilisation rapide

> Toutes les commandes utilisent l'environnement `devofou`.

### Lancer une évaluation DEVO sur le dataset filtré

```bash
cd /home/i/i0002573/test_perso/DEVO

conda run -n devofou python evals/eval_evs/eval_evimo_evs.py \
    --datapath /home/i/i0002573/datasets/evimo_filtered_2805/eval \
    --weights DEVO.pth \
    --val_split splits/evimo/evimo_val.txt \
    --plot \
    --save_trajectory
```

### Comparer avec le dataset original (non filtré)

```bash
conda run -n devofou python evals/eval_evs/eval_evimo_evs.py \
    --datapath /home/i/i0002573/datasets/evimo/eval \
    --weights DEVO.pth \
    --val_split splits/evimo/evimo_val.txt \
    --plot \
    --save_trajectory
```

Les résultats atterrissent dans des dossiers séparés (nommés d'après `--expname` ou
auto-générés avec timestamp), donc les deux runs peuvent coexister sans s'écraser.

### Ajouter un nom d'expérience pour s'y retrouver

```bash
conda run -n devofou python evals/eval_evs/eval_evimo_evs.py \
    --datapath /home/i/i0002573/datasets/evimo_filtered_2805/eval \
    --weights DEVO.pth \
    --val_split splits/evimo/evimo_val.txt \
    --plot \
    --save_trajectory \
    --expname filtered_2805
```

---

## Structure du dataset filtré

```
evimo_filtered_2805/
└── eval/
    ├── filter_stats.json              ← stats par séquence (JSON lisible)
    ├── box/raw/seq_00/
    │   ├── evs.npy                    ← REMPLACÉ (événements filtrés)
    │   ├── gt_stamped.txt             ← copié tel quel
    │   ├── tss_imgs_us.txt            ← copié tel quel
    │   ├── rectify_map.h5             ← copié tel quel
    │   ├── calib.txt
    │   ├── extrinsics.txt
    │   ├── config.txt
    │   └── seq_00.bag
    ├── box/raw/seq_01/ ...
    ├── fast/raw/seq_00/ ...
    ├── fast/raw/seq_01/ ...
    ├── floor/raw/seq_00/ ...
    ├── floor/raw/seq_01/ ...
    ├── table/raw/seq_00/ ...
    │   ...
    ├── tabletop/raw/seq_00/ ...
    │   ...
    └── wall/raw/seq_01/
```

Les 13 séquences du val split (`splits/evimo/evimo_val.txt`) sont toutes présentes
et ont les 4 fichiers requis par le script d'éval.

---

## Statistiques par séquence

| Séquence           | Événements avant | Supprimés   | %    | Couverture masque |
|--------------------|----------------:|------------:|-----:|------------------:|
| box/raw/seq_00     |     3 780 456   |           0 | 0.0% |             0.0%  |
| box/raw/seq_01     |     9 244 495   |         876 | 0.0% |             0.2%  |
| box/raw/seq_02     |     9 962 800   |           0 | 0.0% |             0.0%  |
| box/raw/seq_03     |     3 755 168   |           0 | 0.0% |             0.0%  |
| box/raw/seq_04     |     9 637 582   |           0 | 0.0% |             0.0%  |
| box/raw/seq_05     |    67 884 851   |       8 092 | 0.0% |             0.1%  |
| fast/raw/seq_00    |    14 945 517   |      57 561 | 0.4% |             0.5%  |
| fast/raw/seq_01    |    19 654 657   |     103 702 | 0.5% |             0.6%  |
| fast/raw/seq_02    |    73 191 504   |       4 904 | 0.0% |             0.0%  |
| floor/raw/seq_00   |    14 235 791   |           0 | 0.0% |             0.0%  |
| floor/raw/seq_01   |     5 623 680   |     107 737 | 1.9% |             1.2%  |
| table/raw/seq_00   |    13 010 266   |           0 | 0.0% |             0.0%  |
| table/raw/seq_01   |     7 520 343   |           0 | 0.0% |             0.0%  |
| table/raw/seq_02   |     3 230 803   |           0 | 0.0% |             0.0%  |
| table/raw/seq_03   |    93 300 311   |     622 799 | 0.7% |             0.8%  |
| tabletop/raw/seq_00|     5 711 906   |           0 | 0.0% |             0.0%  |
| tabletop/raw/seq_01|     2 210 388   |           0 | 0.0% |             0.0%  |
| tabletop/raw/seq_02|    33 828 859   |           0 | 0.0% |             0.0%  |
| tabletop/raw/seq_03|       817 448   |           0 | 0.0% |             0.0%  |
| wall/raw/seq_00    |    75 269 809   |     158 875 | 0.2% |             0.1%  |
| wall/raw/seq_01    |   100 104 455   |     395 085 | 0.4% |             0.3%  |
| **TOTAL**          | **566 921 089** | **1 459 631** | **0.3%** |           |

**Pourquoi autant de séquences à 0 % ?**
Les objets EVIMO sont de petits marqueurs plats (~3–9 cm de côté). Pour beaucoup de
séquences (notamment `box`, `tabletop`, `table/seq_00–02`), la trajectoire caméra ne
passe simplement pas devant les objets — ils sont en dehors du champ de la caméra pendant
tout l'enregistrement. La projection 3D→2D le confirme : les coins projetés ne tombent
jamais dans l'image 346×260 px. Ce n'est pas un bug, c'est la géométrie de la scène.

Stats lisibles en JSON : `/home/i/i0002573/datasets/evimo_filtered_2805/eval/filter_stats.json`

---

## Comment le filtrage fonctionne (pipeline)

Script : `scripts/filter_evimo_objects.py`

Pour chaque séquence :

1. **`config.txt`** → quels `Object_N` sont en mouvement
2. **`extrinsics.txt`** → transform rigide caméra→tracker Vicon `(R_E, t_E)` + demi-tailles
   de l'objet en mètres
3. **Bag ROS** → extraction des poses Vicon pour la caméra (`/vicon/DVS346`) et chaque
   objet mobile (`/vicon/Object_1`, etc.). Les frames occludées sont ignorées. Les poses
   sont interpolées : translation linéaire + rotation SLERP.
4. **Stack de masques binaires** à ~100 Hz (un masque par frame Vicon) :
   - Composition de la pose caméra dans le monde : `R_cam = R_V × R_E`, `t_cam = R_V × t_E + t_V`
   - Projection des 4 coins de chaque objet `(±half_x, ±half_y, 0)` dans l'image via
     OpenCV `cv2.projectPoints` avec modèle de distorsion complet
   - Remplissage du quadrilatère convexe avec `cv2.fillPoly`
   - Dilatation de 10 px pour absorber l'incertitude de projection
   - Union des masques de tous les objets mobiles
5. **Filtrage vectorisé** (numpy pur) :
   - Pour chaque event `(ts, x, y, p)` : trouver l'index Vicon le plus proche via `np.searchsorted`
   - `mask_stack[nearest_idx, ev_y, ev_x]` → supprimer l'event si dans le masque
6. **Écriture** : copie de tous les fichiers, remplacement de `evs.npy`

---

## Bugs corrigés dans le script

### Bug 1 — Convention du quaternion dans `extrinsics.txt` (critique)

**Symptôme :** toutes les séquences affichaient 0 % de suppression. En déboguant, tous
les objets avaient Z < 0 dans le repère caméra (derrière la caméra) sur chaque frame.

**Cause :** `extrinsics.txt` ligne 2 stocke le quaternion en **[w, x, y, z]**
(convention Vicon), mais `scipy.spatial.transform.Rotation.from_quat` attend **[x, y, z, w]**.
Lire les valeurs dans le mauvais ordre assignait `w ≈ 0.03` → rotation de ~183° au lieu
des ~8° réels → axe optique retourné → tous les objets "derrière" la caméra.

```
fast/seq_00 : quaternion dans le fichier = 0.997649  -0.0163983  0.0584856  -0.0317361
  Interprété [w,x,y,z] : w = 0.9976  →  θ ≈  8°   ✓ cohérent pour un extrinsèque caméra
  Interprété [x,y,z,w] : w = -0.0317 →  θ ≈ 183°  ✗ impossible physiquement
```

**Correction (`parse_extrinsics`) :**
```python
# Le fichier stocke [w, x, y, z] ; scipy attend [x, y, z, w]
qw, qx, qy, qz = float(lines[9]), float(lines[10]), float(lines[11]), float(lines[12])
R_E = Rotation.from_quat([qx, qy, qz, qw]).as_matrix()
```

### Bug 2 — Faux positifs par `np.clip` avant `fillPoly`

**Symptôme :** avant la correction du bug 1, certaines séquences supprimaient ~13 000
événements alors que la projection était fausse — des faux positifs.

**Cause :** quand les coins projetés atterrissaient hors image (ex. x = 3 000), le code
les clampait sur le bord de l'image avec `np.clip`, puis remplissait le polygone. Résultat :
un masque parasite le long du bord de l'image, qui supprimait des événements corrects
situés en bordure.

**Correction (`_project_object_mask`) :**
```python
# Suppression du np.clip ; ajout d'un test de bounding-box
xmin, xmax = pts_2d[:, 0].min(), pts_2d[:, 0].max()
ymin, ymax = pts_2d[:, 1].min(), pts_2d[:, 1].max()
if xmax < 0 or xmin >= W or ymax < 0 or ymin >= H:
    return None   # objet complètement hors image
# OpenCV gère lui-même le clipping du polygone sur le canvas
```

---

## Reproduire le filtrage depuis zéro

> Nécessite que `preprocess_evimo.py` ait déjà été lancé sur le dataset original
> (les fichiers `gt_stamped.txt`, `tss_imgs_us.txt`, `rectify_map.h5`, `evs.npy`
> doivent exister dans chaque séquence source).

```bash
cd /home/i/i0002573/test_perso/DEVO

# 1. Dry-run : calcule les stats sans rien écrire sur disque
conda run -n devofou python scripts/filter_evimo_objects.py \
    --datapath /home/i/i0002573/datasets/evimo/eval \
    --outpath  /tmp/evimo_dry \
    --dry_run

# 2. Run complet : produit le dataset filtré
conda run -n devofou python scripts/filter_evimo_objects.py \
    --datapath /home/i/i0002573/datasets/evimo/eval \
    --outpath  /home/i/i0002573/datasets/evimo_filtered_2805/eval
```

> **Important :** utiliser l'environnement `devofou` (pas `devo`). Il contient la version
> de `rosbags` avec l'API `Stores` nécessaire pour lire les bags ROS1.
