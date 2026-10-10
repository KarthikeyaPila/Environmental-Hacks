"""Print or write the deterministic Phir demo network seed."""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.api_server import build_state


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write the seed to DynamoDB")
    parser.add_argument("--replace", action="store_true", help="clear the target demo table before writing")
    parser.add_argument("--table", default=os.getenv("DYNAMODB_TABLE", "environmental-recovery"))
    parser.add_argument("--region", default=os.getenv("AWS_REGION", "ap-south-1"))
    args = parser.parse_args()
    if args.replace and not args.write:
        parser.error("--replace requires --write")
    service, area_service = build_state(with_demo_requests=True)
    summary = {
        "profiles": len(service.profiles),
        "households": sum(profile.role.value == "household" for profile in service.profiles.values()),
        "kabadiwalas": sum(profile.role.value == "kabadiwala" for profile in service.profiles.values()),
        "recyclers": sum(profile.role.value == "recycler" for profile in service.profiles.values()),
        "materials": len(service.materials),
        "collectionRequests": len(service.requests),
        "requestStatuses": {status.value: sum(request.status == status for request in service.requests.values()) for status in type(next(iter(service.requests.values())).status)},
        "requirements": len(service.requirements),
        "areas": [summary for summary in area_service.summaries(service.requests.values()) if summary["requestCount"]],
    }
    if args.write:
        from src.dynamodb_repository import DynamoRecoveryRepository
        repository = DynamoRecoveryRepository(table_name=args.table, region_name=args.region)
        if args.replace:
            repository.clear()
        repository.save_service(service)
        summary["written"] = True
        summary["table"] = args.table
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
