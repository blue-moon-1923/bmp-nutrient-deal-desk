DIAGRAM = """
<svg viewBox="0 0 760 430" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto"
     role="img" aria-label="Agent architecture: a document enters deterministic pre-checks, then eight agents, with every number coming from tools over the rate tables">
 <defs>
  <marker id="a" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
   <path d="M0,0 L8,4 L0,8 z" fill="#5b6666"/></marker>
  <marker id="g" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
   <path d="M0,0 L8,4 L0,8 z" fill="#38664f"/></marker>
 </defs>
 <style>
  .bx{fill:#fff;stroke:#0f4768;stroke-width:1.4;rx:6}
  .bd{fill:#f4f8f5;stroke:#38664f;stroke-width:1.4;rx:6}
  .bt{fill:#eef4f8;stroke:#003d47;stroke-width:1.4;rx:6}
  .t{font:600 11px Helvetica,Arial,sans-serif;fill:#001637}
  .s{font:9px Helvetica,Arial,sans-serif;fill:#5b6666}
  .lbl{font:600 9px Helvetica,Arial,sans-serif;fill:#5b6666;letter-spacing:.06em}
  .ln{stroke:#5b6666;stroke-width:1.2;fill:none;marker-end:url(#a)}
  .lg{stroke:#38664f;stroke-width:1.2;fill:none;marker-end:url(#g);stroke-dasharray:4 3}
 </style>

 <text x="8" y="14" class="lbl">INPUT</text>
 <rect class="bt" x="8" y="22" width="132" height="54"/>
 <text x="18" y="42" class="t">Conservation plan</text>
 <text x="18" y="56" class="s">PDF or text, any format</text>
 <text x="18" y="68" class="s">or a practice list</text>

 <text x="8" y="104" class="lbl">DETERMINISTIC, BEFORE ANY MODEL</text>
 <rect class="bd" x="8" y="112" width="132" height="46"/>
 <text x="18" y="130" class="t">Injection scan</text>
 <text x="18" y="144" class="s">text aimed at the agent</text>
 <rect class="bd" x="8" y="166" width="132" height="46"/>
 <text x="18" y="184" class="t">Jurisdiction check</text>
 <text x="18" y="198" class="s">is this a Virginia farm?</text>
 <rect class="bd" x="8" y="220" width="132" height="46"/>
 <text x="18" y="238" class="t">Risk review</text>
 <text x="18" y="252" class="s">6 field-intake flags</text>

 <text x="176" y="14" class="lbl">AGENTS &mdash; gpt-6-luna</text>
 <rect class="bx" x="176" y="22" width="150" height="42"/>
 <text x="186" y="39" class="t">1. Plan reader</text>
 <text x="186" y="54" class="s">extract + validate names</text>
 <rect class="bx" x="176" y="72" width="150" height="42"/>
 <text x="186" y="89" class="t">2. Eligibility</text>
 <text x="186" y="104" class="s">what the farm could host</text>
 <rect class="bx" x="176" y="122" width="150" height="42"/>
 <text x="186" y="139" class="t">3. Alignment</text>
 <text x="186" y="154" class="s">sheet, width, duration</text>
 <rect class="bx" x="176" y="172" width="150" height="42"/>
 <text x="186" y="189" class="t">4. Opportunity</text>
 <text x="186" y="204" class="s">what is not taken</text>
 <rect class="bx" x="176" y="222" width="150" height="42"/>
 <text x="186" y="239" class="t">5. Quantification</text>
 <text x="186" y="254" class="s">the only numeric role</text>
 <rect class="bx" x="176" y="272" width="150" height="42"/>
 <text x="186" y="289" class="t">6. Verification</text>
 <text x="186" y="304" class="s">inspection schedule</text>
 <rect class="bx" x="176" y="322" width="150" height="42"/>
 <text x="186" y="339" class="t">7. Drafter</text>
 <text x="186" y="354" class="s">no tools at all</text>
 <rect class="bx" x="176" y="372" width="150" height="42" style="stroke-width:2.4"/>
 <text x="186" y="389" class="t">8. Review desk</text>
 <text x="186" y="404" class="s">decides last</text>

 <text x="362" y="14" class="lbl">TOOLS &mdash; 18, SCOPED PER AGENT</text>
 <rect class="bd" x="362" y="22" width="172" height="392"/>
 <text x="374" y="44" class="t">Deterministic layer</text>
 <text x="374" y="62" class="s">record_practice_lines</text>
 <text x="374" y="76" class="s">screen_practice_bundle</text>
 <text x="374" y="90" class="s">assess_site_eligibility</text>
 <text x="374" y="104" class="s">check_buffer_alignment</text>
 <text x="374" y="118" class="s">match_practice_names</text>
 <text x="374" y="132" class="s">get_county_rate</text>
 <text x="374" y="146" class="s">rank_practices_for_county</text>
 <text x="374" y="160" class="s">get_credit_duration</text>
 <text x="374" y="174" class="s">scan_document_for_injection</text>
 <text x="374" y="188" class="s">+ 9 more</text>
 <line x1="374" y1="206" x2="522" y2="206" stroke="#38664f" stroke-width=".8"/>
 <text x="374" y="226" class="t">Every number lives here</text>
 <text x="374" y="244" class="s">An agent may not state a</text>
 <text x="374" y="257" class="s">figure a tool did not return.</text>
 <text x="374" y="270" class="s">Tool scoping is also the</text>
 <text x="374" y="283" class="s">first cost control: 0&ndash;4</text>
 <text x="374" y="296" class="s">schemas per agent, not 18.</text>
 <line x1="374" y1="314" x2="522" y2="314" stroke="#38664f" stroke-width=".8"/>
 <text x="374" y="334" class="t">Data</text>
 <text x="374" y="352" class="s">24,704 county rate rows</text>
 <text x="374" y="366" class="s">96 counties, 270 practices</text>
 <text x="374" y="380" class="s">38 reference-guide sheets</text>
 <text x="374" y="394" class="s">11 hydrogeomorphic regions</text>

 <text x="570" y="14" class="lbl">OUTPUT</text>
 <rect class="bt" x="570" y="22" width="182" height="78"/>
 <text x="580" y="42" class="t">Reductions and cost</text>
 <text x="580" y="58" class="s">lb N, lb P, lb sediment</text>
 <text x="580" y="72" class="s">total cost, $/lb, amortised</text>
 <text x="580" y="90" class="s">with the arithmetic shown</text>
 <rect class="bt" x="570" y="110" width="182" height="62"/>
 <text x="580" y="130" class="t">Creditability</text>
 <text x="580" y="146" class="s">creditable / not additional /</text>
 <text x="580" y="160" class="s">double counted / ask</text>
 <rect class="bt" x="570" y="182" width="182" height="62"/>
 <text x="580" y="202" class="t">Opportunities</text>
 <text x="580" y="218" class="s">practices not taken, with</text>
 <text x="580" y="232" class="s">their site requirements</text>
 <rect class="bt" x="570" y="254" width="182" height="62"/>
 <text x="580" y="274" class="t">Verification plan</text>
 <text x="580" y="290" class="s">inspection schedule and</text>
 <text x="580" y="304" class="s">Virginia 5-year interval</text>
 <rect class="bt" x="570" y="326" width="182" height="88"/>
 <text x="580" y="346" class="t">Decision</text>
 <text x="580" y="362" class="s">ADVANCE / NEEDS</text>
 <text x="580" y="376" class="s">INFORMATION / DO NOT</text>
 <text x="580" y="390" class="s">ADVANCE &mdash; cannot advance</text>
 <text x="580" y="404" class="s">while a blocker is open</text>

 <path class="ln" d="M74 78 L74 108"/>
 <path class="ln" d="M144 135 L172 44"/>
 <path class="ln" d="M144 189 L172 94"/>
 <path class="ln" d="M144 243 L172 390"/>
 <path class="lg" d="M330 44 L358 44"/>
 <path class="lg" d="M330 94 L358 94"/>
 <path class="lg" d="M330 144 L358 144"/>
 <path class="lg" d="M330 194 L358 194"/>
 <path class="lg" d="M330 244 L358 244"/>
 <path class="lg" d="M330 294 L358 294"/>
 <path class="lg" d="M330 394 L358 394"/>
 <path class="ln" d="M538 60 L566 60"/>
 <path class="ln" d="M538 140 L566 140"/>
 <path class="ln" d="M538 212 L566 212"/>
 <path class="ln" d="M538 284 L566 284"/>
 <path class="ln" d="M538 370 L566 370"/>
</svg>
"""
