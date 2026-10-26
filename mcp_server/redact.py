"""Strip a producer's personal information before any model sees the document.

A conservation plan identifies a real person: their name, the address of
their farm, a phone number, the tract and farm numbers the agency files them
under. **None of that is needed to decide which practices can be credited.**
The agents need practice names, quantities, widths, land use and the county.

So the pipeline is ordered deliberately:

    1. read the location LOCALLY (deterministic, no model) -- this needs the
       address, and it never leaves the machine
    2. REDACT -- names, street address, phone, email, farm and tract IDs
    3. only then send the text to the model

The model receives a document about "a farm in Rockingham County" with the
practices intact and the person removed. What was removed is reported to the
user, so the redaction is auditable rather than a claim.
"""

from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------- patterns

_STREET = (r"(?:Rd|Road|St|Street|Ln|Lane|Dr|Drive|Hwy|Highway|Pike|Ave|Avenue|"
           r"Way|Ct|Court|Blvd|Boulevard|Cir|Circle|Trl|Trail|Pkwy|Route|Rt)")

# Labels a plan uses before a person's or business's name.
_PERSON_LABEL = (r"(?:Producer|Landowner|Land\s?owner|Operator|Owner|Farmer|"
                 r"Cooperator|Client|Applicant|Contact|Participant|Grantee|"
                 r"Prepared\s+for|Assisted\s+By|Planner|Technician)")

# (key, human label, regex, flags, keep_group)
# keep_group 1 means group 1 is a label to preserve; only the rest is masked.
RULES: list[tuple[str, str, str, int, int]] = [
    ("email", "email address",
     r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", 0, 0),
    ("phone", "phone number",
     r"(?:\(\d{3}\)\s*|\b\d{3}[.\-\s])\d{3}[.\-\s]?\d{4}\b", 0, 0),
    ("ssn", "government identifier",
     r"\b\d{3}-\d{2}-\d{4}\b", 0, 0),
    ("street_address", "street address",
     rf"\b\d{{1,6}}[ \t]+[A-Z][\w.'-]*(?:[ \t]+[A-Z][\w.'-]*){{0,4}}[ \t]+{_STREET}\.?\b", 0, 0),
    ("po_box", "PO box", r"\bP\.?\s?O\.?\s+Box\s+\d+\b", re.I, 0),
    ("name_labelled", "name",
     rf"({_PERSON_LABEL}\s*:)[^\n,]{{2,60}}", re.I, 1),
    ("business_name", "business name",
     r"\b[A-Z][\w'&.-]*(?:[ \t]+[A-Z][\w'&.-]*){0,4}[,]?[ \t]+"
     r"(?:LLC|L\.L\.C\.|Inc\.?|Incorporated|LP|L\.P\.|LLP)\b", 0, 0),
    ("farm_tract_id", "farm or tract identifier",
     r"\b(?:FARM|TRACT|ACC\s*ID|CLU|FSA)\s*[:#]?\s*\d{2,}\b", re.I, 0),
    ("contract_number", "contract number",
     r"\b\d{2}-\d[A-Z]\d{2,}-\d{2}-\d{3,}\b", 0, 0),
    ("zip", "postal code", r"\b\d{5}(?:-\d{4})?\b", 0, 0),
    ("coords", "coordinates",
     r"\b-?\d{1,3}\.\d{4,}\s*,\s*-?\d{1,3}\.\d{4,}\b", 0, 0),
]

# Words that must never be redacted even if a pattern grazes them: these are
# practice and place vocabulary the screening depends on.
_PROTECT = re.compile(
    r"\b(?:Buffer|Cover\s+Crop|Tillage|Nutrient\s+Management|Grazing|Pasture|"
    r"Wetland|Barnyard|Manure|Irrigation|Drainage|Forest|Grass|Retirement|"
    r"Conservation|Riparian|Streambank|County|Watershed|Acres?|Feet|Field)\b",
    re.I)


def redact(text: str, *, keep_county: str | None = None) -> dict[str, Any]:
    """Remove personal information. Returns the clean text and a receipt."""
    found: list[dict[str, Any]] = []
    out = text

    for key, label, pattern, flags, keep_group in RULES:
        rx = re.compile(pattern, flags)

        def _sub(m, _k=key, _l=label, _g=keep_group):
            hit = m.group(0)
            prefix = m.group(_g) if _g else ""
            payload = hit[len(prefix):] if prefix else hit
            if not payload.strip():
                return hit
            # never redact the county being screened, or practice vocabulary
            if keep_county and keep_county.lower() in payload.lower():
                return hit
            if _PROTECT.search(payload):
                return hit
            found.append({
                "type": _k, "label": _l,
                "preview": payload.strip()[:3] + "\u2026",
                "length": len(payload.strip()),
            })
            return prefix + " [" + _l.upper().replace(" ", "_") + "_REDACTED]"

        out = rx.sub(_sub, out)

    by_type: dict[str, int] = {}
    for f in found:
        by_type[f["label"]] = by_type.get(f["label"], 0) + 1

    return {
        "text": out,
        "redacted_count": len(found),
        "by_type": by_type,
        "items": found[:40],
        "clean": len(found) == 0,
        "note": (
            "Personal information was removed before the document reached the "
            "model. The county is kept because the screening needs it; the "
            "person, the street address and the agency file numbers are not "
            "needed to decide which practices can be credited."
            if found else
            "No personal information was detected in this document."
        ),
    }


def verify_absent(text: str, originals: list[str]) -> dict[str, Any]:
    """Confirm specific strings really are gone from the redacted text."""
    leaked = [o for o in originals if o and o.lower() in text.lower()]
    return {"clean": not leaked, "leaked": leaked}
