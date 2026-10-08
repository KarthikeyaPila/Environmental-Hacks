# Development Status

## Current milestone

Define the API contract and build a local vertical slice that can later be
connected to the final frontend.

## Completed

- Product and technical decision questionnaire
- Shared repository foundation
- Initial in-memory domain service
- Basic material, request, collection, inventory, requirement, and booking tests
- Shared API contract

## Next

- Add explicit Delhi area and pickup-opportunity models
- Implement material reservation and transfer states
- Add seeded demo data and reset script
- Add local JSON HTTP API
- Build the temporary `demo/` HTML client
- Test the complete three-role flow
- Add AWS SAM deployment and DynamoDB persistence

## Collaboration rule

The API contract is the boundary between backend and frontend. Changes to
endpoint names or JSON fields should be reflected in `docs/api_contract.md`
before implementation changes are merged.
