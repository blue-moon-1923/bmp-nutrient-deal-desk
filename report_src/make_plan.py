"""Generate a large synthetic NRCS-format Virginia conservation plan.

No real farm, producer or property. Field geometry, soils and practices are
invented, but the structure follows a real plan packet: maps, soils
inventory, resource concerns, practice schedules by tract, a grazing plan,
and a verification schedule.

Specific cases are planted so a demo exercises every rule:
  * a practice funded by EQIP in a prior year   -> "ask: is the credit year funded?"
  * reductions already reported to the state    -> not creditable, double counting
  * a buffer already installed under CREP       -> not additional, structural
  * fencing and a waterline                     -> real costs, not creditable practices
  * several clean, new, creditable practices    -> counted
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fpdf import FPDF
from plan_attachments import (PLANNER, COVER_NARRATIVE, SOIL_COMPONENTS,
                              STANDARDS, RESOURCE_MATRIX, RUSLE2, ENV_REVIEW)

W, H, M = 215.9, 279.4, 16
NAVY, GREY = (30, 40, 48), (110, 118, 124)

TRACTS = [
    dict(no="2208", name="Home tract", crop=214.0, pasture=96.0, woods=22.0,
         stream="Cub Run", frontage=3150,
         fields=[("12", 64.0, "cropland"), ("14", 49.5, "cropland"),
                 ("17", 38.0, "cropland"), ("21", 5.4, "buffer"),
                 ("22", 3.1, "buffer"), ("31", 58.0, "pasture"),
                 ("32", 38.0, "pasture"), ("40", 0.8, "barnyard")]),
    dict(no="2211", name="Cross Keys tract", crop=118.0, pasture=44.0, woods=9.0,
         stream="Mill Creek", frontage=1820,
         fields=[("51", 62.0, "cropland"), ("52", 56.0, "cropland"),
                 ("55", 4.2, "buffer"), ("61", 44.0, "pasture")]),
    dict(no="2214", name="Ridge tract", crop=76.0, pasture=61.0, woods=31.0,
         stream="unnamed tributary", frontage=940,
         fields=[("71", 40.0, "cropland"), ("72", 36.0, "cropland"),
                 ("81", 61.0, "pasture")]),
]

SOILS = [("CnB","Caneyville silt loam, 2 to 6 percent slopes",18.4),
         ("CrD","Carbo-Rock outcrop complex, 15 to 25 percent slopes",11.2),
         ("FaA","Frederick silt loam, 0 to 2 percent slopes",44.1),
         ("FaB","Frederick silt loam, 2 to 7 percent slopes",37.5),
         ("GgA","Guernsey silt loam, 0 to 2 percent slopes",52.6),
         ("InA","Inman silt loam, 0 to 2 percent slopes",88.3),
         ("MnB","Murrill loam, 2 to 7 percent slopes",61.0),
         ("W","Water",2.4),
         ("WeC","Weikert channery silt loam, 8 to 15 percent slopes",32.0)]

# (practice, code, narrative, [(field, amount, unit, month, year, applied)])
PRACTICES = [
 ("Cover Crop","340",
  "Cereal rye drilled following corn silage harvest. Not harvested. No fall\n"
  "nutrient application planned on any field in this schedule.",
  [("12","64.0 ac",9,2026,None),("14","49.5 ac",9,2026,None),
   ("17","38.0 ac",9,2026,None),("51","62.0 ac",9,2026,None),
   ("52","56.0 ac",9,2026,None)]),
 ("Residue and Tillage Management, No Till","329",
  "Continuous no-till on all cropped acres. In place since 2019. Cost-shared\n"
  "under EQIP contract 68-3A75-19-112, which expired in 2024. No cost-share\n"
  "is recorded against the current compliance year.",
  [("12","64.0 ac",4,2019,"5/2019"),("14","49.5 ac",4,2019,"5/2019"),
   ("17","38.0 ac",4,2019,"5/2019"),("51","62.0 ac",4,2020,"4/2020")]),
 ("Nutrient Management","590",
  "Whole-farm plan written 2024 by the district. Reductions for the 2025\n"
  "reporting year were submitted to Virginia DEQ.",
  [("ALL","408.0 ac",3,2024,"3/2024")]),
 ("Riparian Forest Buffer","391",
  "Establish a 75-foot average width hardwood buffer along the west bank of\n"
  "Cub Run where the cropped field edge currently abuts the channel. Not\n"
  "yet installed.",
  [("21","5.4 ac",11,2026,None),("22","3.1 ac",11,2026,None)]),
 ("Riparian Forest Buffer","391",
  "Existing 40-foot buffer on the east bank, planted 2016 under CREP.\n"
  "Retained and maintained. No further work planned.",
  [("23","4.2 ac",3,2016,"4/2016")]),
 ("Riparian Forest Buffer","391",
  "New 60-foot buffer on the Cross Keys tract along Mill Creek.",
  [("55","4.2 ac",11,2027,None)]),
 ("Prescribed Grazing","528",
  "Subdivide the lower pasture into six paddocks and rotate the cow-calf herd\n"
  "on a flexible schedule. No fixed move interval is specified; the producer\n"
  "will adjust to forage conditions.",
  [("31","58.0 ac",5,2027,None),("32","38.0 ac",5,2027,None),
   ("61","44.0 ac",5,2027,None),("81","61.0 ac",5,2028,None)]),
 ("Fence","382",
  "Exclusion fencing along both banks of Cub Run and Mill Creek, and\n"
  "perimeter fencing for the new paddock divisions.",
  [("31","4,200 ft",5,2027,None),("61","2,600 ft",5,2027,None)]),
 ("Watering Facility","614",
  "Frost-free troughs with buried supply line from the existing well to serve\n"
  "the new paddocks. Nearest well is 900 feet from the paddock centre.",
  [("31","2 no",5,2027,None),("61","2 no",5,2027,None)]),
 ("Pipeline","516",
  "Buried waterline from the wellhead to the trough locations.",
  [("31","1,850 ft",5,2027,None)]),
 ("Heavy Use Area Protection","561",
  "Concrete pad and roof runoff control at the existing feeding area adjacent\n"
  "to the barnyard.",
  [("40","0.8 ac",8,2027,None)]),
 ("Conservation Crop Rotation","328",
  "Move fields 12 and 14 from continuous corn silage into a corn / small\n"
  "grain / soybean rotation.",
  [("12","64.0 ac",4,2027,None),("14","49.5 ac",4,2027,None)]),
 ("Tree/Shrub Establishment","612",
  "Shade planting in the lower paddocks at the producer's request. Not a\n"
  "silvopasture establishment; confirm the applicable practice definition\n"
  "before claiming any reduction.",
  [("32","2.0 ac",11,2027,None)]),
]


# --------------------------------------------------------------- drawing

def px(p, x0, y0, sx, sy, maxy):
    return (x0 + p[0] * sx, y0 + (maxy - p[1]) * sy)


def draw_map(pdf, x0, y0, w, h, tract, *, mode="plan"):
    """mode: plan | soils | concerns"""
    import math
    sx, sy = w / 120.0, h / 110.0
    pdf.set_fill_color(242, 246, 240); pdf.rect(x0, y0, w, h, style="F")

    polys = []
    n = len(tract["fields"])
    cols = 3
    for i, (num, ac, kind) in enumerate(tract["fields"]):
        r, c = divmod(i, cols)
        bx, by = 8 + c * 36, 8 + r * 32
        jit = ((i * 37) % 11) - 5
        poly = [(bx, by), (bx + 32 + jit * .4, by - 2 + jit * .3),
                (bx + 34 + jit * .3, by + 26), (bx + 2, by + 28 + jit * .2)]
        polys.append((num, ac, kind, poly))

    SHADE = {"cropland": (228, 236, 222), "pasture": (212, 229, 210),
             "buffer": (186, 206, 180), "barnyard": (232, 226, 214)}
    SOILSH = [(214,221,205),(224,216,198),(206,215,214),(228,224,206),
              (212,218,226),(220,212,204),(216,222,210),(226,218,210)]

    for i, (num, ac, kind, poly) in enumerate(polys):
        pts = [px(p, x0, y0, sx, sy, 110) for p in poly]
        if mode == "soils":
            pdf.set_fill_color(*SOILSH[i % len(SOILSH)])
        elif mode == "concerns":
            pdf.set_fill_color(*( (238,224,212) if kind == "cropland" else (224,234,222) ))
        else:
            pdf.set_fill_color(*SHADE[kind])
        pdf.set_draw_color(92, 112, 92); pdf.set_line_width(0.45)
        pdf.polygon(pts, style="DF")
        cx = sum(p[0] for p in pts) / 4; cy = sum(p[1] for p in pts) / 4
        pdf.set_font("Helvetica", "B", 6.6); pdf.set_text_color(40, 60, 40)
        label = num if mode != "soils" else SOILS[i % len(SOILS)][0]
        pdf.text(cx - 3, cy - 1, label)
        if mode == "plan":
            pdf.set_font("Helvetica", "", 4.9); pdf.set_text_color(76, 96, 76)
            pdf.text(cx - 7, cy + 3, f"{ac:g} ac")
            pdf.text(cx - 7, cy + 6.4, kind)
        elif mode == "concerns" and kind == "cropland":
            pdf.set_font("Helvetica", "", 4.6); pdf.set_text_color(140, 70, 40)
            pdf.text(cx - 8, cy + 3.4, "sheet & rill")

    # stream and buffer
    stream = [(4, 8), (24, 14), (44, 12), (64, 18), (84, 16), (104, 22), (118, 20)]
    pts = [px(p, x0, y0, sx, sy, 110) for p in stream]
    pdf.set_draw_color(176, 198, 170); pdf.set_line_width(2.4)
    for a, b in zip(pts, pts[1:]): pdf.line(a[0], a[1] - 1.1, b[0], b[1] - 1.1)
    pdf.set_draw_color(96, 150, 186); pdf.set_line_width(1.2)
    for a, b in zip(pts, pts[1:]): pdf.line(a[0], a[1], b[0], b[1])
    pdf.set_font("Helvetica", "I", 5.6); pdf.set_text_color(70, 110, 150)
    pdf.text(pts[2][0], pts[2][1] + 3.6, tract["stream"])

    # north arrow + scale
    pdf.set_text_color(60); pdf.set_font("Helvetica", "B", 7.4)
    pdf.text(x0 + w - 11, y0 + 9, "N")
    pdf.set_draw_color(60); pdf.set_line_width(0.45)
    pdf.line(x0 + w - 9, y0 + 10.4, x0 + w - 9, y0 + 4.6)
    pdf.line(x0 + w - 9, y0 + 4.6, x0 + w - 10.7, y0 + 7)
    pdf.line(x0 + w - 9, y0 + 4.6, x0 + w - 7.3, y0 + 7)
    bx, by = x0 + 6, y0 + h - 6
    pdf.set_line_width(0.6); pdf.line(bx, by, bx + 22, by)
    for t in (0, 11, 22): pdf.line(bx + t, by - 1.2, bx + t, by + 1.2)
    pdf.set_font("Helvetica", "", 5.2); pdf.set_text_color(70)
    pdf.text(bx - 1, by + 3.9, "0"); pdf.text(bx + 18, by + 3.9, "1,320 ft")
    pdf.set_text_color(0)


def legend(pdf, x, y, items):
    pdf.set_font("Helvetica", "", 6.2)
    for i, (col, lab) in enumerate(items):
        yy = y + i * 4.8
        pdf.set_fill_color(*col); pdf.set_draw_color(110)
        pdf.rect(x, yy, 4, 3, style="DF")
        pdf.set_text_color(45); pdf.text(x + 5.8, yy + 2.5, lab)
    pdf.set_text_color(0)


class Plan(FPDF):
    def footer(self):
        self.set_y(-12)
        self.set_font("Courier", "", 6.6); self.set_text_color(130)
        self.cell(0, 4, "USDA is an equal opportunity provider, employer and lender.", align="L")
        self.cell(0, 4, f"3/14/2026   Page {self.page_no()} of {{nb}}", align="R")
        self.set_text_color(0)


def head(pdf, title, sub=""):
    pdf.set_font("Helvetica", "B", 8.6); pdf.set_text_color(30)
    pdf.text(M, M + 2, "USDA Natural Resources Conservation Service")
    pdf.set_font("Helvetica", "", 7); pdf.set_text_color(100)
    pdf.text(M, M + 6, "Shenandoah Valley Soil and Water Conservation District   |   "
                       "Field Office: ROCKINGHAM")
    pdf.set_draw_color(165); pdf.set_line_width(0.28)
    pdf.line(M, M + 8.2, W - M, M + 8.2)
    pdf.set_font("Helvetica", "B", 12); pdf.set_text_color(20)
    pdf.text(M, M + 16, title)
    if sub:
        pdf.set_font("Helvetica", "", 7.8); pdf.set_text_color(95); pdf.text(M, M + 21, sub)
    pdf.set_text_color(0)


def idblock(pdf, y, tract=None):
    pdf.set_font("Courier", "", 7.2); pdf.set_text_color(55)
    rows = ["Smith Family Farms, LLC", "4820 Cross Keys Road",
            "Harrisonburg, Rockingham County, VA 22801", ""]
    if tract:
        rows += [f"FARM: 4417    TRACT: {tract['no']}    WATERSHED: 0207",
                 f"ACC ID: 2605100{tract['no']}", "",
                 f"CROPLAND {tract['crop']:.1f} ac   PASTURE {tract['pasture']:.1f} ac   "
                 f"WOODLAND {tract['woods']:.1f} ac",
                 f"{tract['stream'].upper()} FRONTAGE - {tract['frontage']:,} ft"]
    else:
        rows += ["FARM: 4417    TRACTS: 2208, 2211, 2214", "ACC ID: 26051004417", "",
                 "TOTAL CROPLAND 408.0 ac   TOTAL PASTURE 201.0 ac"]
    rows.append("ALL ACRES AND BOUNDARIES ARE APPROXIMATE")
    for i, r in enumerate(rows):
        pdf.text(M, y + i * 3.6, r)
    pdf.set_text_color(0)
    return y + len(rows) * 3.6


def mono_block(pdf, lines, size=8.2):
    pdf.set_font("Courier", "", size)
    for ln in lines:
        if pdf.get_y() > H - 24:
            pdf.add_page(); head(pdf, "CONSERVATION PLAN", "continued"); pdf.set_y(M + 26)
            pdf.set_font("Courier", "", size)
        if set(ln) <= {"-", " "} and len(ln) > 20:
            pdf.set_draw_color(185); pdf.line(M, pdf.get_y() + 1.3, W - M, pdf.get_y() + 1.3)
            pdf.ln(3.8); continue
        bold = ln.endswith(("---",)) or (" - " in ln and not ln.startswith(" ")
                                         and ln.split(" - ")[-1].strip().isdigit())
        pdf.set_font("Courier", "B" if bold else "", size)
        pdf.cell(0, 3.7, ln[:92], new_x="LMARGIN", new_y="NEXT")


def build(out_path: str):
    pdf = Plan(orientation="P", unit="mm", format="Letter")
    pdf.set_auto_page_break(auto=True, margin=16)

    # ---- 1 cover
    pdf.add_page(); head(pdf, "CONSERVATION PLAN", "Whole farm  -  three tracts")
    y = idblock(pdf, M + 28)
    pdf.set_y(y + 6); pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, "OBJECTIVE", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Courier", "", 8.2)
    for ln in ["To maintain a viable corn silage and small grain rotation while",
               "reducing nutrient and sediment delivery to Cub Run and Mill Creek,",
               "and to improve forage distribution for the cow-calf herd.", "",
               "The producer intends to retire a portion of the cropland on the home",
               "tract into perennial pasture over the planning period."]:
        pdf.cell(0, 3.8, ln, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3); pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, "RESOURCE CONCERNS", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Courier", "", 8.2)
    for ln in ["  Sheet and rill erosion on cropland slopes above both streams.",
               "  Livestock have direct access to Cub Run in the lower pasture block.",
               "  Nutrient management records incomplete for the east fields.",
               "  Forage distribution limited by a single watering point."]:
        pdf.cell(0, 3.8, ln, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 9); pdf.cell(0, 5, "PLAN CONTENTS", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Courier", "", 8)
    for ln in ["  Conservation plan map, soils map and resource concerns map, per tract",
               "  Soils inventory report", "  Practice schedule", "  Grazing plan",
               "  Operation and maintenance", "  Verification schedule",
               "  Programme and cost-share notes", "  Signatures"]:
        pdf.cell(0, 3.7, ln, new_x="LMARGIN", new_y="NEXT")

    # ---- per-tract map sets (3 pages each)
    for t in TRACTS:
        pdf.add_page(); head(pdf, "CONSERVATION PLAN MAP", f"Tract {t['no']}  -  {t['name']}")
        y = idblock(pdf, M + 28, t)
        draw_map(pdf, M, y + 3, W - 2 * M, 112, t, mode="plan")
        legend(pdf, M, y + 119, [((228,236,222),"Cropland"),((212,229,210),"Pasture"),
                                 ((186,206,180),"Riparian buffer, planned or existing"),
                                 ((232,226,214),"Barnyard / heavy use area"),
                                 ((96,150,186), f"Perennial stream - {t['stream']}")])

        pdf.add_page(); head(pdf, "SOILS MAP", f"Tract {t['no']}  -  {t['name']}")
        draw_map(pdf, M, M + 26, W - 2 * M, 104, t, mode="soils")
        pdf.set_y(M + 136); pdf.set_font("Helvetica", "B", 8.4)
        pdf.cell(0, 5, "Soils Inventory Report", new_x="LMARGIN", new_y="NEXT"); pdf.ln(1)
        pdf.set_font("Courier", "B", 6.8)
        pdf.cell(16, 4.4, "Symbol"); pdf.cell(104, 4.4, "Map Unit Name")
        pdf.cell(20, 4.4, "Acres", align="R"); pdf.cell(18, 4.4, "Percent", align="R"); pdf.ln()
        pdf.set_draw_color(150); pdf.line(M, pdf.get_y(), W - M, pdf.get_y()); pdf.ln(1)
        pdf.set_font("Courier", "", 6.8)
        tot = sum(s[2] for s in SOILS)
        scale = (t["crop"] + t["pasture"] + t["woods"]) / tot
        for sym, nm, ac in SOILS:
            a = ac * scale
            pdf.cell(16, 4.1, sym); pdf.cell(104, 4.1, nm[:56])
            pdf.cell(20, 4.1, f"{a:.1f}", align="R")
            pdf.cell(18, 4.1, f"{a/ (tot*scale) *100:.0f}%", align="R"); pdf.ln()
        pdf.line(M, pdf.get_y() + .5, W - M, pdf.get_y() + .5); pdf.ln(1.6)
        pdf.set_font("Courier", "B", 6.8)
        pdf.cell(120, 4.1, "Total:"); pdf.cell(20, 4.1, f"{tot*scale:.1f}", align="R")
        pdf.cell(18, 4.1, "100%", align="R")

        pdf.add_page(); head(pdf, "RESOURCE CONCERNS MAP", f"Tract {t['no']}  -  {t['name']}")
        draw_map(pdf, M, M + 26, W - 2 * M, 112, t, mode="concerns")
        legend(pdf, M, M + 142, [((238,224,212),"Sheet and rill erosion"),
                                 ((224,234,222),"Forage distribution"),
                                 ((96,150,186),"Direct livestock access to water")])

    # ---- practice schedule
    pdf.add_page(); head(pdf, "CONSERVATION PLAN", "Practice schedule")
    pdf.set_y(M + 26)
    lines = ["Associated Ag Land                          Tracts: 2208, 2211, 2214",
             "-" * 70, ""]
    for name, code, narr, rows in PRACTICES:
        lines.append(f"{name} - {code}")
        lines += narr.splitlines()
        lines.append("                 Planned                        Applied")
        lines.append("  Field    Amount    Month  Year          Amount      Date")
        tot = 0.0; unit = ""
        for fld, amt, mo, yr, applied in rows:
            ap = f"{amt:>12}   {applied}" if applied else ""
            lines.append(f"  {fld:<8} {amt:>9} {mo:>6}  {yr}        {ap}")
            try:
                tot += float(amt.split()[0].replace(",", "")); unit = amt.split()[1]
            except (ValueError, IndexError):
                pass
        if tot:
            lines.append(f"                                    Total: {tot:,.1f} {unit}")
        lines.append("")
    mono_block(pdf, lines)

    # ---- grazing plan
    pdf.add_page(); head(pdf, "GRAZING PLAN", "Prescribed Grazing - 528")
    pdf.set_y(M + 26)
    mono_block(pdf, [
     "OBJECTIVE",
     "  Improve forage utilisation and distribute grazing pressure away from",
     "  the stream corridor on tracts 2208, 2211 and 2214.", "",
     "PADDOCK LAYOUT",
     "  Field 31   58.0 ac   six paddocks, nominal 9.7 ac each",
     "  Field 32   38.0 ac   four paddocks, nominal 9.5 ac each",
     "  Field 61   44.0 ac   four paddocks, nominal 11.0 ac each",
     "  Field 81   61.0 ac   layout to be determined, year 3", "",
     "MOVE SCHEDULE",
     "  No fixed interval is prescribed. The producer will move stock on",
     "  forage condition, with a target residual height of 3 to 4 inches and",
     "  a minimum 21 day rest in the growing season.", "",
     "  A written move schedule is NOT a condition of this plan. Where NRCS",
     "  prescribed-grazing cost-share is sought, that programme's own plan",
     "  requirement applies.", "",
     "WATER",
     "  Two frost-free troughs per block, supplied from the existing well by",
     "  buried pipeline. Nearest well is 900 ft from the paddock centre on",
     "  tract 2208. Well yield to be confirmed before pipeline design.", "",
     "FORAGE",
     "  Existing stand is predominantly tall fescue with mixed clover.",
     "  Overseeding is not planned in the first two years.", "",
     "SHADE",
     "  Producer has requested shade in the lower paddocks. Tree and shrub",
     "  establishment is scheduled on field 32. This is a shade planting and",
     "  is not proposed as silvopasture establishment."])

    # ---- O&M
    pdf.add_page(); head(pdf, "OPERATION AND MAINTENANCE")
    pdf.set_y(M + 26)
    mono_block(pdf, [
     "COVER CROP - 340",
     "  Seed at the rate and date in the specification sheet. Do not apply",
     "  fall nutrients to any field in this schedule. Terminate ahead of the",
     "  following crop per label.", "",
     "RESIDUE AND TILLAGE MANAGEMENT, NO TILL - 329",
     "  Maintain 15 percent or greater residue cover immediately after",
     "  planting. Document residue counts annually.", "",
     "RIPARIAN FOREST BUFFER - 391",
     "  Protect from livestock for the life of the practice. Replace losses",
     "  to maintain the planted stem count through year three. Control",
     "  competing vegetation for the first two growing seasons.", "",
     "FENCE - 382",
     "  Inspect annually and after major storm events. Repair promptly where",
     "  exclusion fencing is breached.", "",
     "WATERING FACILITY - 614 / PIPELINE - 516",
     "  Drain and winterise as required. Inspect the supply line for leaks at",
     "  each seasonal start-up.", "",
     "HEAVY USE AREA PROTECTION - 561",
     "  Scrape and remove accumulated material as needed. Maintain roof",
     "  runoff conveyance clear of debris."])

    # ---- verification schedule
    pdf.add_page(); head(pdf, "VERIFICATION SCHEDULE")
    pdf.set_y(M + 26)
    mono_block(pdf, [
     "Virginia verifies on a five-year interval.", "",
     "  Practice                              Interval   Responsible",
     "  " + "-" * 62,
     "  Cover Crop - 340                      annual     producer records",
     "  No Till - 329                         annual     producer records",
     "  Nutrient Management - 590             annual     district",
     "  Riparian Forest Buffer - 391          5 year     district",
     "  Prescribed Grazing - 528              5 year     district",
     "  Heavy Use Area Protection - 561       5 year     district",
     "  Conservation Crop Rotation - 328      annual     producer records", "",
     "  Responsibility for the 2027 and later inspections has not yet been",
     "  assigned. A staffed verification plan is required before the first",
     "  structural practice is certified.", "",
     "NOTE ON CREDIT DURATION",
     "  Credit duration is the period a practice counts WITHOUT inspection.",
     "  With inspection it continues to be credited. A missed inspection is",
     "  how a project silently loses its reductions."])

    # ---- programme notes
    pdf.add_page(); head(pdf, "PROGRAMME AND COST-SHARE NOTES")
    pdf.set_y(M + 26)
    mono_block(pdf, [
     "EQIP",
     "  Contract 68-3A75-19-112 covered no-till establishment on tracts 2208",
     "  and 2211. The contract expired in 2024. No cost-share is recorded",
     "  against the current compliance year.", "",
     "CREP",
     "  The 40-foot buffer on the east bank of Cub Run (field 23) was planted",
     "  in 2016 under CREP and remains in place.", "",
     "STATE REPORTING",
     "  Nutrient management reductions for the 2025 reporting year were",
     "  submitted to Virginia DEQ.", "",
     "VIRGINIA AGRICULTURAL COST SHARE",
     "  Perimeter and exclusion fencing, watering facilities and pipeline are",
     "  expected to be cost-shared in part. Final shares to be set at",
     "  contracting.", "",
     "ITEMS THAT ARE COSTS, NOT PRACTICES",
     "  Fencing, pipeline and well work are necessary to deliver the grazing",
     "  system. They are not themselves creditable reduction practices."])

    # ---- signatures
    pdf.add_page(); head(pdf, "SIGNATURES")
    pdf.set_y(M + 30)
    pdf.set_font("Courier", "", 8.4)
    for lbl in ["Producer", "District Conservationist", "District Representative"]:
        pdf.cell(0, 6, lbl, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(7); pdf.set_draw_color(120)
        pdf.line(M, pdf.get_y(), M + 90, pdf.get_y())
        pdf.line(M + 104, pdf.get_y(), M + 150, pdf.get_y())
        pdf.set_font("Courier", "", 6.6); pdf.set_text_color(120)
        pdf.text(M, pdf.get_y() + 3.6, "signature")
        pdf.text(M + 104, pdf.get_y() + 3.6, "date")
        pdf.set_text_color(0); pdf.set_font("Courier", "", 8.4); pdf.ln(14)
    pdf.ln(6); pdf.set_font("Courier", "", 7)
    pdf.multi_cell(0, 4,
      "This plan is a synthetic document created for software testing. No real "
      "farm, producer or property is described. Field geometry, soils, acreages "
      "and practice schedules are invented.")

    # ================= ATTACHMENT PACKET =================

    # ---- planner narrative
    for title, body in COVER_NARRATIVE:
        pdf.add_page(); head(pdf, title.upper(), PLANNER)
        pdf.set_y(M + 26); mono_block(pdf, body)

    # ---- soil map unit descriptions
    pdf.add_page(); head(pdf, "MAP UNIT DESCRIPTION", "Brief, generated")
    pdf.set_y(M + 26)
    mono_block(pdf, [
      "Generated brief soil descriptions are created for major soil",
      "components. The soil component is a part of the map unit. Each map",
      "unit is made up of one or more components.", "",
      "This report is not a substitute for a site specific investigation.",
      "",
      "Components in this survey area are listed on the following pages in",
      "order of extent within the planning unit."])
    for name, sym, pct, body in SOIL_COMPONENTS:
        pdf.add_page(); head(pdf, f"COMPONENT: {name}", f"Map unit symbol {sym}  -  {pct}% of planning unit")
        pdf.set_y(M + 26); mono_block(pdf, body + ["", "",
          "INTERPRETATIONS", "",
          f"  Hydrologic soil group          {'B' if pct > 20 else 'C'}",
          f"  Farmland classification        {'Prime farmland' if pct > 20 else 'Farmland of statewide importance'}",
          f"  Ecological site                F147XY{200+pct}VA",
          "  Hydric rating                  No" if name != "Inman" else
          "  Hydric rating                  Partially hydric"])

    # ---- conservation practice standards
    for title, code, unit, defn, purposes, criteria in STANDARDS:
        pdf.add_page()
        head(pdf, "CONSERVATION PRACTICE STANDARD", f"{title}  ({code})")
        pdf.set_y(M + 26)
        mono_block(pdf, [
          f"Code {code}                                    Unit: {unit}", "",
          "DEFINITION", ""] + ["  " + l for l in _wrap(defn)] + ["",
          "PURPOSE", "",
          "  This practice may be applied to support one or more of the",
          "  following purposes:", ""] +
          [f"    - {p}" for p in purposes] + ["",
          "CONDITIONS WHERE PRACTICE APPLIES", "",
          "  On land where the identified resource concern can be addressed",
          "  by this practice and where the criteria below can be met."])
        pdf.add_page()
        head(pdf, "CONSERVATION PRACTICE STANDARD", f"{title}  ({code})  -  criteria")
        pdf.set_y(M + 26)
        mono_block(pdf, ["CRITERIA", ""] +
          [("  " + c) if c else "" for c in criteria] + ["",
          "CONSIDERATIONS", "",
          "  Consider the effect on the water budget, on downstream flows,",
          "  and on habitat. Consider the compatibility of the practice with",
          "  the producer's equipment and management.", "",
          "PLANS AND SPECIFICATIONS", "",
          "  Prepare plans and specifications that describe the requirements",
          "  for applying the practice to achieve its intended purpose.", "",
          "OPERATION AND MAINTENANCE", "",
          "  Prepare an operation and maintenance plan with the producer.",
          "  Review it periodically and revise as the operation changes.", "",
          "REFERENCES", "",
          "  Field Office Technical Guide, Section IV.",
          "  Virginia Agricultural BMP Manual, current edition."])

    # ---- resource concern assessment
    pdf.add_page(); head(pdf, "RESOURCE CONCERN ASSESSMENT", "Whole farm")
    pdf.set_y(M + 26)
    pdf.set_font("Courier", "", 7.4)
    pdf.cell(0, 4, "  Y = concern identified   P = partially treated   N = not a concern",
             new_x="LMARGIN", new_y="NEXT"); pdf.ln(2)
    for group, rows in RESOURCE_MATRIX:
        if pdf.get_y() > H - 48:
            pdf.add_page(); head(pdf, "RESOURCE CONCERN ASSESSMENT", "continued"); pdf.set_y(M + 26)
        pdf.set_font("Courier", "B", 7.6)
        pdf.cell(0, 5, group, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Courier", "", 7)
        pdf.cell(70, 4, "  Concern"); pdf.cell(14, 4, "Exists", align="C")
        pdf.cell(16, 4, "Treated", align="C"); pdf.cell(0, 4, "Note"); pdf.ln()
        pdf.set_draw_color(180); pdf.line(M, pdf.get_y(), W - M, pdf.get_y()); pdf.ln(.6)
        for concern, exists, treated, note in rows:
            pdf.cell(70, 4, "  " + concern[:44]); pdf.cell(14, 4, exists, align="C")
            pdf.cell(16, 4, treated, align="C"); pdf.cell(0, 4, note[:40]); pdf.ln()
        pdf.ln(3)

    # ---- RUSLE2
    pdf.add_page(); head(pdf, "RUSLE2 SOIL LOSS SUMMARY", "Cropped fields")
    pdf.set_y(M + 26)
    pdf.set_font("Courier", "", 7.6)
    pdf.cell(0, 4, "  Rusle Program Version: 2.6.10.1   Database: Virginia 2024",
             new_x="LMARGIN", new_y="NEXT"); pdf.ln(3)
    pdf.set_font("Courier", "B", 7.2)
    for lbl, wd in (("Field",16),("Soil",14),("Management",54),("Loss",16),
                    ("T",10),("SCI",12),("<T?",10)):
        pdf.cell(wd, 4.6, lbl, align="R" if lbl in ("Loss","T","SCI") else "L")
    pdf.ln(); pdf.set_draw_color(150); pdf.line(M, pdf.get_y(), W - M, pdf.get_y()); pdf.ln(1)
    pdf.set_font("Courier", "", 7.2)
    for fld, soil, mgmt, loss, t, sci, under in RUSLE2:
        pdf.cell(16, 4.2, fld); pdf.cell(14, 4.2, soil); pdf.cell(54, 4.2, mgmt[:34])
        pdf.cell(16, 4.2, f"{loss:.1f}", align="R"); pdf.cell(10, 4.2, f"{t:.0f}", align="R")
        pdf.cell(12, 4.2, f"{sci:.2f}", align="R"); pdf.cell(10, 4.2, under); pdf.ln()
    pdf.ln(4)
    mono_block(pdf, [
      "  Loss is average annual sheet and rill soil loss in tons per acre.",
      "  T is the soil loss tolerance for the mapped soil.",
      "  SCI is the Soil Conditioning Index. A positive index indicates soil",
      "  organic matter is expected to increase under the management shown.",
      "",
      "  Fields 71 and 72 exceed T under the current management. The planned",
      "  conservation crop rotation and cover crop are expected to bring both",
      "  within tolerance. Recalculate after the first full rotation cycle."], 7.6)

    # ---- environmental review
    pdf.add_page(); head(pdf, "ENVIRONMENTAL EVALUATION", "NRCS-CPA-52 equivalent")
    pdf.set_y(M + 26)
    mono_block(pdf, [
      "This evaluation documents the review of the planned practices against",
      "applicable environmental requirements. It was completed by the",
      "planner on the basis of records review and site inspection.", ""], 8)
    for topic, finding, body in ENV_REVIEW:
        if pdf.get_y() > H - 56:
            pdf.add_page(); head(pdf, "ENVIRONMENTAL EVALUATION", "continued"); pdf.set_y(M + 26)
        pdf.set_font("Courier", "B", 7.8)
        pdf.cell(0, 4.6, topic.upper(), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Courier", "", 7.4)
        pdf.cell(0, 4.2, f"  Finding: {finding}", new_x="LMARGIN", new_y="NEXT")
        for l in body:
            pdf.cell(0, 4, "  " + l, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    pdf.output(out_path)
    return pdf.page_no()


def _wrap(text, width=66):
    words, out, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            out.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur: out.append(cur)
    return out


if __name__ == "__main__":
    n = build("data/sample_plans/virginia_plan_full.pdf")
    print("pages so far:", n)
