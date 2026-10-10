# Supporting Evidence — Environmental Waste Recovery Project

> **Purpose:** Evidence bank for the project. This document collects recent, reusable statistics, research findings, policy references, and quantitative framing that support the problem we are addressing: **improving recovery of recyclable household material by connecting it more effectively to the existing kabadiwala/informal recovery network and downstream recycling chain.**
>
> This is an evidence document, not the project specification. The implementation/technology plan will live separately.

---

## 1. Executive evidence snapshot

### India generates an enormous volume of municipal solid waste

- In **2023–24**, India generated **185,195 tonnes/day (TPD)** of municipal solid waste; **179,479 TPD** was collected, **114,110 TPD** was processed, and **39,629 TPD** was landfilled. These figures are based on CPCB data cited in the Government of India's parliamentary material and summarized by PRS. [R1]
- A separate, more recent **2024–25 urban India** Swachh Bharat Mission MIS figure reports **161,157 TPD generated** and **129,708 TPD processed**. This is an urban-SBM portal figure and should **not** be mixed directly with the 2023–24 all-country CPCB series because the reporting bases differ. [R2]

### A substantial fraction of municipal waste is dry material with recovery potential

- In a CPCB assessment covering **20 Indian cities**, **dry waste averaged 33.36%** of municipal solid waste, with a range of **20%–47%**. [R3]
- In that same assessment, the average composition of total municipal solid waste was approximately **12.20% plastic, 9.59% paper, 2.56% glass, and 1.06% metals**. Together, those four categories represent about **25.4% of total MSW by weight** in the sampled cities. [R3]
- This is a **selected-city composition study, not a national composition factor**. It is useful for demonstrating the scale of the addressable material stream, but should not be presented as the exact composition of all Indian MSW.

### Household-level segregation is still a real bottleneck

- A **2026** household waste study in Ujjain found average household waste generation of **651.4 g/day**, including **237 g/day of dry waste**. [R4]
- In that study, **48.1% of material placed in the dry-waste section was mis-sorted**; the largest mis-sorted component was organic waste. [R4]
- The same study found that explicitly identified recyclable fractions including plastics, paper, metals, and glass made up roughly **13.1% of total household waste by weight** in that sample. [R4]

### The informal recycling network is already large and environmentally important

- A **2025 India case study from the International Alliance of Waste Pickers / GRID-Arendal** estimates around **4 million people** in India's informal waste recycling sector, including waste pickers, local **kabadiwalas**, larger aggregators/junkyard owners, dealers, and other intermediaries. [R5]
- The same source cites an estimate that waste pickers in Indian cities collect around **15–20% of municipal solid waste**, and notes their role in recovering paper, plastic, metals, and other recyclable materials. [R5]
- An Indian mass-flow analysis found that households and informal-sector actors collectively recover very large quantities of recyclable material; the study estimated annual recovery of **1.2–2.4 Mt of newspapers, 2.4–4.3 Mt of cardboard/mixed paper, 6.5–8.5 Mt of plastic, >1.3 Mt of glass, and >2.6 Mt of metal**, among other recyclable materials. [R6]
- The same study describes the established household-to-kabadiwala/raddiwala pathway: households sell recyclable paper, carton, plastic, glass and metal; doorstep itinerant buyers purchase sorted material; specialized kabadiwalas aggregate it further before sale to recycling plants. [R6]

### Better segregation can materially improve environmental outcomes

- A **2026 randomized controlled trial in India** found that when a reliable segregated collection service already existed, a low-cost household campaign increased waste segregation rates by **45 percentage points**, and adding weekly reminders increased them by **60 percentage points**. [R7]
- A field experiment in Delhi found that **information and economic incentives** can increase household waste segregation, with monetary incentives having a particularly strong effect. It also found that the behaviour of downstream garbage collectors can undermine household segregation. [R8]

### India's policy direction is strongly aligned with source segregation and digital tracking

- India's **Solid Waste Management Rules, 2026**, effective from **1 April 2026**, mandate four-stream source segregation: **wet waste, dry waste, sanitary waste, and special-care waste**. [R9]
- The 2026 rules also provide for **online tracking and monitoring of collection, transportation, processing and disposal** through a centralized online portal. [R10]
- This creates a strong policy context for software that improves the collection and recovery of dry recyclable material rather than treating recycling as a purely awareness-driven problem.

---

## 2. Scale of India's municipal waste problem

### Latest all-country CPCB-based baseline

