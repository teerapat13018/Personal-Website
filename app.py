# =============================================================================
# Investment Dashboard - app.py  (v3 — Advanced Analytics Pack)
# =============================================================================
# Section 1 : Imports & Page Config
# Section 2 : Google Sheets Database  (diary / alerts / watchlist / portfolio)
# Section 3 : Support/Resistance Analysis (Local Extrema)
# Section 4 : Plotly Chart Builder
# Section 5 : Advanced Analytics Helpers  ← NEW v3
#               5A: Portfolio History & Benchmark
#               5B: ETF Look-through & True Exposure
#               5C: Correlation Matrix
#               5D: Drawdown Analysis
# Section 6 : Main App  (Sidebar + 5 Tabs)
#              Tab 1 — Chart & Analysis
#              Tab 2 — Portfolio
#              Tab 3 — Investment Diary
#              Tab 4 — Watchlist
#              Tab 5 — 🚀 Advanced Analytics  ← NEW v3
#                  Sub-tab A: 📈 Benchmark
#                  Sub-tab B: 🔍 Risk & Correlation
#                  Sub-tab C: ⚖️ Rebalancing
#                  Sub-tab D: 📉 Drawdown
# =============================================================================
# วิธีรัน:
#   pip install streamlit yfinance pandas plotly numpy
#   streamlit run app.py
# =============================================================================


# ─── Section 1: Imports & Config ────────────────────────────────────────────

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime
from pathlib import Path

