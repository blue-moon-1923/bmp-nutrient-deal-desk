"""Deal screening: the arithmetic that used to live in a spreadsheet.

Every number returned here is computed from the county rate table or the
CBP Quick Reference Guide. No value is supplied by a language model, and the
agents are instructed that they may not state a figure that did not come
back from one of these functions.
"""

from __future__ import annotations

import sqlite3
from typing import Any

import cast_rules as CR
import program as P


class ScreeningError(Exception):
    """A request the rules do not permit, or data we do not have."""


def _connect(db_path: str) -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


# ---------------------------------------------------------------- lookups

def list_counties(db_path: str) -> list[str]:
    with _connect(db_path) as con:
        return [r[0] for r in con.execute(
            "SELECT DISTINCT county FROM bmp_rates ORDER BY county")]


def county_rate(db_path: str, county: str, bmp_name: str) -> dict[str, Any]:
    """The county's own CAST rate for one practice. Refuses to guess."""
    with _connect(db_path) as con:
        row = con.execute("""
            SELECT bmp_name, county, unit, cost_per_unit, tn_lb_per_unit,
                   tn_cost_per_lb, tp_lb_per_unit, tp_cost_per_lb,
                   tss_lb_per_unit, geography_full
            FROM bmp_rates
            WHERE county = ? AND bmp_name = ? AND tier = 'Primary'
            ORDER BY tn_lb_per_unit DESC LIMIT 1""", (county, bmp_name)).fetchone()
        if row is None:
            known = [r[0] for r in con.execute(
                "SELECT DISTINCT county FROM bmp_rates WHERE bmp_name=? LIMIT 5",
                (bmp_name,))]
            raise ScreeningError(
                f"No Virginia rate on file for {bmp_name!r} in {county!r}. "
                f"Counties that do have it include: {known}. "
                "This tool will not substitute another county's rate."
            )
        return dict(row)


# ---------------------------------------------------------------- screen

def screen_farm(
    db_path: str,
    *,
    county: str,
    cropland_acres: float,
    pathway: str = "rotational_grazing",
    hgmr: str | None = None,
    buffer_acres: float = 0.0,
    buffer_width_ft: float | None = None,
    prior_land_use: str = "cropland",
) -> dict[str, Any]:
    """Screen one farm end to end.

    Returns reductions, cost, cost per pound, and the arithmetic
    that produced each, so the audit trail can show the work.
    """
    if pathway not in P.PATHWAY:
        raise ScreeningError(
            f"Unknown pathway {pathway!r}. Must be one of {list(P.PATHWAY)}.")
    if cropland_acres <= 0:
        raise ScreeningError("cropland_acres must be positive.")

    steps: list[dict[str, Any]] = []
    total_tn = total_tp = total_tss = 0.0
    total_cast_cost = 0.0

    for bmp in P.PATHWAY[pathway]:
        rate = county_rate(db_path, county, bmp)
        tn = (rate["tn_lb_per_unit"] or 0.0) * cropland_acres
        tp = (rate["tp_lb_per_unit"] or 0.0) * cropland_acres
        tss = (rate["tss_lb_per_unit"] or 0.0) * cropland_acres
        cast_cost = (rate["cost_per_unit"] or 0.0) * cropland_acres
        total_tn += tn; total_tp += tp; total_tss += tss
        total_cast_cost += cast_cost
        steps.append({
            "practice": bmp,
            "unit": rate["unit"],
            "acres": cropland_acres,
            "tn_lb_per_unit": rate["tn_lb_per_unit"],
            "tp_lb_per_unit": rate["tp_lb_per_unit"],
            "tn_lb": round(tn, 2),
            "tp_lb": round(tp, 2),
            "tss_lb": round(tss, 2),
            "cast_cost": round(cast_cost, 2),
            "arithmetic": (
                f"{rate['tn_lb_per_unit']:.4f} lb N/{rate['unit']} x "
                f"{cropland_acres:g} = {tn:,.2f} lb N"
            ),
            "source": f"CAST county rate, {rate['geography_full']}",
        })

    # ---- optional riparian buffer, which follows different rules entirely
    buffer_block = None
    if buffer_acres > 0:
        buffer_block = _screen_buffer(
            db_path, county=county, buffer_acres=buffer_acres,
            buffer_width_ft=buffer_width_ft, hgmr=hgmr,
            prior_land_use=prior_land_use)
        total_tn += buffer_block["tn_lb"]
        total_tp += buffer_block["tp_lb"]
        total_cast_cost += buffer_block["cast_cost"]

    return {
        "county": county,
        "pathway": pathway,
        "cropland_acres": cropland_acres,
        "commitment_years": P.COMMITMENT_YEARS,
        "steps": steps,
        "buffer": buffer_block,
        "totals": {
            "tn_lb_per_year": round(total_tn, 2),
            "tp_lb_per_year": round(total_tp, 2),
            "tss_lb_per_year": round(total_tss, 2),
            "tn_lb_over_commitment": round(total_tn * P.COMMITMENT_YEARS, 2),
        },
        "cost": {
            "total_cost": round(total_cast_cost, 2),
            "basis": P.COST_BASIS,
            "cost_per_lb_n": round(total_cast_cost / total_tn, 2) if total_tn else None,
            "cost_per_lb_n_over_commitment": (
                round(total_cast_cost / (total_tn * P.COMMITMENT_YEARS), 2)
                if total_tn else None),
        },
        "alternatives_not_taken": _alternatives_note(
            db_path, county, total_tn / cropland_acres if cropland_acres else 0.0),
        "cost_note": (
            f"${total_cast_cost:,.0f} across {cropland_acres:g} acres, from "
            "each county's own published per-unit cost. Costs are per unit "
            "of practice and are not escalated or adjusted."
        ),
    }


