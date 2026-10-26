# Motivation and impact

Source material for the report. Figures come from the practitioner who did
the work, and from this application's own measured runs.

---

## The person

A four-person non-profit running a cropland-retirement programme in the
Chesapeake watershed. It paid roughly **twelve full-time outreach staff**,
employed through local non-profits and cooperatives, to meet farmers.

Those twelve had one job before anything else could happen: collect basic
information from a producer, then bring it back for an answer to the only
two questions a farmer actually asks.

> **"What will I have to do, and how much will I get paid to do it?"**

Answering that was one analyst. The author of this project.

## The work, as it was done

Every screening meant:

1. Read the conservation plan. These are **written differently by every
   planner**, sometimes **over a hundred pages**, with the things that matter
   — practice names, acreages, the property address — buried.
2. Compare each practice against the BMP Quick Reference Guide to find the
   governing definition and qualifying conditions.
3. Hunt for the right rows in the isolated scenarios to get reduction values.
4. Build the arithmetic by hand in a spreadsheet.
5. Sanity-check it.

**About four hours per project.**

The practitioner's own account: *"I was a bottleneck spending late nights
working on this... We were the bottleneck, and the hardest part was
deciphering the conservation plans."*

## What that costs, in numbers

| | |
|---|---|
| Projects scoped per year | **250** |
| Projects reaching contract | **50** (20%) |
| Hours per screening | **4** |
| **Analyst hours per year** | **1,000** |
| As 40-hour weeks | **25 weeks** |
| As a share of one full-time person | **48%** |
| As a share of a four-person organisation | **12% of total staff capacity** |

Two consequences follow, and the second is worse than the first.

**Latency.** When several projects were scoped at once, an initial estimate
could take **up to ten days** to reach the farmer. Twelve field staff sat
waiting on one person to answer the question they had been sent out to ask.

**Waste.** At a 20% conversion rate, **800 of those 1,000 hours each year go
into projects that never proceed.** The screening is what determines whether
a project is viable, so the effort cannot simply be skipped — but four hours
is an expensive way to discover a project does not work.

## What this application changes

Measured across seven real runs logged in `output/token_log.json`:

| | By hand | This application |
|---|---|---|
| Time to a first estimate | **4 hours** | **33 seconds** (mean of 7 runs; range 14–53 s) |
| Turnaround to the farmer | up to **10 days** | **same day** |
| Tokens per run | — | 54,956 mean (21k without a document, ~68k with one) |

Allowing **30 minutes of human review per project** — which the work still
needs, and the application does not pretend otherwise:

| | Hours/year |
|---|---|
| Current | 1,000 |
| With screening automated, 30 min review each | **127** |
| **Saved** | **873 hours, or 87%** |

At 15 minutes of review the saving is 935 hours (94%). The honest figure is
the conservative one: **roughly 870 hours a year**, about **22 working weeks**,
returned to a four-person organisation.

## What it does not change

The programme still needs the next step: a finer-toothed review of each
project, and a person the farmer trusts to sign the final contract. This
application produces a **screening**, not a certification. Its value is in
removing four hours of document archaeology and arithmetic from the front of
that process, not in replacing the judgement at the end of it.

## The second-order effect

The county map and practice ranking are not screening tools. They let the
twelve field staff see, before a visit, **which practices are worth targeting
in which county** — a 34× cost-effectiveness spread exists for the same
practice across Virginia counties. That turns outreach from relationship-led
into evidence-led, and it builds institutional knowledge in the field team
rather than in one analyst's head.

## Sources for every number

- **4 hours, 250 scoped, 50 successful, 12 outreach staff, 4-person
  organisation, 10-day turnaround, 100+ page plans**: practitioner account
  from the person who performed the work.
- **33 seconds, 54,956 tokens**: measured, seven runs, `output/token_log.json`.
- **34× county spread**: computed from the county rate table,
  `data/cast_bmp_va.db`.
- **87% saving**: derived from the above, stated with its assumption
  (30 minutes of human review retained per project).
