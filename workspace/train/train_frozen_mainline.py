from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from workspace.common.io_utils import read_json, write_json, write_text
from workspace.train.train_two_stage_et import (
    _append_failure_csv,
    _append_family_metrics_csv,
    _write_representative_manifest,
    render_loss_curve,
    train_mode,
)


def train_frozen_mainline(output_root: Path, epochs: int, batch_size: int, lr: float, smoke_limit: int) -> dict:
    metrics = train_mode(output_root=output_root, mode="M2", epochs=epochs, batch_size=batch_size, lr=lr, smoke_limit=smoke_limit)
    _append_family_metrics_csv(output_root, "M2", metrics)
    _append_failure_csv(output_root, "M2", metrics)
    _write_representative_manifest(output_root, "M2")
    metrics["mode"] = "frozen_mainline"
    metrics["frozen_mainline_definition"] = {
        "frontend": "Variant B",
        "physics_backbone": "ref3",
        "second_stage": "3D U-Net",
        "training_data": "shape_family_full only",
    }
    src_ckpt_dir = output_root / "checkpoints" / "M2"
    dst_ckpt_dir = output_root / "checkpoints" / "frozen_mainline"
    if dst_ckpt_dir.exists():
        shutil.rmtree(dst_ckpt_dir)
    shutil.copytree(src_ckpt_dir, dst_ckpt_dir)
    metrics["best_checkpoint"] = str((dst_ckpt_dir / "best.pt").relative_to(output_root))
    write_json(output_root / "metrics_frozen_mainline.json", metrics)
    config = read_json(output_root / "metrics_M2.json")["config"]
    lines = [
        "mode: frozen_mainline",
        "frontend: Variant B",
        "physics_backbone: ref3",
        "second_stage: 3D U-Net",
        "training_data: shape_family_full_only",
    ]
    for key, value in config.items():
        lines.append(f"{key}: {value}")
    write_text(output_root / "training_config_frozen_mainline.yaml", "\n".join(lines) + "\n")
    render_loss_curve(output_root, "frozen_mainline", metrics)
    if (output_root / "predictions" / "frozen_mainline").exists():
        shutil.rmtree(output_root / "predictions" / "frozen_mainline")
    shutil.copytree(output_root / "predictions" / "M2", output_root / "predictions" / "frozen_mainline")
    shutil.copyfile(output_root / "predictions" / "M2_representatives.json", output_root / "predictions" / "frozen_mainline_representatives.json")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Train task_real_006b frozen mainline.")
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--smoke-limit", type=int, default=16)
    args = parser.parse_args()
    metrics = train_frozen_mainline(Path(args.output_root), args.epochs, args.batch_size, args.lr, args.smoke_limit)
    print(
        f"Finished frozen_mainline learned_nmse={metrics['overall']['learned_nmse_mean']:.6f} "
        f"gain={metrics['overall']['nmse_gain_vs_ref3']:.6f}"
    )


if __name__ == "__main__":
    main()