| Indicator | 2023–24 |
|---|---:|
| MSW generated | **185,195 TPD** |
| MSW collected | **179,479 TPD** |
| MSW processed | **114,110 TPD** |
| MSW landfilled | **39,629 TPD** |

Source: CPCB data as reported in parliamentary material and summarized by PRS. [R1]

Approximate ratios from these figures:

- Collected / generated: **~97.0%**
- Processed / generated: **~61.6%**
- Landfilled / generated: **~21.4%**

**Important:** these categories should not automatically be treated as a perfect mass balance of all generated waste; reporting definitions and accounting of treated, disposed, legacy, and other streams can differ.

### More recent urban SBM figure

For **2024–25**, the Swachh Bharat Mission-Urban MIS reported:

- **161,157 TPD generated**
- **129,708 TPD processed**
- **~80% processed**

This figure covers **urban India under the SBM-U reporting system**, so it is best used as a current urban-system indicator rather than as a direct replacement for the CPCB 2023–24 national series. [R2]

---

## 3. How much recyclable material is in the waste stream?

### CPCB 20-city composition study

CPCB's 2024 Standard Operating Procedure / inventory assessment covered 20 pilot cities and found:[R3]

| Material / fraction | Average share of total MSW |
|---|---:|
| Wet waste | 66.76% |
| Dry waste | **33.36%** |
| Plastic | **12.20%** |
| Paper | **9.59%** |
| Glass | **2.56%** |
| Metals | **1.06%** |

The four explicitly recyclable categories above sum to approximately **25.4% of total MSW** in this selected-city sample.

The study reported a dry-waste range of **20%–47%** across the sampled cities. Plastic alone ranged from **8%–17%** of total MSW in the sampled cities.[R3]

### Why this matters for our project

Our project does not need to claim that all MSW is recyclable. The evidence supports a more precise statement:

> **A substantial, measurable dry-material fraction of municipal waste consists of materials such as plastic, paper, glass, and metals that can enter recovery/recycling pathways when appropriately segregated and collected.** [R3]

---

## 4. Household-level evidence

### Recent Ujjain household study — 2026

A 2026 peer-reviewed study analysed household waste in Ujjain, Madhya Pradesh, using seven consecutive days of door-to-door collection and physical sorting across 23 waste fractions.[R4]

Key results:

- Average household waste generation: **651.4 g/household/day**
- Average dry waste generation: **237 g/household/day**
- Average per-capita generation: **141 g/person/day**
- **48.1%** of material placed in the dry-waste section was mis-sorted.[R4]

The same study measured the following overall household waste fractions:[R4]

- Plastic packaging: **3.05%**
- Other plastics: **2.88%**
- PET bottles: **0.36%**
- Paper packaging: **2.50%**
- Newspaper/newsprint: **0.87%**
- Other paper: **2.29%**
- Paper cardboard: **0.37%**
- Metal packaging: **0.05%**
- Aluminium cans: **0.01%**
- Other metals: **0.27%**
- Glass packaging: **0.36%**
- Other glass: **0.05%**

Combined, these explicitly identified plastic + paper + metal + glass fractions account for approximately **13.1% of total household waste** in this sample.[R4]

### Interpretation

This study gives us a concrete way to explain why household recovery matters:

> **The household waste stream contains a measurable recyclable fraction, while segregation mistakes remain common enough to make recovery harder.** [R4]

Do **not** generalize the exact Ujjain percentages to every Indian city.

---

## 5. The role of kabadiwalas / informal recovery workers

### Scale and environmental role

The 2025 India case study by GRID-Arendal and the International Alliance of Waste Pickers estimates around **4 million people** in India's informal waste recycling sector, including waste pickers and kabadiwalas, and cites estimates that waste pickers collect about **15–20% of municipal solid waste in Indian cities**.[R5]

The case study also notes that waste pickers recover paper, plastic, metals and other materials from households, streets and disposal points, and highlights their importance to India's resource-recovery system.[R5]

### Existing household recovery pathway

A large-scale material-flow study of India describes the established recycling chain as involving:

**Household → doorstep buyer / raddiwala → kabadiwala / aggregator → recycling plant**.[R6]

It reports substantial annual recovery volumes of newspapers, cardboard/mixed paper, plastics, glass and metals through the combined activity of households and informal actors.[R6]

### Why this supports our design

This is the central design premise:

> **We do not need to invent the physical recovery network. The collectors, aggregators and downstream recyclers already exist. The opportunity is to improve the digital coordination layer that helps recyclable household material enter that network.** [R5][R6]

