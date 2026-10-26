"""Build report.html — one self-contained file, images base64-embedded."""
from __future__ import annotations
import base64, mimetypes, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
ROOT = HERE.parent
SHOTS = ROOT / "output" / "screenshots"

from data import TOK, ORG, COST_PER_RUN, scale_rows, PRICE_IN_PER_M, PRICE_OUT_PER_M, RUNS_PER_USER_MONTH
from style import CSS
from diagram import DIAGRAM

REPO_URL = "https://github.com/blue-moon-1923/mgt409-bmp-nutrient-deal-desk"


def b64(p: Path) -> str:
    mime = mimetypes.guess_type(p.name)[0] or "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def fig(name, cap, num=None):
    p = SHOTS / name
    label = f"<b>Figure {num}.</b> " if num else ""
    if not p.is_file():
        return f'<figure class="missing"><div class="ph">missing: {name}</div><figcaption>{label}{cap}</figcaption></figure>'
    return f'<figure><img src="{b64(p)}" alt="{cap}"><figcaption>{label}{cap}</figcaption></figure>'


def money(x, d=2): return f"${x:,.{d}f}"
def num(x, d=0): return f"{x:,.{d}f}"

S = scale_rows()
HTML = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BMP Nutrient Deal Desk — Final Report</title><style>{CSS}</style></head><body>
<div class="page">

<div class="hero">
  <img src="{b64(SHOTS/'00_banner.jpg')}" alt="Virginia pasture with perimeter fencing and a riparian forest buffer">
  <div class="ov"></div>
  <div class="tx">
    <h1>BMP Nutrient Deal&nbsp;Desk</h1>
    <p class="sub">Reading conservation plans to screen nutrient-credit projects in Virginia</p>
  </div>
</div>

<dl class="meta">
  <dt>Author</dt><dd>Christian Roberts</dd>
  <dt>Course</dt><dd>MGT 409, AI Foundations for Managers, Yale School of Management</dd>
  <dt>Repository</dt><dd><a href="{REPO_URL}">{REPO_URL}</a></dd>
  <dt>Run locally</dt><dd><code>uvicorn backend.main:app --port 8000</code> &mdash; see the README</dd>
  <dt>Model</dt><dd><code>gpt-6-luna</code> via Portkey, reasoning effort off</dd>
</dl>

<p class="lead">An agent team that reads a farm's conservation plan, works out which
best management practices can actually be credited, and returns the nitrogen,
phosphorus and sediment reductions with their cost &mdash; in about half a minute,
replacing roughly four hours of manual document work.</p>

<div class="toc"><ol>
<li>Motivation</li><li>What is new here</li><li>The agents</li><li>Tokenomics</li>
<li>Safety</li><li>Impact</li><li>Limits and next steps</li><li>Sources</li>
</ol></div>

<h2><span class="n">1</span>Motivation</h2>

<h3>The person</h3>
<p>A four-person non-profit runs a cropland-retirement programme in the Chesapeake
Bay watershed. It pays roughly twelve full-time outreach staff, employed through
local non-profits and cooperatives, to meet farmers. Those twelve have one job
before anything else can happen: collect basic information from a producer, then
bring it back for an answer to the only two questions a farmer actually asks.</p>

<blockquote><p>&ldquo;What will I have to do, and how much will I get paid to do it?&rdquo;</p></blockquote>

<p>Answering that was one analyst, working alongside a colleague who did the same.
I was that analyst. I wrote this application because I was the bottleneck.</p>

<h3>The work as it was done</h3>
<p>Every screening meant reading a conservation plan &mdash; <b>written differently by
every planner, routinely twenty pages and sometimes over a hundred</b>, with the
things that matter buried: practice names, acreages, the property address.
Then comparing each practice against the Chesapeake Bay Program's BMP Quick
Reference Guide for its definition and qualifying conditions. Then hunting for
the right rows in the isolated scenarios to get reduction values. Then building
the arithmetic by hand in a spreadsheet, and sanity-checking it.</p>

<p><b>About four hours per project, and not four continuous hours</b> &mdash; it stretched
across days while a missing acreage or an address was chased down.</p>

