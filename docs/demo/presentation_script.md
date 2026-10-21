# Phir demo dialogue

Continuation script for `assets/demo/Phir_Hackathon_Vox_V9.mp4` (kept locally; excluded from Git because of its size).

The current video is 62 seconds long and ends on the Phir landing page with the
three role cards visible. This continuation is paced for roughly two minutes at
a natural speaking speed. **Action** is what to show; quoted text is what to
say. The lines are intentionally short so the demo actions have room to breathe.

## 0:00–0:10 — Landing page

**Action:** Hold on the landing page and move across the three role cards.

**Dialogue:**

> Phir connects households, collection partners, and recyclers, so recyclable
> material can move through one visible recovery chain. Let’s follow one item.

## 0:10–0:38 — Household

**Action:** Open Household, click **Add material**, show manual entry and photo
identification, then choose the photo path and upload the prepared image.

**Dialogue:**

> A household can add material manually or get a photo-based material
> suggestion. In this local walkthrough, classification is mocked so the
> recovery flow can run without AWS. A deployed version can use Rekognition
> Custom Labels; the user confirms the suggestion and enters the weight.

**Action:** Confirm the suggestion, enter the weight, and show **Your materials**.

> The confirmed record updates inventory and estimated value.

**Action:** Click **Request collection** and show the collection panel.

> Now I’ll request collection. It starts pending, then moves to accepted and
> collected. Contributions show the measured activity.

**Action:** Open **Contributions** briefly, then return to the role switcher.

> The household can see its recorded results.

## 0:38–1:08 — Collection partner

**Action:** Switch to **Collection partner**. Show **Collection map**, hover over
a locality, select one with requests, and show the request list.

**Dialogue:**

> The map turns requests into local opportunities. Selecting a Delhi locality
> shows requests, material, and value. Locations stay approximate.

**Action:** Open the request, click **Accept**, then **Mark collected**. Switch to
**Inventory**.

> Accepting and completing records the handoff and updates inventory.

**Action:** Show **Inventory**, then **Profile & impact**, pausing on the ID card.

> Inventory shows material by type. Profile and impact show service area and
> recovery history.

## 1:08–1:32 — Recycler

**Action:** Switch to **Recycler**, show **Material marketplace**, hover over the
material cards, open one booking, and confirm it.

**Dialogue:**

> The recycler sees collected material by partner and type. Booking reserves
> quantity; confirmation records the downstream handover.

**Action:** Open **Requirements**, create or show one requirement, then briefly
show **Bookings** and **Company profile**.

> Requirements request a quantity, such as cardboard. They move from open to
> partially fulfilled or fulfilled. Bookings track reservations; Company profile
> stores organization details.

## 1:32–1:57 — AWS implementation

**Action:** Show an architecture slide, or point to the relevant screen while
the corresponding product action remains visible.

**Dialogue:**

> **AWS Amplify Hosting** and **Amazon CloudFront** deliver the frontend.
> **Amazon API Gateway** routes to **AWS Lambda**, while **Amazon DynamoDB**
> stores shared records.

> **Amazon S3** temporarily stores photos, and **Amazon Rekognition Custom
> Labels** classifies them. **Amazon CloudWatch** provides logs, **AWS IAM**
> controls access, and **AWS CloudFormation through SAM** deploys everything.

> **Amazon Location Service** can provide the production locality map while
> keeping household locations approximate. Each service supports one step in
> the recovery flow.

## 1:57–2:00 — Close

**Action:** Return to the three-role landing page or show the connected flow:
household → collection partner → recycler.

**Dialogue:**

> Phir makes recovery handoffs visible, actionable, and traceable—so more
> recyclable material gets a second beginning.

## Recording notes

- Keep the photo ready before recording so the upload and classifier result do
  not consume the demo time.
- Use one prepared household and collection-partner profile. Create the request
  immediately before switching roles, or prepare it in advance.
- Pause briefly on **pending**, **accepted**, and **collected** so the transition
  is visible.
- Say “estimated value” and “prototype” whenever discussing money or impact.
- Amazon Location Service is described as the production map extension here;
  do not say it currently powers the illustrative Delhi map unless enabled.
