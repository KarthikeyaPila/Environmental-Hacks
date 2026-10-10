# Phir — Hackathon Handoff Context

This document is written for the next ChatGPT/Codex conversation. Read it fully
before changing anything. The goal is to continue the project with the same
context, product judgment, and implementation style established so far.

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

The core local and deployed recovery workflow is implemented.

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
frontend/phirFinal.html
```

This is a large, self-contained cinematic HTML experience with embedded fonts,
artwork, styles, story scenes, role selection, dashboards, and a presentation
sorting game.

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

The old `demo/index.html` remains a simple functional/reference client. It is
not the primary frontend anymore.

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

The working tree was clean after the deployment commit.

Meaningful changes should be committed and pushed to `origin/main`. Do not
push every tiny edit; use coherent milestone commits.

## Known limitations / next work

1. The deployed frontend has not had a full interactive browser walkthrough yet.
2. AWS Rekognition Custom Labels is live in the deployed API; keep the model stopped when not actively demoing to control cost.
3. Authentication is intentionally omitted for the MVP.
4. The frontend is a 46 MB single HTML file because it embeds visual assets.
5. Amplify deployment currently publishes the static frontend manually through the Amplify Hosting deployment API; the package must contain the root file `index.html` copied from `frontend/phirFinal.html`.
6. CloudWatch alarms and production observability are not configured beyond basic Lambda/API logging.
7. The API uses demo identities such as `household_1`, `kabadiwala_1`, and `recycler_1`.
8. The frontend should eventually replace remaining static descriptive copy with profile API values.

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
asking questions. The best next step is a browser-based smoke test of the live
frontend, followed by fixing any real interaction bugs found there.

Work conversationally and collaboratively. The project owner likes direct,
practical progress, dislikes unnecessary scope expansion, and prefers that
meaningful changes are verified, committed, and pushed.
