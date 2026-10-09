# Mechanical Range Detector

Rule-based range boxes, as a TradingView indicator (`range_detector.pine`) and a
Python port for backtesting (`range_detector.py`). Both use identical logic.

## Rules
1. **Pivots**: swing highs/lows confirmed `pivot_len` bars after they form (no repaint once drawn).
2. **Open a range** on a new pivot when all of these hold:
   - the last `touches` pivot highs are within `tol_mult` x ATR of each other, and likewise the lows;
   - box height is between `min_h` and `max_h` x ATR;
   - Kaufman efficiency ratio over `er_len` bars is <= `er_max` (low = choppy, not trending);
   - no close has left the box (plus buffer) since its first pivot.
3. **Box**: top = highest pivot high, bottom = lowest pivot low, plus midpoint and deviation zones (`dev_pct` of height).
4. **Close the range** on the first close beyond an edge by `brk_buf` x ATR, labelled break up/down.

## TradingView
Pine Editor -> paste `range_detector.pine` -> Add to chart. Alerts: range formed / break up / break down.

## Python
```
python range_detector.py ohlc.csv --out ranges.csv [--plot chart.png]   # plot needs matplotlib
python range_detector.py ohlc.csv --max-h 8 --tol-mult 0.75              # any Params field is a flag
```
CSV columns: `time` (or date/datetime), `open`, `high`, `low`, `close`.

## Tuning notes
- Ranges are detected with lag (pivot confirmation + ER filter), so they are known late by design.
- `max_h` and `tol_mult` are the most sensitive: raise them on wide-swinging instruments/timeframes.
- Pine was written without access to TradingView here; Python was tested on synthetic data
  (found both planted ranges). Check the Pine on a chart and tell me about any compile errors.
