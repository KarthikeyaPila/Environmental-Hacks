# Product and Technical Decision Questions

Answer directly below each question. If a question does not matter yet, write
`TBD`. If you accept the recommendation, write `Accept recommendation`.

This document is for alignment before further implementation. It should become
the source of truth for the MVP decisions.

## 1. Hackathon and demo goals

1. What is the hackathon name, theme, and judging criteria?
=> you can find everything here: https://www.wemakedevs.org/aws/env
2. What is the exact demo duration?
=> it's given 3 minutes, but it's a little flexible.
3. What is the target date for a demo-ready build?
=> we got 3 days. 
4. Which flow is most important to demonstrate?
   - Household → Kabadiwala
   - Household → Kabadiwala → Recycler
   - All three roles equally
=> household -> kbd -> recyc
5. What should the audience remember in one sentence after the demo?
=> that it was a very well executed project solving a real problem.
6. Are there required AWS services, technical constraints, or judging requirements?
=> we must use AWS, as it's a aws hackathon. and you can find the rest in the link above.
7. Will the demo run with internet access and AWS credentials, or must it work offline/local?
=> I want it to be a website, so with internet access.
8. Do we need a presentation, architecture diagram, README walkthrough, or deployment URL in addition to the application?
=> idts we need all that rn.

## 2. Roles and demo access

9. Should the application use a simple demo role/user switcher instead of authentication?
=> yeah, a temporary user would suffice.
10. Which seeded users should exist? Provide names, roles, and locations if you have preferences.
=> i don't really have any preferences. 
11. Should a role be allowed to view only its own data, or can the demo switch between all users freely?
=> it's own data only, I don't want the household user to be looking at the kabadiwala data lol. 
12. Should users have editable profiles, or are profiles seeded and read-only for the MVP?
=> they don't need to have a good section on profile imo, it's just going to be temporary anyways.
   just for the proof of concept.
13. What profile information is needed?
   - Name
   - Phone/email
   - Approximate location
   - Service radius
   - Supported materials
   - Company details
=> sure all this can be done. but user specific i'd say.

## 3. Material catalog

14. Which material types should the MVP support?
   - PET/plastic bottles
   - Cardboard
   - Paper
   - Aluminium/metal
   - Glass
   - wood as well ig..?
=> that should suffice.
15. Should material names be normalized internally? For example, should `PET`, `plastic bottle`, and `PET bottle` map to one material type?
=> yeah.
16. Should quantities support only kilograms, or kilograms plus item counts?
=> it should be an estimated value, so maybe total weight in kilogram and the material shoud suffice.
17. Can material records contain fractional quantities such as `0.6 kg`?
=> sure.
18. Should one material record represent one input action, or should repeated additions automatically merge into one aggregate record?
=> merge.
19. Can households edit or delete material records after adding them?
=> yes.
20. Can kabadiwalas adjust collected quantities after weighing material?
=> not really necessary. we should not go that deep into this.
21. What should happen when material is classified as `other/unknown`?
=> we can just prompt that you can discard it maybe. 

## 4. Pricing and value

22. Should recovery rates be illustrative demo values or values you provide?
=> yeah, demo values would do, lets just take the average cost of that item. 
23. Please provide the desired rate per kilogram for each supported material, if known.
=> we can take the average.
24. Should rates be editable through configuration, or changed through an admin interface?
=> this feature is not required.
25. Should estimated value be calculated when material is added, when it is collected, or both?
=> when it is added, then we aggregate the regions value, and then provide that to the kabadiwala. 
26. Should household value and kabadiwala revenue use the same rate table?
=> yeah ig. 
27. Should the application clearly label rates and values as estimated/demo values?
=> yes ig.. but it should be such that we don't give off a marketplace vibe.
28. Should value be displayed in Indian rupees (`₹`) with two decimal places or rounded whole rupees?
=>  idk mann, rounded sounds good, as it'll be clear to see.

## 5. Household workflow

29. Can a household create a collection request at any quantity, or is there a minimum threshold?
=> there can be any quantity, it'll be on the kabadiwala to figure out which area he wants to check into.
30. Can one collection request contain multiple material types?
=> yeah.
31. Can a household have multiple active collection requests at once?
=> not really.
32. Should materials become unavailable for new requests once included in an active request?
=> yeah
33. Can a household add more material to an existing pending request?
=> yes, I think if they want to add they can just do that, and it'll directly be added to the region/radius, that they're in.
34. Should households select a specific kabadiwala, or should nearby eligible kabadiwalas see the request?
=> I'd say they should have a choice onto whom they select, lets also give ratings to the kabadiwalas on some metrics like how much he has recycled, how much more does he pay and all other metrics.
35. Can a household cancel a request? If yes, until which state?
=> umm, not required.
36. Should the household see the assigned kabadiwala's name and contact details?
=> sure.
37. What collection statuses should the household see?
   - Pending
   - Accepted
   - Collected

38. Should a request expire if nobody accepts it after a certain period?
=> umm no.
39. Should the household confirm that collection actually happened, or is the kabadiwala's confirmation sufficient for the MVP?
=> I think both of them work. 

