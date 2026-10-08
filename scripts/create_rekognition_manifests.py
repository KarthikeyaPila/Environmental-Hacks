#!/usr/bin/env python3
"""Create Amazon Rekognition Custom Labels image-classification manifests."""

import argparse
import json
from pathlib import Path


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}


def create_manifest(prepared_root: Path, split: str, bucket: str, prefix: str, output: Path) -> int:
    split_root = prepared_root / split
    if not split_root.is_dir():
        raise FileNotFoundError(f"Prepared split not found: {split_root}")

    records = []
    for label_dir in sorted(path for path in split_root.iterdir() if path.is_dir()):
        label = label_dir.name
        for image in sorted(path for path in label_dir.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES):
            key = "/".join(part.strip("/") for part in (prefix, split, label, image.name) if part.strip("/"))
            records.append(
                {
                    "source-ref": f"s3://{bucket}/{key}",
                    "waste-type": label,
                    "waste-type-metadata": {
                        "confidence": 1.0,
                        "job-name": "environmental-recovery-manifest",
                        "class-name": label,
                        "human-annotated": "yes",
                        "creation-date": "2026-01-01T00:00:00.000Z",
                        "type": "groundtruth/image-classification",
                    },
                }
            )

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, separators=(",", ":")) + "\n")
    return len(records)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prepared_root", type=Path)
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--prefix", default="datasets/trashnet")
    parser.add_argument("--output", type=Path, default=Path("ml/manifests"))
    args = parser.parse_args()

    summary = {}
    for split in ("training", "testing"):
        output = args.output / f"{split}.manifest.jsonl"
        summary[split] = create_manifest(args.prepared_root, split, args.bucket, args.prefix, output)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
