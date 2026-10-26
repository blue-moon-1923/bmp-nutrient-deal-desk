"""Virginia nutrient credit rules, as constants with their sources attached.

Every number an agent is allowed to state comes from this file or is computed
from it. Nothing here is remembered or inferred by a language model.

Each constant carries a SOURCE note. Values marked REFERENCE are plausible
magnitudes used so the tool runs end to end; they are NOT authoritative and
must be replaced with the loading rates in the applicable Watershed
Implementation Plan or approved TMDL before any real filing. The app surfaces
this distinction to the user on every result -- see `rate_basis` in outputs.
"""

from dataclasses import dataclass, field

# --------------------------------------------------------------------------
# Statutory and regulatory constants -- VERIFIED
# --------------------------------------------------------------------------

# 9VAC25-900-90: "5.0% of the total credits certified will be retired by the
# department at the time of nutrient credit certification and will not be
# placed on the registry for exchange."
CERTIFICATION_RETIREMENT = 0.05

# 9VAC25-900-110 D: conversions within 35 feet of a water body with perennial
# flow, measured from the top of the channel bank, generate no credits.
PERENNIAL_BUFFER_EXCLUSION_FT = 35

# 9VAC25-900-110: in the Chesapeake Bay watershed, reductions from practices
# in place before this date cannot generate credits. Southern Rivers
# watersheds use July 1, 2009.
BAY_PRACTICE_CUTOFF = "2005-07-01"
SOUTHERN_RIVERS_PRACTICE_CUTOFF = "2009-07-01"

# 9VAC25-900-90: release schedule for land use conversion projects.
RELEASE_SCHEDULE_CONVERSION = (
    ("certification_verified", 0.25, "DEQ verifies certification conditions are met"),
    ("afforestation_planted", 0.25, "At least 400 woody stems per acre planted"),
    ("performance_criteria_met", 0.50, "Implementation plan criteria under 9VAC25-900-120"),
)

# 9VAC25-900-90: stream and wetland restoration release schedule.
RELEASE_SCHEDULE_RESTORATION = (
    ("construction_complete", 0.25, "Construction complete and conditions verified"),
    ("monitoring_yr_bankfull", 0.25, "Per monitoring year, if a bankfull event occurs"),
    ("monitoring_yr_stable", 0.10, "Per monitoring year, stable channel but no bankfull event"),
)
# No further restoration credits release after the fourth monitoring year
# until a bankfull event occurs.
RESTORATION_BANKFULL_STALL_YEAR = 4


# --------------------------------------------------------------------------
# Market prices -- VERIFIED RANGES, dated
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class CreditPrice:
    label: str
    low: float
    high: float
    unit: str
    nutrient: str
    source: str
    as_of: str
    valid_for: str

    def midpoint(self) -> float:
        return (self.low + self.high) / 2


PRICES = {
    "perpetual_p_impervious": CreditPrice(
        label="Perpetual phosphorus, impervious-surface offset",
        low=15_000.0, high=20_000.0, unit="$/lb P", nutrient="P",
        source="Environmental Policy Innovation Center market analysis",
        as_of="2026-08",
        valid_for="Land development offsetting impervious surface under 9VAC25-875",
    ),
    "perpetual_p_study_range": CreditPrice(
        label="Perpetual phosphorus, observed purchase range (MS4 study)",
        low=9_500.0, high=17_000.0, unit="$/lb P", nutrient="P",
        source="Ferris et al., JAWRA 2024, Virginia MS4 compliance study",
        as_of="2024",
        valid_for="MS4 perpetual phosphorus compliance; historical reference",
    ),
    "point_source_p": CreditPrice(
        label="Point-source phosphorus credit",
        low=5.0, high=6.0, unit="$/lb P", nutrient="P",
        source="Ferris et al., JAWRA 2024",
        as_of="2024",
        valid_for="Point-source discharger permit compliance",
    ),
    "point_source_n": CreditPrice(
        label="Point-source nitrogen credit",
        low=3.0, high=4.0, unit="$/lb N", nutrient="N",
        source="Ferris et al., JAWRA 2024",
        as_of="2024",
        valid_for="Point-source discharger permit compliance",
    ),
    "offset_fund_n": CreditPrice(
        label="Nutrient Offset Fund, nitrogen (statutory rate)",
        low=5.08, high=5.08, unit="$/lb N", nutrient="N",
        source="Virginia regulation cited in EPA WQT case study, 2024",
        as_of="2024",
        valid_for="Payments into the Nutrient Offset Fund",
    ),
    "offset_fund_p": CreditPrice(
        label="Nutrient Offset Fund, phosphorus (statutory rate)",
        low=11.15, high=11.15, unit="$/lb P", nutrient="P",
        source="Virginia regulation cited in EPA WQT case study, 2024",
        as_of="2024",
        valid_for="Payments into the Nutrient Offset Fund",
    ),
}