st.set_page_config(
    page_title="📈 Investment Dashboard",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    /* ── Typography ─────────────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* ── Hide sidebar ───────────────────────────────────────────────────── */
    button[data-testid="collapsedControl"] { display: none !important; }
    section[data-testid="stSidebar"]       { display: none !important; }

    /* ── Tabs ───────────────────────────────────────────────────────────── */
    div[data-testid="stTabs"] button {
        font-size: 14px;
        font-weight: 500;
        padding: 8px 14px;
    }

    /* ── Metric cards ───────────────────────────────────────────────────── */
    div[data-testid="metric-container"] {
        background: linear-gradient(145deg, #1e1e2e 0%, #16162a 100%);
        border: 1px solid rgba(124, 58, 237, 0.2);
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.4),
                    0 0 0 1px rgba(255,255,255,0.03);
    }
    div[data-testid="metric-container"] label {
        font-size: 12px !important;
        font-weight: 600 !important;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: #8b8ba7 !important;
    }
    div[data-testid="metric-container"] [data-testid="stMetricValue"] {
        font-size: 26px !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }

    /* ── Primary button ─────────────────────────────────────────────────── */
    div.stButton button[kind="primary"],
    div.stButton > button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #6d28d9 0%, #4c1d95 100%);
        border: none;
        border-radius: 10px;
        font-weight: 600;
        letter-spacing: 0.02em;
        box-shadow: 0 4px 14px rgba(109, 40, 217, 0.35);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    div.stButton button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(109, 40, 217, 0.5);
    }

    /* ── Semantic text colours ──────────────────────────────────────────── */
    .positive { color: #34d399; font-weight: 700; }
    .negative { color: #f87171; font-weight: 700; }

    /* ── Action item cards ──────────────────────────────────────────────── */
    .action-card {
        border-radius: 10px;
        padding: 10px 14px;
        margin-bottom: 8px;
        font-size: 13px;
        line-height: 1.5;
    }
    .action-buy  { background:#0d2b1d; border-left:4px solid #34d399; }
    .action-warn { background:#2d2200; border-left:4px solid #fbbf24; }
    .action-risk { background:#2d1b1b; border-left:4px solid #f87171; }
    .action-info { background:#1a1a2e; border-left:4px solid #818cf8; }

    /* ── Legacy cards (preserved) ───────────────────────────────────────── */
    .news-card {
        background: #1a1a2e;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
        border-left: 3px solid #7c3aed;
    }
    .alert-triggered {
        background: #2d1b1b;
        border-left: 4px solid #f87171;
        border-radius: 6px;
        padding: 8px 12px;
        margin: 4px 0;
    }
    .rebal-alert {
        background: #2d1f00;
        border-left: 4px solid #fbbf24;
        border-radius: 6px;
        padding: 8px 12px;
        margin: 3px 0;
        font-size: 13px;
    }
    .rebal-ok {
        background: #0d2b1d;
        border-left: 4px solid #34d399;
        border-radius: 6px;
        padding: 8px 12px;
        margin: 3px 0;
        font-size: 13px;
    }

    /* ── Mobile responsive ──────────────────────────────────────────────── */
    @media (max-width: 640px) {
        div[data-testid="metric-container"] {
            padding: 12px 14px;
            border-radius: 10px;
        }
        div[data-testid="metric-container"] [data-testid="stMetricValue"] {
            font-size: 20px !important;
        }
        div[data-testid="stTabs"] button {
            font-size: 12px;
            padding: 6px 8px;
        }
        .action-card { font-size: 12px; }
        h1 { font-size: 1.4rem !important; }
        h2 { font-size: 1.15rem !important; }
    }
</style>
""", unsafe_allow_html=True)


# ─── Section 2: Google Sheets Database ──────────────────────────────────────
# ใช้ Google Sheets แทน SQLite เพื่อให้ข้อมูลคงอยู่บน Streamlit Cloud
# ต้องตั้งค่า secrets.toml ก่อน (ดู DEPLOY_CHECKLIST.md)

from db_gsheets import (
    init_db,
    db_save, db_load, db_delete_diary,
    portfolio_load, portfolio_save,
    wl_add, wl_load, wl_delete,
    pt_add, pt_load, pt_clear,
    etf_holdings_load, etf_holdings_save,
    rebalancing_load, rebalancing_save,
)


# ─── Section 3: Support & Resistance (Local Extrema) ────────────────────────

def find_support_resistance(df: pd.DataFrame, order: int = 10):
    highs = df["High"].values
    lows  = df["Low"].values
    n     = len(highs)
    resistance_idx, support_idx = [], []

    for i in range(order, n - order):
        hw = highs[i - order: i + order + 1]
        lw = lows[i - order: i + order + 1]
        if highs[i] >= np.max(hw) * 0.9995:
            resistance_idx.append(i)
        if lows[i] <= np.min(lw) * 1.0005:
            support_idx.append(i)

    def cluster_sup(levels, threshold=0.05):
        """Support: ถ้า 2 level ห่างกัน < 5% → เอาตัวบน (ใกล้ราคามากกว่า)"""
        if not levels:
            return []
        levels = sorted(set(round(l, 2) for l in levels), reverse=True)  # เรียงสูง→ต่ำ
        out = [levels[0]]
        for lv in levels[1:]:
            if abs(out[-1] - lv) / lv > threshold:
                out.append(lv)
        return list(reversed(out))  # คืนกลับเป็นต่ำ→สูง

    def cluster_res(levels, threshold=0.05):
        """Resistance: ถ้า 2 level ห่างกัน < 5% → เอาตัวล่าง (ใกล้ราคามากกว่า)"""
        if not levels:
            return []
        levels = sorted(set(round(l, 2) for l in levels))  # เรียงต่ำ→สูง
        out = [levels[0]]
        for lv in levels[1:]:
            if abs(lv - out[-1]) / out[-1] > threshold:
                out.append(lv)
        return out

    current = df["Close"].iloc[-1]
    supports    = [s for s in cluster_sup([lows[i]  for i in support_idx])    if s < current]
    resistances = [r for r in cluster_res([highs[i] for i in resistance_idx]) if r > current]
    return supports[-6:], resistances[:6]


# ─── Section 4: Chart Builder ────────────────────────────────────────────────

BULL = "#26a69a"
BEAR = "#ef5350"


def build_candlestick(df, ticker, supports, resistances):
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        vertical_spacing=0.04, row_heights=[0.72, 0.28],
    )
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"], name="OHLC",
        increasing_line_color=BULL, decreasing_line_color=BEAR,
        increasing_fillcolor=BULL, decreasing_fillcolor=BEAR,
    ), row=1, col=1)

    bar_colors = [BULL if c >= o else BEAR
                  for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(
        x=df.index, y=df["Volume"], name="Volume",
        marker_color=bar_colors, showlegend=False, opacity=0.7,
    ), row=2, col=1)

    for lv in supports:
        fig.add_shape(type="line", x0=df.index[0], x1=df.index[-1],
                      y0=lv, y1=lv, line=dict(color=BULL, width=1.5, dash="dot"),
                      row=1, col=1)
        fig.add_annotation(x=df.index[-1], y=lv, text=f" S {lv:,.2f}",
                           showarrow=False, xanchor="left",
                           font=dict(color=BULL, size=10), row=1, col=1)

    for lv in resistances:
        fig.add_shape(type="line", x0=df.index[0], x1=df.index[-1],
                      y0=lv, y1=lv, line=dict(color=BEAR, width=1.5, dash="dot"),
                      row=1, col=1)
        fig.add_annotation(x=df.index[-1], y=lv, text=f" R {lv:,.2f}",
                           showarrow=False, xanchor="left",
                           font=dict(color=BEAR, size=10), row=1, col=1)

    fig.update_layout(
        title=dict(text=f"<b>{ticker}</b> — Candlestick + S/R Levels",
                   font=dict(size=18)),
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        height=580,
        margin=dict(l=60, r=110, t=60, b=40),
        showlegend=False,
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117",
    )
    fig.update_yaxes(gridcolor="#2a2a3e", row=1, col=1)
    fig.update_yaxes(gridcolor="#2a2a3e", row=2, col=1)
    fig.update_xaxes(gridcolor="#2a2a3e")
    return fig


# ─── Section 5: Advanced Analytics Helpers ──────────────────────────────────
# 5A: Portfolio History & Benchmark
# 5B: ETF Look-through & True Exposure
# 5C: Correlation Matrix
# 5D: Drawdown Analysis

# ── 5A: Portfolio History & Benchmark ───────────────────────────────────────

def _strip_tz(series: pd.Series) -> pd.Series:
    """Remove timezone from DatetimeIndex to avoid comparison issues."""
    if hasattr(series.index, "tz") and series.index.tz is not None:
        series = series.copy()
        series.index = series.index.tz_convert(None)
    return series


def adv_fetch_portfolio_history(portfolio_items: list, period: str):
    """
    Fetch historical Close prices for all valid portfolio items.
    Returns (df_prices, port_value_series, failed_tickers).
    port_value = Σ (Close[tk] × qty) each day.
    """
    closes = {}
    failed = []

    for item in portfolio_items:
        tk  = item.get("ticker", "")
        qty = item.get("qty", 0)
        if not tk or qty <= 0:
            continue
        try:
            h = yf.Ticker(tk).history(period=period)
            if not h.empty:
                s = _strip_tz(h["Close"])
                closes[tk] = s
            else:
                failed.append(tk)
        except Exception:
            failed.append(tk)

    if not closes:
        return None, None, failed

    df = pd.DataFrame(closes)
    df = df.ffill().dropna(how="all")

    port_value = pd.Series(0.0, index=df.index)
    for item in portfolio_items:
        tk  = item.get("ticker", "")
        qty = item.get("qty", 0)
        if tk in df.columns and qty > 0:
            port_value = port_value + df[tk] * qty

    port_value = port_value[port_value > 0]
    return df, port_value, failed


def adv_fetch_benchmark(ticker: str, period: str) -> pd.Series:
    """Fetch benchmark close price series. Returns None on failure."""
    try:
        h = yf.Ticker(ticker).history(period=period)
        if not h.empty:
            return _strip_tz(h["Close"])
    except Exception:
        pass
    return None


def adv_normalize(series: pd.Series) -> pd.Series:
    """Normalize a series to start at 100."""
    s = series.dropna()
    if s.empty or s.iloc[0] == 0:
        return s
    return s / s.iloc[0] * 100


def adv_align_normalize(port_value: pd.Series, bench_series: pd.Series):
    """
    Align portfolio and benchmark to a common date range,
    then normalize both to 100 from the common start date.
    Returns (port_norm, bench_norm).
    """
    if bench_series is None or bench_series.empty:
        return adv_normalize(port_value), None

    common_start = max(port_value.index[0], bench_series.index[0])

    pv = port_value[port_value.index >= common_start]
    bs = bench_series[bench_series.index >= common_start]

    bs_reindexed = bs.reindex(pv.index, method="ffill").dropna()
    common_idx   = pv.index.intersection(bs_reindexed.index)

    if common_idx.empty:
        return adv_normalize(port_value), None

    return adv_normalize(pv.loc[common_idx]), adv_normalize(bs_reindexed.loc[common_idx])


# ── 5B: ETF Look-through & True Exposure ────────────────────────────────────

def adv_compute_true_exposure(portfolio_items: list, current_prices: dict,
                              fx_rates: dict = None,
                              manual_holdings: dict = None):
    """
    Compute true portfolio exposure including ETF look-through.
    manual_holdings: dict { etf_ticker_upper: [{"symbol": str, "weight_pct": float}, ...] }
        If provided, uses manual data FIRST before trying yfinance API.
    fx_rates: dict mapping suffix → USD multiplier e.g. {"BK": 0.02985}

    Returns:
        exposure   : dict {symbol: total_market_value_USD}   (combined)
        etf_notes  : list[str]  (log messages for user)
        direct_exp : dict {ticker: mkt_val_USD}              (directly held only)
        etf_exp    : dict {symbol: value_USD}                (from ETF look-through only)
    """
    exposure   = {}
    etf_notes  = []
    direct_exp = {}   # ← directly held stocks
    etf_exp    = {}   # ← ETF look-through holdings
    if fx_rates is None:
        fx_rates = {}
    if manual_holdings is None:
        manual_holdings = {}

    for item in portfolio_items:
        tk  = item.get("ticker", "")
        qty = item.get("qty", 0)
        if not tk or qty <= 0:
            continue

        price      = current_prices.get(tk, 0)
        _suffix    = tk.upper().split(".")[-1] if "." in tk else ""
        _fx        = fx_rates.get(_suffix, 1.0)
        mkt_val    = price * qty * _fx          # แปลงเป็น USD แล้ว
        if mkt_val <= 0:
            exposure[tk] = exposure.get(tk, 0)
            continue

        # ── 1) ตรวจ manual_holdings ก่อน ───────────────────────────────────
        tk_up = tk.upper()
        if tk_up in manual_holdings:
            man_rows = manual_holdings[tk_up]
            if man_rows:
                total_pct = 0.0
                for row in man_rows:
                    sym = str(row.get("symbol", "")).strip().upper()
                    pct = float(row.get("weight_pct", 0) or 0) / 100.0
                    if sym and pct > 0:
                        val = mkt_val * pct
                        exposure[sym] = exposure.get(sym, 0) + val
                        etf_exp[sym]  = etf_exp.get(sym, 0)  + val
                        total_pct += pct
                if total_pct < 0.99:
                    other_key = f"{tk} (Other)"
                    rem = mkt_val * (1.0 - total_pct)
                    exposure[other_key] = exposure.get(other_key, 0) + rem
                    etf_exp[other_key]  = etf_exp.get(other_key, 0)  + rem
                etf_notes.append(
                    f"📋 **{tk}** (Manual): ใช้ข้อมูลจาก Excel — "
                    f"{len(man_rows)} holdings, รวม {total_pct*100:.1f}%")
                continue   # ข้ามขั้นตอน yfinance

        # ── 2) Try yfinance API ──────────────────────────────────────────────
        try:
            info       = yf.Ticker(tk).info
            quote_type = info.get("quoteType", "").upper()
            is_etf     = quote_type in ("ETF", "MUTUALFUND")
            holdings   = info.get("holdings", None) if is_etf else None
        except Exception:
            is_etf   = False
            holdings = None

        if is_etf:
            if holdings and isinstance(holdings, list) and len(holdings) > 0:
                etf_notes.append(
                    f"✅ **{tk}** (ETF): ดึง holdings ได้ {len(holdings)} รายการ")
                total_pct = 0.0
                for h_item in holdings:
                    sym = (h_item.get("symbol") or h_item.get("name") or "").strip()
                    pct = float(h_item.get("holdingPercent", 0) or 0)
                    if sym and pct > 0:
                        val = mkt_val * pct
                        exposure[sym] = exposure.get(sym, 0) + val
                        etf_exp[sym]  = etf_exp.get(sym, 0)  + val
                        total_pct += pct
                # Remaining weight → "TICKER (Other)"
                if total_pct < 0.99:
                    other_key = f"{tk} (Other)"
                    rem = mkt_val * (1.0 - total_pct)
                    exposure[other_key] = exposure.get(other_key, 0) + rem
                    etf_exp[other_key]  = etf_exp.get(other_key, 0)  + rem
            else:
                etf_notes.append(
                    f"⚠️ **{tk}** (ETF): ไม่มีข้อมูล holdings — นับเป็น single asset")
                exposure[tk]    = exposure.get(tk, 0)    + mkt_val
                direct_exp[tk]  = direct_exp.get(tk, 0)  + mkt_val
        else:
            # ← Direct stock holding
            exposure[tk]   = exposure.get(tk, 0)   + mkt_val
            direct_exp[tk] = direct_exp.get(tk, 0) + mkt_val

    return exposure, etf_notes, direct_exp, etf_exp


def adv_get_sector_map(tickers: list) -> dict:
    """
    Fetch sector info for a list of tickers.
    Returns {ticker: sector_string}.
    Falls back to 'Unknown' on any error.
    """
    sector_map = {}
    for tk in tickers:
        try:
            info   = yf.Ticker(tk).info
            sector = info.get("sector") or "Unknown"
            sector_map[tk] = sector
        except Exception:
            sector_map[tk] = "Unknown"
    return sector_map


# ── 5C: Correlation Matrix ───────────────────────────────────────────────────

def adv_compute_correlation(df_prices: pd.DataFrame):
    """
    Compute Pearson correlation matrix of daily returns.
    Returns None if fewer than 2 assets.
    """
    if df_prices is None or df_prices.empty:
        return None
    cols = df_prices.columns.tolist()
    if len(cols) < 2:
        return None
    returns = df_prices[cols].pct_change().dropna()
    if returns.empty:
        return None
    return returns.corr()


# ── 5D: Drawdown Analysis ────────────────────────────────────────────────────

def adv_compute_drawdown(port_value: pd.Series):
    """
    Compute:
      running_max  : pd.Series — cumulative peak
      drawdown_pct : pd.Series — % drop from peak (always <= 0)
      mdd          : float     — Maximum Drawdown (most negative value)
    """
    if port_value is None or port_value.empty:
        return None, None, None

    running_max  = port_value.cummax()
    drawdown_pct = (port_value - running_max) / running_max * 100
    mdd          = float(drawdown_pct.min())
    return running_max, drawdown_pct, mdd


# ─── Section 5E: Executive Summary Snapshot ─────────────────────────────────

@st.cache_data(ttl=300)
def _exec_snapshot(portfolio_items: tuple) -> dict:
    """Fetch latest prices for all portfolio tickers and compute summary stats.
    Cached 5 min to avoid hammering yfinance on every rerun.
    Args: portfolio_items — tuple of (ticker: str, qty: float, avg_cost: float)
    """
    empty = {
        "rows": [], "total_mkt": 0.0, "total_cost": 0.0,
        "total_chg": 0.0, "total_chg_pct": 0.0,
        "total_pnl_pct": 0.0, "prices": {}, "var95": None,
    }
    if not portfolio_items:
        return empty

    # ── FX: THB → USD ─────────────────────────────────
    thb_usd = 1.0 / 33.5
    try:
        _fx_h = yf.Ticker("THBUSD=X").history(period="5d")
        if not _fx_h.empty:
            thb_usd = float(_fx_h["Close"].iloc[-1])
    except Exception:
        pass

    rows, prices, port_series = [], {}, {}
    total_mkt = total_cost = prev_mkt = 0.0

    for _entry in portfolio_items:
        tk, qty, cost = str(_entry[0]).strip().upper(), float(_entry[1]), float(_entry[2])
        if not tk or qty <= 0:
            continue
        try:
            h = yf.Ticker(tk).history(period="1y")
            if h.empty:
                continue
            curr = float(h["Close"].iloc[-1])
            prev = float(h["Close"].iloc[-2]) if len(h) >= 2 else curr
            is_bk    = tk.endswith(".BK")
            fx       = thb_usd if is_bk else 1.0
            mkt_now  = curr * qty * fx
            mkt_prev = prev * qty * fx
            cost_usd = cost * qty * fx
            pnl_pct     = (curr - cost) / cost * 100 if cost > 0 else 0.0
            day_chg_pct = (curr - prev) / prev  * 100 if prev > 0 else 0.0

            # ── Local Extrema S/R — เหมือน Chart Analysis ─────────────────
            support = resistance = None
            try:
                _sups, _ress = find_support_resistance(h, order=10)
                support    = _sups[-1] if _sups else None   # แนวรับที่ใกล้ที่สุด (สูงสุดใต้ราคา)
                resistance = _ress[0]  if _ress else None   # แนวต้านที่ใกล้ที่สุด (ต่ำสุดเหนือราคา)
            except Exception:
                pass

            rows.append({
                "ticker":       tk,
                "price":        curr,
                "day_chg_pct":  day_chg_pct,
                "mkt_val":      mkt_now,
                "cost_usd":     cost_usd,
                "pnl_pct":      pnl_pct,
                "support":      support,
                "resistance":   resistance,
            })
            prices[tk]      = curr
            port_series[tk] = h["Close"] * qty * fx
            total_mkt  += mkt_now
            total_cost += cost_usd
            prev_mkt   += mkt_prev
        except Exception:
            continue

    total_chg     = total_mkt - prev_mkt
    total_chg_pct = total_chg / prev_mkt * 100 if prev_mkt > 0 else 0.0
    total_pnl_pct = (total_mkt - total_cost) / total_cost * 100 if total_cost > 0 else 0.0

    # ── VaR(95%) — 30-day portfolio history ───────────────────────────────
    var95 = None
    try:
        if port_series:
            combined = None
            for _s in port_series.values():
                combined = _s.copy() if combined is None else combined.add(_s, fill_value=0)
            if combined is not None:
                rets = combined.pct_change().dropna() * 100
                if len(rets) >= 5:
                    var95 = float(rets.quantile(0.05))
    except Exception:
        pass

    return {
        "rows": rows, "total_mkt": total_mkt, "total_cost": total_cost,
        "total_chg": total_chg, "total_chg_pct": total_chg_pct,
        "total_pnl_pct": total_pnl_pct, "prices": prices, "var95": var95,
    }


# ─── Section 5F: Portfolio News Feed ────────────────────────────────────────

@st.cache_data(ttl=300)
def _fetch_portfolio_news(tickers_tuple: tuple) -> list:
    """Fetch recent news for all portfolio tickers — cached 5 min
    Handles both yfinance old format (flat dict) and new format (nested content dict)
    """
    from datetime import datetime, timezone
    all_news = []
    for tk in tickers_tuple:
        try:
            items = yf.Ticker(tk).news or []
            for item in items[:4]:  # max 4 per ticker
                # ── yfinance >= 0.2.x: nested under "content" key ──────────
                if "content" in item and isinstance(item["content"], dict):
                    c    = item["content"]
                    title = c.get("title", "")
                    pub   = (c.get("provider") or {}).get("displayName", "")
                    link  = (c.get("canonicalUrl") or {}).get("url", "#") or "#"
                    # pubDate is ISO string e.g. "2025-03-10T14:32:00Z"
                    pub_date = c.get("pubDate", "") or c.get("displayDate", "")
                    try:
                        ts = int(datetime.fromisoformat(
                            pub_date.replace("Z", "+00:00")).timestamp()) if pub_date else 0
                    except Exception:
                        ts = 0
                # ── yfinance < 0.2.x: flat dict ────────────────────────────
                else:
                    title = item.get("title", "")
                    pub   = item.get("publisher", "")
                    link  = item.get("link", "#") or "#"
                    ts    = int(item.get("providerPublishTime", 0))

                if title:  # skip empty-title items
                    all_news.append({
                        "ticker":    tk,
                        "title":     title,
                        "publisher": pub,
                        "link":      link,
                        "ts":        ts,
                    })
        except Exception:
            pass
    all_news.sort(key=lambda x: x["ts"], reverse=True)
    return all_news[:20]


def _news_time_label(ts: int) -> str:
    """Convert Unix timestamp → human-readable Thai label"""
    from datetime import datetime, timezone, timedelta
    if not ts:
        return ""
    now  = datetime.now(timezone.utc)
    pub  = datetime.fromtimestamp(ts, tz=timezone.utc)
    diff = now - pub
    mins = int(diff.total_seconds() // 60)
    if mins < 60:    return f"{mins} นาทีที่แล้ว"
    if mins < 1440:  return f"{mins // 60} ชม.ที่แล้ว"
    return f"{mins // 1440} วันที่แล้ว"


# ─── Section 6: Main App ─────────────────────────────────────────────────────

def main():
    init_db()  # เชื่อมต่อ Google Sheets และตรวจสอบ tabs

    # ════════════════════════════════════
    # SIDEBAR — minimal
    # ════════════════════════════════════
    with st.sidebar:
        st.markdown("## 📈 Investment Dashboard")
        st.caption(f"Last session: {datetime.now().strftime('%d %b %Y %H:%M')}")
        st.divider()
        st.caption("👈 ไปที่แท็บ **✏️ กรอกพอร์ต** เพื่อเพิ่ม/แก้ไขหุ้น")

    # ── initialize before tabs ──
    update_portfolio_btn = False

    # ── Pre-load portfolio into session_state (available to ALL tabs) ─────
    if "portfolio" not in st.session_state:
        _saved = portfolio_load()
        st.session_state.portfolio = _saved if _saved else []

    # ════════════════════════════════════
    # HEADER
    # ════════════════════════════════════
    st.title("📈 Investment Dashboard")
    st.caption(f"Last session: {datetime.now().strftime('%d %b %Y %H:%M')}")

    tab_exec, tab_input, tab_chart, tab_adv = st.tabs([
        "🏠  ภาพรวม",
        "✏️  พอร์ตของฉัน",
        "📊  Chart & Analysis",
        "🚀  Advanced",
    ])
    # Hidden tabs — preserved for future use
    tab_port  = None  # hidden below with if False:
    tab_diary = None  # hidden below with if False:
    tab_watch = None  # hidden below with if False:


    # ════════════════════════════════════════════════════════════════════
    # TAB EXEC — 🏠 Executive Summary
    # ════════════════════════════════════════════════════════════════════
    with tab_exec:
        # ── Auto-jump to Chart tab if triggered from Portfolio Snapshot ──
        if st.session_state.get("chart_jump_trigger"):
            import streamlit.components.v1 as _comp_v1
            _comp_v1.html("""
            <script>
            setTimeout(function() {
                var tabs = window.parent.document.querySelectorAll('[data-baseweb="tab"]');
                for (var i = 0; i < tabs.length; i++) {
                    if (tabs[i].innerText.includes('Chart')) {
                        tabs[i].click();
                        break;
                    }
                }
            }, 150);
            </script>
            """, height=0)
            st.session_state["chart_jump_trigger"] = False

        st.markdown("## 🏠 Executive Summary")

        _port_items = st.session_state.get("portfolio", [])

        # ── Refresh control ───────────────────────────────────────────
        _ref_col, _ts_col = st.columns([1, 5])
        with _ref_col:
            _do_refresh = st.button("🔄 Refresh", key="exec_refresh",
                                    help="อัพเดทราคาล่าสุด (cache 5 นาที)")
        if _do_refresh:
            _exec_snapshot.clear()

        if not _port_items:
            st.info("📋 ยังไม่มีข้อมูลพอร์ต — ไปที่แท็บ **✏️ กรอกพอร์ต** เพื่อเพิ่มหุ้น")
        else:
            # Build a hashable argument for cache (tuple of frozen tuples)
            _cache_key = tuple(
                (item["ticker"], float(item["qty"]), float(item["avg_cost"]))
                for item in _port_items
                if item.get("ticker") and float(item.get("qty", 0)) > 0
            )
            with st.spinner("⏳ กำลังดึงราคาพอร์ต …"):
                _snap = _exec_snapshot(_cache_key)

            # ── Top 4 Metric Cards ─────────────────────────────────────
            _m1, _m2, _m3, _m4 = st.columns(4)
            _chg_sym  = "▲" if _snap["total_chg_pct"] >= 0 else "▼"
            _pnl_sym  = "▲" if _snap["total_pnl_pct"] >= 0 else "▼"
            _var_label = f"{_snap['var95']:.2f}%" if _snap["var95"] is not None else "N/A"

            with _m1:
                st.metric(
                    label="💼 Portfolio Value",
                    value=f"${_snap['total_mkt']:,.0f}",
                )
            with _m2:
                st.metric(
                    label="📅 Today's Change",
                    value=f"{_chg_sym} {abs(_snap['total_chg_pct']):.2f}%",
                    delta=f"${_snap['total_chg']:+,.0f}",
                    delta_color="normal",
                )
            with _m3:
                st.metric(
                    label="📈 Overall P&L",
                    value=f"{_pnl_sym} {abs(_snap['total_pnl_pct']):.2f}%",
                    delta=f"${_snap['total_mkt'] - _snap['total_cost']:+,.0f}",
                    delta_color="normal",
                )
            with _m4:
                _var_color = "normal"
                st.metric(
                    label="⚠️ VaR (95%, 1-day)",
                    value=_var_label,
                    help="Value-at-Risk: โอกาส 5% ที่พอร์ตจะขาดทุนเกินค่านี้ในวันเดียว",
                )

            st.divider()

            # ── Action Items ────────────────────────────────────────────
            _col_act, _col_snap = st.columns([1, 1.4])

            with _col_act:
                st.markdown("### 🎯 Action Items")

                _prices    = _snap.get("prices", {})
                _rows_snap = _snap.get("rows", [])

                _has_action = False

                # 1) Big movers (day change > ±3%)
                for _r in _rows_snap:
                    _d = _r["day_chg_pct"]
                    if abs(_d) >= 3.0:
                        _icon = "🚀" if _d > 0 else "📉"
                        _cls  = "action-buy" if _d > 0 else "action-risk"
                        st.markdown(
                            f'<div class="action-card {_cls}">'
                            f'{_icon} <b>{_r["ticker"]}</b> เคลื่อนไหว '
                            f'<b>{_d:+.1f}%</b> วันนี้'
                            f'</div>', unsafe_allow_html=True
                        )
                        _has_action = True

                # 3) VaR warning
                if _snap["var95"] is not None and _snap["var95"] < -2.5:
                    st.markdown(
                        f'<div class="action-card action-risk">'
                        f'⚠️ <b>ความเสี่ยงสูง</b> — VaR(95%) = {_snap["var95"]:.2f}%<br>'
                        f'พอร์ตมีโอกาส 5% ขาดทุนเกิน {abs(_snap["var95"]):.2f}% ต่อวัน'
                        f'</div>', unsafe_allow_html=True
                    )
                    _has_action = True

                if not _has_action:
                    st.markdown(
                        '<div class="action-card action-info">'
                        '✅ ไม่มี Action ที่ต้องดำเนินการในขณะนี้'
                        '</div>', unsafe_allow_html=True
                    )

            # ── Portfolio Snapshot Table ────────────────────────────────
            with _col_snap:
                st.markdown("### 📊 Portfolio Snapshot")
                if _rows_snap:
                    _df_raw = pd.DataFrame(_rows_snap)

                    # ── helper: format level with % distance from price ──
                    def _fmt_level(price, level):
                        if level is None or (isinstance(level, float) and pd.isna(level)):
                            return "—"
                        dist = (level - price) / price * 100
                        return f"${level:,.2f} ({dist:+.1f}%)"

                    _df_snap = pd.DataFrame({
                        "Ticker":          _df_raw["ticker"],
                        "Price ($)":       _df_raw["price"].map(lambda x: f"${x:,.2f}"),
                        "Day %":           _df_raw["day_chg_pct"].map(lambda x: f"{x:+.2f}%"),
                        "Support ▼":   _df_raw.apply(
                            lambda r: _fmt_level(r["price"], r.get("support")), axis=1),
                        "Resistance ▲": _df_raw.apply(
                            lambda r: _fmt_level(r["price"], r.get("resistance")), axis=1),
                        "P&L %":           _df_raw["pnl_pct"].map(lambda x: f"{x:+.2f}%"),
                        # ซ่อน _dist_s / _dist_r ไว้สำหรับ coloring
                        "_dist_s": _df_raw.apply(
                            lambda r: (r.get("support", r["price"]) - r["price"]) / r["price"] * 100
                            if r.get("support") is not None else 0.0, axis=1),
                        "_dist_r": _df_raw.apply(
                            lambda r: (r.get("resistance", r["price"]) - r["price"]) / r["price"] * 100
                            if r.get("resistance") is not None else 0.0, axis=1),
                    })

                    def _color_row(val, col_name, row_idx):
                        """color by value sign or proximity to S/R"""
                        try:
                            v = float(str(val).replace("%","").replace("+","").replace("$","").replace(",","").split("(")[0].strip())
                        except Exception:
                            return ""
                        if col_name in ("Day %", "P&L %"):
                            if v > 0:   return "color: #34d399; font-weight:700"
                            elif v < 0: return "color: #f87171; font-weight:700"
                        return ""

                    def _color_pct(val):
                        try:
                            v = float(str(val).replace("%","").replace("+",""))
                        except Exception:
                            return ""
                        if v > 0:   return "color: #34d399; font-weight:700"
                        elif v < 0: return "color: #f87171; font-weight:700"
                        return ""

                    def _color_support(val):
                        """ยิ่งใกล้ support ยิ่งเขียว → ส้ม → เหลือง → แดง"""
                        try:
                            dist = float(str(val).split("(")[1].replace("%","").replace(")","").replace("+",""))
                        except Exception:
                            return ""
                        # dist < 0; ใกล้ 0 = ใกล้ support = เขียว, ห่าง = แดง
                        if dist >= -3:    return "color: #10b981; font-weight:700"  # ≤3%  — เขียว
                        elif dist >= -7:  return "color: #f97316; font-weight:600"  # 3-7% — ส้ม
                        elif dist >= -15: return "color: #facc15"                   # 7-15% — เหลือง
                        return "color: #ef4444"                                     # >15% — แดง

                    def _color_resistance(val):
                        """ยิ่งใกล้ resistance ยิ่งแดง → เหลือง → ส้ม → เขียว"""
                        try:
                            dist = float(str(val).split("(")[1].replace("%","").replace(")","").replace("+",""))
                        except Exception:
                            return ""
                        # dist > 0; ใกล้ 0 = ใกล้ resistance = แดง, ห่าง = เขียว
                        if dist <= 3:    return "color: #ef4444; font-weight:700"   # ≤3%  — แดง
                        elif dist <= 7:  return "color: #facc15; font-weight:600"   # 3-7% — เหลือง
                        elif dist <= 15: return "color: #f97316"                    # 7-15% — ส้ม
                        return "color: #10b981"                                     # >15% — เขียว

                    _display = _df_snap[["Ticker","Price ($)","Day %","Support ▼","Resistance ▲","P&L %"]]
                    _styled = _display.style \
                        .map(_color_pct,        subset=["Day %", "P&L %"]) \
                        .map(_color_support,    subset=["Support ▼"]) \
                        .map(_color_resistance, subset=["Resistance ▲"])
                    st.dataframe(_styled, use_container_width=True, hide_index=True)
                    st.caption("แนวรับ/แนวต้าน = Local Extrema (เหมือน Chart Analysis, 6 เดือนย้อนหลัง)  |  Support: 🟢 ≤3% · 🟠 ≤7% · 🟡 ≤15% · 🔴 >15%  |  Resistance: 🔴 ≤3% · 🟡 ≤7% · 🟠 ≤15% · 🟢 >15%")
                else:
                    st.info("ไม่มีข้อมูลราคา")

            # ── Quick-jump buttons — full-width below both columns ──────────
            if _rows_snap:
                st.markdown("**📊 เปิด Chart:**")
                _tickers_in_snap = [r["ticker"] for r in _rows_snap]
                _btn_jump_cols = st.columns(min(len(_tickers_in_snap), 8))
                for _btn_i, _btk in enumerate(_tickers_in_snap):
                    with _btn_jump_cols[_btn_i % len(_btn_jump_cols)]:
                        if st.button(_btk, key=f"snap_goto_{_btk}",
                                     use_container_width=True,
                                     help=f"เปิด Chart Analysis สำหรับ {_btk}  (1y · 1d · SR=10)"):
                            st.session_state["chart_jump_ticker"]   = _btk
                            st.session_state["chart_jump_period"]   = "1y"
                            st.session_state["chart_jump_interval"] = "1d"
                            st.session_state["chart_jump_sr"]       = 10
                            st.session_state["chart_jump_do_fetch"] = True
                            st.session_state["chart_jump_trigger"]  = True
                            st.rerun()

            # ── Portfolio News Feed — HIDDEN ────────────────────────────
            # (re-enable by removing the `if False:` wrapper)
            if False:
                st.divider()
                st.markdown("### 📰 ข่าวหุ้นในพอร์ต")
                _news_tickers = tuple(
                    item["ticker"].upper()
                    for item in st.session_state.get("portfolio", [])
                    if item.get("ticker") and float(item.get("qty", 0)) > 0
                )
                if _news_tickers:
                    with st.spinner("⏳ กำลังโหลดข่าว …"):
                        _news_items = _fetch_portfolio_news(_news_tickers)
                    if _news_items:
                        for _ni in _news_items:
                            _tl = _news_time_label(_ni["ts"])
                            st.markdown(
                                f'<div style="padding:10px 14px;margin-bottom:8px;'
                                f'border-left:3px solid #3b82f6;'
                                f'background:rgba(59,130,246,0.06);border-radius:6px;">'
                                f'<span style="background:#1d4ed8;color:#fff;font-size:11px;'
                                f'padding:2px 7px;border-radius:4px;font-weight:700;'
                                f'margin-right:8px;">{_ni["ticker"]}</span>'
                                f'<a href="{_ni["link"]}" target="_blank" '
                                f'style="color:#e2e8f0;text-decoration:none;font-size:14px;'
                                f'font-weight:500;">{_ni["title"]}</a><br>'
                                f'<span style="color:#64748b;font-size:11px;">'
                                f'{_ni["publisher"]}  ·  {_tl}</span>'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                    else:
                        st.info("ไม่พบข่าวในขณะนี้")
                else:
                    st.info("เพิ่มหุ้นในพอร์ตเพื่อดูข่าว")

            # ── Quick Night Diary ───────────────────────────────────────
            st.markdown("### 📝 Quick Night Diary")
            with st.form("exec_diary_form", clear_on_submit=True):
                # Row 1: Ticker | Date | Mood
                _d_r1 = st.columns([2, 2, 2])
                with _d_r1[0]:
                    _port_tickers = [
                        i["ticker"].upper() for i in st.session_state.get("portfolio", [])
                        if i.get("ticker") and float(i.get("qty", 0)) > 0
                    ]
                    _ticker_opts = ["(ไม่ระบุ)"] + _port_tickers
                    _diary_ticker_sel = st.selectbox(
                        "Ticker", _ticker_opts,
                        help="เลือกหุ้นที่จะบันทึก หรือเลือก '(ไม่ระบุ)' สำหรับ macro note"
                    )
                    _diary_ticker_manual = st.text_input(
                        "หรือพิมพ์ Ticker เอง", placeholder="เช่น TSLA",
                        label_visibility="visible",
                    )
                with _d_r1[1]:
                    _diary_date = st.date_input(
                        "วันที่", value=datetime.now().date(),
                        help="วันที่บันทึก (default = วันนี้)"
                    )
                with _d_r1[2]:
                    _diary_mood = st.selectbox(
                        "Mood", ["😐 Neutral", "🟢 Bullish", "🔴 Bearish", "⚠️ Cautious"],
                    )

                # Row 2: Note
                _diary_note = st.text_area(
                    "บันทึก",
                    placeholder="เช่น TSLA ขึ้น 5% หลัง earnings — พิจารณา trim 10%\nMacro: Fed minutes dovish, risk-on น่าจะต่อเนื่อง",
                    height=90,
                    label_visibility="collapsed",
                )

                _diary_submit = st.form_submit_button(
                    "💾 บันทึก Diary", use_container_width=True, type="primary"
                )

                if _diary_submit and _diary_note.strip():
                    try:
                        # ── resolve ticker ──────────────────────────────
                        _dtk = _diary_ticker_manual.strip().upper() or (
                            "" if _diary_ticker_sel == "(ไม่ระบุ)" else _diary_ticker_sel
                        )
                        # ── ดึงราคาปัจจุบัน ─────────────────────────────
                        _dprice = None
                        if _dtk:
                            try:
                                _dh = yf.Ticker(_dtk).history(period="2d")
                                if not _dh.empty:
                                    _dprice = round(float(_dh["Close"].iloc[-1]), 4)
                            except Exception:
                                pass
                        # ── save ────────────────────────────────────────
                        _full_note = f"[{_diary_mood}] {_diary_note.strip()}"
                        db_save(
                            _dtk or "—",
                            str(_diary_date),
                            "note",
                            _dprice,
                            _full_note,
                        )
                        _price_str = f" @ ${_dprice:,.4f}" if _dprice else ""
                        st.success(f"✅ บันทึกสำเร็จ!{f'  {_dtk}{_price_str}' if _dtk else ''}")
                    except Exception as _e:
                        st.error(f"❌ บันทึกไม่สำเร็จ: {_e}")
                elif _diary_submit:
                    st.warning("กรุณากรอกข้อความก่อนบันทึก")

    # ════════════════════════════════════
    # TAB 0 — Portfolio Input (Excel-style)
    # ════════════════════════════════════
    with tab_input:
        st.markdown("## ✏️ กรอกพอร์ตของฉัน")
        st.caption("พิมพ์ Ticker → กรอกจำนวนหุ้นและทุนเฉลี่ย → กด **💾 Save** เพื่อบันทึก")

        # portfolio already loaded above — just read from session_state
        port_data = st.session_state.portfolio
        if not port_data:
            port_data = [{"ticker": "", "qty": 0.0, "avg_cost": 0.0}]

        # โหลด Rebalancing Targets เพื่อรวมในตารางเดียวกัน
        if "rebalancing" not in st.session_state:
            _rb_raw_init = rebalancing_load()
            st.session_state.rebalancing = [
                {"Ticker": _tk, "Target %": _pct}
                for _tk, _pct in _rb_raw_init.items()
            ]
        _rb_map = {r["Ticker"].upper(): r["Target %"] for r in st.session_state.rebalancing}

        df_port = pd.DataFrame(port_data)[["ticker", "qty", "avg_cost"]]
        df_port.columns = ["Ticker", "จำนวนหุ้น", "ทุนเฉลี่ย ($)"]
        # เพิ่มคอลัมน์ Target % โดย map จาก rebalancing
        df_port["Target %"] = df_port["Ticker"].str.upper().map(_rb_map).fillna(0.0)

        edited_df = st.data_editor(
            df_port,
            column_config={
                "Ticker": st.column_config.TextColumn(
                    "Ticker", width="medium",
                    help="เช่น TSLA, AAPL, PTT.BK (หุ้นไทยใส่ .BK)"
                ),
                "จำนวนหุ้น": st.column_config.NumberColumn(
                    "จำนวนหุ้น", min_value=0.0, format="%.2f", width="medium"
                ),
                "ทุนเฉลี่ย ($)": st.column_config.NumberColumn(
                    "ทุนเฉลี่ย ($)", min_value=0.0, format="%.4f", width="medium",
                    help="หุ้นไทยใส่เป็นบาท เช่น 32.50"
                ),
                "Target %": st.column_config.NumberColumn(
                    "Target % ⚖️", min_value=0.0, max_value=100.0,
                    format="%.1f", width="small",
                    help="สัดส่วนเป้าหมายของ Rebalancing (%) เช่น 20.0"
                ),
            },
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            key="portfolio_editor",
        )

        # แสดงผลรวม Target %
        _target_col_vals = pd.to_numeric(edited_df.get("Target %", pd.Series(dtype=float)), errors="coerce").fillna(0)
        _target_total = _target_col_vals.sum()
        if _target_total > 0:
            _tc_color = "green" if abs(_target_total - 100) < 0.5 else "orange"
            st.caption(
                f"⚖️ รวม Target %: :{_tc_color}[**{_target_total:.1f}%**]"
                + (" ✅" if abs(_target_total - 100) < 0.5 else " ⚠️ ควรรวมเป็น 100%")
            )
        else:
            st.caption("💡 คลิกแถวล่างสุดเพื่อเพิ่มหุ้นใหม่ — คลิกแถวแล้วกด Delete เพื่อลบ | กรอก Target % เพื่อใช้ Rebalancing")

        # ═══════════════════════════════════════════════════════════════
        # ETF Holdings — กรอก Holdings ของ ETF แต่ละตัว
        # ═══════════════════════════════════════════════════════════════
        st.divider()
        st.markdown("### 🔍 ETF Holdings (Look-through)")
        st.caption(
            "กรอก Holdings ของ ETF แต่ละตัวในพอร์ต "
            "เพื่อให้ระบบวิเคราะห์ True Exposure  \n"
            "• **ETF Ticker** = ETF ที่คุณถืออยู่ เช่น `VTI`, `QQQ`  \n"
            "• **Symbol** = หุ้นที่อยู่ภายใน ETF นั้น เช่น `AAPL`  \n"
            "• **Weight %** = สัดส่วนใน ETF (%) เช่น `7.5`"
        )

        if "etf_holdings" not in st.session_state:
            _eh_raw = etf_holdings_load()
            _eh_rows = []
            for _etk, _holdings in _eh_raw.items():
                for _h in _holdings:
                    _eh_rows.append({
                        "ETF Ticker": _etk,
                        "Symbol":     _h["symbol"],
                        "Weight %":   _h["weight_pct"],
                    })
            st.session_state.etf_holdings = _eh_rows

        _eh_data = st.session_state.etf_holdings
        if not _eh_data:
            _eh_data = [{"ETF Ticker": "", "Symbol": "", "Weight %": 0.0}]

        _df_eh_edit = pd.DataFrame(_eh_data)[["ETF Ticker", "Symbol", "Weight %"]]
        _edited_eh = st.data_editor(
            _df_eh_edit,
            column_config={
                "ETF Ticker": st.column_config.TextColumn(
                    "ETF Ticker", width="medium",
                    help="เช่น VTI, QQQ, SPY"
                ),
                "Symbol": st.column_config.TextColumn(
                    "Symbol", width="medium",
                    help="หุ้นที่อยู่ใน ETF เช่น AAPL, MSFT"
                ),
                "Weight %": st.column_config.NumberColumn(
                    "Weight %", min_value=0.0, max_value=100.0,
                    format="%.2f", width="small",
                    help="สัดส่วนใน ETF (%) เช่น 7.5"
                ),
            },
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            key="etf_holdings_editor",
        )
        st.caption("💡 ETF 1 ตัวมีได้หลาย Symbol — กรอกแต่ละ row ด้วย ETF Ticker เดิม")

        # ═══════════════════════════════════════════════════════════════
        # UNIFIED SAVE — บันทึกพอร์ต + ETF Holdings + Rebalancing ทีเดียว
        # ═══════════════════════════════════════════════════════════════
        st.divider()
        st.markdown("### 💾 บันทึกข้อมูลทั้งหมด")
        st.caption("กดปุ่มนี้เพื่อบันทึก **พอร์ตหุ้น**, **ETF Holdings** และ **Rebalancing Targets** ทีเดียวพร้อมกัน")

        _save_col, _ = st.columns([2, 5])
        with _save_col:
            if st.button("💾 บันทึกทั้งหมด", use_container_width=True, type="primary"):
                _save_errors = []

                # 1) Save Portfolio + Rebalancing (อ่านจากตารางเดียวกัน)
                _port_items = []
                _rb_items   = []
                try:
                    for _, _r in edited_df.iterrows():
                        _tk  = str(_r["Ticker"]).strip().upper()
                        _q   = float(_r["จำนวนหุ้น"]) if pd.notna(_r["จำนวนหุ้น"]) else 0.0
                        _c   = float(_r["ทุนเฉลี่ย ($)"]) if pd.notna(_r["ทุนเฉลี่ย ($)"]) else 0.0
                        _pct = float(_r["Target %"]) if pd.notna(_r.get("Target %")) else 0.0
                        if _tk and _q > 0 and _c > 0:
                            _port_items.append({"ticker": _tk, "qty": _q, "avg_cost": _c})
                        if _tk and _pct > 0:
                            _rb_items.append({"ticker": _tk, "target_pct": _pct})
                    portfolio_save(_port_items)
                    st.session_state.portfolio = _port_items
                except Exception as _e:
                    _save_errors.append(f"Portfolio: {_e}")

                # 2) Save ETF Holdings
                try:
                    _eh_items = []
                    for _, _r in _edited_eh.iterrows():
                        _etk2 = str(_r["ETF Ticker"]).strip().upper()
                        _sym2 = str(_r["Symbol"]).strip().upper()
                        _pct2 = float(_r["Weight %"]) if pd.notna(_r["Weight %"]) else 0.0
                        if _etk2 and _sym2 and _pct2 > 0:
                            _eh_items.append({
                                "etf_ticker": _etk2,
                                "symbol":     _sym2,
                                "weight_pct": _pct2,
                            })
                    etf_holdings_save(_eh_items)
                    st.session_state.etf_holdings = [
                        {"ETF Ticker": i["etf_ticker"],
                         "Symbol":     i["symbol"],
                         "Weight %":   i["weight_pct"]}
                        for i in _eh_items
                    ]
                except Exception as _e:
                    _save_errors.append(f"ETF Holdings: {_e}")

                # 3) Save Rebalancing (ใช้ _rb_items ที่สร้างจาก Portfolio loop ด้านบน)
                try:
                    rebalancing_save(_rb_items)
                    st.session_state.rebalancing = [
                        {"Ticker": i["ticker"], "Target %": i["target_pct"]}
                        for i in _rb_items
                    ]
                except Exception as _e:
                    _save_errors.append(f"Rebalancing: {_e}")

                if _save_errors:
                    st.error("⚠️ บันทึกบางส่วนล้มเหลว:\n" + "\n".join(_save_errors))
                else:
                    _p_count  = len(_port_items)  if "_port_items"  in dir() else 0
                    _eh_count = len(_eh_items)    if "_eh_items"    in dir() else 0
                    _rb_count = len(_rb_items)    if "_rb_items"    in dir() else 0
                    st.success(
                        f"✅ บันทึกสำเร็จ! — "
                        f"Portfolio {_p_count} รายการ · "
                        f"ETF Holdings {_eh_count} rows · "
                        f"Rebalancing {_rb_count} rows"
                    )

    # ════════════════════════════════════
    # TAB 1 — Chart & Analysis
    # ════════════════════════════════════
    with tab_chart:
        # ── Consume jump flags from Portfolio Snapshot ─────────────────
        _jump_ticker   = st.session_state.pop("chart_jump_ticker",   None)
        _jump_period   = st.session_state.pop("chart_jump_period",   None)
        _jump_interval = st.session_state.pop("chart_jump_interval", None)
        _jump_sr       = st.session_state.pop("chart_jump_sr",       None)
        _jump_do_fetch = st.session_state.pop("chart_jump_do_fetch", False)

        # ── Smart Ticker Selection: pull from portfolio ────────────────
        _ptk_list = [
            item["ticker"].upper().strip()
            for item in st.session_state.get("portfolio", [])
            if item.get("ticker") and float(item.get("qty", 0)) > 0
        ]
        if _ptk_list:
            _ptk_options = ["(พิมพ์เอง)"] + _ptk_list
            # If jumped from snapshot, pre-select that ticker in the dropdown
            _jump_port_idx = 0
            if _jump_ticker and _jump_ticker.upper() in _ptk_list:
                _jump_port_idx = _ptk_options.index(_jump_ticker.upper())
            _ptk_sel = st.selectbox(
                "📌 เลือกจากพอร์ต",
                options=_ptk_options,
                index=_jump_port_idx,
                help="เลือก Ticker จากพอร์ตของคุณ หรือเลือก '(พิมพ์เอง)' เพื่อกรอก Ticker เอง",
            )
            _default_ticker = "" if _ptk_sel == "(พิมพ์เอง)" else _ptk_sel
        else:
            _default_ticker = "TSLA"

        # Period / interval / sr defaults — override when coming from snapshot
        _period_list   = ["1mo","3mo","6mo","1y","2y","5y"]
        _interval_list = ["1d","1wk","1mo"]
        _period_default_idx   = _period_list.index(_jump_period)   if _jump_period   in _period_list   else 2
        _interval_default_idx = _interval_list.index(_jump_interval) if _jump_interval in _interval_list else 0
        _sr_default           = _jump_sr if _jump_sr is not None else 10

        c1, c2, c3, c4 = st.columns([2.5, 1.2, 1.2, 1.2])
        with c1:
            _ti_val = _jump_ticker if _jump_ticker else (_default_ticker if _default_ticker else "TSLA")
            ticker_input = st.text_input(
                "🔍 Ticker Symbol",
                value=_ti_val,
                placeholder="TSLA / AAPL / BTC-USD"
            ).upper().strip()
        with c2:
            period = st.selectbox("Period", _period_list, index=_period_default_idx)
        with c3:
            interval = st.selectbox("Interval", _interval_list, index=_interval_default_idx)
        with c4:
            sr_order = st.slider("S/R Sensitivity", 2, 20, _sr_default,
                help="ค่าสูง = Major level เท่านั้น")

        fetch_btn = st.button(
            "🔄  Update Data", use_container_width=True, type="primary")

        if fetch_btn or _jump_do_fetch:
            with st.spinner(f"⏳ กำลังดึงข้อมูล {ticker_input} …"):
                try:
                    raw    = yf.Ticker(ticker_input)
                    df_raw = raw.history(period=period, interval=interval)
                    news   = raw.news or []
                    if df_raw.empty:
                        st.error(f"❌ ไม่พบข้อมูล **{ticker_input}**")
                    else:
                        st.session_state["df"]     = df_raw
                        st.session_state["news"]   = news
                        st.session_state["ticker"] = ticker_input
                except Exception as e:
                    st.error(f"❌ Error: {e}")

        if "df" in st.session_state:
            df      = st.session_state["df"]
            news    = st.session_state.get("news", [])
            fetched = st.session_state.get("ticker", ticker_input)

            curr  = df["Close"].iloc[-1]
            prev  = df["Close"].iloc[-2]
            chg   = curr - prev
            chg_p = chg / prev * 100

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("💵 Price",       f"${curr:,.2f}",
                      f"{chg:+.2f} ({chg_p:+.2f}%)")
            m2.metric("📈 Period High", f"${df['High'].max():,.2f}")
            m3.metric("📉 Period Low",  f"${df['Low'].min():,.2f}")
            m4.metric("📦 Avg Volume",  f"{df['Volume'].mean():,.0f}")
            m5.metric("🕯️ Candles",     len(df))

            supports, resistances = find_support_resistance(df, order=sr_order)
            # Store S/R data in session state
            st.session_state["chart_supports"]    = supports
            st.session_state["chart_ticker"]      = fetched
            st.session_state["chart_curr_price"]  = float(curr)

            fig = build_candlestick(df, fetched, supports, resistances)
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            col_s, col_r = st.columns(2)
            with col_s:
                st.markdown(f"### 🟢 Support ({len(supports)})")
                if supports:
                    st.dataframe(pd.DataFrame([
                        {"Level ($)": f"{s:,.2f}",
                         "Distance":  f"-{(curr-s)/curr*100:.2f}%"}
                        for s in reversed(supports)
                    ]), hide_index=True, use_container_width=True)
                else:
                    st.info("ไม่พบแนวรับ")
            with col_r:
                st.markdown(f"### 🔴 Resistance ({len(resistances)})")
                if resistances:
                    st.dataframe(pd.DataFrame([
                        {"Level ($)": f"{r:,.2f}",
                         "Distance":  f"+{(r-curr)/curr*100:.2f}%"}
                        for r in resistances
                    ]), hide_index=True, use_container_width=True)
                else:
                    st.info("ไม่พบแนวต้าน")

            # ── 🎯 Strategic Entry Planner ────────────────────────────────
            st.divider()
            st.markdown("## 🎯 Strategic Entry Planner")
            st.caption(
                "วางแผนการเข้า Position อย่าง Strategic — "
                "เลือก Support Level · จัดสรร USD · คำนวณ Shares อัตโนมัติ"
            )

            # ── Portfolio data ─────────────────────────────────────────
            _sep_port = st.session_state.get("portfolio_data", None)
            _sep_port_val    = 0.0
            _sep_port_labels = []
            _sep_port_values = []
            if _sep_port:
                _, _sep_port_labels, _sep_port_values = _sep_port
                _sep_port_val = float(sum(_sep_port_values))

            # ── Initialise simulation basket ───────────────────────────
            st.session_state.setdefault("sep_sim_basket", {})

            # ── Two-column layout ──────────────────────────────────────
            _sep_c1, _sep_c2 = st.columns([1.4, 2.2], gap="medium")

            with _sep_c1:
                st.markdown("#### 🎯 ตั้งค่า")

                # ── Ticker & Price from chart (no separate input) ──────
                _sep_ticker = fetched
                _cinfo1, _cinfo2 = st.columns(2)
                _cinfo1.metric("📌 Ticker", _sep_ticker)
                _cinfo2.metric("💲 ราคา", f"${float(curr):,.2f}")

                _sep_invest = st.number_input(
                    "💵 งบลงทุนรวม (USD)",
                    min_value=1.0,
                    value=500.0,
                    step=50.0,
                    format="%.2f",
                    key="sep_invest_total",
                )

                # ── Add to Simulation Basket ───────────────────────────
                st.markdown("---")
                if _sep_ticker and _sep_invest > 0:
                    if st.button(
                        f"➕ เพิ่ม {_sep_ticker} → Basket",
                        key="sep_add_basket_btn",
                        help=f"เพิ่ม {_sep_ticker} ${_sep_invest:,.0f} เข้า Simulation Basket",
                    ):
                        st.session_state["sep_sim_basket"][_sep_ticker] = float(_sep_invest)
                        st.rerun()

                # ── Support levels from chart ──────────────────────────
                if supports:
                    _sep_supports = list(reversed(sorted(supports)))[:3]
                    st.success(
                        "✅ Support จากกราฟ: "
                        + ", ".join([f"${s:,.2f}" for s in _sep_supports])
                    )
                else:
                    st.info("ℹ️ ไม่พบ Support จากกราฟ — กรอกเองด้านล่าง")
                    _m_s1 = st.number_input(
                        "Support 1 ($)", min_value=0.0, value=0.0,
                        step=0.5, format="%.2f", key="sep_ms1",
                    )
                    _m_s2 = st.number_input(
                        "Support 2 ($)", min_value=0.0, value=0.0,
                        step=0.5, format="%.2f", key="sep_ms2",
                    )
                    _m_s3 = st.number_input(
                        "Support 3 ($)", min_value=0.0, value=0.0,
                        step=0.5, format="%.2f", key="sep_ms3",
                    )
                    _sep_supports = sorted(
                        [s for s in [_m_s1, _m_s2, _m_s3] if s > 0],
                        reverse=True,
                    )

            # ── Right column: Order Slicing ────────────────────────────
            with _sep_c2:
                st.markdown("#### 📊 จัดสรรงบตาม Support Levels")
                _sep_allocs = []  # (support_price, usd_amount, shares)

                if _sep_supports:
                    _num_levels = len(_sep_supports[:3])
                    for _si, _sup in enumerate(_sep_supports[:3]):
                        _sk = f"sep_usd_{_si}"
                        st.session_state.setdefault(
                            _sk, round(_sep_invest / _num_levels, 2)
                        )
                        _rc_a, _rc_b, _rc_c = st.columns([1.1, 1.6, 1.3])
                        with _rc_a:
                            st.markdown(f"**Level {_si+1}**  \n`${_sup:,.2f}`")
                        with _rc_b:
                            _usd_in = st.number_input(
                                f"USD Lv{_si+1}",
                                min_value=0.0,
                                value=float(st.session_state[_sk]),
                                step=10.0,
                                format="%.2f",
                                label_visibility="collapsed",
                                key=_sk,
                            )
                        with _rc_c:
                            if _sup > 0 and _usd_in > 0:
                                _sh = _usd_in / _sup
                                st.markdown(f"**{_sh:.4f}** sh")
                            else:
                                _sh = 0.0
                                st.markdown("—")
                        _sep_allocs.append((_sup, _usd_in, _sh))

                    _total_usd    = sum(a[1] for a in _sep_allocs)
                    _total_shares = sum(a[2] for a in _sep_allocs)
                    _is_valid     = _total_usd <= _sep_invest + 0.01

                    st.markdown("---")
                    _va, _vb, _vc = st.columns(3)
                    _va.metric("💵 จัดสรรแล้ว",  f"${_total_usd:,.2f}")
                    _vb.metric("🎯 งบรวม",       f"${_sep_invest:,.2f}")
                    _vc.metric("📦 Total Shares", f"{_total_shares:.4f}")

                    if not _is_valid:
                        st.error(
                            f"⚠️ จัดสรรเกินงบ! "
                            f"${_total_usd:,.2f} > ${_sep_invest:,.2f}"
                        )
                    elif _total_usd > 0:
                        st.success(f"✅ งบคงเหลือ: ${_sep_invest - _total_usd:,.2f}")

                    _valid_allocs = [(p, u, s) for p, u, s in _sep_allocs if u > 0]
                    if _valid_allocs:
                        st.markdown("**📋 Summary**")
                        _sum_df = pd.DataFrame([
                            {
                                "Support Price": f"${p:,.2f}",
                                "USD to Spend":  f"${u:,.2f}",
                                "Target Shares": f"{s:.4f}",
                            }
                            for p, u, s in _valid_allocs
                        ])
                        st.dataframe(_sum_df, hide_index=True, use_container_width=True)

                        if _sep_ticker and _is_valid:
                            if st.button(
                                "💾 Add to Planned Trades",
                                key="sep_add_btn",
                                type="primary",
                            ):
                                for _sp, _su, _ssh in _valid_allocs:
                                    pt_add(_sep_ticker, _sp, _su, _ssh)
                                st.success(
                                    f"✅ บันทึก {len(_valid_allocs)} รายการ "
                                    f"สำหรับ {_sep_ticker}"
                                )
                                st.rerun()
                else:
                    st.info("👈 ลด S/R Sensitivity หรือกรอก Support Levels เองด้านซ้าย")

            # ── Portfolio Impact Simulation (multi-stock basket) ───────
            if _sep_port_val > 0:
                st.markdown("---")
                st.markdown("#### 📊 Portfolio Impact Simulation")
                _basket = st.session_state["sep_sim_basket"]

                _bh1, _bh2 = st.columns([3, 1])
                with _bh1:
                    st.caption(
                        "🛒 **Simulation Basket** — "
                        "เพิ่มหุ้นหลายตัวเพื่อดูผลกระทบต่อ Portfolio รวม"
                    )
                with _bh2:
                    if _basket:
                        if st.button("🧹 Clear Basket", key="sep_clear_basket_btn"):
                            st.session_state["sep_sim_basket"] = {}
                            st.rerun()

                if _basket:
                    _bk_hdr = st.columns([2, 2, 0.8])
                    _bk_hdr[0].caption("**Ticker**")
                    _bk_hdr[1].caption("**USD**")
                    _bk_hdr[2].caption("**ลบ**")
                    _to_remove_ = None
                    for _bt_, _bv_ in list(_basket.items()):
                        _bc1_, _bc2_, _bc3_ = st.columns([2, 2, 0.8])
                        _bc1_.markdown(f"`{_bt_}`")
                        _bc2_.markdown(f"${_bv_:,.2f}")
                        with _bc3_:
                            if st.button("🗑️", key=f"sep_rm_{_bt_}"):
                                _to_remove_ = _bt_
                    if _to_remove_:
                        del st.session_state["sep_sim_basket"][_to_remove_]
                        st.rerun()

                    # Build simulated portfolio
                    _cur_labels = list(_sep_port_labels)
                    _cur_vals   = [float(v) for v in _sep_port_values]
                    _cur_total  = float(sum(_cur_vals))
                    _cur_dict   = {
                        str(l).upper(): float(v)
                        for l, v in zip(_cur_labels, _cur_vals)
                    }
                    _sim_dict_: dict = dict(_cur_dict)
                    for _bt_, _bv_ in _basket.items():
                        _sim_dict_[_bt_] = _sim_dict_.get(_bt_, 0.0) + float(_bv_)
                    _sim_total_ = float(sum(_sim_dict_.values()))

                    # ── Shared pie style helper ────────────────────────
                    _pie_layout = dict(
                        template="plotly_dark",
                        paper_bgcolor="#0e1117",
                        plot_bgcolor="#0e1117",
                        height=300,
                        margin=dict(t=32, b=72, l=8, r=8),
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            y=-0.18,
                            x=0.5,
                            xanchor="center",
                            font=dict(size=9, color="#c9d1d9"),
                            itemwidth=40,
                        ),
                    )

                    _sim_pc1, _sim_pc2 = st.columns(2)

                    with _sim_pc1:
                        st.markdown(
                            "<p style='text-align:center;color:#8b949e;"
                            "font-size:13px;margin-bottom:4px'>ก่อน (Current)</p>",
                            unsafe_allow_html=True,
                        )
                        _fig_bef_ = go.Figure(go.Pie(
                            labels=_cur_labels,
                            values=_cur_vals,
                            hole=0.42,
                            sort=True,
                            direction="clockwise",
                            textinfo="percent",
                            textposition="inside",
                            textfont=dict(size=10, color="white"),
                            hovertemplate=(
                                "<b>%{label}</b><br>"
                                "%{percent:.1%}<br>"
                                "$%{value:,.0f}"
                                "<extra></extra>"
                            ),
                            marker=dict(line=dict(color="#0e1117", width=1.5)),
                        ))
                        _fig_bef_.update_layout(**_pie_layout)
                        st.plotly_chart(_fig_bef_, use_container_width=True)

                    with _sim_pc2:
                        st.markdown(
                            "<p style='text-align:center;color:#8b949e;"
                            "font-size:13px;margin-bottom:4px'>หลัง (Simulated)</p>",
                            unsafe_allow_html=True,
                        )
                        _sim_labels_ = list(_sim_dict_.keys())
                        _sim_vals_   = list(_sim_dict_.values())
                        _fig_aft_ = go.Figure(go.Pie(
                            labels=_sim_labels_,
                            values=_sim_vals_,
                            hole=0.42,
                            sort=True,
                            direction="clockwise",
                            textinfo="percent",
                            textposition="inside",
                            textfont=dict(size=10, color="white"),
                            hovertemplate=(
                                "<b>%{label}</b><br>"
                                "%{percent:.1%}<br>"
                                "$%{value:,.0f}"
                                "<extra></extra>"
                            ),
                            marker=dict(line=dict(color="#0e1117", width=1.5)),
                        ))
                        _fig_aft_.update_layout(**_pie_layout)
                        st.plotly_chart(_fig_aft_, use_container_width=True)

                    # Summary metrics
                    _basket_total_ = float(sum(_basket.values()))
                    _sm1, _sm2, _sm3 = st.columns(3)
                    _sm1.metric("🛒 Basket รวม",     f"${_basket_total_:,.2f}")
                    _sm2.metric("📦 Portfolio ก่อน", f"${_cur_total:,.2f}")
                    _sm3.metric("📦 Portfolio หลัง", f"${_sim_total_:,.2f}")

                    # Overweight warnings
                    for _tk_, _av_ in _sim_dict_.items():
                        _aw_ = _av_ / _sim_total_ * 100 if _sim_total_ else 0.0
                        if _aw_ > 20:
                            st.warning(
                                f"⚠️ {_tk_} จะมีน้ำหนัก **{_aw_:.1f}%** "
                                f"ใน Portfolio — สูงกว่า 20% threshold"
                            )
                else:
                    st.info(
                        "กด **➕ เพิ่ม [Ticker] → Basket** ด้านบน "
                        "เพื่อเพิ่มหุ้นลง Basket และดูผลกระทบต่อ Portfolio"
                    )

            # ── Planned Trades Log ─────────────────────────────────────
            st.markdown("---")
            st.markdown("#### 📋 Planned Trades Log")
            _pt_df = pt_load()
            if not _pt_df.empty:
                _pt_disp = _pt_df.rename(columns={
                    "id": "ID", "ticker": "Ticker",
                    "support_price": "Support ($)",
                    "usd_amount": "USD", "shares": "Shares",
                    "created_at": "Created",
                })
                st.dataframe(_pt_disp, hide_index=True, use_container_width=True)
                if st.button("🗑️ Clear All Planned Trades", key="pt_clear_all"):
                    pt_clear()
                    st.rerun()
            else:
                st.info(
                    "ยังไม่มี Planned Trades — "
                    "กรอกแผนด้านบนแล้วกด 'Add to Planned Trades'"
                )

        else:
            st.info("👆 กรอก Ticker แล้วกด **Update Data** เพื่อโหลดกราฟ")

    # ════════════════════════════════════════════════════════════════════════

    if False:  # 💼 Portfolio P&L — hidden (not removed, just disabled)
        # TAB 2 — Portfolio
        # ════════════════════════════════════
        with tab_port:
            if update_portfolio_btn or "portfolio_data" in st.session_state:
                valid = [i for i in st.session_state.portfolio
                         if i["ticker"] and i["qty"] > 0]
                if not valid:
                    st.warning("⚠️ กรุณากรอกข้อมูลหุ้นในแท็บ **✏️ กรอกพอร์ต** ก่อน")
                else:
                    with st.spinner("⏳ กำลังดึงราคา…"):
                        rows, labels, values = [], [], []
                        portfolio_raw_update  = {}          # raw floats สำหรับ What-if Simulator

                        # ── ดึงอัตราแลกเปลี่ยน THB/USD ครั้งเดียว ──────────────
                        _thb_usd = 0.0
                        try:
                            _fx_hist = yf.Ticker("THBUSD=X").history(period="5d")
                            if not _fx_hist.empty:
                                _thb_usd = float(_fx_hist["Close"].iloc[-1])
                        except Exception:
                            pass
                        if _thb_usd <= 0:
                            _thb_usd = 1.0 / 33.5   # fallback ~33.5 THB per USD
                        # ─────────────────────────────────────────────────────────

                        for item in valid:
                            try:
                                hist = yf.Ticker(item["ticker"]).history(period="2d")
                                if hist.empty:
                                    continue
                                price = hist["Close"].iloc[-1]

                                # แปลงค่าเงินถ้าเป็นหุ้นไทย (.BK = บาท → USD)
                                _suffix = item["ticker"].upper().split(".")[-1] \
                                          if "." in item["ticker"] else ""
                                _is_th  = _suffix == "BK"
                                _fx     = _thb_usd if _is_th else 1.0
                                _ccy    = "฿" if _is_th else "$"

                                mkt_val_loc = price * item["qty"]          # มูลค่า local currency
                                mkt_val_usd = mkt_val_loc * _fx            # แปลงเป็น USD
                                cost_loc    = item["avg_cost"] * item["qty"]
                                pnl_loc     = mkt_val_loc - cost_loc       # P&L ใน local currency
                                pnl_p       = (price - item["avg_cost"]) / item["avg_cost"] * 100 \
                                              if item["avg_cost"] > 0 else 0.0

                                labels.append(item["ticker"])
                                values.append(mkt_val_usd)                 # allocation ใช้ USD เสมอ
                                rows.append({
                                    "Ticker":           item["ticker"],
                                    "Shares":           item["qty"],
                                    f"Avg Cost ({_ccy})": f"{item['avg_cost']:,.2f}",
                                    f"Price ({_ccy})":  f"{price:,.2f}",
                                    "Mkt Value ($)":    f"{mkt_val_usd:,.2f}",
                                    "P&L ($)":          f"{pnl_loc * _fx:+,.2f}",
                                    "P&L (%)":          f"{pnl_p:+.2f}%",
                                })
                                portfolio_raw_update[item["ticker"]] = {
                                    "qty":         item["qty"],
                                    "avg_cost":    item["avg_cost"],
                                    "price":       float(price),
                                    "mkt_val_usd": mkt_val_usd,
                                    "cost_usd":    cost_loc * _fx,
                                    "pnl_pct":     pnl_p,
                                    "fx":          _fx,
                                    "is_th":       _is_th,
                                }
                            except Exception:
                                st.warning(f"ดึงข้อมูล {item['ticker']} ไม่ได้")
                        st.session_state["portfolio_data"] = (rows, labels, values)
                        st.session_state["port_thb_usd"]   = _thb_usd
                        st.session_state["portfolio_raw"]  = portfolio_raw_update

                if "portfolio_data" in st.session_state:
                    rows, labels, values = st.session_state["portfolio_data"]
                    _thb_usd_disp = st.session_state.get("port_thb_usd", 1.0/33.5)
                    if rows:
                        total = sum(values)
                        _has_bk = any(".BK" in r["Ticker"].upper() for r in rows)
                        st.markdown(f"## 💰 Total (USD): **${total:,.2f}**")
                        if _has_bk:
                            st.caption(f"💱 อัตราแลกเปลี่ยน THB/USD = {_thb_usd_disp:.6f}  "
                                       f"(≈ {1/_thb_usd_disp:.2f} ฿/$)  — มูลค่าหุ้นไทยแปลงเป็น USD แล้ว")
                        st.divider()
                        col_pie, col_tbl = st.columns([1, 1.3])
                        with col_pie:
                            # ── จัดกลุ่ม slice เล็ก (<2%) เป็น "Others" ──────────
                            _pairs = sorted(zip(values, labels), reverse=True)
                            _pie_vals, _pie_labels = [], []
                            _other_val = 0.0
                            for _v, _l in _pairs:
                                if _v / total >= 0.02:
                                    _pie_vals.append(_v)
                                    _pie_labels.append(_l)
                                else:
                                    _other_val += _v
                            if _other_val > 0:
                                _pie_vals.append(_other_val)
                                _pie_labels.append("Others")
                            # ─────────────────────────────────────────────────────
                            fig_pie = go.Figure(go.Pie(
                                labels=_pie_labels,
                                values=_pie_vals,
                                hole=0.50,
                                textinfo="percent",
                                textposition="inside",
                                insidetextorientation="radial",
                                hovertemplate="<b>%{label}</b><br>$%{value:,.2f}<br>%{percent}<extra></extra>",
                                marker=dict(line=dict(color="#0e1117", width=2)),
                                sort=False,
                            ))
                            fig_pie.update_layout(
                                title=dict(text="Asset Allocation (USD)",
                                           font=dict(size=15)),
                                template="plotly_dark",
                                height=420,
                                margin=dict(l=10, r=10, t=50, b=10),
                                paper_bgcolor="#0e1117",
                                legend=dict(
                                    orientation="v",
                                    x=1.02, y=0.5,
                                    font=dict(size=11),
                                    bgcolor="rgba(0,0,0,0)",
                                ),
                                showlegend=True,
                            )
                            st.plotly_chart(fig_pie, use_container_width=True)
                        with col_tbl:
                            st.markdown("### Holdings Detail")
                            def color_pnl(val):
                                if isinstance(val, str) and "+" in val:
                                    return "color: #26a69a"
                                elif isinstance(val, str) and "-" in val:
                                    return "color: #ef5350"
                                return ""
                            styled = pd.DataFrame(rows).style.applymap(
                                color_pnl, subset=["P&L ($)", "P&L (%)"])
                            st.dataframe(styled, hide_index=True, use_container_width=True)

                        if False:
                            _adv = st.session_state.get("adv_data", {})
                            _man = _adv.get("manual_holdings", {})

                            # ── ปุ่ม Global Shock / Reset ─────────────────────────
                            _shock_col, _reset_col, _sp = st.columns([1.6, 1, 3.4])
                            with _shock_col:
                                _black_swan = st.button(
                                    "💀 Black Swan (−20%)",
                                    key="btn_blackswan",
                                    use_container_width=True,
                                )
                            with _reset_col:
                                _reset_all = st.button(
                                    "🔄 Reset All",
                                    key="btn_reset_wi",
                                    use_container_width=True,
                                )

                            if _black_swan:
                                for _tk_bs in _raw:
                                    st.session_state[f"whatif_pct_{_tk_bs}"] = -20
                            if _reset_all:
                                for _tk_rs in _raw:
                                    st.session_state[f"whatif_pct_{_tk_rs}"] = 0

                            # ── Initialize slider defaults ────────────────────────
                            for _tk_init in _raw:
                                if f"whatif_pct_{_tk_init}" not in st.session_state:
                                    st.session_state[f"whatif_pct_{_tk_init}"] = 0

                            # ── Sliders (ไม่เกิน 4 columns) ──────────────────────
                            _slider_vals = {}
                            _n_cols_wi   = min(len(_raw), 4)
                            _cols_wi     = st.columns(_n_cols_wi)
                            for _ci_wi, _tk_s in enumerate(_raw.keys()):
                                with _cols_wi[_ci_wi % _n_cols_wi]:
                                    _slider_vals[_tk_s] = st.slider(
                                        _tk_s,
                                        min_value=-50,
                                        max_value=50,
                                        step=1,
                                        key=f"whatif_pct_{_tk_s}",
                                        format="%d%%",
                                    )

                            # ── คำนวณ Simulated Market Value ─────────────────────
                            _curr_total  = sum(d["mkt_val_usd"] for d in _raw.values())
                            _sim_details = {}
                            for _tk_c, _rd in _raw.items():
                                _direct_chg = _slider_vals.get(_tk_c, 0) / 100.0
                                _base_mv    = _rd["mkt_val_usd"]
                                _tk_up      = _tk_c.upper().replace(".BK", "")

                                # ETF look-through: ถ้า ticker นี้เป็น ETF ใน manual_holdings
                                # effective_change = direct_slider + Σ(weight_i × constituent_slider_i)
                                if _tk_up in _man:
                                    _const_adj = 0.0
                                    for _row_m in _man[_tk_up]:
                                        _sym_up = _row_m["symbol"].upper()
                                        _w      = _row_m["weight_pct"] / 100.0
                                        _c_tk   = next(
                                            (t for t in _raw
                                             if t.upper().replace(".BK", "") == _sym_up),
                                            None,
                                        )
                                        if _c_tk:
                                            _const_adj += _w * (_slider_vals.get(_c_tk, 0) / 100.0)
                                    _eff_chg = _direct_chg + _const_adj
                                else:
                                    _eff_chg = _direct_chg

                                _sim_mv = _base_mv * (1 + _eff_chg)
                                _sim_details[_tk_c] = {
                                    "curr_mv": _base_mv,
                                    "sim_mv":  _sim_mv,
                                    "delta":   _sim_mv - _base_mv,
                                }

                            _sim_total   = sum(d["sim_mv"] for d in _sim_details.values())
                            _total_delta = _sim_total - _curr_total
                            _pct_delta   = (_total_delta / _curr_total * 100) if _curr_total else 0.0

                            # ── Comparison Metrics ────────────────────────────────
                            st.markdown("#### 📊 Portfolio Comparison")
                            _mc1, _mc2, _mc3 = st.columns(3)
                            _mc1.metric("💼 Current Portfolio",
                                        f"${_curr_total:,.2f}")
                            _mc2.metric("🔮 Simulated Portfolio",
                                        f"${_sim_total:,.2f}",
                                        delta=f"${_total_delta:+,.2f}")
                            _mc3.metric("📈 Change",
                                        f"{_pct_delta:+.2f}%",
                                        delta=f"${_total_delta:+,.2f}")

                            # ── Delta Bar Chart ───────────────────────────────────
                            _bar_tks    = list(_sim_details.keys())
                            _bar_deltas = [_sim_details[t]["delta"] for t in _bar_tks]
                            _bar_colors = [
                                "#26a69a" if d >= 0 else "#ef5350"
                                for d in _bar_deltas
                            ]
                            _fig_wi = go.Figure(go.Bar(
                                x=_bar_tks,
                                y=_bar_deltas,
                                marker_color=_bar_colors,
                                text=[f"${d:+,.0f}" for d in _bar_deltas],
                                textposition="outside",
                                hovertemplate=(
                                    "<b>%{x}</b><br>"
                                    "Delta: $%{y:+,.2f}<extra></extra>"
                                ),
                            ))
                            _fig_wi.update_layout(
                                title="Delta Market Value per Asset (Simulated − Current)",
                                template="plotly_dark",
                                height=360,
                                xaxis_title=None,
                                yaxis_title="USD",
                                paper_bgcolor="#0e1117",
                                plot_bgcolor="#0e1117",
                                margin=dict(l=10, r=10, t=50, b=30),
                                yaxis=dict(gridcolor="#2a2a3a"),
                            )
                            st.plotly_chart(_fig_wi, use_container_width=True)

                            # ── Detail Table ──────────────────────────────────────
                            with st.expander("📋 ดูรายละเอียดแต่ละตัว"):
                                _wi_rows = []
                                for _tk_d, _sd in _sim_details.items():
                                    _wi_rows.append({
                                        "Ticker":        _tk_d,
                                        "Change (%)":    f"{_slider_vals.get(_tk_d, 0):+d}%",
                                        "Current ($)":   f"{_sd['curr_mv']:,.2f}",
                                        "Simulated ($)": f"{_sd['sim_mv']:,.2f}",
                                        "Delta ($)":     f"{_sd['delta']:+,.2f}",
                                        "Weight Now":    (
                                            f"{(_sd['curr_mv'] / _curr_total * 100):.1f}%"
                                            if _curr_total else "—"
                                        ),
                                        "Weight Sim":    (
                                            f"{(_sd['sim_mv'] / _sim_total * 100):.1f}%"
                                            if _sim_total else "—"
                                        ),
                                    })
                                def _wi_color(val):
                                    if isinstance(val, str):
                                        if "+" in val:
                                            return "color: #26a69a"
                                        if val.lstrip().startswith("-"):
                                            return "color: #ef5350"
                                    return ""
                                _wi_styled = pd.DataFrame(_wi_rows).style.applymap(
                                    _wi_color, subset=["Delta ($)", "Change (%)"])
                                st.dataframe(_wi_styled, hide_index=True,
                                             use_container_width=True)
            else:
                st.info("💡 กรอกพอร์ตในแท็บ **✏️ กรอกพอร์ต** แล้วกด **Save & Update P&L**")

        # ════════════════════════════════════
    if False:  # 📔 Investment Diary — hidden
        # TAB 3 — Investment Diary
        # ════════════════════════════════════
        with tab_diary:
            st.markdown("## 📔 Investment Diary")
            st.caption("จดบันทึกเหตุผลการเทรด — บันทึกใน Google Sheets (ไม่หาย)")

            col_form, col_hist = st.columns([1, 1.2])

            with col_form:
                st.markdown("### ✍️ New Entry")
                with st.form("diary_form", clear_on_submit=True):
                    d_ticker = st.text_input("Ticker", placeholder="เช่น TSLA").upper().strip()
                    d_date   = st.date_input("วันที่", value=datetime.now().date())
                    d_type   = st.selectbox("ประเภท",
                        ["🟢 Buy","🔴 Sell","🔵 Analysis","🟡 Watchlist","⚪ Note","⚠️ Risk"])
                    d_price  = st.number_input("ราคาอ้างอิง ($)", min_value=0.0,
                        step=0.01, format="%.2f")
                    d_note   = st.text_area("บันทึก / เหตุผล",
                        placeholder="- เหตุผลที่ซื้อ\n- Stop loss ที่ ...\n- Target ที่ ...",
                        height=180)
                    ok = st.form_submit_button("💾 บันทึก",
                        use_container_width=True, type="primary")

                if ok:
                    if not d_ticker:
                        st.warning("⚠️ ระบุ Ticker ก่อน")
                    elif not d_note.strip():
                        st.warning("⚠️ กรอกบันทึกก่อน")
                    else:
                        db_save(d_ticker, str(d_date), d_type, d_price, d_note.strip())
                        st.success(f"✅ บันทึก [{d_ticker}] สำเร็จ!")
                        st.rerun()

            with col_hist:
                st.markdown("### 📜 ประวัติ")
                f1, f2 = st.columns(2)
                with f1:
                    f_ticker = st.text_input("กรอง Ticker",
                        placeholder="เว้นว่าง = ทั้งหมด").upper().strip()
                with f2:
                    f_type = st.selectbox("กรอง Type",
                        ["ทั้งหมด","🟢 Buy","🔴 Sell","🔵 Analysis",
                         "🟡 Watchlist","⚪ Note","⚠️ Risk"])

                diary_df = db_load(f_ticker)
                if f_type != "ทั้งหมด":
                    diary_df = diary_df[diary_df["entry_type"] == f_type]

                if diary_df.empty:
                    st.info("ยังไม่มีบันทึก — เริ่มจดได้เลย!")
                else:
                    st.caption(f"พบ {len(diary_df)} รายการ")
                    for _, row in diary_df.iterrows():
                        p_str = f"@ ${row['price_ref']:.2f}" \
                                if row["price_ref"] and row["price_ref"] > 0 else ""
                        hdr = (f"{row['entry_type']}  **{row['ticker']}**  "
                               f"{p_str}  —  {row['entry_date']}  "
                               f"*(saved {row['created_at']})*")
                        with st.expander(hdr):
                            st.markdown(row["note"])
                            if st.button("🗑️ ลบ", key=f"del_{row['id']}", type="secondary"):
                                db_delete_diary(int(row["id"]))
                                st.rerun()

        # ════════════════════════════════════
    if False:  # 🌙 Watchlist — hidden
        # TAB 4 — Watchlist
        # ════════════════════════════════════
        with tab_watch:
            st.markdown("## 🌙 Watchlist")
            st.caption("รายชื่อหุ้นที่จับตาดู — กด **Refresh Prices** เพื่ออัปเดตราคาทั้งหมด")

            w1, w2, w3 = st.columns([1.5, 2, 1])
            with w1:
                wl_ticker = st.text_input("Ticker", placeholder="e.g. TSLA",
                    label_visibility="collapsed").upper().strip()
            with w2:
                wl_note = st.text_input("หมายเหตุ", placeholder="เช่น รอ breakout / ดูรายงาน Q3",
                    label_visibility="collapsed")
            with w3:
                if st.button("➕ Add to Watchlist", use_container_width=True):
                    if wl_ticker:
                        wl_add(wl_ticker, wl_note)
                        st.success(f"✅ เพิ่ม {wl_ticker} แล้ว")
                        st.rerun()
                    else:
                        st.warning("กรอก Ticker ก่อนนะครับ")

            st.divider()

            wl_df = wl_load()
            if wl_df.empty:
                st.info("💡 ยังไม่มีหุ้นใน Watchlist — เพิ่มด้านบนได้เลย")
            else:
                refresh_btn = st.button(
                    "🔄 Refresh Prices", use_container_width=True, type="primary")

                if refresh_btn or "wl_prices" in st.session_state:
                    if refresh_btn:
                        with st.spinner("⏳ กำลังดึงราคา Watchlist…"):
                            wl_rows = []
                            for _, wrow in wl_df.iterrows():
                                try:
                                    hist = yf.Ticker(wrow["ticker"]).history(period="2d")
                                    if hist.empty:
                                        raise ValueError("no data")
                                    p   = hist["Close"].iloc[-1]
                                    p0  = hist["Close"].iloc[-2] if len(hist) >= 2 else p
                                    chg = p - p0
                                    chg_p = chg / p0 * 100 if p0 else 0
                                    wl_rows.append({
                                        "_id":       wrow["id"],
                                        "Ticker":    wrow["ticker"],
                                        "Price ($)": round(p, 2),
                                        "Chg ($)":   f"{chg:+.2f}",
                                        "Chg (%)":   f"{chg_p:+.2f}%",
                                        "Note":      wrow["note"] or "",
                                        "Added":     wrow["added_at"],
                                    })
                                except Exception:
                                    wl_rows.append({
                                        "_id":       wrow["id"],
                                        "Ticker":    wrow["ticker"],
                                        "Price ($)": "N/A",
                                        "Chg ($)":   "—",
                                        "Chg (%)":   "—",
                                        "Note":      wrow["note"] or "",
                                        "Added":     wrow["added_at"],
                                    })
                            st.session_state["wl_prices"] = wl_rows

                    wl_rows = st.session_state.get("wl_prices", [])

                    if wl_rows:
                        st.caption(f"อัปเดตล่าสุด: {datetime.now().strftime('%H:%M:%S')}")

                        for wr in wl_rows:
                            col_t, col_p, col_c, col_cp, col_n, col_btn = st.columns(
                                [1, 1, 0.8, 0.8, 2.5, 0.6])
                            with col_t:
                                st.markdown(f"**{wr['Ticker']}**")
                            with col_p:
                                p_val = wr['Price ($)']
                                st.markdown(f"`${p_val}`" if p_val != "N/A" else "`N/A`")
                            with col_c:
                                chg_str = wr['Chg ($)']
                                color = "positive" if "+" in str(chg_str) else \
                                        "negative" if "-" in str(chg_str) else ""
                                st.markdown(
                                    f'<span class="{color}">{chg_str}</span>',
                                    unsafe_allow_html=True)
                            with col_cp:
                                cp_str = wr['Chg (%)']
                                color2 = "positive" if "+" in str(cp_str) else \
                                         "negative" if "-" in str(cp_str) else ""
                                st.markdown(
                                    f'<span class="{color2}">{cp_str}</span>',
                                    unsafe_allow_html=True)
                            with col_n:
                                st.caption(wr["Note"])
                            with col_btn:
                                if st.button("🗑️", key=f"wl_del_{wr['_id']}",
                                             help="ลบออกจาก Watchlist"):
                                    wl_delete(int(wr["_id"]))
                                    if "wl_prices" in st.session_state:
                                        del st.session_state["wl_prices"]
                                    st.rerun()

                        st.divider()

                        with st.expander("📈 เปรียบเทียบ % Return ของ Watchlist"):
                            tickers_in_wl = [wr["Ticker"] for wr in wl_rows
                                             if wr["Price ($)"] != "N/A"]
                            if tickers_in_wl:
                                with st.spinner("กำลังโหลดกราฟ…"):
                                    fig_cmp = go.Figure()
                                    for tk in tickers_in_wl:
                                        try:
                                            h = yf.Ticker(tk).history(period="3mo")
                                            if h.empty:
                                                continue
                                            norm = (h["Close"] / h["Close"].iloc[0] - 1) * 100
                                            fig_cmp.add_trace(go.Scatter(
                                                x=h.index, y=norm, name=tk, mode="lines"))
                                        except Exception:
                                            pass
                                    fig_cmp.update_layout(
                                        title="% Return (3 เดือน)",
                                        template="plotly_dark",
                                        yaxis_title="% Return",
                                        height=380,
                                        hovermode="x unified",
                                        paper_bgcolor="#0e1117",
                                        plot_bgcolor="#0e1117",
                                    )
                                    st.plotly_chart(fig_cmp, use_container_width=True)
                else:
                    st.caption(f"มี {len(wl_df)} หุ้นใน Watchlist — กด Refresh Prices เพื่อดูราคา")
                    for _, wrow in wl_df.iterrows():
                        c1_, c2_, c3_ = st.columns([1, 3, 0.5])
                        with c1_:
                            st.markdown(f"**{wrow['ticker']}**")
                        with c2_:
                            st.caption(wrow["note"] or "")
                        with c3_:
                            if st.button("🗑️", key=f"wl_pre_{wrow['id']}"):
                                wl_delete(int(wrow["id"]))
                                st.rerun()

            # ════════════════════════════════════════════════════════════════
    # TAB 5 — 🚀 ADVANCED ANALYTICS  (NEW v3)
    # ════════════════════════════════════════════════════════════════════════
    with tab_adv:
        st.markdown("## 🚀 Advanced Analytics")
        st.caption(
            "วิเคราะห์เชิงลึก: Benchmark · Risk/Correlation · Rebalancing"
        )

        valid_port = [i for i in st.session_state.portfolio
                      if i.get("ticker") and i.get("qty", 0) > 0]

        if not valid_port:
            st.warning("⚠️ กรุณากรอกข้อมูลพอร์ตในแท็บ **✏️ กรอกพอร์ต** ก่อน แล้วกด Save & Update P&L")
        else:
            # ── Control Row ──────────────────────────────────────────────
            ctrl1, ctrl2, ctrl3 = st.columns([1.5, 1.8, 1])
            with ctrl1:
                adv_period = st.selectbox(
                    "📅 Period",
                    ["3mo", "6mo", "1y", "2y", "3y"],
                    index=2,
                    key="adv_period",
                )
            with ctrl2:
                benchmark_opts = {
                    "S&P 500 (^GSPC)":   "^GSPC",
                    "NASDAQ (^IXIC)":    "^IXIC",
                    "SET Index (^SET.BK)": "^SET.BK",
                    "QQQ (NASDAQ ETF)":  "QQQ",
                    "Gold (GC=F)":       "GC=F",
                }
                bench_label  = st.selectbox(
                    "📌 Benchmark", list(benchmark_opts.keys()), key="adv_bench")
                bench_ticker = benchmark_opts[bench_label]
            with ctrl3:
                run_adv_btn = st.button(
                    "🔄 Run Analysis", type="primary",
                    use_container_width=True, key="run_adv")

            # ── Fetch & Cache ─────────────────────────────────────────────
            if run_adv_btn:
                with st.spinner("⏳ กำลังดึงข้อมูลพอร์ต & Benchmark…"):
                    df_px, pv, failed = adv_fetch_portfolio_history(
                        valid_port, adv_period)
                    bench_s = adv_fetch_benchmark(bench_ticker, adv_period)

                    # Current prices from last row of history
                    cur_prices = {}
                    if df_px is not None:
                        for tk in df_px.columns:
                            last = df_px[tk].dropna()
                            if not last.empty:
                                cur_prices[tk] = float(last.iloc[-1])

                    # ── ดึงอัตราแลกเปลี่ยน THB/USD ──────────────────────
                    _adv_thb_usd = 0.0
                    try:
                        _fx_h = yf.Ticker("THBUSD=X").history(period="5d")
                        if not _fx_h.empty:
                            _adv_thb_usd = float(_fx_h["Close"].iloc[-1])
                    except Exception:
                        pass
                    if _adv_thb_usd <= 0:
                        _adv_thb_usd = 1.0 / 33.5
                    _adv_fx_rates = {"BK": _adv_thb_usd}

                    # ── อ่าน ETF_Holdings + Rebalancing จาก Google Sheets ──
                    _manual_holdings = {}
                    _target_pcts_xl  = {}
                    try:
                        _manual_holdings = etf_holdings_load()
                    except Exception:
                        pass
                    try:
                        _target_pcts_xl = rebalancing_load()
                    except Exception:
                        pass
                    # ─────────────────────────────────────────────────────

                    st.session_state["adv_data"] = {
                        "df_prices":       df_px,
                        "port_value":      pv,
                        "bench_series":    bench_s,
                        "bench_ticker":    bench_ticker,
                        "bench_label":     bench_label,
                        "cur_prices":      cur_prices,
                        "valid_port":      valid_port,
                        "period":          adv_period,
                        "failed":          failed,
                        "fx_rates":        _adv_fx_rates,
                        "thb_usd":         _adv_thb_usd,
                        "manual_holdings": _manual_holdings,
                        "target_pcts_xl":  _target_pcts_xl,
                    }
                if failed:
                    st.warning(f"⚠️ ดึงข้อมูลไม่ได้: {', '.join(failed)}")
                else:
                    st.success("✅ โหลดข้อมูลเสร็จแล้ว!")

            if "adv_data" not in st.session_state:
                st.info("👆 กด **Run Analysis** เพื่อเริ่มวิเคราะห์")
            else:
                D = st.session_state["adv_data"]

                adv_t1, adv_t2, adv_t3 = st.tabs([
                    "📈 Benchmark",
                    "🔍 Risk & Correlation",
                    "⚖️ Rebalancing",
                    # "📉 Drawdown",  # Hidden — uncomment + add adv_t4 to enable
                ])

                # ────────────────────────────────────────────────────────
                # SUB-TAB A — Benchmark
                # ────────────────────────────────────────────────────────
                with adv_t1:
                    st.markdown(f"### 📈 Portfolio vs {D['bench_label']}")
                    pv = D["port_value"]

                    if pv is None or pv.empty:
                        st.error("❌ ไม่สามารถสร้าง Portfolio history ได้")
                    else:
                        port_norm, bench_norm = adv_align_normalize(
                            pv, D["bench_series"])

                        port_ret = float(port_norm.iloc[-1]) - 100

                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("📊 Portfolio Return",
                                  f"{port_ret:+.2f}%",
                                  help="Cumulative return ตลอด period ที่เลือก")
                        m4.metric("📅 Period", D["period"])

                        if bench_norm is not None and not bench_norm.empty:
                            bench_ret = float(bench_norm.iloc[-1]) - 100
                            alpha     = port_ret - bench_ret
                            m2.metric(f"📌 {D['bench_label'][:18]}",
                                      f"{bench_ret:+.2f}%")
                            m3.metric("🎯 Alpha (Port − Bench)",
                                      f"{alpha:+.2f}%",
                                      delta="ชนะ Benchmark ✅" if alpha >= 0
                                            else "แพ้ Benchmark ❌",
                                      delta_color="normal")
                        else:
                            st.warning(
                                f"⚠️ ดึงข้อมูล {D['bench_ticker']} ไม่ได้ "
                                f"— แสดงเฉพาะ Portfolio")

                        # Chart
                        fig_b = go.Figure()
                        fig_b.add_trace(go.Scatter(
                            x=port_norm.index, y=port_norm.values,
                            name="📊 My Portfolio", mode="lines",
                            line=dict(color="#7c3aed", width=2.5),
                        ))
                        if bench_norm is not None and not bench_norm.empty:
                            fig_b.add_trace(go.Scatter(
                                x=bench_norm.index, y=bench_norm.values,
                                name=f"📌 {D['bench_label']}", mode="lines",
                                line=dict(color="#ff9800", width=2, dash="dash"),
                            ))
                        fig_b.add_hline(
                            y=100, line_dash="dot", line_color="#555",
                            annotation_text="Base (100)",
                            annotation_position="bottom right")
                        fig_b.update_layout(
                            title=f"Cumulative Return — Normalized (Base = 100)",
                            template="plotly_dark", height=460,
                            yaxis_title="Normalized Value",
                            hovermode="x unified",
                            legend=dict(orientation="h", y=1.02, x=0),
                            paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                        )
                        fig_b.update_xaxes(gridcolor="#2a2a3e")
                        fig_b.update_yaxes(gridcolor="#2a2a3e")
                        st.plotly_chart(fig_b, use_container_width=True)

                        st.caption(
                            "**หมายเหตุ:** ผลตอบแทนพอร์ตคำนวณจากราคา × จำนวนหุ้น "
                            "(ไม่รวม Dividend) / ราคาเริ่มต้น × 100")

                # ────────────────────────────────────────────────────────
                # SUB-TAB B — Risk & Correlation
                # ────────────────────────────────────────────────────────
                with adv_t2:
                    st.markdown("### 🔍 Risk Concentration & Correlation")

                    cur_prices       = D["cur_prices"]
                    df_px            = D["df_prices"]
                    vp               = D["valid_port"]
                    _fx_rates        = D.get("fx_rates", {})
                    _man_holdings    = D.get("manual_holdings", {})

                    # ── ETF Look-through (Manual first → yfinance fallback) ──
                    _src_label = "Excel" if _man_holdings else "yfinance API"
                    with st.spinner(f"🔍 วิเคราะห์ ETF holdings ({_src_label})…"):
                        exposure, etf_notes, direct_exp, etf_exp = (
                            adv_compute_true_exposure(
                                vp, cur_prices, _fx_rates, _man_holdings))

                    if etf_notes:
                        with st.expander("📋 ETF Look-through Log", expanded=False):
                            for note in etf_notes:
                                st.markdown(note)

                    if not exposure:
                        st.warning("⚠️ ไม่มีข้อมูล Exposure — ตรวจสอบราคาหุ้น")
                    else:
                        total_exp = sum(exposure.values())

                        # ── Sector map for main tickers ──
                        main_tks = [i["ticker"] for i in vp]
                        with st.spinner("📊 กำลังดึง Sector info…"):
                            sector_map = adv_get_sector_map(main_tks)

                        def _sector(sym):
                            if sym in sector_map:
                                return sector_map[sym] or "Unknown"
                            if "(Other)" in sym:
                                return "ETF — Other"
                            return "ETF Holdings"

                        exp_df = pd.DataFrame([
                            {
                                "Symbol":   k,
                                "Sector":   _sector(k),
                                "Value":    v,
                                "Alloc %":  v / total_exp * 100,
                            }
                            for k, v in sorted(
                                exposure.items(), key=lambda x: -x[1])
                        ])

                        # Exposure table
                        disp = exp_df.copy()
                        disp["Value"] = disp["Value"].map("${:,.2f}".format)
                        disp["Alloc %"] = disp["Alloc %"].map("{:.2f}%".format)
                        st.dataframe(disp, hide_index=True,
                                     use_container_width=True)

                        # ── Overlap: Direct vs ETF Exposure ──────────
                        st.markdown("---")
                        st.markdown("#### 🔄 Overlap Analysis — Direct vs ETF")
                        st.caption(
                            "หุ้นที่ถือตรงในพอร์ต **และ** ปรากฏใน ETF Look-through "
                            "— แสดงความเสี่ยงที่ซ้อนทับกัน")

                        # สร้าง set ของ ticker ที่ถือตรง (normalize upper)
                        _direct_keys = {k.upper() for k in direct_exp}
                        _etf_keys    = {k.upper() for k in etf_exp}
                        _overlap_set = _direct_keys & _etf_keys

                        if not _overlap_set:
                            st.info(
                                "✅ ไม่มี Overlap — หุ้นในพอร์ตไม่ทับซ้อนกับ "
                                "ETF holdings ที่วิเคราะห์")
                        else:
                            # แถว all symbols: direct + etf (union)
                            _all_syms = sorted(
                                _direct_keys | _etf_keys,
                                key=lambda s: -(
                                    direct_exp.get(s, 0) + etf_exp.get(s, 0)))
                            ov_rows = []
                            for sym in _all_syms:
                                dv = direct_exp.get(sym, 0)
                                ev = etf_exp.get(sym, 0)
                                tv = dv + ev
                                ov_rows.append({
                                    "Symbol":          sym,
                                    "Direct ($)":      dv   if dv > 0 else None,
                                    "ETF Exposure ($)": ev  if ev > 0 else None,
                                    "Total ($)":       tv,
                                    "Total %":         tv / total_exp * 100,
                                    "Overlap":         "⚠️ ทับซ้อน"
                                                       if sym in _overlap_set
                                                       else "",
                                })

                            ov_df = pd.DataFrame(ov_rows)

                            # Format for display
                            ov_disp = ov_df.copy()
                            for col in ["Direct ($)", "ETF Exposure ($)",
                                        "Total ($)"]:
                                ov_disp[col] = ov_disp[col].apply(
                                    lambda x: f"${x:,.2f}" if x is not None
                                    and x > 0 else "—")
                            ov_disp["Total %"] = ov_disp["Total %"].map(
                                "{:.2f}%".format)

                            st.dataframe(ov_disp, hide_index=True,
                                         use_container_width=True)


                    # ── Correlation Matrix ────────────────────────────
                    st.markdown("---")
                    st.markdown("#### 🔄 Correlation Matrix (Daily Returns)")

                    corr_df = adv_compute_correlation(df_px)

                    if corr_df is None:
                        st.info(
                            "ต้องมีหุ้นอย่างน้อย **2 ตัว** ในพอร์ตเพื่อคำนวณ Correlation")
                    else:
                        n_assets = len(corr_df)
                        fig_corr = go.Figure(go.Heatmap(
                            z=corr_df.values,
                            x=corr_df.columns.tolist(),
                            y=corr_df.index.tolist(),
                            colorscale="RdBu",
                            zmid=0, zmin=-1, zmax=1,
                            text=[[f"{v:.2f}" for v in row]
                                  for row in corr_df.values],
                            texttemplate="%{text}",
                            textfont={"size": 13},
                            hovertemplate=(
                                "<b>%{y} vs %{x}</b><br>"
                                "Correlation: %{z:.3f}<extra></extra>"),
                        ))
                        fig_corr.update_layout(
                            title="Correlation Matrix (Daily Returns)",
                            template="plotly_dark",
                            height=max(350, n_assets * 65 + 100),
                            paper_bgcolor="#0e1117",
                            plot_bgcolor="#0e1117",
                        )
                        st.plotly_chart(fig_corr, use_container_width=True)

                        st.caption(
                            "**การอ่านค่า:**  "
                            "+1.0 = เคลื่อนไหวเหมือนกันทุกประการ  |  "
                            "0 = ไม่สัมพันธ์กัน  |  "
                            "-1.0 = เคลื่อนไหวตรงข้ามกัน")

                        # Highlight high correlations
                        high_pairs = [
                            (corr_df.index[i], corr_df.columns[j],
                             corr_df.iloc[i, j])
                            for i in range(n_assets)
                            for j in range(i + 1, n_assets)
                            if abs(corr_df.iloc[i, j]) >= 0.80
                        ]
                        if high_pairs:
                            pairs_txt = ", ".join(
                                f"**{a}&{b}** ({c:.2f})"
                                for a, b, c in high_pairs[:6])
                            st.warning(
                                f"⚠️ พบ High Correlation ≥ 0.80 "
                                f"({len(high_pairs)} คู่): {pairs_txt}  \n"
                                "หุ้นที่ correlation สูงมาก ให้ผลกระจาย risk น้อย")

                # ────────────────────────────────────────────────────────
                # ────────────────────────────────────────────────────────
                # SUB-TAB C — Rebalancing  (Google Sheets-driven)
                # ────────────────────────────────────────────────────────
                with adv_t3:
                    st.markdown("### ⚖️ Rebalancing Summary")
                    st.caption(
                        "กรอก **Target %** ในคอลัมน์ **Target % ⚖️** ของตารางพอร์ต (แท็บ ✏️ กรอกพอร์ต) "
                        "→ กด **💾 บันทึกทั้งหมด** → กด **Run Analysis** เพื่อโหลดผล"
                    )

                    cur_prices      = D["cur_prices"]
                    vp              = D["valid_port"]
                    _rb_fx          = D.get("fx_rates", {})
                    _target_pcts_xl = D.get("target_pcts_xl", {})

                    # ── Build port value list ────────────────────────────
                    port_w_val = []
                    total_val  = 0.0
                    for item in vp:
                        tk     = item["ticker"]
                        qty    = item.get("qty", 0)
                        prc    = cur_prices.get(tk, 0)
                        _sfx   = tk.upper().split(".")[-1] if "." in tk else ""
                        _fxrb  = _rb_fx.get(_sfx, 1.0)
                        mv     = prc * qty * _fxrb
                        port_w_val.append({**item, "price": prc, "mkt_val": mv})
                        total_val += mv

                    if total_val <= 0:
                        st.error("❌ ไม่มีข้อมูลราคา — กลับไปกด **Run Analysis**")
                    elif not _target_pcts_xl:
                        # ── ยังไม่มีข้อมูล Rebalancing ───────────────────
                        st.warning(
                            "📋 **ยังไม่มีข้อมูล Target %**\n\n"
                            "**วิธีกรอก:**\n"
                            "1. ไปที่แท็บ ✏️ **กรอกพอร์ต** → คอลัมน์ **Target % ⚖️** ในตารางหลัก\n"
                            "2. กรอก Target % ของแต่ละหุ้นให้รวม = **100%**\n"
                            "3. กด **💾 บันทึกทั้งหมด** → กลับมากด **Run Analysis** อีกครั้ง"
                        )
                        # แสดงตาราง current allocation เป็น reference
                        st.markdown("##### 📊 Current Allocation (อ้างอิง)")
                        ref_rows = []
                        for item in port_w_val:
                            ref_rows.append({
                                "Ticker":      item["ticker"],
                                "Market Value ($)":
                                    f"${item['mkt_val']:,.2f}",
                                "Current %":
                                    f"{item['mkt_val']/total_val*100:.2f}%",
                            })
                        st.dataframe(ref_rows, use_container_width=True,
                                     hide_index=True)
                    else:
                        # ── มีข้อมูล Target จาก Excel ────────────────────
                        tgt_sum = sum(_target_pcts_xl.values())
                        _xl_ok  = abs(tgt_sum - 100) <= 0.6

                        _info_col, _val_col = st.columns([3, 1])
                        _info_col.success(
                            f"📋 โหลด Target จาก Excel — "
                            f"**{len(_target_pcts_xl)} Tickers**, รวม **{tgt_sum:.1f}%**")
                        _val_col.metric("💰 Total Value", f"${total_val:,.2f}")

                        if not _xl_ok:
                            st.error(
                                f"⚠️ Target รวม = **{tgt_sum:.1f}%** — ควรได้ 100%  "
                                "กรุณาแก้ใน Excel แล้ว Run Analysis ใหม่")

                        threshold = st.slider(
                            "⚠️ Alert Threshold (%)",
                            min_value=1, max_value=20, value=5,
                            help="แจ้งเตือนเมื่อ Deviation เกินค่านี้",
                            key="rebal_threshold")

                        st.markdown("---")
                        st.markdown("#### 📊 Rebalancing Summary")

                        n_stocks    = len(port_w_val)
                        default_pct = round(100.0 / n_stocks, 1)
                        rebal_rows  = []
                        has_alert   = False

                        for item in port_w_val:
                            tk       = item["ticker"]
                            curr_pct = item["mkt_val"] / total_val * 100
                            # ใช้ Target จาก Excel; ถ้าไม่มี ticker นั้น → equal weight
                            tgt_pct  = _target_pcts_xl.get(
                                tk.upper(), default_pct)
                            deviation = curr_pct - tgt_pct
                            tgt_val   = tgt_pct / 100 * total_val
                            diff_val  = tgt_val - item["mkt_val"]
                            diff_sh   = (diff_val / item["price"]
                                         if item["price"] > 0 else 0)
                            alerted   = abs(deviation) > threshold
                            if alerted:
                                has_alert = True
                            rebal_rows.append({
                                "tk":       tk,
                                "curr_pct": curr_pct,
                                "tgt_pct":  tgt_pct,
                                "dev":      deviation,
                                "diff_val": diff_val,
                                "diff_sh":  diff_sh,
                                "alerted":  alerted,
                            })

                        # ── Summary table ────────────────────────────────
                        h0, h1, h2, h3, h4, h5 = st.columns(
                            [1, 1.1, 1.1, 1.1, 1.5, 2.2])
                        for hdr, col in zip(
                            ["Ticker", "Current %", "Target %",
                             "Deviation", "Action ($)", "Status"],
                            [h0, h1, h2, h3, h4, h5]):
                            col.markdown(f"**{hdr}**")

                        for r in rebal_rows:
                            action_lbl = (
                                f"{'🟢 ซื้อ' if r['diff_val'] > 0 else '🔴 ขาย'} "
                                f"${abs(r['diff_val']):,.2f} "
                                f"({abs(r['diff_sh']):.2f} หุ้น)")
                            c0, c1, c2, c3, c4, c5 = st.columns(
                                [1, 1.1, 1.1, 1.1, 1.5, 2.2])
                            c0.markdown(f"**{r['tk']}**")
                            c1.markdown(f"{r['curr_pct']:.2f}%")
                            c2.markdown(
                                f"{r['tgt_pct']:.1f}% "
                                f"<small style='color:#888'>*(XL)*</small>",
                                unsafe_allow_html=True)
                            dev_color = "positive" if r["dev"] >= 0 else "negative"
                            c3.markdown(
                                f'<span class="{dev_color}">'
                                f'{r["dev"]:+.2f}%</span>',
                                unsafe_allow_html=True)
                            c4.caption(action_lbl)
                            if r["alerted"]:
                                c5.markdown(
                                    f'<div class="rebal-alert">'
                                    f'🔔 เกิน ±{threshold}%</div>',
                                    unsafe_allow_html=True)
                            else:
                                c5.markdown(
                                    '<div class="rebal-ok">✅ ในเกณฑ์</div>',
                                    unsafe_allow_html=True)

                        st.markdown("---")
                        if has_alert:
                            st.error(
                                f"🔔 มีหุ้นที่ Deviation เกิน ±{threshold}% "
                                f"— ควร Rebalance!")
                        else:
                            st.success(
                                f"✅ พอร์ตสมดุล — ไม่มี Deviation เกิน ±{threshold}%")

                        # ── Deviation Bar Chart ──────────────────────────
                        devs   = [r["dev"] for r in rebal_rows]
                        tks_rb = [r["tk"]  for r in rebal_rows]
                        bar_colors = [
                            "#ef5350" if abs(d) > threshold else "#26a69a"
                            for d in devs]
                        fig_dev = go.Figure(go.Bar(
                            x=tks_rb, y=devs,
                            marker_color=bar_colors,
                            text=[f"{d:+.1f}%" for d in devs],
                            textposition="outside",
                        ))
                        fig_dev.add_hline(
                            y=threshold,  line_dash="dash",
                            line_color="#ff9800",
                            annotation_text=f"+{threshold}%",
                            annotation_position="top right")
                        fig_dev.add_hline(
                            y=-threshold, line_dash="dash",
                            line_color="#ff9800",
                            annotation_text=f"-{threshold}%",
                            annotation_position="bottom right")
                        fig_dev.add_hline(y=0, line_color="#555")
                        fig_dev.update_layout(
                            title="Deviation from Target Allocation (%)",
                            template="plotly_dark", height=360,
                            yaxis_title="Deviation (%)",
                            paper_bgcolor="#0e1117",
                            plot_bgcolor="#0e1117",
                        )
                        fig_dev.update_xaxes(gridcolor="#2a2a3e")
                        fig_dev.update_yaxes(gridcolor="#2a2a3e")
                        st.plotly_chart(fig_dev, use_container_width=True)

                # ────────────────────────────────────────────────────────
                # SUB-TAB D — Drawdown Analysis  [HIDDEN]
                # Re-enable: (1) uncomment "📉 Drawdown" in st.tabs() above
                #            (2) restore "with adv_t4:" line below
                # ────────────────────────────────────────────────────────
                if False:  # with adv_t4:  ← change back to enable
                    st.markdown("### 📉 Portfolio Drawdown Analysis")

                    pv = D["port_value"]

                    if pv is None or pv.empty:
                        st.error("❌ ไม่สามารถคำนวณ Drawdown ได้")
                    else:
                        running_max, dd_pct, mdd = adv_compute_drawdown(pv)

                        # ── Metrics ──────────────────────────────────
                        d1, d2, d3, d4 = st.columns(4)
                        d1.metric(
                            "📉 Max Drawdown (MDD)",
                            f"{mdd:.2f}%",
                            help="Peak-to-Trough ที่แย่ที่สุดในช่วงนี้")
                        d2.metric(
                            "💰 All-time High (Period)",
                            f"${float(running_max.max()):,.2f}")
                        d3.metric(
                            "💵 Current Value",
                            f"${float(pv.iloc[-1]):,.2f}")
                        curr_dd = float(dd_pct.iloc[-1])
                        d4.metric(
                            "📊 Current Drawdown",
                            f"{curr_dd:.2f}%",
                            delta="At Peak! 🎉" if curr_dd == 0
                                  else f"{curr_dd:.2f}% from peak",
                            delta_color="off")

                        mdd_date = dd_pct.idxmin()
                        st.caption(
                            f"📅 วัน Drawdown สูงสุด: "
                            f"**{mdd_date.strftime('%d %b %Y')}**")

                        st.markdown("---")

                        # ── Combined Chart ──────────────────────────
                        fig_dd = make_subplots(
                            rows=2, cols=1, shared_xaxes=True,
                            vertical_spacing=0.06,
                            row_heights=[0.52, 0.48],
                            subplot_titles=(
                                "Portfolio Value & Running Maximum",
                                "Drawdown (%)"),
                        )

                        # Portfolio value
                        fig_dd.add_trace(go.Scatter(
                            x=pv.index, y=pv.values,
                            name="Portfolio Value", mode="lines",
                            line=dict(color="#7c3aed", width=2),
                        ), row=1, col=1)

                        # Running max
                        fig_dd.add_trace(go.Scatter(
                            x=running_max.index, y=running_max.values,
                            name="Running Max", mode="lines",
                            line=dict(color="#26a69a", width=1.5, dash="dot"),
                        ), row=1, col=1)

                        # Drawdown filled area
                        fig_dd.add_trace(go.Scatter(
                            x=dd_pct.index, y=dd_pct.values,
                            name="Drawdown (%)", mode="lines",
                            fill="tozeroy",
                            line=dict(color="#ef5350", width=1.5),
                            fillcolor="rgba(239,83,80,0.3)",
                        ), row=2, col=1)

                        # MDD reference line
                        fig_dd.add_hline(
                            y=mdd,
                            line_dash="dash", line_color="#ff9800",
                            annotation_text=f"MDD: {mdd:.2f}%",
                            annotation_position="bottom right",
                            row=2, col=1)

                        fig_dd.update_layout(
                            template="plotly_dark", height=580,
                            paper_bgcolor="#0e1117",
                            plot_bgcolor="#0e1117",
                            hovermode="x unified",
                            legend=dict(
                                orientation="h", y=1.02, x=0),
                        )
                        fig_dd.update_yaxes(
                            gridcolor="#2a2a3e",
                            title_text="Portfolio Value ($)", row=1, col=1)
                        fig_dd.update_yaxes(
                            gridcolor="#2a2a3e",
                            title_text="Drawdown (%)", row=2, col=1)
                        fig_dd.update_xaxes(gridcolor="#2a2a3e")
                        st.plotly_chart(fig_dd, use_container_width=True)

                        # ── Return Distribution ───────────────────────
                        st.markdown("---")
                        st.markdown("#### 📊 Daily Return Distribution")

                        daily_ret = pv.pct_change().dropna() * 100
                        mean_r    = float(daily_ret.mean())
                        std_r     = float(daily_ret.std())
                        var95     = float(daily_ret.quantile(0.05))
                        skew_r    = float(daily_ret.skew())

                        s1, s2, s3, s4 = st.columns(4)
                        s1.metric("Mean Daily Return",  f"{mean_r:.3f}%")
                        s2.metric("Std Dev (Volatility)", f"{std_r:.3f}%")
                        s3.metric("VaR 95% (1-day)",     f"{var95:.3f}%",
                                  help="5% ของวันที่แย่ที่สุด ขาดทุนมากกว่าค่านี้")
                        s4.metric("Skewness",            f"{skew_r:.3f}",
                                  help="+ve = หางขวายาว (กำไรสูง) | -ve = หางซ้ายยาว (ขาดทุนหนัก)")

                        fig_hist = go.Figure(go.Histogram(
                            x=daily_ret.values,
                            nbinsx=50,
                            marker_color="#7c3aed",
                            opacity=0.75,
                            name="Daily Returns",
                        ))
                        fig_hist.add_vline(
                            x=mean_r, line_dash="dash",
                            line_color="#26a69a",
                            annotation_text=f"Mean {mean_r:.2f}%",
                            annotation_position="top right")
                        fig_hist.add_vline(
                            x=var95, line_dash="dash",
                            line_color="#ef5350",
                            annotation_text=f"VaR95% {var95:.2f}%",
                            annotation_position="top left")
                        fig_hist.update_layout(
                            title="Distribution of Daily Returns",
                            template="plotly_dark", height=320,
                            xaxis_title="Daily Return (%)",
                            yaxis_title="Frequency",
                            paper_bgcolor="#0e1117",
                            plot_bgcolor="#0e1117",
                        )
                        fig_hist.update_xaxes(gridcolor="#2a2a3e")
                        fig_hist.update_yaxes(gridcolor="#2a2a3e")
                        st.plotly_chart(fig_hist, use_container_width=True)


# ─── Entry Point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()
