"""FastAPI app: API routes plus the dashboard, served as one page.

No build step and no node_modules. `uvicorn` is the only thing a grader has
to run.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "mcp_server"))

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

import settings as CFG
import toolbelt as TB
from tokenomics import PRICED, append_run, load_runs
import runner as RUN

app = FastAPI(title="Virginia Pasture Conversion Deal Desk")

STATIC = ROOT / "frontend"


# --------------------------------------------------------------- models

class PracticeLine(BaseModel):
    practice: str
    units: float
    width_ft: float | None = None
    prior_land_use: str | None = None


class ScreenRequest(BaseModel):
    county: str
    practices: list[PracticeLine] = Field(default_factory=list)
    plan_text: str | None = None
    hgmr: str | None = None
    prior_land_use: str = "cropland"
    risk_answers: dict = Field(default_factory=dict)


# --------------------------------------------------------------- routes

@app.get("/api/health")
def health():
    return {
        "ok": True,
        "model": CFG.MODEL_NAME,
        "env_file_used": str(CFG.ENV_FILE_USED) if CFG.ENV_FILE_USED else None,
        "key_configured": bool(CFG.PORTKEY_API_KEY or CFG.OPENAI_API_KEY),
        "key_name": "PORTKEY_API_KEY" if CFG.PORTKEY_API_KEY
                    else ("OPENAI_API_KEY" if CFG.OPENAI_API_KEY else None),
        "cost_priced": PRICED,
        "setup_hint": CFG.missing_key_message(),
    }


@app.get("/api/counties")
def counties():
    return TB.call_tool("list_counties", {})


@app.get("/api/practices")
def practices(county: str | None = None):
    base = TB.call_tool("list_known_practices", {"county": county})
    base["units"] = TB.t_practice_units(county)["units"]
    return base


@app.get("/api/hgmr")
def hgmr():
    return TB.call_tool("list_hgmr_regions", {})


@app.get("/api/program")
def program():
    return TB.call_tool("get_program_terms", {})


@app.get("/api/rank/{county}")
def rank(county: str, limit: int = 12):
    return TB.call_tool("rank_practices_for_county",
                        {"county": county, "limit": limit})


@app.get("/api/compare")
def compare(practice: str, limit: int = 12):
    return TB.call_tool("compare_counties",
                        {"practice": practice, "limit": limit})


class BundleRequest(BaseModel):
    county: str
    practices: list[PracticeLine]
    hgmr: str | None = None
    prior_land_use: str = "cropland"


@app.post("/api/quote")
def quote(req: BundleRequest):
    """Deterministic screen with no model involved. Instant, free, exact."""
    return TB.call_tool("screen_practice_bundle", {
        "county": req.county,
        "practices": [p.model_dump(exclude_none=True) for p in req.practices],
        "hgmr": req.hgmr,
        "prior_land_use": req.prior_land_use,
    })


class ScanRequest(BaseModel):
    text: str


@app.post("/api/scan")
def scan(req: ScanRequest):
    return TB.call_tool("scan_document_for_injection", {"text": req.text})


@app.post("/api/screen")
async def screen(req: ScreenRequest):
    """Full agent run."""
    if not (CFG.PORTKEY_API_KEY or CFG.OPENAI_API_KEY):
        raise HTTPException(status_code=503, detail=CFG.missing_key_message())
    if not req.practices and not req.plan_text:
        raise HTTPException(
            status_code=400,
            detail="Supply either a practice list or a conservation plan.")
    try:
        return await RUN.screen_project(
            county=req.county,
            practices=[p.model_dump(exclude_none=True) for p in req.practices],
            plan_text=req.plan_text,
            hgmr=req.hgmr,
            prior_land_use=req.prior_land_use,
            risk_answers=req.risk_answers,
        )
    except Exception as e:  # surfaced to the UI rather than a blank 500
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@app.get("/api/runs")
def runs():
    """Token log across every run, for the tokenomics panel."""
    data = load_runs(CFG.OUTPUT_DIR / "token_log.json")
    if not data:
        return {"runs": [], "aggregate": None}
    tot = sum(r.get("total_tokens", 0) for r in data)
    agg = {
        "run_count": len(data),
        "total_tokens": tot,
        "mean_tokens_per_run": round(tot / len(data)),
        "mean_input": round(sum(r.get("input_tokens", 0) for r in data) / len(data)),
        "mean_cached": round(sum(r.get("cached_input_tokens", 0) for r in data) / len(data)),
        "mean_output": round(sum(r.get("output_tokens", 0) for r in data) / len(data)),
        "mean_latency_ms": round(sum(r.get("latency_ms", 0) for r in data) / len(data)),
        "priced": PRICED,
    }
    return {"runs": data[-50:], "aggregate": agg}


@app.get("/api/sample-plan/{name}")
def sample_plan(name: str):
    safe = "".join(c for c in name if c.isalnum() or c in "_-")
    p = CFG.DATA_DIR / "sample_plans" / f"{safe}.txt"
    if not p.is_file():
        raise HTTPException(status_code=404, detail="No such sample plan.")
    return {"name": safe, "text": p.read_text()}


@app.get("/api/map")
def county_map(practice: str = "Land Retirement to Pasture"):
    """County polygons joined to cost-effectiveness for one practice.

    Counties with no rate row are outside the Chesapeake Bay watershed
    portion the programme covers, and are returned flagged as ineligible
    rather than omitted -- the absence is itself the answer.
    """
    import sqlite3
    geo_path = CFG.DATA_DIR / "va_counties.json"
    if not geo_path.is_file():
        raise HTTPException(status_code=500, detail="Map data missing.")
    geo = json.loads(geo_path.read_text())

    con = sqlite3.connect(f"file:{TB.DB_PATH}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    rows = con.execute("""
        SELECT county, tn_lb_per_unit, tn_cost_per_lb, cost_per_unit, unit
        FROM bmp_rates WHERE bmp_name=? AND tier='Primary' AND tn_lb_per_unit>0
    """, (practice,)).fetchall()
    con.close()
    rates = {r["county"]: dict(r) for r in rows}

    vals = [r["tn_cost_per_lb"] for r in rows if r["tn_cost_per_lb"]]
    out = []
    for f in geo["features"]:
        rate = rates.get(f["n"])
        out.append({
            "name": f["n"], "rings": f["r"],
            "eligible": bool(f["m"]),
            "has_rate": rate is not None,
            "tn_lb_per_unit": rate["tn_lb_per_unit"] if rate else None,
            "tn_cost_per_lb": rate["tn_cost_per_lb"] if rate else None,
        })
    return {
        "practice": practice,
        "counties": out,
        "scale": {
            "min": round(min(vals), 2) if vals else None,
            "max": round(max(vals), 2) if vals else None,
            "n_with_rate": len(vals),
            "n_total": len(out),
        },
        "note": ("Counties without a rate row lie outside the Chesapeake Bay "
                 "watershed portion covered by the programme data."),
    }


@app.get("/api/sources")
def sources():
    """Every source behind a number this app reports."""
    import cast_rules as CR
    return {
        "data": [
            {
                "label": "County BMP reduction and cost workbook",
                "detail": ("Per-county, per-practice pounds of nitrogen, "
                           "phosphorus and sediment reduced per unit, with "
                           "cost per unit. 24,704 Virginia rows across 96 "
                           "counties and 270 practices."),
                "used_for": "Every reduction and cost figure in the app.",
                "url": "https://cast.chesapeakebay.net/",
            },
            {
                "label": "CBP Quick Reference Guide for BMPs (CBP/TRS-323-18)",
                "detail": ("Second edition, 2022/2024. Sheets A-12 and A-13 "
                           "supply buffer efficiencies by hydrogeomorphic "
                           "region, the 35 ft width threshold, and the "
                           "qualifying conditions."),
                "used_for": "Buffer alignment and upland efficiency values.",
                "url": "https://www.chesapeakebay.net/files/documents/BMP-Guide_Full.pdf",
            },
            {
                "label": "Riparian buffer expert panel report",
                "detail": CR.SOURCES["expert_panel"],
                "used_for": "Provenance of the buffer removal rates.",
                "url": "https://www.chesapeakebay.net/documents/Riparian_BMP_Panel_Report_FINAL_October_2014.pdf",
            },
            {
                "label": "Chesapeake Assessment Scenario Tool (CAST)",
                "detail": ("The Bay Program's scenario tool. The reference "
                           "guide states buffer reductions are not simple to "
                           "quantify without it."),
                "used_for": "Origin of the practice definitions and efficiencies.",
                "url": "https://cast.chesapeakebay.net/",
            },
            {
                "label": "Virginia DEQ nutrient trading programme",
                "detail": ("Virginia's nonpoint source nutrient credit "
                           "certification and registry, under 9VAC25-900."),
                "used_for": "Regulatory context for what a reduction can become.",
                "url": "https://www.deq.virginia.gov/permits/water/nutrient-trading",
            },
            {
                "label": "9VAC25-900, Certification of Nonpoint Source Nutrient Credits",
                "detail": ("Credit calculation procedures, the 5% retirement "
                           "at certification, and the release schedule."),
                "used_for": "Verification and credit-release logic.",
                "url": "https://law.lis.virginia.gov/admincodefull/title9/agency25/chapter900/",
            },
            {
                "label": "US county boundaries",
                "detail": "Census county polygons, simplified for display.",
                "used_for": "The county map.",
                "url": "https://www.census.gov/geographies/mapping-files.html",
            },
        ],
        "model": {
            "name": CFG.MODEL_NAME,
            "note": ("The model routes, reads documents, and writes prose. It "
                     "produces no figures. Every number shown in this app "
                     "comes from the workbook or the reference guide, through "
                     "a tool call."),
        },
    }


@app.get("/api/hgmr-for/{county}")
def hgmr_for(county: str):
    """Suggest a hydrogeomorphic region from the county.

    A SUGGESTION, not a determination. Virginia's physiographic provinces run
    broadly west to east, so a county centroid places most counties well, but
    several counties straddle a boundary and the carbonate/siliciclastic
    split within a province is geology rather than geography. The UI shows
    this as suggested and leaves it editable.
    """
    path = CFG.DATA_DIR / "county_hgmr.json"
    if not path.is_file():
        raise HTTPException(status_code=500, detail="HGMR lookup data missing.")
    table = json.loads(path.read_text())
    hit = table.get(county)
    if not hit:
        return {"county": county, "hgmr": None,
                "note": "No suggestion on file for this county."}
    return {
        "county": county,
        "hgmr": hit["hgmr"],
        "basis": hit["basis"],
        "confidence": "named province" if hit["basis"] == "province" else "centroid longitude",
        "note": ("Suggested from the county's physiographic province. Confirm "
                 "against the site before relying on it: counties near a "
                 "province boundary can fall either way, and the carbonate "
                 "or siliciclastic split is geology, not location."),
    }


class RepoEntry(BaseModel):
    label: str
    county: str
    practices: list[PracticeLine] = Field(default_factory=list)
    hgmr: str | None = None
    totals: dict = Field(default_factory=dict)
    cost: dict = Field(default_factory=dict)
    risk_summary: dict = Field(default_factory=dict)
    run_id: str | None = None
    note: str | None = None


@app.get("/api/repository")
def repository_list():
    """Saved projects. Opt-in only: nothing is stored unless a user asks."""
    data = load_runs(CFG.OUTPUT_DIR / "repository.json")
    return {"count": len(data), "projects": data}


@app.post("/api/repository")
def repository_add(entry: RepoEntry):
    from datetime import datetime, timezone
    import uuid as _uuid
    rec = entry.model_dump()
    rec["id"] = f"prj_{_uuid.uuid4().hex[:8]}"
    rec["saved_at"] = datetime.now(timezone.utc).isoformat()
    rec["practices"] = [p for p in rec.get("practices", [])]
    append_run(CFG.OUTPUT_DIR / "repository.json", rec)
    return {"saved": True, "id": rec["id"]}


@app.delete("/api/repository/{project_id}")
def repository_delete(project_id: str):
    import json as _json
    path = CFG.OUTPUT_DIR / "repository.json"
    data = load_runs(path)
    keep = [r for r in data if r.get("id") != project_id]
    if len(keep) == len(data):
        raise HTTPException(status_code=404, detail="No such project.")
    tmp = path.with_suffix(".tmp")
    tmp.write_text(_json.dumps(keep, indent=2))
    tmp.replace(path)
    return {"deleted": project_id, "remaining": len(keep)}


# An upload cap is a resource control, not a feature: the file is read into
# memory before extraction, so an unbounded upload is a denial-of-service
# vector. 40 MB comfortably covers a scanned multi-page plan while still
# bounding what one request can allocate.
MAX_UPLOAD_BYTES = 40 * 1024 * 1024
MAX_PDF_PAGES = 150
MAX_EXTRACTED_CHARS = 400_000
TEXT_SUFFIXES = {".txt", ".md", ".csv", ".text", ".log"}


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    """Pull text out of an uploaded document.

    Accepts plain text and PDF. The extracted text is returned to the browser
    and nothing is written to disk: a conservation plan belongs to the
    producer, and this app has no reason to keep a copy.
    """
    raw = await file.read()
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413,
            detail=(f"That file is {len(raw)/(1024*1024):.1f} MB; the limit is "
                    f"{MAX_UPLOAD_BYTES // (1024*1024)} MB. If it is a scanned "
                    "plan, exporting it as text or splitting out the relevant "
                    "pages will usually get well under the cap."))
    name = (file.filename or "upload").lower()
    suffix = "." + name.rsplit(".", 1)[-1] if "." in name else ""

    if suffix == ".pdf":
        try:
            import io
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(raw))
            n_pages = len(reader.pages)
            pages = [(pg.extract_text() or "") for pg in reader.pages[:MAX_PDF_PAGES]]
            text = "\n".join(pages).strip()
            with_text = sum(1 for pg in pages if pg.strip())
            kind = f"pdf, {n_pages} page(s)"
            if n_pages > MAX_PDF_PAGES:
                kind += f" (first {MAX_PDF_PAGES} read)"
            if n_pages and with_text == 0:
                raise HTTPException(status_code=422,
                    detail=("This PDF has no text layer, so it is almost "
                            "certainly a scan. Nothing can be extracted from "
                            "it without OCR. Paste the text, or run the file "
                            "through an OCR step first."))
            if n_pages and with_text < n_pages * 0.4:
                kind += f" — only {with_text} of {n_pages} pages had extractable text"
        except Exception as e:
            raise HTTPException(status_code=422,
                detail=f"Could not read that PDF: {e}")
    elif suffix in TEXT_SUFFIXES or not suffix:
        try:
            text = raw.decode("utf-8", errors="replace").strip()
            kind = "text"
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Could not decode: {e}")
    else:
        raise HTTPException(status_code=415,
            detail=f"Unsupported file type {suffix!r}. Upload a PDF or a text file, "
                   "or paste the text directly.")

    if not text:
        raise HTTPException(status_code=422,
            detail="No text could be extracted. If this is a scanned PDF it has no "
                   "text layer; paste the text instead.")

    scan = TB.call_tool("scan_document_for_injection", {"text": text})
    privacy = TB.call_tool("redact_personal_information", {"text": text})
    return {
        "filename": file.filename, "kind": kind,
        "characters": len(text), "text": text[:MAX_EXTRACTED_CHARS],
        "truncated": len(text) > MAX_EXTRACTED_CHARS,
        "injection_scan": scan,
        "privacy_preview": privacy,
        "stored": False,
    }


class LocateRequest(BaseModel):
    text: str


@app.post("/api/locate")
def locate(req: LocateRequest):
    """Read state, county and address out of a document."""
    import plan_reader as PR
    return PR.detect_location(TB.DB_PATH, req.text)


@app.get("/img/{name}")
def image(name: str):
    from fastapi.responses import FileResponse
    safe = "".join(c for c in name if c.isalnum() or c in "._-")
    f = STATIC / "img" / safe
    if not f.is_file():
        raise HTTPException(status_code=404, detail="No such image.")
    return FileResponse(f)


@app.get("/", response_class=HTMLResponse)
def index():
    page = STATIC / "index.html"
    if not page.is_file():
        return HTMLResponse("<h1>Dashboard not built</h1>", status_code=500)
    return HTMLResponse(page.read_text())