<div class="kpis">
  <div class="kpi"><div class="k">Scoped per year</div><div class="v">{ORG['scoped']}</div><div class="n">projects</div></div>
  <div class="kpi"><div class="k">Reaching contract</div><div class="v">{ORG['converted']}</div><div class="n">20% conversion</div></div>
  <div class="kpi"><div class="k">Analyst hours</div><div class="v">{num(ORG['analyst_hours'])}</div><div class="n">per year</div></div>
  <div class="kpi"><div class="k">Of a 4-person org</div><div class="v">{ORG['analyst_hours']/ORG['fte_hours']/4:.0%}</div><div class="n">of staff capacity</div></div>
</div>

<p>Two figures corroborate each other. By role, screening was 20% of my job and 20%
of a colleague's &mdash; {num(ORG['analyst_hours'])} hours a year. By volume,
{ORG['scoped']} projects at four hours each is {num(ORG['volume_hours'])} hours.
They agree within 17%; this report uses the conservative figure throughout.</p>

<h3>What that cost, beyond the hours</h3>
<p><b>Latency.</b> When several projects were scoped at once, an initial estimate could
take <b>up to ten days</b> to reach the farmer. Twelve field staff waited on one
person to answer the question they had been sent out to ask. They were not idle
&mdash; they were redeployed to recruiting more farmers and to business development
with credit buyers &mdash; but the queue set the pace of the programme. A few projects
a year were lost outright to that delay, mostly when planting dates moved.</p>

<p><b>Waste.</b> At a 20% conversion rate, <b>{num(ORG['dead_end_hours'])} of those
{num(ORG['analyst_hours'])} hours each year went into projects that never
proceeded</b> &mdash; about {money(ORG['dead_end_hours']*ORG['hourly'],0)} of payroll at
the organisation's {money(ORG['hourly'])} average hourly cost. The screening is
what determines viability, so the work cannot simply be skipped. But four hours
is an expensive way to discover a project does not work.</p>

<h3>Why those projects died</h3>
<table>
<thead><tr><th>Reason a scoped project did not convert</th><th class="n">Share</th><th class="n">Projects</th><th class="n">Hours</th></tr></thead>
<tbody>
<tr><td>Project price &mdash; the programme's offer was too low</td><td class="n">{ORG['no_price']:.0%}</td><td class="n">{ORG['no_price']*200:.0f}</td><td class="n">{ORG['no_price']*ORG['dead_end_hours']:.0f}</td></tr>
<tr><td>Data requirements &mdash; the producer would not share what was needed</td><td class="n">{ORG['no_data']:.0%}</td><td class="n">{ORG['no_data']*200:.0f}</td><td class="n">{ORG['no_data']*ORG['dead_end_hours']:.0f}</td></tr>
<tr><td>Already sold to EQIP or another cost-share programme</td><td class="n">{ORG['no_eqip']:.0%}</td><td class="n">{ORG['no_eqip']*200:.0f}</td><td class="n">{ORG['no_eqip']*ORG['dead_end_hours']:.0f}</td></tr>
<tr class="tot"><td>Total</td><td class="n">100%</td><td class="n">200</td><td class="n">{num(ORG['dead_end_hours'])}</td></tr>
</tbody></table>

<p>That table is the design brief. A quarter of the dead ends are EQIP overlap,
which is a fact stated in the conservation plan itself and discoverable in
seconds. Two fifths are economics, which a cost-per-pound figure settles early.
The remaining third &mdash; data requirements &mdash; this application does not solve, and
section 7 says so plainly.</p>

<h2><span class="n">2</span>What is new here</h2>

<p>Every component of this problem already has a tool. None of them reads the
document a farm actually arrives as.</p>