---

## 6. Evidence that household behaviour can change

### 2026 randomized controlled trial in India

A 2026 field experiment examined household segregation **in the presence of a reliable segregated collection service**.[R7]

Results:

- Information + bucket intervention: **+45 percentage points** in segregation rate
- Same intervention + weekly reminders: **+60 percentage points**

The finding is particularly useful for our project because it shows that:

> **Household behaviour is responsive to low-cost interventions when a reliable downstream collection service exists.** [R7]

That supports a system design in which the household interface is tightly coupled to an actual collection pathway rather than being just an awareness/education app.

### Delhi field experiment

A Delhi field experiment found that:

- information on segregation and its benefits can influence behaviour;
- **economic incentives** play an important role;
- and collector behaviour can undermine correct household segregation.[R8]

This provides evidence for two concepts we considered earlier:

1. **Immediate economic value can be a useful behavioural incentive.**
2. **The collector is part of the intervention, not merely a downstream actor.**

We should present these as evidence-backed design hypotheses, not as guarantees that our exact UI will change behaviour.

---

## 7. Environmental value of recovering/recycling material

### Plastic recycling

An India-focused life-cycle assessment comparing plastic end-of-life pathways found that **recycling had the lowest environmental impact among the major scenarios studied for PET/PE**, while open burning was a major contributor to climate-change impact and landfill disposal was a major contributor to marine ecotoxicity in the model.[R11]

The study also identified **plastic collection rate**, open burning of uncollected plastic, recycling rejects and replacement of virgin plastic with recycled material as important sensitivity parameters.[R11]

### Recycling and virgin-material displacement

A broader environmental assessment explains the central mechanism behind recycling benefits: manufacturing from recycled inputs can reduce the need to extract and process virgin materials, which can reduce energy use and environmental burdens.[R12]

### Recent India paper-recycling case study

A 2026 Indian case study of a closed-loop waste-paper recycling system reported an **85% reduction in greenhouse-gas emissions versus conventional landfilling** for that specific system, driven largely by material recovery and avoided virgin paper production.[R13]

**Important:** the 85% figure is a case-specific LCA result and should not be turned into a universal “recycling saves 85% emissions” claim.

---

## 8. Plastic waste — a high-value supporting substory

India's reported plastic-waste generation based on SPCB/PCC data was:[R14]

| Financial year | Plastic waste generated |
|---|---:|
| 2018–19 | 3,360,043 TPA |
| 2019–20 | 3,469,782 TPA |
| 2020–21 | 4,126,808 TPA |
| 2021–22 | 3,901,802 TPA |
| 2022–23 | **4,136,189 TPA** |

CPCB's 2022–23 annual report separately recorded **3.90 million tonnes/year** estimated plastic-waste generation for 2021–22 and documented substantial national recycling/co-processing capacity.[R15]

These figures show why a system that improves collection and recovery of high-volume dry materials, particularly plastics, can have significant environmental relevance.

---

## 9. Current policy context — Solid Waste Management Rules, 2026

India's regulatory environment has moved further toward source segregation and digital monitoring.

The **Solid Waste Management Rules, 2026**:

- came into force on **1 April 2026**;
- replaced the 2016 rules;
- mandate segregation at source into **four streams: wet, dry, sanitary, and special-care waste**; and
- emphasize circular economy and Extended Producer Responsibility.[R9]

The Government has also stated that the 2026 rules provide for **online tracking and monitoring of all stages of solid-waste management**, including collection, transportation, processing and disposal.[R10]

### Relevance to our project

This gives us a strong policy-alignment statement:

> **Our project supports the same direction now being formalized nationally: better source segregation, better collection of dry recyclables, circular material flows, and digital visibility across the waste-management chain.** [R9][R10]

---

## 10. Quantifying our project's potential impact

### Do not claim a national percentage without deployment data

We cannot honestly say:

> “Our system will solve X% of India's waste problem.”

That depends on adoption, collector participation, material acceptance, capture rates, repeat usage, city conditions and actual downstream recycling.

Instead, quantify impact at the **network / pilot level**.

### Recommended project KPI

The cleanest environmental KPI is:

> **Kilograms of recyclable material successfully recovered through the network.**

Supporting KPIs:

- households participating
- collection requests fulfilled
- kilograms recovered by material type
- share of requests successfully collected
- average time from household request → collection
- collector utilization / capacity
- kilograms delivered to downstream recyclers
- material successfully handed off to a verified recycling destination

### Simple impact model

Use:

