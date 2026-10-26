"""Build slides.html — reveal.js from CDN, every image embedded."""
from __future__ import annotations
import base64, mimetypes, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
ROOT = HERE.parent
SHOTS = ROOT / "output" / "screenshots"
from data import TOK, ORG, COST_PER_RUN, scale_rows
from flow import BEFORE, AFTER

S = scale_rows()
SAVED = ORG["saved_hours"]
CONV = (ORG["conv_before"] - ORG["conv_after"]) * ORG["scoped"]


def b64(n):
    p = SHOTS / n
    if not p.is_file():
        return ""
    m = mimetypes.guess_type(p.name)[0] or "image/jpeg"
    return f"data:{m};base64," + base64.b64encode(p.read_bytes()).decode()


def money(x, d=2): return f"${x:,.{d}f}"
def num(x, d=0): return f"{x:,.{d}f}"

CSS = """
:root{--navy:#001637;--teal:#0f4768;--deep:#003d47;--green:#38664f;
--sky:#3899b8;--pale:#9ed9ff;--amber:#ffb026;--ink:#0d1212}
.reveal{font-family:Figtree,system-ui,-apple-system,sans-serif;font-size:30px;color:#e8eef2}
.reveal-viewport{background:var(--navy)}
.reveal h1,.reveal h2,.reveal h3{font-family:Figtree,sans-serif;font-weight:700;
text-transform:none;letter-spacing:-.018em;color:#fff;margin:0 0 .35em}
.reveal h1{font-size:2.05em;line-height:1.06}
.reveal h2{font-size:1.42em;line-height:1.14}
.reveal h3{font-size:1.0em;color:var(--pale);font-weight:600}
.reveal section{text-align:left}
.reveal p{line-height:1.45;margin:0 0 .5em}
.reveal .eyebrow{font-size:.44em;letter-spacing:.17em;text-transform:uppercase;
color:var(--amber);font-weight:700;margin-bottom:.7em}
.reveal .lead{font-size:.72em;color:#b9cdd8;line-height:1.5}
.reveal .big{font-size:2.5em;font-weight:800;color:var(--amber);line-height:1;
letter-spacing:-.03em}
.reveal .grid{display:grid;gap:18px}
.reveal .g2{grid-template-columns:1fr 1fr}
.reveal .g3{grid-template-columns:repeat(3,1fr)}
.reveal .g4{grid-template-columns:repeat(4,1fr)}
.reveal .box{background:rgba(255,255,255,.055);border:1px solid rgba(255,255,255,.14);
border-radius:12px;padding:18px 20px}
.reveal .box.hi{background:rgba(255,176,38,.11);border-color:rgba(255,176,38,.42)}
.reveal .box.ok{background:rgba(95,163,124,.13);border-color:rgba(95,163,124,.45)}
.reveal .box.no{background:rgba(194,97,74,.13);border-color:rgba(194,97,74,.45)}
.reveal .box .k{font-size:.4em;letter-spacing:.11em;text-transform:uppercase;
color:#9fb6c9;font-weight:700}
.reveal .box .v{font-size:1.32em;font-weight:800;color:#fff;line-height:1.08;margin-top:5px;
letter-spacing:-.02em}
.reveal .box .n{font-size:.42em;color:#9fb6c9;margin-top:5px;line-height:1.4}
.reveal ul{margin:0;padding-left:1.05em}
.reveal li{margin-bottom:.4em;line-height:1.4;font-size:.78em}
.reveal li b{color:#fff}
.reveal .q{font-size:.68em;line-height:1.5;border-left:4px solid var(--amber);
padding:4px 0 4px 20px;color:#dbe7ee;font-style:italic}
.reveal .q cite{display:block;font-style:normal;font-size:.72em;color:#8da7b8;
margin-top:10px;letter-spacing:.02em}
.reveal img.shot{width:100%;border-radius:9px;border:1px solid rgba(255,255,255,.2);display:block}
.reveal .cap{font-size:.4em;color:#8da7b8;margin-top:8px;line-height:1.4}
.reveal table{font-size:.52em;width:100%;border-collapse:collapse;color:#dbe7ee}
.reveal table th{color:var(--pale);font-weight:700;text-align:left;padding:7px 9px;
border-bottom:2px solid rgba(255,255,255,.28);font-size:.86em;
text-transform:uppercase;letter-spacing:.07em}
.reveal table td{padding:7px 9px;border-bottom:1px solid rgba(255,255,255,.12)}
.reveal table td.n,.reveal table th.n{text-align:right;font-variant-numeric:tabular-nums}
.reveal .amber{color:var(--amber)}.reveal .grn{color:#8fd3ab}.reveal .mut{color:#8da7b8}
/* title slide: the photo is the slide; the words sit on it with air */
.reveal section.title{height:100%;display:flex;align-items:center;justify-content:flex-start}
.reveal section.title .title-inner{position:relative;z-index:1;
padding:0 50% 0 10.5%;width:100%;transform:translateY(7%)}
.reveal section.title .eyebrow{font-size:.38em;letter-spacing:.24em;
color:#ffb026;margin-bottom:2.4em;opacity:.95}
.reveal section.title h1{font-size:2.1em;line-height:1.12;letter-spacing:-.022em;
margin:0 0 .52em;text-shadow:0 4px 38px rgba(0,8,20,.62)}
.reveal .tagline{font-size:.62em;line-height:1.78;color:#dce9f1;max-width:26ch;
margin:0;text-shadow:0 2px 20px rgba(0,8,20,.72);font-weight:400}
.reveal .byline{font-size:.4em;color:#a8c0d1;margin:3.4em 0 0;letter-spacing:.2em;
text-transform:uppercase;font-weight:600;text-shadow:0 2px 14px rgba(0,8,20,.8)}
.reveal .progress{color:var(--amber)}
.reveal .slide-number{background:transparent;color:#5d7585;font-size:14px}
.reveal section.present{animation:none}
@media screen and (max-width:900px){.reveal{font-size:22px}}
"""

