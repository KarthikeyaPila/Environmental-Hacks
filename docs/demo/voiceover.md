Firr connects households, collection partners, and recyclers, so recyclable material can move through one visible recovery chain. Let’s follow one item.

A household can add material manually or get a photo-based material suggestion. In the local walkthrough, classification is mocked so the recovery flow can run without AWS. A deployed version can use Rekognition Custom Labels; the user confirms the suggestion and enters the weight.

The confirmed record updates inventory and estimated value.

Now I’ll request collection. It starts pending, then moves to accepted and collected. Contributions show the measured activity.

The household can see its recorded results.

The map turns requests into local opportunities. Selecting a Delhi locality shows requests, material, and value. Locations stay approximate.

Accepting and completing records the handoff and updates inventory.

Inventory shows material by type. Profile and impact show the collection partner’s service area and recovery history.

The recycler sees collected material by partner and type. Booking reserves quantity; confirmation records the downstream handover.

Requirements request a quantity, such as cardboard. They move from open to partially fulfilled or fulfilled. Bookings track reservations, and Company Profile stores the organization details.

A W S Amplify Hosting and Amazon CloudFront deliver the frontend. Amazon A P I Gateway routes to AWS Lambda, while Amazon Dynamo D B stores shared records.

Amazon S three temporarily stores photos, and Amazon Rekognition Custom Labels classifies them. Amazon CloudWatch provides logs, AWS I A M controls access, and AWS CloudFormation through SAM deploys everything.

Amazon Location Service can provide the production locality map while keeping household locations approximate. Each service supports one step in the recovery flow.

Firr makes recovery handoffs visible, actionable, and traceable, so more recyclable material gets a second beginning.