```text
Recovered material (kg)
=
Households served
×
Recoverable material available per household
×
Capture rate
×
Collection success rate
```

For a pilot, the model can be populated with **your actual prototype data** instead of making national claims.

### Illustrative example only

Using the Ujjain study's **237 g dry waste / household / day** as a reference point,[R4] a hypothetical network of 1,000 households would generate about:

```text
237 kg/day of dry waste
```

If a subset of that dry stream is recoverable and the system successfully captures a measured portion, the resulting kilograms recovered can become the primary environmental metric for the demo.

**This example is illustrative, not a forecast.**

---

## 11. Strong evidence-backed statements we can reuse

### Problem

> **India generated about 185,000 tonnes of municipal solid waste per day in 2023–24, and only about 62% of the reported generated quantity was processed.** [R1]

> **CPCB's 20-city assessment found that dry waste averaged about one-third of municipal solid waste, with paper, plastic, glass and metals forming substantial fractions.** [R3]

> **A 2026 household study in Ujjain found that nearly half of the material placed in the dry-waste section was mis-sorted.** [R4]

### Why kabadiwalas matter

> **India already has a large informal recovery sector, including kabadiwalas and waste pickers, that plays a major role in collecting and recovering recyclable materials.** [R5][R6]

> **Existing research describes a household → doorstep buyer/kabadiwala → aggregator → recycling-plant pathway for recyclable materials.** [R6]

### Why intervention can work

> **A 2026 randomized controlled trial in India found large increases in household segregation when information and reminders were paired with reliable segregated collection.** [R7]

> **Indian field evidence also shows that information and economic incentives can improve household segregation behaviour.** [R8]

### Environmental impact

> **Life-cycle research indicates that recycling can reduce environmental impacts by replacing virgin material production, while unmanaged disposal and open burning can carry significant environmental burdens.** [R11][R12]

### Policy alignment

> **India's 2026 Solid Waste Management Rules mandate source segregation into wet, dry, sanitary and special-care streams and support digital tracking across the waste-management chain.** [R9][R10]

---

## 12. Claims we should NOT make without stronger evidence

These are intentionally excluded from the project's evidence claims:

- “India sends X% of all recyclable waste to landfills.”
- “Our system will recover X% of India's waste.”
- “One household saves X trees / X kg CO₂” without a transparent, defensible conversion methodology.
- “Kabadiwalas handle the majority of all Indian waste” — the available evidence is sector- and material-specific; use the more precise estimates.
- “Everyone knows what is recyclable, therefore education is unnecessary.”
- “Scanning every waste item will definitely change behaviour.”
- “All plastic/paper/glass/metal is recyclable.”
- “A recycler will definitely buy any material a household collects.”

---

# References

### [R1] PRS India — Demand for Grants 2026–27: Environment, Forests and Climate Change

**Use for:** 2023–24 national MSW generation, collection, processing and landfilling figures; recent policy context.

https://prsindia.org/budgets/parliament/demand-for-grants-2026-27-analysis-environment-forests-and-climate-change

---

### [R2] Press Information Bureau — Swachh Bharat Mission Urban waste-management status

**Use for:** 2024–25 urban India waste generated and processed figures.

https://www.pib.gov.in/PressReleasePage.aspx?PRID=2118321

---

### [R3] Central Pollution Control Board — Standard Operating Procedure / Plastic Waste Assessment, 2024

**Use for:** 20-city MSW composition; dry waste range; paper, plastic, glass and metal shares.

https://cpcb.nic.in/uploads/plasticwaste/SOP_PWM_24062024.pdf

---

### [R4] Kalyanasundaram et al. — *Quantitative assessment of household waste composition and segregation pattern in urban settings of Ujjain, Madhya Pradesh: a pick analysis/waste composition analysis study*, Frontiers in Sustainability, published 15 January 2026

**Use for:** household waste generation, dry-waste quantity, mis-sorting, detailed household material fractions.

https://www.frontiersin.org/journals/sustainability/articles/10.3389/frsus.2025.1707300/full

DOI: https://doi.org/10.3389/frsus.2025.1707300

---

### [R5] GRID-Arendal / International Alliance of Waste Pickers — *Organising and Integrating the Informal Recycling Sector in the Solid Waste Management Sector: India*, 2025

**Use for:** scale of the informal recycling sector; 4 million people; 15–20% municipal-solid-waste collection estimate; role of waste pickers and kabadiwalas.

https://wastepickersinternational.org/document/organising-and-integrating-the-informal-recycling-sector-in-the-solid-waste-management-sector-india/