HTML = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BMP Nutrient Deal Desk</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/theme/black.css">
<style>{CSS}</style></head><body>
<div class="reveal"><div class="slides">

<!-- 1 -->
<section data-background-image="{b64('00_title_bg.jpg')}" data-background-size="cover"
         data-background-position="center" class="title">
 <div class="title-inner">
  <p class="eyebrow">Final project &middot; MGT 409</p>
  <h1>BMP&nbsp;Nutrient<br>Deal&nbsp;Desk</h1>
  <p class="tagline">Reading conservation plans to screen
  nutrient-credit projects in Virginia.</p>
  <p class="tagline" style="margin-top:1.15em"><span class="amber">Four hours of
  document work, in thirty seconds.</span></p>
  <p class="byline">Christian Roberts</p>
 </div>
</section>

<!-- 2 -->
<section>
 <p class="eyebrow">The problem</p>
 <h2>One analyst stood between<br>twelve field staff and an answer</h2>
 {BEFORE}
 <div class="grid g4" style="margin-top:16px">
  <div class="box"><div class="k">Scoped / year</div><div class="v">250</div><div class="n">50 reach contract</div></div>
  <div class="box"><div class="k">Per screening</div><div class="v">4 hours</div><div class="n">plans run 20&ndash;100+ pages</div></div>
  <div class="box hi"><div class="k">Analyst hours</div><div class="v">{num(ORG['analyst_hours'])}</div><div class="n">per year</div></div>
  <div class="box no"><div class="k">On dead ends</div><div class="v">{num(ORG['dead_end_hours'])}</div><div class="n">{money(ORG['dead_end_hours']*ORG['hourly'],0)} of payroll</div></div>
 </div>
</section>

<!-- 3 -->
<section>
 <p class="eyebrow">Where the waste is</p>
 <h2>The most common reason a project dies<br>is one the tool catches in 33 seconds</h2>
 <table style="margin-top:22px;font-size:.6em">
  <tr><th>Why a scoped project did not convert</th><th class="n">Share</th><th class="n">Hours</th><th>What this tool does</th></tr>
  <tr><td>Programme's offer was too low</td><td class="n">40%</td><td class="n">{0.40*ORG['dead_end_hours']:.0f}</td><td class="grn">Surfaced in 33 seconds</td></tr>
  <tr><td>Producer would not share data</td><td class="n">35%</td><td class="n">{0.35*ORG['dead_end_hours']:.0f}</td><td class="mut">Not addressed</td></tr>
  <tr><td>Already sold to EQIP</td><td class="n">25%</td><td class="n">{0.25*ORG['dead_end_hours']:.0f}</td><td class="grn">Caught outright</td></tr>
 </table>
 <div class="grid g2" style="margin-top:20px">
  <div class="box ok"><div class="k">Caught or surfaced early</div><div class="v">65%</div>
   <div class="n">of dead-end screening effort</div></div>
  <div class="box no"><div class="k">Untouched &mdash; and possibly worsened</div><div class="v">35%</div>
   <div class="n">the data-trust problem, named independently by the user</div></div>
 </div>
