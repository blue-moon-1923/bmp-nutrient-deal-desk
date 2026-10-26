CSS = """
:root{--navy:#001637;--teal:#0f4768;--deep:#003d47;--green:#38664f;--dgreen:#213e2d;
--sky:#3899b8;--pale:#9ed9ff;--amber:#ffb026;--ink:#14191a;--mute:#5b6666;
--paper:#fff;--line:#dfe5e4;--soft:#f6f8f7}
*{box-sizing:border-box}
body{margin:0;background:#eef1f0;color:var(--ink);
font:11.2pt/1.6 "Iowan Old Style",Georgia,"Times New Roman",serif}
.page{max-width:7.1in;margin:0 auto;background:var(--paper);padding:0.72in 0.85in 0.8in}
h1,h2,h3,h4{font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;font-weight:700;
letter-spacing:-.012em;color:var(--navy);margin:0}
h1{font-size:25pt;line-height:1.14}
h2{font-size:15pt;margin:30px 0 4px;padding-top:16px;border-top:2.5px solid var(--navy)}
h2 .n{color:var(--amber);margin-right:9px}
h3{font-size:11.6pt;margin:18px 0 5px;color:var(--teal)}
h4{font-size:10.4pt;margin:14px 0 3px;color:var(--dgreen)}
p{margin:0 0 9px}
.lead{font-size:12.4pt;color:#36403f;margin-bottom:14px}
.sub{font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;font-size:9.6pt;
color:var(--mute);letter-spacing:.02em}
a{color:var(--teal);word-break:break-word}
ul,ol{margin:0 0 10px;padding-left:19px}li{margin-bottom:4px}
table{width:100%;border-collapse:collapse;font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;
font-size:9.1pt;margin:11px 0 13px}
th{text-align:left;background:var(--soft);border-bottom:1.5px solid var(--navy);
padding:6px 7px;font-size:8pt;text-transform:uppercase;letter-spacing:.055em;color:var(--navy)}
td{padding:5px 7px;border-bottom:1px solid var(--line);vertical-align:top}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
tr.tot td{font-weight:700;border-top:1.5px solid var(--navy);background:var(--soft)}
figure{margin:15px 0;page-break-inside:avoid}
figure img{width:100%;border:1px solid var(--line);border-radius:5px;display:block}
figcaption{font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;font-size:8.4pt;
color:var(--mute);margin-top:5px;line-height:1.45}
figcaption b{color:var(--navy)}
.missing .ph{border:2px dashed var(--line);border-radius:5px;padding:40px;text-align:center;
color:var(--mute);font-family:Helvetica,Arial,sans-serif;font-size:9pt;background:var(--soft)}
blockquote{margin:13px 0;padding:11px 16px;background:var(--soft);
border-left:3.5px solid var(--green);font-size:10.6pt}
blockquote p:last-child{margin-bottom:0}
.callout{border:1px solid var(--line);border-left:3.5px solid var(--amber);
background:#fffdf7;border-radius:4px;padding:11px 15px;margin:13px 0;font-size:10.4pt}
.callout.warn{border-left-color:#b4442f;background:#fdf4f2}
.callout.ok{border-left-color:var(--green);background:#f4f8f5}
.callout h4{margin-top:0}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin:13px 0}
.kpi{border:1px solid var(--line);border-radius:5px;padding:9px 10px;background:var(--soft)}
.kpi .k{font-family:Helvetica,Arial,sans-serif;font-size:7.4pt;text-transform:uppercase;
letter-spacing:.07em;color:var(--mute)}
.kpi .v{font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;font-size:16pt;
font-weight:700;color:var(--navy);line-height:1.1;margin-top:2px}
.kpi .n{font-size:8pt;color:var(--mute)}
code{font-family:"SF Mono",Menlo,Consolas,monospace;font-size:9pt;background:var(--soft);
padding:1px 4px;border-radius:3px}
.hero{margin:-0.72in -0.85in 20px;position:relative}
.hero img{width:100%;display:block}
.hero .ov{position:absolute;inset:0;background:linear-gradient(180deg,
rgba(0,22,55,.72),rgba(0,22,55,.45) 45%,rgba(0,22,55,.88))}
.hero .tx{position:absolute;left:0.85in;right:0.85in;bottom:26px;color:#fff}
.hero h1{color:#fff;text-shadow:0 2px 16px rgba(0,10,22,.8)}
.hero .sub{color:#d9e7ee}
.meta{display:grid;grid-template-columns:auto 1fr;gap:3px 16px;font-size:9.6pt;
font-family:Helvetica,Arial,sans-serif;margin:14px 0 4px}
.meta dt{color:var(--mute)}.meta dd{margin:0}
.toc{background:var(--soft);border:1px solid var(--line);border-radius:5px;
padding:12px 17px;margin:16px 0 4px;font-family:Helvetica,Arial,sans-serif;font-size:9.4pt}
.toc ol{margin:0;padding-left:17px;columns:2;column-gap:26px}
.toc li{margin-bottom:3px}
.fn{font-size:8.6pt;color:var(--mute);border-top:1px solid var(--line);
margin-top:26px;padding-top:9px}
@media print{body{background:#fff}.page{max-width:none;padding:0.5in 0.6in}
h2{page-break-after:avoid}figure,table,.callout,blockquote{page-break-inside:avoid}}
"""
