from __future__ import annotations

from pathlib import Path

from workspace.recon.reference_recon import reconstruct_from_scene_path


def run_bp(scene_path: Path, output_dir: Path | None = None) -> dict:
    return reconstruct_from_scene_path(scene_path=scene_path, method="BP", output_dir=output_dir)