def _screen_buffer(
    db_path: str, *, county: str, buffer_acres: float,
    buffer_width_ft: float | None, hgmr: str | None, prior_land_use: str,
) -> dict[str, Any]:
    """Buffers: sheet selection, the 35 ft cliff, and the upland multiplier."""
    if prior_land_use not in CR.SHEET_BY_PRIOR_LAND_USE:
        raise ScreeningError(
            f"prior_land_use must be one of "
            f"{list(CR.SHEET_BY_PRIOR_LAND_USE)} -- it decides whether sheet "
            "A-12 (cropland) or A-13 (pasture, with exclusion fencing) "
            "governs, and therefore which practice name applies.")
    if buffer_width_ft is None:
        raise ScreeningError(
            "buffer_width_ft is required. Below "
            f"{CR.BUFFER_MIN_WIDTH_FT} ft a buffer qualifies only as a narrow "
            "practice and receives NO upland efficiency, which changes the "
            "nitrogen result by more than half. It cannot be assumed.")

    sheet = CR.SHEET_BY_PRIOR_LAND_USE[prior_land_use]
    width_class = "full" if buffer_width_ft >= CR.BUFFER_MIN_WIDTH_FT else "narrow"
    practice = CR.PRACTICE_BY_SHEET_AND_WIDTH[(sheet, width_class)]

    rate = county_rate(db_path, county, practice)
    tn = (rate["tn_lb_per_unit"] or 0.0) * buffer_acres
    tp = (rate["tp_lb_per_unit"] or 0.0) * buffer_acres
    tss = (rate["tss_lb_per_unit"] or 0.0) * buffer_acres
    cast_cost = (rate["cost_per_unit"] or 0.0) * buffer_acres

    upland = None
    if width_class == "full":
        if hgmr is None:
            raise ScreeningError(
                "hgmr is required for a full-width buffer. Forest buffer "
                "nitrogen efficiency ranges from 19% to 65% depending only on "
                f"hydrogeomorphic region. Known regions: "
                f"{sorted(CR.HGMR_BUFFER_EFFICIENCY)}")
        if hgmr not in CR.HGMR_BUFFER_EFFICIENCY:
            raise ScreeningError(
                f"Unknown HGMR {hgmr!r}. Known: "
                f"{sorted(CR.HGMR_BUFFER_EFFICIENCY)}")
        n_eff, _grass_n, p_eff, _tss = CR.HGMR_BUFFER_EFFICIENCY[hgmr]
        upland = {
            "hgmr": hgmr,
            "n_efficiency_pct": n_eff,
            "p_efficiency_pct": p_eff,
            "upland_acres_n": buffer_acres * CR.UPLAND_ACRES_PER_BUFFER_ACRE["N"],
            "upland_acres_p": buffer_acres * CR.UPLAND_ACRES_PER_BUFFER_ACRE["P"],
            "note": (
                f"Nitrogen efficiency applies to "
                f"{CR.UPLAND_ACRES_PER_BUFFER_ACRE['N']} upland acres per acre "
                f"of buffer; phosphorus to "
                f"{CR.UPLAND_ACRES_PER_BUFFER_ACRE['P']}."
            ),
        }

    return {
        "sheet": sheet,
        "practice": practice,
        "width_class": width_class,
        "buffer_width_ft": buffer_width_ft,
        "buffer_acres": buffer_acres,
        "tn_lb": round(tn, 2),
        "tp_lb": round(tp, 2),
        "tss_lb": round(tss, 2),
        "cast_cost": round(cast_cost, 2),
        "upland_treatment": upland,
        "narrow_warning": (
            None if width_class == "full" else
            f"At {buffer_width_ft:g} ft this is a NARROW buffer. Narrow "
            "buffers are simulated as a load source change only and receive "
            "no upland efficiency treatment."
        ),
    }


