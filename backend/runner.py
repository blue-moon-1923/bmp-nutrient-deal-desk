"""Orchestration: run a screening end to end and record what happened.

The sequence mirrors the human workflow it replaces. A plan arrives from the
field, it gets read, checked against specifications, quantified, compared
against what else the county offers, given a verification schedule, and
written up. The review desk makes the call last, having seen all of it.

Specialists that do not depend on each other run concurrently.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import settings as CFG
import toolbelt as TB
from agents import AgentStep, make_client, run_agent
from tokenomics import RunMeter, append_run


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _run_in_thread(fn, *a, **kw):
    return await asyncio.to_thread(fn, *a, **kw)


async def screen_project(
    *,
    county: str,
    practices: list[dict] | None = None,
    plan_text: str | None = None,
    hgmr: str | None = None,
    prior_land_use: str = "cropland",
    risk_answers: dict | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Full screening run. Returns everything the dashboard and report need."""
    run_id = run_id or f"run_{uuid.uuid4().hex[:10]}"

    # The hydrogeomorphic region is a property of the site, and we know the
    # county. Fill it in rather than letting a full-width buffer be refused
    # for a value the application can derive. The UI does the same thing; a
    # caller hitting the API directly should not get a worse answer.
    hgmr_source = "supplied"
    if not hgmr and county:
        try:
            table = json.loads(
                (CFG.DATA_DIR / "county_hgmr.json").read_text())
            hit = table.get(county)
            if hit:
                hgmr = hit["hgmr"]
                hgmr_source = f"derived from {county} County ({hit['basis']})"
        except (OSError, ValueError, KeyError):
            pass
    started = _now()
    meter = RunMeter(run_id, CFG.MAX_TOKENS_PER_SCREEN)
    client = make_client()
    steps: list[AgentStep] = []

    # ---- 0. deterministic pre-checks, before any model sees the document
    injection = None
    jurisdiction = None
    privacy = None
    excerpt = None
    if plan_text:
        injection = TB.call_tool("scan_document_for_injection", {"text": plan_text})
        import plan_reader as _PR
        import redact as _RD
        jurisdiction = _PR.detect_jurisdiction(plan_text)

        # Everything above runs locally on the original. From here the
        # producer's identity is removed, and the REDACTED text is the only
        # version any model sees. Practice names, quantities, widths and the
        # county all survive; the person does not.
        privacy = _RD.redact(plan_text, keep_county=county)
        plan_text = privacy.pop("text")

        # A plan is mostly attachments. The practice schedule can start ten
        # pages in, so taking the first N characters reads the cover letter
        # and misses the schedule entirely. Pick the region that matters.
        excerpt = _PR.relevant_excerpt(plan_text)
        plan_text = excerpt.pop("text")

    risk = TB.call_tool("run_risk_review", risk_answers or {})

    # Ground truth, computed without any model. Recorded alongside the agent
    # output so the two can be compared, and so a saved project carries real
    # figures rather than whatever prose came back.
    quote = None
    extraction = None
    if practices:
        quote = TB.call_tool("screen_practice_bundle", {
            "county": county, "practices": practices,
            "hgmr": hgmr, "prior_land_use": prior_land_use})

    # ---- 1. plan reader (only if a plan was supplied)
    if plan_text:
        steps.append(await _run_in_thread(
            run_agent, client, "plan_reader",
            "Read this conservation plan and list its practices. Validate "
            "every name. Flag anything already implemented under a "
            "cost-share programme.",
            meter,
            {"county": county, "plan_text": plan_text,
             "injection_scan": injection},
        ))

    # If the plan reader extracted a costable bundle and the form supplied
    # no practice rows, price what the document actually proposes. A plan of
    # BMPs about to go in is the common case, and it has to be credited, not
    # merely discussed.
    if plan_text and steps:
        for tc in steps[-1].tool_calls:
            if tc.tool == "record_practice_lines" and tc.result:
                extraction = tc.result
                break
        if extraction and extraction.get("bundle") and not practices:
            practices = extraction["bundle"]
            quote = TB.call_tool("screen_practice_bundle", {
                "county": county, "practices": practices,
                "hgmr": hgmr, "prior_land_use": prior_land_use})

    # ---- 1b. eligibility, from the same document
    if plan_text:
        steps.append(await _run_in_thread(
            run_agent, client, "eligibility",
            "Read this document for the farm's physical features, then work "
            "out which practices it could host. Say what you could not "
            "establish and what to ask.",
            meter, {"county": county, "plan_text": plan_text},
        ))

    # ---- 2. alignment + opportunity can run together
    align_task = (
        "Check this project against the programme's specifications. Report "
        "which practice the rules select for any buffer, credit durations, "
        "and anything missing that you need."
    )
    opp_task = (
        "Identify the highest-value practices in this county that this "
        "project does not include. State every site requirement."
    )
    ctx = {"county": county, "practices": practices or [],
           "hgmr": hgmr, "prior_land_use": prior_land_use}
    if steps:
        ctx["plan_reader_findings"] = steps[0].output

    align_step, opp_step = await asyncio.gather(
        _run_in_thread(run_agent, client, "alignment", align_task, meter, ctx),
        _run_in_thread(run_agent, client, "opportunity", opp_task, meter, ctx),
    )
    steps.extend([align_step, opp_step])

    # ---- 3. quantification, after alignment has settled the practice names
    quant_ctx = dict(ctx)
    quant_ctx["alignment_findings"] = align_step.output
    quant_step = await _run_in_thread(
        run_agent, client, "quantification",
        "Produce the nutrient and cost figures for this project using "
        "screen_practice_bundle. Report the arithmetic for every line.",
        meter, quant_ctx)
    steps.append(quant_step)

    # ---- 4. verification
    ver_step = await _run_in_thread(
        run_agent, client, "verification",
        "Produce a verification schedule for these practices.",
        meter, {"county": county, "practices": practices or [],
                "alignment_findings": align_step.output})
    steps.append(ver_step)

    # ---- 5. drafter, holding no tools, writing only from what it was given
    draft_ctx = {
        "county": county,
        "quantification": quant_step.output,
        "alignment": align_step.output,
        "verification": ver_step.output,
        "opportunities": opp_step.output,
        "risk_review": risk,
        "injection_scan": injection,
    }
    draft_step = await _run_in_thread(
        run_agent, client, "drafter",
        "Write the project narrative for a funding proposal.",
        meter, draft_ctx)
    steps.append(draft_step)

    # ---- 6. review desk decides last
    desk_ctx = dict(draft_ctx)
    desk_ctx["specialist_steps"] = [
        {"agent": s.agent, "output": s.output[:1500]} for s in steps]
    desk_step = await _run_in_thread(
        run_agent, client, "review_desk",
        "Make the call on this project.",
        meter, desk_ctx, CFG.MAX_REQUESTS_BOSS)
    steps.append(desk_step)

    summary = meter.summary()
    result = {
        "run_id": run_id,
        "started_at": started,
        "finished_at": _now(),
        "county": county,
        "practices": practices or [],
        "plan_supplied": bool(plan_text),
        "injection_scan": injection,
        "jurisdiction": jurisdiction,
        "privacy": privacy,
        "excerpt": excerpt if plan_text else None,
        "risk_review": risk,
        "hgmr": hgmr,
        "hgmr_source": hgmr_source,
        "quote": quote,
        "extraction": extraction,
        "quote_totals": (quote or {}).get("totals", {}),
        "quote_cost": (quote or {}).get("cost", {}),
        "steps": [
            {
                "agent": s.agent,
                "output": s.output,
                "tokens": s.tokens,
                "latency_ms": s.latency_ms,
                "halted": s.halted,
                "tool_calls": [asdict(tc) for tc in s.tool_calls],
            }
            for s in steps
        ],
        "decision": desk_step.output,
        "tokenomics": summary,
        "model": CFG.MODEL_NAME,
    }

    append_run(CFG.OUTPUT_DIR / "token_log.json", {
        "run_id": run_id, "at": started, "county": county,
        "model": CFG.MODEL_NAME,
        "plan_supplied": bool(plan_text),
        "practice_count": len(practices or []),
        **{k: summary[k] for k in (
            "model_calls", "tool_calls", "input_tokens",
            "cached_input_tokens", "output_tokens", "total_tokens",
            "cost_usd", "latency_ms", "halted_reason")},
        "by_agent": summary["by_agent"],
    })
    return result
