"""Factories pour créer un LearnedDynMaskProvider sur n'importe quel dataset DEVO.

Pour les datasets sans objets dynamiques GT (tous sauf EVIMO), on applique le modèle MS
en inférence pure (mode M1/M2/M3). Le modèle donnerait idéalement des scores proches de 0
sur des scènes statiques, laissant DEVO se comporter comme vanilla.

Usage :
    from utils.ms_dataset_factory import make_ms_factory

    factory = make_ms_factory("rpg", ms_weights="path/to/best.pt",
                              ms_config="path/to/config.yaml", side="left")
    # factory(scene, datapath_val) -> LearnedDynMaskProvider
"""

from __future__ import annotations

import glob
import os
from pathlib import Path
from typing import Optional

import numpy as np


# ---------------------------------------------------------------------------
# Helpers internes
# ---------------------------------------------------------------------------

def _frame_ts_s(tss_txt_path: str) -> np.ndarray:
    """Charge tss_imgs_us (µs) et les convertit en secondes."""
    return np.sort(np.loadtxt(tss_txt_path).astype(np.float64)) / 1e6


def _make_provider(ea, frame_ts_s, ms_weights, ms_config, threshold, device):
    from ms_model.oracle import LearnedDynMaskProvider
    return LearnedDynMaskProvider.from_event_array(
        ea, frame_ts_s, ms_weights, ms_config,
        device=device, threshold=threshold, ts_offset_s=0.0,
    )


# ---------------------------------------------------------------------------
# Loaders par dataset
# ---------------------------------------------------------------------------

def _load_rpg(scenedir: str, side: str = "left") -> tuple:
    from ms_model.io.loaders import load_events_rpg
    # Résolution variable : 180×240 (Davis240C) ou 260×346 (DVS346)
    evs_path = os.path.join(scenedir, f"evs_{side}.txt")
    tss_path = os.path.join(scenedir, f"tss_imgs_us_{side}.txt")
    H, W = (260, 346) if "simulation_3planes" in scenedir else (180, 240)
    ea = load_events_rpg(evs_path, H=H, W=W)
    return ea, _frame_ts_s(tss_path)


def _load_fpv(scenedir: str) -> tuple:
    from ms_model.io.loaders import load_events_fpv
    tss_path = os.path.join(scenedir, "images_timestamps_us.txt")
    ea = load_events_fpv(scenedir, H=260, W=346)
    return ea, _frame_ts_s(tss_path)


def _load_hku(scenedir: str, side: str = "left") -> tuple:
    from ms_model.io.loaders import load_events_prophesee_h5
    h5_path = os.path.join(scenedir, f"evs_{side}.h5")
    tss_path = os.path.join(scenedir, f"tss_imgs_us_{side}.txt")
    ea = load_events_prophesee_h5(h5_path, H=260, W=346)
    return ea, _frame_ts_s(tss_path)


def _load_eds(scenedir: str) -> tuple:
    from ms_model.io.loaders import load_events_prophesee_h5
    h5_path = glob.glob(os.path.join(scenedir, "events.h5"))[0]
    tss_path = os.path.join(scenedir, "images_timestamps_us.txt")
    ea = load_events_prophesee_h5(h5_path, H=480, W=640)
    return ea, _frame_ts_s(tss_path)


def _load_mvsec(scenedir: str, side: str = "left") -> tuple:
    from ms_model.io.loaders import load_events_mvsec
    h5_files = glob.glob(os.path.join(scenedir, "*_data.hdf5"))
    assert len(h5_files) == 1, f"Expected 1 MVSEC hdf5 in {scenedir}, found {h5_files}"
    tss_path = os.path.join(scenedir, f"tss_imgs_us_{side}.txt")
    ea = load_events_mvsec(h5_files[0], side=side, H=260, W=346)
    return ea, _frame_ts_s(tss_path)


def _load_vector(scenedir: str, side: str = "left") -> tuple:
    from ms_model.io.loaders import load_events_prophesee_h5
    seq = os.path.basename(scenedir)
    h5_path = os.path.join(scenedir, f"{seq}1.synced.{side}_event.hdf5")
    tss_path = os.path.join(scenedir, f"tss_imgs_us_{side}.txt")
    ea = load_events_prophesee_h5(h5_path, H=480, W=640)
    return ea, _frame_ts_s(tss_path)


def _load_tumvie(scenedir: str, camID: int = 2) -> tuple:
    from ms_model.io.loaders import load_events_prophesee_h5
    side = "left" if camID == 2 else "right"
    h5_files = glob.glob(os.path.join(scenedir, f"*events_{side}.h5"))
    assert len(h5_files) == 1, f"Expected 1 TUM-VIE h5 in {scenedir}, found {h5_files}"
    tss_path = os.path.join(scenedir, f"{side}_images_undistorted", f"image_timestamps_{side}.txt")
    ea = load_events_prophesee_h5(h5_files[0], H=720, W=1280)
    return ea, _frame_ts_s(tss_path)


# ---------------------------------------------------------------------------
# API publique
# ---------------------------------------------------------------------------

_LOADERS = {
    "rpg": lambda sd, side, camID: _load_rpg(sd, side),
    "fpv": lambda sd, side, camID: _load_fpv(sd),
    "hku": lambda sd, side, camID: _load_hku(sd, side),
    "eds": lambda sd, side, camID: _load_eds(sd),
    "mvsec": lambda sd, side, camID: _load_mvsec(sd, side),
    "vector": lambda sd, side, camID: _load_vector(sd, side),
    "tumvie": lambda sd, side, camID: _load_tumvie(sd, camID),
}


def make_ms_factory(
    dataset: str,
    ms_weights: str,
    ms_config: str,
    side: str = "left",
    camID: int = 2,
    threshold: Optional[float] = None,
    device: str = "cuda",
):
    """Retourne une factory `(scene, datapath_val) -> LearnedDynMaskProvider`.

    Args:
        dataset: 'rpg' | 'fpv' | 'hku' | 'eds' | 'mvsec' | 'vector' | 'tumvie'
        ms_weights: chemin vers le checkpoint MS (best.pt ou ms_final.pt).
        ms_config: chemin vers le yaml de config MS.
        side: 'left' | 'right' (pour datasets stéréo).
        camID: 2 | 3 (TUM-VIE seulement).
        threshold: None => score continu ; float => masque binaire.
        device: 'cuda' | 'cpu'.
    """
    assert dataset in _LOADERS, f"Dataset inconnu : '{dataset}'. Choix : {list(_LOADERS)}"
    loader = _LOADERS[dataset]

    def factory(scene: str, datapath_val: str):
        print(f"[MS-factory/{dataset}] Chargement events pour '{scene}'…")
        try:
            ea, frame_ts_s = loader(datapath_val, side, camID)
        except Exception as e:
            print(f"[MS-factory/{dataset}] ERREUR chargement events : {e} → provider None")
            return None
        if len(ea) == 0:
            print(f"[MS-factory/{dataset}] Pas d'events dans '{scene}' → provider None")
            return None
        return _make_provider(ea, frame_ts_s, ms_weights, ms_config, threshold, device)

    return factory


def _mean_ate(results_dict: dict) -> float:
    vals = [float(v) for v in results_dict.values() if v is not None]
    return sum(vals) / len(vals) if vals else float("nan")