</section>

<!-- 4 -->
<section>
 <p class="eyebrow">What is new</p>
 <h2>Every piece exists.<br>Nothing reads the document.</h2>
 <div class="grid g2" style="margin-top:22px">
  <div>
   <table>
    <tr><th>Exists today</th><th>Why it isn't this</th></tr>
    <tr><td><b>CAST</b></td><td>Prices a scenario you already specified</td></tr>
    <tr><td><b>Nutrient Tracking Tool</b></td><td>Needs field data from an expert</td></tr>
    <tr><td><b>ACPF FNRT</b></td><td>Watershed planning, Iowa &amp; Minnesota</td></tr>
    <tr><td><b>Truterra, ESMC, Regrow</b></td><td>Carbon-first &mdash; no water metric</td></tr>
    <tr><td><b>DEQ registry, SWaN</b></td><td>Begins where this ends</td></tr>
    <tr><td><b>ChatGPT</b></td><td>No rate table &mdash; invents numbers silently</td></tr>
   </table>
  </div>
  <div class="box hi">
   <div class="k">The gap</div>
   <p style="font-size:.62em;line-height:1.5;margin-top:12px">A search for agent extraction of
   conservation plans for credit origination returned <b>nothing in agriculture</b>. The nearest
   published analogue is in medicine.</p>
   <p style="font-size:.62em;line-height:1.5;margin-top:14px">CAST holds the rates. The reference
   guide holds the conditions. The regulation holds the rules. <b class="amber">Nothing reads the
   document a farm actually arrives as</b> &mdash; and refuses when it cannot.</p>
  </div>
 </div>
</section>

<!-- 5 -->
<section>
 <p class="eyebrow">What it produces</p>
 <h2>A plan in. Pounds and cost out.</h2>
 <div class="grid g2" style="margin-top:14px;grid-template-columns:1.5fr 1fr;align-items:start">
  <div><img class="shot" src="{b64('04_run_result_top.jpg')}" alt="Reductions and cost">
   <p class="cap">A detailed conservation plan: outlined existing commitments and eligible
   practices, then calculated the nutrient reductions and cost &mdash;
   {num(67162)} tokens, 63 seconds.</p></div>
  <div>
   <div class="box ok" style="margin-bottom:12px"><div class="k">Nitrogen</div>
    <div class="v">3,087.8</div><div class="n">lb per year</div></div>
   <div class="box ok" style="margin-bottom:12px"><div class="k">Phosphorus</div>
    <div class="v">590.0</div><div class="n">lb per year</div></div>
   <div class="box ok" style="margin-bottom:12px"><div class="k">Sediment</div>
    <div class="v">382,206</div><div class="n">lb per year</div></div>
   <div class="box hi"><div class="k">Cost</div><div class="v">$27,130</div>
    <div class="n">$8.79 per lb N &middot; $0.88 amortised over the commitment</div></div>
  </div>
 </div>
</section>

<!-- 6 -->
<section>
 <p class="eyebrow">How it works</p>
 <h2>Eight agents. None of them may state a number.</h2>
 <div class="grid g2" style="margin-top:14px;grid-template-columns:1fr 1.25fr;align-items:start">
  <div>
   <ul style="font-size:.92em">
    <li><b>Plan reader</b> &mdash; extract and validate every practice name</li>
    <li><b>Eligibility</b> &mdash; what the farm could physically host</li>
    <li><b>Alignment</b> &mdash; which reference sheet governs, width, duration</li>
    <li><b>Opportunity</b> &mdash; what the project leaves on the table</li>
    <li><b>Quantification</b> &mdash; <span class="amber">the only numeric role</span></li>
    <li><b>Verification</b> &mdash; inspection schedule</li>
    <li><b>Drafter</b> &mdash; <span class="amber">holds zero tools by design</span></li>
    <li><b>Review desk</b> &mdash; decides last, cannot pass a blocker</li>
   </ul>
   <div class="box ok" style="margin-top:14px">
    <p style="font-size:.54em;line-height:1.45;margin:0">Every figure returns from a tool over
    24,704 county rate rows. <b>Fabrication is structurally impossible, not discouraged.</b></p>
   </div>
  </div>
  <div><img class="shot" src="{b64('05_additionality.jpg')}" alt="Creditability decisions">
   <p class="cap"><b>Creditability decided per practice, from the document.</b> Nutrient Management
   held &mdash; already reported to Virginia DEQ. An existing CREP buffer held &mdash; not additional.
   Fence unresolved &mdash; a real cost, not a creditable practice.</p></div>
 </div>
