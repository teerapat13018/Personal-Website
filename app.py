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


def _corr_cluster_order(corr_df: pd.DataFrame) -> list:
    """
    Return ticker order sorted by hierarchical clustering (average linkage).
    Stocks that move together end up adjacent in the matrix.
    Falls back to original order if scipy unavailable or < 3 assets.
    """
    tickers = corr_df.columns.tolist()
    if len(tickers) < 3:
        return tickers
    try:
        from scipy.cluster.hierarchy import linkage, leaves_list
        from scipy.spatial.distance import squareform
        # Convert correlation → distance (0 = identical, 2 = opposite)
        dist = 1 - corr_df.values
        # Clip rounding errors to valid distance range
        dist = dist.clip(0, 2)
        # squareform expects condensed distance matrix (upper triangle)
        condensed = squareform(dist, checks=False)
        Z = linkage(condensed, method="average")
        order = leaves_list(Z)
        return [tickers[i] for i in order]
    except Exception:
        return tickers


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

    tab_exec, tab_input, tab_chart, tab_adv, tab_val, tab_timeline, tab_earnings = st.tabs([
        "🏠  ภาพรวม",
        "✏️  พอร์ตของฉัน",
        "📊  Chart & Analysis",
        "🚀  Advanced",
        "💎  Valuation",
        "📖  Company Timeline",
        "📞  Earnings Call",
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

                    _all_tickers = list(df_px.columns)

                    # ── Toggle: เลือก/ซ่อนหุ้นแต่ละตัว ─────────────────
                    _corr_sel_key = "corr_selected_tickers"
                    if _corr_sel_key not in st.session_state:
                        st.session_state[_corr_sel_key] = set(_all_tickers)

                    # ── ปุ่ม Select All / Deselect All ───────────────────
                    _cb1, _cb2, _cb3 = st.columns([1, 1, 6])
                    with _cb1:
                        if st.button("✅ ทั้งหมด", key="corr_sel_all",
                                     use_container_width=True):
                            st.session_state[_corr_sel_key] = set(_all_tickers)
                            st.rerun()
                    with _cb2:
                        if st.button("⬜ ล้าง", key="corr_desel_all",
                                     use_container_width=True):
                            st.session_state[_corr_sel_key] = set()
                            st.rerun()

                    # ── Checkbox grid (8 per row) ────────────────────────
                    _n_cols = min(len(_all_tickers), 8)
                    _tick_cols = st.columns(_n_cols)
                    for _ti, _tk in enumerate(_all_tickers):
                        with _tick_cols[_ti % _n_cols]:
                            _checked = _tk in st.session_state[_corr_sel_key]
                            if st.checkbox(_tk, value=_checked,
                                           key=f"corr_cb_{_tk}"):
                                st.session_state[_corr_sel_key].add(_tk)
                            else:
                                st.session_state[_corr_sel_key].discard(_tk)

                    # ── กรอง df_px ตาม selection ─────────────────────────
                    _sel_tickers = [t for t in _all_tickers
                                    if t in st.session_state[_corr_sel_key]]
                    _df_px_filtered = df_px[_sel_tickers] if _sel_tickers else df_px[[]]

                    corr_df = adv_compute_correlation(_df_px_filtered)

                    if corr_df is None:
                        st.info(
                            "เลือกหุ้นอย่างน้อย **2 ตัว** เพื่อแสดง Correlation Matrix")
                    else:
                        # ── Reorder by hierarchical clustering ───────────
                        _ordered = _corr_cluster_order(corr_df)
                        corr_df  = corr_df.loc[_ordered, _ordered]

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
                            title=f"Correlation Matrix — เรียงตาม Cluster ({n_assets} หุ้น)",
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

    # ════════════════════════════════════════════════════════════════════
    # TAB VAL — 💎 Valuation (DCF / FCFF Wizard)
    # ════════════════════════════════════════════════════════════════════
    with tab_val:
        _render_valuation_tab()

    with tab_timeline:
        _render_timeline_tab()

    with tab_earnings:
        _render_earnings_tab()


# ─────────────────────────────────────────────────────────────────────────────
# VALUATION TAB — helper (called inside main())
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def _cached_fetch_yf(ticker: str) -> dict:
    """Cache Yahoo Finance fetch result for 1 hour to avoid rate-limits."""
    from dcf_engine import fetch_yf_financials
    return fetch_yf_financials(ticker)


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_fetch_multiples(ticker: str) -> dict:
    """Cache peer multiples fetch for 1 hour to avoid rate-limits."""
    from dcf_engine import fetch_multiples
    return fetch_multiples(ticker)


def _val_inject_css():
    """Inject Theme-C CSS — Dark Gradient / Gamified / Mobile-friendly."""
    st.markdown("""
<style>
/* ── Theme C: Dark Gradient + Glow ─────────────────────────────────────── */

/* Page background */
[data-testid="stAppViewContainer"] > .main {
    background: linear-gradient(160deg, #0d0d1a 0%, #12122a 50%, #0d1b2a 100%);
    min-height: 100vh;
}
[data-testid="stSidebar"] {
    background: #0a0a18 !important;
}

/* ── Wizard step progress bar ───────────────────────────────────────────── */
.val-progress {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0;
    margin: 0 auto 24px auto;
    max-width: 560px;
    padding: 0 8px;
}
.val-step-wrap { display:flex; flex-direction:column; align-items:center; gap:6px; }
.val-step-circle {
    width: 40px; height: 40px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 15px;
    transition: all .3s ease;
}
.val-step-circle.done {
    background: linear-gradient(135deg,#00b4d8,#0077b6);
    color: #fff;
    box-shadow: 0 0 14px rgba(0,180,216,.55);
}
.val-step-circle.active {
    background: linear-gradient(135deg,#e94560,#c2185b);
    color: #fff;
    box-shadow: 0 0 18px rgba(233,69,96,.65);
    animation: pulse-ring 2s ease-in-out infinite;
}
.val-step-circle.todo {
    background: #1e1e3a;
    color: #555;
    border: 1.5px solid #333;
}
.val-step-label {
    font-size: 11px;
    color: #888;
    text-align: center;
    line-height: 1.3;
    max-width: 80px;
}
.val-step-label.active { color: #e94560; font-weight: 600; }
.val-step-label.done   { color: #00b4d8; }
.val-connector {
    flex: 1;
    height: 2px;
    margin-bottom: 18px;
    max-width: 80px;
}
.val-connector.done   { background: linear-gradient(90deg,#00b4d8,#0077b6); }
.val-connector.pending { background: #1e1e3a; }

@keyframes pulse-ring {
    0%,100% { box-shadow: 0 0 18px rgba(233,69,96,.65); }
    50%      { box-shadow: 0 0 28px rgba(233,69,96,.9); }
}

/* ── Hero metric cards ──────────────────────────────────────────────────── */
.val-hero-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin: 16px 0 24px 0;
}
.val-hero-card {
    background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
    border-radius: 14px;
    padding: 18px 14px 14px 14px;
    position: relative;
    overflow: hidden;
    transition: transform .2s ease, box-shadow .2s ease;
}
.val-hero-card::before {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: 14px;
    padding: 1.5px;
    background: var(--card-accent, linear-gradient(135deg,#e94560,#7b2fff));
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
}
.val-hero-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(0,0,0,.5);
}
.val-hero-card .hc-icon  { font-size: 18px; margin-bottom: 4px; }
.val-hero-card .hc-label { font-size: 11px; color: #888; letter-spacing:.4px; text-transform:uppercase; }
.val-hero-card .hc-value { font-size: 26px; font-weight: 800; color: #eaeaea; margin: 4px 0 2px 0; line-height:1.1; }
.val-hero-card .hc-sub   { font-size: 11px; color: #666; }
.val-hero-card .hc-glow  { position:absolute; width:80px; height:80px; border-radius:50%; opacity:.12; right:-10px; top:-10px; }
.card-intrinsic { --card-accent: linear-gradient(135deg,#e94560,#c2185b); }
.card-intrinsic .hc-value { color: #ff6b8a; }
.card-intrinsic .hc-glow  { background: #e94560; }
.card-mos    { --card-accent: linear-gradient(135deg,#7b2fff,#5c13c5); }
.card-mos    .hc-value { color: #b57bff; }
.card-mos    .hc-glow  { background: #7b2fff; }
.card-ev     { --card-accent: linear-gradient(135deg,#00b4d8,#0077b6); }
.card-ev     .hc-value { color: #5bc8e8; }
.card-ev     .hc-glow  { background: #00b4d8; }
.card-equity { --card-accent: linear-gradient(135deg,#00e676,#00897b); }
.card-equity .hc-value { color: #66ffa6; }
.card-equity .hc-glow  { background: #00e676; }

/* ── Signal badge ───────────────────────────────────────────────────────── */
.val-signal-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 18px;
    border-radius: 99px;
    font-weight: 700;
    font-size: 14px;
    letter-spacing: .3px;
    margin-bottom: 4px;
}
.badge-undervalued { background:rgba(0,230,118,.15); color:#00e676; border:1px solid rgba(0,230,118,.4); }
.badge-fairly      { background:rgba(255,171,0,.15);  color:#ffab00; border:1px solid rgba(255,171,0,.4); }
.badge-overvalued  { background:rgba(233,69,96,.15);  color:#e94560; border:1px solid rgba(233,69,96,.4); }

/* ── Reverse DCF cards ──────────────────────────────────────────────────── */
.rdcf-card {
    background: linear-gradient(145deg, #1a1a2e, #0f1729);
    border-radius: 14px;
    padding: 20px;
    position: relative;
    overflow: hidden;
}
.rdcf-card .rdcf-big { font-size: 36px; font-weight: 800; margin: 8px 0 4px 0; }

/* ── Pill button overrides ──────────────────────────────────────────────── */
div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #e94560 0%, #7b2fff 100%) !important;
    border: none !important;
    border-radius: 99px !important;
    font-weight: 700 !important;
    letter-spacing: .4px !important;
    box-shadow: 0 4px 18px rgba(233,69,96,.35) !important;
    transition: opacity .2s !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
    opacity: .88 !important;
}
div[data-testid="stButton"] > button[kind="secondary"],
div[data-testid="stButton"] > button:not([kind]) {
    border-radius: 99px !important;
    border-color: #333 !important;
    background: #1a1a2e !important;
    color: #ccc !important;
}

/* ── Section headers ────────────────────────────────────────────────────── */
.val-section-head {
    font-size: 15px;
    font-weight: 700;
    color: #a8a8d8;
    text-transform: uppercase;
    letter-spacing: .8px;
    margin: 20px 0 10px 0;
    display: flex;
    align-items: center;
    gap: 8px;
}
.val-section-head::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg,#2a2a4a,transparent);
    margin-left: 8px;
}

/* ── Mobile responsive ──────────────────────────────────────────────────── */
@media (max-width: 768px) {
    .val-hero-grid {
        grid-template-columns: repeat(2, 1fr) !important;
        gap: 10px !important;
    }
    .val-hero-card .hc-value { font-size: 20px !important; }
    .val-progress { max-width: 100%; }
    .val-connector { max-width: 40px; }
    .val-step-label { font-size: 10px; max-width: 62px; }
}
@media (max-width: 480px) {
    .val-hero-grid { grid-template-columns: 1fr 1fr !important; }
    .val-hero-card { padding: 12px 10px !important; }
    .val-hero-card .hc-value { font-size: 18px !important; }
}
</style>
""", unsafe_allow_html=True)


def _fetch_sec_guidance(ticker: str, company_name: str = "") -> str:
    """Fetch most recent 10-Q/10-K from SEC EDGAR → extract management guidance.
    Returns text snippet or "" on any failure (fail silently).
    """
    import urllib.request, json, re

    _HEADERS = {"User-Agent": "InvestmentDashboard teerapat.13018@gmail.com",
                "Accept": "application/json"}

    def _get(url: str, max_bytes: int = 1_000_000) -> str:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=12) as r:
            raw = r.read(max_bytes)
            enc = r.headers.get_content_charset("utf-8")
            return raw.decode(enc, errors="ignore")

    try:
        # ── Step 1: Ticker → CIK ─────────────────────────────────────────────
        tickers_json = json.loads(_get(
            "https://www.sec.gov/files/company_tickers.json",
            max_bytes=3_000_000,
        ))
        entry = next(
            (v for v in tickers_json.values()
             if v.get("ticker", "").upper() == ticker.upper()),
            None,
        )
        if not entry:
            return ""
        cik_int = int(entry["cik_str"])
        cik_pad = str(cik_int).zfill(10)

        # ── Step 2: Get recent filings list ──────────────────────────────────
        subs = json.loads(_get(f"https://data.sec.gov/submissions/CIK{cik_pad}.json"))
        recent = subs.get("filings", {}).get("recent", {})
        forms      = recent.get("form", [])
        accessions = recent.get("accessionNumber", [])
        dates      = recent.get("filingDate", [])

        # Find most recent 10-Q, fallback 10-K
        idx = next((i for i, f in enumerate(forms) if f == "10-Q"), None)
        if idx is None:
            idx = next((i for i, f in enumerate(forms) if f == "10-K"), None)
        if idx is None:
            return ""

        acc_dashes   = accessions[idx]               # "0001045810-24-000042"
        acc_nodashes = acc_dashes.replace("-", "")   # "000104581024000042"
        form_type    = forms[idx]
        filed_date   = dates[idx]

        # ── Step 3: Filing index → find main .htm document ───────────────────
        index_url = (
            f"https://www.sec.gov/Archives/edgar/data/"
            f"{cik_int}/{acc_nodashes}/{acc_dashes}-index.json"
        )
        index_data = json.loads(_get(index_url))
        doc_name = None
        for doc in index_data.get("documents", []):
            dtype = doc.get("type", "")
            dname = doc.get("document", "")
            if dtype in (form_type, "10-K", "10-Q") and dname.lower().endswith(".htm"):
                doc_name = dname
                break
        if not doc_name:
            for doc in index_data.get("documents", []):
                if doc.get("document", "").lower().endswith(".htm"):
                    doc_name = doc["document"]
                    break
        if not doc_name:
            return ""

        # ── Step 4: Fetch document (limit 800KB) ─────────────────────────────
        doc_url = (
            f"https://www.sec.gov/Archives/edgar/data/"
            f"{cik_int}/{acc_nodashes}/{doc_name}"
        )
        html = _get(doc_url, max_bytes=800_000)

        # Strip HTML → plain text
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"&[a-zA-Z]+;|&#[0-9]+;", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        # ── Step 5: Extract guidance / outlook snippets ───────────────────────
        _KW = [
            "our outlook", "we expect", "management expects",
            "revenue guidance", "guidance", "full year",
            "next quarter", "fiscal year", "we anticipate",
            "forward-looking", "outlook",
        ]
        seen, snippets = set(), []
        tl = text.lower()
        for kw in _KW:
            pos = 0
            while len(snippets) < 8:
                idx2 = tl.find(kw, pos)
                if idx2 == -1:
                    break
                start = max(0, idx2 - 80)
                end   = min(len(text), idx2 + 450)
                chunk = text[start:end].strip()
                key   = chunk[:60]
                if len(chunk) > 60 and key not in seen:
                    seen.add(key)
                    snippets.append(chunk)
                pos = idx2 + len(kw)

        if not snippets:
            return ""

        header = f"[SEC {form_type} filed {filed_date} — {company_name or ticker}]"
        body   = "\n\n".join(snippets[:6])
        return f"{header}\n{body}"

    except Exception:
        return ""


def _ai_suggest_dcf(saved: dict, groq_key: str) -> tuple[dict, str]:
    """ให้ Groq วิเคราะห์และแนะนำค่า DCF parameters ทั้งชุด
    Returns (params_dict, reasoning_text) หรือ ({}, error_msg)
    """
    import json as _json

    ticker  = saved.get("ticker", "")
    company = saved.get("company_name", ticker)

    # ── Fresh yfinance fetch — ดึง real-time data ──────────────────────────
    ctx_lines = [f"Company: {company} ({ticker})"]
    try:
        import yfinance as _yf
        tk   = _yf.Ticker(ticker)
        info = tk.info or {}

        sector   = info.get("sector", saved.get("sector", ""))
        industry = info.get("industry", "")
        if sector:   ctx_lines.append(f"Sector: {sector}")
        if industry: ctx_lines.append(f"Industry: {industry}")

        # ── Price & Market Cap ──────────────────────────────────────────────
        price = info.get("currentPrice") or info.get("regularMarketPrice") or 0
        mktcap = info.get("marketCap", 0)
        if price:  ctx_lines.append(f"Current Price: ${float(price):,.2f}")
        if mktcap: ctx_lines.append(f"Market Cap: ${float(mktcap)/1e9:,.1f}B")

        # ── Revenue (TTM + growth) ──────────────────────────────────────────
        revenue = info.get("totalRevenue", 0)
        if revenue: ctx_lines.append(f"Revenue TTM: ${float(revenue)/1e9:,.2f}B")
        rev_growth = info.get("revenueGrowth")
        if rev_growth is not None:
            ctx_lines.append(f"Revenue Growth (YoY TTM): {float(rev_growth):.1%}")

        # ── Revenue history — คำนวณ CAGR 3 ปี ─────────────────────────────
        try:
            fin = tk.financials
            if fin is not None and not fin.empty:
                rev_rows = [r for r in fin.index if "total revenue" in r.lower() or "revenue" == r.lower()]
                if rev_rows:
                    rev_hist = fin.loc[rev_rows[0]].dropna().astype(float).sort_index()
                    if len(rev_hist) >= 2:
                        rev_vals = rev_hist.values
                        years = len(rev_vals) - 1
                        cagr = (rev_vals[0] / rev_vals[-1]) ** (1/years) - 1
                        ctx_lines.append(f"Revenue CAGR {years}yr: {cagr:.1%}")
                        for i, (dt, v) in enumerate(rev_hist.items()):
                            ctx_lines.append(f"  Revenue {str(dt)[:4]}: ${v/1e9:,.2f}B")
        except Exception:
            pass

        # ── Margins ────────────────────────────────────────────────────────
        op_margin    = info.get("operatingMargins")
        gross_margin = info.get("grossMargins")
        profit_margin = info.get("profitMargins")
        if op_margin    is not None: ctx_lines.append(f"Operating Margin (TTM): {float(op_margin):.1%}")
        if gross_margin is not None: ctx_lines.append(f"Gross Margin (TTM): {float(gross_margin):.1%}")
        if profit_margin is not None: ctx_lines.append(f"Net Profit Margin (TTM): {float(profit_margin):.1%}")

        # ── Profitability ──────────────────────────────────────────────────
        roe  = info.get("returnOnEquity")
        roa  = info.get("returnOnAssets")
        if roe is not None: ctx_lines.append(f"Return on Equity (TTM): {float(roe):.1%}")
        if roa is not None: ctx_lines.append(f"Return on Assets (TTM): {float(roa):.1%}")

        # ── ROIC proxy ─────────────────────────────────────────────────────
        total_debt = float(info.get("totalDebt", 0) or 0)
        cash_val   = float(info.get("totalCash", 0) or info.get("cashAndCashEquivalents", 0) or 0)
        equity_val = float(info.get("totalStockholderEquity", 0) or 0)
        net_income = float(info.get("netIncomeToCommon", 0) or 0)
        invested_cap = equity_val + total_debt - cash_val
        if invested_cap > 0 and net_income:
            roic = net_income / invested_cap
            ctx_lines.append(f"Approx. ROIC: {roic:.1%}")
        if total_debt: ctx_lines.append(f"Total Debt: ${total_debt/1e9:,.2f}B")
        if cash_val:   ctx_lines.append(f"Cash: ${cash_val/1e9:,.2f}B")

        # ── Sales-to-Capital ───────────────────────────────────────────────
        if revenue and invested_cap > 0:
            s2c = float(revenue) / invested_cap
            ctx_lines.append(f"Sales-to-Capital (current): {s2c:.2f}x")

        # ── FCF ────────────────────────────────────────────────────────────
        fcf = info.get("freeCashflow")
        if fcf: ctx_lines.append(f"Free Cash Flow (TTM): ${float(fcf)/1e9:,.2f}B")

        # ── Beta & Risk ────────────────────────────────────────────────────
        beta = info.get("beta")
        if beta: ctx_lines.append(f"Beta (5yr monthly): {float(beta):.2f}")

        # ── Analyst estimates ──────────────────────────────────────────────
        eps_growth = info.get("earningsGrowth") or info.get("earningsQuarterlyGrowth")
        fwd_eps    = info.get("forwardEps")
        fwd_pe     = info.get("forwardPE")
        analyst_tgt = info.get("targetMeanPrice")
        if eps_growth:   ctx_lines.append(f"Earnings Growth (YoY): {float(eps_growth):.1%}")
        if fwd_eps:      ctx_lines.append(f"Forward EPS (analyst est): ${float(fwd_eps):.2f}")
        if fwd_pe:       ctx_lines.append(f"Forward P/E: {float(fwd_pe):.1f}x")
        if analyst_tgt:  ctx_lines.append(f"Analyst Mean Price Target: ${float(analyst_tgt):,.2f}")

        # ── Payout / Buyback ───────────────────────────────────────────────
        payout = info.get("payoutRatio")
        if payout: ctx_lines.append(f"Payout Ratio: {float(payout):.1%}")

    except Exception as _e:
        # yfinance ไม่ได้ → fallback to saved
        ctx_lines.append("(yfinance unavailable — using cached data)")
        revenue       = saved.get("revenue_base", 0)
        ebit_margin   = saved.get("ebit_margin_base", 0)
        price         = saved.get("current_price", 0)
        if revenue:     ctx_lines.append(f"Revenue: ${revenue:,.0f}M")
        if ebit_margin: ctx_lines.append(f"EBIT Margin: {ebit_margin:.1%}")
        if price:       ctx_lines.append(f"Price: ${price:,.2f}")

    context = "\n".join(ctx_lines)

    # ── Tavily: ดึงข่าวล่าสุด real-time ───────────────────────────────────
    news_context = ""
    try:
        from tavily import TavilyClient as _Tavily
        _tv_key = saved.get("_tavily_key", "")
        if _tv_key:
            _tv = _Tavily(api_key=_tv_key)
            _queries = [
                f"{ticker} {company} revenue outlook 2025 2026",
                f"{ticker} {company} risk factors earnings guidance",
            ]
            _snippets = []
            for _q in _queries:
                try:
                    _res = _tv.search(query=_q, max_results=3,
                                      search_depth="basic",
                                      include_answer=True)
                    if _res.get("answer"):
                        _snippets.append(_res["answer"])
                    for _r in (_res.get("results") or [])[:2]:
                        _content = _r.get("content", "").strip()
                        if _content:
                            _snippets.append(f"[{_r.get('title','')}] {_content[:300]}")
                except Exception:
                    pass
            if _snippets:
                news_context = "\n".join(f"- {s}" for s in _snippets[:8])
    except Exception:
        pass

    news_section = f"\nRECENT NEWS & ANALYST CONTEXT (real-time):\n{news_context}" if news_context else ""

    # ── SEC EDGAR: ดึง management guidance จาก 10-Q/10-K ล่าสุด ─────────────
    sec_text    = _fetch_sec_guidance(ticker, company)
    sec_section = f"\nSEC FILING — OFFICIAL MANAGEMENT GUIDANCE:\n{sec_text}" if sec_text else ""

    prompt = f"""You are a senior equity analyst specializing in DCF valuation. Analyze ALL data sources below — live financials, recent news, AND official SEC guidance — to recommend specific, well-reasoned DCF assumptions.

COMPANY DATA:
{context}{news_section}{sec_section}

Return ONLY valid JSON (no markdown, no explanation outside JSON) with this exact schema:
{{
  "revenue_growth_yr1":   <float 0–1>,
  "revenue_growth_final": <float 0–0.10>,
  "growth_years":         <int 5–15>,
  "ebit_margin_target":   <float 0–0.80>,
  "sales_to_capital":     <float 0.5–8.0>,
  "wacc":                 <float 0.06–0.18>,
  "terminal_growth":      <float 0.01–0.05>,
  "terminal_roic":        <float 0.08–0.50>,
  "margin_of_safety":     <float 0.10–0.50>,
  "narrative": "<Thai: 3-4 sentences telling the investment story — where the company is now, key growth drivers, key risks, and overall DCF stance (optimistic/neutral/conservative). Cite real numbers from the data.>",
  "reasoning": {{
    "revenue_growth_yr1":   "<Thai: cite actual numbers, e.g. historical growth X%, analyst consensus Y%, justify mean-reversion>",
    "revenue_growth_final": "<Thai: cite sector long-term GDP or industry growth rate>",
    "growth_years":         "<Thai: cite sector visibility, competitive moat duration>",
    "ebit_margin_target":   "<Thai: cite current margin X%, peer comparison, trajectory>",
    "sales_to_capital":     "<Thai: cite current ratio X, asset-light vs capital-heavy business model>",
    "wacc":                 "<Thai: cite beta X, risk-free rate ~4.3%, equity risk premium, sector risk>",
    "terminal_growth":      "<Thai: cite US/global GDP assumption, must stay below WACC>",
    "terminal_roic":        "<Thai: cite current ROIC X%, moat strength, long-term competitive advantage>",
    "margin_of_safety":     "<Thai: cite stock volatility beta, business predictability, cycle risk>"
  }}
}}

STRICT RULES:
- terminal_growth MUST be less than wacc
- Every reasoning field MUST cite specific numbers from the data provided (%, ratios, dollar amounts)
- narrative MUST mention key growth drivers AND risks with actual numbers
- Apply mean-reversion: if historical growth >60%, yr1 should be meaningfully lower than historical
- For fabless semiconductor companies: sales_to_capital should be 3–6x (asset-light model)
- Respond in JSON only, no text outside the JSON object"""

    try:
        from groq import Groq as _Groq
        client = _Groq(api_key=groq_key)
        resp = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1800,
            temperature=0.2,
        )
        raw = resp.choices[0].message.content.strip()
        # strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"): raw = raw[4:]
        data      = _json.loads(raw)
        narrative = data.pop("narrative", "")
        reasoning = data.pop("reasoning", {})
        _label_map = {
            "revenue_growth_yr1":   "📈 Revenue Growth ปีที่ 1",
            "revenue_growth_final": "📉 Revenue Growth ปีสุดท้าย",
            "growth_years":         "📅 จำนวนปีที่คาดการณ์",
            "ebit_margin_target":   "💰 EBIT Margin เป้าหมาย",
            "sales_to_capital":     "🏭 Sales-to-Capital",
            "wacc":                 "💸 WACC",
            "terminal_growth":      "🏁 Terminal Growth Rate",
            "terminal_roic":        "📊 Terminal ROIC",
            "margin_of_safety":     "🛡️ Margin of Safety",
        }
        val_map = {k: v for k, v in data.items()}
        reasoning_parts = []
        for k, label in _label_map.items():
            val = val_map.get(k, "")
            if k == "growth_years":
                val_str = f"{int(val)} ปี" if val else ""
            elif k == "sales_to_capital":
                val_str = f"{float(val):.2f}x" if val else ""
            else:
                val_str = f"{float(val)*100:.1f}%" if val else ""
            reason = reasoning.get(k, "")
            reasoning_parts.append(f"**{label}** → `{val_str}`  \n{reason}")

        # narrative เป็น header ก่อน ตามด้วย separator แล้วรายละเอียด
        narrative_block = f"### 📝 สรุปภาพรวมบริษัท\n{narrative}\n\n---\n### 🔢 รายละเอียดแต่ละพารามิเตอร์\n" if narrative else ""
        reasoning_text  = narrative_block + "\n\n".join(reasoning_parts)
        return data, reasoning_text
    except Exception as e:
        return {}, f"❌ AI Suggest ล้มเหลว: {e}"


