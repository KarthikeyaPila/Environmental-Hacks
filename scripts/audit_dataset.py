"""Audit a prepared training/testing image directory."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.prepare_dataset import IMAGE_EXTENSIONS


EXPECTED_LABELS = {"pet", "cardboard", "paper", "aluminium", "glass"}


def audit_dataset(root: Path) -> dict:
    result = {"training": {}, "testing": {}, "overlap": [], "missingLabels": []}
    seen: dict[str, str] = {}
    for split in ("training", "testing"):
        split_dir = root / split
        for label_dir in sorted(path for path in split_dir.iterdir() if path.is_dir()) if split_dir.exists() else []:
            images = {path.name for path in label_dir.iterdir() if path.suffix.lower() in IMAGE_EXTENSIONS}
            result[split][label_dir.name] = len(images)
            for image_name in images:
                if image_name in seen and seen[image_name] != split:
                    result["overlap"].append(image_name)
                seen[image_name] = split
    result["missingLabels"] = sorted(EXPECTED_LABELS - set(result["training"]) - set(result["testing"]))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="prepared dataset root")
    args = parser.parse_args()
    report = audit_dataset(args.root)
    print(report)
    if report["missingLabels"] or report["overlap"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
