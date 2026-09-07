# Chronological Walk-Forward Cross-Validation Report
**Asset**: EURUSD | **Total Folds**: 3 | **Total OOS Signals**: 18
**Overall OOS Win Rate**: 22.2% | **Total Net Realized R**: -6.9R | **Expectancy**: -0.383R

## 1. Walk-Forward Folds Breakdown

| Fold | Training Window | Out-of-Sample Test Window | Signals | Wins | Losses | Win Rate | Net R | Expectancy |
|---|---|---|---|---|---|---|---|---|
| Fold 1 | 2016-08-01 to 2016-10-21 | 2016-12-05 to 2017-01-13 | 9 | 0 | 9 | 0.0% | -9.45R | -1.050R |
| Fold 2 | 2016-09-26 to 2016-12-16 | 2017-01-30 to 2017-03-10 | 4 | 0 | 4 | 0.0% | -4.20R | -1.050R |
| Fold 3 | 2016-11-21 to 2017-02-10 | 2017-03-27 to 2017-05-05 | 5 | 4 | 1 | 80.0% | +6.75R | +1.350R |

## 2. Zero-Leakage Guarantee
Folds are strictly chronological. Out-of-sample test folds are evaluated blindly on closed candles with zero lookahead.