"""Which practices could this farm actually host?

A conservation plan lists what somebody already decided to do. It does not
list what the farm is *capable* of. This module answers the second question
from the farm's physical features, so a screening can surface practices the
plan never mentioned.

Requirements come from the CBP Quick Reference Guide's qualifying conditions
(indexed in data/bmp_guide_index.json) plus the practice definitions. Where
the guide is silent, the practice is treated as generally available.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GUIDE_INDEX = ROOT / "data" / "bmp_guide_index.json"


# --------------------------------------------------------------------------
# Site features an outreach visit can establish
# --------------------------------------------------------------------------

SITE_FEATURES = {
    "has_cropland":        "Is any land in row crops?",
    "has_pasture":         "Is any land in pasture or hay?",
    "has_stream_frontage": "Does a stream, pond or tidal water border the land?",
    "has_livestock":       "Are livestock grazed on the property?",
    "has_dairy":           "Is this a dairy operation?",
    "has_poultry":         "Is there a poultry operation?",
    "has_horses":          "Are horses kept on the property?",
    "has_barnyard":        "Is there a barnyard, loafing lot or heavy-use area?",
    "has_manure_storage":  "Is manure stored or handled on site?",
    "has_irrigation":      "Is any cropland irrigated?",
    "has_tile_drainage":   "Is any cropland tile-drained?",
    "has_forest":          "Is any land wooded, or available to be planted?",
    "has_wetland_area":    "Is there hydric soil, floodplain or a drained wetland?",
}

# practice -> (required_any, required_all, note)
# required_any: at least one of these features must be present
# required_all: every one must be present
REQUIREMENTS: dict[str, tuple[tuple[str, ...], tuple[str, ...], str]] = {
    "Forest Buffer":                 (("has_stream_frontage",), (), "Linear wooded strip along water."),
    "Forest Buffer - Narrow":        (("has_stream_frontage",), (), "10-35 ft wide; no upland treatment."),
    "Grass Buffer":                  (("has_stream_frontage",), (), "Linear grass strip along water."),
    "Grass Buffer - Narrow":         (("has_stream_frontage",), (), "10-35 ft wide; no upland treatment."),
    "Forest Buffer-Streamside with Exclusion Fencing":
        ((), ("has_stream_frontage", "has_livestock"), "Pasture buffer; fencing keeps stock out of the stream."),
    "Grass Buffer-Streamside with Exclusion Fencing":
        ((), ("has_stream_frontage", "has_livestock"), "Pasture buffer with exclusion fencing."),
    "Forest Buffer-Narrow with Exclusion Fencing":
        ((), ("has_stream_frontage", "has_livestock"), "Narrow pasture buffer with fencing."),
    "Grass Buffer-Narrow with Exclusion Fencing":
        ((), ("has_stream_frontage", "has_livestock"), "Narrow pasture buffer with fencing."),
    "Off Stream Watering Without Fencing":
        ((), ("has_livestock",), "Alternative water source draws stock off the stream."),
    "Precision Intensive Rotational/Prescribed Grazing":
        ((), ("has_livestock", "has_pasture"), "Managed rotation across paddocks."),
    "Horse Pasture Management":      ((), ("has_horses",), "Specific to horse operations."),
    "Barnyard Runoff Control":       ((), ("has_barnyard",), "Treats runoff from a heavy-use area."),
    "Loafing Lot Management":        ((), ("has_barnyard",), "Treats a loafing lot."),
    "Animal Waste Management System":((), ("has_manure_storage",), "Storage and handling structure."),
    "Animal mortality disposal by composting": ((), ("has_livestock",), "Requires livestock mortality."),
    "Dairy Precision Feeding and/or Forage Management":
        ((), ("has_dairy",), "Ration management reduces excreted nutrients."),
    "Lagoon Covers":                 ((), ("has_manure_storage",), "Requires a lagoon."),
    "Poultry Litter Amendments (alum, for example)": ((), ("has_poultry",), "Requires poultry litter."),
    "Manure Transport":              ((), ("has_manure_storage",), "Moves surplus manure off the watershed."),
    "Manure Incorporation Low Disturbance Late": ((), ("has_manure_storage", "has_cropland"), "Incorporates applied manure."),
    "Cropland Irrigation Management":((), ("has_irrigation",), "Requires irrigated cropland."),
    "Irrigation Water Capture Reuse":((), ("has_irrigation",), "Captures and reuses irrigation water."),
    "Drainage Water Management":     ((), ("has_tile_drainage",), "Controls tile outflow timing."),
    "Denitrifying Ditch Bioreactors":((), ("has_tile_drainage",), "Treats tile drainage water."),
    "Saturated Buffer":              ((), ("has_tile_drainage", "has_stream_frontage"), "Routes tile water through a buffer."),
    "Blind inlets":                  ((), ("has_tile_drainage",), "Replaces open tile inlets."),
    "Cover Crop Commodity Normal":   ((), ("has_cropland",), "Planted after harvest; may be harvested."),
    "Cover Crop Traditional Wheat Late Other": ((), ("has_cropland",), "Not harvested."),
    "Cover Crop Traditional with Fall Nutrients Wheat Late Other": ((), ("has_cropland",), "Fall nutrients applied."),
    "Tillage Management-Conservation": ((), ("has_cropland",), "Must keep 15% or more residue after planting."),
    "Alternative Crops":             ((), ("has_cropland",), "Replaces a conventional row crop."),
    "Land Retirement to Pasture":    ((), ("has_cropland",), "Retires cropland into perennial pasture."),
    "Land Retirement to Ag Open Space": ((), ("has_cropland",), "Retires cropland to open space."),
    "Tree Planting":                 (("has_cropland", "has_pasture", "has_forest"), (), "Establishes trees on open land."),
    "Wetland Restoration - Floodplain":  ((), ("has_wetland_area",), "Restores a drained or degraded wetland."),
    "Wetland Restoration - Headwater":   ((), ("has_wetland_area",), "Restores a headwater wetland."),
    "Wetland Creation - Floodplain":     ((), ("has_wetland_area",), "Creates wetland where none existed."),
    "Wetland Creation - Headwater":      ((), ("has_wetland_area",), "Creates a headwater wetland."),
    "Agricultural Stormwater Management": ((), ("has_cropland",), "Treats runoff from cropped acres."),
    "Nutrient Management Core N":    (("has_cropland", "has_pasture"), (), "Core plan, nitrogen."),
    "Nutrient Management Core P":    (("has_cropland", "has_pasture"), (), "Core plan, phosphorus."),
    "Soil Conservation and Water Quality Plans": (("has_cropland", "has_pasture"), (), "Whole-farm plan."),
}


def _guide_index() -> dict[str, dict]:
    if not GUIDE_INDEX.is_file():
        return {}
    try:
        return {s["code"]: s for s in json.loads(GUIDE_INDEX.read_text())}
    except (json.JSONDecodeError, OSError):
        return {}


def county_practices(db_path: str, county: str) -> dict[str, dict]:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    rows = con.execute("""
        SELECT bmp_name, unit, cost_per_unit, tn_lb_per_unit, tn_cost_per_lb
        FROM bmp_rates WHERE county=? AND sector='Agriculture' AND tier='Primary'
          AND tn_lb_per_unit > 0""", (county,)).fetchall()
    con.close()
    return {r["bmp_name"]: dict(r) for r in rows}


def assess(
    db_path: str, *, county: str, features: dict[str, bool],
    limit: int = 40,
) -> dict[str, Any]:
    """Which practices this farm can host, cannot host, and cannot be judged.

    A feature left unanswered produces an `undetermined` result, never an
    assumed yes. The point of the tool is to tell a field visit
    which question to go back and ask.
    """
    known = county_practices(db_path, county)
    if not known:
        return {"error": f"No agricultural rate data for county {county!r}.",
                "refused": True}

    eligible, ineligible, undetermined = [], [], []
    for name, rate in known.items():
        req_any, req_all, note = REQUIREMENTS.get(name, ((), (), ""))
        needed = set(req_any) | set(req_all)
        if not needed:
            eligible.append({**rate, "practice": name, "requires": [],
                             "why": "No site-specific requirement on file."})
            continue
        unknown = [f for f in needed if features.get(f) is None]
        if unknown:
            undetermined.append({
                "practice": name, "unresolved": unknown,
                "questions": [SITE_FEATURES[f] for f in unknown if f in SITE_FEATURES],
                "tn_cost_per_lb": rate["tn_cost_per_lb"],
                "tn_lb_per_unit": rate["tn_lb_per_unit"],
                "why": note})
            continue
        ok_all = all(features.get(f) for f in req_all)
        ok_any = (not req_any) or any(features.get(f) for f in req_any)
        if ok_all and ok_any:
            eligible.append({**rate, "practice": name,
                             "requires": sorted(needed), "why": note})
        else:
            missing = [f for f in req_all if not features.get(f)]
            if req_any and not ok_any:
                missing.append("any of: " + ", ".join(req_any))
            ineligible.append({"practice": name, "missing": missing, "why": note})

    eligible.sort(key=lambda r: (r["tn_cost_per_lb"] is None, r["tn_cost_per_lb"]))
    undetermined.sort(key=lambda r: (r["tn_cost_per_lb"] is None, r["tn_cost_per_lb"]))

    answered = sum(1 for v in features.values() if v is not None)
    return {
        "county": county,
        "features_answered": answered,
        "features_total": len(SITE_FEATURES),
        "eligible": eligible[:limit],
        "undetermined": undetermined[:limit],
        "ineligible": ineligible[:limit],
        "counts": {"eligible": len(eligible), "undetermined": len(undetermined),
                   "ineligible": len(ineligible)},
        "note": ("Eligibility is physical capability, not a recommendation. "
                 "An undetermined practice is one where a site question has "
                 "not been answered; it is never assumed either way."),
    }


def guide_conditions(practice_or_code: str) -> dict[str, Any]:
    """The reference guide's qualifying conditions for a sheet."""
    idx = _guide_index()
    hit = idx.get(practice_or_code.upper())
    if not hit:
        q = practice_or_code.lower()
        for code, sheet in idx.items():
            if q in sheet["title"].lower():
                hit = sheet
                break
    if not hit:
        return {"error": f"No reference sheet found for {practice_or_code!r}.",
                "available": sorted(idx), "refused": True}
    return {
        "code": hit["code"], "title": hit["title"], "page": hit["page"],
        "definition": hit.get("definition"),
        "qualifying_conditions": hit.get("qualifying_conditions"),
        "source": ("CBP Quick Reference Guide for BMPs, CBP/TRS-323-18, "
                   "second edition."),
    }
