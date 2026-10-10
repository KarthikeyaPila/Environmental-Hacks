# Development Status

## Current milestone

Harden the deployed three-role vertical slice and verify the live browser flow.

## Completed

- Product and technical decision questionnaire
- Shared repository foundation
- Initial in-memory domain service
- Basic material, request, collection, inventory, requirement, and booking tests
- Shared API contract
- Deployed Amplify frontend, API Gateway/Lambda backend, DynamoDB persistence,
  temporary S3 image uploads, and Rekognition integration

## Next

- Harden partial reservation and material-splitting behavior
- Complete a browser smoke test of all three live roles
- Remove remaining frontend/backend and documentation drift
- Stop Rekognition Custom Labels outside active demonstrations
- The Lambda adapter serializes requests within a warm execution environment;
  targeted DynamoDB conditional writes/transactions remain required before
  allowing concurrent environments to safely mutate shared state.

## Collaboration rule

The API contract is the boundary between backend and frontend. Changes to
endpoint names or JSON fields should be reflected in `docs/api_contract.md`
before implementation changes are merged.