def _render_valuation_tab():
    """Render the 💎 Valuation tab — 3-step DCF Wizard"""
    from dcf_engine import DCFInputs, DCFOutputs, run_dcf, run_scenarios, sensitivity_table, reverse_dcf, reverse_dcf_single_stage, fetch_multiples, implied_value_from_multiples
    from db_gsheets import (
        val_save, val_load, val_load_one, val_update, val_delete,
        scenario_save, scenario_load, scenario_delete, scenario_delete_all,
    )

    st.markdown("## 💎 DCF Valuation")
    st.caption("ประเมินมูลค่าหุ้นด้วย Free Cash Flow to Firm (FCFF) — Damodaran model")

    # ── Session state init ────────────────────────────────────────────────────
    if "val_step"      not in st.session_state: st.session_state["val_step"]      = 1
    if "val_inputs"    not in st.session_state: st.session_state["val_inputs"]    = {}
    if "val_result"    not in st.session_state: st.session_state["val_result"]    = None
    if "val_edit_id"   not in st.session_state: st.session_state["val_edit_id"]   = None
    if "val_view_mode" not in st.session_state: st.session_state["val_view_mode"] = "wizard"

    # ── Top-level view toggle ─────────────────────────────────────────────────
    col_mode1, col_mode2, _ = st.columns([1, 1, 4])
    if col_mode1.button("➕ Valuation ใหม่", use_container_width=True,
                        type="primary" if st.session_state["val_view_mode"] == "wizard" else "secondary"):
        st.session_state["val_view_mode"] = "wizard"
        st.session_state["val_step"]      = 1
        st.session_state["val_edit_id"]   = None
        st.rerun()
    if col_mode2.button("📋 รายการที่บันทึก", use_container_width=True,
                        type="primary" if st.session_state["val_view_mode"] == "list" else "secondary"):
        st.session_state["val_view_mode"] = "list"
        st.rerun()

    st.divider()

    # ════════════════════════════════════════════════════════════════════
    # VIEW: รายการ Valuations ที่บันทึก
    # ════════════════════════════════════════════════════════════════════
    if st.session_state["val_view_mode"] == "list":
        _val_list_view()
        return

    # ════════════════════════════════════════════════════════════════════
    # VIEW: Wizard (3 ขั้นตอน)
    # ════════════════════════════════════════════════════════════════════
    _val_wizard()


