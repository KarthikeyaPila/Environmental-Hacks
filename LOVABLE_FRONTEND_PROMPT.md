# Lovable Frontend Handoff Prompt

Build the frontend for this repository's Environmental Recovery Platform.
Before coding, read these files in order:

1. `FRONTEND_DECISIONS.md` — product behavior, roles, privacy, map, and image UX.
2. `docs/api_contract.md` — authoritative API endpoints and JSON schemas.
3. `README.md` — setup and project context.

## Non-negotiable rules

- Use the existing backend API; do not recreate workflow, pricing, status, or
  inventory logic in the frontend.
- Keep JSON fields in camelCase and preserve opaque IDs.
- Support three role views: Household, Kabadiwala, and Recycler.
- Show loading, empty, success, validation, and HTTP 503 retry states.
- Never display exact household addresses or exact home locations.
- Keep image classification user-confirmed; never silently save a prediction.

## Core experiences

Household: add material and kilograms, inspect inventory, use image assistance,
confirm/correct the prediction, and create one collection request.

Kabadiwala: choose a Delhi locality, zoom the map to its center, show
approximate opportunity pins, select stops, call the route endpoint, and draw
the returned route with ordered stop numbers, distance, and duration.

Recycler: create a material requirement, view collected inventory, book material,
and confirm transfer.

## Image flow

Use `POST /api/image-upload`, PUT the selected JPG/PNG to `uploadUrl` with the
returned headers, then call `POST /api/classify-image` with `s3Key`. Display
material, confidence, AWS/mock mode, and a confirmation action. Guide users to
upload one dominant material per image; mixed-material detection is not yet
supported.

## Map flow

Initially support the backend's `mode: local-preview` route response. Render
`route` as a polyline and `stops` as numbered markers. Keep the map component
replaceable so Amazon Location Maps can be added later.

Do not invent endpoints. If an API detail is unclear, consult
`docs/api_contract.md` before making assumptions.