<table>
<thead><tr><th>Existing product</th><th>What it is</th><th>Why it does not do this</th></tr></thead>
<tbody>
<tr><td><b>CAST</b><br><span class="sub">Chesapeake Bay Program</span></td>
<td>The authoritative scenario tool. Estimates load reductions, BMP acres and costs, consistent with the Watershed Model.</td>
<td>Prices a scenario you have already specified. You must already know which practice applies, where, at what acreage, and whether it qualifies. It is the rate table this application reads from.</td></tr>
<tr><td><b>Nutrient Tracking Tool</b><br><span class="sub">Tarleton State / USDA-NRCS</span></td>
<td>Field-scale, built on the APEX model. Compares practices for cost-effectiveness.</td>
<td>Requires detailed field management data entered by someone who knows both the farm and the tool. Answers &ldquo;what would this practice do here&rdquo;, not &ldquo;what is in this document and can any of it be credited&rdquo;.</td></tr>
<tr><td><b>ACPF Financial &amp; Nutrient Reduction Tool</b></td>
<td>Watershed BMP mapping with cost and nitrogen estimates; places opportunity cost spatially.</td>
<td>Watershed planning, Iowa and Minnesota, not document-driven, no additionality logic.</td></tr>
<tr><td><b>Truterra, Field to Market, ESMC, Regrow</b></td>
<td>Grower enrolment and sustainability platforms at national scale.</td>
<td><b>Carbon-first.</b> The Truterra Ohio wheat project tracks greenhouse gas, nitrogen use efficiency, soil quality, erosion and a sustainability score &mdash; <b>no water quality metric</b>.</td></tr>
<tr><td><b>Virginia DEQ registry and SWaN</b></td>
<td>Credit certification registry, and a marketplace launched December 2025.</td>
<td>Transaction infrastructure for credits that already exist and have already been certified. They begin where this ends.</td></tr>
<tr><td><b>A general chatbot</b></td>
<td>Will discuss practices fluently and produce a confident nitrogen figure on request.</td>
<td>Holds no county rate table, no qualifying conditions, no additionality rules. Nothing stops it inventing a number, and the failure is silent.</td></tr>
</tbody></table>

<div class="callout ok"><h4>The gap, stated narrowly</h4>
<p>A targeted search for agent or LLM extraction of conservation plans for credit
origination returned <b>nothing in agriculture</b>. The nearest published analogue is
in medicine &mdash; agent-based extraction from breast cancer synoptic reports, 2026.</p>
<p>So the claim is not that the data or the rules are new. CAST holds the rates. The
reference guide holds the qualifying conditions. The regulation holds the
additionality rules. <b>What does not exist is anything that reads the document a
farm actually arrives as, decides which practices are real, which are creditable,
and which need a question answered &mdash; and refuses to produce a number when it
cannot.</b></p></div>

<p>An independent confirmation that the bottleneck is real, from a competitor: an
ESMC and Regrow pilot in Minnesota targeting 50,000 acres with water quality
credits reported that <b>farmer enrolment was harder than anticipated and farm data
collection was time-consuming</b>. The constraint in these programmes is not
modelling. It is getting a farm's information into a form the programme can act on.</p>

{fig('01_screening_example.jpg', 'The application on first load. The result panel is pre-filled with a worked example so a reader can see every output category before running anything.', 1)}

<h2><span class="n">3</span>The agents</h2>

<p>Eight agents on <code>gpt-6-luna</code>, the only model permitted on the course key.
It is a small model, and that suited the design rather than constraining it:
<b>every number in this application comes from a deterministic tool.</b> The model
routes work, reads prose, and writes prose. There is nothing here for expensive
reasoning to buy, which is why reasoning effort is pinned off &mdash; a decision
section 4 revisits as a cost lever.</p>

<figure>{DIAGRAM}<figcaption><b>Figure 2.</b> Architecture. A document passes three
deterministic checks before any model sees it. Eight agents then work through it,
each holding only the tools its role needs. Every figure returns from the tool
layer over the county rate tables; no agent may state a number a tool did not
produce.</figcaption></figure>