</section>

<!-- 7 -->
<section>
 <p class="eyebrow">Cost to run</p>
 <h2>Two dollars and sixty-seven cents a year</h2>
 <div class="grid g4" style="margin:24px 0">
  <div class="box"><div class="k">Mean / run</div><div class="v">{num(TOK['mean'])}</div><div class="n">tokens, {TOK['n']} real runs</div></div>
  <div class="box"><div class="k">Input share</div><div class="v">{(TOK['input']+TOK['cached'])/TOK['mean']:.0%}</div><div class="n">documents are input-heavy</div></div>
  <div class="box"><div class="k">Wall clock</div><div class="v">{TOK['sec']:.0f}s</div><div class="n">{TOK['sec_min']:.0f}&ndash;{TOK['sec_max']:.0f}s</div></div>
  <div class="box hi"><div class="k">12 staff / year</div><div class="v">{money(S[1]['cost_per_year'])}</div><div class="n">published list rate</div></div>
 </div>
 <div class="grid g2">
  <div>
   <table>
    <tr><th>Users</th><th class="n">Runs / mo</th><th class="n">Cost / year</th></tr>
    <tr><td>12 (this programme)</td><td class="n">{S[1]['runs_per_month']:,.0f}</td><td class="n">{money(S[1]['cost_per_year'])}</td></tr>
    <tr><td>100</td><td class="n">{S[2]['runs_per_month']:,.0f}</td><td class="n">{money(S[2]['cost_per_year'])}</td></tr>
    <tr><td>10,000</td><td class="n">{S[3]['runs_per_month']:,.0f}</td><td class="n">{money(S[3]['cost_per_year'])}</td></tr>
   </table>
   <p class="cap">Priced at <code>gpt-6-luna</code>'s published list rate on Azure:
   $0.110 / $0.011 cached / $0.550 per million tokens. Cost controls: tool scoping
   (19 schemas &rarr; 3 per agent), reasoning off, a zero-token calculator path,
   capped output.</p>
  </div>
  <div class="box ok">
   <p style="font-size:.6em;line-height:1.5;margin:0">Running it for the whole field team costs
   <b>{money(S[1]['cost_per_year'])}</b> against <b>{money(SAVED*ORG['hourly'],0)}</b> of analyst time.</p>
   <p style="font-size:.6em;line-height:1.5;margin:12px 0 0"><b class="amber">Even at one hundred
   times the published rate</b>, that is {money(S[1]['cost_per_year']*100,0)} against
   {money(SAVED*ORG['hourly'],0)}. The model is not the cost of running this &mdash;
   the people are.</p>
  </div>
 </div>
</section>