# ---------------------------------------------------------------- risk

def risk_review(
    *,
    uses_eqip: bool | None = None,
    needs_water_infrastructure: bool | None = None,
    needs_perimeter_fencing: bool | None = None,
    grazing_plan_required: bool | None = None,
    verification_plan_written: bool | None = None,
    discussing_tree_shade: bool | None = None,
) -> dict[str, Any]:
    """Raise the flags the intake call identified. Unanswered is not clear."""
    answers = {
        "eqip_stacking": uses_eqip,
        "water_infrastructure": needs_water_infrastructure,
        "perimeter_fencing": needs_perimeter_fencing,
        "grazing_plan_required": grazing_plan_required,
        "verification_burden": verification_plan_written,
        "silvopasture_definition": discussing_tree_shade,
    }
    raised, unanswered = [], []
    for flag in P.RISK_FLAGS:
        a = answers.get(flag.key)
        if a is None:
            unanswered.append({"flag": flag.key, "question": flag.question})
            continue
        # verification_burden is the inverse: a written plan is the good case
        triggered = (not a) if flag.key == "verification_burden" else bool(a)
        if triggered:
            raised.append({
                "flag": flag.key,
                "question": flag.question,
                "why_it_matters": flag.why_it_matters,
                "blocks_deal": flag.blocks_deal,
            })
    blocking = [r for r in raised if r["blocks_deal"]]
    return {
        "raised": raised,
        "unanswered": unanswered,
        "blocking": [r["flag"] for r in blocking],
        "clear_to_proceed": not blocking and not unanswered,
        "note": (
            "An unanswered flag is not a cleared flag. Screening is not "
            "complete until every question has an answer from the field."
        ),
    }

# ---------------------------------------------------------------- alternatives

# Practices whose unit is not an acre of the farm's own cropland cannot be
# compared like-for-like, and practices that need site features the farm may
# not have are flagged rather than silently ranked above the contract path.
SITE_DEPENDENT = {
    "Forest Buffer": "requires stream frontage",
    "Forest Buffer - Narrow": "requires stream frontage",
    "Forest Buffer-Streamside with Exclusion Fencing": "requires stream frontage and livestock",
    "Forest Buffer-Narrow with Exclusion Fencing": "requires stream frontage and livestock",
    "Grass Buffer": "requires stream frontage",
    "Grass Buffer - Narrow": "requires stream frontage",
    "Grass Buffer-Streamside with Exclusion Fencing": "requires stream frontage and livestock",
    "Grass Buffer-Narrow with Exclusion Fencing": "requires stream frontage and livestock",
    "Barnyard Runoff Control": "requires a barnyard",
    "Animal Waste Management System": "requires confined livestock",
    "Dairy Precision Feeding and/or Forage Management": "requires a dairy herd",
    "Loafing Lot Management": "requires a loafing lot",
    "Horse Pasture Management": "requires horses",
    "Manure Transport": "requires surplus manure",
    "Lagoon Covers": "requires a lagoon",
    "Poultry Litter Amendments (alum, for example)": "requires poultry",
    "Animal mortality disposal by composting": "requires livestock mortality",
}