# ─────────────────────────────────────────────────────────────────────────────
# WIZARD — 3 steps
# ─────────────────────────────────────────────────────────────────────────────

def _val_wizard():
    from dcf_engine import DCFInputs, DCFOutputs, run_dcf, run_scenarios, sensitivity_table, reverse_dcf, reverse_dcf_single_stage, fetch_multiples, implied_value_from_multiples

    # ── Inject Theme-C CSS ────────────────────────────────────────────────────
    _val_inject_css()

    step = st.session_state["val_step"]

    # ── Step progress bar (Theme C) ───────────────────────────────────────────
    def _step_state(s):
        if s < step:  return "done"
        if s == step: return "active"
        return "todo"

    step_info = [
        (1, "บริษัท &<br>ตัวเลขพื้นฐาน"),
        (2, "สมมติฐาน &<br>ต้นทุนทุน"),
        (3, "ผลการ<br>ประเมิน"),
    ]
    circles = ""
    for idx, (s, lbl) in enumerate(step_info):
        state = _step_state(s)
        icon  = "✓" if state == "done" else str(s)
        circles += f"""
        <div class="val-step-wrap">
            <div class="val-step-circle {state}">{icon}</div>
            <div class="val-step-label {state}">{lbl}</div>
        </div>"""
        if idx < len(step_info) - 1:
            conn_cls = "done" if step > s else "pending"
            circles += f'<div class="val-connector {conn_cls}"></div>'

    st.markdown(f'<div class="val-progress">{circles}</div>', unsafe_allow_html=True)

    saved = st.session_state.get("val_inputs", {})

    # ════════════════════════════════════════════════════════════════════
    # STEP 1 — Company info & Base financials
    # ════════════════════════════════════════════════════════════════════
    if step == 1:
        st.markdown("### 🏢 ข้อมูลบริษัทและตัวเลขปีล่าสุด")

        # ── Yahoo Finance Auto-fill ───────────────────────────────────────────
        with st.expander("🔍 Auto-fill จาก Yahoo Finance", expanded=True):
            yf_col1, yf_col2 = st.columns([3, 1])
            yf_ticker_input  = yf_col1.text_input(
                "กรอก Ticker เพื่อดึงข้อมูลอัตโนมัติ",
                value=saved.get("ticker", ""),
                placeholder="เช่น AAPL, GOOGL, PTT.BK, 2380.SR",
                key="yf_ticker_fetch",
            )
            if yf_col2.button("⬇️ ดึงข้อมูล", use_container_width=True, key="btn_yf_fetch"):
                if yf_ticker_input.strip():
                    with st.spinner("กำลังดึงข้อมูลจาก Yahoo Finance…"):
                        yf_data = _cached_fetch_yf(yf_ticker_input.strip())
                    if "_error" in yf_data:
                        st.error(f"❌ {yf_data['_error']}")
                    else:
                        # Merge into val_inputs (only non-private keys)
                        clean = {k: v for k, v in yf_data.items() if not k.startswith("_")}
                        st.session_state["val_inputs"].update(clean)
                        hint = yf_data.get("_growth_hint")
                        if hint is not None:
                            st.session_state["val_inputs"]["revenue_growth_yr1"] = round(max(0.02, hint), 4)
                        # Auto-correct currency dropdown
                        fetched_cur = clean.get("currency", "USD")
                        if fetched_cur not in ["USD","THB","SAR","EUR","GBP","JPY","SGD","HKD"]:
                            fetched_cur = "USD"
                        st.session_state["val_inputs"]["currency"] = fetched_cur
                        st.success(
                            f"✅ ดึงข้อมูล **{clean.get('company_name','')}** สำเร็จ  "
                            f"({clean.get('currency','')}  Revenue: "
                            f"{clean.get('revenue_base', 0):,.0f}M)"
                        )
                        st.rerun()
                else:
                    st.warning("กรุณากรอก Ticker ก่อน")

        # reload saved after possible update from YF button
        saved = st.session_state.get("val_inputs", {})

        c1, c2, c3 = st.columns([2, 1, 1])
        company_name = c1.text_input("ชื่อบริษัท",   value=saved.get("company_name", ""),  placeholder="เช่น Apple Inc.")
        ticker       = c2.text_input("Ticker Symbol", value=saved.get("ticker", ""),        placeholder="เช่น AAPL")
        _cur_opts    = ["USD","THB","SAR","EUR","GBP","JPY","SGD","HKD"]
        _cur_val     = saved.get("currency","USD")
        _cur_idx     = _cur_opts.index(_cur_val) if _cur_val in _cur_opts else 0
        currency     = c3.selectbox("สกุลเงิน", _cur_opts, index=_cur_idx)

        st.markdown('<div class="val-section-head">💰 ตัวเลขปีล่าสุด (Base Year)</div>', unsafe_allow_html=True)
        st.caption("กรอกตัวเลขจาก Annual Report ปีล่าสุด  (หน่วย: ล้าน)")

        col1, col2 = st.columns(2)
        with col1:
            revenue_base     = st.number_input("Revenue (ล้าน)",    value=float(saved.get("revenue_base",      10_000.0)), min_value=0.01,   step=100.0,  format="%.2f",
                                               help="รายได้รวมปีล่าสุด")
            ebit_margin_base = st.slider("EBIT Margin ปีล่าสุด (%)", 0.0, 50.0,
                                         float(saved.get("ebit_margin_base", 0.10)) * 100, 0.5,
                                         format="%.1f%%") / 100
            tax_rate         = st.slider("Tax Rate (%)", 0.0, 40.0,
                                         float(saved.get("tax_rate", 0.20)) * 100, 0.5,
                                         format="%.1f%%") / 100
        with col2:
            net_debt          = st.number_input("Net Debt (ล้าน)",         value=float(saved.get("net_debt", 0.0)),            step=100.0, format="%.2f",
                                                help="Net Debt = หนี้สิน − เงินสด (ใส่ค่าลบถ้า net cash)")
            minority_interest = st.number_input("Minority Interest (ล้าน)", value=float(saved.get("minority_interest", 0.0)),   step=10.0,  format="%.2f")
            shares_outstanding = st.number_input("หุ้นทั้งหมด (ล้านหุ้น)",  value=float(saved.get("shares_outstanding", 100.0)), min_value=0.01, step=10.0,  format="%.2f")
            current_price     = st.number_input(
                "ราคาตลาดปัจจุบัน (ต่อหุ้น)",
                value=float(saved.get("current_price", 0.0)),
                min_value=0.0, step=0.01, format="%.4f",
                help="📍 ราคาหุ้นล่าสุด จาก Yahoo Finance หรือ Bloomberg — ใช้สำหรับ Reverse DCF (กรอก 0 เพื่อข้าม)"
            )

        st.markdown("---")
        if st.button("ถัดไป →  ขั้นตอนที่ 2", type="primary", use_container_width=True):
            if not company_name.strip():
                st.error("กรุณากรอกชื่อบริษัท")
                return
            if revenue_base <= 0:
                st.error("Revenue ต้องมากกว่า 0")
                return
            st.session_state["val_inputs"].update({
                "company_name":      company_name.strip(),
                "ticker":            ticker.strip().upper(),
                "currency":          currency,
                "revenue_base":      revenue_base,
                "ebit_margin_base":  ebit_margin_base,
                "tax_rate":          tax_rate,
                "net_debt":          net_debt,
                "minority_interest": minority_interest,
                "shares_outstanding": shares_outstanding,
                "current_price":     current_price,
            })
            st.session_state["val_step"] = 2
            st.rerun()

    # ════════════════════════════════════════════════════════════════════
    # STEP 2 — Growth assumptions & WACC
    # ════════════════════════════════════════════════════════════════════
    elif step == 2:
        st.markdown("### 📈 สมมติฐานการเติบโตและต้นทุนทุน")

        # ── AI Suggest ────────────────────────────────────────────────────────
        if "ai_dcf_reasoning" not in st.session_state:
            st.session_state["ai_dcf_reasoning"] = ""
        if "ai_dcf_error"    not in st.session_state:
            st.session_state["ai_dcf_error"]    = ""

        ai_col1, ai_col2 = st.columns([3, 1])
        ai_col1.caption("🤖 ให้ AI วิเคราะห์ข้อมูลบริษัทแล้วแนะนำค่าพารามิเตอร์ทั้งชุดพร้อมเหตุผล")
        ai_clicked = ai_col2.button("🤖 AI Suggest", type="primary", use_container_width=True)

        if ai_clicked:
            try:
                _gk = st.secrets["GROQ_API_KEY"]
                groq_key = str(_gk["GROQ_API_KEY"] if hasattr(_gk, "__getitem__") and not isinstance(_gk, str) else _gk)
            except Exception:
                groq_key = ""
            if not groq_key:
                st.session_state["ai_dcf_error"]    = "❌ ไม่พบ GROQ_API_KEY ใน Secrets"
                st.session_state["ai_dcf_reasoning"] = ""
            else:
                # แนบ Tavily key เข้า saved ชั่วคราว เพื่อให้ _ai_suggest_dcf ดึงข่าวได้
                try:
                    _tv = st.secrets["tavily_api_key"]
                    _tv_key = str(_tv["tavily_api_key"] if hasattr(_tv, "__getitem__") and not isinstance(_tv, str) else _tv)
                except Exception:
                    _tv_key = ""
                saved_with_keys = {**saved, "_tavily_key": _tv_key}
                with st.spinner("🔍 ดึงข่าว + 📋 SEC filing + 🤖 AI วิเคราะห์..."):
                    params, reasoning = _ai_suggest_dcf(saved_with_keys, groq_key)
                if not params:
                    st.session_state["ai_dcf_error"]    = reasoning  # reasoning = error msg
                    st.session_state["ai_dcf_reasoning"] = ""
                else:
                    # Apply suggested values → update val_inputs then rerun
                    st.session_state["ai_dcf_error"]    = ""
                    st.session_state["ai_dcf_reasoning"] = reasoning
                    st.session_state["val_inputs"].update({
                        k: v for k, v in params.items()
                        if k in ("revenue_growth_yr1","revenue_growth_final","growth_years",
                                 "ebit_margin_target","sales_to_capital","wacc",
                                 "terminal_growth","terminal_roic","margin_of_safety")
                    })
                    st.rerun()

        if st.session_state["ai_dcf_error"]:
            st.error(st.session_state["ai_dcf_error"])
        if st.session_state["ai_dcf_reasoning"]:
            with st.expander("📋 ดูเหตุผลจาก AI", expanded=True):
                st.success("✅ AI แนะนำค่าพารามิเตอร์และอัพเดต slider แล้ว ปรับเพิ่มเติมได้ตามต้องการ")
                st.markdown(st.session_state["ai_dcf_reasoning"])

        st.divider()

        # ── คู่มือหาค่าพารามิเตอร์ (expander) ─────────────────────────────────
        with st.expander("📚 วิธีหาค่าพารามิเตอร์แต่ละตัว", expanded=False):
            st.markdown("""
| พารามิเตอร์ | หาจากที่ไหน | ค่าอ้างอิงทั่วไป |
|---|---|---|
| **Revenue Growth ปีที่ 1** | Yahoo Finance → แท็บ **Analysis** → Revenue Estimate / หรือ Management Guidance ใน Earnings Call | ตาม Analyst consensus |
| **Revenue Growth ปีสุดท้าย** | Growth ที่คาดว่าบริษัทจะเติบโตได้ยั่งยืนระยะยาว | 3–8% แล้วแต่อุตสาหกรรม |
| **จำนวนปีที่คาดการณ์** | ตัดสินใจตามความแน่นอนของธุรกิจ | สาธารณูปโภค/อาหาร = 10, Tech/Startup = 5 |
| **EBIT Margin เป้าหมาย** | Macrotrends.net → ค้นชื่อบริษัท → *Operating Profit Margin* ย้อนหลัง 5 ปี หรือ Peer average | ตาม Historical margin |
| **Sales-to-Capital Ratio** | คำนวณเอง: `Revenue ÷ (Equity + Debt − Cash)` จาก Balance Sheet | หรือดู Industry avg จาก **Damodaran Online** |
| **WACC** | [WACC.com](https://wacc.com) คำนวณให้แล้ว / หรือใช้ CAPM: `Rf + Beta × ERP` (Beta จาก Yahoo Finance, Rf = Bond yield 10 ปี) | Developed ≈ 8–12%, Emerging ≈ 10–15% |
| **Terminal Growth Rate** | GDP growth ระยะยาวของประเทศที่บริษัทขายส่วนใหญ่ — **ห้ามเกิน WACC** | US/EU ≈ 2–3%, ไทย/ซาอุ ≈ 3–5% |
| **Terminal ROIC** | ROIC เฉลี่ย 5 ปีย้อนหลังจาก Macrotrends หรือ Wisesheets | บริษัท moat แข็ง = สูงได้, Commodity = ≈ WACC |
| **Margin of Safety** | ตัดสินใจตามความเสี่ยงที่รับได้ | มั่นคง = 20%, ปานกลาง = 30%, ผันผวน = 40–50% |

**แหล่งข้อมูลหลัก:** [Yahoo Finance](https://finance.yahoo.com) · [Macrotrends](https://macrotrends.net) · [Damodaran Online](https://pages.stern.nyu.edu/~adamodar) · Annual Report ของบริษัท
""")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="val-section-head">🚀 การเติบโตของรายได้</div>', unsafe_allow_html=True)
            growth_yr1   = st.slider(
                "Revenue Growth ปีที่ 1 (%)", -10.0, 50.0,
                float(saved.get("revenue_growth_yr1",   0.12)) * 100, 0.5, format="%.1f%%",
                help="📍 Yahoo Finance → Analysis → Revenue Estimate | หรือ Management Guidance ใน Earnings Call"
            ) / 100
            growth_final = st.slider(
                "Revenue Growth ปีสุดท้าย (%)", -5.0, 30.0,
                float(saved.get("revenue_growth_final", 0.05)) * 100, 0.5, format="%.1f%%",
                help="📍 Growth ที่คาดว่าบริษัทจะเติบโตได้ยั่งยืน — โดยทั่วไป 3–8% แล้วแต่อุตสาหกรรม"
            ) / 100
            growth_years = st.slider(
                "จำนวนปีที่คาดการณ์", 3, 15,
                int(saved.get("growth_years", 10)), 1,
                help="📍 สาธารณูปโภค / อาหาร = 10 ปี | Tech / Startup = 5 ปี | ยิ่งคาดเดาง่าย ยิ่งใช้ได้นานขึ้น"
            )

            st.markdown('<div class="val-section-head">📊 Margin &amp; Reinvestment</div>', unsafe_allow_html=True)
            ebit_target  = st.slider(
                "EBIT Margin เป้าหมาย (%)", 0.0, 50.0,
                float(saved.get("ebit_margin_target", 0.15)) * 100, 0.5, format="%.1f%%",
                help="📍 Macrotrends.net → ค้นชื่อบริษัท → Operating Profit Margin ย้อนหลัง 5 ปี | หรือ Peer average"
            ) / 100
            sales_to_cap = st.number_input(
                "Sales-to-Capital Ratio",
                value=float(saved.get("sales_to_capital", 1.5)),
                min_value=0.1, max_value=10.0, step=0.1, format="%.2f",
                help="📍 คำนวณ: Revenue ÷ (Equity + Debt − Cash) จาก Balance Sheet | หรือดู Industry avg จาก Damodaran Online"
            )

        with col2:
            st.markdown('<div class="val-section-head">💸 ต้นทุนทุน (WACC)</div>', unsafe_allow_html=True)
            wacc         = st.slider(
                "WACC (%)", 3.0, 20.0,
                float(saved.get("wacc", 0.10)) * 100, 0.25, format="%.2f%%",
                help="📍 WACC.com คำนวณให้แล้ว | หรือ CAPM: Rf + Beta × ERP (Beta จาก Yahoo Finance, Rf = Bond yield 10 ปี)"
            ) / 100

            st.markdown('<div class="val-section-head">🏁 Terminal Value</div>', unsafe_allow_html=True)
            term_growth  = st.slider(
                "Terminal Growth Rate (%)", 0.0, 5.0,
                float(saved.get("terminal_growth", 0.025)) * 100, 0.25, format="%.2f%%",
                help="📍 GDP growth ระยะยาว — Developed (US/EU) ≈ 2–3% | Emerging (ไทย/ซาอุ) ≈ 3–5% | ห้ามเกิน WACC"
            ) / 100
            term_roic    = st.slider(
                "Terminal ROIC (%)", 3.0, 30.0,
                float(saved.get("terminal_roic", 0.12)) * 100, 0.5, format="%.1f%%",
                help="📍 ROIC เฉลี่ย 5 ปีย้อนหลัง จาก Macrotrends หรือ Wisesheets | บริษัท moat แข็ง = สูงได้ | Commodity = ≈ WACC"
            ) / 100

            st.markdown('<div class="val-section-head">🛡️ Margin of Safety</div>', unsafe_allow_html=True)
            mos          = st.slider(
                "Margin of Safety (%)", 0.0, 50.0,
                float(saved.get("margin_of_safety", 0.20)) * 100, 5.0, format="%.0f%%",
                help="📍 มั่นคง = 20% | ปานกลาง = 30% | ผันผวนสูง = 40–50% | Buffett มักใช้ 25–50%"
            ) / 100

        # ── Preview ──────────────────────────────────────────────────────────
        preview_inp = DCFInputs(
            **{**saved,
               "revenue_growth_yr1":   growth_yr1,
               "revenue_growth_final": growth_final,
               "growth_years":         growth_years,
               "ebit_margin_target":   ebit_target,
               "sales_to_capital":     sales_to_cap,
               "wacc":                 wacc,
               "terminal_growth":      term_growth,
               "terminal_roic":        term_roic,
               "margin_of_safety":     mos,
            }
        )
        preview_out = run_dcf(preview_inp)
        st.divider()
        if preview_out.error:
            st.error(f"⚠️ {preview_out.error}")
        else:
            cur = saved.get("currency", "USD")
            pm1, pm2, pm3, pm4 = st.columns(4)
            pm1.metric("📌 Intrinsic Value/Share",
                       f"{preview_out.intrinsic_per_share:,.2f} {cur}")
            pm2.metric(f"🛡️ MOS Price (−{mos:.0%})",
                       f"{preview_out.mos_price:,.2f} {cur}")
            pm3.metric("🏛️ Enterprise Value",
                       f"{preview_out.enterprise_value:,.0f}M")
            pm4.metric("📊 PV Terminal / Total",
                       f"{preview_out.pv_terminal / preview_out.enterprise_value * 100:.0f}%" if preview_out.enterprise_value else "—")

        st.markdown("---")
        col_back, col_next = st.columns(2)
        if col_back.button("← ย้อนกลับ", use_container_width=True):
            st.session_state["val_step"] = 1
            st.rerun()
        if col_next.button("คำนวณและดูผล →", type="primary", use_container_width=True):
            if wacc <= term_growth:
                st.error("WACC ต้องมากกว่า Terminal Growth Rate")
                return
            st.session_state["val_inputs"].update({
                "revenue_growth_yr1":   growth_yr1,
                "revenue_growth_final": growth_final,
                "growth_years":         growth_years,
                "ebit_margin_target":   ebit_target,
                "sales_to_capital":     sales_to_cap,
                "wacc":                 wacc,
                "terminal_growth":      term_growth,
                "terminal_roic":        term_roic,
                "margin_of_safety":     mos,
            })
            # คำนวณ Base + Scenarios
            final_inp = DCFInputs.from_dict(st.session_state["val_inputs"])
            st.session_state["val_result"] = {
                "inp":       final_inp,
                "base":      run_dcf(final_inp),
                "scenarios": run_scenarios(final_inp),
            }
            st.session_state["val_step"] = 3
            st.rerun()

    # ════════════════════════════════════════════════════════════════════
    # STEP 3 — Results
    # ════════════════════════════════════════════════════════════════════
    elif step == 3:
        result = st.session_state.get("val_result")
        if not result:
            st.warning("ไม่มีผลการคำนวณ — กลับไปขั้นตอนที่ 1")
            st.session_state["val_step"] = 1
            st.rerun()
            return

        inp: DCFInputs  = result["inp"]
        out: DCFOutputs = result["base"]
        scenarios: dict = result["scenarios"]
        cur = inp.currency

        if out.error:
            st.error(f"❌ {out.error}")
            if st.button("← แก้ไข"):
                st.session_state["val_step"] = 2
                st.rerun()
            return

        # ── Hero metrics (Theme C glow cards) ─────────────────────────────────
        st.markdown(
            f"<div style='font-size:22px;font-weight:800;color:#eaeaea;margin-bottom:4px'>"
            f"📊 ผลการประเมิน — "
            f"<span style='color:#e94560'>{inp.company_name}</span>"
            f" <span style='color:#555;font-size:16px'>({inp.ticker})</span></div>",
            unsafe_allow_html=True,
        )

        # compare vs market price for delta
        _cp = inp.current_price if inp.current_price and inp.current_price > 0 else None
        _iv = out.intrinsic_per_share
        _mos = out.mos_price
        if _cp:
            _iv_pct = (_iv - _cp) / _cp * 100
            _mos_pct = (_mos - _cp) / _cp * 100
            _iv_delta  = f"<span style='color:{'#00e676' if _iv_pct>=0 else '#e94560'};font-size:12px'>{'▲' if _iv_pct>=0 else '▼'} {abs(_iv_pct):.1f}% vs ตลาด</span>"
            _mos_delta = f"<span style='color:{'#00e676' if _mos_pct>=0 else '#e94560'};font-size:12px'>{'▲' if _mos_pct>=0 else '▼'} {abs(_mos_pct):.1f}% vs ตลาด</span>"
        else:
            _iv_delta = _mos_delta = ""

        st.markdown(f"""
<div class="val-hero-grid">
  <div class="val-hero-card card-intrinsic">
    <div class="hc-glow"></div>
    <div class="hc-icon">💎</div>
    <div class="hc-label">Intrinsic Value / Share</div>
    <div class="hc-value">{out.intrinsic_per_share:,.2f}</div>
    <div class="hc-sub">{cur} / share &nbsp;{_iv_delta}</div>
  </div>
  <div class="val-hero-card card-mos">
    <div class="hc-glow"></div>
    <div class="hc-icon">🛡️</div>
    <div class="hc-label">MOS Price (−{inp.margin_of_safety:.0%})</div>
    <div class="hc-value">{out.mos_price:,.2f}</div>
    <div class="hc-sub">{cur} / share &nbsp;{_mos_delta}</div>
  </div>
  <div class="val-hero-card card-ev">
    <div class="hc-glow"></div>
    <div class="hc-icon">🏛️</div>
    <div class="hc-label">Enterprise Value</div>
    <div class="hc-value">{out.enterprise_value:,.0f}M</div>
    <div class="hc-sub">{cur}</div>
  </div>
  <div class="val-hero-card card-equity">
    <div class="hc-glow"></div>
    <div class="hc-icon">💼</div>
    <div class="hc-label">Equity Value</div>
    <div class="hc-value">{out.equity_value:,.0f}M</div>
    <div class="hc-sub">{cur}</div>
  </div>
</div>
""", unsafe_allow_html=True)

        # ── Reverse DCF ───────────────────────────────────────────────────────
        if inp.current_price > 0:
            st.divider()
            st.markdown('<div class="val-section-head">🔍 ตลาดคาดอะไร? (Reverse DCF)</div>', unsafe_allow_html=True)

            rdcf  = reverse_dcf(inp)
            rdcf1 = reverse_dcf_single_stage(inp)

            if rdcf.get("error") and not rdcf.get("converged", True):
                st.warning(f"⚠️ Reverse DCF: {rdcf['error']}")
            else:
                # ── signal badge ─────────────────────────────────────────────
                signal = rdcf.get("signal", "")
                sig_color = {"undervalued": "#00e676", "fairly_valued": "#ffab00", "overvalued": "#e94560"}.get(signal, "#888")
                sig_badge_cls = {"undervalued": "badge-undervalued", "fairly_valued": "badge-fairly", "overvalued": "badge-overvalued"}.get(signal, "badge-fairly")
                sig_icon  = {"undervalued": "▲", "fairly_valued": "●", "overvalued": "▼"}.get(signal, "●")
                sig_th_label = {"undervalued": "UNDERVALUED — ตลาดคาดน้อยกว่า assumption อาจมี Upside",
                                "fairly_valued": "FAIRLY VALUED — ตลาดคาดใกล้เคียง assumption",
                                "overvalued": "OVERVALUED — Priced-in มาก ระวัง Downside"}.get(signal, "")

                implied_g  = rdcf.get("implied_growth_yr1", 0.0)
                user_g     = inp.revenue_growth_yr1
                diff       = rdcf.get("vs_user_growth", 0.0)

                st.markdown(
                    f'<span class="val-signal-badge {sig_badge_cls}">{sig_icon} {sig_th_label}</span>',
                    unsafe_allow_html=True,
                )

                r1, r2 = st.columns(2)
                with r1:
                    st.markdown(f"""
<div class="rdcf-card" style="border:1px solid {sig_color}33">
  <div style="font-size:11px;color:#888;letter-spacing:.5px;text-transform:uppercase">📈 Multi-year Implied Growth</div>
  <div class="rdcf-big" style="color:{sig_color}">{implied_g:.1%}<span style="font-size:16px;color:#aaa"> / ปี</span></div>
  <div style="font-size:13px;color:#ccc;margin-top:6px">
    ราคาตลาด <b style="color:#eaeaea">{inp.current_price:,.2f} {cur}</b> imply ต้องโต <b style="color:{sig_color}">{implied_g:.1%}</b> ในปีแรก
  </div>
  <div style="display:flex;gap:16px;margin-top:10px">
    <div style="font-size:12px;color:#888">Assumption ของคุณ<br/><b style="color:#eaeaea;font-size:14px">{user_g:.1%}</b></div>
    <div style="font-size:12px;color:#888">ส่วนต่าง<br/><b style="color:{sig_color};font-size:14px">{diff:+.1%}</b></div>
  </div>
</div>
""", unsafe_allow_html=True)

                with r2:
                    if not rdcf1.get("error"):
                        rev_m  = rdcf1.get("revenue_multiple", 0.0)
                        ss_rev = rdcf1.get("implied_revenue",  0.0)
                        st.markdown(f"""
<div class="rdcf-card" style="border:1px solid #7b2fff44">
  <div style="font-size:11px;color:#888;letter-spacing:.5px;text-transform:uppercase">🏁 Single-Stage Sanity Check</div>
  <div class="rdcf-big" style="color:#b57bff">{rev_m:.1f}<span style="font-size:16px;color:#aaa">x Revenue</span></div>
  <div style="font-size:13px;color:#ccc;margin-top:6px">
    ต้องโต <b style="color:#b57bff">{rev_m:.1f} เท่า</b> → <b style="color:#eaeaea">{ss_rev:,.0f}M {cur}</b>
  </div>
  <div style="display:flex;gap:16px;margin-top:10px">
    <div style="font-size:12px;color:#888">EBIT Margin<br/><b style="color:#eaeaea;font-size:14px">{inp.ebit_margin_target:.0%}</b></div>
    <div style="font-size:12px;color:#888">RONIC<br/><b style="color:#eaeaea;font-size:14px">{inp.terminal_roic:.0%}</b></div>
    <div style="font-size:12px;color:#888">g<br/><b style="color:#eaeaea;font-size:14px">{inp.terminal_growth:.1%}</b></div>
  </div>
  <div style="font-size:11px;color:#555;margin-top:8px">⚠️ Floor estimate — ไม่นับ negative FCFF ช่วงแรก</div>
</div>
""", unsafe_allow_html=True)

                # ── Margin sensitivity (single-stage) ───────────────────────
                if not rdcf1.get("error") and rdcf1.get("margin_scenarios"):
                    st.markdown("**Sensitivity: Revenue ที่ต้องใหญ่ถึง — ตาม EBIT Margin**")
                    ms_cols = st.columns(3)
                    for ms_col, ms in zip(ms_cols, rdcf1["margin_scenarios"]):
                        ms_col.metric(
                            f"Margin {ms['margin']:.0%}",
                            f"{ms['implied_revenue']:,.0f}M {cur}",
                            f"×{ms['multiple']:.1f} จากปัจจุบัน",
                        )

        st.divider()

        # ══════════════════════════════════════════════════════════════════════
        # ── Cross-validate: Peer Multiples (Comps) ────────────────────────────
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<div class="val-section-head">🏢 Cross-validate — Peer Comparable Multiples</div>', unsafe_allow_html=True)
        st.caption(
            "กรอก Ticker ของบริษัทในอุตสาหกรรมเดียวกัน 3–5 ตัว → ดึง EV/EBITDA, P/E, EV/Revenue → "
            "คำนวณ implied value และเปรียบเทียบกับ DCF ของคุณ"
        )

        # ── Peer ticker input ────────────────────────────────────────────────
        peer_col1, peer_col2 = st.columns([3, 1])
        with peer_col1:
            peer_tickers_raw = st.text_input(
                "Peer Tickers (คั่นด้วย comma)",
                value=st.session_state.get("peer_tickers_raw", ""),
                placeholder="เช่น  RKLB, SPCE, ASTR, RDW",
                key="peer_tickers_input",
                help="ใช้ Yahoo Finance ticker เช่น AAPL, PTT.BK, 2280.SR"
            )
        with peer_col2:
            fetch_peers_btn = st.button(
                "🔍 ดึงข้อมูล Peers",
                use_container_width=True,
                key="fetch_peers_btn"
            )

        # ── Fetch & cache peer data ──────────────────────────────────────────
        if fetch_peers_btn and peer_tickers_raw.strip():
            tickers_list = [t.strip().upper() for t in peer_tickers_raw.split(",") if t.strip()]
            if tickers_list:
                st.session_state["peer_tickers_raw"] = peer_tickers_raw
                with st.spinner("กำลังดึงข้อมูลจาก Yahoo Finance…"):
                    peer_data_list = []
                    for pt in tickers_list[:6]:   # max 6 peers
                        pd_row = _cached_fetch_multiples(pt)
                        peer_data_list.append(pd_row)
                st.session_state["peer_multiples"] = peer_data_list

        peer_list = st.session_state.get("peer_multiples", [])

        if peer_list:
            valid_peers  = [p for p in peer_list if not p.get("_error")]
            broken_peers = [p for p in peer_list if p.get("_error")]

            if broken_peers:
                for bp in broken_peers:
                    st.warning(f"⚠️ {bp['ticker']}: {bp['_error']}")

            if valid_peers:
                # ── Peer comparison table ────────────────────────────────────
                import pandas as _pd_peer
                peer_rows = []
                for p in valid_peers:
                    peer_rows.append({
                        "Ticker":       p.get("ticker", ""),
                        "Company":      (p.get("company_name") or "")[:28],
                        "Mkt Cap (M)":  f"{p['market_cap_m']:,.0f}" if p.get("market_cap_m") else "–",
                        "Revenue (M)":  f"{p['revenue_m']:,.0f}"    if p.get("revenue_m")    else "–",
                        "EBITDA (M)":   f"{p['ebitda_m']:,.0f}"     if p.get("ebitda_m")     else "–",
                        "EV/EBITDA":    f"{p['ev_ebitda']:.1f}x"    if p.get("ev_ebitda")    else "–",
                        "P/E":          f"{p['pe_ratio']:.1f}x"     if p.get("pe_ratio")     else "–",
                        "EV/Revenue":   f"{p['ev_revenue']:.2f}x"   if p.get("ev_revenue")   else "–",
                    })

                peer_df = _pd_peer.DataFrame(peer_rows)
                st.markdown("**📊 ตาราง Peer Multiples**")
                st.dataframe(peer_df, use_container_width=True, hide_index=True)

                # ── Implied value from peer medians ──────────────────────────
                implied = implied_value_from_multiples(inp, valid_peers, inp.shares_outstanding)
                if not implied.get("_error"):
                    st.markdown("**💡 Implied Value จาก Peer Median Multiples**")
                    st.caption(
                        f"คำนวณจาก Revenue = {inp.revenue_base:,.0f}M | "
                        f"EBIT Margin target = {inp.ebit_margin_target:.0%} | "
                        f"Net Debt = {inp.net_debt:,.0f}M | Shares = {inp.shares_outstanding:,.2f}M"
                    )

                    impl_cols = st.columns(3)
                    _impl_methods = [
                        ("EV/EBITDA",  implied.get("median_ev_ebitda"),  implied.get("implied_price_ev_ebitda"),  "median EV/EBITDA",  "x"),
                        ("P/E",        implied.get("median_pe"),          implied.get("implied_price_pe"),         "median P/E",         "x"),
                        ("EV/Revenue", implied.get("median_ev_revenue"),  implied.get("implied_price_ev_rev"),     "median EV/Rev",      "x"),
                    ]
                    for icol, (method_name, median_val, impl_price, label, suffix) in zip(impl_cols, _impl_methods):
                        with icol:
                            if median_val is not None and impl_price is not None:
                                # Compare to current price
                                cp = inp.current_price
                                if cp and cp > 0:
                                    pct_diff = (impl_price - cp) / cp * 100
                                    arrow = "▲" if pct_diff > 0 else "▼"
                                    diff_txt = f"{arrow} {abs(pct_diff):.1f}% vs ราคาตลาด"
                                    diff_color = "#26a69a" if pct_diff > 0 else "#ef5350"
                                else:
                                    diff_txt   = ""
                                    diff_color = "#aaa"

                                st.markdown(
                                    f"""<div style="border:1px solid #3a3a5c; border-radius:10px; padding:14px; text-align:center">
                                    <div style="font-size:0.85rem; color:#aaa">{method_name}</div>
                                    <div style="font-size:0.75rem; color:#888">{label} = {median_val:.1f}{suffix}</div>
                                    <div style="font-size:1.8rem; font-weight:700; color:#5c6bc0; margin:4px 0">
                                        {impl_price:,.2f}</div>
                                    <div style="font-size:0.75rem; color:#aaa">{cur}/share</div>
                                    <div style="font-size:0.8rem; color:{diff_color}; margin-top:4px">{diff_txt}</div>
                                    </div>""",
                                    unsafe_allow_html=True
                                )
                            else:
                                st.markdown(
                                    f"<div style='border:1px solid #333; border-radius:10px; padding:14px; text-align:center; color:#666'>"
                                    f"{method_name}<br/>ข้อมูลไม่เพียงพอ</div>",
                                    unsafe_allow_html=True
                                )

                # ── Football Field Chart ──────────────────────────────────────
                st.markdown("**🏈 Football Field Chart — Valuation Range**")
                import plotly.graph_objects as _go_ff

                ff_methods  = []
                ff_lows     = []
                ff_highs    = []
                ff_colors   = []

                # 1. DCF: Bear → Bull
                bear_out = scenarios.get("Bear")
                bull_out = scenarios.get("Bull")
                if bear_out and not bear_out.error and bull_out and not bull_out.error:
                    ff_methods.append("DCF (Bear–Bull)")
                    ff_lows.append(bear_out.mos_price)
                    ff_highs.append(bull_out.intrinsic_per_share)
                    ff_colors.append("#7c3aed")

                # 2. DCF Base (point — show as narrow range ±5%)
                ff_methods.append("DCF Base Intrinsic")
                ff_lows.append(out.mos_price)
                ff_highs.append(out.intrinsic_per_share)
                ff_colors.append("#5c6bc0")

                # 3. EV/EBITDA
                if implied.get("implied_price_ev_ebitda"):
                    _p = implied["implied_price_ev_ebitda"]
                    ff_methods.append(f"EV/EBITDA ({implied['median_ev_ebitda']:.1f}x)")
                    ff_lows.append(_p * 0.85)
                    ff_highs.append(_p * 1.15)
                    ff_colors.append("#26a69a")

                # 4. P/E
                if implied.get("implied_price_pe"):
                    _p = implied["implied_price_pe"]
                    ff_methods.append(f"P/E ({implied['median_pe']:.1f}x)")
                    ff_lows.append(_p * 0.85)
                    ff_highs.append(_p * 1.15)
                    ff_colors.append("#66bb6a")

                # 5. EV/Revenue
                if implied.get("implied_price_ev_rev"):
                    _p = implied["implied_price_ev_rev"]
                    ff_methods.append(f"EV/Revenue ({implied['median_ev_revenue']:.2f}x)")
                    ff_lows.append(_p * 0.85)
                    ff_highs.append(_p * 1.15)
                    ff_colors.append("#ffa726")

                # 6. Reverse DCF (implied fair-value = market price)
                if inp.current_price and inp.current_price > 0:
                    cp = inp.current_price
                    ff_methods.append("ราคาตลาดปัจจุบัน")
                    ff_lows.append(cp)
                    ff_highs.append(cp)
                    ff_colors.append("#ef5350")

                if ff_methods:
                    fig_ff = _go_ff.Figure()
                    for i, (method, lo, hi, clr) in enumerate(zip(ff_methods, ff_lows, ff_highs, ff_colors)):
                        fig_ff.add_trace(_go_ff.Bar(
                            name        = method,
                            y           = [method],
                            x           = [hi - lo if hi != lo else 0.001],
                            base        = [lo],
                            orientation = "h",
                            marker_color= clr,
                            marker_line = dict(color=clr, width=1),
                            text        = [f"{lo:,.2f} – {hi:,.2f}" if hi != lo else f"{lo:,.2f}"],
                            textposition= "inside",
                            insidetextanchor="middle",
                            textfont    = dict(size=11, color="white"),
                            showlegend  = False,
                        ))

                    # Market price reference line
                    if inp.current_price and inp.current_price > 0:
                        fig_ff.add_vline(
                            x           = inp.current_price,
                            line_dash   = "dash",
                            line_color  = "#ef5350",
                            line_width  = 2,
                            annotation_text     = f"ราคาตลาด {inp.current_price:,.2f}",
                            annotation_position = "top right",
                            annotation_font     = dict(color="#ef5350", size=11),
                        )

                    # MOS price reference line
                    fig_ff.add_vline(
                        x           = out.mos_price,
                        line_dash   = "dot",
                        line_color  = "#ffd54f",
                        line_width  = 1.5,
                        annotation_text     = f"MOS {out.mos_price:,.2f}",
                        annotation_position = "bottom right",
                        annotation_font     = dict(color="#ffd54f", size=10),
                    )

                    fig_ff.update_layout(
                        title       = f"Football Field — Valuation Comparison ({cur}/share)",
                        template    = "plotly_dark",
                        height      = max(280, 70 * len(ff_methods) + 80),
                        paper_bgcolor = "#0e1117",
                        plot_bgcolor  = "#0e1117",
                        xaxis_title   = f"Implied Price ({cur})",
                        xaxis         = dict(gridcolor="#2a2a3e"),
                        yaxis         = dict(gridcolor="#2a2a3e"),
                        margin        = dict(l=20, r=20, t=50, b=30),
                        barmode       = "overlay",
                    )
                    st.plotly_chart(fig_ff, use_container_width=True)
                    st.caption(
                        "📌 แท่งสี = valuation range จากแต่ละวิธี  |  "
                        "เส้นประแดง = ราคาตลาดปัจจุบัน  |  "
                        "เส้นจุดเหลือง = MOS price ของ DCF Base"
                    )
            else:
                st.info("กรอก Peer Tickers แล้วกด 'ดึงข้อมูล Peers' เพื่อเริ่มต้น")
        else:
            st.info("กรอก Peer Tickers ด้านบนแล้วกด **🔍 ดึงข้อมูล Peers** เพื่อ cross-validate มูลค่า")

        st.divider()

        # ── Scenario comparison ───────────────────────────────────────────────
        st.markdown('<div class="val-section-head">🎯 เปรียบเทียบ 3 Scenarios</div>', unsafe_allow_html=True)
        sc_cols = st.columns(3)
        sc_colors = {"Bull": "#26a69a", "Base": "#7c3aed", "Bear": "#ef5350"}
        sc_icons  = {"Bull": "🐂", "Base": "⚖️", "Bear": "🐻"}
        for sc_col, (sc_name, sc_out) in zip(sc_cols, [
            ("Bull", scenarios.get("Bull")),
            ("Base", scenarios.get("Base")),
            ("Bear", scenarios.get("Bear")),
        ]):
            with sc_col:
                color = sc_colors.get(sc_name, "#888")
                icon  = sc_icons.get(sc_name, "")
                if sc_out and not sc_out.error:
                    st.markdown(
                        f"""<div style="border:1px solid {color}; border-radius:12px; padding:16px; text-align:center">
                        <div style="font-size:1.5rem">{icon} {sc_name}</div>
                        <div style="color:{color}; font-size:2rem; font-weight:700">
                            {sc_out.intrinsic_per_share:,.2f}</div>
                        <div style="color:#aaa; font-size:0.8rem">{cur}/share (Intrinsic)</div>
                        <div style="color:{color}; font-size:1.2rem; margin-top:6px">
                            MOS: {sc_out.mos_price:,.2f} {cur}</div>
                        </div>""",
                        unsafe_allow_html=True
                    )
                else:
                    err_msg = sc_out.error if sc_out else "N/A"
                    st.error(f"{sc_name}: {err_msg}")

        st.divider()

        # ── Year-by-year projection table ─────────────────────────────────────
        with st.expander("📋 ตารางคาดการณ์รายปี", expanded=False):
            proj_df = pd.DataFrame({
                "ปี":             out.years,
                f"Revenue ({cur}M)": [f"{v:,.0f}" for v in out.revenues],
                "EBIT Margin":    [f"{v:.1%}" for v in out.ebit_margins],
                f"NOPAT ({cur}M)":   [f"{v:,.0f}" for v in out.nopats],
                f"Reinvest ({cur}M)":[f"{v:,.0f}" for v in out.reinvestments],
                f"FCFF ({cur}M)":    [f"{v:,.0f}" for v in out.fcffs],
                "Discount Factor":[f"{v:.4f}" for v in out.discount_factors],
                f"PV FCFF ({cur}M)": [f"{v:,.0f}" for v in out.pv_fcffs],
            })
            st.dataframe(proj_df, use_container_width=True, hide_index=True)

            # Terminal summary
            st.markdown(
                f"**Terminal FCFF:** {out.terminal_fcff:,.0f}M {cur} &nbsp;|&nbsp;"
                f"**Terminal Value:** {out.terminal_value:,.0f}M {cur} &nbsp;|&nbsp;"
                f"**PV Terminal:** {out.pv_terminal:,.0f}M {cur}"
            )

        # ── Waterfall bar chart ───────────────────────────────────────────────
        with st.expander("📊 Waterfall — EV Bridge", expanded=True):
            import plotly.graph_objects as go_val
            wf_x = ["PV of FCFFs", "PV Terminal Value", "Enterprise Value",
                    "− Net Debt", "− Minority", "Equity Value"]
            wf_base  = [0, out.pv_fcff_sum, 0, out.equity_value + inp.minority_interest + inp.net_debt, out.equity_value + inp.minority_interest, 0]
            wf_vals  = [out.pv_fcff_sum, out.pv_terminal, 0,
                        -inp.net_debt, -inp.minority_interest, 0]
            wf_total = [False, False, True, False, False, True]
            wf_color = ["#7c3aed", "#26a69a", "#5c6bc0",
                        "#ef5350", "#ff7043", "#4caf50"]

            fig_wf = go_val.Figure(go_val.Waterfall(
                orientation="v",
                measure = ["relative","relative","total","relative","relative","total"],
                x       = wf_x,
                y       = [out.pv_fcff_sum, out.pv_terminal, None,
                           -inp.net_debt, -inp.minority_interest, None],
                connector={"line": {"color": "#444"}},
                increasing={"marker": {"color": "#26a69a"}},
                decreasing={"marker": {"color": "#ef5350"}},
                totals    ={"marker": {"color": "#7c3aed"}},
            ))
            fig_wf.update_layout(
                title=f"Enterprise Value → Equity Value Bridge ({cur}M)",
                template="plotly_dark", height=360,
                paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                yaxis_title=f"{cur} Million",
            )
            st.plotly_chart(fig_wf, use_container_width=True)

        # ── Sensitivity table ─────────────────────────────────────────────────
        with st.expander("🔍 Sensitivity: WACC × Terminal Growth", expanded=False):
            wacc_range = [inp.wacc - 0.02, inp.wacc - 0.01, inp.wacc, inp.wacc + 0.01, inp.wacc + 0.02]
            tg_range   = [inp.terminal_growth - 0.005, inp.terminal_growth, inp.terminal_growth + 0.005,
                          inp.terminal_growth + 0.01]
            wacc_range = [max(0.01, w) for w in wacc_range]
            tg_range   = [max(0.005, t) for t in tg_range]

            sens = sensitivity_table(inp, "wacc", wacc_range, "terminal_growth", tg_range)
            tg_labels  = [f"{t:.2%}" for t in sens["col_values"]]
            wacc_labels = [f"{w:.2%}" for w in sens["row_values"]]

            sens_df = pd.DataFrame(
                sens["table"],
                index=pd.Index(wacc_labels, name="WACC \\ TG"),
                columns=tg_labels,
            )
            # Color-code cells vs MOS price
            def _sens_style(val):
                if val is None: return ""
                mos_p = out.mos_price
                if val >= mos_p * 1.2:  return "background-color: #1b5e20; color: white"
                if val >= mos_p:        return "background-color: #2e7d32; color: white"
                if val >= mos_p * 0.8:  return "background-color: #f57f17; color: black"
                return "background-color: #b71c1c; color: white"

            st.dataframe(
                sens_df.style.applymap(_sens_style).format("{:.2f}"),
                use_container_width=True,
            )
            st.caption(
                f"🟢 เขียว = ราคาสูงกว่า MOS Price ({out.mos_price:.2f} {cur}) "
                f"| 🟠 ส้ม = ใกล้ MOS | 🔴 แดง = ต่ำกว่า MOS"
            )

        # ── Tornado chart ─────────────────────────────────────────────────────
        with st.expander("🌪️ Tornado Chart — ปัจจัยที่มีผลกับมูลค่าสูงสุด", expanded=False):
            from dcf_engine import tornado_data
            tornado_rows = tornado_data(inp, metric="intrinsic_per_share")
            import plotly.graph_objects as go_t
            labels_t = [r["label"]  for r in tornado_rows]
            lows_t   = [r["low"]    for r in tornado_rows]
            highs_t  = [r["high"]   for r in tornado_rows]
            base_t   = out.intrinsic_per_share

            fig_t = go_t.Figure()
            fig_t.add_trace(go_t.Bar(
                y=labels_t, x=[h - base_t for h in highs_t],
                base=base_t,
                orientation="h",
                name="High",
                marker_color="#26a69a",
            ))
            fig_t.add_trace(go_t.Bar(
                y=labels_t, x=[l - base_t for l in lows_t],
                base=base_t,
                orientation="h",
                name="Low",
                marker_color="#ef5350",
            ))
            fig_t.add_vline(x=base_t, line_dash="dash", line_color="#ffd54f",
                            annotation_text=f"Base {base_t:.2f}", annotation_position="top right")
            fig_t.update_layout(
                title=f"Sensitivity Tornado — Intrinsic Value/Share ({cur})",
                barmode="overlay",
                template="plotly_dark", height=420,
                paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                xaxis_title=f"Intrinsic Value ({cur})",
                yaxis={"autorange": "reversed"},
                legend={"orientation": "h", "yanchor": "bottom", "y": 1.02},
            )
            fig_t.update_xaxes(gridcolor="#2a2a3e")
            fig_t.update_yaxes(gridcolor="#2a2a3e")
            st.plotly_chart(fig_t, use_container_width=True)
            st.caption("แต่ละแท่งแสดงผลกระทบเมื่อปรับพารามิเตอร์ ±ขั้นตอนเดียว — แท่งกว้าง = ความเสี่ยงสูง")

        # ── Export CSV ────────────────────────────────────────────────────────
        with st.expander("⬇️ Export ผลการประเมิน", expanded=False):
            from dcf_engine import export_to_csv
            csv_str = export_to_csv(inp, out, scenarios)
            import io as _io
            st.download_button(
                label    = "⬇️ Download CSV",
                data     = csv_str,
                file_name= f"DCF_{inp.ticker}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime     = "text/csv",
                use_container_width=True,
            )
            st.caption("ไฟล์ CSV มีตาราง projection รายปี + ผล scenarios + inputs ทั้งหมด")

        st.divider()

        # ── Save button ───────────────────────────────────────────────────────
        st.markdown('<div class="val-section-head">💾 บันทึกการประเมินนี้</div>', unsafe_allow_html=True)
        save_notes = st.text_area("หมายเหตุ (ถ้ามี)", placeholder="เช่น ใช้ตัวเลข FY2024, สมมติว่า...", height=80)
        col_save, col_back2, col_new = st.columns([2, 1, 1])

        if col_save.button("💾 บันทึกลง Google Sheets", type="primary", use_container_width=True):
            try:
                import json as _j
                val_id = val_save(
                    company_name  = inp.company_name,
                    ticker        = inp.ticker,
                    currency      = inp.currency,
                    date_valued   = datetime.now().strftime("%Y-%m-%d"),
                    inputs        = inp.to_dict(),
                    outputs       = out.to_dict(),
                    notes         = save_notes,
                )
                # บันทึก 3 scenarios ด้วย
                for sc_name, sc_out in scenarios.items():
                    if not sc_out.error:
                        # หา inputs ของ scenario นั้น
                        from dcf_engine import _SCENARIO_PRESETS, DCFInputs as _DI
                        deltas    = _SCENARIO_PRESETS.get(sc_name, {})
                        sc_d      = inp.to_dict()
                        for k, dv in deltas.items():
                            if k in sc_d:
                                sc_d[k] = sc_d[k] + dv
                        scenario_save(val_id, sc_name, sc_d, sc_out.to_dict())

                st.success(f"✅ บันทึกแล้ว (ID: {val_id})")
                st.session_state["val_edit_id"] = val_id
            except Exception as _e:
                st.error(f"บันทึกไม่สำเร็จ: {_e}")

        if col_back2.button("← แก้ไขสมมติฐาน", use_container_width=True):
            st.session_state["val_step"] = 2
            st.rerun()

        if col_new.button("🆕 Valuation ใหม่", use_container_width=True):
            st.session_state["val_step"]   = 1
            st.session_state["val_inputs"] = {}
            st.session_state["val_result"] = None
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# LIST VIEW — saved valuations
# ─────────────────────────────────────────────────────────────────────────────

