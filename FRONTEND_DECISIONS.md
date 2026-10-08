# Frontend Decisions and Handoff Guide

This document is the shared frontend reference for the Environmental Recovery
Platform. The frontend should consume the backend API rather than recreate
business rules locally.

## How to use this document

This is the authoritative frontend handoff for Lovable or any frontend
developer. Read this document first, then use `docs/api_contract.md` for exact
request and response schemas. Do not invent endpoints, fields, workflow rules,
pricing, or status transitions.

## Development setup

Run the backend from the repository root:

```bash
./scripts/run_demo.sh
```

The demo is available at `http://localhost:8080`. The API base path is `/api`.
The frontend may use a configurable `VITE_API_BASE_URL` or equivalent, with an
empty value for same-origin local development.

The backend supports two modes:

- Local mode: in-memory state and deterministic mock image classification.
- AWS mode: DynamoDB persistence, private S3 uploads, and Rekognition Custom
  Labels image classification.

The frontend must work in both modes and must not assume AWS is available.

## Product story

The application connects:

```text
Household → Kabadiwala → Recycler
```

The product improves the flow of recyclable household material into the
existing recovery network. It is a focused hackathon proof of concept, not a
full municipal waste-management system.

## Roles

The MVP uses temporary seeded users instead of authentication. A demo role/user
switcher is acceptable, but each role should see only its own relevant data.

### Household view

The household should be able to:

- Add material manually using a controlled material list.
- Enter estimated weight in kilograms, including fractional values.
- See aggregated inventory and estimated rupee value.
- Edit or remove material that has not entered a request.
- Create one active collection request.
- Add new material directly to a pending request.
- See request status and assigned kabadiwala details.
- View measured contribution metrics and downstream destination.

Supported materials: `pet`, `cardboard`, `paper`, `aluminium`, `glass`, and
`wood`. Unknown material should remain a manual/discard decision. Image
classification is optional and must always allow confirmation/correction. The
current AWS model expects one dominant material per image; guide users toward
single-item photos and show a retry state while the model is starting.

### Kabadiwala view

The main view is area-based, not a list of household addresses:

```text
Delhi → locality summary → approximate pickup opportunities
```

Show locality name, opportunity rank, request count, total kilograms, estimated
value, and material breakdown. Clicking an area reveals approximate coordinates
and pickup material. Never expose exact household addresses.

The kabadiwala can accept a pending request, mark it collected, view assigned
request history, view aggregated inventory, and see profile/performance
indicators. Ratings and payout values are seeded demo indicators, not real
user-generated reputation scores.

### Recycler view

The recycler should be able to:

- Create one active requirement per material type.
- Set required and minimum quantities.
- View all relevant kabadiwala inventory.
- Create partial bookings.
- See booking status and history.
- Confirm transfer after booking.

## State displays

Material lifecycle:

```text
available → requested → collected → reserved → transferred
```

Collection request lifecycle:

```text
pending → accepted → collected
```

Requirement lifecycle:

```text
open → partially_fulfilled → fulfilled
```

Booking lifecycle:

```text
confirmed → completed
```

Booking reserves material immediately. Ownership changes only after recycler
confirmation. The UI should make `reserved` visibly different from
`transferred`.

## API conventions

- Base path: `/api`
- JSON fields: `camelCase`
- IDs: opaque strings
- Dates: ISO 8601 UTC strings
- Quantities: kilograms as numbers
- Currency: rounded Indian rupees
- Authentication: omitted for MVP; send demo `userId` where required
- MVP responses are small seeded result sets; pagination is not required

Use `docs/api_contract.md` as the exact source for every endpoint. Common error
codes include `INVALID_REQUEST`, `NOT_FOUND`, and `AWS_SERVICE_ERROR`. Display
the returned human-readable message for development, but use friendly UI copy
in the final product. HTTP 503 from image classification means the AWS model is
starting, stopped, or temporarily unavailable; show a retry action.

Full endpoint details and payload examples live in `docs/api_contract.md`.

For image assistance, use this sequence:

```text
POST /api/image-upload → PUT uploadUrl → POST /api/classify-image → confirm
```

The backend deletes the temporary S3 object after classification. If direct S3
upload is blocked in local development, the demo has an API fallback.

The preferred request sequence is:

```text
POST /api/image-upload
  → PUT the file to uploadUrl with Content-Type and x-amz-server-side-encryption: AES256
  → POST /api/classify-image with s3Key
  → display prediction and confidence
  → wait for user confirmation
  → POST /api/materials if confirmed
```