<!-- 8 -->
<section>
 <p class="eyebrow">Safety</p>
 <h2>The producer never reaches the model</h2>
 <div class="grid g2" style="margin-top:12px;grid-template-columns:1fr 1.05fr;align-items:start">
  <div><img class="shot" src="{b64('08_privacy_receipt.jpg')}" alt="Privacy receipt">
   <p class="cap">Shown before the run starts and again in the result &mdash;
   <b>a count the user can check</b>, not a policy they have to believe.</p></div>
  <div>
   <div class="box ok" style="margin-bottom:11px">
    <div class="k">Order of operations</div>
    <p style="font-size:.48em;line-height:1.5;margin:7px 0 0">
    Injection scan &rarr; jurisdiction &rarr; <b>location</b>: all local, on the original.
    <b class="amber">Then redact.</b> Then the agents, which see only the redacted text.
    Location detection needs the address &mdash; which is why it runs first, and locally.</p></div>
   <div class="grid g2" style="gap:11px;margin-bottom:11px">
    <div class="box no"><div class="k">Removed</div>
     <p style="font-size:.44em;line-height:1.45;margin:6px 0 0">Names, address, phone, email,
     farm and tract numbers, contract numbers, postcode, coordinates.</p></div>
    <div class="box ok"><div class="k">Kept</div>
     <p style="font-size:.44em;line-height:1.45;margin:6px 0 0">Nine practice lines, every quantity,
     the county, the EQIP / CREP / DEQ signals.</p></div>
   </div>
   <div class="box hi"><p style="font-size:.48em;line-height:1.45;margin:0">
    <b>Output identical before and after:</b> same seven creditable practices,
    same 3,087.8 lb N, same $27,130. Removing the person costs the screening nothing.</p></div>
  </div>
 </div>
 <div class="grid g4" style="margin-top:14px">
  <div class="box"><div class="k">Prompt injection</div><p style="font-size:.42em;margin:5px 0 0;line-height:1.4">Three injected instructions quoted and <b>not obeyed</b>. Clean plans: zero findings.</p></div>
  <div class="box"><div class="k">Agent malfunction</div><p style="font-size:.42em;margin:5px 0 0;line-height:1.4">The review desk once contradicted its own tool. <b>The panel was right.</b></p></div>
  <div class="box"><div class="k">Wrong match</div><p style="font-size:.42em;margin:5px 0 0;line-height:1.4"><code>subsoiler</code> once matched <b>Biofilters</b>. Now refused.</p></div>
  <div class="box"><div class="k">Wrong state</div><p style="font-size:.42em;margin:5px 0 0;line-height:1.4">A PA plan priced on VA rates looked normal. Now detected and refused.</p></div>
 </div>
</section>

<!-- 9 -->
<section>
 <p class="eyebrow">Impact</p>
 <h2>Same team, more farmers reached</h2>
 {AFTER}
 <div class="grid g4" style="margin-top:20px">
  <div class="box ok"><div class="k">First estimate</div><div class="v">4h &rarr; 33s</div></div>
  <div class="box ok"><div class="k">Turnaround</div><div class="v">10d &rarr; same day</div></div>
  <div class="box ok"><div class="k">Analyst hours</div><div class="v">&minus;{num(SAVED)}</div><div class="n">{ORG['saved_pct']:.0%}, 30 min review kept</div></div>
  <div class="box hi"><div class="k">Conversations</div><div class="v">5 &rarr; 2</div><div class="n">user's own figure</div></div>
 </div>
</section>

<!-- 10 -->
<section>
 <p class="eyebrow">The user, and what is next</p>
 <h2>&ldquo;We would certainly use it&rdquo;</h2>
 <div class="grid g2" style="margin-top:18px">
  <div>
   <p class="q">This is so useful, particularly the reading of the conservation plans&hellip; we would
   certainly use it and encourage all of our outreach specialists to use it.<br><br>
   I worry about farmers' trust of the numbers, and their willingness to enter data like a
   conservation plan into AI. Also, this wouldn't work for our Amish farmers &mdash; roughly 10% of
   farmers &mdash; since they don't use technology.
   <cite>Director, Revolving Water Fund</cite></p>
  </div>
  <div>
   <div class="box no" style="margin-bottom:14px"><div class="k">Honest limits</div>
    <p style="font-size:.54em;line-height:1.45;margin:8px 0 0">35% of lost projects are a data-trust
    problem this tool does not solve &mdash; and may worsen. ~10% of producers are excluded outright,
    so the 60% conversation saving applies to about 90% of the base.</p></div>
   <div class="box ok"><div class="k">Next, in order</div>
    <p style="font-size:.54em;line-height:1.45;margin:8px 0 0">1. Solve the data-trust problem &mdash;
    field-staff-mediated mode.<br>2. Per-user accounts with a private project repository.<br>
    3. Pennsylvania and Maryland rates.<br>4. Ask the ambiguous cost-share year outright.</p></div>
  </div>
 </div>
</section>

</div></div>
<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js"></script>
<script>
Reveal.initialize({{hash:true,slideNumber:'c/t',transition:'fade',
 width:1360,height:820,margin:0.055,controlsTutorial:false}});
</script>
</body></html>"""

out = ROOT / "slides.html"
out.write_text(HTML)
print(f"slides.html written ({out.stat().st_size/1024:.0f} KB)")
