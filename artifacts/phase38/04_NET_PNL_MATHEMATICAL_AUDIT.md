# Phase 38 Artifact 04: Net P&L Mathematical Audit

## Mathematical Formulas

### Gross P&L
$$\text{Gross Move} = \begin{cases} \text{Exit Price} - \text{Entry Price}, & \text{for BUY / LONG} \\ \text{Entry Price} - \text{Exit Price}, & \text{for SELL / SHORT} \end{cases}$$

$$\text{Gross P\&L} = \text{Gross Move} \times \text{Lot Size} \times \text{Pip Value}$$

### Cost Deductions
$$\text{Spread Cost} = \text{Spread (pips)} \times \text{Lot Size} \times \text{Pip Value}$$
$$\text{Slippage Cost} = \text{Slippage (pips)} \times \text{Lot Size} \times \text{Pip Value}$$
$$\text{Broker Fees} = \text{Fee per Lot} \times \text{Lot Size}$$

### Net P&L
$$\text{Net P\&L} = \text{Gross P\&L} - \text{Spread Cost} - \text{Slippage Cost} - \text{Broker Fees}$$

### R-Multiple
$$\text{Risk Amount} = |\text{Entry Price} - \text{Stop Loss}| \times \text{Lot Size} \times \text{Pip Value}$$
$$\text{R-Multiple} = \frac{\text{Net P\&L}}{\text{Risk Amount}}$$

## Test Evidence
Validated by `tests/test_phase38_pnl_math.py` and `scripts/phase38_pnl_validator.py` with 100% mathematical precision.