## 6. Kabadiwala workflow

40. Can multiple kabadiwalas see the same pending request, with the first acceptance winning it?
=> sure, we can do that.
41. What eligibility rules should determine whether a kabadiwala sees a request?
=>   we can do whatever. it's not really that important.
42. Should the kabadiwala be able to change their service radius?
=> yeah, but I want all the kabadiwalas to have a direct view of where in that city they have the largest
   revenue, and if some other kabadiwala has taken that area or not. I don't want them to be confined to 
   just a single area.
43. Should the radius default to 1 km, 2 km, or another value?
=> the radius of a particular area should be 1km.
44. Should nearby requests be sorted by distance, estimated value, quantity, or a combination?
=> sure.
45. What should the radius summary display?
   - Number of requests
   - Estimated value

46. Should the kabadiwala be able to reject a request with a reason?
=> no, they don't need such a thing, they'll simply just ignore it. and they'll have a area wise  thing
   not a request home specific request.
47. Should a kabadiwala be able to accept multiple requests in one action?
=> they'll have an area that they can choose from.
48. Is route planning explicitly outside scope, with the kabadiwala deciding the travel order manually?
=> yeah, they can just look at the area, and then directly go there to collect.
49. Should collection confirmation require the actual collected quantity to be entered?
=> nah.
50. If the collected quantity differs from the household estimate, which quantity becomes authoritative?
=> the collected quantity.

## 7. Inventory and material traceability

51. Should material records remain individually traceable from household to recycler, or is aggregated inventory sufficient for the demo?
=> aggregated inventory will be sufficient.
52. Should inventory be computed from material records, maintained as aggregate records, or use both?
=> aggregate records would suffice.
53. What material states are required?
   - Available
   - Collected
   - Requested
54. Should a collection request transition exactly as follows?
   ```text
   pending → accepted → collected
   ```
sure we can keep that.
55. Should rejected and cancelled requests be terminal states?
=> sure.
56. Can collected material be returned to a household?
=> no.
57. Can one kabadiwala transfer material to another kabadiwala, or is that out of scope?
=> no, that is out of scope.
58. Should inventory show only quantity, or quantity plus estimated value?
=> quantity plus the estimated value.

## 8. Recycler workflow

59. What recycler profile information should be shown?
=> all the basics like the name of the company, what they make, what materials they recycle, and maybe
   some metrics like how much they've recycled till now and all.
60. Can a recycler create multiple requirements for the same material type?
=> I think one material one request would be enough.
61. Should requirements support a minimum acceptable quantity?
=> sure.
62. Should recycler requirements have these states?

   ```text
   open → partially_fulfilled → fulfilled
   ```
sure.

63. Should a requirement automatically become fulfilled when its requested quantity is reached?
=> sure.
64. Should recyclers see all kabadiwala inventory or only inventory matching their requirements?
=> all the kabadiwalas inventories. 
65. Should available material be grouped by kabadiwala, material type, or both?
=> yeah they can be grouped. multiple kabadiwala inventory to fullfil a recyclers request.
66. Should a recycler initiate a booking, or should a kabadiwala approve it first?
=> initiate the booking first.
67. Should partial bookings be supported?
=> sure.
68. Should booking reserve material immediately?

   Recommended lifecycle:

   ```text
   available → reserved → transferred
   ```
yeah. 

69. When should ownership change from kabadiwala to recycler?
   - At recycler confirmation

70. Can bookings be cancelled? If yes, when?
=> nah, that much depth is not required for now.
71. Should cancelled bookings release reserved material?
=> yeah.
72. Is a contact/booking record enough, or do we need a more complete procurement workflow?
=> that should suffice.

## 9. Metrics and environmental claims

73. Which household metrics should be shown?
   - Total material recorded
   - Quantity by material type
   - Estimated value
   - Downstream destination

74. Which kabadiwala metrics should be shown?
   - Requests accepted
   - Total kilograms collected
   - Estimated revenue
   - Material by type
   
75. Which recycler metrics should be shown?
   - Requirements
   - Fulfilled quantity
   - Available network inventory
   
76. Should all metrics be calculated only from actual stored records?
=> sure.

77. Should we avoid CO₂, trees-saved, landfill-diversion, and similar conversions unless we add a documented methodology?
=> yeah we can avoid them. they're very common nowadays. we can add something much more itneresting.

78. Should the demo include a fixed “before vs after” recovery comparison, or only live system totals?
=> yeah, I think before vs after would be a great addition.

## 10. Location and map behavior

79. Which city or geographic area should seeded data represent?
=> Delhi, as the hackathon is taking place there.
80. Should we use realistic seeded coordinates or a fully mocked map mode?
=> realistic coordinates if possible. but the data of the area wise could be a mocked one.
81. Should exact household addresses be hidden and replaced with approximate coordinates?
=> yeah, we can do that. but again everything is mocked, we don't really need to collect the
   address of anyone as of now.
