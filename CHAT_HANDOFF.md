# Phir — Hackathon Handoff Context

This document is written for the next ChatGPT/Codex conversation. Read it fully
before changing anything. The goal is to continue the project with the same
context, product judgment, and implementation style established so far.

## Latest handoff — 12 October 2026

### Repository and deployment status update

- The judges subsequently reported HTTP 500 responses from deployed data
  endpoints; only the mock classify endpoint responded during their review.
  Treat the deployed data workflow described below as historical/unverified
  until the deployed Lambda artifact and API are inspected and smoke-tested.
- The judges also found that the deployed frontend bundle did not match the
  repository source. Deployment provenance needs to be re-established before
  claiming the live site reflects this checkout.
- The DynamoDB repository currently reads and rewrites a table snapshot for
  mutations. This is a known correctness/scaling concern; targeted writes or
  transactions have not yet replaced it.
- Local `./scripts/run_demo.sh` is an AWS-free in-memory demo of the simple
  `demo/` client. It does not run the stylized frontend, persist across restarts,
  or invoke Rekognition by default. See the root README for the current setup.

- Live frontend: <https://main.d3hgpobebqphe1.amplifyapp.com/>
- Historical Amplify deployment record: job `96`, status `SUCCEED` at the time
  of that deployment (app `d3hgpobebqphe1`,
  branch `main`, region `ap-south-1`).
- The live page now uses staged external assets. Root HTML is `367,099` bytes
  (previously `41,550,432` bytes), with all 44 original media files extracted
  byte-for-byte into content-hashed paths (`30,661,382` bytes total).
- The opening artwork, transition truck, and three role-card illustrations are
  preloaded first. A role-scene portrait starts downloading only on hover,
  keyboard focus, or touch of that role; other page imagery loads when its
  section is reached. The appearance and image bytes are unchanged.
- The 48,280-byte DM Sans variable font used by the first-screen Phir wordmark
  is also preloaded from the initial HTML response, ahead of the images, so the
  brand text can render with its intended font without waiting for CSS font
  discovery. The live HTML is now `367,260` bytes.
- Amplify custom headers give `/media/*` a one-year immutable cache policy;
  hashed filenames make that safe. Live checks confirmed the root and a sample
  image return HTTP 200, zero inline base64 assets remain, and the sample image
  exactly matches the local source bytes.
- The staged build matches the previous opening/chooser screenshot. A local
  browser test confirmed the transition and all three role characters render.
- `scripts/build_fast_frontend.py` recreates the static package in ignored
  `dist/phir-fast/`; the deployed archive was approximately 29 MB, but end users
  no longer download that entire archive as one HTML response. Keep the source
  `frontend/phirFinal.optimized.html` unchanged as the visual source of truth.
- A test deployment using a custom `Content-Encoding` header failed because
  Amplify treats that header as read-only. It did not affect the live site; do
  not repeat that custom-header approach.
- The lossless PNG re-encode test produced no savings, so do not trade image
  quality or alter the visual experience just to chase a smaller number. The
  owner wants the complete artwork preserved, but prefers staged loading over
  delivering every image in the initial HTML response.

## Project identity

Project name: **Phir**

Working meaning: every recyclable material can have another beginning.

Hackathon: Environmental Hacks / Bharat Builds Tour.

The project is a focused proof of concept for improving how recyclable household
material enters the existing kabadiwala/recovery network.

Core flow:

```text
Household → Recovery request → Kabadiwala → Collected inventory → Recycler
```

The product is not a municipal waste-management platform, a new collection
fleet, a full marketplace, or a production identity/payment system.

## Product story

Recoverable material is often lost before it reaches the recovery chain. The
physical recovery network already exists through local kabadiwalas and
aggregators, but households and downstream recyclers lack a simple coordination
layer.

The demo should begin with the environmental problem, then show:

1. A household records recyclable material.
2. The household creates a collection request.
3. A kabadiwala sees the request in the correct Delhi region.
4. The kabadiwala accepts and records collection.
5. The material enters kabadiwala inventory.
6. A recycler publishes demand, sees available material, books it, and confirms handover.
7. The app shows measured records, not unsupported carbon/tree claims.

## Current status

The local recovery workflow is implemented in the current checkout. The
deployed recovery workflow was reported failing during judging and is not
currently verified.

### Household

- Add material
- Edit available material
- Delete available material
- View inventory and estimated value
- Create collection request
- See resolved Delhi region on the request
- See request status
- Optional image-assisted entry
- Live S3/Rekognition Custom Labels path is configured in deployment
- Selecting a photo immediately runs recognition and displays material/confidence
- Manual confirmation remains available when confidence is low or recognition fails
- Backend metrics hydration

