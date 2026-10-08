# Frontend Backend Handoff

This document describes what the backend provides to the frontend. The
frontend team owns layout, styling, components, navigation, responsiveness,
animations, and all visual design decisions.

Use `docs/api_contract.md` as the authoritative request and response schema.
The backend runs at `http://localhost:8080` in local development, with API
routes under `/api`.

## Shared backend rules

- JSON fields use `camelCase`.
- IDs are opaque strings.
- Quantities are kilograms as numbers.
- Currency values are Indian rupees as numbers.
- Timestamps are ISO-8601 strings where provided.
- Authentication is omitted for the MVP; demo IDs are used in requests.
- Backend owns pricing, state transitions, inventory calculations, matching,
  metrics, and validation.
- Do not recreate those rules in frontend code.
- Handle loading, empty, validation, success, and error responses.

## Household page: backend capabilities

The household page can:

- Add material with `POST /api/materials`.
- Read inventory with `GET /api/households/{householdId}/inventory`.
- Edit available material with `PUT /api/materials/{materialId}`.
- Delete available material with `DELETE /api/materials/{materialId}`.
- Create one active collection request with `POST /api/collection-requests`.
- Read the current request with `GET /api/households/{householdId}/collection-request`.
- Read contribution metrics with `GET /api/households/{householdId}/metrics`.

Supported material values are `pet`, `cardboard`, `paper`, `aluminium`,
`glass`, and `wood`. The backend returns estimated value and material status.
The household must confirm image suggestions before creating a material.

## Kabadiwala page: backend capabilities

The kabadiwala page can:

- Read Delhi locality summaries with `GET /api/kabadiwalas/{kabadiwalaId}/areas`.
- Read locality opportunities with `GET /api/kabadiwalas/{kabadiwalaId}/areas/{areaId}/opportunities`.
- Accept a request with `POST /api/collection-requests/{requestId}/accept`.
- Reject a request with `POST /api/collection-requests/{requestId}/reject`.
- Mark an accepted request collected with `POST /api/collection-requests/{requestId}/collect`.
- Read collected inventory with `GET /api/kabadiwalas/{kabadiwalaId}/inventory`.
- Read assigned request history with `GET /api/kabadiwalas/{kabadiwalaId}/requests`.
- Read profile indicators with `GET /api/kabadiwalas/{kabadiwalaId}/profile`.
- Read metrics with `GET /api/kabadiwalas/{kabadiwalaId}/metrics`.

Area and opportunity coordinates are approximate. The backend must not expose
household names, phone numbers, addresses, or exact home locations.

### Route planning

For selected opportunity IDs, call:

```text
POST /api/kabadiwalas/{kabadiwalaId}/route
```

with `areaId`, `requestIds`, and optional `optimizeFor`. The response provides
ordered approximate stops, route coordinates, distance, duration, and a mode.
The current mode is `local-preview`; Amazon Location can provide a future
road-aware route without changing the response contract.

## Recycler page: backend capabilities

The recycler page can:

- Create a requirement with `POST /api/recycler-requirements`.
- Read requirements with `GET /api/recyclers/{recyclerId}/requirements`.
- Read available material with `GET /api/recyclers/{recyclerId}/available-material`.
- Create a booking with `POST /api/bookings`.
- Confirm a booking with `POST /api/bookings/{bookingId}/confirm`.
- Read booking history with `GET /api/recyclers/{recyclerId}/bookings`.
- Read metrics with `GET /api/recyclers/{recyclerId}/metrics`.

Booking reserves material immediately. Material transfers only after booking
confirmation. The backend updates requirement fulfillment and material status.

## Image-assisted material input

Preferred AWS flow:

```text
POST /api/image-upload
→ PUT image to returned uploadUrl
→ POST /api/classify-image with s3Key
→ user confirms prediction
→ POST /api/materials
```

Only JPG and PNG images are supported. Temporary S3 objects are deleted after
classification. The current model is trained for one dominant material per
image; mixed-material recognition is not supported by this model.

The legacy `filename` and `imageBase64` inputs remain available for local/mock
fallback behavior. AWS model startup or runtime failures return HTTP 503 with
error code `AWS_SERVICE_ERROR`.

## State values supplied by the backend

Material lifecycle: `available → requested → collected → reserved → transferred`

Collection request lifecycle: `pending → accepted → collected`

Requirement lifecycle: `open → partially_fulfilled → fulfilled`

Booking lifecycle: `confirmed → completed`

## Runtime and testing

The backend can run in local mock/in-memory mode or AWS-backed mode using
DynamoDB, S3, and Rekognition. The frontend should function in both modes and
must not contain AWS credentials.

Run locally with:

```bash
./scripts/run_demo.sh
```

Verify the complete journey:

```text
household material → collection request → kabadiwala accept → collect
→ recycler requirement → booking → confirmation → updated metrics
```
