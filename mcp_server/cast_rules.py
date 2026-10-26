"""CAST / Chesapeake Bay Program rules, transcribed from source documents.

Sources, both published by the Chesapeake Bay Program:
  * CBP Quick Reference Guide for BMPs, CBP/TRS-323-18, Second Edition
    (2022/2024), sheets A-12 and A-13.
  * BMP_LbsReducedAndCostsCounty workbook -> data/cast_bmp_va.db
    (24,704 Virginia rows: per-county cost and TN/TP/TSS lbs reduced per unit)

Nothing in this file is recalled by a language model. Every value is read
from one of those two documents.
"""

# --------------------------------------------------------------------------
# Buffer upland efficiencies by hydrogeomorphic region
# Quick Reference Guide, Tables A-12-1 and A-13-1 (identical values).
# Phase 6 Watershed Model.
# --------------------------------------------------------------------------

# CRITICAL: nitrogen efficiency is applied to FOUR upland acres per acre of
# buffer; phosphorus and sediment to TWO. Treating the ratio as 1:1 is the
# single easiest way to understate a buffer project, and it is the kind of
# mistake a hand-built spreadsheet makes silently.
UPLAND_ACRES_PER_BUFFER_ACRE = {"N": 4, "P": 2, "TSS": 2}

# HGMR -> (forest buffer N%, grass buffer N%, P% both, sediment% both)
HGMR_BUFFER_EFFICIENCY = {
    "Coastal Plain Dissected Uplands":  (65, 46, 42, 56),
    "Piedmont Carbonate":               (46, 32, 36, 48),
    "Appalachian Plateau Siliciclastic":(54, 38, 42, 56),
    "Coastal Plain Uplands":            (31, 21, 45, 60),
    "Appalachian Plateau Carbonate":    (54, 38, 42, 56),
    "Piedmont Crystalline":             (56, 39, 42, 56),
    "Valley and Ridge Carbonate":       (34, 24, 30, 40),
    "Valley and Ridge Siliciclastic":   (46, 32, 39, 52),
    "Blue Ridge":                       (34, 24, 30, 40),
    "Coastal Plain Lowlands":           (19, 13, 45, 60),
    "Mesozoic Lowlands":                (34, 24, 30, 40),
}

# Forest buffer nitrogen efficiency spans 19% to 65% depending ONLY on which
# hydrogeomorphic region the buffer sits in. Picking the wrong HGMR is a
# 3.4x error on the nitrogen number.
HGMR_SPREAD_NOTE = (
    "Forest buffer nitrogen efficiency ranges from 19% (Coastal Plain "
    "Lowlands) to 65% (Coastal Plain Dissected Uplands). HGMR is a property "
    "of the site, never a choice."
)

# --------------------------------------------------------------------------
# Buffer width thresholds -- Quick Reference Guide A-12 / A-13
# --------------------------------------------------------------------------

BUFFER_MIN_WIDTH_FT = 35          # below this, only "narrow" practices qualify
BUFFER_RECOMMENDED_WIDTH_FT = 100
BUFFER_NARROW_RANGE_FT = (10, 35)

# Narrow buffers are simulated as a LOAD SOURCE CHANGE ONLY. They receive no
# upland efficiency treatment at all.
NARROW_BUFFER_GETS_UPLAND_EFFICIENCY = False

# --------------------------------------------------------------------------
# Which reference sheet governs -- A-12 vs A-13
# --------------------------------------------------------------------------

# A-12 covers buffers on converted CROPLAND.
# A-13 covers buffers on converted PASTURE, which include exclusion fencing.
# Using the wrong sheet means using the wrong practice name, and therefore
# the wrong row in the county cost/reduction table.
SHEET_BY_PRIOR_LAND_USE = {
    "cropland": "A-12",
    "pasture":  "A-13",
}

PRACTICE_BY_SHEET_AND_WIDTH = {
    ("A-12", "full"):   "Forest Buffer",
    ("A-12", "narrow"): "Forest Buffer - Narrow",
    ("A-13", "full"):   "Forest Buffer-Streamside with Exclusion Fencing",
    ("A-13", "narrow"): "Forest Buffer-Narrow with Exclusion Fencing",
}

GRASS_PRACTICE_BY_SHEET_AND_WIDTH = {
    ("A-12", "full"):   "Grass Buffer",
    ("A-12", "narrow"): "Grass Buffer - Narrow",
    ("A-13", "full"):   "Grass Buffer-Streamside with Exclusion Fencing",
    ("A-13", "narrow"): "Grass Buffer-Narrow with Exclusion Fencing",
}

# --------------------------------------------------------------------------
# Qualifying conditions the alignment step must confirm
# --------------------------------------------------------------------------

QUALIFYING_CONDITIONS = {
    "buffer": [
        ("prior_land_use_matches_sheet",
         "Buffer practices on cropland use A-12; on pasture use A-13 (which "
         "includes exclusion fencing). The sheet determines the practice name."),
        ("width_determines_practice",
         f"Any buffer under {BUFFER_MIN_WIDTH_FT} ft average width qualifies "
         "only as a narrow buffer, which receives no upland efficiency."),
        ("cost_share_standard",
         "Cost-shared buffers must meet the standards of the federal or state "
         "program they are enrolled in (e.g. CREP, EQIP)."),
        ("non_cost_share_ri",
         "Non-cost-shared buffers must be documented and meet CBP Resource "
         "Improvement criteria: RI-7,8 grass / RI-9,10 forest on cropland "
         "(A-12); RI-4a,4b narrow and RI-5,6 on pasture (A-13)."),
    ],
}

# --------------------------------------------------------------------------
# Credit duration and verification -- CBP verification framework
# --------------------------------------------------------------------------

# Credit duration = how long a practice counts as valid WITHOUT re-inspection.
# With inspection, a BMP is credited indefinitely.
CREDIT_DURATION_YEARS = {
    "Forest Buffer": 15,
    "Forest Buffer - Narrow": 15,
    "Forest Buffer-Streamside with Exclusion Fencing": 15,
    "Forest Buffer-Narrow with Exclusion Fencing": 15,
    "Tree Planting": 15,
    "_default": 10,
}
# Wetland BMPs carry no credit duration.
NO_CREDIT_DURATION = ("Wetland Creation", "Wetland Restoration")

# Virginia's verification interval under VSMP.
VA_VERIFICATION_INTERVAL_YEARS = 5

SOURCES = {
    "quick_reference_guide": (
        "Chesapeake Bay Program. 2022. Quick Reference Guide for Best "
        "Management Practices. CBP/TRS-323-18. Second Edition (2022/2024). "
        "Sheets A-12, A-13."
    ),
    "county_rates": (
        "BMP_LbsReducedAndCostsCounty workbook, Virginia rows "
        "(24,704 rows, 96 counties, 270 practices)."
    ),
    "expert_panel": (
        "Belt et al. 2014. Recommendations of the Expert Panel to Reassess "
        "Removal Rates for Riparian Forest and Grass Buffers BMPs. Approved "
        "by CBP Water Quality Goal Implementation Team, October 2014."
    ),
}
