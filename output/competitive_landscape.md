# What already exists

Source material for the report's Motivation section. Every product named here
is real and current; the gap claimed at the end is stated narrowly on purpose.

---

## 1. CAST — Chesapeake Assessment Scenario Tool

Chesapeake Bay Program. <https://cast.chesapeakebay.net/>

The authority. CAST estimates nitrogen, phosphorus and sediment load
reductions, acres of each BMP, and costs for a scenario, with results
consistent with the Bay Program's Watershed Model. EPA notes it reports BMP
cost so users can select the most cost-effective practices.

**What it does not do.** CAST prices a scenario you have already specified.
You must already know which practice applies, in which county, at what
acreage, and whether it qualifies. It is the rate table this application
reads from — not a competitor so much as the substrate. A scenario tool
cannot tell you that "subsoiler" is not a creditable practice, or that a
riparian buffer already in the ground is not additional.

## 2. Nutrient Tracking Tool (NTT)

Texas Institute for Applied Environmental Research, Tarleton State
University, with USDA-NRCS. Built on the APEX model.

Field-scale. Estimates on-farm sediment, nitrogen and phosphorus losses from
soil, weather and management inputs, and compares practices to find
cost-effective strategies.

**What it does not do.** NTT needs detailed field-level management data
entered by someone who knows the farm and the tool. It answers "what would
this practice do on this field", not "what is in this document and can any of
it be credited".

## 3. ACPF Financial and Nutrient Reduction Tool

Agricultural Conservation Planning Framework add-on (Bravard et al.,
*Journal of Environmental Quality*, 2022).

The closest published match in spirit: pairs watershed BMP mapping with cost
and nitrogen-reduction estimates, and places the opportunity cost of retired
cropland spatially using crop productivity indices and land rent. Iowa and
Minnesota HUC-12 watersheds. Scenarios reported 26–31% nitrate reduction in
Iowa at $0.58m–$2.3m per year.

**What it does not do.** Watershed planning, not deal screening. Not
Chesapeake, not document-driven, no additionality logic.

## 4. Enrollment platforms — Truterra, Field to Market, ESMC, Regrow

Truterra is a farmer-owned, retailer-driven sustainability platform; its
carbon programme reported over $21m paid to farmers and 58% participation
growth in 2023. Field to Market leads a USDA climate-smart commodities
project across 30+ states with Truterra, Regrow and Corteva.

**Two things worth saying plainly.** First, these are **carbon-first**. The
Truterra Ohio wheat project's tracked indicators are greenhouse gas, nitrogen
use efficiency, soil quality, erosion, practices deployed and a sustainability
score — **no water quality metric**. Second, an ESMC/Regrow Minnesota pilot
targeting 50,000 acres with water quality credits reported that **farmer
enrollment was harder than anticipated and farm data collection was
time-consuming**.

That second point is independent confirmation of the bottleneck this
application addresses. The constraint in these programmes is not modelling —
it is getting a farm's information into a form the programme can act on.

## 5. State registries — Virginia DEQ, SWaN

Virginia's nonpoint source nutrient credit registry under 9VAC25-900, and
SWaN, the DEQ marketplace launched December 2025 with Water Ledger.

**What they do not do.** Transaction and listing infrastructure for credits
that already exist and have already been certified. They begin where this
application ends.

## 6. A general chatbot

ChatGPT or similar will discuss conservation practices fluently and will
produce a confident nitrogen figure on request. It holds no county rate
table, no reference-guide qualifying conditions, and no additionality rules,
and nothing stops it inventing a number. The failure is silent, which is the
dangerous kind.

---

## The gap

A targeted search for LLM or agent-based extraction of NRCS conservation
plans for credit origination returned **nothing in agriculture**. The nearest
published analogue is in medicine — agent-based extraction of structured data
from breast cancer synoptic reports (2026).

So the honest claim is narrow and defensible:

> Every piece of this exists. CAST holds the rates. The reference guide holds
> the qualifying conditions. The regulation holds the additionality rules.
> What does not exist is anything that reads the document a farm actually
> arrives as, decides which practices are real, which are creditable, and
> which need a question answered — and refuses to produce a number when it
> cannot.

Four things this does that none of the above do:

1. **Starts from the document**, not a form. A conservation plan, a list of
   BMPs about to go in, or field notes all enter the same way.
2. **Validates every practice name** against the county rate table, and
   refuses rather than approximating. `subsoiler` does not become
   `Biofilters`.
3. **Applies additionality by practice kind** — an existing structural
   practice is not additional; an annual practice can be credited for a year
   no cost-share paid for; anything reported to the state is never creditable.
4. **Converts ignorance into a work item.** A missing acreage or an unknown
   cost-share year comes back as the specific question to ask the producer,
   not as an assumption.

## Honest limitations to state in the report

- Virginia only. The rate tables, delivery factors and hydrogeomorphic
  regions are Virginia's, and the app now detects and refuses plans from
  other states rather than silently mispricing them.
- CAST remains the authority for stacked practices on shared acres; this
  tool assumes distinct acres and says so on every result.
- The county→HGMR suggestion is derived from physiographic province and
  centroid, and is offered as a suggestion to confirm, not a determination.