82. Should Amazon Location be integrated in the first AWS milestone, or should distance calculations remain local initially?
=> yeah we can do that. and no distance calculation is needed wdym..? just the area, the kabadiwala
   can look for himself if he wants to travel there and get whatever.
   when the kabadiwala clicks on an area then he would be able to see what all places he needs to go.

83. Should the map display household request markers, kabadiwala radius, material summaries, and request status?
=> the map should display: whole of delhi/whatever place -> then each area in that place with their
   expected revenue -> then when the kabadiwala clicks on that area -> he'll be exposed to the individual
   coordinates.

## 11. Image and ML feature

84. Should image classification be included in the first demo or remain a secondary feature?
=> we can keep it as a secondary feature for now.
85. Should development use deterministic mock classification before Rekognition integration?
=> which ever works well and is faster to implement.
86. What classes should the mock classifier return?
=> TBD
87. What confidence threshold should require user confirmation?
=> TBD
88. Should the user always confirm or correct the detected material before saving it?
=> yeah, I think that would be correct.
89. Should uploaded images be deleted immediately after classification, with S3 lifecycle expiration as a backup?
=> yeah I think after classification the image would not be required.
90. Do we need real Rekognition Custom Labels training for the hackathon, or only an architecture-ready integration point?
=> TBD.

## 12. API and frontend integration

91. Should the first interface be REST-style JSON endpoints?
=> TBD
92. Should API responses use snake_case or camelCase field names?
=> TBD
93. Should identifiers be UUIDs, readable seeded IDs, or both?
=> TBD
94. Should dates be returned as ISO 8601 UTC strings?
=> TBD
95. Should API errors use a consistent structure such as:

   ```json
   {
     "error": {
       "code": "INVALID_STATE",
       "message": "Request must be accepted before collection"
     }
   }
   ```
=> TBD
96. Should the API include pagination, or can MVP endpoints return complete seeded result sets?
=> TBD
97. Should the API expose derived dashboard summaries directly, or should the frontend calculate them?
=> I think the frontend should calculate that part, else the database cost and all would be higher.
98. Should we write the agreed API contract in a separate `docs/api_contract.md` file?
=> yeah, definiatly, so that my friend will be on the same path as well.
99. What frontend framework and field naming conventions is your friend using?
=> I don't know really, we can check when he pushes into git ig.
100. Will the frontend and backend live in this same repository, with the frontend eventually placed under `frontend/`?
=> I think separate directories would be a good start.

## 13. Persistence and AWS

101. Should the local backend remain usable without AWS credentials?
=> sure. but i'd highly want it to run on aws when we're done as a whole.
102. Should we use separate DynamoDB tables for simplicity?

   Suggested tables:

   ```text
   Profiles
   Materials
   CollectionRequests
   RecyclerRequirements
   Bookings
   ```

=> sure we can do that.

103. Should seeded data be loaded through a script, a Lambda/admin endpoint, or committed as fixtures?
=> a script would be enough. else the cost would be higher everytime we fetch them.
104. Which AWS region should be used?
=> south hyderabad or mumbai.
105. Is there already an AWS account, project, or deployment environment available?
=> yeah, it's all there, we just need to log into that.
106. Should infrastructure be defined with AWS CDK, SAM, CloudFormation, or another tool?
=> I think we did that before by SAM.
107. Should CloudWatch logging be included in the first deployment?
=> nah, not necessary.
108. Do we need separate local, staging, and production environments, or only one hackathon environment?
=> I think local first for our own internal testing, and then move onto the environment.
109. Should authentication remain completely out of scope for the deployed MVP?
=> yeah, that's not at all required.
110. Are there any cost limits or services we must avoid enabling?
=> nope. not for now that is.

## 14. Repository and collaboration

111. Should backend and frontend changes use separate branches?
=> umm sure.
112. What branch should be the shared integration branch: `main`, `develop`, or another branch?
=> main could be the shared one.
113. Should contributors open pull requests, or can trusted collaborators push directly to the shared branch?
=> they can directly push to main. ig. it's just two of us, so it'll be fine.
114. What commit style should we use? Recommended: imperative, focused messages such as `Add collection request state transitions`.
=> anything would work.
115. Should we add a development status document or milestone checklist?
=> oh yeah, that'd help us write the blogs later.
116. Should the repository include example environment configuration such as `.env.example`?
=> sure.
117. Are there files or folders your friend plans to add that we should reserve now?
=> I'm unsure for now.
## 15. Final scope confirmation

118. What must be complete for the project to count as successful?
=> TBD
119. What features are explicitly optional if time runs short?
=> idts time will run out, we've got plenty of it honestly.
120. What features should we absolutely not build, even if time remains?
=> idk, not really required to think of that.
121. Is there anything in the current project documents that you want to change or remove?
=> nah, it seems alright.
122. Is there any important product behavior, stakeholder expectation, or judging concern not covered above?
=> you can have a look at the website yourself. 
   btw the judging critera is like:

   * aws usage - 10 points
   * idea and impact - 8 points
   * execution - 4 points
   * demo video - 4 points
   * design and usability - 4 points.
