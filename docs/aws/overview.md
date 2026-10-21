# Phir — Project and AWS Architecture Notes

This document describes the intended/reference AWS architecture and prior
integration. It is not a live health report: the hackathon review found that
deployed data endpoints returned HTTP 500, and the deployed bundle did not
match the repository source. Check the root README and `development_status.md`
before presenting any integration as currently verified.

## What the project does

Phir is a digital coordination layer for recyclable household material.
Recoverable material often gets mixed into ordinary waste because the handoff
between households, local collection partners, and recycling companies is not
visible or coordinated.

Phir connects that flow:

**Household → Collection partner → Recycler**

Households can record material manually or use photo-assisted identification,
request a collection, and track progress. Collection partners can discover
nearby requests, accept and complete collections, and manage recovered
inventory. Recycling companies can publish material requirements, view matching
available material, and book it for downstream processing.

The goal is not to replace the existing kabadiwala network. It is to help more
recyclable material reach that network and remain traceable through the next
handoff.

## How AWS is used

### AWS open-source tools

- **AWS Serverless Application Model (AWS SAM) and SAM CLI:** define, build,
  package, and deploy the API Gateway and Lambda infrastructure from the
  project’s `template.yaml`.
- **AWS CLI:** deploy Amplify builds, inspect AWS resources, reset demo data,
  and verify deployment status from repeatable commands.
- **Boto3, the AWS SDK for Python:** connect the Python backend to DynamoDB, S3,
  and Rekognition using standard AWS SDK clients.

These tools cover the checked-in backend definition and SDK integration. Some
dependencies (including DynamoDB, S3, Rekognition, and Amplify configuration)
are managed separately and are not all provisioned by the SAM template.

### AWS services

- **AWS Amplify Hosting:** hosts and deploys the single-page frontend.
- **Amazon CloudFront:** provides the content-delivery layer managed by
  Amplify Hosting, allowing the frontend to load quickly for viewers.
- **Amazon API Gateway HTTP API:** exposes the REST-style application API to
  the frontend.
- **AWS Lambda:** runs the backend logic for materials, collection requests,
  state transitions, inventory, recycler requirements, bookings, and metrics.
- **Amazon DynamoDB:** stores profiles, material records, collection requests,
  inventories, requirements, bookings, and their statuses in the shared
  application data layer.
- **Amazon S3:** stores uploaded photos temporarily during material
  identification. The backend generates a short-lived upload URL and removes
  the temporary object after processing.
- **Amazon Rekognition Custom Labels:** provides the photo-assisted material
  suggestion for selected recyclable categories. The result assists the user;
  the household confirms the material and supplies the weight.
- **Amazon CloudWatch:** receives Lambda logs and supports basic debugging of
  API behavior and AWS classification failures.
- **AWS IAM:** controls the Lambda execution permissions for DynamoDB, S3, and
  Rekognition using scoped access policies.
- **AWS CloudFormation:** provisions the serverless resources through the AWS
  SAM template, making the deployment repeatable.

### Current scope note

The Delhi map in the current demo is an illustrative, privacy-safe locality
map. **Amazon Location Service** is the planned AWS-native extension for a
production location layer; it is not presented as the source of exact household
locations in this prototype.

Authentication is intentionally outside the current hackathon MVP. The demo
uses lightweight profiles and seeded data so the complete recovery journey can
be shown without adding a production identity system.

## End-to-end AWS flow

```text
Frontend on Amplify
        ↓
API Gateway HTTP API
        ↓
Lambda business logic
        ↓
DynamoDB shared recovery records

Photo → temporary S3 object → Rekognition Custom Labels
                         → confirmed material → DynamoDB
```

The intended public alias for the deployed demo is **phir-recovery.in**; the
custom-domain and DNS association is a separate hosting configuration step.
