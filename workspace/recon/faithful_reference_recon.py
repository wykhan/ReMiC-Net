from __future__ import annotations

from pathlib import Path

from workspace.common.io_utils import read_json, write_json
from workspace.recon.faithful_cylindrical_fast_recon import reconstruct_faithful


def reconstruct_from_paths(scene_path: Path, echo_path: Path, method: str, output_dir: Path | None = None) -> dict:
    result = reconstruct_faithful(scene_path=scene_path, echo_path=echo_path, method=method)
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        import numpy as np

        np.savez_compressed(
            output_dir / f"{result['sample_id']}_{method}_faithful.npz",
            volume=result["volume"],
            gt_volume=result["gt_volume"],
            x_values=result["x_values"],
            y_values=result["y_values"],
            z_values=result["z_values"],
        )
        write_json(
            output_dir / f"{result['sample_id']}_{method}_faithful_meta.json",
            {
                "sample_id": result["sample_id"],
                "method": result["method"],
                "wall_time_sec": result["wall_time_sec"],
                "fft_shape": result["fft_shape"],
                "quality": result["quality"],
            },
        )
    return result
