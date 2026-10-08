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
      "areaId": "area_north_delhi",
      "name": "North Delhi",
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
### `GET /api/recyclers/{recyclerId}/metrics`

Metrics are derived only from stored records. No unsupported carbon or
tree-equivalent claims are returned.
