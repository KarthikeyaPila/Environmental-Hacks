# DynamoDB Schema

Table: `environmental-recovery` in `ap-south-1`  
Billing: on-demand  
Primary key: `pk` + `sk`  
Indexes: `gsi1(gsi1pk, gsi1sk)` and `gsi2(gsi2pk, gsi2sk)`

The table uses a single-table layout so the household, kabadiwala, and
recycler flows can share one consistent source of truth.

## Item shapes

| Entity | `pk` | `sk` | Useful index keys |
| --- | --- | --- | --- |
| Profile | `PROFILE#<id>` | `PROFILE` | `gsi1pk=ROLE#<role>`, `gsi1sk=<id>` |
| Material | `MATERIAL#<id>` | `MATERIAL` | `gsi1pk=OWNER#<profileId>`, `gsi1sk=<status>#<id>`; `gsi2pk=MATERIAL#<type>#<status>`, `gsi2sk=<id>` |
| Collection request | `REQUEST#<id>` | `REQUEST` | `gsi1pk=HOUSEHOLD#<id>`, `gsi1sk=<createdAt>#<id>`; `gsi2pk=REQUEST_STATUS#<status>`, `gsi2sk=<createdAt>#<id>` |
| Recycler requirement | `REQUIREMENT#<id>` | `REQUIREMENT` | `gsi1pk=RECYCLER#<id>`, `gsi1sk=<status>#<id>` |
| Booking | `BOOKING#<id>` | `BOOKING` | `gsi1pk=RECYCLER#<id>`, `gsi1sk=<createdAt>#<id>` |

Amounts are stored as DynamoDB `Decimal` values, timestamps as ISO-8601 UTC
strings, and status transitions are written with conditional expressions.

## Migration sequence

1. Add a repository adapter using the schema above.
2. Add read-through support behind `DYNAMODB_ENABLED=false` by default.
3. Backfill only deterministic demo records for local integration testing.
4. Enable writes in a staging environment and verify request, reservation, and
   transfer transitions.
5. Switch the API default after persistence tests pass.

Never store image bytes in DynamoDB. Keep images in private S3 and store only
the object key and classification metadata.
