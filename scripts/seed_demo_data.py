"""Print the deterministic demo seed summary.

This is intentionally a small, dependency-free entry point.  It is the place
where DynamoDB insertion can be added later without changing demo data rules.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.api_server import build_state


def main() -> None:
    service, area_service = build_state(with_demo_requests=True)
    print(json.dumps({
        "profiles": len(service.profiles),
        "materials": len(service.materials),
        "collectionRequests": len(service.requests),
        "areas": [summary for summary in area_service.summaries(service.requests.values()) if summary["requestCount"]],
    }, indent=2))


if __name__ == "__main__":
    main()
