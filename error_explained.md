# Pourquoi l'estimation démarre décalée en orientation (yaw/pitch/roll)

## Symptôme observé

Sur certaines séquences (notamment **Box Seq 00**), les courbes d'erreur yaw/pitch/roll
montrent un offset **constant** dès le début, au lieu de démarrer à zéro.
Ce n'est pas une dérive de l'odométrie — c'est un problème d'alignement.

---

## La chaîne jusqu'au plot

Le plot d'erreur RPY vient de `compute_absolute_error` dans
`thirdparty/rpg_trajectory_evaluation/src/rpg_trajectory_evaluation/compute_trajectory_errors.py:68` :

```python
e_R = np.dot(R_we, np.linalg.inv(R_wg))
e_ypr[i, :] = tf.euler_from_matrix(e_R, 'rzyx')
```

C'est l'erreur d'orientation **après alignement** de la trajectoire estimée sur le GT.
La valeur est ensuite plottée dans `thirdparty/rpg_trajectory_evaluation/scripts/analyze_trajectory_single.py:213` :

```python
plot_traj.abs_errors['abs_e_ypr'] * 180.0/np.pi  # labels=['yaw', 'pitch', 'roll']
```

---

## Le vrai problème : l'alignement Umeyama n'utilise que les positions

Avant de calculer les erreurs, la trajectoire estimée est alignée sur le GT via `sim3`
(alignement par défaut) dans `thirdparty/rpg_trajectory_evaluation/src/rpg_trajectory_evaluation/trajectory.py:250` :

```python
self.scale, self.rot, self.trans = au.alignTrajectory(
    self.p_es, self.p_gt, self.q_es, self.q_gt,
    self.align_type, self.align_num_frames)
```

Et dans `thirdparty/rpg_trajectory_evaluation/src/rpg_trajectory_evaluation/align_utils.py:104`,
la méthode `sim3` appelle Umeyama :

```python
def alignSIM3(p_es, p_gt, q_es, q_gt, n_aligned=-1):
    ...
    s, R, t = align.align_umeyama(gt_pos, est_pos)  # seulement les POSITIONS
    return s, R, t
```

**Umeyama ne regarde que les positions XYZ**, pas les quaternions.
La rotation `R` qu'il trouve est celle qui minimise l'erreur de position sur toute la trajectoire.
Les quaternions `q_es` et `q_gt` passés en argument ne sont pas utilisés dans ce chemin.

La rotation trouvée est ensuite appliquée aux quaternions estimés dans `trajectory.py:259-263` :

```python
for i in range(np.shape(self.p_es)[0]):
    self.p_es_aligned[i, :] = self.scale * self.rot.dot(self.p_es[i, :]) + self.trans
    q_es_R = self.rot.dot(tf.quaternion_matrix(self.q_es[i, :])[0:3, 0:3])
    q_es_T = np.identity(4)
    q_es_T[0:3, 0:3] = q_es_R
    self.q_es_aligned[i, :] = tf.quaternion_from_matrix(q_es_T)
```

Si la rotation `self.rot` est mauvaise (cf. section suivante), toutes les orientations
alignées héritent du même offset.

---

## Pourquoi Box Seq 00 est particulièrement touché

La trajectoire "box" a une **symétrie à 4 degrés** : si l'on fait tourner le chemin de
90°, 180° ou 270°, il ressemble géométriquement au chemin original.

Du coup, l'algorithme Umeyama peut converger vers une rotation qui aligne bien les
positions, mais qui est décalée (par exemple de 90°) par rapport à la vraie
transformation de référentiel entre l'estimation et le GT.

Résultat : toutes les orientations alignées ont un offset **constant** `R_offset`.

---

## Pourquoi l'erreur est constante (pas croissante)

Si DEVO estime correctement les mouvements relatifs (pas de dérive en rotation),
mais que l'alignement initial est décalé de `R_offset`, alors pour tout instant `i` :

```
R_we_aligned[i] = R_offset * R_we[i]

e_R[i] = R_we_aligned[i] * R_wg[i]^{-1}
       = R_offset * R_we[i] * R_wg[i]^{-1}
       ≈ R_offset   (si l'odométrie est bonne, R_we[i] ≈ R_wg[i])
```

L'erreur RPY est donc **identique à chaque instant** — c'est le signe que
**DEVO ne dérive pas en rotation** sur cette séquence ; c'est l'alignement qui
est cassé, pas l'odométrie.

---

## La solution

Utiliser l'alignement `se3` avec `n_aligned=1` (premier frame seulement).
Dans `align_utils.py:71`, `alignSE3Single` utilise directement les quaternions initiaux
pour calculer la rotation :

```python
def alignSE3Single(p_es, p_gt, q_es, q_gt):
    ...
    g_rot   = tfs.quaternion_matrix(q_gt_0)[0:3, 0:3]
    est_rot = tfs.quaternion_matrix(q_es_0)[0:3, 0:3]
    R = np.dot(g_rot, np.transpose(est_rot))   # utilise les vraies orientations
    t = p_gt_0 - np.dot(R, p_es_0)
    return R, t
```

Cela garantit que l'orientation au `t=0` est exactement alignée, éliminant l'offset constant.

Pour activer ce mode, placer un fichier `eval_cfg.yaml` dans le dossier de résultats :

```yaml
align_type: se3
align_num_frames: 1
```

---

## Résumé

| Cause | Détail |
|---|---|
| Alignement par défaut | `sim3` Umeyama — utilise uniquement les positions XYZ |
| Trajectoire Box | Symétrie à 90° → Umeyama peut converger vers la mauvaise rotation |
| Erreur constante | Indique que DEVO ne dérive pas ; c'est l'alignement qui est faux |
| Fix | `se3` + `n_aligned=1` → aligne les quaternions du premier frame directement |