def _val_list_view():
    from db_gsheets import val_load, val_load_one, val_delete, scenario_load
    from dcf_engine import DCFInputs, DCFOutputs

    st.markdown("### 📋 รายการ Valuation ที่บันทึกไว้")

    try:
        df = val_load()
    except Exception as e:
        st.error(f"โหลดข้อมูลไม่ได้: {e}")
        return

    if df.empty:
        st.info("ยังไม่มี valuation ที่บันทึก — กดปุ่ม **➕ Valuation ใหม่** เพื่อเริ่ม")
        return

    # ── Table list ────────────────────────────────────────────────────────────
    for _, row in df.iterrows():
        import json as _j
        val_id   = str(row.get("id", ""))
        name     = str(row.get("company_name", ""))
        ticker   = str(row.get("ticker", ""))
        cur      = str(row.get("currency", ""))
        dt_val   = str(row.get("date_valued", ""))
        notes    = str(row.get("notes", ""))

        try:
            out_d = _j.loads(row.get("outputs_json") or "{}")
            iv    = float(out_d.get("intrinsic_per_share", 0))
            mos   = float(out_d.get("mos_price", 0))
            ev    = float(out_d.get("enterprise_value", 0))
        except Exception:
            iv, mos, ev = 0, 0, 0

        with st.expander(f"**{name}** ({ticker}) — {dt_val}", expanded=False):
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Intrinsic/Share",    f"{iv:,.2f} {cur}")
            m2.metric("MOS Price",          f"{mos:,.2f} {cur}")
            m3.metric("Enterprise Value",   f"{ev:,.0f}M")
            m4.metric("Date",               dt_val)

            if notes:
                st.caption(f"📝 {notes}")

            # Scenarios sub-section
            sc_list = scenario_load(val_id)
            if sc_list:
                sc_data = {s["scenario_name"]: s for s in sc_list}
                sc_names = ["Bull", "Base", "Bear"]
                sc_cols  = st.columns(3)
                sc_icons = {"Bull": "🐂", "Base": "⚖️", "Bear": "🐻"}
                sc_colors = {"Bull": "#26a69a", "Base": "#7c3aed", "Bear": "#ef5350"}
                for scol, sc_name in zip(sc_cols, sc_names):
                    sc = sc_data.get(sc_name)
                    if sc:
                        try:
                            sc_iv  = float(sc["outputs"].get("intrinsic_per_share", 0))
                            sc_mos = float(sc["outputs"].get("mos_price", 0))
                            color  = sc_colors.get(sc_name, "#888")
                            icon   = sc_icons.get(sc_name, "")
                            scol.markdown(
                                f"<div style='text-align:center; color:{color}'>"
                                f"<b>{icon} {sc_name}</b><br/>"
                                f"<span style='font-size:1.3rem;font-weight:700'>{sc_iv:,.2f}</span> {cur}/share<br/>"
                                f"MOS: {sc_mos:,.2f}</div>",
                                unsafe_allow_html=True
                            )
                        except Exception:
                            pass

            # Action buttons
            ba1, ba2 = st.columns([1, 1])
            if ba1.button("✏️ แก้ไข / ดูรายละเอียด", key=f"edit_{val_id}", use_container_width=True):
                # โหลด inputs กลับมาใส่ Wizard
                try:
                    rec = val_load_one(val_id)
                    if rec:
                        st.session_state["val_inputs"]    = rec["inputs"]
                        st.session_state["val_edit_id"]   = val_id
                        st.session_state["val_step"]      = 3
                        st.session_state["val_result"]    = {
                            "inp":       DCFInputs.from_dict(rec["inputs"]),
                            "base":      DCFOutputs.from_dict(rec["outputs"]),
                            "scenarios": {},
                        }
                        st.session_state["val_view_mode"] = "wizard"
                        st.rerun()
                except Exception as _err:
                    st.error(f"โหลดไม่สำเร็จ: {_err}")

            if ba2.button("🗑️ ลบ", key=f"del_{val_id}", use_container_width=True):
                try:
                    val_delete(val_id)
                    st.success(f"ลบ {name} แล้ว")
                    st.rerun()
                except Exception as _err:
                    st.error(f"ลบไม่สำเร็จ: {_err}")


