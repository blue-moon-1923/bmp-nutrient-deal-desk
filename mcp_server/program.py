"""The program being screened: cropland retirement to perennial pasture.

Design parameters for a modelled cropland-retirement programme. They are
assumptions this screening tool operates under, not a description of any
particular organisation's contract:

  * The contracted deliverable is RETIREMENT OF CROPLAND. Converting land
    out of row crops is the measurable commitment; grazing management on
    the resulting pasture is supported but not required.
  * The programme is non-prescriptive about grazing frequency. Prescriptive
    management requirements raise the administrative burden on a producer,
    which is a recognised constraint on enrolment in voluntary conservation
    programmes.
  * Infrastructure, particularly stock water, is treated as the binding
    practical constraint on establishing managed grazing.
  * Carbon outcomes are out of scope, so no herd monitoring is modelled.

Change these to match whatever programme you are screening against.
"""

from dataclasses import dataclass

COMMITMENT_YEARS = 10

# --------------------------------------------------------------------------
# Cost basis
# --------------------------------------------------------------------------
# All costs come from the CostPerUnitOfBmp column of the county BMP cost
# workbook -- the same published figures CAST uses. No contract rates, no
# multipliers, no assumptions layered on top.
COST_BASIS = (
    "CostPerUnitOfBmp from the county BMP cost workbook (CAST published "
    "costs). Costs are per unit of practice and vary by county."
)

# --------------------------------------------------------------------------
# Practice selection
# --------------------------------------------------------------------------
# The call identified several stacked reductions along one pathway:
#   establishing perennial pasture -> hayed -> grazed -> rotationally grazed
# Each step is a different CAST practice with a different county rate.
PATHWAY = {
    "hay": ["Land Retirement to Pasture"],
    "rotational_grazing": [
        "Land Retirement to Pasture",
        "Precision Intensive Rotational/Prescribed Grazing",
    ],
}

# --------------------------------------------------------------------------
# Timeline gates
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class TimelineGate:
    key: str
    label: str
    detail: str


TIMELINE = (
    TimelineGate("contract_signed", "Contract signed",
                 "Signing must precede the establishment season; a project "
                 "that misses it waits a full year."),
    TimelineGate("silage_window", "Silage harvest into pasture planting",
                 "Where corn yields are poor, shucking for silage and planting "
                 "pasture straight afterward in the fall is the earliest "
                 "possible establishment path."),
    TimelineGate("seeding_complete", "Seeding complete",
                 "Seeding must complete within the establishment window set "
                 "by the sponsoring agency."),
)

# --------------------------------------------------------------------------
# Risk flags the screening must raise -- every one came out of the call
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class RiskFlag:
    key: str
    question: str
    why_it_matters: str
    blocks_deal: bool = False


RISK_FLAGS = (
    RiskFlag(
        "water_infrastructure",
        "Does the farm need new or extended watering infrastructure?",
        "Stock water is typically the most expensive and slowest part of "
        "establishing managed grazing. Well drilling in particular can carry "
        "a long lead time, making it a schedule risk and not only a cost.",
    ),
    RiskFlag(
        "perimeter_fencing",
        "Is perimeter fencing required, and is it costed?",
        "Perimeter fencing is a significant line item. State cost-share and "
        "EQIP programs may cover part of it.",
    ),
    RiskFlag(
        "eqip_stacking",
        "Has the producer used or applied for EQIP on this acreage?",
        "Claiming reductions on acreage already funded through EQIP raises an "
        "additionality and double-counting question that must be resolved "
        "before the reduction is claimed. NRCS does not report to the Bay "
        "Program, so the overlap will not surface automatically.",
        blocks_deal=True,
    ),
    RiskFlag(
        "grazing_plan_required",
        "Will a written grazing plan be required?",
        "NRCS prescribed-grazing funding generally requires a written grazing "
        "plan. A plan written more tightly than the operation can follow "
        "tends to go unused, so keeping any required plan broad lowers the "
        "barrier to enrolment.",
    ),
    RiskFlag(
        "verification_burden",
        "Is a per-farm verification plan written and staffed?",
        "Per-farm verification planning is a well known administrative load "
        "in outcome-based conservation programmes. Virginia verifies on a "
        "five-year interval.",
    ),
    RiskFlag(
        "silvopasture_definition",
        "Is tree planting for shade being discussed?",
        "Shade is a common producer request, but planting trees for shade is "
        "not necessarily silvopasture. Confirm the published practice "
        "definition before claiming any reduction for it.",
    ),
)