def rank_alternatives(
    db_path: str, *, county: str, limit: int = 12,
    max_cost_per_lb: float = 1000.0,
) -> dict[str, Any]:
    """Every agricultural practice with rate data in this county, by $/lb N.

    Surfaces what the contracted pathway is NOT capturing. Site-dependent
    practices are labelled so a cheap row that the farm cannot physically
    host is not mistaken for an available option.
    """
    with _connect(db_path) as con:
        rows = con.execute("""
            SELECT bmp_name, unit, cost_per_unit, tn_lb_per_unit, tn_cost_per_lb,
                   tp_lb_per_unit
            FROM bmp_rates
            WHERE county = ? AND sector = 'Agriculture' AND tier = 'Primary'
              AND tn_lb_per_unit > 0 AND tn_cost_per_lb <= ?
            ORDER BY tn_cost_per_lb ASC LIMIT ?""",
            (county, max_cost_per_lb, int(limit))).fetchall()
    if not rows:
        raise ScreeningError(f"No agricultural rate data for county {county!r}.")

    out = []
    for r in rows:
        d = dict(r)
        d["site_requirement"] = SITE_DEPENDENT.get(r["bmp_name"])
        d["generally_available"] = r["bmp_name"] not in SITE_DEPENDENT
        d["free_or_negative_cost"] = (r["tn_cost_per_lb"] or 0) <= 0
        out.append(d)
    return {
        "county": county,
        "practices": out,
        "note": (
            "Ranked by CAST cost per pound of nitrogen. A practice marked "
            "with a site_requirement cannot be assumed available on a given "
            "farm; confirm with the field before comparing it to the "
            "contracted pathway."
        ),
    }


def _alternatives_note(db_path: str, county: str, chosen_lb_n_per_acre: float):
    """What the contracted pathway is leaving on the table, if anything."""
    try:
        ranked = rank_alternatives(db_path, county=county, limit=40)
    except ScreeningError:
        return None
    better = [
        p for p in ranked["practices"]
        if (p["tn_lb_per_unit"] or 0) > chosen_lb_n_per_acre * 1.5
    ][:5]
    if not better:
        return {"note": "No practice on file materially out-yields the "
                        "contracted pathway in this county.", "candidates": []}
    return {
        "note": (
            f"The contracted pathway yields {chosen_lb_n_per_acre:.1f} lb N "
            f"per acre here. The practices below yield materially more. They "
            "are not necessarily available on this farm -- check "
            "site_requirement -- and the contract may require the pathway "
            "regardless. Surfaced so the trade-off is explicit."
        ),
        "candidates": [
            {"practice": p["bmp_name"], "tn_lb_per_unit": p["tn_lb_per_unit"],
             "tn_cost_per_lb": p["tn_cost_per_lb"],
             "site_requirement": p["site_requirement"]}
            for p in better
        ],
    }

# ---------------------------------------------------------------- bundles

