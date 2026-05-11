from __future__ import annotations

from pathlib import Path

from workspace.recon.cyl_fast_reference_engine import build_ground_truth, load_sparse_echo, reconstruct_cylindrical_reference


def reconstruct_faithful(scene_path: Path, echo_path: Path, method: str) -> dict:
    return reconstruct_cylindrical_reference(scene_path=scene_path, echo_path=echo_path, method=method)


def proof_line(scene_path: Path, echo_path: Path) -> str:
    scene = __import__("workspace.common.io_utils", fromlist=["read_json"]).read_json(scene_path)
    point = scene["points"][0]
    echo_sparse = load_sparse_echo(echo_path)
    return (
        f"scene={scene['sample_id']} rho={point['rho_m']:.3f} z={point['z_m']:.3f} "
        f"active_cells={len(echo_sparse['azimuth_idx'])} gt_shape={build_ground_truth(scene)['volume'].shape}"
    )
