# Environmental Hackathon Project — Current Plan

## Working Concept

We are building a **digital recovery layer for recyclable household waste**, centered around the existing kabadiwala network.

The goal is **not** to build a new waste-management or recycling system. The goal is to improve one specific part of the existing system: **getting recyclable material from households into kabadiwala collection workflows efficiently and reliably**.

### Core statement

> **Recoverable household material is often lost before it reaches the recovery chain. We use a digital collection-coordination layer to turn scattered household recyclable material into actionable pickup opportunities for existing kabadiwalas, then carry the material into the downstream recycling chain.**

### Core flow

**Household → Kabadiwala → Recycler**

The system helps each participant see, manage, and act on the recyclable material available to them.

---

# 1. Problem

A significant amount of household waste that could potentially be recovered is mixed into ordinary waste and leaves the recovery chain.

The physical infrastructure for recovering many recyclable materials already exists through **kabadiwalas and other local collectors**. Recycling companies also need specific recyclable materials.

The specific digital gap we are targeting is the handoff between:

- recyclable material available at households, and
- kabadiwalas who can collect and aggregate it.

The recycler connection remains important for closing the loop, but it is intentionally downstream and lighter-weight.

The project focuses on making collection opportunities more visible, organized, and actionable for the existing recovery network.

---

# 2. What We Are Building

A multi-role application with three main participants:

1. **Households / Customers**
2. **Kabadiwalas / Recovery Collectors**
3. **Recycling Companies / Material Buyers**

The system keeps recyclable material as a trackable entity as it moves through the network.

### High-level lifecycle

```text
Household identifies recyclable material
            ↓
Material is recorded with type + quantity
            ↓
Household creates / accumulates a recovery request
            ↓
Kabadiwala sees nearby available material
            ↓
Kabadiwala accepts and collects it
            ↓
Kabadiwala inventory is updated
            ↓
Recycling company sees available material matching its requirements
            ↓
Recycler books / confirms acquisition
            ↓
Material continues into the recycling chain
```

---

# 3. Household / Customer

## Purpose

Help a household identify, record, accumulate, and hand over recyclable material instead of losing it in the normal waste stream.

## Planned functionality

### Material input

- Manual material selection
- Quantity / weight input
- Optional image input / computer-vision assistance for items the user is unsure about

The image feature is **supporting functionality**, not the core product.

### Recovery decision

The application can indicate:

- what should be disposed of,
- what can be recovered/recycled,
- estimated value/recovery amount where applicable.

### Recovery inventory

The household can maintain an inventory of material such as:

```text
PET bottles      2.4 kg
Cardboard        3.1 kg
Aluminium        0.6 kg

Estimated value  ₹151
```

### Collection request

The household can submit a structured collection request for its accumulated recyclable material. Eligible nearby kabadiwalas can then see the request and decide whether to service it.

Relevant information may include:

- material type,
- quantity/estimated value,
- pickup location,
- request status,
- eligible collector information where applicable.

### Contribution / impact

The household can see its contribution to the recovery process, such as:

- total material recovered,
- material by type,
- collections completed,
- estimated recovery value,
- downstream destination / recycling sector where available.

The impact section should use measurable data rather than unsupported environmental conversions.

---

# 4. Kabadiwala / Recovery Collector

## Purpose

Give existing collectors a structured view of available recyclable material and make it easier to decide which recovery requests to service.

## Planned functionality

### Collection map

A map showing household recovery requests / collection opportunities.

Each request can display:

- material type,
- estimated quantity,
- estimated value/revenue,
- location,
- request status.

### Request management

The kabadiwala can:

- accept a request,
- reject a request,
- view request details,
- update collection status.

### Collection opportunity view

The system can organize available collection requests on a map and summarize the material/value available within a configurable radius. The kabadiwala decides which requests to service and how to travel between them.

We are **not** building a full route-optimization engine.

### Collector inventory

After collection, the kabadiwala's inventory is updated with the materials collected.

Example:

```text
PET             42 kg
Cardboard       68 kg
Aluminium       17 kg
Paper           91 kg
```

### Recycler requirements

The kabadiwala can see demand from participating recycling companies, for example:

```text
PET bottles     High demand
Cardboard       Medium demand
Aluminium       High demand
```

This helps collectors understand which materials are currently useful downstream.

### Collector dashboard / impact

The dashboard can show:

- material collected,
- total quantity,
- completed collections,
- estimated revenue/value,
- environmental contribution / recovery metrics.

---

# 5. Recycling Company / Recycler

## Purpose

Give downstream companies visibility into recyclable material available through the recovery network.

The recycler component is important for **closing the loop**, but it will not be the primary focus of the application/demo.

## Planned functionality

### Company profile

Basic company information and contact details.

### Material requirements

Companies can specify:

- required material type,
- required quantity,
- demand status.

Example:

```text
PET bottles
Required: 500 kg
Currently available: 327 kg
Status: Open
```

### Available material / kabadiwala view

The recycler can browse participating kabadiwalas and the material they currently hold.

The system should surface material relevant to the recycler's requirements.

### Booking / confirmation

The recycler can initiate or confirm a material acquisition/booking with the appropriate kabadiwala.

---

# 6. Material as a Core Entity

A recyclable material record should be maintained throughout the system rather than existing only inside a user's dashboard.

A material record should conceptually contain:

```text
Material
- type
- quantity
- estimated value
- source
- current holder
- status
- destination
```

This allows the system to represent the material's journey:

**Household material → Kabadiwala inventory → Recycler**

This also provides the foundation for later traceability and impact reporting without making traceability the primary product.

---

# 7. Core User Journey

### Household

```text
Add recyclable material
        ↓
Identify/select material
        ↓
Enter quantity
        ↓
Material added to recovery inventory
        ↓
Create collection request
        ↓
Select / get matched with kabadiwala
        ↓
Collection confirmed
```

### Kabadiwala

```text
Open collector dashboard
        ↓
See nearby recovery requests
        ↓
Review material + quantity + value
        ↓
Accept selected requests
        ↓
Collect material
        ↓
Update inventory
        ↓
View relevant recycler demand
```

### Recycler

```text
Set material requirements
        ↓
View available aggregated material
        ↓
Find suitable kabadiwala / material
        ↓
Book / confirm acquisition
```

---

# 8. Environmental Outcome

The project's primary intended environmental outcome is:

> **Increase the amount of recoverable household material that successfully enters the recycling/recovery chain instead of being discarded as ordinary waste.**

The application should ultimately be able to report measurable network outcomes such as:

- kilograms of material recovered,
- kilograms by material type,
- number of household recovery requests,
- number of collections completed,
- quantity aggregated by kabadiwalas,
- quantity transferred to recycling companies.

---

# 9. Demo Philosophy

The demo should tell the story of a recyclable item that would normally be lost in the waste stream and show how the system gives it a path into recovery.

### Planned narrative

1. **Physical opening:** show recyclable material sitting in a waste pile.
2. Ask: **Why is recoverable material here instead of in the recycling chain?**
3. Explain where the existing system breaks between household and recovery.
4. Demonstrate the **household** workflow.
5. Demonstrate the **kabadiwala** workflow.
6. Demonstrate the **recycler** workflow briefly to close the loop.
7. Show measurable environmental contribution.
8. Explain the AWS-backed implementation naturally alongside the demonstrated workflows.
9. End by returning to the original waste pile and showing that the material now has a path into recovery.

### Core presentation message

> **We are not building another recycling system. We are making the existing recovery system more connected and effective.**

---

# 10. Scope Guardrails

The project should remain focused on the core recovery workflow.

We are **not** currently planning to build:

- a new garbage collection fleet,
- a recycling plant,
- a municipal waste-management platform,
- a large social/community platform,
- extensive gamification,
- a complex carbon calculator,
- unnecessary payment infrastructure,
- unrelated smart-city features.

The recycler module remains lightweight, and the camera/ML feature remains optional/supporting.

---

# 11. Current Definition of the Project

> **A digital recovery platform that improves the flow of recyclable household material into the existing kabadiwala network, helps collectors manage and aggregate that material, and connects the resulting supply with recycling-company demand.**

The core environmental objective is simple:

> **Recover more recyclable material that would otherwise be lost to the ordinary waste stream.**

---

## Future Documentation

This file intentionally documents only the **current idea, scope, entities, workflow, and demo direction**.

Separate documents will later cover:

- **Supporting Evidence & Research** — problem evidence, statistics, studies, existing systems, competitors, and useful links.
- **Technology & Implementation** — architecture, AWS services, ML approach, data model, APIs, deployment, and implementation details.
