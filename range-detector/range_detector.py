"""Mechanical range detector (Python port of range_detector.pine).

Same rules as the TradingView indicator, bar-by-bar with no lookahead:
  1. Swing pivots are confirmed `pivot_len` bars after they form.
  2. A range opens when the last `touches` pivot highs sit within
     `tol_mult` x ATR of each other, the last `touches` pivot lows do too,
     the box height is within [min_h, max_h] x ATR, the Kaufman efficiency
     ratio is <= `er_max`, and no close has left the box since it began.
  3. A range ends on the first close beyond an edge by `brk_buf` x ATR.

Usage:
    python range_detector.py ohlc.csv [--out ranges.csv] [--plot chart.png]
CSV needs columns: time (or date/datetime), open, high, low, close.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd


@dataclass
class Params:
    pivot_len: int = 5
    touches: int = 2
    tol_mult: float = 0.5
    atr_len: int = 14
    min_h: float = 1.0
    max_h: float = 6.0
    er_len: int = 30
    er_max: float = 0.35
    brk_buf: float = 0.25
    dev_pct: float = 10.0


def atr_wilder(df: pd.DataFrame, n: int) -> np.ndarray:
    pc = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1).max(axis=1)
    tr.iloc[0] = df["high"].iloc[0] - df["low"].iloc[0]
    return tr.ewm(alpha=1 / n, adjust=False, min_periods=n).mean().to_numpy()


def efficiency_ratio(close: pd.Series, n: int) -> np.ndarray:
    net = (close - close.shift(n)).abs()
    path = close.diff().abs().rolling(n).sum()
    return (net / path.where(path > 0)).fillna(1.0).to_numpy()


def detect_ranges(df: pd.DataFrame, p: Params = Params()) -> pd.DataFrame:
    h, l, c = (df[k].to_numpy(float) for k in ("high", "low", "close"))
    n, L = len(df), p.pivot_len
    atr = atr_wilder(df, p.atr_len)
    er = efficiency_ratio(df["close"], p.er_len)

    hi_p: list[float] = []; hi_b: list[int] = []
    lo_p: list[float] = []; lo_b: list[int] = []
    out: list[dict] = []
    active: dict | None = None

    for i in range(n):
        # Manage an open range first (uses only data up to bar i).
        if active is not None:
            buf = p.brk_buf * atr[i]
            if c[i] > active["top"] + buf or c[i] < active["bottom"] - buf:
                active["end"] = i
                active["break"] = "up" if c[i] > active["top"] else "down"
                out.append(active)
                active = None
                continue

        # Confirm a pivot at bar i-L (needs L bars on each side).
        new_pivot = False
        j = i - L
        if j >= L:
            if h[j] == h[j - L : i + 1].max() and (h[j - L : j] < h[j]).all() and (h[j + 1 : i + 1] < h[j]).all():
                hi_p.append(h[j]); hi_b.append(j); new_pivot = True
                hi_p, hi_b = hi_p[-p.touches:], hi_b[-p.touches:]
            if l[j] == l[j - L : i + 1].min() and (l[j - L : j] > l[j]).all() and (l[j + 1 : i + 1] > l[j]).all():
                lo_p.append(l[j]); lo_b.append(j); new_pivot = True
                lo_p, lo_b = lo_p[-p.touches:], lo_b[-p.touches:]

        if active is None and new_pivot and len(hi_p) == p.touches and len(lo_p) == p.touches and not np.isnan(atr[i]):
            tol = p.tol_mult * atr[i]
            top, bot = max(hi_p), min(lo_p)
            height = top - bot
            start = min(hi_b + lo_b)
            seg = c[max(start, i - 499) : i + 1]
            clean = seg.max() <= top + p.brk_buf * atr[i] and seg.min() >= bot - p.brk_buf * atr[i]
            if (
                max(hi_p) - min(hi_p) <= tol
                and max(lo_p) - min(lo_p) <= tol
                and p.min_h * atr[i] <= height <= p.max_h * atr[i]
                and er[i] <= p.er_max
                and clean
            ):
                active = dict(start=start, confirmed=i, end=None, top=top, bottom=bot,
                              mid=(top + bot) / 2, dev_top=top + height * p.dev_pct / 100,
                              dev_bottom=bot - height * p.dev_pct / 100, **{"break": None})

    if active is not None:  # still open at the last bar
        active["end"] = n - 1
        out.append(active)

    res = pd.DataFrame(out)
    if res.empty:
        return res
    t = df["time"] if "time" in df else df.index.to_series()
    res["start_time"] = t.iloc[res["start"]].to_numpy()
    res["confirmed_time"] = t.iloc[res["confirmed"]].to_numpy()
    res["end_time"] = t.iloc[res["end"]].to_numpy()
    res["bars"] = res["end"] - res["start"] + 1
    return res


def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [x.strip().lower() for x in df.columns]
    for k in ("time", "date", "datetime", "timestamp"):
        if k in df:
            df = df.rename(columns={k: "time"})
            df["time"] = pd.to_datetime(df["time"], errors="coerce")
            break
    return df.reset_index(drop=True)


def plot(df: pd.DataFrame, ranges: pd.DataFrame, path: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(df.index, df["close"], lw=0.8, color="#333")
    for _, r in ranges.iterrows():
        col = {"up": "#1b9e77", "down": "#d95f02"}.get(r["break"], "#3366cc")
        ax.add_patch(Rectangle((r["start"], r["bottom"]), r["end"] - r["start"], r["top"] - r["bottom"],
                               fc=col, alpha=0.18, ec=col))
        ax.hlines(r["mid"], r["start"], r["end"], colors=col, linestyles="--", lw=0.8)
    ax.set_title(f"Mechanical ranges ({len(ranges)})")
    fig.tight_layout(); fig.savefig(path, dpi=120)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv")
    ap.add_argument("--out")
    ap.add_argument("--plot")
    for k, v in asdict(Params()).items():
        ap.add_argument(f"--{k.replace('_', '-')}", type=type(v), default=v)
    a = ap.parse_args()
    p = Params(**{k: getattr(a, k) for k in asdict(Params())})
    df = load_csv(a.csv)
    rg = detect_ranges(df, p)
    print(rg.drop(columns=["start", "confirmed", "end"], errors="ignore").to_string() if len(rg) else "No ranges found.")
    if a.out and len(rg):
        rg.to_csv(a.out, index=False)
    if a.plot:
        plot(df, rg, a.plot)


if __name__ == "__main__":
    main()
