# Frontend Decisions and Handoff Guide

This document is the shared frontend reference for the Environmental Recovery
Platform. The frontend should consume the backend API rather than recreate
business rules locally.

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

Full endpoint details and payload examples live in `docs/api_contract.md`.

For image assistance, use this sequence:

```text
POST /api/image-upload → PUT uploadUrl → POST /api/classify-image → confirm
```

The backend deletes the temporary S3 object after classification. If direct S3
upload is blocked in local development, the demo has an API fallback.

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
