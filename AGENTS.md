# AGENTS.md — Environmental Hackathon Project

## 0. Status

**Active — planning and backend foundation phase**

The project is currently defining the backend contract and end-to-end workflow
before connecting the frontend. Existing backend code is provisional and should
not be expanded until the architecture and API decisions are agreed together.

## 1. Mission

Build a focused proof-of-concept that improves the flow of recyclable household material into the existing kabadiwala/recovery network.

**Core environmental problem:** recyclable material is lost before it reliably reaches the recovery chain.

**Core intervention:** a digital coordination layer for household recovery requests and kabadiwala collection decisions, with a lightweight downstream recycler view to close the loop.

**Core flow:**

`Household → Recovery Request → Kabadiwala → Collected Material → Recycler`

The project must remain a **focused hackathon POC**, not a production waste-management platform.

---

## 2. Non-Negotiable Product Scope

### Household
- Manual material selection is the primary path.
- Quantity/weight input.
- Optional image-assisted material identification.
- Recovery inventory.
- Estimated recovery value.
- Create collection request.
- View request/collection status.
- View contribution/impact metrics based only on measured system data.
- Show downstream destination/sector where demo data supports it.

### Kabadiwala
- Map of nearby household recovery requests.
- Request details: material, quantity, estimated value/revenue, location, status.
- Accept/reject.
- Configurable collection radius / service area.
- Aggregate opportunity within a radius (e.g. total kg/value).
- Kabadiwala inventory after collection.
- Recycler requirements/demand view.
- Basic collection, revenue and impact dashboard.

### Recycler
- Basic company profile.
- Material requirements + quantities.
- View relevant kabadiwala inventories / available material.
- Booking/confirmation action.

### Core Material Entity
Material is a first-class entity and must remain traceable through the flow:
- type
- quantity
- unit
- estimated value
- source
- current holder
- destination
- status
- timestamps

---

## 3. Explicitly Out of Scope

Do **not** add these unless the user explicitly changes scope:

- Full municipal waste-management system
- New physical collection fleet
- Full marketplace/network-effects product
- Full route optimization / vehicle routing solver
- Payment processing
- Production authentication/identity system
- Social features, leaderboards or heavy gamification
- Carbon calculators or unsupported “trees saved” style metrics
- Notifications/SMS/email
- SQS/event-driven architecture without a concrete need
- Scheduled jobs unless a concrete requirement appears
- Complex recycler procurement workflows
- Fraud/dispute resolution
- Production-scale operations tooling

**Do not add features simply because they sound impressive.**

---

## 4. AWS Architecture

Use a small serverless stack:

- **AWS Amplify Hosting** — frontend deployment
- **Amazon API Gateway** — HTTP API
- **AWS Lambda** — backend/business logic
- **Amazon DynamoDB** — application data
- **Amazon S3** — temporary image uploads
- **Amazon Rekognition Custom Labels** — proof-of-concept waste material detection
- **Amazon Location Service** — map, coordinates, radius/proximity visualization
- **Amazon CloudWatch** — basic logs/diagnostics only

Do not introduce additional AWS services without a real implementation requirement.

Authentication is intentionally omitted for the MVP. Demo users/data can be seeded and role-switched in the application.

---

## 5. ML / Computer Vision Rules

The image model is **supporting functionality**, not the core product.

Use a small controlled set of material classes, initially:
- PET/plastic bottles
- cardboard
- paper
- aluminium/metal
- glass
- other/unknown

Use **Rekognition Custom Labels object detection** where practical.

Training approach:
1. Curate labelled images for the selected classes.
2. Prefer TrashNet/TACO plus curated images suitable for the exact demo classes.
3. Include useful variation in angle, lighting and background.
4. Train/test separately.
5. Inspect false positives/negatives.
6. Retrain only when evidence shows a problem.

Never imply universal waste recognition.

The model assists the user. Low-confidence results must be confirmable/correctable.

For development efficiency, support a **mock/deterministic ML mode** so UI and backend work can proceed without repeatedly invoking or retraining AWS ML resources.

---

## 6. Image Lifecycle

Images are temporary.

Preferred flow:

`Frontend → S3 temporary object → Rekognition → confirmed material result → DynamoDB → delete image`

Use S3 lifecycle expiration as a safety net where appropriate.

Do not build a permanent photo archive.

---

## 7. Location / Map Logic

Use Amazon Location Service only for:
- displaying locations
- calculating basic proximity/distance where needed
- showing a collector's service radius
- summarizing nearby recovery opportunity

Example:

> Within 1 km: 12 requests · 31 kg · ₹184 estimated value

**Do not implement full route optimization.**
The kabadiwala decides which requests to visit and how to travel.

---

## 8. Data / Backend Principles

Prefer simple REST-style endpoints and straightforward Lambda functions.

Keep business logic server-side when it affects shared state or calculations:
- estimated value
- request state transitions
- inventory updates
- recycler-demand matching/filtering
- contribution totals
- radius aggregation

Use DynamoDB consistently rather than introducing a relational database unless the existing implementation proves it necessary.

Keep state transitions explicit, e.g.:

`pending → accepted → collected`

and for recycler demand:

`open → partially_fulfilled → fulfilled`

Prevent impossible duplicate transitions.

---

## 9. Development Strategy — Optimize Codex / Free-Plan Usage

The agent should optimize for **few, high-value tool calls** and avoid wasting model/tool usage.

