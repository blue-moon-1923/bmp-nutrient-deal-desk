"""Sections 4-8, appended to report.html."""
from __future__ import annotations
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
ROOT = HERE.parent
from data import TOK, ORG, COST_PER_RUN, scale_rows, PRICE_IN_PER_M, PRICE_OUT_PER_M, RUNS_PER_USER_MONTH
from build import fig, money, num

S = scale_rows()
ALL_TOOLS, SCOPED_MEAN = 18, 3.0
SAVED = ORG['saved_hours']; SAVED_PCT = ORG['saved_pct']

PART2 = f"""
<h2><span class="n">4</span>Tokenomics</h2>

<div class="callout warn"><h4>The price below is a placeholder</h4>
<p><code>gpt-6-luna</code> is provisioned for this course behind a Portkey gateway. The
gateway returns exact token counts and latency but <b>no cost field</b>, and the rate
was not published to students. This report uses
<b>{money(PRICE_IN_PER_M,2)} per million input tokens and {money(PRICE_OUT_PER_M,2)} per
million output</b> &mdash; plausible for a small hosted model, and <b>not verified</b>.
Every dollar figure in this section scales linearly with those two numbers.</p>
<p>The application itself does not guess. With no rate configured it reports exact
token counts and prints <b>&ldquo;unpriced&rdquo;</b> rather than inventing a cost. Setting
<code>MODEL_PRICE_IN</code> and <code>MODEL_PRICE_OUT</code> in <code>.env</code>
recalculates everything. <b>The token counts are measured and real; the dollars are
arithmetic on an unverified rate.</b></p></div>

<h3>What one run actually costs</h3>
<p>Measured across <b>{TOK['n']} real runs</b>, logged automatically to
<code>output/token_log.json</code> and displayed in the application itself.</p>

<div class="kpis">
  <div class="kpi"><div class="k">Mean per run</div><div class="v">{num(TOK['mean'])}</div><div class="n">tokens</div></div>
  <div class="kpi"><div class="k">Range</div><div class="v">{num(TOK['min']/1000,1)}&ndash;{num(TOK['max']/1000,1)}k</div><div class="n">tokens</div></div>
  <div class="kpi"><div class="k">Wall clock</div><div class="v">{TOK['sec']:.0f}s</div><div class="n">{TOK['sec_min']:.0f}&ndash;{TOK['sec_max']:.0f}s</div></div>
  <div class="kpi"><div class="k">Cost per run</div><div class="v">{money(COST_PER_RUN,4)}</div><div class="n">placeholder rate</div></div>
</div>

<table>
<thead><tr><th>Token type</th><th class="n">Mean per run</th><th class="n">Share</th><th>Note</th></tr></thead>
<tbody>
<tr><td>Input, uncached</td><td class="n">{num(TOK['input'])}</td><td class="n">{TOK['input']/TOK['mean']:.0%}</td><td>system prompts, tool schemas, document text</td></tr>
<tr><td>Input, cached</td><td class="n">{num(TOK['cached'])}</td><td class="n">{TOK['cached']/TOK['mean']:.0%}</td><td>repeated prompt prefixes across an agent's tool rounds</td></tr>
<tr><td>Output</td><td class="n">{num(TOK['output'])}</td><td class="n">{TOK['output']/TOK['mean']:.0%}</td><td>the agents' written findings</td></tr>
<tr class="tot"><td>Total</td><td class="n">{num(TOK['mean'])}</td><td class="n">100%</td><td></td></tr>
</tbody></table>

<p><b>Input dominates at {(TOK['input']+TOK['cached'])/TOK['mean']:.0%} of tokens.</b> That is
the shape of this workload: a conservation plan is thousands of tokens of input,
and the useful output is a few hundred words of findings. Any cost work has to
attack input, not output.</p>

<p>The run cost splits cleanly by whether a document is involved:</p>
<table>
<thead><tr><th>Run type</th><th class="n">Runs</th><th class="n">Mean tokens</th><th class="n">Cost</th><th>Agents that fire</th></tr></thead>
<tbody>
<tr><td>Practice list, no document</td><td class="n">{TOK['n_without']}</td><td class="n">{num(TOK['without_plan'])}</td><td class="n">{money(TOK['without_plan']/TOK['mean']*COST_PER_RUN,4)}</td><td>6 of 8</td></tr>
<tr><td>Conservation plan supplied</td><td class="n">{TOK['n_with']}</td><td class="n">{num(TOK['with_plan'])}</td><td class="n">{money(TOK['with_plan']/TOK['mean']*COST_PER_RUN,4)}</td><td>all 8</td></tr>
</tbody></table>

<p>Reading a document costs <b>{TOK['with_plan']/TOK['without_plan']:.1f}&times;</b> a run
without one &mdash; the plan reader and eligibility agents both read the full text. That
is the feature the user named as most valuable, and it is where the tokens go.</p>

<h3>Cost per user, per month, and at scale</h3>
<p>The programme scopes {ORG['scoped']} projects a year across {ORG['outreach_staff']}
field staff, and a project is typically screened more than once as information
arrives. That is <b>{RUNS_PER_USER_MONTH:.1f} runs per user per month</b>.</p>

<table>
<thead><tr><th>Users</th><th class="n">Runs / month</th><th class="n">Tokens / month</th><th class="n">Cost / month</th><th class="n">Cost / year</th></tr></thead>
<tbody>
{''.join(f'<tr><td>{r["users"]:,}{" (this programme)" if r["users"]==ORG["outreach_staff"] else ""}</td><td class="n">{r["runs_per_month"]:,.0f}</td><td class="n">{r["tokens_per_month"]:,.0f}</td><td class="n">{money(r["cost_per_month"])}</td><td class="n">{money(r["cost_per_year"])}</td></tr>' for r in S)}
</tbody></table>

<div class="callout"><h4>The number that matters</h4>
<p>Running this for the entire twelve-person field team costs
<b>{money(S[1]['cost_per_year'])} a year</b> at the placeholder rate. The analyst time it
replaces is worth <b>{money(SAVED*ORG['hourly'],0)}</b>. Even if the true token price were
<b>one hundred times</b> my placeholder, the tool would cost
{money(S[1]['cost_per_year']*100,0)} against {money(SAVED*ORG['hourly'],0)} of labour.
<b>The conclusion does not depend on the price being right.</b></p></div>

<h3>What I did to keep cost down</h3>

<h4>1. Tool scoping &mdash; the largest lever</h4>
<p>A model pays input tokens for every tool schema it is shown, on every call. The
application has <b>{ALL_TOOLS} tools</b>; each agent is given only the ones its role
needs &mdash; between zero and four, a mean of about {SCOPED_MEAN:.0f}.</p>
<table>
<thead><tr><th>Approach</th><th class="n">Schemas shown per call</th><th class="n">Approx. schema tokens</th></tr></thead>
<tbody>
<tr><td>All tools to every agent</td><td class="n">{ALL_TOOLS}</td><td class="n">~{ALL_TOOLS*110:,}</td></tr>
<tr><td>Scoped per role (shipped)</td><td class="n">{SCOPED_MEAN:.0f}</td><td class="n">~{int(SCOPED_MEAN*110):,}</td></tr>
<tr class="tot"><td>Saved per model call</td><td class="n">&minus;{ALL_TOOLS-SCOPED_MEAN:.0f}</td><td class="n">~&minus;{int((ALL_TOOLS-SCOPED_MEAN)*110):,}</td></tr>
</tbody></table>
<p>At roughly {int(TOK['n']*4)} model calls across the logged runs, that is a
material fraction of input. <b>It also improved behaviour</b>: scoping is enforced in
code, so an agent that asks for a tool outside its role gets a refusal rather than
reaching a capability it should not have.</p>

<h4>2. Reasoning effort off</h4>
<p>Pinned to <code>none</code>. This began as a necessity &mdash; the model rejects function
tools on the chat-completions endpoint when a reasoning effort is set &mdash; but it is
also correct here. Every figure comes from a deterministic tool; there is no
arithmetic for paid reasoning tokens to perform.</p>

<h4>3. A free path that skips the model entirely</h4>
<p>The <b>quick quote</b> runs the calculator directly: same reductions, same costs,
same refusals, <b>zero tokens and under a second</b>. When a user already knows the
practices, the agents add nothing. Most interactions during development used this
path, and it is the first button in the interface.</p>

<h4>4. Output capped, documents truncated</h4>
<p><code>MAX_OUTPUT_TOKENS</code> is 1,100 per call, and document text is capped before
it reaches a model. A hundred-page plan does not become a hundred pages of input.</p>

<h3>Did any of it hurt performance?</h3>
<p>Honestly: <b>two of the four cost measures are free, and two have a real cost I can
describe.</b></p>
<table>
<thead><tr><th>Measure</th><th>Quality effect</th><th>Evidence</th></tr></thead>
<tbody>
<tr><td>Tool scoping</td><td><b>Improved it.</b> Narrow toolsets reduce wrong-tool calls, and scope violations are refused in code.</td><td>Refusals visible in the agent trace, Figure 5.</td></tr>
<tr><td>Quick-quote path</td><td><b>No effect.</b> Identical deterministic output; it skips prose, not arithmetic.</td><td>The run result shows the calculator block and the agent cross-check side by side.</td></tr>
<tr><td>Reasoning off</td><td><b>Costs some robustness.</b> The agents occasionally misread an ambiguous field, and run-to-run variation on the EQIP year question is visible across runs.</td><td>Section 5, the review-desk contradiction.</td></tr>
<tr><td>Output cap</td><td><b>Costs some depth.</b> The drafted narrative is terse; on long plans it summarises where more detail would help.</td><td>Figure 3 narrative section.</td></tr>
</tbody></table>
<p>I did not pay to fix the last two, because the structural defence &mdash; no number
without a tool &mdash; means a terser or occasionally confused agent produces a worse
<i>explanation</i>, not a wrong <i>number</i>.</p>

<h2><span class="n">5</span>Safety</h2>

<p>Two things can go badly wrong here, and the obvious one is not the more
important one. The obvious risk is <b>a confident wrong number reaching a funding
proposal</b>. The one a producer actually cares about is <b>their name and the
location of their farm being sent to a language model they did not choose</b>.</p>

<h3>Threat 1 &mdash; the producer's identity leaving the machine</h3>

<p>A conservation plan identifies a real person. It carries their name, the street
address of the farm, a phone number, and the tract and farm numbers the agency
files them under. <b>None of that is needed to decide which practices can be
credited.</b> The agents need practice names, quantities, widths, land use, and the
county.</p>

<p>This is not a hypothetical concern. It is the objection the user raised
unprompted, and the second-largest reason projects die in this programme:</p>

<blockquote><p>&ldquo;I worry about farmers' trust of the numbers, and their
willingness to enter data like a conservation plan into AI.&rdquo;</p></blockquote>

<p>So the pipeline is ordered to make the leak impossible rather than unlikely:</p>

<table>
<thead><tr><th class="n">Step</th><th>What runs</th><th>Where</th></tr></thead>
<tbody>
<tr><td class="n">1</td><td>Injection scan</td><td>Locally, on the original</td></tr>
<tr><td class="n">2</td><td>Jurisdiction check</td><td>Locally, on the original</td></tr>
<tr><td class="n">3</td><td>Location detection &mdash; county, address, town</td><td>Locally, on the original</td></tr>
<tr><td class="n">4</td><td><b>Redaction</b></td><td>Locally</td></tr>
<tr><td class="n">5</td><td>Eight agents</td><td><b>See only the redacted text</b></td></tr>
</tbody></table>

<p>Location detection needs the address, which is exactly why it runs first and
locally. By the time anything leaves the machine the address is gone and the
county remains.</p>

{fig('08_privacy_receipt.jpg', 'The privacy receipt, shown in the result directly beneath the reductions and cost. Thirteen items removed from the sample plan before any model saw it: farm and tract identifiers, business names, a street address, a contract number and a postal code. Also covered are personal names after labels such as Producer or Landowner, phone numbers, email addresses, PO boxes, government identifiers and GPS coordinates.', 9)}

<h4>The test that matters is the other direction</h4>
<p>Removing information is easy; removing it <i>without breaking the screening</i> is
the actual requirement. Verified on the sample plan:</p>
<table>
<thead><tr><th>Survives redaction</th><th class="n">Result</th></tr></thead>
<tbody>
<tr><td>All nine practice lines with their NRCS codes</td><td class="n">intact</td></tr>
<tr><td>Every quantity &mdash; 151.5 ac, 4,200 ft, 75-foot width</td><td class="n">intact</td></tr>
<tr><td>County, for the rate lookup</td><td class="n">intact</td></tr>
<tr><td>EQIP, CREP and DEQ mentions &mdash; the additionality signals</td><td class="n">intact</td></tr>
<tr><td>Stream frontage</td><td class="n">intact</td></tr>
<tr class="tot"><td>Producer name, address, postcode, farm and tract numbers, contract number</td><td class="n">gone</td></tr>
</tbody></table>
<p>Searching the redacted text for each removed string returns nothing. The
screening output is <b>identical</b> before and after: the same seven creditable
practices, the same 3,087.8 lb of nitrogen, the same $27,130.</p>

<div class="callout ok"><h4>Two design choices</h4>
<p><b>The receipt never contains the document.</b> The redaction tool returns counts
and categories &mdash; &ldquo;street address: 1&rdquo; &mdash; never the removed strings. A log of
what you redacted that contains what you redacted is not a protection.</p>
<p><b>It is shown, not claimed.</b> The upload status line reports the count
<i>before</i> a run starts, and the result shows the full breakdown. The user's
objection was about trust; a number she can check is worth more than a privacy
policy she has to believe.</p></div>

<p>What this does <b>not</b> solve: a producer still has to be willing to hand the
plan over in the first place, and nothing in the architecture is visible to them.
Section 7 treats that as the project's largest open problem.</p>

<h3>Threat 2 &mdash; prompt injection in an uploaded document</h3>
<p>A conservation plan is a document a stranger hands you. This is the realistic
attack surface, and it is the one an agent that treats documents as instructions
will fail. The application scans every upload <b>before any model sees it</b>, and
treats findings as data to report, never as instructions to follow.</p>

{fig('07_injection_blocked.jpg', 'A plan containing a hidden instruction block. The scan caught three separate violations — ignore-instructions, asserting a decision not yet made, and asking to skip the EQIP check — quoted them with line numbers, and reported them. The agents continued with the legitimate content; the injected demand for a 9,500 lb figure never reached a result.', 8)}

<p>Three defences stack here, and the third is the one that matters:</p>
<ol>
<li><b>Deterministic pre-scan</b> &mdash; pattern-matched, runs before any model call, cannot itself be talked out of running.</li>
<li><b>Prompt instruction</b> &mdash; every agent is told uploaded documents are data, never instructions.</li>
<li><b>Structural impossibility</b> &mdash; <b>even if the model were fully persuaded, it could not report 9,500 lb</b>, because it cannot state a figure that did not come back from the calculator.</li>
</ol>
<p>The clean sample produces <b>zero findings</b>, so this is not a scanner that cries wolf.</p>

<h3>Threat 3 &mdash; the agent gets it wrong on its own</h3>
<p>More likely than an attacker, and I caught a real instance. On an earlier run the
review desk wrote:</p>
<blockquote><p>&ldquo;The risk review has no unanswered flags&rdquo;</p></blockquote>
<p><b>There were two.</b> The structured panel immediately above it said so. The model
contradicted its own tool output in prose.</p>
<div class="callout"><h4>Why this is in the report rather than hidden</h4>
<p>It is the clearest evidence for the architecture. Risk state and numbers live in
deterministic panels computed from tool output; the prose is commentary. The panel
was right, the narration was wrong, and <b>the panel is what a user acts on</b>. A
design that trusted narration would have shipped that error to a funder.</p></div>

<h3>Threat 4 &mdash; a wrong-but-plausible match</h3>
<p>Testing on a real plan, the fuzzy matcher resolved <code>subsoiler</code> &mdash; a tillage
implement &mdash; to <b>Biofilters</b>, a water-treatment structure, on character overlap
alone. That would have credited a practice the farm does not have.</p>
<p>Fixed by requiring both a high similarity ratio and a shared meaningful word.
<code>subsoiler</code>, <code>swales</code>, <code>mushroom compost</code>, <code>culverts</code> and
<code>archie basin</code> now all return <b>unresolved</b>. <b>A wrong practice is worse than
no practice</b>, and the tool is tuned to refuse.</p>

<h3>Threat 5 &mdash; the right answer for the wrong place</h3>
<p>During testing I screened a <b>Pennsylvania</b> farm against Virginia rate tables and
got a result that looked entirely normal. Every rate, delivery factor and
hydrogeomorphic region in this application is Virginia's.</p>
<p>The application now reads the state from the document and <b>refuses before costing
anything</b>, quoting the address as evidence. This is the failure mode nobody
notices, which makes it the one most worth detecting.</p>

<h3>Threat 6 &mdash; overspending</h3>
<p>A hard token ceiling per screening (<code>MAX_TOKENS_PER_SCREEN</code>): a run that
would cross it <b>halts before the call</b> rather than continuing to spend, and the
halt is reported in the trace. Uploads are capped at 40&nbsp;MB and 150 pages
because the file is read into memory. Delegation depth and tool rounds are both
bounded.</p>

<h3>What the application refuses to do</h3>
<table>
<thead><tr><th>Asked to</th><th>Response</th></tr></thead>
<tbody>
<tr><td>Price a buffer with no width given</td><td>Refuses &mdash; below 35&nbsp;ft only the narrow practice qualifies and no upland efficiency applies. The answer would differ by more than half.</td></tr>
<tr><td>Price a full-width buffer with no hydrogeomorphic region</td><td>Refuses &mdash; efficiency ranges 19% to 65% by region.</td></tr>
<tr><td>Use a neighbouring county's rate</td><td>Refuses and names the counties that do have the practice.</td></tr>
<tr><td>Credit a practice whose name does not resolve</td><td>Returns it unresolved. Never approximates.</td></tr>
<tr><td>Credit an existing structural practice</td><td>Refuses &mdash; not additional.</td></tr>
<tr><td>Credit a reduction already reported to the state</td><td>Refuses &mdash; double counting.</td></tr>
<tr><td>Send a producer's name or address to the model</td><td>Cannot &mdash; redaction happens before the model is called, not as an instruction to it.</td></tr>
<tr><td>Confirm a practice is certified</td><td>Will not. Every result is labelled a screening; the state certifies.</td></tr>
</tbody></table>
"""

p = ROOT / "report.html"
s = p.read_text()
s = s.replace("</div></body></html>", PART2 + "\n</div></body></html>")
p.write_text(s)
print(f"part 2 appended ({p.stat().st_size/1024:.0f} KB)")
