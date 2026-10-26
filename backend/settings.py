"""Configuration for the Virginia nutrient credit deal desk.

The teaching staff clone this repo into a submissions folder and keep their
.env one level ABOVE it:

    submissions/
    ├── .env                 <- their keys live here
    └── va-credit-desk/      <- this repo
        └── .env             <- or here, if you have your own

So we look in our own folder first, then the parent. First file found wins;
values already in the real environment always take precedence over both.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]

ENV_SEARCH_PATH = (
    REPO_ROOT / ".env",           # our own folder
    REPO_ROOT.parent / ".env",    # one level up (teaching staff)
)


def load_environment() -> Path | None:
    """Load the first .env found. Returns the path used, or None."""
    for candidate in ENV_SEARCH_PATH:
        if candidate.is_file():
            load_dotenv(candidate, override=False)
            return candidate
    return None


ENV_FILE_USED = load_environment()

# ---------------------------------------------------------------- model

# The course key is a Portkey gateway key. gpt-6-luna is the only model
# permitted on it, and it is a deliberately small model: this app leans on
# deterministic tools for every number, so the model only has to route,
# explain, and write. See output/tokenomics.md.
PORTKEY_API_KEY = os.environ.get("PORTKEY_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

MODEL_NAME = "gpt-6-luna"
# "none" is required on this gateway whenever function tools are sent.
REASONING_EFFORT = "none"
VERBOSITY = "low"
MAX_OUTPUT_TOKENS = 1100

# ---------------------------------------------------------------- limits

# Nothing here is tuning for its own sake. Each cap is a spend control that
# the safety section of the report demonstrates firing.
MAX_REQUESTS_SPECIALIST = 4      # tool calls one specialist may make per task
MAX_REQUESTS_BOSS = 8            # tool calls the deal desk may make per screen
MAX_DELEGATION_DEPTH = 2         # boss -> specialist -> specialist, no deeper
MAX_DELEGATIONS_PER_SCREEN = 6   # total hand-offs for one screening
MAX_TOKENS_PER_SCREEN = 220_000  # hard stop; refuses rather than overspends

# How much of a document an agent may be shown. A conservation plan runs to
# tens of thousands of characters and the practice schedule can sit ten pages
# in, so this has to be generous. The runner picks the relevant region first.
MAX_DOCUMENT_CHARS = 30_000

# ---------------------------------------------------------------- paths

DATA_DIR = REPO_ROOT / "data"
OUTPUT_DIR = REPO_ROOT / "output"
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"

DB_PATH = DATA_DIR / "va_credit_market.db"
AUDIT_PATH = OUTPUT_DIR / "audit_trail.json"


def missing_key_message() -> str | None:
    """Human-readable setup error, or None if we have what we need."""
    if PORTKEY_API_KEY or OPENAI_API_KEY:
        return None
    looked_in = "\n".join(f"  - {p}" for p in ENV_SEARCH_PATH)
    return (
        "No API key found. This app needs PORTKEY_API_KEY (preferred) or "
        "OPENAI_API_KEY.\n\nLooked for a .env file in:\n"
        f"{looked_in}\n\nCopy .env.example to .env and fill in your key."
    )
