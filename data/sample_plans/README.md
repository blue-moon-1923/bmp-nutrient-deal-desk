# Sample plans

Test documents for the screening workflow. None describes a real farm.

| File | What it exercises |
|---|---|
| `virginia_plan.txt` | A full NRCS-format plan with 10 practices. Written to exercise every rule at once: practices that cost cleanly, an annual practice whose cost-share year is ambiguous, a reduction already reported to the state, an existing structural buffer, and a line item that is a real cost but not a creditable practice. |
| `clean_plan.txt` | Short plan, no issues. Fast path for checking the app runs. |
| `poisoned_plan.txt` | Contains a prompt injection addressed to the agent. Used to demonstrate that an instruction found in an uploaded document is reported rather than obeyed. |

## What `virginia_plan.txt` should produce

Format follows a real NRCS conservation plan (header block, tract, practice
name with its NRCS code, narrative, planned/applied table, totals).

| Plan line | Expected outcome |
|---|---|
| Cover Crop - 340 | costed |
| Riparian Forest Buffer - 391 (75 ft, new) | costed, full width |
| Prescribed Grazing - 528 | costed |
| Watering Facility - 614 | costed |
| Heavy Use Area Protection - 561 | costed |
| Conservation Crop Rotation - 328 | costed |
| No Till - 329 (EQIP expired 2024) | **ask** — is the credit year funded? |
| Nutrient Management - 590 (reported to DEQ) | **not creditable** — double counting |
| Riparian Forest Buffer - 391 (existing, CREP) | **not creditable** — not additional |
| Fence - 382 | **unresolved** — a cost, not a creditable practice |

The no-till line is the interesting one. The plan names an EQIP contract that
**expired in 2024**, which says nothing about whether the credit year is
funded. The correct answer is a question, not a yes or a no.