---

### [R6] *Recovery of consumer waste in India – A mass flow analysis for paper, plastic and glass and the contribution of households and the informal sector*

**Use for:** material-recovery volumes and the established household → raddiwala/kabadiwala → recycler chain.

https://www.sciencedirect.com/science/article/pii/S0921344915300082

---

### [R7] Wadehra, Nie & Alpízar — *Increasing Household Waste Segregation Rates in the Presence of a Segregated Collection Service: A Randomized Controlled Trial in India*, Journal of the Association of Environmental and Resource Economists, 2026

**Use for:** +45 percentage points from information/bucket intervention; +60 percentage points with weekly reminders when reliable segregated collection exists.

https://www.journals.uchicago.edu/doi/10.1086/742220

DOI: https://doi.org/10.1086/742220

---

### [R8] *Encouraging urban households to segregate the waste they generate: Insights from a field experiment in Delhi, India*

**Use for:** household behaviour; information; economic incentives; collector behaviour.

https://www.sciencedirect.com/science/article/pii/S0921344918301150

---

### [R9] Ministry of Environment, Forest and Climate Change — Solid Waste Management Rules, 2026

**Use for:** four-stream source segregation; commencement from 1 April 2026; circular-economy/EPR direction.

https://moef.gov.in/uploads/pdf-uploads/pdf_69a16e3b04c107.91022257.pdf

---

### [R10] Press Information Bureau — *New Solid Waste Management Rules Notified; To Come into Force from April 1, 2026*, 28 January 2026

**Use for:** policy explanation and online tracking/monitoring of the waste-management process.

https://www.pib.gov.in/PressReleseDetailm.aspx?PRID=2219676

---

### [R11] *Life cycle assessment of plastic waste end-of-life for India and Indonesia*

**Use for:** comparison of plastic end-of-life pathways; environmental impacts of recycling vs disposal/open burning; importance of collection rate and virgin-material replacement.

https://www.sciencedirect.com/science/article/abs/pii/S0921344921003839

---

### [R12] U.S. EPA — *Frequent Questions on Recycling*

**Use for:** general mechanism by which recycling reduces virgin-material extraction/processing and associated energy demand.

https://www.epa.gov/recycle/frequent-questions-recycling

---

### [R13] *A case study of integrated life cycle assessment & socio-economic impact of university-supported waste paper recycling initiative*, Discover Sustainability, 2026

**Use for:** India case study reporting 85% GHG reduction versus conventional landfilling in a specific closed-loop paper-recycling system.

https://link.springer.com/article/10.1007/s43621-026-02734-8

---

### [R14] Press Information Bureau — *Parliament Question: Plastic waste in the country*, 12 December 2024

**Use for:** official plastic-waste generation series through 2022–23.

https://www.pib.gov.in/PressReleasePage.aspx?PRID=2083801

---

### [R15] Central Pollution Control Board — Annual Report 2022–23, Plastic Waste Management section

**Use for:** plastic-waste generation and recycling-capacity data for 2021–22.

https://cpcb.nic.in/openpdffile.php?id=UmVwb3J0RmlsZXMvMTY2OV8xNzI3NDE0NTc1X21lZGlhcGhvdG8yOTAyNy5wZGY=

---

## Evidence hierarchy for the project

When making claims in the final presentation, prefer sources in this order:

1. **Government of India / CPCB / MoEFCC / PIB**
2. **Peer-reviewed recent Indian studies**
3. **Established research institutions / international sector organizations**
4. Older foundational studies only when they provide structural or historical context that newer sources do not replace.

For the actual demo, the strongest numbers to keep visible are:

> **185,195 TPD** — India's reported MSW generation in 2023–24 [R1]
>
> **33.36%** — average dry-waste share across the CPCB 20-city sample [R3]
>
> **48.1%** — mis-sorted share within the dry-waste section in the 2026 Ujjain household study [R4]
>
> **~4 million** — estimated people in India's informal waste-recycling sector [R5]
>
> **45–60 percentage points** — improvement in household segregation observed in a 2026 Indian RCT when a reliable segregated collection service existed [R7]
>
> **1 April 2026** — effective date of India's new Solid Waste Management Rules requiring four-way source segregation [R9]

These figures create a coherent evidence chain:

**large waste stream → large dry/recoverable fraction → household sorting/recovery gap → existing informal recovery workforce → behaviour improves when collection works → national policy now explicitly requires source segregation and digital monitoring.**
