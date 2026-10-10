# Technical Plan — Environmental Hackathon Project

## 1. Technical Objective

Build a lightweight digital recovery platform that improves the flow of recyclable household material into the existing kabadiwala/recovery network.

Core technical flow:

**Household request → material record → nearby recovery requests/map → kabadiwala decision → collection → kabadiwala inventory → recycler demand/booking**

The system is intentionally scoped as a proof of concept. We are not building a production waste-management platform, full logistics operation, payment system, or real-time marketplace.

---

## 2. Proposed Technology Stack

### Frontend
- **React / Next.js** (implementation choice)
- **AWS Amplify Hosting** for deployment
- Responsive web application

### Backend
- **Amazon API Gateway** for HTTP API endpoints
- **AWS Lambda** for backend/business logic
- Serverless architecture

### Database
- **Amazon DynamoDB**
- Stores households, material records, collection requests, kabadiwalas, recycler requirements, and status/state transitions

### Image handling
- **Amazon S3** for temporary image uploads
- Images are processed and then deleted because long-term image storage is not required by the product

### Computer vision
- **Amazon Rekognition Custom Labels**
- Custom object-detection model for a small set of common recyclable categories

### Location
- **Amazon Location Service**
- Map display, coordinates, distance/proximity visualization and radius-based opportunity visualization

### Monitoring / debugging
- **Amazon CloudWatch** as the default AWS logging and operational monitoring layer for Lambda/API activity
- No custom monitoring dashboard in the MVP

### Explicitly out of scope for MVP
- Cognito/authentication
- SNS/SES notifications
- SQS/event-driven queues
- EventBridge scheduled jobs unless a real requirement appears
- Fargate/ECS
- Aurora/RDS
- Route optimization engine
- Payments
- Production-grade identity, fraud prevention, or dispute resolution

---

## 3. Application Roles

### Household
Primary actions:
- Add recyclable material manually
- Optionally upload an image for material identification
- Enter quantity/weight
- See estimated recovery value
- Maintain recovery inventory
- Submit collection request
- See nearby kabadiwala options / collection status
- View personal environmental contribution

### Kabadiwala
Primary actions:
- View nearby collection requests on a map
- See material, approximate quantity and estimated value for requests
- Accept / reject requests
- Use a radius-based view to judge where collection opportunities are concentrated
- Track collected material in inventory
- View recycler requirements relevant to their inventory
- Review basic collection/impact metrics

### Recycler
Primary actions:
- Create/update company information
- Specify required recyclable materials and quantities
- View available material aggregated by kabadiwalas
- Contact/booking action for material procurement
- Confirm downstream material transaction/booking

---

## 4. Core Data Model

A **Material Record** is a first-class entity because the material must remain traceable as it moves through the system.

### Material Record
Suggested fields:
- `material_id`
- `material_type`
- `quantity`
- `unit` (kg, count, etc.)
- `estimated_value`
- `source_type` (household / kabadiwala)
- `source_id`
- `current_holder_type`
- `current_holder_id`
- `destination_type`
- `destination_id`
- `status`
- `created_at`
- `updated_at`

### Household
Suggested fields:
- `household_id`
- approximate location
- recovery inventory summary
- active collection requests
- contribution metrics

### Kabadiwala
Suggested fields:
- `kabadiwala_id`
- name/profile
- service localities
- supported material types
- collection capacity
- current inventory summary
- active requests
- basic score/impact metrics

### Collection Request
Suggested fields:
- `request_id`
- `household_id`
- material type(s)
- quantity/weight
- estimated value
- pickup coordinates
- status: `pending / accepted / rejected / collected / cancelled`
- assigned kabadiwala
- timestamps

### Recycler Requirement
Suggested fields:
- `requirement_id`
- `recycler_id`
- material type
- required quantity
- current fulfilled quantity
- status: `open / partially_fulfilled / fulfilled`
- created/updated timestamps

---

## 5. Household Material Input Approach

Manual input is the primary path because it is simple, deterministic, and reliable for the prototype.

The household can select from a controlled material list such as:
- PET/plastic bottles
- cardboard
- paper
- aluminium/metal
- glass
- other/unknown

The user then supplies an approximate quantity or weight.

### Optional computer-vision path

The image feature exists for cases where the household is unsure about an item or wants quick identification.

Flow:

**Camera/upload → S3 temporary object → Rekognition Custom Labels → detected material(s) + confidence → Lambda/business logic → user confirmation → material record**

The image is not the source of truth for quantity. Quantity remains a user-entered/confirmed value in the MVP.

---

## 6. Computer Vision / Image Processing Approach

### Goal

Recognize a small, practical set of common household recyclable materials rather than attempting universal waste recognition.

### Model choice

Use **Amazon Rekognition Custom Labels** for the proof of concept.

The model should be configured for **object detection** where possible, so multiple recognizable objects/materials can be detected in the same image.

Example output:

- PET bottle — 0.92 confidence
- Cardboard — 0.87 confidence
- Aluminium can — 0.90 confidence

### Dataset approach

Use a combination of public waste-image datasets and a small curated dataset suitable for the exact classes being demonstrated.

Potential datasets:
- **TrashNet** for clean/basic waste categories
- **TACO** for more varied “waste in the wild” images

The proof-of-concept should prioritize consistency over breadth.

### Training strategy

Use supervised learning through Rekognition Custom Labels:
1. Define a small set of target classes.
2. Collect/curate labelled images for each class.
3. Include variation in background, lighting, angle and object orientation.
4. Split data into training and testing/validation sets.
5. Train a custom detection model.
6. Evaluate per-class performance and inspect false positives/negatives.
7. Adjust labels/data and retrain if necessary.
8. Deploy the trained model for inference.

### Important UX decision

The model should **assist**, not silently decide.

If confidence is low or multiple materials are detected, the household should be allowed to confirm/correct the result before creating the final material record.

Example:

> Detected: PET bottle (92%)
>
> `[ Confirm ]  [ Change ]`

### Scope limitation

Do not claim that the model can identify every recyclable object. The demo should clearly position it as a **proof-of-concept classifier/detector for selected common categories**.

---

## 7. Temporary Image Storage

S3 is used only as an intermediate object store.

Recommended flow:

1. Frontend uploads image to S3.
2. Backend invokes/requests Rekognition inference.
3. Detection result is written to DynamoDB after user confirmation.
4. Temporary image is deleted after processing.

Possible implementation:
- short-lived object prefix/bucket policy
- lifecycle expiration as a safety mechanism
- explicit deletion from Lambda after inference

No permanent household photo archive is needed.

---

## 8. Estimated Recovery Value

The prototype can calculate an estimated value using a configurable material-rate table.

Example conceptual model:

`estimated_value = confirmed_quantity × configured_rate_per_unit`

Rates should be treated as **illustrative/demo rates** unless connected to a current local price source.

The calculation belongs in backend business logic so that household and kabadiwala views use the same values.

---

## 9. Household Recovery Inventory

When a household confirms a material for recovery:

**User input → validation → material record → inventory update**

Inventory should aggregate by material type rather than creating unnecessary item-level records.

Example:

- PET: 2.4 kg
- Cardboard: 3.1 kg
- Aluminium: 0.6 kg

The household can see:
- recovered quantity
- estimated value
- active collection request
- completed collections
- contribution metrics

---

## 10. Kabadiwala Map / Opportunity Visualization

We intentionally avoid building a full route optimizer.

### What the system does

It displays:
- household pickup-request locations
- material types available
- approximate quantities/value
- request status
- selected Delhi locality

### Locality concept

The map groups opportunities into the frontend's 11 major Delhi regions: North, North West, West, South West, Central, New Delhi, North East, Shahdara, East, South East, and South.

Within a selected locality, the system can calculate/display an aggregate opportunity such as:

> **Lajpat Nagar**
> 12 requests
> 31 kg recyclable material
> ₹420 estimated recovery value

The kabadiwala then decides where and how to travel.

This keeps the project focused on **decision support and collection visibility**, not vehicle routing.

---

## 11. Kabadiwala Decision Logic

The system can filter or rank visible requests using deterministic rules such as:

- in the selected locality
- supported material types
- request quantity/value
- request priority/status
- current collection capacity

This is intentionally not framed as “AI matching.”

Simple rules are sufficient and easier to explain/debug.

---

## 12. Kabadiwala Inventory

Once a collection request becomes `collected`:

**Household material record → kabadiwala inventory update**

The inventory is aggregated by material type and quantity.

Example:

- PET: 42 kg
- cardboard: 68 kg
- aluminium: 17 kg
- paper: 91 kg

This inventory becomes the supply side for recycler visibility.

---

## 13. Recycler Demand Matching

This is intentionally lightweight and downstream.

Recycler enters:
- material type
- required quantity
- optional minimum quantity
- requirement status

System compares requirements against available kabadiwala inventory.

Example:

> PET required: 500 kg
> Network inventory: 327 kg
> Status: partially fulfilled

The MVP can support a booking/contact action rather than a full transactional marketplace.

---

## 14. Environmental Contribution Metrics

Metrics should be derived from actual application records rather than invented impact numbers.

Useful prototype metrics:
- total recyclable material recorded
- total material collected
- material by type
- number of households participating
- number of collection requests fulfilled
- total material transferred to recycler stage

Avoid unsupported claims such as exact trees saved or exact CO₂ avoided unless a documented conversion methodology is incorporated.

---

## 15. API / Backend Responsibilities

Representative API endpoints:

### Household
- `POST /material`
- `GET /household/inventory`
- `POST /collection-request`
- `GET /household/requests`
- `GET /household/contribution`

