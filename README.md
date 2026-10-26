# BMP Nutrient Deal Desk

An agent team that reads a farm's conservation plan, works out which best
management practices can actually be credited, and returns the nitrogen,
phosphorus and sediment reductions with their cost — in about half a minute,
replacing roughly four hours of manual document work.

Built for **MGT 409, AI Foundations for Managers**, Yale School of Management.
Virginia, Chesapeake Bay watershed.

---

## Run it — three commands

You need **Python 3.11 or newer**. Nothing else: no Node, no npm, no build step,
no database to download.

```bash
cd bmp-nutrient-deal-desk
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
./.venv/bin/uvicorn backend.main:app --port 8000
```

Then open **<http://127.0.0.1:8000>**

On Windows the venv paths are `.venv\Scripts\pip` and `.venv\Scripts\uvicorn`.

### The API key

The app looks for a `.env` file in **two** places, in this order:

1. this repository's own folder
2. **one level above it** — so a `.env` sitting beside the repo in a
   `submissions/` folder is found automatically

```
submissions/
├── .env                        <- your key here works
└── bmp-nutrient-deal-desk/
    ├── .env                    <- or here
    └── README.md
```

It uses `PORTKEY_API_KEY` if present, otherwise `OPENAI_API_KEY`. Copy
`.env.example` to `.env` if you need a template.

**Without a key the app still runs.** Every deterministic feature works — the
calculator, the county map, the practice ranking, the document reader, the
injection scanner. Only the agent screening needs the model.

Check what it found: <http://127.0.0.1:8000/api/health> reports which `.env`
file was loaded and which key name it is using.

---

## Try it in two minutes

Open the app and work down the left-hand panel.

### 1. The fastest thing — no tokens spent

**Practices** tab → **Example farm** → **Quick quote**

Instant, exact, free. This path calls the calculator directly and never touches
a model. It returns the same numbers the agents would.

### 2. Watch it refuse

Clear the **Buffer width** box on the Forest Buffer row → **Quick quote** again.

It refuses and explains why: below 35 ft a buffer qualifies only as a *narrow*
practice and receives no upland treatment, which changes the nitrogen answer by
more than half. The tool will not produce a figure from an assumed input.

### 3. A real conservation plan *(needs a key)*

**Conservation plan** tab → **NRCS-style Virginia plan** → **Full screening with agents**

A four-page NRCS-format plan for a 310-acre Rockingham County farm with ten
practices. The app reads the address, sets the county and hydrogeomorphic region
itself, then screens every practice. Takes about 30–60 seconds.

Watch for three things:

- **Nutrient Management** is held — the plan says its reductions were already
  reported to Virginia DEQ. That is double counting.
- **An existing CREP buffer** is held — a structural practice already in the
  ground is not additional.
- **Fence** comes back *unresolved* — a real cost, but not a creditable practice.

### 4. The safety demo *(needs a key)*

Same tab → **Sample with injection** → **Full screening with agents**

That document contains instructions addressed to the agent. They are quoted back
with line numbers and **not obeyed**.

### 5. The other tabs

**County map** — every Virginia county shaded by cost per pound of nitrogen.
Grey counties lie outside the Bay watershed portion the data covers.

**Practice ranking** — all practices in a county ranked by cost-effectiveness,
with the site features each one requires.

---

## What is in here

```
backend/          FastAPI app, the agent team, token accounting
  agents.py         one agent turn: tool loop, metering, scope enforcement
  runner.py         orchestration — who runs when, what runs concurrently
  toolbelt.py       the 18 tools and which agent may call which
  tokenomics.py     token and cost accounting, the spend ceiling
  prompts/          one file per agent, plus shared rules
mcp_server/       the tool layer, also exposed as an MCP server
  server.py         MCP entry point (see .mcp.json)
  screening.py      the deterministic calculator
  plan_reader.py    document parsing, name validation, additionality rules
  eligibility.py    which practices a farm could physically host
  cast_rules.py     buffer efficiencies and thresholds from the reference guide
data/
  cast_bmp_va.db    24,704 Virginia rate rows, 96 counties, 270 practices
  bmp_guide_index.json   38 reference-guide sheets with qualifying conditions
  county_hgmr.json       county → hydrogeomorphic region
  va_counties.json       simplified county boundaries for the map
  sample_plans/          test documents, including a 4-page NRCS-format PDF
frontend/
  index.html        the whole interface, one file
output/
  token_log.json    measured token counts for every run
report.html       the project report
slides.html       the slide deck
```

**No data download is needed.** The 8.6 MB rate database ships with the
repository so a fresh clone runs immediately.

---

## The MCP server

The same tools are exposed over MCP for use in a vibe coder:

```bash
./.venv/bin/python mcp_server/server.py
```

`.mcp.json` registers it as `bmp-deal-desk`.

---

## How it works, briefly

**No agent may state a number a tool did not return.** Nutrient pounds, costs,
efficiencies and practice names all come from the county rate tables or the
Chesapeake Bay Program reference guide, through a deterministic tool call. The
model routes work, reads documents, and writes prose.

Eight agents: **plan reader** (extract and validate), **eligibility** (what the
farm could host), **alignment** (which reference sheet governs), **opportunity**
(what is not taken), **quantification** (the only numeric role), **verification**
(inspection schedule), **drafter** (holds no tools at all), **review desk**
(decides last).

Three deterministic checks run before any model sees a document: injection scan,
jurisdiction check, and the field-intake risk review.

---

## Known limits

- **Virginia only.** Rates, delivery factors and hydrogeomorphic regions are
  Virginia's. A plan from another state is detected and refused rather than
  silently mispriced.
- **Stacked practices on shared acres.** CAST applies sequential treatment; this
  tool assumes distinct acres and says so on every result.
- **The hydrogeomorphic suggestion is a suggestion**, derived from physiographic
  province and county centroid. Confirm against the site.
- **This is a screening, not a certification.** The state certifies.

---

## Model and cost

`gpt-6-luna` through a Portkey gateway, reasoning effort pinned off — every
figure comes from a tool, so there is nothing for paid reasoning to compute.

The app measures its own token use and shows it live. It does **not** guess at
a price: with no rate configured it reports exact token counts and prints
*unpriced*. To see dollar figures, set these in `.env`:

```
MODEL_PRICE_IN=0.15
MODEL_PRICE_OUT=0.60
```

---

## Troubleshooting

| Symptom | Cause |
|---|---|
| `address already in use` | Something else is on port 8000. Use `--port 8001`. |
| Agent screening returns 503 | No API key found. Check `/api/health`. |
| `Function tools with reasoning_effort are not supported` | The model rejects tools when a reasoning effort is set. `backend/settings.py` pins it to `none`; make sure that value is unchanged. |
| A PDF uploads but extracts nothing | It is a scan with no text layer. The app says so explicitly. Paste the text instead. |
| Map or ranking tab is empty | `data/cast_bmp_va.db` is missing. It ships with the repo — re-clone. |

No sample plan, screenshot or data file in this repository describes a real
farm, producer or property.
