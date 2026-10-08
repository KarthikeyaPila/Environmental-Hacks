"""Prepare a local waste-image dataset for Rekognition Custom Labels.

Expected input layout is a TrashNet-style directory with one subdirectory per
source class. Images are copied into a deterministic train/test layout; source
images are never modified.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path


LABEL_MAP = {
    "plastic": "pet",
    "pet": "pet",
    "cardboard": "cardboard",
    "paper": "paper",
    "glass": "glass",
    "metal": "aluminium",
    "aluminium": "aluminium",
}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def prepare_dataset(source: Path, output: Path, test_ratio: float = 0.2) -> dict:
    if not source.is_dir():
        raise ValueError(f"source directory does not exist: {source}")
    if not 0 < test_ratio < 1:
        raise ValueError("test_ratio must be between 0 and 1")

    counts = {"training": {}, "testing": {}, "skipped": {}}
    for source_class in sorted(path for path in source.iterdir() if path.is_dir()):
        label = LABEL_MAP.get(source_class.name.lower())
        images = sorted(path for path in source_class.rglob("*") if path.suffix.lower() in IMAGE_EXTENSIONS)
        if not label:
            counts["skipped"][source_class.name] = len(images)
            continue
        for image in images:
            digest = hashlib.sha256(str(image.relative_to(source)).encode()).hexdigest()
            split = "testing" if int(digest[:8], 16) / 0xFFFFFFFF < test_ratio else "training"
            target_dir = output / split / label
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / f"{source_class.name}_{image.name}"
            shutil.copy2(image, target)
            counts[split][label] = counts[split].get(label, 0) + 1
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="local dataset directory with class subdirectories")
    parser.add_argument("--output", type=Path, default=Path("ml/data"), help="output directory")
    parser.add_argument("--test-ratio", type=float, default=0.2)
    args = parser.parse_args()
    counts = prepare_dataset(args.source, args.output, args.test_ratio)
    print("Dataset prepared:")
    for split in ("training", "testing"):
        print(f"  {split}: {counts[split]}")
    if counts["skipped"]:
        print(f"  skipped source classes: {counts['skipped']}")


if __name__ == "__main__":
    main()