def _events_to_df(events) -> "pd.DataFrame":
    """แปลง list[TimelineEvent] → DataFrame สำหรับ st.data_editor
    credibility:
      🔗 มีแหล่งอ้างอิง  = มี source_url จริง (Tavily article)
      📖 Wikipedia       = source_name มีคำว่า wikipedia
      🤖 AI Knowledge    = Groq เติมจาก knowledge ล้วนๆ ไม่มี URL
    default include: True ถ้า importance >= 2
    """
    rows = []
    for e in events:
        if e.source_url and e.source_url.startswith("http"):
            cred = "🔗 มีแหล่งอ้างอิง"
        elif e.source_name and "wikipedia" in e.source_name.lower():
            cred = "📖 Wikipedia"
        elif e.source_name:
            cred = f"📖 {e.source_name[:35]}"
        else:
            cred = "🤖 AI Knowledge"

        rows.append({
            "✓":            e.importance >= 2,
            "ปี":           e.year,
            "เดือน":        e.month if e.month else "",
            "หัวข้อ":       e.title,
            "หมวด":         f"{e.icon} {e.category_label}",
            "★":            "★" * e.importance,
            "แหล่งข้อมูล": cred,
        })
    return pd.DataFrame(rows)




def _render_timeline_chart(ticker_input: str, events) -> None:
    """กราฟราคาหุ้น (area) + ทุก event
    แบบ B — visual weight:
      Tier 2 (product/pivot/expansion/milestone/acquisition) = circle ใหญ่ + emoji
      อื่นๆ (founding/leadership/crisis/ipo/funding/other)   = diamond เล็ก โปร่งแสง
    """
    import plotly.graph_objects as go
    import pandas as pd

    # ── Category config ────────────────────────────────────────────────────
    TIER_2A = {"product", "pivot", "expansion", "milestone"}
    TIER_2B = {"acquisition"}
    TIER_2  = TIER_2A | TIER_2B

    # สีและ emoji ของ Tier 2
    T2_COLOR = {"product": "#06b6d4", "pivot": "#f97316",
                "expansion": "#06b6d4", "milestone": "#22c55e",
                "acquisition": "#a855f7"}
    T2_EMOJI = {"product": "🚀", "pivot": "🔄", "expansion": "🌍",
                "milestone": "🏆", "acquisition": "🤝"}

    try:
        import yfinance as _yf
        hist = _yf.Ticker(ticker_input).history(period="max")
        if hist.empty:
            st.caption("ไม่พบข้อมูลราคาหุ้น — แสดงเฉพาะ timeline")
            return
    except Exception:
        st.caption("ไม่พบข้อมูลราคาหุ้น — แสดงเฉพาะ timeline")
        return

    monthly   = hist["Close"].resample("ME").last().dropna()
    ipo_start = monthly.index[0]

    fig = go.Figure()

    # ── Area chart ─────────────────────────────────────────────────────────
    fig.add_trace(go.Scatter(
        x=monthly.index, y=monthly.values,
        mode="lines", name="ราคาปิด",
        line=dict(color="#0ea5e9", width=1.5),
        fill="tozeroy", fillcolor="rgba(14,165,233,0.08)",
        hovertemplate="%{x|%b %Y}  $%{y:,.2f}<extra></extra>",
    ))

    def _snap(ev):
        """แปลง event → (date, price) บน monthly index"""
        month    = ev.month or 6
        event_dt = pd.Timestamp(year=ev.year, month=month, day=15, tz="UTC")
        if event_dt < ipo_start:
            return None, None
        if event_dt > monthly.index[-1]:
            event_dt = monthly.index[-1]
        idx   = monthly.index.get_indexer([event_dt], method="nearest")[0]
        return monthly.index[idx], float(monthly.iloc[idx])

    # ── วาด secondary events ก่อน (ทับได้ → Tier 2 จะอยู่บน) ──────────────
    secondary = [e for e in events if e.category not in TIER_2]
    for ev in secondary:
        try:
            date, price = _snap(ev)
            if date is None:
                continue
            desc  = ev.description[:120] + "…" if len(ev.description) > 120 else ev.description
            # diamond เล็ก โปร่งแสง ใช้สีของ category เดิม
            size  = {1: 6, 2: 8, 3: 10}.get(ev.importance, 8)
            color_hex = ev.color        # สีจาก CATEGORIES
            # แปลง hex → rgba โปร่งแสง 55%
            r, g, b   = int(color_hex[1:3], 16), int(color_hex[3:5], 16), int(color_hex[5:7], 16)
            fill_rgba = f"rgba({r},{g},{b},0.55)"
            fig.add_trace(go.Scatter(
                x=[date], y=[price],
                mode="markers",
                marker=dict(size=size, color=fill_rgba, symbol="diamond",
                            line=dict(color=color_hex, width=1)),
                hovertemplate=(
                    f"<b>{ev.icon} {ev.category_label}</b><br>"
                    f"<b>{ev.date_label}</b><br>"
                    f"<b>{ev.title}</b><br>"
                    f"<span style='color:#aaa'>{desc}</span>"
                    f"<extra></extra>"
                ),
                showlegend=False,
            ))
        except Exception:
            continue

    # ── วาด Tier 2 ทับบน (circle ใหญ่ + emoji) ────────────────────────────
    tier2 = [e for e in events if e.category in TIER_2]
    for ev in tier2:
        try:
            date, price = _snap(ev)
            if date is None:
                continue
            color = T2_COLOR.get(ev.category, "#06b6d4")
            emoji = T2_EMOJI.get(ev.category, "🔷")
            label = ev.category_label
            size  = {1: 10, 2: 14, 3: 18}.get(ev.importance, 14)
            desc  = ev.description[:150] + "…" if len(ev.description) > 150 else ev.description
            fig.add_trace(go.Scatter(
                x=[date], y=[price],
                mode="markers+text",
                marker=dict(size=size, color=color, symbol="circle",
                            line=dict(color="#ffffff", width=1.5)),
                text=[emoji],
                textposition="top center",
                textfont=dict(size=10),
                hovertemplate=(
                    f"<b>{emoji} {label}</b><br>"
                    f"<b>{ev.date_label}</b><br>"
                    f"<b>{ev.title}</b><br>"
                    f"<span style='color:#aaa'>{desc}</span>"
                    f"<extra></extra>"
                ),
                showlegend=False,
            ))
        except Exception:
            continue

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0d0d1a",
        plot_bgcolor="#0d0d1a",
        height=440,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", title=""),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)",
                   title="ราคา (USD)", tickprefix="$"),
        hovermode="closest",
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "🚀 Product  🔄 Pivot  🌍 Expansion  🏆 Milestone  🤝 M&A  "
        "· circle ใหญ่ = Tier 2 (สำคัญ)  · diamond เล็ก = เหตุการณ์อื่น  "
        "· hover ดูรายละเอียด"
    )


