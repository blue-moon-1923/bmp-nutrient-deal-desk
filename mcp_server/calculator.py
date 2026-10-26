"""Deterministic credit arithmetic. No model touches these numbers.

Pipeline, in the order the regulation imposes it:

    baseline eligibility  ->  gross reduction  ->  delivery factor
      ->  5% certification retirement  ->  release schedule over time
      ->  price by BUYER's regulatory driver  ->  deal economics

Each step returns its own inputs alongside its output so the audit trail can
show the arithmetic, not just the answer.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import va_rules as R


class RuleViolation(Exception):
    """Raised when a request is outside what the regulation permits."""


# ---------------------------------------------------------------- baseline

def check_baseline(
    *,
    pre_use: str,
    post_use: str,
    tributary: str,
    practice_year: int,
    acres_within_35ft_perennial: float = 0.0,
    wip_baseline_met: bool = False,
    follows_practice_standard: bool = True,
    structural_bmp: bool = False,
    financial_assurance: bool = False,
) -> dict[str, Any]:
    """Run every gate in 9VAC25-900-100/110. Blocking failures stop the deal."""
    for use in (pre_use, post_use):
        if use not in R.LOADING_RATES:
            raise RuleViolation(
                f"Unknown land use {use!r}. Known: {sorted(R.LOADING_RATES)}"
            )
    if tributary not in R.DELIVERY_FACTORS:
        raise RuleViolation(
            f"Unknown tributary {tributary!r}. Known: {sorted(R.DELIVERY_FACTORS)}"
        )

    southern = tributary == "southern_rivers"
    cutoff_year = 2009 if southern else 2005
    cutoff_label = R.SOUTHERN_RIVERS_PRACTICE_CUTOFF if southern else R.BAY_PRACTICE_CUTOFF

    findings = []

    too_old = practice_year < cutoff_year
    findings.append({
        "check": "practice_start_date",
        "passed": not too_old,
        "blocking": True,
        "detail": (
            f"Practice dated {practice_year}; cutoff is {cutoff_label}. "
            + ("Pre-dates the cutoff, so it cannot generate credits."
               if too_old else "After the cutoff.")
        ),
    })

    findings.append({
        "check": "wip_baseline_met",
        "passed": bool(wip_baseline_met),
        "blocking": True,
        "detail": (
            "WIP/TMDL baseline reduction confirmed as achieved."
            if wip_baseline_met else
            "Baseline under 9VAC25-900-100 not confirmed. Credits accrue only "
            "above baseline, so nothing can be certified until this is met."
        ),
    })

    intensifies = R.is_more_intensive(pre_use, post_use)
    findings.append({
        "check": "more_intensive",
        "passed": not intensifies,
        "blocking": True,
        "detail": (
            f"{pre_use} -> {post_use} is a more intensive use; 9VAC25-900-110 D "
            "generates no credits." if intensifies
            else f"{pre_use} -> {post_use} is not an intensification."
        ),
    })

    findings.append({
        "check": "practice_standard",
        "passed": bool(follows_practice_standard),
        "blocking": True,
        "detail": (
            "Follows VACS BMP Manual / NRCS FOTG."
            if follows_practice_standard else
            "Practice does not follow VACS BMP Manual or FOTG, so department "
            "removal efficiencies do not apply."
        ),
    })

    findings.append({
        "check": "perennial_buffer",
        "passed": True,  # informational: acreage is excluded, not the deal
        "blocking": False,
        "detail": (
            f"{acres_within_35ft_perennial:g} acres lie within "
            f"{R.PERENNIAL_BUFFER_EXCLUSION_FT} ft of perennial flow and are "
            "excluded from the creditable area."
            if acres_within_35ft_perennial else
            "No acreage reported within 35 ft of perennial flow."
        ),
    })

    if structural_bmp:
        findings.append({
            "check": "financial_assurance",
            "passed": bool(financial_assurance),
            "blocking": False,
            "detail": (
                "Financial assurance approved."
                if financial_assurance else
                "Structural BMP without approved financial assurance: credits "
                "may be certified but DEQ will not RELEASE them until it is."
            ),
        })

    blocking_failures = [f for f in findings if f["blocking"] and not f["passed"]]
    return {
        "eligible": not blocking_failures,
        "blocking_failures": [f["check"] for f in blocking_failures],
        "findings": findings,
        "cutoff_applied": cutoff_label,
        "excluded_acres": acres_within_35ft_perennial,
    }


# ---------------------------------------------------------------- credits

@dataclass
class CreditResult:
    acres_credited: float
    pre_use: str
    post_use: str
    tributary: str
    n_rate_pre: float
    n_rate_post: float
    p_rate_pre: float
    p_rate_post: float
    n_gross_lb: float
    p_gross_lb: float
    delivery_n: float
    delivery_p: float
    n_delivered_lb: float
    p_delivered_lb: float
    retirement_pct: float
    n_retired_lb: float
    p_retired_lb: float
    n_certified_lb: float
    p_certified_lb: float
    rate_basis: str


def calculate_credits(
    *,
    pre_use: str,
    post_use: str,
    acres: float,
    tributary: str,
    acres_within_35ft_perennial: float = 0.0,
) -> dict[str, Any]:
    """Land use conversion credits per 9VAC25-900-110 D, then the 5% retirement.

    credits/acre = pre-conversion load/acre - post-conversion load/acre
    total        = credits/acre * creditable acreage
    """
    if acres <= 0:
        raise RuleViolation("Acreage must be positive.")
    if R.is_more_intensive(pre_use, post_use):
        raise RuleViolation(
            f"{pre_use} -> {post_use} is a more intensive land use. "
            "9VAC25-900-110 D: no credits are generated."
        )

    creditable = max(0.0, acres - acres_within_35ft_perennial)
    if creditable == 0:
        raise RuleViolation(
            "All acreage falls within 35 ft of perennial flow and is excluded."
        )

    pre, post = R.LOADING_RATES[pre_use], R.LOADING_RATES[post_use]
    df = R.DELIVERY_FACTORS[tributary]

    n_gross = (pre.n_lb_ac_yr - post.n_lb_ac_yr) * creditable
    p_gross = (pre.p_lb_ac_yr - post.p_lb_ac_yr) * creditable

    n_delivered = n_gross * df["n"]
    p_delivered = p_gross * df["p"]

    n_retired = n_delivered * R.CERTIFICATION_RETIREMENT
    p_retired = p_delivered * R.CERTIFICATION_RETIREMENT

    result = CreditResult(
        acres_credited=round(creditable, 3),
        pre_use=pre_use, post_use=post_use, tributary=tributary,
        n_rate_pre=pre.n_lb_ac_yr, n_rate_post=post.n_lb_ac_yr,
        p_rate_pre=pre.p_lb_ac_yr, p_rate_post=post.p_lb_ac_yr,
        n_gross_lb=round(n_gross, 2), p_gross_lb=round(p_gross, 2),
        delivery_n=df["n"], delivery_p=df["p"],
        n_delivered_lb=round(n_delivered, 2), p_delivered_lb=round(p_delivered, 2),
        retirement_pct=R.CERTIFICATION_RETIREMENT,
        n_retired_lb=round(n_retired, 2), p_retired_lb=round(p_retired, 2),
        n_certified_lb=round(n_delivered - n_retired, 2),
        p_certified_lb=round(p_delivered - p_retired, 2),
        rate_basis=f"{pre.basis} loading rates; {df['basis']} delivery factors",
    )
    out = asdict(result)
    out["arithmetic"] = [
        f"N: ({pre.n_lb_ac_yr} - {post.n_lb_ac_yr}) lb/ac/yr x {creditable:g} ac "
        f"= {n_gross:,.2f} lb gross",
        f"N: {n_gross:,.2f} x {df['n']} delivery = {n_delivered:,.2f} lb delivered",
        f"N: less {R.CERTIFICATION_RETIREMENT:.0%} retired at certification "
        f"= {n_delivered - n_retired:,.2f} lb certified",
        f"P: ({pre.p_lb_ac_yr} - {post.p_lb_ac_yr}) lb/ac/yr x {creditable:g} ac "
        f"= {p_gross:,.2f} lb gross",
        f"P: {p_gross:,.2f} x {df['p']} delivery = {p_delivered:,.2f} lb delivered",
        f"P: less {R.CERTIFICATION_RETIREMENT:.0%} retired at certification "
        f"= {p_delivered - p_retired:,.2f} lb certified",
    ]
    out["caveat"] = (
        "Loading rates and delivery factors are REFERENCE values. "
        "9VAC25-900-110 requires the levels in the applicable WIP or approved "
        "TMDL. Replace before any filing."
    )
    return out


# ---------------------------------------------------------------- release

def release_schedule(
    *,
    certified_lb: float,
    project_type: str = "conversion",
    afforestation: bool = False,
) -> dict[str, Any]:
    """When certified credits actually become sellable (9VAC25-900-90).

    This is the step a spreadsheet usually skips. Credits are an asset with a
    delivery schedule, not a lump sum.
    """
    if project_type not in ("conversion", "restoration"):
        raise RuleViolation("project_type must be 'conversion' or 'restoration'.")

    tranches = []
    if project_type == "conversion":
        running = 0.0
        for key, pct, condition in R.RELEASE_SCHEDULE_CONVERSION:
            if key == "afforestation_planted" and not afforestation:
                continue
            lb = certified_lb * pct
            running += lb
            tranches.append({
                "milestone": key, "share": pct, "lb": round(lb, 2),
                "condition": condition, "cumulative_lb": round(running, 2),
            })
        if not afforestation:
            # The afforestation tranche folds into performance criteria.
            shortfall = certified_lb - running
            if shortfall > 0.01:
                tranches[-1]["lb"] = round(tranches[-1]["lb"] + shortfall, 2)
                tranches[-1]["cumulative_lb"] = round(certified_lb, 2)
                tranches[-1]["condition"] += (
                    " (includes the afforestation share, as no afforestation "
                    "is planned)"
                )
    else:
        tranches.append({
            "milestone": "construction_complete", "share": 0.25,
            "lb": round(certified_lb * 0.25, 2),
            "condition": "Construction complete and conditions verified",
            "cumulative_lb": round(certified_lb * 0.25, 2),
        })
        tranches.append({
            "milestone": "monitoring_years", "share": 0.75,
            "lb": round(certified_lb * 0.75, 2),
            "condition": (
                "25% per monitoring year with a bankfull event, or 10% if the "
                f"channel is stable without one. No further release after "
                f"monitoring year {R.RESTORATION_BANKFULL_STALL_YEAR} until a "
                "bankfull event occurs."
            ),
            "cumulative_lb": round(certified_lb, 2),
        })

    return {
        "project_type": project_type,
        "certified_lb": round(certified_lb, 2),
        "immediately_sellable_lb": tranches[0]["lb"] if tranches else 0.0,
        "immediately_sellable_pct": tranches[0]["share"] if tranches else 0.0,
        "tranches": tranches,
        "note": (
            "Only credits DEQ has released are available for exchange "
            "(9VAC25-900-90). Certified is not the same as sellable."
        ),
    }


# ---------------------------------------------------------------- pricing

def price_credits(
    *,
    nutrient: str,
    pounds: float,
    buyer_driver: str,
) -> dict[str, Any]:
    """Price by the BUYER's regulatory driver -- never by seller preference.

    buyer_driver is the thing that decides which market a credit belongs to.
    Getting it wrong is a ~3,000x error, so this refuses to guess.
    """
    nutrient = nutrient.upper()
    if nutrient not in ("N", "P"):
        raise RuleViolation("nutrient must be 'N' or 'P'.")

    driver_map = {
        "impervious_offset": "perpetual_p_impervious",
        "ms4_perpetual": "perpetual_p_study_range",
        "point_source": "point_source_p" if nutrient == "P" else "point_source_n",
        "offset_fund": "offset_fund_p" if nutrient == "P" else "offset_fund_n",
    }
    if buyer_driver not in driver_map:
        raise RuleViolation(
            f"Unknown buyer_driver {buyer_driver!r}. Must be one of "
            f"{sorted(driver_map)}. The buyer's regulatory obligation "
            "determines the credit type and therefore the price; it cannot "
            "be assumed."
        )

    key = driver_map[buyer_driver]
    price = R.PRICES[key]
    if price.nutrient != nutrient:
        raise RuleViolation(
            f"Driver {buyer_driver!r} prices {price.nutrient}, not {nutrient}. "
            f"{price.label} is valid for: {price.valid_for}"
        )

    return {
        "nutrient": nutrient,
        "pounds": round(pounds, 2),
        "buyer_driver": buyer_driver,
        "price_label": price.label,
        "price_low": price.low,
        "price_high": price.high,
        "unit": price.unit,
        "value_low": round(pounds * price.low, 2),
        "value_high": round(pounds * price.high, 2),
        "value_midpoint": round(pounds * price.midpoint(), 2),
        "source": price.source,
        "as_of": price.as_of,
        "valid_for": price.valid_for,
        "spread_warning": R.PRICE_SPREAD_NOTE,
    }
