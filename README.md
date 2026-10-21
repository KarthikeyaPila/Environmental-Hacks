# Phir — Environmental Recovery POC

Phir is a hackathon proof of concept for helping recyclable household material
reach the existing kabadiwala and recycling network.

```text
Household → recovery request → kabadiwala → collected inventory → recycler
```

The project demonstrates a coordination flow. It is not a municipal waste
platform, a collection fleet, or a production marketplace. Demo identities,
records, and map locations are illustrative. Impact figures should be derived
from recorded prototype data; they are not real-world deployment results.

## Current status

The repository contains a local Python API and a separate, stylized frontend
with AWS API bridges. The local API can run without AWS in mock mode. The
hosted deployment was reported by hackathon judges to return HTTP 500 from its
data endpoints, even though its mock classify endpoint responded. Treat the
deployed data flow as broken/unverified until the deployed artifact and API are
smoke-tested together. The currently deployed bundle was also reported to
differ from repository source.

Known implementation limitations include DynamoDB persistence that currently
reads and rewrites a table snapshot during mutations rather than applying
targeted item-level updates, no production authentication, mock local image
classification, and incomplete end-to-end verification of the stylized UI
against the local API. See [development status](docs/development_status.md) and
[the handoff notes](CHAT_HANDOFF.md) for context.

## Run the local mock demo (no AWS)

Requirements: Python 3.11 or newer and Bash. The default script configuration
uses in-memory storage and does not start a Rekognition model.

```bash
./scripts/run_demo.sh
```

Open <http://localhost:8080>. Change the port with
`PORT=3000 ./scripts/run_demo.sh`. This serves the simple functional client
from `demo/`; it is not the large, folk-art frontend. Local in-memory state
resets when the server stops. Image classification is deterministic/mock and
does not call Rekognition. The script can load a local `.env`; start from
`.env.example` and never commit secrets.

The stylized frontend has a separate build path described in
[`frontend/README.md`](frontend/README.md). Its checked-in API configuration
points to the deployed API Gateway. Running the local API alone does not
automatically connect that frontend to localhost.

## Project layout

| Path | Purpose |
| --- | --- |
| `src/` | API server, recovery domain logic, and DynamoDB repository |
| `demo/` | Small local functional client served by `run_demo.sh` |
| `frontend/` | Stylized HTML experience, API bridges, map, and build inputs |
| `scripts/` | Local run, deterministic seed, and frontend packaging utilities |
| `template.yaml` | SAM definition for the API/Lambda backend |
| `docs/` | Product, API, data, AWS, demo, and status documentation |
| `assets/demo/` | Local presentation media; large video is excluded from Git |
| `tests/` | Python unit and workflow tests |
| `CHAT_HANDOFF.md` | Detailed project history and handoff context |

`frontend/backend-context/` contains historical reference snapshots, not the
active backend implementation. Generated output such as `dist/` and `.aws-sam/`
is local build material and is ignored by Git.

## Architecture

The intended hosted stack is Amplify Hosting for the frontend, API Gateway and
Lambda for the HTTP API, DynamoDB for shared records, S3 for temporary image
uploads, and Rekognition Custom Labels for optional image suggestions.
Amazon Location is an architectural option for approximate locality display;
the current map uses illustrative locality data. CloudWatch is used for basic
diagnostics. Authentication, payments, routing optimization, and notifications
are outside the POC scope.

The SAM template defines the backend API/Lambda, but does not provision every
dependent resource: the DynamoDB table, S3 bucket, Rekognition project/model,
and Amplify frontend are configured separately. Do not assume a clean checkout
can recreate the deployed stack by running SAM alone. AWS mode requires valid
credentials, region/resource configuration, and may incur charges.

## Frontend package

The current fast-package source is `frontend/phirFinal.optimized.html`. Build
the static package with:

```bash
python3 scripts/build_fast_frontend.py
```

The generated package is `dist/phir-fast/` and is ignored by Git. See
[`frontend/README.md`](frontend/README.md) for the distinction between this
source, the older `frontend/phirFinal.html`, generated media, and API setup.

## Demo data and AWS writes

Print/inspect the deterministic seed fixture without AWS:

```bash
python3 scripts/seed_demo_data.py
```

The script's `--write` option writes to DynamoDB and requires AWS credentials
and the correct table/region. `--replace` clears the selected table before
writing; verify the target carefully before using it. Do not use those options
against a shared or production table.

## AWS deployment

Deployment is not a one-command full-stack process. Backend deployment uses
AWS SAM and frontend hosting is managed separately through Amplify. Confirm
AWS identity, region, resource names, and expected cost before any cloud
operation; keep Rekognition Custom Labels models stopped except during intended
evaluation/inference. Follow the project-specific notes in
[`docs/aws/overview.md`](docs/aws/overview.md) and
[`CHAT_HANDOFF.md`](CHAT_HANDOFF.md). Never commit credentials, `.env` files,
household photos, or training data.

## Documentation

Start at [`docs/README.md`](docs/README.md) for the documentation index. The
API contract is in [`docs/api_contract.md`](docs/api_contract.md); data model
notes are in [`docs/dynamodb_schema.md`](docs/dynamodb_schema.md). The
repository guidance and product constraints are in [`AGENTS.md`](AGENTS.md).

## Development checks

From the repository root, the Python test suite can be run with:

```bash
python3 -m unittest discover -s tests -v
```

This command is documented for contributors; it is not run automatically by
the local demo script.
