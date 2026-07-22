#!/bin/bash
# Guide de téléchargement et preprocessing de tous les datasets DEVO.
# Pour chaque dataset : télécharger → décompresser → lancer pp_DATASET.py → lancer eval.
#
# Usage : bash scripts/download_datasets_guide.sh [dataset]
# Ex   : bash scripts/download_datasets_guide.sh hku
#
# Ce script est DOCUMENTATIF : remplissez les URLs depuis les sites officiels,
# ou utilisez les commandes section par section.
#
# Datasets + sites officiels :
#   RPG    : https://rpg.ifi.uzh.ch/ECCV18_stereo_davis.html
#   FPV    : https://fpv.ifi.uzh.ch/  (inscription requise)
#   HKU    : https://github.com/arclab-hku/Event_based_VO-VIO-SLAM
#   EDS    : https://rpg.ifi.uzh.ch/eds.html
#   MVSEC  : https://daniilidis-group.github.io/mvsec/
#   VECtor : https://star-datasets.github.io/vector/
#   TUM-VIE: https://cvg.cit.tum.de/data/datasets/visual-inertial-event-dataset

set -e
DATASET_BASE=${DATASET_BASE:-/home/i/i0002573/arthur_ipal/datasets}
REPO_DEVO=${REPO_DEVO:-/home/i/i0002573/arthur_ipal/DEVO}
DEVO_WEIGHTS=${DEVO_WEIGHTS:-/home/i/i0002573/test_perso/DEVO/DEVO.pth}
MS_MODEL=${MS_MODEL:-/home/i/i0002573/arthur_ipal/MS_Model}

download_rpg() {
    echo "=== RPG ==="
    # Séquences mono (Davis240C + DVS346) depuis https://rpg.ifi.uzh.ch/ECCV18_stereo_davis.html
    # Téléchargez les .bag manuellement et posez-les dans $DATASET_BASE/rpg/
    # Puis preprocessing :
    conda activate devofou && cd "$REPO_DEVO"
    python scripts/pp_rpg.py --bagdir "$DATASET_BASE/rpg" --outdir "$DATASET_BASE/rpg/rpg_dataset"
}

download_fpv() {
    echo "=== FPV (inscription requise) ==="
    # Site : https://fpv.ifi.uzh.ch/  → créer un compte → télécharger les séquences
    # indoor_forward_*, indoor_45_* → poser dans $DATASET_BASE/fpv/
    conda activate devofou && cd "$REPO_DEVO"
    python scripts/pp_fpv.py --indir "$DATASET_BASE/fpv" --outdir "$DATASET_BASE/fpv_preprocessed"
}

download_hku() {
    echo "=== HKU ==="
    # Google Drive : https://github.com/arclab-hku/Event_based_VO-VIO-SLAM
    # Télécharger les séquences HKU_aggressive_*, HKU_HDR_*, hku_* → $DATASET_BASE/hku/
    conda activate devofou && cd "$REPO_DEVO"
    python scripts/pp_hku.py --indir "$DATASET_BASE/hku" --outdir "$DATASET_BASE/hku_preprocessed"
}

download_eds() {
    echo "=== EDS ==="
    # Site : https://rpg.ifi.uzh.ch/eds.html → télécharger les séquences
    # Séquences : 00_peanuts_dark, 01_peanuts_light, ... → $DATASET_BASE/eds/
    conda activate devofou && cd "$REPO_DEVO"
    python scripts/pp_eds.py --indir "$DATASET_BASE/eds" --outdir "$DATASET_BASE/eds_preprocessed"
}

download_mvsec() {
    echo "=== MVSEC ==="
    # Site : https://daniilidis-group.github.io/mvsec/
    # Séquences indoor_flying1-4 (HDF5 direct download disponible)
    mkdir -p "$DATASET_BASE/mvsec"
    # Exemple de téléchargement (URLs à vérifier sur le site officiel) :
    # for seq in indoor_flying1 indoor_flying2 indoor_flying3 indoor_flying4; do
    #     wget -P "$DATASET_BASE/mvsec" "https://daniilidis-group.github.io/mvsec/data/${seq}_data.hdf5"
    # done
    conda activate devofou && cd "$REPO_DEVO"
    python scripts/pp_mvsec.py --indir "$DATASET_BASE/mvsec" --outdir "$DATASET_BASE/mvsec_preprocessed"
}

download_vector() {
    echo "=== VECtor (inscription possible requise) ==="
    # Site : https://star-datasets.github.io/vector/
    # Séquences corner_slow, robot_normal, ... → $DATASET_BASE/vector/
    conda activate devofou && cd "$REPO_DEVO"
    python scripts/pp_vector.py --indir "$DATASET_BASE/vector" --outdir "$DATASET_BASE/vector_preprocessed"
}

download_tumvie() {
    echo "=== TUM-VIE ==="
    # Site : https://cvg.cit.tum.de/data/datasets/visual-inertial-event-dataset
    # Séquences mocap-shake, mocap-shake2, ... (fichiers H5 volumineux)
    mkdir -p "$DATASET_BASE/tumvie"
    conda activate devofou && cd "$REPO_DEVO"
    python scripts/pp_tumvie.py --indir "$DATASET_BASE/tumvie" --outdir "$DATASET_BASE/tumvie_preprocessed"
}

# Lancer le preprocessing d'un dataset spécifique
case "${1:-all}" in
    rpg)    download_rpg ;;
    fpv)    download_fpv ;;
    hku)    download_hku ;;
    eds)    download_eds ;;
    mvsec)  download_mvsec ;;
    vector) download_vector ;;
    tumvie) download_tumvie ;;
    all)
        echo "Lancer chaque section manuellement selon vos besoins."
        echo "Datasets disponibles : rpg fpv hku eds mvsec vector tumvie"
        ;;
    *)
        echo "Usage: $0 [rpg|fpv|hku|eds|mvsec|vector|tumvie|all]"
        exit 1
        ;;
esac
