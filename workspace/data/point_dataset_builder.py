from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from workspace.common.io_utils import ensure_dir, write_json
from workspace.data.point_scene_generator import SampleConfig, generate_point_scene


DEFAULT_SMOKE_SPLITS = {"train": 64, "val": 16, "test": 16}
DEFAULT_FORMAL_SPLITS = {"train": 6000, "val": 1000, "test": 1000}


def build_dataset(output_root: Path, smoke: bool, base_seed: int) -> dict:
    dataset_dir = ensure_dir(output_root / "dataset")
    scenes_dir = ensure_dir(dataset_dir / "scenes")
    split_sizes = DEFAULT_SMOKE_SPLITS if smoke else DEFAULT_FORMAL_SPLITS

    index: list[dict] = []
    point_hist = Counter()

    for split, count in split_sizes.items():
        split_dir = ensure_dir(scenes_dir / split)
        for offset in range(count):
            seed = base_seed + len(index)
            sample_id = f"{split}_{offset:04d}"
            sample = generate_point_scene(
                SampleConfig(sample_id=sample_id, split=split, seed=seed, smoke=smoke)
            )
            write_json(split_dir / f"{sample_id}.json", sample)
            index.append(
                {
                    "sample_id": sample_id,
                    "split": split,
                    "seed": seed,
                    "scene_path": str((split_dir / f"{sample_id}.json").relative_to(output_root)),
                    "point_count": sample["point_count"],
                }
            )
            point_hist[sample["point_count"]] += 1

    summary = {
        "mode": "smoke" if smoke else "formal",
        "split_sizes": split_sizes,
        "total_samples": len(index),
        "point_count_histogram": {str(key): point_hist[key] for key in sorted(point_hist)},
        "index_path": "dataset/index.json",
    }
    write_json(dataset_dir / "index.json", index)
    write_json(output_root / "dataset_summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build protocol-v1 point-target dataset metadata.")
    parser.add_argument("--output-root", required=True, help="Task artifact root.")
    parser.add_argument("--mode", choices=["smoke", "formal"], default="smoke")
    parser.add_argument("--base-seed", type=int, default=20260415)
    args = parser.parse_args()

    summary = build_dataset(Path(args.output_root), smoke=args.mode == "smoke", base_seed=args.base_seed)
    print(f"Built dataset mode={summary['mode']} total_samples={summary['total_samples']}")


if __name__ == "__main__":
    main()