### Kabadiwala
- `GET /kabadiwala/requests`
- `GET /kabadiwala/map-opportunities`
- `POST /collection-request/{id}/accept`
- `POST /collection-request/{id}/reject`
- `POST /collection-request/{id}/collect`
- `GET /kabadiwala/inventory`
- `GET /kabadiwala/recycler-requirements`

### Recycler
- `POST /recycler/requirements`
- `GET /recycler/available-materials`
- `POST /recycler/booking`
- `GET /recycler/bookings`

### ML
- `POST /classify-image`

Lambda functions can be organized by domain rather than creating a function for every tiny operation.

---

## 16. DynamoDB Design Approach

Prefer a simple design that matches the prototype's access patterns.

Potential tables:

1. `Users` / role profiles
2. `Materials`
3. `CollectionRequests`
4. `RecyclerRequirements`
5. `Bookings`

A single-table DynamoDB design is possible, but a small set of clearly separated tables may be easier for the team to develop and demo quickly.

The final choice should follow actual query patterns rather than theoretical optimization.

Use:
- primary keys for identity
- GSIs where necessary for lookups such as location/status/material
- timestamps and status fields for workflow state

---

## 17. Location Data Approach

Each pickup request needs approximate coordinates.

Amazon Location Service is used for:
- map display
- location lookup/visualization
- proximity calculations where appropriate
- drawing/displaying service-radius regions

For the hackathon, realistic seeded/demo coordinates are acceptable. They should be clearly treated as demonstration data rather than claiming live municipal coverage.

---

## 18. Security / Data Handling

MVP principles:
- minimal personal information
- no permanent image storage
- HTTPS/API authentication at the infrastructure level where required
- S3 objects should not be public
- avoid storing unnecessary household identity/address details
- use environment/configuration variables for secrets

Full production IAM, fraud prevention, audit systems and privacy workflows are outside scope but should be considered for real deployment.

---

## 19. Demonstration Dataset / Seed Data

Because this is a hackathon proof of concept, the app should include seeded data for:
- households
- kabadiwalas
- collection requests
- material inventories
- recycler requirements

The demo can therefore reliably show the complete material flow without requiring real users.

Example:

**Household A** → 4 kg PET + 2 kg cardboard

→ collection request

→ **Kabadiwala Ramesh accepts**

→ inventory increases

→ **Recycler requires PET**

→ booking/transfer demonstrated

→ household contribution updates

---

## 20. AWS Architecture Summary

```text
                    ┌─────────────────────┐
                    │   Amplify Frontend  │
                    └──────────┬──────────┘
                               │
                         HTTPS/API calls
                               │
                    ┌──────────▼──────────┐
                    │   API Gateway       │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │     Lambda          │
                    │ Business Logic      │
                    └─────┬─────────┬─────┘
                          │         │
                ┌─────────▼───┐ ┌─▼─────────────────┐
                │  DynamoDB   │ │ Amazon Location   │
                │ app records │ │ maps / proximity  │
                └─────────────┘ └───────────────────┘

                    Image-assisted workflow

Frontend → S3 (temporary image)
              ↓
     Rekognition Custom Labels
              ↓
          Lambda
              ↓
         User confirms
              ↓
          DynamoDB

CloudWatch provides backend logs/metrics for debugging and operational visibility.
```

---

## 21. Why These Technologies

### Amplify
Fast deployment and hosting for the web application without managing servers.

### API Gateway + Lambda
Fits a small event/request-driven application and keeps backend infrastructure lightweight.

### DynamoDB
Good fit for serverless application state and status-driven records without requiring a relational database for the MVP.

### S3
Standard durable object storage for temporary image uploads and ML processing.

### Rekognition Custom Labels
Provides managed custom computer vision without requiring the team to build/train/host the entire inference stack manually.

### Amazon Location Service
Provides AWS-native mapping and geographic visualization needed for the collection-request map and service-radius concept.

### CloudWatch
Basic logging and monitoring for Lambda/API behavior; not a user-facing product feature.

---

## 22. Implementation Priorities

### Must have
1. Household material entry
2. Collection request creation
3. Kabadiwala request map
4. Accept/reject workflow
5. Kabadiwala inventory
6. Recycler material requirements
7. Recycler booking/connection flow
8. Household contribution dashboard
9. DynamoDB persistence
10. API Gateway + Lambda backend
11. Amplify deployment
12. Amazon Location map

### Strong supporting feature
- Rekognition Custom Labels material detection

### Nice to have
- Radius opportunity aggregation
- More detailed contribution history
- Confidence-based ML confirmation UX

### Do not build unless time remains
- Authentication
- Notifications
- Real-time events
- Full route optimization
- Payment gateway
- Advanced analytics/BI
- Complex marketplace pricing

---

## 23. Technical Principle

The implementation should follow one rule:

> **Use technology only where it materially improves the existing recovery process.**

The project should not become a collection of AWS services for their own sake. Every service must correspond to a clear application requirement.
