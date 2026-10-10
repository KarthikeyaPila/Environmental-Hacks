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

The primary frontend is `frontend/phirFinal.html` and consumes the stable API
contract through the adjacent bridge scripts. Keep shared business rules in `src/`; do not duplicate pricing,
workflow transitions, inventory, or matching logic in the frontend.

The authoritative project documentation lives in `docs/` and `CHAT_HANDOFF.md`.
The files under `frontend/backend-context/` are preserved reference snapshots;
update the authoritative documents first when contracts or architecture change.

## Current backend scope

The domain service models the flow:

`Household → collection request → kabadiwala collection → inventory → recycler booking`

It supports dependency-free in-memory mode for local tests and an opt-in AWS
mode using DynamoDB persistence, private S3 image uploads, and Rekognition
Custom Labels.

The current hosted demo is available at:
`https://main.d3hgpobebqphe1.amplifyapp.com/`

## Development

Use Python 3.11+ and run the dependency-free test suite from the repository
root:

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile src/recovery_domain.py
```

For AWS-backed local development:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
```

Run the temporary demo website:

```bash
./scripts/run_demo.sh
```

Then open `http://localhost:8080`. Set a different port with
`PORT=3000 ./scripts/run_demo.sh`.

For a separate static frontend host, set `window.PHIR_API_BASE` before the
bridge scripts load, for example to the deployed API Gateway base URL. Local
development uses the same-origin default.

Do not commit credentials, local environment files, generated caches, or
temporary uploaded images. AWS integration should use configuration supplied by
the deployment environment.