### Before changing code
- Inspect the repository structure once.
- Read relevant files in batches.
- Prefer targeted searches over repeatedly reading entire directories.
- Reuse information already established in the conversation/repository.
- Do not repeatedly rediscover the same architecture.

### During implementation
- Make the smallest coherent change.
- Batch related edits into one implementation pass.
- Avoid speculative abstractions.
- Avoid adding dependencies unless clearly necessary.
- Prefer existing project libraries/components.
- Prefer deterministic seeded demo data over building admin tooling.
- Build the main happy path first.
- Integrate AWS after the local/data flow is stable rather than repeatedly switching between mock and cloud implementations.

### Validation
- Run focused tests/type checks/linting after meaningful milestones.
- Do not run expensive full builds repeatedly after every tiny edit.
- When a failure occurs, diagnose and fix the root cause instead of repeatedly rerunning the same command.
- Before finishing a milestone, run the smallest meaningful verification suite plus one production-like build if appropriate.

### Communication
- Do not ask for confirmation for routine implementation decisions that are already covered by this document.
- Ask only when a decision would materially change scope, architecture, security, cost, or product behavior.

---

## 10. UI / UX Principles

The UI should support the environmental story rather than become the product.

Priorities:
1. Clear household → kabadiwala → recycler flow.
2. Fast material entry.
3. Clear quantity/value information.
4. Clear collection-request status.
5. Kabadiwala map that immediately shows material + quantity/value.
6. Recycler demand that is understandable at a glance.
7. Contribution/impact that uses real system totals.

Avoid:
- decorative dashboards with no functional purpose
- excessive cards/charts
- gimmicky animations
- unnecessary onboarding
- fake “AI” interactions

---

## 11. Demo / Story Constraints

The demo should begin with the environmental problem, not the technology.

Preferred narrative:

1. Physical pile of recyclable material at a trash dump.
2. Ask why recoverable material ended up there.
3. Explain where the existing recovery chain breaks.
4. Household: record material and create recovery request.
5. Kabadiwala: see and decide among nearby opportunities.
6. Recycler: see aggregated material and demand.
7. Show measured prototype impact.
8. Explain AWS architecture naturally alongside the product flow.
9. Return to the original waste pile and close with the environmental outcome.

Do not claim prototype metrics are real-world deployment results.

---

## 12. Code Quality

- Keep functions/modules small and cohesive.
- Use clear names instead of clever abstractions.
- Validate API inputs.
- Handle loading, empty and error states.
- Keep environment/configuration separate from source code.
- Never commit credentials, API keys, secret files or `.env` values containing secrets.
- Use environment variables for deploy-time configuration.
- Keep sample/demo data obviously distinguishable from real data.
- Preserve accessibility and responsive behavior for the main flows.

---

## 13. Git Discipline

Use Git continuously, but **do not create noisy commit history**.

### Commit rules
- Commit only after a coherent, working milestone.
- Use conventional-style messages, e.g.:
  - `feat: add household recovery requests`
  - `feat: add kabadiwala request map`
  - `feat: add recycler demand view`
  - `fix: prevent duplicate collection acceptance`
  - `refactor: simplify material inventory state`
  - `docs: add deployment instructions`
- Keep commits small enough to review, but large enough to represent a real change.
- Do not make meaningless commits such as `update`, `changes`, `stuff`, `wip` unless explicitly required.

### Before committing
Run the relevant focused checks and verify that generated files/secrets are excluded.

### Push policy
- If a Git remote is configured and the user expects repository progress to be pushed, push **stable milestones**, not every edit.
- Never force-push.
- Never rewrite shared history unless explicitly requested.
- If authentication/push is unavailable, report it clearly rather than pretending the push happened.

### Recommended milestone commits
1. `chore: scaffold application`
2. `feat: implement household material flow`
3. `feat: implement kabadiwala collection workflow`
4. `feat: implement recycler demand flow`
5. `feat: integrate location map`
6. `feat: integrate material recognition`
7. `feat: add impact dashboard`
8. `chore: harden demo flow and documentation`

Merge/reorder these as needed; do not force eight commits if fewer coherent milestones are more appropriate.

---

## 14. Definition of Done — MVP

The MVP is complete when a seeded/demo household can:

`Add recyclable material → create recovery request → kabadiwala sees it on map → accepts → collection completes → kabadiwala inventory increases → recycler can see matching material/demand → household contribution updates`

And the optional image path can demonstrate:

`Image → Rekognition Custom Labels → material suggestion → user confirmation → material record`

The application must be deployable through the intended Amplify/AWS setup and must have no secrets committed to Git.

---

## 15. Priority Order

When time is limited, implement in this order:

**P0 — absolutely required**
- Household material entry
- Recovery request
- Kabadiwala request list/map
- Accept/reject
- Collection completion
- Inventory updates

**P1 — important**
- Recycler requirements
- Kabadiwala ↔ recycler material visibility
- Household contribution dashboard
- Radius aggregation

**P2 — only after the core flow works**
- Rekognition Custom Labels integration
- Image-assisted material input
- UI polish
- Extra analytics

If time becomes tight, **cut ML before cutting the core recovery workflow.**

---

## 16. Final Engineering Principle

When deciding whether to add something, ask:

> **Does this materially improve the recovery of household recyclable material through the existing kabadiwala system?**

If the answer is no, it probably does not belong in the hackathon MVP.
