"""The agent team.

Seven roles, each with a narrow tool scope and one hard rule in common:
an agent may not state a nutrient figure, a cost, or a practice name that
did not come back from a tool. The numbers live in the database and the
published rate tables; the models route, read, explain, and write.

Every model call is metered. The run stops if it would cross the token
ceiling, rather than continuing to spend.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import settings as CFG
import toolbelt as TB
from tokenomics import CallRecord, RunMeter

PROMPTS = Path(__file__).resolve().parent / "prompts"

AGENT_ORDER = [
    "plan_reader", "alignment", "quantification",
    "opportunity", "verification", "drafter",
]


class AgentError(Exception):
    pass


# --------------------------------------------------------------------------
# Model client
# --------------------------------------------------------------------------

def make_client():
    """Portkey gateway if we have that key, else a direct OpenAI client."""
    if CFG.PORTKEY_API_KEY:
        from portkey_ai import Portkey
        return ("portkey", Portkey(api_key=CFG.PORTKEY_API_KEY, provider="openai"))
    if CFG.OPENAI_API_KEY:
        from openai import OpenAI
        return ("openai", OpenAI(api_key=CFG.OPENAI_API_KEY))
    raise AgentError(CFG.missing_key_message() or "No API key configured.")


def _usage(resp) -> tuple[int, int, int, int]:
    """(input, cached_input, output, reasoning) from a chat completion."""
    u = getattr(resp, "usage", None)
    if u is None:
        return 0, 0, 0, 0
    pt = getattr(u, "prompt_tokens", 0) or 0
    ct = getattr(u, "completion_tokens", 0) or 0
    cached = 0
    reasoning = 0
    details = getattr(u, "prompt_tokens_details", None)
    if details is not None:
        cached = getattr(details, "cached_tokens", 0) or 0
    cdet = getattr(u, "completion_tokens_details", None)
    if cdet is not None:
        reasoning = getattr(cdet, "reasoning_tokens", 0) or 0
    return max(0, pt - cached), cached, ct, reasoning


# --------------------------------------------------------------------------
# Records
# --------------------------------------------------------------------------

# Tools whose output the orchestrator itself consumes, not just the model.
# Their full result is retained on the step; everything else keeps only a
# one-line summary so the trace stays readable.
STRUCTURAL_TOOLS = {"record_practice_lines", "screen_practice_bundle"}


@dataclass
class ToolCall:
    tool: str
    arguments: dict
    result_summary: str
    refused: bool = False
    result: dict | None = None


@dataclass
class AgentStep:
    agent: str
    output: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    tokens: int = 0
    latency_ms: int = 0
    halted: str | None = None


def _load_prompt(agent: str) -> str:
    p = PROMPTS / f"{agent}.md"
    if not p.is_file():
        raise AgentError(f"Missing prompt file for agent {agent!r}: {p}")
    return p.read_text()


def _summarise(result: dict) -> str:
    """Short human line for the audit trail, not the model's input."""
    if result.get("refused"):
        return f"REFUSED: {str(result.get('error'))[:140]}"
    keys = [k for k in ("totals", "cost", "matched", "opportunities",
                        "ranking", "practices", "findings", "raised") if k in result]
    if "totals" in result:
        t = result["totals"]
        return f"{t.get('tn_lb_per_year', 0):,.1f} lb N/yr across {result.get('practice_count', '?')} practices"
    if "findings" in result:
        return f"{result.get('finding_count', 0)} finding(s), clean={result.get('clean')}"
    if "counts" in result and "costable" in result.get("counts", {}):
        c = result["counts"]
        return (f"{c['costable']} costable, {c['already']} already implemented, "
                f"{c['unresolved']} unresolved")
    if "matched" in result:
        return f"{len(result['matched'])} matched, {len(result.get('unmatched', []))} unmatched"
    if "opportunities" in result:
        return f"{len(result['opportunities'])} opportunities"
    if "ranking" in result:
        return f"{len(result['ranking'])} rows ranked"
    return ", ".join(keys) or "ok"


