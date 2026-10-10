# Recovery Platform API Contract

This is the frontend/backend boundary for the MVP. The temporary demo UI and
the final frontend should use the same JSON shapes.

## Conventions

- Base URL: `/api`
- JSON field names: `camelCase`
- IDs: opaque strings
- Dates: ISO 8601 UTC strings
- Quantities: kilograms as numbers; fractional values are valid
- Currency: rounded Indian rupees as numbers
- Authentication: omitted for the MVP; the demo sends a `userId`

Successful responses return the resource directly unless noted otherwise.

Errors use:

```json
{
  "error": {
    "code": "INVALID_STATE",
    "message": "Request must be accepted before collection"
  }
}
```

## Demo context

### `GET /api/demo/users`

Returns seeded users available to the temporary role switcher.

```json
{
  "users": [
    {
      "id": "household_1",
      "role": "household",
      "name": "Household A"
    }
  ]
}
```

### `POST /api/demo/reset`

Resets the local/demo data to the known seeded scenario. Returns `{ "ok": true }`.

## Household endpoints

### `POST /api/materials`

Request:

```json
{
  "userId": "household_1",
  "materialType": "pet",
  "quantityKg": 2.4
}
```

Repeated additions of the same material merge into the household aggregate.

### `PUT /api/materials/{materialId}`

Updates the quantity of available household material. Requested or collected
material cannot be edited.

```json
{
  "userId": "household_1",
  "quantityKg": 3.1
}
```

### `DELETE /api/materials/{materialId}`

Removes available household material. Material already attached to a request
cannot be removed.

### `GET /api/households/{householdId}/inventory`

Returns aggregate material, estimated value, and active request status.

### `POST /api/collection-requests`

```json
{
  "householdId": "household_1"
}
```

The request includes all currently available household inventory. A household
can have one active request. New material added while it is pending joins the
request and its area opportunity.

### `GET /api/households/{householdId}/collection-request`

Returns the household's active request and status.

## Kabadiwala endpoints

### `GET /api/kabadiwalas/{kabadiwalaId}/areas`

Returns Delhi area summaries visible to the kabadiwala.

```json
{
  "areas": [
    {
      "areaId": "area_north",
      "name": "North",
      "requestCount": 12,
      "materialKg": 31.0,
      "estimatedValueInr": 1840,
      "opportunityRank": 1,
      "materialBreakdown": {"pet": 12.0, "cardboard": 19.0},
      "isActiveForCollector": true
    }
  ]
}
```

### `GET /api/kabadiwalas/{kabadiwalaId}/areas/{areaId}/opportunities`

Returns approximate pickup coordinates and material summaries for the selected
area. Exact household addresses are never returned.

### `POST /api/collection-requests/{requestId}/accept`

```json
{ "kabadiwalaId": "kabadiwala_1" }
```

The first valid acceptance assigns the request to that kabadiwala.

### `POST /api/collection-requests/{requestId}/collect`

```json
{ "kabadiwalaId": "kabadiwala_1" }
```

Transitions an accepted request to `collected` and updates aggregate inventory.

### `GET /api/kabadiwalas/{kabadiwalaId}/inventory`

Returns collected material grouped by type with estimated value.

### `GET /api/kabadiwalas/{kabadiwalaId}/requests`

Returns requests assigned to the kabadiwala, including their current status.

## Recycler endpoints

### `POST /api/recycler-requirements`

```json
{
  "recyclerId": "recycler_1",
  "materialType": "pet",
  "requiredQuantityKg": 500,
  "minimumQuantityKg": 50
}
```

Each material type has one active requirement per recycler for the MVP.

### `GET /api/recyclers/{recyclerId}/available-material`

Returns all kabadiwala inventory grouped by kabadiwala and material type, with
matching requirements highlighted.

### `GET /api/recyclers/{recyclerId}/bookings`

Returns the recycler's booking history, including `confirmed` and `completed`
bookings.

### `POST /api/bookings`

```json
{
  "recyclerId": "recycler_1",
  "requirementId": "requirement_1",
  "kabadiwalaId": "kabadiwala_1",
  "quantityKg": 50
}
```

Booking reserves material immediately. It is not transferred until confirmation.

### `POST /api/bookings/{bookingId}/confirm`

```json
{ "recyclerId": "recycler_1" }
```

Transfers ownership to the recycler and updates requirement fulfillment.

## Metrics endpoints

### `GET /api/households/{householdId}/metrics`
### `GET /api/kabadiwalas/{kabadiwalaId}/metrics`

### `GET /api/kabadiwalas/{kabadiwalaId}/profile`

Returns the collector's seeded demo profile indicators and supported materials.
`demoRating` and `payoutIndex` are demonstration values,
not user-generated reputation scores.
### `GET /api/recyclers/{recyclerId}/metrics`

### `POST /api/recyclers/{recyclerId}/profile`

Updates the demo recycler company profile. Authentication is intentionally
omitted for the MVP.

Metrics are derived only from stored records. No unsupported carbon or
tree-equivalent claims are returned.

## Image classification

### `POST /api/classify-image`

For AWS mode, upload the image first with `POST /api/image-upload`, then send
the returned `key`. The legacy `filename` input remains available for local
mock mode, and `imageBase64` remains a compatibility fallback.

### `POST /api/image-upload`

Request: `{ "filename": "bottle.jpg", "contentType": "image/jpeg" }`

Response: `{ "uploadUrl": "https://...", "key": "demo-uploads/<id>.jpg", "expiresIn": 600 }`

The frontend must `PUT` the file to `uploadUrl` with the same `Content-Type`
and `x-amz-server-side-encryption: AES256` headers, then call
`POST /api/classify-image` with `{ "s3Key": "..." }`. The backend deletes the
temporary S3 object after AWS classification.

```json
{
  "s3Key": "demo-uploads/<opaque-id>.jpg"
}
```

The current model is single-item image classification. Ask users to upload one
dominant material per image. Mixed-material scenes require a future multi-label
or object-detection model. If the model is starting or stopped, the API returns
HTTP `503` with error code `AWS_SERVICE_ERROR`; show a retry message.

## Kabadiwala map and route planning

### `POST /api/kabadiwalas/{kabadiwalaId}/route`

The frontend sends selected request IDs and an area ID. The backend returns
privacy-safe approximate stop coordinates only; it never exposes household
addresses or exact home locations.

Request:

```json
{
  "areaId": "area_rohini",
  "requestIds": ["req_123", "req_456"],
  "optimizeFor": "distance"
}
```

The response contains `mode`, ordered `stops`, a `route` polyline coordinate
list, `totalDistanceKm`, and `estimatedDurationMinutes`. Stop numbers define
the pickup order. The current backend uses a deterministic local preview; it
will later be replaced by Amazon Location Routes `OptimizeWaypoints` without
changing this frontend contract.

Response:

```json
{
  "detections": [
    {
      "materialType": "pet",
      "confidence": 0.92,
      "requiresConfirmation": false
    }
  ],
  "mode": "mock"
}
```