### Kabadiwala

- View region summaries
- View opportunities within a selected region
- Accept requests
- Decline requests
- Mark accepted requests collected
- View inventory
- View backend metrics
- View collector profile data
- Generate privacy-safe route preview

### Recycler

- Publish material requirements
- View available collected material
- See collector name and mapped Delhi region
- Reserve material
- View bookings
- Confirm handovers
- View backend metrics
- Save company profile

## Frontend

Primary frontend:

```text
frontend/phirFinal.optimized.html
```

This is the source consumed by `scripts/build_fast_frontend.py`; generated
output is written to ignored `dist/phir-fast/`. The older
`frontend/phirFinal.html` remains in the repository as a standalone source
artifact but is not used by that builder.

Supporting bridge scripts:

- `frontend/phir-config.js` — deployed API base URL
- `frontend/phir-api-bridge.js` — household API integration
- `frontend/phir-collector-api-bridge.js` — kabadiwala API integration
- `frontend/phir-recycler-api-bridge.js` — recycler API integration
- `frontend/phir-polish.js` — live API status, reset synchronization, metrics painting, and mobile polish

The frontend intentionally keeps presentation-only features local:

- Sorting game
- Story animation state
- Demo-record export

Those features do not represent shared recovery state.

`demo/index.html` is the simple functional client served by the local demo
script. It is separate from the stylized frontend and is the easiest client for
local API development.

## Delhi map model

The full hoverable frontend map contains 11 regions, and the backend now uses
the same set:

1. North
2. North West
3. West
4. South West
5. Central
6. New Delhi
7. North East
8. Shahdara
9. East
10. South East
11. South

Identifiers follow the pattern `area_north_west`, etc.

This is region grouping for demo simplicity. There is no user-configurable
kabadiwala radius metric in the active product model. Coordinates are
approximate and privacy-safe; exact household addresses are never exposed.

## Backend

Local backend entrypoint:

```bash
python3 -m src.api_server
```

Local default URL:

```text
http://localhost:8080
```

The backend uses:

- `src/recovery_domain.py` — business rules and state transitions
- `src/api_server.py` — local JSON HTTP API
- `src/area_opportunities.py` — 11-region grouping and summaries
- `src/dynamodb_repository.py` — DynamoDB persistence
- `src/image_storage.py` — temporary S3 upload helpers
- `src/image_classifier.py` — Rekognition/mock classification
- `src/route_planner.py` — deterministic privacy-safe route preview

Important state transitions:

```text
Material: available → requested → collected → reserved → transferred
Request: pending → accepted → collected
Requirement: open → partially_fulfilled → fulfilled
Booking: confirmed → completed
```

## Main API capabilities

Household:

```text
POST   /api/materials
PUT    /api/materials/{materialId}
DELETE /api/materials/{materialId}
GET    /api/households/{householdId}/inventory
POST   /api/collection-requests
GET    /api/households/{householdId}/collection-request
GET    /api/households/{householdId}/metrics
```

Kabadiwala:

```text
GET  /api/kabadiwalas/{id}/areas
GET  /api/kabadiwalas/{id}/areas/{areaId}/opportunities
GET  /api/kabadiwalas/{id}/requests
GET  /api/kabadiwalas/{id}/inventory
GET  /api/kabadiwalas/{id}/metrics
GET  /api/kabadiwalas/{id}/profile
POST /api/collection-requests/{requestId}/accept
POST /api/collection-requests/{requestId}/reject
POST /api/collection-requests/{requestId}/collect
POST /api/kabadiwalas/{id}/route
```

Recycler:

```text
POST /api/recycler-requirements
GET  /api/recyclers/{id}/requirements
GET  /api/recyclers/{id}/available-material
GET  /api/recyclers/{id}/bookings
GET  /api/recyclers/{id}/metrics
POST /api/recyclers/{id}/profile
POST /api/bookings
POST /api/bookings/{bookingId}/confirm
```

Demo/image:

```text
GET  /api/demo/users
POST /api/demo/reset
POST /api/image-upload
POST /api/classify-image
```

## AWS deployment

AWS account used:

```text
Account: 132218943520
Region: ap-south-1 (Mumbai)
```

Existing resources reused:

- DynamoDB table: `environmental-recovery`
- ML S3 bucket: `environmental-recovery-ml-132218943520`

New deployed resources:

- CloudFormation/SAM stack: `phir-recovery-api`
- API Gateway HTTP API
- Lambda function generated from `template.yaml`
- Amplify Hosting app: `phir-recovery`
- Amplify app ID: `d3hgpobebqphe1`