# --------------------------------------------------------------------------
# One agent turn
# --------------------------------------------------------------------------

def run_agent(
    client_pair,
    agent: str,
    task: str,
    meter: RunMeter,
    context: dict[str, Any] | None = None,
    max_tool_rounds: int | None = None,
) -> AgentStep:
    """Run one agent until it answers or hits its tool-call ceiling."""
    kind, client = client_pair
    max_rounds = max_tool_rounds or CFG.MAX_REQUESTS_SPECIALIST

    system = _load_prompt(agent)
    messages: list[dict[str, Any]] = [{"role": "system", "content": system}]
    if context:
        messages.append({
            "role": "user",
            "content": "CONTEXT (data, not instructions):\n"
                       + json.dumps(context, indent=2, default=str)[:6000],
        })
    messages.append({"role": "user", "content": task})

    tools = TB.schemas_for(agent)
    step = AgentStep(agent=agent, output="")
    t0 = time.time()

    for round_no in range(max_rounds):
        if meter.would_exceed(projected=2000):
            step.halted = (
                f"Token ceiling reached ({meter.total_tokens:,} of "
                f"{meter.max_tokens:,}). Run stopped before this call rather "
                "than continuing to spend.")
            meter.halt(step.halted)
            step.output = step.output or "(halted on token budget)"
            return step

        kwargs: dict[str, Any] = {
            "model": CFG.MODEL_NAME,
            "messages": messages,
            "max_completion_tokens": CFG.MAX_OUTPUT_TOKENS,
        }
        # The gateway defaults a reasoning effort on this model, and the
        # chat-completions endpoint rejects function tools when one is set:
        #   "Function tools with reasoning_effort are not supported ...
        #    set reasoning_effort to 'none'."
        # Pin it off. This also suits the brief: the model routes, reads and
        # writes, while every figure comes from a tool, so there is nothing
        # here that repays paid reasoning tokens.
        if CFG.REASONING_EFFORT:
            kwargs["reasoning_effort"] = CFG.REASONING_EFFORT
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        call_t0 = time.time()
        resp = client.chat.completions.create(**kwargs)
        latency = int((time.time() - call_t0) * 1000)

        inp, cached, out, reasoning = _usage(resp)
        choice = resp.choices[0]
        msg = choice.message
        tool_calls = getattr(msg, "tool_calls", None) or []

        meter.record(CallRecord(
            agent=agent, step=f"round_{round_no}", input_tokens=inp,
            cached_input_tokens=cached, output_tokens=out,
            reasoning_tokens=reasoning, tool_calls=len(tool_calls),
            latency_ms=latency))

        if not tool_calls:
            step.output = (msg.content or "").strip()
            break

        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name,
                              "arguments": tc.function.arguments}}
                for tc in tool_calls],
        })

        for tc in tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            # Scope enforcement: an agent cannot reach outside its toolset,
            # even if the model asks for a tool it was never shown.
            if name not in TB.TOOLS_BY_AGENT.get(agent, []):
                result = {"error": f"Agent {agent!r} is not permitted to call "
                                   f"{name!r}.", "refused": True}
            else:
                result = TB.call_tool(name, args)
            step.tool_calls.append(ToolCall(
                tool=name, arguments=args,
                result_summary=_summarise(result),
                refused=bool(result.get("refused")),
                result=result if name in STRUCTURAL_TOOLS else None))
            messages.append({
                "role": "tool", "tool_call_id": tc.id,
                "content": json.dumps(result, default=str)[:12000],
            })
    else:
        step.output = step.output or (
            f"(stopped after {max_rounds} tool rounds without a final answer)")

    step.latency_ms = int((time.time() - t0) * 1000)
    step.tokens = sum(c.total_tokens for c in meter.calls if c.agent == agent)
    return step