# The spread that makes this app necessary: the same pound of phosphorus is
# worth ~$5 or ~$17,500 depending entirely on which regulatory driver the
# buyer is satisfying. Quoting the wrong one is a three-order-of-magnitude
# error, which is why no agent may name a price without calling a tool.
PRICE_SPREAD_NOTE = (
    "Point-source P and perpetual impervious-offset P differ by roughly "
    "3,000x. Credit type is determined by the BUYER's regulatory driver, "
    "never by what the seller would prefer."
)


# --------------------------------------------------------------------------
# Loading rates -- REFERENCE VALUES, must be replaced with WIP/TMDL figures
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class LoadingRate:
    land_use: str
    n_lb_ac_yr: float
    p_lb_ac_yr: float
    basis: str = "REFERENCE"


# 9VAC25-900-110: "the loadings per acre shall be based on the applicable
# loading levels in the Watershed Implementation Plan or an approved TMDL."
# Those levels are tributary- and segment-specific. The magnitudes below are
# ordinary published ranges for the Bay watershed, included so the tool runs;
# they are flagged REFERENCE everywhere they surface.
LOADING_RATES = {
    "cropland":      LoadingRate("Cropland, conventional",        19.0, 1.90),
    "cropland_nt":   LoadingRate("Cropland, no-till w/ cover",    12.5, 1.10),
    "pasture":       LoadingRate("Pasture, unimproved",            10.5, 1.25),
    "pasture_rot":   LoadingRate("Pasture, rotational grazing",     7.0, 0.80),
    "hayland":       LoadingRate("Hayland",                         6.5, 0.55),
    "forest":        LoadingRate("Forest",                          2.4, 0.14),
    "wetland":       LoadingRate("Restored wetland",                1.9, 0.11),
    "turfgrass":     LoadingRate("Turfgrass / managed open",       11.0, 1.05),
    "impervious":    LoadingRate("Impervious surface",             16.0, 1.60),
}

# Land uses ordered by intensity. 9VAC25-900-110 D: "Conversion of land to a
# more intensive land use activity will not generate nutrient credits."
INTENSITY_ORDER = (
    "wetland", "forest", "hayland", "pasture_rot", "pasture",
    "turfgrass", "cropland_nt", "cropland", "impervious",
)


def is_more_intensive(pre: str, post: str) -> bool:
    """True if converting pre -> post moves to a MORE intensive use."""
    return INTENSITY_ORDER.index(post) > INTENSITY_ORDER.index(pre)


# --------------------------------------------------------------------------
# Delivery factors by tributary -- REFERENCE VALUES
# --------------------------------------------------------------------------

# 9VAC25-900-110 A: "The applicable delivery factors, dependent upon the
# tributary in which the nutrient credit-generating project is located, shall
# be applied when calculating the potential credits generated."
DELIVERY_FACTORS = {
    "potomac":        {"n": 0.75, "p": 0.62, "basis": "REFERENCE"},
    "rappahannock":   {"n": 0.81, "p": 0.70, "basis": "REFERENCE"},
    "york":           {"n": 0.84, "p": 0.73, "basis": "REFERENCE"},
    "james":          {"n": 0.69, "p": 0.55, "basis": "REFERENCE"},
    "eastern_shore":  {"n": 0.92, "p": 0.85, "basis": "REFERENCE"},
    "southern_rivers": {"n": 1.00, "p": 1.00, "basis": "REFERENCE, non-Bay"},
}


# --------------------------------------------------------------------------
# Baseline eligibility -- 9VAC25-900-100
# --------------------------------------------------------------------------

@dataclass
class BaselineCheck:
    key: str
    question: str
    why: str
    blocking: bool = True


BASELINE_CHECKS = [
    BaselineCheck(
        "practice_start_date",
        "Was the practice in place before the watershed cutoff date?",
        "9VAC25-900-110: Bay watershed practices in place before 2005-07-01 "
        "(Southern Rivers: 2009-07-01) cannot generate credits.",
    ),
    BaselineCheck(
        "wip_baseline_met",
        "Has the baseline level of reduction assigned in the WIP or approved "
        "TMDL been achieved for cropland, hayland, and pasture?",
        "9VAC25-900-100: baseline must be met before credits accrue.",
    ),
    BaselineCheck(
        "perennial_buffer",
        "Is any part of the conversion within 35 ft of perennial flow?",
        "9VAC25-900-110 D: that acreage generates no credits.",
    ),
    BaselineCheck(
        "more_intensive",
        "Does the conversion move to a more intensive land use?",
        "9VAC25-900-110 D: more intensive conversion generates no credits.",
    ),
    BaselineCheck(
        "practice_standard",
        "Does the practice follow the VACS BMP Manual or NRCS FOTG standard?",
        "9VAC25-900-110 B: required for department-approved efficiencies.",
    ),
    BaselineCheck(
        "financial_assurance",
        "For structural BMPs, is approved financial assurance in place?",
        "9VAC25-900-90: structural BMPs require financial assurance before "
        "any credits are released.",
        blocking=False,
    ),
]