Only allow JPG and PNG files, enforce a 5 MB client-side limit, show upload and
classification progress, and handle failed uploads. The backend deletes the
temporary S3 object after AWS classification. Never put AWS credentials in the
frontend. The current model recognizes one dominant item per image, so guide
users to photograph one material at a time. Mixed-material photos should show
that limitation rather than silently producing an incomplete result.

## Kabadiwala map and route experience

When a kabadiwala selects a Delhi locality:

1. Zoom the map to the locality `center` returned by the areas endpoint.
2. Render one privacy-safe approximate pin per pending opportunity.
3. Do not render household names, addresses, phone numbers, or exact homes.
4. Let the kabadiwala select stops and click **Plan route**.
5. Call `POST /api/kabadiwalas/{kabadiwalaId}/route` with `areaId` and the
   selected `requestIds`.
6. Draw the returned `route` as a polyline and show ordered stop numbers,
   total distance, and estimated duration.

The current response uses `mode: local-preview` and deterministic nearest-
neighbour ordering. Keep the UI independent of this mode because the same
contract will later return an Amazon Location road-aware route. Use
`optimizeFor: distance` for the demo; a future option can support `time`.

### Map implementation details

The backend already provides 14 approximate Delhi locality centers. The map
should initially render those centers and their opportunity summaries. When a
locality is selected, zoom to its `center` and request its opportunities.

Each opportunity may be represented by an approximate marker containing only:

- Request ID
- Approximate latitude and longitude
- Material breakdown
- Estimated kilograms
- Estimated rupee value
- Request status

Do not show household names, phone numbers, exact addresses, or exact home
locations. Marker positions are for operational visualization, not navigation
to a resident's home.

For route planning, send selected request IDs to:

```text
POST /api/kabadiwalas/kabadiwala_1/route
```

The response includes `mode`, ordered `stops`, `route`, `totalDistanceKm`, and
`estimatedDurationMinutes`. Draw `route` as a polyline and label each stop with
`stopNumber`. The current backend uses `mode: local-preview`; keep the map
component replaceable because Amazon Location Routes can later provide
road-aware `OptimizeWaypoints` results without changing the UI contract.

Amazon Location Maps/MapLibre is the intended map direction. Do not add live
tracking, geofences, route optimization UI, or exact household navigation to
the MVP.

## Suggested frontend structure

Use components or modules equivalent to:

```text
src/
├── api/                 # typed API client and request helpers
├── components/          # reusable cards, status badges, dialogs, map
├── pages/               # Household, Kabadiwala, Recycler views
├── state/               # selected role, selected area, request/route state
└── types/               # API response/request types
```

Keep API calls in one client layer. Keep material/status constants in one place,
but do not duplicate domain transitions. Use optimistic UI only where failure
rollback is implemented; normal API refreshes are safer for this demo.

## Acceptance checklist

- Household can add, edit, remove, and submit materials.
- Household can confirm or correct image predictions.
- Kabadiwala can select a locality and see approximate opportunity markers.
- Kabadiwala can select stops and see an ordered route preview.
- Kabadiwala can accept and collect requests.
- Recycler can create requirements, book supply, and confirm transfers.
- All views show loading, empty, error, and success states.
- Refreshing data does not duplicate cards or requests.
- No exact household location or private AWS credential reaches the UI.
- The interface works with both local mock mode and AWS-backed mode.

Important endpoints include:

```text
POST /api/materials
PUT /api/materials/{materialId}
DELETE /api/materials/{materialId}
POST /api/collection-requests
GET  /api/kabadiwalas/{id}/areas
GET  /api/kabadiwalas/{id}/areas/{areaId}/opportunities
POST /api/collection-requests/{id}/accept
POST /api/collection-requests/{id}/collect
POST /api/recycler-requirements
GET  /api/recyclers/{id}/available-material
POST /api/bookings
POST /api/bookings/{id}/confirm
```

Errors use:

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Human-readable explanation"
  }
}
```

## Demo priorities

The three-minute story should show one complete material journey:

1. Household adds PET/cardboard.
2. Household creates a collection request.
3. Kabadiwala opens a Delhi locality and accepts the opportunity.
4. Kabadiwala marks the material collected.
5. Recycler sees the supply, creates a requirement, books, and confirms transfer.
6. Metrics update from actual records.

Keep the interface clear and functional. Avoid heavy gamification, unsupported
carbon conversions, fake AI behavior, route optimization, payments, and
authentication.

## Runtime configuration

The backend can run in mock/in-memory mode or AWS-backed mode. The frontend
should display a retry state for HTTP 503 responses from image classification.

```text
DYNAMODB_ENABLED=true
AWS_REGION=ap-south-1
ML_S3_BUCKET=environmental-recovery-ml-132218943520
REKOGNITION_MODEL_ARN=<configured by runtime>
```