def _render_timeline_tab():
    """Tab: Company Timeline Generator — Upload File"""
    try:
        from timeline_engine import render_timeline_html, CATEGORIES
    except ImportError as _ie:
        st.error(f"❌ Import error: {_ie}")
        return

    st.markdown("## 📖 Company Timeline Generator")
    _render_file_timeline_tab(render_timeline_html, CATEGORIES)


# ─── File Upload Timeline Tab ────────────────────────────────────────────────

def _render_file_timeline_tab(render_timeline_html, CATEGORIES) -> None:
    """Sub-tab: Upload Excel/CSV → แสดง Timeline ทันที ทุก event สำคัญหมด"""
    from file_timeline_engine import (
        parse_uploaded_file, detect_date_event_cols, df_to_events,
    )

    st.caption("อัพโหลด Excel/CSV → ระบบตรวจจับคอลัมน์อัตโนมัติ → แสดง Timeline ทันที")

    # ── Session state ──────────────────────────────────────────────────────
    for _k, _v in [("ft_events", []), ("ft_ticker_used", "")]:
        if _k not in st.session_state:
            st.session_state[_k] = _v

    # ── Input row: file + ticker + button ─────────────────────────────────
    up_col, ticker_col, btn_col = st.columns([3, 1, 1])
    uploaded  = up_col.file_uploader(
        "ไฟล์", type=["xlsx", "xls", "csv"], label_visibility="collapsed",
    )
    ft_ticker = ticker_col.text_input(
        "Ticker", placeholder="เช่น NVDA", label_visibility="collapsed",
    ).upper().strip()
    generate  = btn_col.button("📊 Generate", type="primary", use_container_width=True)

    if not uploaded:
        st.info("💡 อัพโหลด Excel/CSV แล้วกด Generate")
        return

    # ── Process เมื่อกด Generate เท่านั้น ─────────────────────────────────
    if generate:
        df, err = parse_uploaded_file(uploaded)
        if err:
            st.error(err)
            return
        if df.empty:
            st.warning("ไฟล์ว่างเปล่า")
            return
        date_col, event_col, cat_col, desc_col = detect_date_event_cols(df)
        events = df_to_events(df, date_col, event_col, cat_col=cat_col, desc_col=desc_col)
        if not events:
            st.warning("ไม่พบข้อมูลที่ parse ได้")
            return
        st.session_state["ft_events"]      = events
        st.session_state["ft_ticker_used"] = ft_ticker

    # ── Render ─────────────────────────────────────────────────────────────
    events = st.session_state["ft_events"]
    if not events:
        return

    ticker_used = st.session_state["ft_ticker_used"]
    st.caption(f"พบ **{len(events)}** events · {min(e.year for e in events)} – {max(e.year for e in events)}")

    if ticker_used:
        _render_timeline_chart(ticker_used, events)
        st.divider()

    # ── Filter ─────────────────────────────────────────────────────────────
    all_cats = sorted({e.category for e in events})
    cat_opts = {k: f"{CATEGORIES[k][0]} {CATEGORIES[k][1]}" for k in all_cats}
    fc1, fc2 = st.columns([3, 2])
    with fc1:
        sel_cats = st.multiselect(
            "ประเภท event", options=list(cat_opts.keys()),
            default=list(cat_opts.keys()),
            format_func=lambda k: cat_opts[k],
            key="ft_cats",
        )
    with fc2:
        yr_min = min(e.year for e in events)
        yr_max = max(e.year for e in events)
        yr_range = (
            st.slider("ช่วงปี", yr_min, yr_max, (yr_min, yr_max), key="ft_yr")
            if yr_min < yr_max else (yr_min, yr_max)
        )

    # ── Render timeline ────────────────────────────────────────────────────
    html = render_timeline_html(
        events,
        filter_cats = sel_cats or None,
        year_min    = yr_range[0],
        year_max    = yr_range[1],
    )
    st.markdown(html, unsafe_allow_html=True)