def screen_practice_bundle(
    db_path: str,
    *,
    county: str,
    practices: list[dict],
    hgmr: str | None = None,
    prior_land_use: str = "cropland",
) -> dict[str, Any]:
    """Screen an arbitrary set of practices on one farm.

    `practices` is a list of {"practice": str, "units": float} -- whatever
    the farm is actually going to implement, in whatever combination. Each
    entry is priced from that county's own rate row.

    Buffers are routed through the buffer rules (sheet selection, the 35 ft
    cliff, HGMR) rather than treated as a flat per-acre practice, so a
    bundle containing a buffer still gets the alignment checks.
    """
    if not practices:
        raise ScreeningError(
            "No practices supplied. Pass a list of "
            '{"practice": name, "units": number}.')

    lines: list[dict[str, Any]] = []
    tn = tp = tss = cast_cost = 0.0
    warnings: list[str] = []

    for item in practices:
        name = item.get("practice")
        units = item.get("units")
        if not name or units is None:
            raise ScreeningError(
                f"Each entry needs 'practice' and 'units'. Got: {item!r}")
        if units <= 0:
            raise ScreeningError(f"Units for {name!r} must be positive.")

        is_buffer = "Buffer" in name
        if is_buffer:
            width = item.get("width_ft")
            if width is None:
                raise ScreeningError(
                    f"{name!r} is a buffer practice, so width_ft is required. "
                    f"Below {CR.BUFFER_MIN_WIDTH_FT} ft only the narrow "
                    "practice qualifies and no upland efficiency applies.")
            block = _screen_buffer(
                db_path, county=county, buffer_acres=units,
                buffer_width_ft=width, hgmr=hgmr,
                prior_land_use=item.get("prior_land_use", prior_land_use))
            if block["practice"] != name:
                warnings.append(
                    f"Requested {name!r} but the rules select "
                    f"{block['practice']!r} for a {block['width_class']} "
                    f"buffer on {item.get('prior_land_use', prior_land_use)} "
                    f"(sheet {block['sheet']}). Using the rules.")
            tn += block["tn_lb"]; tp += block["tp_lb"]
            tss += block.get("tss_lb", 0.0)
            cast_cost += block["cast_cost"]
            lines.append({
                "practice": block["practice"], "requested_as": name,
                "units": units, "unit": "Acres in Buffers",
                "tn_lb": block["tn_lb"], "tp_lb": block["tp_lb"],
                "tss_lb": block.get("tss_lb", 0.0),
                "cast_cost": block["cast_cost"],
                "buffer_detail": block, "routed_through": "buffer rules",
            })
            continue

        rate = county_rate(db_path, county, name)
        l_tn = (rate["tn_lb_per_unit"] or 0.0) * units
        l_tp = (rate["tp_lb_per_unit"] or 0.0) * units
        l_tss = (rate["tss_lb_per_unit"] or 0.0) * units
        l_cost = (rate["cost_per_unit"] or 0.0) * units
        tn += l_tn; tp += l_tp; tss += l_tss; cast_cost += l_cost
        lines.append({
            "practice": name, "units": units, "unit": rate["unit"],
            "tn_lb_per_unit": rate["tn_lb_per_unit"],
            "tn_lb": round(l_tn, 2), "tp_lb": round(l_tp, 2),
            "tss_lb": round(l_tss, 2), "cast_cost": round(l_cost, 2),
            "arithmetic": (
                f"{rate['tn_lb_per_unit']:.4f} lb N/{rate['unit']} x "
                f"{units:g} = {l_tn:,.2f} lb N"),
            "source": f"CAST county rate, {rate['geography_full']}",
        })

    return {
        "county": county,
        "practice_count": len(lines),
        "lines": lines,
        "warnings": warnings,
        "totals": {
            "tn_lb_per_year": round(tn, 2),
            "tp_lb_per_year": round(tp, 2),
            "tss_lb_per_year": round(tss, 2),
            "tn_lb_over_commitment": round(tn * P.COMMITMENT_YEARS, 2),
            "commitment_years": P.COMMITMENT_YEARS,
        },
        "cost": {
            "total_cost": round(cast_cost, 2),
            "basis": P.COST_BASIS,
            "cost_per_lb_n": round(cast_cost / tn, 2) if tn else None,
            "cost_per_lb_n_over_commitment": (
                round(cast_cost / (tn * P.COMMITMENT_YEARS), 2) if tn else None),
        },
        "stacking_warning": (
            "Reductions from practices applied to the SAME acres do not "
            "simply add. CAST applies sequential treatment: the second "
            "practice acts on the load the first one left behind. These "
            "totals assume the practices act on distinct acres. Where they "
            "overlap, confirm the stacked result in CAST before claiming it."
        ),
    }
