# Environmental Recovery Platform

A hackathon proof of concept that helps recyclable household material enter the
existing kabadiwala recovery network and continue toward recycling companies.

## Repository structure

```text
.
├── docs/                  # Product, technical, and evidence documentation
├── src/                   # UI-independent backend/domain logic
├── tests/                 # Automated domain and workflow tests
├── AGENTS.md              # Contributor and agent guidance
└── README.md
```

The future frontend should live in `frontend/` and consume a stable API
contract. Keep shared business rules in `src/`; do not duplicate pricing,
workflow transitions, inventory, or matching logic in the frontend.

## Current backend scope

The domain service models the flow:

`Household → collection request → kabadiwala collection → inventory → recycler booking`

It currently runs in memory so the workflow can be tested before connecting
Lambda, API Gateway, and DynamoDB.

## Development

Use Python 3.11+ and run the dependency-free test suite from the repository
root:

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile src/recovery_domain.py
```

Do not commit credentials, local environment files, generated caches, or
temporary uploaded images. AWS integration should use configuration supplied by
the deployment environment.

