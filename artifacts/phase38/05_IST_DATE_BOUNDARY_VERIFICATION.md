# Phase 38 Artifact 05: Indian Standard Time (IST) Boundary Verification

## Timezone Architecture

| Domain | Standard | Timezone Offset | Reason |
| :--- | :--- | :--- | :--- |
| Database Storage | UTC | `+00:00` | Standardized database querying & cross-server portability |
| User Grouping | IST | `+05:30` | Explicit user operational day boundary (Asia/Kolkata) |

## Daily Bound Arithmetic
- **Today (IST)**:
  $$\text{Target Day IST} = \text{now}_{\text{IST}}.\text{replace}(00:00:00.000000)$$
  $$\text{Start UTC} = \text{Target Day IST} - 05:30 = \text{Yesterday 18:30:00 UTC}$$
  $$\text{End UTC} = \text{Start UTC} + 24\text{ hours} = \text{Today 18:30:00 UTC}$$

- **Yesterday (IST)**:
  $$\text{Start UTC} = \text{Yesterday 00:00:00 IST} = \text{2 days ago 18:30:00 UTC}$$
  $$\text{End UTC} = \text{Today 00:00:00 IST} = \text{Yesterday 18:30:00 UTC}$$

Validated with 100% precision in `tests/test_phase38_date_boundaries.py`.
