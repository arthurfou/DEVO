import os
import shutil
import torch
from devo.config import cfg

from utils.load_utils import load_gt_us, evimo_evs_iterator
from utils.eval_utils import assert_eval_config, run_voxel
from utils.eval_utils import log_results, write_raw_results, compute_median_results
from utils.viz_utils import viz_flow_inference

# EVIMO2 samsung_mono resolution — confirm with §3 NPZ inspection (may differ from 480×640)
H, W = 480, 640


@torch.no_grad()
def evaluate(config, args, net, train_step=None, datapath="", split_file=None,
             stride=1, trials=1, plot=False, save=False, return_figure=False, viz=False, timing=False, viz_flow=False, map_path=None,
             dyn_mask_provider_factory=None):
    dataset_name = "evimo2_evs"

    if config is None:
        config = cfg
        config.merge_from_file("config/eval_evimo.yaml")

    scenes = open(split_file).read().split()
    scenes = [s for s in scenes if '#' not in s]

    results_dict_scene, figures = {}, {}
    all_results = []
    for scene in scenes:
        gt_path = os.path.join(datapath, scene, "gt_stamped.txt")
        if not os.path.exists(gt_path):
            print(f"Scene {scene} has no GT, skipping (run preprocess_evimo2.py first)")
            continue

        print(f"Eval on {scene}")
        results_dict_scene[scene] = []

        for trial in range(trials):
            datapath_val = os.path.join(datapath, scene)

            dyn_mask_provider = None if dyn_mask_provider_factory is None \
                else dyn_mask_provider_factory(scene, datapath_val)

            tmp_map_path = None
            if map_path is not None:
                tmp_map_path = os.path.join(os.path.dirname(map_path), f"_tmp_{scene.replace('/', '_')}_{trial}.ply")

            traj_est, tstamps, flowdata = run_voxel(
                datapath_val, config, net, viz=viz,
                iterator=evimo_evs_iterator(datapath_val, stride=stride, timing=timing, H=H, W=W),
                timing=timing, H=H, W=W, viz_flow=viz_flow, map_path=tmp_map_path,
                dyn_mask_provider=dyn_mask_provider)

            tss_traj_us, traj_hf = load_gt_us(gt_path)

            data = (traj_hf, tss_traj_us, traj_est, tstamps)
            hyperparam = (train_step, net, dataset_name, scene, trial, cfg, args)
            all_results, results_dict_scene, figures, outfolder = log_results(
                data, hyperparam, all_results, results_dict_scene, figures,
                plot=plot, save=save, return_figure=return_figure, stride=stride,
                expname=args.expname)

            if tmp_map_path is not None and os.path.exists(tmp_map_path):
                shutil.move(tmp_map_path, os.path.join(outfolder, "map.ply"))

            if viz_flow:
                viz_flow_inference(outfolder, flowdata)

        print(scene, sorted(results_dict_scene[scene]))

    write_raw_results(all_results, outfolder)
    results_dict = compute_median_results(results_dict_scene, all_results, dataset_name, outfolder)

    if return_figure:
        return results_dict, figures
    return results_dict, None


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default="config/eval_evimo.yaml")
    parser.add_argument('--datapath', default='', help='path to EVIMO2 eval_preprocessed/ directory')
    parser.add_argument('--weights', default="DEVO.pth")
    parser.add_argument('--val_split', type=str, default="splits/evimo2/evimo2_val.txt")
    parser.add_argument('--trials', type=int, default=1)
    parser.add_argument('--plot', action="store_true")
    parser.add_argument('--save_trajectory', action="store_true")
    parser.add_argument('--return_figs', action="store_true")
    parser.add_argument('--viz', action="store_true")
    parser.add_argument('--timing', action="store_true")
    parser.add_argument('--stride', type=int, default=1)
    parser.add_argument('--viz_flow', action="store_true")
    parser.add_argument('--expname', type=str, default="")
    parser.add_argument('--map_path', type=str, default=None)

    args = parser.parse_args()
    assert_eval_config(args)

    cfg.merge_from_file(args.config)
    print("Running eval_evimo2_evs.py with config...")
    print(cfg)

    torch.manual_seed(1234)

    args.plot = True
    args.save_trajectory = True
    val_results, val_figures = evaluate(
        cfg, args, args.weights, datapath=args.datapath, split_file=args.val_split,
        trials=args.trials, plot=args.plot, save=args.save_trajectory,
        return_figure=args.return_figs, viz=args.viz, timing=args.timing,
        stride=args.stride, viz_flow=args.viz_flow, map_path=args.map_path)

    print("val_results=")
    for k in val_results:
        print(k, val_results[k])
