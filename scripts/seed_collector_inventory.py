"""Safely add deterministic demo collector profiles and collected marketplace stock."""

import argparse
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.api_server import build_state
from src.dynamodb_repository import DynamoRecoveryRepository, _native


def records_to_seed():
    service, _ = build_state(with_demo_requests=True)
    stock_households = {
        profile.id for profile in service.profiles.values()
        if profile.id.startswith("demo_stock_household_")
    }
    materials = [item for item in service.materials.values() if item.source_id in stock_households]
    requests = [item for item in service.requests.values() if item.household_id in stock_households]
    for material in materials:
        collector, slot = material.source_id.removeprefix("demo_stock_household_").split("_")
        material.id = f"demo_stock_material_{collector}_{slot}"
    material_ids = {item.source_id: item.id for item in materials}
    for request in requests:
        collector, slot = request.household_id.removeprefix("demo_stock_household_").split("_")
        request.id = f"demo_stock_request_{collector}_{slot}"
        request.material_ids = [material_ids[request.household_id]]

    profiles = [
        service.profiles[f"kabadiwala_{index}"]
        for index in (5, 6)
    ] + [service.profiles[profile_id] for profile_id in sorted(stock_households)]

    items = []
    for profile in profiles:
        item = _native(asdict(profile))
        item.update(pk=f"PROFILE#{profile.id}", sk="PROFILE", gsi1pk=f"ROLE#{profile.role.value}", gsi1sk=profile.id)
        items.append(item)
    for material in materials:
        item = _native(asdict(material))
        item.update(
            pk=f"MATERIAL#{material.id}", sk="MATERIAL",
            gsi1pk=f"OWNER#{material.current_holder_id}", gsi1sk=f"{material.status}#{material.id}",
            gsi2pk=f"MATERIAL#{material.material_type}#{material.status}", gsi2sk=material.id,
        )
        items.append(item)
    for request in requests:
        item = _native(asdict(request))
        item.update(
            pk=f"REQUEST#{request.id}", sk="REQUEST",
            gsi1pk=f"HOUSEHOLD#{request.household_id}", gsi1sk=f"{request.created_at}#{request.id}",
            gsi2pk=f"REQUEST_STATUS#{request.status.value}", gsi2sk=f"{request.created_at}#{request.id}",
        )
        items.append(item)
    return items, len(profiles), len(materials), sum(item.quantity_kg for item in materials)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="add missing records to DynamoDB")
    parser.add_argument("--table", default=os.getenv("DYNAMODB_TABLE", "environmental-recovery"))
    parser.add_argument("--region", default=os.getenv("AWS_REGION", "ap-south-1"))
    args = parser.parse_args()
    items, profile_count, material_count, inventory_kg = records_to_seed()
    result = {
        "profiles": profile_count,
        "collectedMaterialRecords": material_count,
        "collectedInventoryKg": round(inventory_kg, 2),
        "mode": "write" if args.write else "dry-run",
    }
    if args.write:
        repository = DynamoRecoveryRepository(table_name=args.table, region_name=args.region)
        table = repository.table
        written = 0
        skipped = 0
        with table.batch_writer() as batch:
            for item in items:
                existing = table.get_item(Key={"pk": item["pk"], "sk": item["sk"]}, ConsistentRead=True).get("Item")
                if existing:
                    if item["sk"] == "PROFILE" and (
                        existing.get("role") != item["role"] or existing.get("is_demo") is not True
                    ):
                        raise RuntimeError(f"Refusing to overwrite non-demo profile {item['pk']}")
                    if item["sk"] == "REQUEST" and (
                        existing.get("household_id") != item["household_id"] or existing.get("is_demo") is not True
                    ):
                        raise RuntimeError(f"Refusing to overwrite non-demo request {item['pk']}")
                    if item["sk"] == "MATERIAL" and any(
                        existing.get(field) != item[field]
                        for field in ("source_id", "current_holder_id", "material_type", "status")
                    ):
                        raise RuntimeError(f"Refusing to overwrite non-demo record {item['pk']}")
                    skipped += 1
                    continue
                batch.put_item(Item=item)
                written += 1
        result.update(table=args.table, written=written, skippedExistingDemo=skipped)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