<table>
<thead><tr><th>Agent</th><th>What it does</th><th class="n">Tools</th></tr></thead>
<tbody>
<tr><td><b>Plan reader</b></td><td>Scans for injection first, lists every practice with its quantity, validates each name against the county rate table, and applies the additionality rules.</td><td class="n">4</td></tr>
<tr><td><b>Eligibility</b></td><td>Reads the same document for physical facts &mdash; frontage, livestock, cropland, tile &mdash; and works out which practices the farm could host at all.</td><td class="n">3</td></tr>
<tr><td><b>Alignment</b></td><td>Which reference sheet governs each buffer (A-12 cropland, A-13 pasture), the 35&nbsp;ft width threshold, credit durations, Virginia's verification interval.</td><td class="n">4</td></tr>
<tr><td><b>Opportunity</b></td><td>What the project leaves on the table, ranked by cost per pound, each labelled with the site feature it requires.</td><td class="n">3</td></tr>
<tr><td><b>Quantification</b></td><td><b>The only agent that produces numbers</b>, and only through one tool. Returns the per-line arithmetic so a reviewer can check it by hand.</td><td class="n">3</td></tr>
<tr><td><b>Verification</b></td><td>Inspection schedule, what happens if one is missed, and an honest note on staffing.</td><td class="n">2</td></tr>
<tr><td><b>Drafter</b></td><td>Writes the proposal narrative. <b>Holds zero tools by design.</b></td><td class="n">0</td></tr>
<tr><td><b>Review desk</b></td><td>Decides last. Returns ADVANCE, NEEDS INFORMATION or DO NOT ADVANCE, and cannot say ADVANCE while a blocking risk is open.</td><td class="n">3</td></tr>
</tbody></table>

<div class="callout"><h4>Why the drafter has no tools</h4>
<p>It is the agent most likely to invent a plausible figure, because its job is
fluent prose. Giving it zero numeric tools makes fabrication structurally
impossible rather than merely discouraged. It can only use numbers already handed
to it; if one is missing it writes the sentence without it or marks it pending.</p></div>

<h3>A real run, traced</h3>
<p>The run below is <code>run_172a7d1d60</code>, a detailed conservation plan for a 310-acre
Rockingham County farm. The application read it, outlined the existing commitments and the
eligible practices, and calculated the nutrient reductions and their cost.
<b>{num(67162)} tokens, {62.7:.1f} seconds, 31 tool calls.</b></p>

{fig('04_run_result_top.jpg', 'The document located itself. The plan reader extracted the address and county, the application set the county and the hydrogeomorphic region, and the deterministic calculator returned nitrogen, phosphorus, sediment and cost before any agent prose appears.', 3)}

{fig('05_additionality.jpg', 'The additionality rules on a real document. Seven practices creditable and counted. Nutrient Management held because the plan states its reductions were already reported to Virginia DEQ — double counting. An existing CREP buffer held because a structural practice already in the ground is not additional. Fence returned unresolved: a real cost, but not a creditable practice. The field-intake answers on the left feed the risk panel.', 4)}

{fig('06_agent_trace.jpg', "The agent trace. The plan reader's first tool call was REFUSED for bad arguments, it corrected itself, and the full extraction is visible. Note its reasoning on the no-till line: the EQIP contract documented in the plan expired in 2024, which says nothing about the credit year, so the practice is treated as creditable for a new season.", 5)}

<h3>Two things worth noticing in that trace</h3>
<p><b>A refused tool call appears in the record.</b> The first attempt passed bad
arguments and the tool rejected it. The agent recovered. Both are visible, because
a trace that hides failed calls is not a trace.</p>

<p><b>The agents' arithmetic is checkable against ground truth.</b> Every run computes
the deterministic result independently and shows it above the agent prose. On this
run the quantification agent reproduced the tool's figures exactly, line by line.
That comparison is in the product, not just in this report.</p>

{fig('02_county_map.jpg', 'County map. Shading is cost per pound of nitrogen for the selected practice; the grey counties have no rate row because they lie outside the Chesapeake Bay watershed portion the programme covers. The absence is itself the answer.', 6)}

{fig('03_practice_ranking.jpg', 'Every practice in a county ranked by cost per pound of nitrogen, with site requirements flagged. Two practices carry zero or negative net cost. Streamside buffers with exclusion fencing deliver 220 lb N per acre against 9.3 for cropland retirement — but need stream frontage and livestock, which a given farm may not have.', 7)}

<p>These two screens are not screening tools. They let field staff see, before a
visit, which practices are worth targeting where. <b>The same practice ranges from
{money(1.93)} to {money(64.72)} per pound of nitrogen across Virginia counties &mdash; a
34&times; spread.</b> That turns outreach from relationship-led into evidence-led.</p>

</div></body></html>"""

if __name__ == "__main__":
    out = ROOT / "report.html"
    out.write_text(HTML)
    print(f"part 1 written ({out.stat().st_size/1024:.0f} KB)")
