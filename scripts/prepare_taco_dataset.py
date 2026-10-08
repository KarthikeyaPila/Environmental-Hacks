"""Prepare relevant TACO COCO annotations for our controlled material labels."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


CATEGORY_MAP = {
    "Aluminium foil": "aluminium",
    "Aluminium blister pack": "aluminium",
    "Food Can": "aluminium",
    "Drink can": "aluminium",
    "Aerosol": "aluminium",
    "Metal bottle cap": "aluminium",
    "Metal lid": "aluminium",
    "Scrap metal": "aluminium",
    "Other plastic bottle": "pet",
    "Clear plastic bottle": "pet",
    "Glass bottle": "glass",
    "Broken glass": "glass",
    "Glass cup": "glass",
    "Glass jar": "glass",
    "Other carton": "cardboard",
    "Egg carton": "cardboard",
    "Drink carton": "cardboard",
    "Corrugated carton": "cardboard",
    "Meal carton": "cardboard",
    "Pizza box": "cardboard",
    "Magazine paper": "paper",
    "Tissues": "paper",
    "Wrapping paper": "paper",
    "Normal paper": "paper",
    "Paper bag": "paper",
    "Paper cup": "paper",
}
LABEL_IDS = {label: index + 1 for index, label in enumerate(("pet", "cardboard", "paper", "aluminium", "glass"))}


def prepare_taco(annotation_file: Path, image_root: Path, output: Path, test_ratio: float = 0.2) -> dict:
    if not annotation_file.is_file():
        raise ValueError(f"TACO annotation file not found: {annotation_file}\nDownload/clone TACO first, then pass the real path to data/annotations.json.")
    if not image_root.is_dir():
        raise ValueError(f"TACO image directory not found: {image_root}\nPass the real TACO data directory containing batch_* folders.")
    data = json.loads(annotation_file.read_text())
    categories = {category["id"]: category["name"] for category in data["categories"]}
    mapped_categories = {category_id: CATEGORY_MAP[name] for category_id, name in categories.items() if name in CATEGORY_MAP}
    annotations_by_image: dict[int, list] = {}
    for annotation in data["annotations"]:
        if annotation["category_id"] in mapped_categories:
            annotations_by_image.setdefault(annotation["image_id"], []).append(annotation)

    result = {"training": {}, "testing": {}, "skipped": {}, "images": 0, "annotations": 0}
    mapped_images = {image["id"]: image for image in data["images"] if image["id"] in annotations_by_image}
    output_annotations = {"images": [], "annotations": [], "categories": [{"id": id_, "name": name} for name, id_ in LABEL_IDS.items()]}
    new_image_id = 1
    new_annotation_id = 1
    for image_id, image in mapped_images.items():
        source = image_root / image["file_name"]
        if not source.exists():
            result["skipped"][image["file_name"]] = "image not downloaded"
            continue
        digest = hashlib.sha256(image["file_name"].encode()).hexdigest()
        split = "testing" if int(digest[:8], 16) / 0xFFFFFFFF < test_ratio else "training"
        target = output / split / Path(image["file_name"]).name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        new_image = {"id": new_image_id, "file_name": target.name, "width": image.get("width"), "height": image.get("height")}
        output_annotations["images"].append(new_image)
        result[split]["images"] = result[split].get("images", 0) + 1
        for annotation in annotations_by_image[image_id]:
            label = mapped_categories[annotation["category_id"]]
            output_annotations["annotations"].append({"id": new_annotation_id, "image_id": new_image_id, "category_id": LABEL_IDS[label], "bbox": annotation["bbox"], "area": annotation.get("area"), "iscrowd": annotation.get("iscrowd", 0)})
            result["annotations"] += 1
            new_annotation_id += 1
        new_image_id += 1
    (output / "annotations_mapped.json").write_text(json.dumps(output_annotations, indent=2))
    result["images"] = len(output_annotations["images"])
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("annotations", type=Path)
    parser.add_argument("image_root", type=Path)
    parser.add_argument("--output", type=Path, default=Path("/tmp/taco-prepared"))
    args = parser.parse_args()
    print(json.dumps(prepare_taco(args.annotations, args.image_root, args.output), indent=2))


if __name__ == "__main__":
    main()
