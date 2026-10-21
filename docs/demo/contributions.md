# Team contributions

We began with a simple question: why does recyclable material still end up in
ordinary waste when households, local kabadiwalas, and recycling companies
already exist? We focused Phir on the coordination gap between them, shaping
the journey **Household → Collection partner → Recycler**.

## Project lead — [Your name]

- Defined the problem, target users, and focused hackathon scope.
- Chose manual material entry as the main path, with optional photo
  identification that suggests a material for the user to confirm.
- Set privacy-conscious locality mapping, database-backed demo data, and clear
  real-versus-demo labels as product requirements.
- Kept production authentication, payments, and route optimization out of the
  MVP; prioritized a clear, working recovery journey and evidence-based impact.
- Reviewed the interfaces through hands-on testing and guided fixes to
  usability, loading, and data consistency issues.
- Shaped the environmental story and requested specific AWS explanations for
  the demo.

## Team deliverables

The team built the household inventory and collection flow, collection-partner
map and inventory, and recycler marketplace, requirements, and bookings. The
application uses API Gateway, Lambda, DynamoDB, temporary S3 uploads, and
Rekognition Custom Labels, with Amplify Hosting and AWS SAM deployment. Seeded
requests populate Delhi localities for the demonstration.

*Add teammate names and adjust individual engineering attribution to match the
team’s actual task assignments.*