Live frontend:

```text
https://main.d3hgpobebqphe1.amplifyapp.com
```

Live API:

```text
https://jxhlv53d4f.execute-api.ap-south-1.amazonaws.com
```

The API uses HTTP API CORS for the Amplify origin and the ML S3 bucket allows
presigned PUT uploads from the hosted frontend. The Lambda role includes
`dynamodb:BatchWriteItem`, required by the repository batch writer.

Rekognition model currently configured:

```text
arn:aws:rekognition:ap-south-1:132218943520:project/environmental-recovery-classifier/version/trashnet-v1/1791474677175
```

The model version is running and uses the five-label TrashNet baseline:
`pet`, `cardboard`, `paper`, `aluminium`, and `glass`.

Important request handoff behavior: `/api/kabadiwalas/kabadiwala_1/requests`
returns all pending requests plus requests already assigned to that kabadiwala.
Region opportunities remain grouped by the simplified Delhi major-region map.

Deployment files:

- `template.yaml`
- `samconfig.toml`
- `src/lambda_handler.py`
- `.gitignore` excludes `.aws-sam/`

The Lambda adapter reuses the existing API routing logic and translates API
Gateway events into the existing request/response shape.

## Verification

The full Python test suite currently passes:

```text
25 tests passed
```

Useful checks:

```bash
python3 -m unittest discover -s tests -q
sam validate --template-file template.yaml
sam build --template-file template.yaml
node --check frontend/phir-api-bridge.js
node --check frontend/phir-collector-api-bridge.js
node --check frontend/phir-recycler-api-bridge.js
node --check frontend/phir-polish.js
git diff --check
```

## Git state and history

The repository is connected to:

```text
https://github.com/KarthikeyaPila/Environmental-Hacks.git
```

The latest pushed commits are:

```text
1bf09b8 fix: expose pending requests to kabadiwala
9b9f71e fix: enable browser CORS for image uploads
a238456 feat: classify household photo on selection
96919e6 fix: show household image recommendation
099014d fix: connect household photo recognition in frontend
2c7dce6 fix: enable material persistence and image classification
```

The working tree is currently dirty. Preserve existing work; do not reset,
clean, or revert files to make it appear clean. At handoff there are edits in
the frontend API/identity bridges and backend files, plus untracked demo and
documentation files. Check `git status --short` before editing or deploying.

Meaningful changes should be committed and pushed to `origin/main`. Do not
push every tiny edit; use coherent milestone commits.

## Known limitations / next work

1. The staged live frontend has had opening/chooser and HTTP smoke checks, but
   still needs a full interactive walkthrough of household, collector, and
   recycler flows.
2. AWS Rekognition Custom Labels is live in the deployed API; keep the model stopped when not actively demoing to control cost.
3. Authentication is intentionally omitted for the MVP.
4. The source visual file remains a ~41.55 MB self-contained HTML, but deployment
   must now go through `python3 scripts/build_fast_frontend.py` to split assets
   without recompressing or altering their bytes. Do not deploy that source HTML
   directly, or the first-load delay will return.
5. Amplify deployment is manual through the Amplify Hosting deployment API.
   Deploy the complete contents of ignored `dist/phir-fast/` as the site root;
   it includes the generated `index.html`, media files, bridge scripts, map,
   loader, and custom-header config. The app's `/media/*` cache policy is already
   configured in Amplify.
6. CloudWatch alarms and production observability are not configured beyond basic Lambda/API logging.
7. The API uses demo identities such as `household_1`, `kabadiwala_1`, and `recycler_1`.
8. The frontend should eventually replace remaining static descriptive copy with profile API values.
9. The Lambda adapter serializes requests within a warm execution environment.
   The snapshot repository still needs targeted conditional DynamoDB writes or
   transactions before it can safely support concurrent Lambda environments.

## Important product guardrails

- Keep the project focused on recovery coordination.
- Do not add payment processing, authentication, notifications, fleet routing,
  social features, carbon calculators, or unsupported impact claims.
- Keep images temporary.
- Keep household locations approximate.
- Let the kabadiwala decide collection order; route preview is only decision support.
- Prefer deterministic local/mock behavior while developing.
- Cut ML before cutting the household → kabadiwala → recycler flow.

## How to continue naturally

Start by acknowledging the current deployed state and read this file before
asking questions. The best next step is a browser-based walkthrough of the live
frontend's household, collector, and recycler flows, followed by fixing any
real interaction bugs found there.

Work conversationally and collaboratively. The project owner likes direct,
practical progress, dislikes unnecessary scope expansion, and prefers that
meaningful changes are verified, committed, and pushed.
