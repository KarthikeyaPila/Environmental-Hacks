# AWS services feedback

## What worked well

AWS SAM made our API Gateway and Lambda setup repeatable from one template, and
the AWS CLI made deploying and checking Amplify builds straightforward. API
Gateway and Lambda gave us a simple serverless path for the app, while DynamoDB
let the household, collection partner, and recycler share persisted recovery
records without managing a database server. S3 presigned uploads paired cleanly
with Rekognition Custom Labels for the photo identification demo. Amplify
Hosting also made publishing the frontend quick.

## What could be better

The first-time setup involved several separate pieces: Amplify hosting, the
API, DynamoDB, S3 permissions, Rekognition configuration, and CORS. When a
frontend URL changed, the API CORS allowlist had to be updated and redeployed;
that made experimenting with a readable Amplify branch URL unexpectedly
costly and error-prone. SAM deployments also uploaded a large artifact, making
small backend changes slower than expected. Rekognition Custom Labels requires
careful model configuration and active model availability, which adds setup
and cost considerations for a short demo. A clearer end-to-end starter flow
for connecting Amplify, API Gateway, Lambda, DynamoDB, and temporary S3 uploads
would make this kind of prototype easier to onboard and iterate on.

-------------------

## AWS services used

- **AWS Amplify Hosting** — deploys the frontend.
- **Amazon API Gateway HTTP API** — exposes backend endpoints.
- **AWS Lambda** — runs application logic.
- **Amazon DynamoDB** — persists recovery profiles, materials, requests,
  inventories, requirements, and bookings.
- **Amazon S3** — temporarily stores photo uploads.
- **Amazon Rekognition Custom Labels** — suggests material from uploaded
  photos.
- **Amazon CloudWatch** — provides Lambda logs for troubleshooting.
- **AWS IAM** — scopes backend access to AWS resources.
- **AWS CloudFormation via AWS SAM** — defines and deploys infrastructure.
- **Amazon CloudFront** — delivery layer managed by Amplify Hosting.

The locality map is illustrative; Amazon Location Service is not currently
integrated into the deployed map.
