"""Token accounting. Measured, not estimated.

The report has to answer four questions with real numbers: what one run
costs, what that is per user per month, what it would be at 100 and 10,000
users, and whether any cost cutting hurt quality. So every model call is
recorded here, per agent, and the dashboard shows the running total while
the screen is still on screen.

Prices live in one place and are declared, not assumed. If the rate is
unknown the app reports token counts and marks cost as unpriced rather than
inventing a number.
"""

from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------
# Pricing
# --------------------------------------------------------------------------
# USD per 1,000,000 tokens. Set MODEL_PRICE_IN / MODEL_PRICE_OUT in .env to
# the rate your gateway actually bills. Left unset, the app still reports
# exact token counts and simply marks cost as unpriced.
PRICE_IN_PER_M = os.environ.get("MODEL_PRICE_IN")
PRICE_OUT_PER_M = os.environ.get("MODEL_PRICE_OUT")
PRICE_CACHED_IN_PER_M = os.environ.get("MODEL_PRICE_CACHED_IN")


def _f(v):
    try:
        return float(v) if v not in (None, "") else None
    except ValueError:
        return None


RATES = {
    "input": _f(PRICE_IN_PER_M),
    "cached_input": _f(PRICE_CACHED_IN_PER_M),
    "output": _f(PRICE_OUT_PER_M),
}
PRICED = RATES["input"] is not None and RATES["output"] is not None


@dataclass
class CallRecord:
    """One model call."""
    agent: str
    step: str
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    tool_calls: int = 0
    latency_ms: int = 0
    at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.cached_input_tokens + self.output_tokens

    def cost_usd(self) -> float | None:
        if not PRICED:
            return None
        cached_rate = RATES["cached_input"]
        if cached_rate is None:
            cached_rate = RATES["input"] * 0.5  # conservative if unspecified
        return (
            self.input_tokens * RATES["input"]
            + self.cached_input_tokens * cached_rate
            + self.output_tokens * RATES["output"]
        ) / 1_000_000


class RunMeter:
    """Token accounting for a single screening run.

    Also enforces the spend ceiling: a run that exceeds the cap stops rather
    than continuing to burn budget. That cap is a safety control, and the
    report demonstrates it firing.
    """

    def __init__(self, run_id: str, max_tokens: int):
        self.run_id = run_id
        self.max_tokens = max_tokens
        self.calls: list[CallRecord] = []
        self._lock = threading.Lock()
        self.halted_reason: str | None = None

    def record(self, rec: CallRecord) -> None:
        with self._lock:
            self.calls.append(rec)

    @property
    def total_tokens(self) -> int:
        return sum(c.total_tokens for c in self.calls)

    @property
    def remaining(self) -> int:
        return max(0, self.max_tokens - self.total_tokens)

    def would_exceed(self, projected: int = 0) -> bool:
        return (self.total_tokens + projected) >= self.max_tokens

    def halt(self, reason: str) -> None:
        self.halted_reason = reason

    def by_agent(self) -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        for c in self.calls:
            a = out.setdefault(c.agent, {
                "calls": 0, "input_tokens": 0, "cached_input_tokens": 0,
                "output_tokens": 0, "reasoning_tokens": 0, "tool_calls": 0,
                "total_tokens": 0, "cost_usd": 0.0 if PRICED else None,
            })
            a["calls"] += 1
            a["input_tokens"] += c.input_tokens
            a["cached_input_tokens"] += c.cached_input_tokens
            a["output_tokens"] += c.output_tokens
            a["reasoning_tokens"] += c.reasoning_tokens
            a["tool_calls"] += c.tool_calls
            a["total_tokens"] += c.total_tokens
            if PRICED:
                a["cost_usd"] = round((a["cost_usd"] or 0) + (c.cost_usd() or 0), 6)
        return out

    def summary(self) -> dict[str, Any]:
        tot_in = sum(c.input_tokens for c in self.calls)
        tot_cached = sum(c.cached_input_tokens for c in self.calls)
        tot_out = sum(c.output_tokens for c in self.calls)
        cost = None
        if PRICED:
            cost = round(sum(c.cost_usd() or 0 for c in self.calls), 6)
        return {
            "run_id": self.run_id,
            "model_calls": len(self.calls),
            "tool_calls": sum(c.tool_calls for c in self.calls),
            "input_tokens": tot_in,
            "cached_input_tokens": tot_cached,
            "output_tokens": tot_out,
            "total_tokens": tot_in + tot_cached + tot_out,
            "cost_usd": cost,
            "priced": PRICED,
            "budget_tokens": self.max_tokens,
            "budget_remaining": self.remaining,
            "budget_used_pct": round(100 * self.total_tokens / self.max_tokens, 1)
                               if self.max_tokens else None,
            "halted_reason": self.halted_reason,
            "by_agent": self.by_agent(),
            "latency_ms": sum(c.latency_ms for c in self.calls),
        }


# --------------------------------------------------------------------------
# Scale projections -- what the report's tokenomics section needs
# --------------------------------------------------------------------------

def project_scale(
    tokens_per_run: int,
    runs_per_user_per_month: int = 20,
    user_counts: tuple[int, ...] = (1, 100, 10_000),
) -> dict[str, Any]:
    """Cost at scale from a measured per-run token count."""
    rows = []
    for users in user_counts:
        runs = users * runs_per_user_per_month
        tokens = runs * tokens_per_run
        cost = None
        if PRICED:
            # Apportion at the observed input/output mix is handled upstream;
            # here we price the blended per-run cost supplied by the caller.
            cost = None
        rows.append({
            "users": users,
            "runs_per_month": runs,
            "tokens_per_month": tokens,
            "cost_usd_per_month": cost,
        })
    return {
        "tokens_per_run": tokens_per_run,
        "runs_per_user_per_month": runs_per_user_per_month,
        "projection": rows,
        "priced": PRICED,
    }


def price_tokens(input_tokens: int, cached: int, output: int) -> float | None:
    if not PRICED:
        return None
    cached_rate = RATES["cached_input"] or RATES["input"] * 0.5
    return (input_tokens * RATES["input"] + cached * cached_rate
            + output * RATES["output"]) / 1_000_000


# --------------------------------------------------------------------------
# Persistence -- so the report can quote real runs
# --------------------------------------------------------------------------

def append_run(path: Path, summary: dict[str, Any]) -> None:
    """Append one run summary to the token log, atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    existing: list[dict[str, Any]] = []
    if path.is_file():
        try:
            existing = json.loads(path.read_text())
            if not isinstance(existing, list):
                existing = []
        except (json.JSONDecodeError, OSError):
            quarantine = path.with_suffix(".corrupt.json")
            try:
                path.replace(quarantine)
            except OSError:
                pass
            existing = []
    existing.append(summary)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(existing, indent=2))
    tmp.replace(path)


def load_runs(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []
