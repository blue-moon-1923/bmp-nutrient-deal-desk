"""Figures for the report, read from the project's own artefacts."""
from __future__ import annotations
import json, statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"

# ---- PLACEHOLDER PRICE -------------------------------------------------
# gpt-6-luna is a course-provisioned model behind a Portkey gateway. The
# gateway returns token counts and latency but no cost field, and the rate
# was not published to students. The figures below are a PLACEHOLDER in the
# range of comparable small hosted models. Every cost in this report scales
# linearly with them.
PRICE_IN_PER_M = 0.15
PRICE_OUT_PER_M = 0.60
PRICE_IS_PLACEHOLDER = True
# ------------------------------------------------------------------------

def runs() -> list[dict]:
    p = OUT / "token_log.json"
    if not p.is_file():
        return []
    return [r for r in json.loads(p.read_text()) if r.get("total_tokens")]

R = runs()
WITH = [r for r in R if r.get("plan_supplied")]
WITHOUT = [r for r in R if not r.get("plan_supplied")]

def _m(xs): return st.mean(xs) if xs else 0

TOK = {
    "n": len(R),
    "mean": _m([r["total_tokens"] for r in R]),
    "min": min([r["total_tokens"] for r in R], default=0),
    "max": max([r["total_tokens"] for r in R], default=0),
    "input": _m([r["input_tokens"] for r in R]),
    "cached": _m([r["cached_input_tokens"] for r in R]),
    "output": _m([r["output_tokens"] for r in R]),
    "sec": _m([r["latency_ms"]/1000 for r in R]),
    "sec_min": min([r["latency_ms"]/1000 for r in R], default=0),
    "sec_max": max([r["latency_ms"]/1000 for r in R], default=0),
    "with_plan": _m([r["total_tokens"] for r in WITH]),
    "without_plan": _m([r["total_tokens"] for r in WITHOUT]),
    "n_with": len(WITH), "n_without": len(WITHOUT),
}

def cost_of(inp: float, cached: float, out: float) -> float:
    # cached input is billed at the input rate here; the gateway reports no
    # separate cached rate, so this is the conservative assumption.
    return ((inp + cached) * PRICE_IN_PER_M + out * PRICE_OUT_PER_M) / 1_000_000

COST_PER_RUN = cost_of(TOK["input"], TOK["cached"], TOK["output"])

# ---- organisation figures, from the practitioner ----
ORG = {
    "salary": 75_000, "fte_hours": 2080,
    "scoped": 250, "converted": 50,
    "hours_per_screen": 4,
    "outreach_staff": 12, "org_size": 14,
    "analyst_fte": 0.40,          # 20% of two roles
    "outreach_share": 0.35,
    "conv_before": 5, "conv_after": 2,
    "no_price": 0.40, "no_data": 0.35, "no_eqip": 0.25,
}
ORG["hourly"] = ORG["salary"] / ORG["fte_hours"]
ORG["analyst_hours"] = ORG["analyst_fte"] * ORG["fte_hours"]
ORG["volume_hours"] = ORG["scoped"] * ORG["hours_per_screen"]
ORG["analyst_cost"] = ORG["analyst_hours"] * ORG["hourly"]
ORG["review_min"] = 30
ORG["after_hours"] = ORG["scoped"] * (TOK["sec"]/60 + ORG["review_min"]) / 60
ORG["saved_hours"] = ORG["analyst_hours"] - ORG["after_hours"]
ORG["saved_pct"] = ORG["saved_hours"] / ORG["analyst_hours"]
ORG["dead_end_hours"] = ORG["analyst_hours"] * (ORG["scoped"]-ORG["converted"])/ORG["scoped"]

# runs per user per month, for the scale table
RUNS_PER_USER_MONTH = ORG["scoped"] / ORG["outreach_staff"] / 12 * 2  # 2 passes each

def scale_rows():
    rows = []
    for users in (1, ORG["outreach_staff"], 100, 10_000):
        per_month = users * RUNS_PER_USER_MONTH
        rows.append({
            "users": users,
            "runs_per_month": per_month,
            "tokens_per_month": per_month * TOK["mean"],
            "cost_per_month": per_month * COST_PER_RUN,
            "cost_per_year": per_month * COST_PER_RUN * 12,
        })
    return rows

if __name__ == "__main__":
    print(f"runs {TOK['n']} | mean {TOK['mean']:,.0f} tok | {TOK['sec']:.1f}s")
    print(f"  with plan {TOK['with_plan']:,.0f} (n={TOK['n_with']}) | without {TOK['without_plan']:,.0f} (n={TOK['n_without']})")
    print(f"  cost/run ${COST_PER_RUN:.4f}  [PLACEHOLDER price]")
    print(f"  runs/user/month {RUNS_PER_USER_MONTH:.1f}")
    for r in scale_rows():
        print(f"  {r['users']:>6,} users  {r['runs_per_month']:>10,.0f} runs/mo  "
              f"{r['tokens_per_month']:>14,.0f} tok  ${r['cost_per_month']:>10,.2f}/mo  ${r['cost_per_year']:>11,.2f}/yr")
    print(f"\n  analyst {ORG['analyst_hours']:,.0f} h  ->  {ORG['after_hours']:,.0f} h   saved {ORG['saved_hours']:,.0f} h ({ORG['saved_pct']:.0%})")
    print(f"  dead-end hours {ORG['dead_end_hours']:,.0f}  (${ORG['dead_end_hours']*ORG['hourly']:,.0f})")
