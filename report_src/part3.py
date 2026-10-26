"""Sections 6-8."""
from __future__ import annotations
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
ROOT = HERE.parent
from data import TOK, ORG, COST_PER_RUN, scale_rows
from build import money, num

S = scale_rows()
SAVED = ORG['saved_hours']
CONV_SAVED = (ORG['conv_before'] - ORG['conv_after']) * ORG['scoped']
BD_HOURS = 2 * 0.20 * ORG['fte_hours']

PART3 = f"""
<h2><span class="n">6</span>Impact</h2>

<h3>What a real user said</h3>
<p>The application was shown to the <b>Director of the Revolving Water Fund</b> at the
organisation described in section 1 &mdash; the person who runs this programme, and my
former manager. Her written reply, lightly copy-edited for spelling and
punctuation only:</p>

<blockquote>
<p>&ldquo;This is so useful, particularly the reading of the conservation plans. If we
can tweak this tool as we find barriers, we would certainly use it and encourage
all of our outreach specialists to use it.</p>
<p>I worry about farmers' trust of the numbers, and their willingness to enter data
like a conservation plan into AI. Also, this wouldn't work for our Amish farmers
&mdash; roughly 10% of farmers &mdash; since they don't use technology.</p>
<p>Overall this would save a ton of early scoping conversations, and potentially
drop the number from five project-defining conversations down to two. Let's talk
more about your AI work and applicability to CIF.&rdquo;</p>
</blockquote>
<p class="sub">Edits: &ldquo;specaists&rdquo; to &ldquo;specialists&rdquo;, &ldquo;farmers trust&rdquo; to &ldquo;farmers'
trust&rdquo;, capitalisation of &ldquo;Amish&rdquo;, hyphenation of &ldquo;project-defining&rdquo;. No words
added, removed or reordered.</p>

<p>Of everything in the application &mdash; the map, the ranking, the calculator, eight
agents &mdash; <b>the feature she named first was the document reading</b>. That is the
four hours described in section 1, identified independently by the person who owns
the process.</p>

<h3>Her number, and mine</h3>
<p>She supplied an operational figure I had not asked for and could not have
derived: <b>five project-defining conversations down to two</b>. That measures
something different from my four hours. <b>Four hours is analyst time.
Conversations are the farmer's time and the field team's</b> &mdash; the 35% of twelve
salaries that intake consumes.</p>

<table>
<thead><tr><th>Measure</th><th class="n">Before</th><th class="n">After</th><th class="n">Change</th><th>Source</th></tr></thead>
<tbody>
<tr><td>Time to a first estimate</td><td class="n">4 hours</td><td class="n">{TOK['sec']:.0f} seconds</td><td class="n">&minus;99.8%</td><td>measured, {TOK['n']} runs</td></tr>
<tr><td>Turnaround to the farmer</td><td class="n">up to 10 days</td><td class="n">same day</td><td class="n">&mdash;</td><td>practitioner</td></tr>
<tr><td>Analyst hours per year</td><td class="n">{num(ORG['analyst_hours'])}</td><td class="n">{num(ORG['after_hours'])}</td><td class="n">&minus;{num(SAVED)} h ({ORG['saved_pct']:.0%})</td><td>derived, 30 min review retained</td></tr>
<tr><td>Project-defining conversations</td><td class="n">{ORG['conv_before']*ORG['scoped']:,}</td><td class="n">{ORG['conv_after']*ORG['scoped']:,}</td><td class="n">&minus;{CONV_SAVED:,} (60%)</td><td><b>user-supplied</b></td></tr>
</tbody></table>

<p>The hours figure keeps <b>30 minutes of human review per project</b>, which the work
still needs. At 15 minutes the saving is 94%; I report the conservative number.</p>

<h3>What it does to the waste</h3>
<p>Section 1 showed {num(ORG['dead_end_hours'])} hours a year going into projects that
never proceed. Against the stated reasons:</p>
<table>
<thead><tr><th>Cause</th><th class="n">Share</th><th class="n">Hours</th><th>What this application does</th></tr></thead>
<tbody>
<tr><td>Project price too low</td><td class="n">40%</td><td class="n">{0.40*ORG['dead_end_hours']:.0f}</td><td><b>Surfaced faster.</b> Cost per pound in {TOK['sec']:.0f} seconds shows whether the economics can work before four hours are spent.</td></tr>
<tr><td>Data requirements</td><td class="n">35%</td><td class="n">{0.35*ORG['dead_end_hours']:.0f}</td><td><b>Not addressed</b>, and possibly made worse.</td></tr>
<tr><td>Already sold to EQIP</td><td class="n">25%</td><td class="n">{0.25*ORG['dead_end_hours']:.0f}</td><td><b>Caught outright</b> by the additionality check, from the plan itself.</td></tr>
</tbody></table>
<p><b>65% of dead-end screening is caught or surfaced early. 35% is untouched</b> &mdash; and
that 35% is the same barrier the director named without having seen this
breakdown. Two independent sources converging on one limitation is the honest
ceiling of this project.</p>

<h3>The second-order effect</h3>
<p>The practitioner's own projection: with screening automated, <b>two associates
could shift roughly 20% of their time to business development</b> &mdash; finding credit
buyers, including corporate buyers for stacked outcomes &mdash; and that could
plausibly yield <b>{money(400000,0)} a year in additional credit deals</b>.</p>
<div class="callout"><h4>Stated as a projection, with its gap</h4>
<p>That shift needs {num(BD_HOURS)} hours. Screening automation frees {num(SAVED)} &mdash;
<b>{SAVED/BD_HOURS:.1f}&times;, not 1.0&times;</b>. The freed analyst time covers most of
the redeployment, not all of it; the remainder has to come from the conversation
reduction the director described. Sense-check: {money(400000,0)} across
{ORG['converted']} contracted projects is {money(400000/ORG['converted'],0)} per project, or
about eight additional projects at the same average &mdash; inside the range the
programme already operates in. <b>This is a practitioner's projection, not a
measurement.</b></p></div>

<h3>Cost against benefit</h3>
<table>
<thead><tr><th>Item</th><th class="n">Per year</th><th>Basis</th></tr></thead>
<tbody>
<tr><td>Running the application, 12 field staff</td><td class="n">{money(S[1]['cost_per_year'])}</td><td>measured tokens, <b>placeholder</b> price</td></tr>
<tr><td>Analyst time returned</td><td class="n">{money(SAVED*ORG['hourly'],0)}</td><td>{num(SAVED)} h at {money(ORG['hourly'])}</td></tr>
<tr><td>Dead-end screening addressed (65%)</td><td class="n">{money(0.65*ORG['dead_end_hours']*ORG['hourly'],0)}</td><td>derived from the stated split</td></tr>
<tr><td>Additional deal value</td><td class="n">{money(400000,0)}</td><td><b>practitioner projection</b></td></tr>
</tbody></table>

<h2><span class="n">7</span>Limits and next steps</h2>

<h3>What does not work</h3>
<p><b>The data-trust problem, which is the largest one.</b> 35% of non-conversions are
producers who will not share what the programme needs, and asking them to put a
conservation plan into an AI tool plausibly makes that worse. The application does
not store uploads &mdash; text is read and discarded, and the response says so &mdash; but a
producer has no reason to take that on faith. This is a consent problem, not an
architecture problem.</p>

<p><b>Roughly 10% of producers are excluded outright.</b> Amish farmers do not use the
technology. No interface change fixes this; for that tenth the tool is useful only
to the field staff member screening on their behalf. <b>The 60% conversation
reduction therefore applies to about 90% of producers &mdash; call it 54% across the
whole base.</b> I would not have identified this limitation; the user did.</p>

<p><b>Trust in a thirty-second number.</b> A figure produced that fast carries less
weight with a producer than one an analyst worked through. The application's
answer is partial &mdash; every result shows its arithmetic line by line, names its
source, and labels itself a screening &mdash; but trust is earned by the person
delivering the number, not by the tool.</p>

<p><b>Virginia only.</b> Rate tables, delivery factors and hydrogeomorphic regions are
Virginia's. Other states are detected and refused rather than silently mispriced.</p>

<p><b>Stacked practices on shared acres.</b> CAST applies sequential treatment; this tool
assumes distinct acres and says so on every result. Overlapping practices must be
confirmed in CAST.</p>

<p><b>The hydrogeomorphic suggestion is a suggestion.</b> Derived from physiographic
province and county centroid. Boundary counties can fall either way, and the
carbonate/siliciclastic split is geology, not geography.</p>

<p><b>Run-to-run variation on ambiguous fields.</b> Where a plan names a cost-share
contract for an earlier year, different runs have treated the credit year
differently. The correct answer is a question, and the application does not always
ask it.</p>

<h3>What I would build next, in order</h3>
<ol>
<li><b>Something that solves the data-trust problem.</b> The largest untouched barrier
and the one the user named. Likely a field-staff-mediated mode where the producer
never interacts with the tool, plus a clear, auditable statement of what is and is
not retained.</li>
<li><b>Per-user accounts with a private project repository.</b> Partly a feature, mostly
part of the trust answer &mdash; a named account holding your own projects is a
different proposition from pasting a plan into a shared tool.</li>
<li><b>Pennsylvania and Maryland rates.</b> The workbook already contains them; it is a
database rebuild plus each state's ratio tables.</li>
<li><b>Resolve the ambiguous-year question deterministically</b> by asking the user
directly rather than leaving it to the agent.</li>
</ol>

<h2><span class="n">8</span>Sources</h2>
<table>
<thead><tr><th>Figure</th><th>Where it comes from</th></tr></thead>
<tbody>
<tr><td>Reduction and cost rates, all practices</td><td>County BMP reduction and cost workbook (CAST published costs). 24,704 Virginia rows, 96 counties, 270 practices, shipped as <code>data/cast_bmp_va.db</code>.</td></tr>
<tr><td>Buffer efficiencies, width thresholds, qualifying conditions</td><td>Chesapeake Bay Program, <i>Quick Reference Guide for Best Management Practices</i>, CBP/TRS-323-18, second edition (2022/2024), sheets A-12 and A-13. 38 sheets indexed as <code>data/bmp_guide_index.json</code>.</td></tr>
<tr><td>Buffer removal rate provenance</td><td>Belt et al. 2014, <i>Recommendations of the Expert Panel to Reassess Removal Rates for Riparian Forest and Grass Buffers</i>, approved by the CBP Water Quality Goal Implementation Team.</td></tr>
<tr><td>Credit retirement, release schedule, certification</td><td>9VAC25-900, Certification of Nonpoint Source Nutrient Credits; Virginia DEQ nutrient trading programme.</td></tr>
<tr><td>County boundaries</td><td>US Census county polygons, simplified for display.</td></tr>
<tr><td>Token counts, latency, run costs</td><td><b>Measured</b>, {TOK['n']} runs, <code>output/token_log.json</code>.</td></tr>
<tr><td>4 hours, 250 scoped, 50 converted, 12 outreach staff, 10-day turnaround, non-conversion split, $75k average salary</td><td><b>Practitioner account</b> &mdash; the author, who performed the work.</td></tr>
<tr><td>5 conversations to 2; the three barriers; 10% Amish exclusion; $400k projection</td><td><b>User interview</b> &mdash; Director, Revolving Water Fund.</td></tr>
<tr><td>Competing products</td><td>CAST; Nutrient Tracking Tool (Tarleton State / USDA-NRCS); ACPF FNRT (Bravard et al., <i>J. Environ. Qual.</i> 2022); Truterra; Field to Market; ESMC; Regrow; Virginia DEQ and SWaN.</td></tr>
<tr><td>Token price</td><td><b>PLACEHOLDER, unverified.</b> See the note opening section 4.</td></tr>
</tbody></table>

<p class="fn">Built for MGT 409, AI Foundations for Managers, Yale School of
Management. All code, data and sample documents are in the repository. The sample
conservation plan is synthetic: no real farm, producer or property is described
anywhere in this report or the repository, and no client document is included.</p>
"""

p = ROOT / "report.html"
s = p.read_text()
s = s.replace("</div></body></html>", PART3 + "\n</div></body></html>")
p.write_text(s)
print(f"part 3 appended ({p.stat().st_size/1024:.0f} KB)")
