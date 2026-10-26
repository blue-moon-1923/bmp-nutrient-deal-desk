"""People-workflow diagrams: how work moved before and after."""

def _defs():
    return """<defs>
 <marker id="ar" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
  <path d="M0,0 L9,4.5 L0,9 z" fill="#8a9a99"/></marker>
 <marker id="arw" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
  <path d="M0,0 L9,4.5 L0,9 z" fill="#ffb026"/></marker>
 <marker id="arg" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
  <path d="M0,0 L9,4.5 L0,9 z" fill="#5fa37c"/></marker>
</defs>
<style>
 .person{fill:#0b2342;stroke:#2d5f8a;stroke-width:1.6;rx:10}
 .tool{fill:#143b32;stroke:#5fa37c;stroke-width:1.8;rx:10}
 .block{fill:#4a1f1f;stroke:#c2614a;stroke-width:1.8;rx:10}
 .nm{font:600 17px Figtree,system-ui,sans-serif;fill:#fff}
 .rl{font:13px Figtree,system-ui,sans-serif;fill:#9fb6c9}
 .tg{font:600 13px Figtree,system-ui,sans-serif;fill:#ffb026}
 .tgg{font:600 13px Figtree,system-ui,sans-serif;fill:#8fd3ab}
 .fl{stroke:#8a9a99;stroke-width:1.8;fill:none;marker-end:url(#ar)}
 .flw{stroke:#ffb026;stroke-width:2.2;fill:none;marker-end:url(#arw)}
 .flg{stroke:#5fa37c;stroke-width:2.2;fill:none;marker-end:url(#arg)}
 .cap{font:600 12px Figtree,system-ui,sans-serif;fill:#6f8694;letter-spacing:.09em}
</style>"""


BEFORE = f"""<svg viewBox="0 0 1180 300" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto">
{_defs()}
 <text x="0" y="16" class="cap">BEFORE</text>

 <rect class="person" x="0" y="42" width="196" height="92"/>
 <text x="22" y="76" class="nm">Farmer</text>
 <text x="22" y="99" class="rl">&ldquo;What do I have to do,</text>
 <text x="22" y="117" class="rl">and what do I get paid?&rdquo;</text>

 <rect class="person" x="258" y="42" width="196" height="92"/>
 <text x="280" y="76" class="nm">12 field staff</text>
 <text x="280" y="99" class="rl">collect basic farm</text>
 <text x="280" y="117" class="rl">information, then wait</text>

 <rect class="block" x="516" y="42" width="196" height="92"/>
 <text x="538" y="76" class="nm">1 analyst</text>
 <text x="538" y="99" class="rl">reads a 20&ndash;100 page plan,</text>
 <text x="538" y="117" class="rl">calculates by hand</text>
 <text x="538" y="156" class="tg">4 hours per project</text>

 <rect class="person" x="774" y="42" width="196" height="92"/>
 <text x="796" y="76" class="nm">Estimate</text>
 <text x="796" y="99" class="rl">goes back out to</text>
 <text x="796" y="117" class="rl">the producer</text>

 <path class="fl" d="M196 88 L252 88"/>
 <path class="fl" d="M454 88 L510 88"/>
 <path class="flw" d="M712 88 L768 88"/>
 <path class="flw" d="M872 138 C 872 210, 98 210, 98 140" />
 <text x="408" y="232" class="tg">up to 10 days</text>

 <rect class="block" x="1010" y="42" width="170" height="92"/>
 <text x="1030" y="72" class="nm">The queue</text>
 <text x="1030" y="95" class="rl">250 scoped a year</text>
 <text x="1030" y="113" class="rl">1,000 analyst hours</text>
 <text x="1030" y="156" class="tg">80% never convert</text>
</svg>"""


AFTER = f"""<svg viewBox="0 0 1180 300" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto">
{_defs()}
 <text x="0" y="16" class="cap">AFTER</text>

 <rect class="person" x="0" y="42" width="196" height="92"/>
 <text x="22" y="76" class="nm">Farmer</text>
 <text x="22" y="99" class="rl">same two questions,</text>
 <text x="22" y="117" class="rl">answered on the visit</text>

 <rect class="person" x="258" y="42" width="196" height="92"/>
 <text x="280" y="76" class="nm">12 field staff</text>
 <text x="280" y="99" class="rl">upload the plan,</text>
 <text x="280" y="117" class="rl">read the answer</text>

 <rect class="tool" x="516" y="42" width="196" height="92"/>
 <text x="538" y="76" class="nm">BMP Deal Desk</text>
 <text x="538" y="99" class="rl">8 agents, 18 tools,</text>
 <text x="538" y="117" class="rl">every number from data</text>
 <text x="538" y="156" class="tgg">33 seconds</text>

 <rect class="person" x="774" y="42" width="196" height="92"/>
 <text x="796" y="76" class="nm">1 analyst</text>
 <text x="796" y="99" class="rl">reviews the screen,</text>
 <text x="796" y="117" class="rl">signs what proceeds</text>
 <text x="796" y="156" class="tgg">30 min, not 4 hours</text>

 <path class="fl" d="M196 88 L252 88"/>
 <path class="flg" d="M454 88 L510 88"/>
 <path class="flg" d="M712 88 L768 88"/>
 <path class="flg" d="M872 138 C 872 210, 98 210, 98 140"/>
 <text x="430" y="232" class="tgg">same day</text>

 <rect class="tool" x="1010" y="42" width="170" height="92"/>
 <text x="1030" y="72" class="nm">The queue</text>
 <text x="1030" y="95" class="rl">EQIP overlap caught</text>
 <text x="1030" y="113" class="rl">before the 4 hours</text>
 <text x="1030" y="156" class="tgg">704 hours returned</text>
</svg>"""