# ─── Earnings Call Tab ───────────────────────────────────────────────────────

def _render_earnings_tab():
    """Tab: 📞 Earnings Call — ดึง transcript → แปลไทย → สรุป Mindmap"""
    st.markdown("## 📞 Earnings Call")
    st.caption(
        "ดึง transcript จาก **SEC EDGAR** · แปลเป็นภาษาไทยด้วย Groq · สรุปเป็น Interactive Mindmap"
    )

    # ── Session state init ────────────────────────────────────────────────
    _EC_DEFAULTS = {
        "ec_raw":       "",     # English transcript
        "ec_th":        "",     # Thai translation
        "ec_mindmap":   "",     # Mindmap markdown
        "ec_source":    "",
        "ec_words":     0,
        "ec_chunks":    0,
        "ec_error":     "",
        "ec_ticker":    "",
        "ec_quarter":   "Q4",
        "ec_year":      2024,
    }
    for k, v in _EC_DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # ── Input row ─────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns([2, 1, 1, 2])
    ticker  = c1.text_input(
        "Ticker", placeholder="เช่น NVDA, AAPL, NVO",
        key="ec_ticker_input", label_visibility="visible",
    ).upper().strip()
    quarter = c2.selectbox("Quarter", ["Q1", "Q2", "Q3", "Q4"],
                           index=3, key="ec_q_input")
    year    = c3.number_input("ปี (ปฏิทิน)", min_value=2015, max_value=2026,
                               value=2024, step=1, key="ec_yr_input")
    fetch_clicked = c4.button(
        "🔍 ดึง Transcript", type="primary",
        use_container_width=True, key="ec_fetch_btn",
    )

    # ── Fetch ─────────────────────────────────────────────────────────────
    if fetch_clicked:
        if not ticker:
            st.warning("กรุณาใส่ Ticker ก่อน")
        else:
            with st.spinner(f"🔍 ค้นหา {ticker} {quarter} {int(year)} ใน SEC EDGAR..."):
                from earnings_engine import fetch_transcript
                res = fetch_transcript(ticker, int(year), quarter)

            if res["success"]:
                st.session_state.update({
                    "ec_raw":     res["text"],
                    "ec_source":  res["source"],
                    "ec_words":   res["word_count"],
                    "ec_th":      "",
                    "ec_mindmap": "",
                    "ec_error":   "",
                    "ec_ticker":  ticker,
                    "ec_quarter": quarter,
                    "ec_year":    int(year),
                })
            else:
                st.session_state.update({
                    "ec_raw":   "",
                    "ec_error": res["error"],
                })

    # ── Error ─────────────────────────────────────────────────────────────
    if st.session_state["ec_error"]:
        st.error(st.session_state["ec_error"])
        return

    # ── No data yet ───────────────────────────────────────────────────────
    if not st.session_state["ec_raw"]:
        st.info(
            "💡 กรอก **Ticker** และเลือก **Quarter / ปี** ที่ต้องการ แล้วกด **ดึง Transcript**\n\n"
            "รองรับบริษัทจดทะเบียนในสหรัฐฯ ที่ยื่น 8-K transcript ผ่าน SEC EDGAR (ฟรี ไม่ต้อง API key)"
        )
        return

    # ── Show fetch result ─────────────────────────────────────────────────
    raw    = st.session_state["ec_raw"]
    words  = st.session_state["ec_words"]
    source = st.session_state["ec_source"]
    st.success(f"✅ พบ transcript จาก **{source}** — **{words:,} คำ**")

    with st.expander("📄 Transcript ต้นฉบับ (ภาษาอังกฤษ)", expanded=False):
        st.text_area("", raw, height=280, key="ec_raw_view")

    st.divider()

    # ── Translate ─────────────────────────────────────────────────────────
    st.markdown("### 🌐 แปลเป็นภาษาไทย")

    chunks_est = max(1, words // 700)
    st.caption(
        f"ประมาณ **{chunks_est} chunks** · ใช้เวลาราว **{chunks_est * 5}–{chunks_est * 8} วินาที**"
    )

    translate_clicked = st.button(
        "🌐 แปลเต็ม Transcript", type="primary", key="ec_translate_btn",
    )

    if translate_clicked:
        try:
            _gk      = st.secrets["GROQ_API_KEY"]
            groq_key = str(_gk["GROQ_API_KEY"] if hasattr(_gk, "__getitem__") and not isinstance(_gk, str) else _gk)
        except Exception:
            groq_key = ""

        if not groq_key:
            st.error("❌ ไม่พบ GROQ_API_KEY ใน Secrets")
        else:
            prog_bar  = st.progress(0.0, text="เริ่มแปล...")
            prog_text = st.empty()

            def _prog(done, total):
                pct = done / total if total else 0
                prog_bar.progress(pct, text=f"แปลส่วนที่ {done}/{total}...")
                prog_text.caption(f"⏳ {done} / {total} chunks เสร็จแล้ว")

            from translate_engine import translate_transcript as _translate
            res = _translate(
                raw, groq_key,
                ticker=st.session_state["ec_ticker"],
                progress_callback=_prog,
            )
            prog_bar.empty()
            prog_text.empty()

            if res["success"]:
                st.session_state["ec_th"]     = res["translated"]
                st.session_state["ec_chunks"] = res["chunks_total"]
            else:
                st.error(res["error"])

    # ── Thai transcript display ───────────────────────────────────────────
    if st.session_state["ec_th"]:
        chunks_done = st.session_state["ec_chunks"]
        st.success(f"✅ แปลเสร็จ {chunks_done} chunks")
        st.text_area(
            "📜 Transcript ภาษาไทย",
            st.session_state["ec_th"],
            height=360,
            key="ec_th_view",
        )

        st.divider()

        # ── Mindmap ───────────────────────────────────────────────────────
        st.markdown("### 🗺️ Mindmap สรุป Earnings Call")

        mindmap_clicked = st.button(
            "🗺️ สร้าง Mindmap", type="primary", key="ec_mindmap_btn",
        )

        if mindmap_clicked:
            try:
                _gk      = st.secrets["GROQ_API_KEY"]
                groq_key = str(_gk["GROQ_API_KEY"] if hasattr(_gk, "__getitem__") and not isinstance(_gk, str) else _gk)
            except Exception:
                groq_key = ""

            with st.spinner("🗺️ AI สรุปและสร้าง mindmap..."):
                from translate_engine import generate_mindmap_data as _gen_mm
                res = _gen_mm(
                    raw, groq_key,
                    ticker  = st.session_state["ec_ticker"],
                    quarter = st.session_state["ec_quarter"],
                    year    = st.session_state["ec_year"],
                )

            if res["success"]:
                st.session_state["ec_mindmap"] = res["markdown"]
            else:
                st.error(res["error"])

        if st.session_state["ec_mindmap"]:
            _mm_md = st.session_state["ec_mindmap"]

            # Load template and inject markdown
            _tpl_path = Path(__file__).parent / "mindmap_template.html"
            if _tpl_path.exists():
                _tpl = _tpl_path.read_text(encoding="utf-8")
                # Escape backticks and template literals for JS injection
                _mm_safe = _mm_md.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
                _html    = _tpl.replace("MINDMAP_MARKDOWN", _mm_safe)
                import streamlit.components.v1 as _cv1
                _cv1.html(_html, height=560, scrolling=False)
            else:
                # Fallback: render markdown directly
                st.markdown(_mm_md)

            with st.expander("📋 Mindmap Markdown (copy-paste ได้)", expanded=False):
                st.code(_mm_md, language="markdown")


# ─── Entry Point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()
