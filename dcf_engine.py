# =============================================================================
# dcf_engine.py — FCFF DCF Valuation Engine (Phase 1)
# =============================================================================
# Model: Free Cash Flow to Firm (FCFF) — Damodaran style
#
# Flow:
#   1. Forecast revenue for N years with declining growth rate
#   2. Calculate EBIT → NOPAT (after tax)
#   3. Calculate Reinvestment (Revenue Growth / Sales-to-Capital ratio)
#   4. FCFF = NOPAT − Reinvestment
#   5. Terminal Value via Gordon Growth Model  (TV = FCFF_N+1 / (WACC − g))
#   6. Discount all CFs by WACC → Enterprise Value
#   7. Bridge to Equity Value  (EV − Debt + Cash)
#   8. Intrinsic Value per Share  (Equity Value / Shares Outstanding)
# =============================================================================

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List
import math


# ─────────────────────────────────────────────────────────────────────────────
# Input Dataclass
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class DCFInputs:
    # ── Company identifiers ──────────────────────────────────────────────────
    company_name:         str   = ""
    ticker:               str   = ""
    currency:             str   = "USD"

    # ── Base year financials ─────────────────────────────────────────────────
    revenue_base:         float = 0.0    # Revenue ปีล่าสุด (ล้านหน่วยเงิน)
    ebit_margin_base:     float = 0.10   # EBIT Margin ปีล่าสุด (เช่น 0.10 = 10%)
    tax_rate:             float = 0.25   # อัตราภาษีนิติบุคคลที่มีผล (effective tax rate)

    # ── Growth phase (Stage 1 + Stage 2 → Terminal) ──────────────────────────
    revenue_growth_yr1:   float = 0.15   # อัตราโตรายได้ปีที่ 1
    revenue_growth_final: float = 0.03   # อัตราโตรายได้ปีสุดท้ายก่อน Terminal
    growth_years:         int   = 10     # จำนวนปีที่คาดการณ์  (phase 1+2 รวม)

    # ── Profitability convergence ────────────────────────────────────────────
    ebit_margin_target:   float = 0.15   # EBIT Margin เป้าหมายปีสุดท้าย (converge)

    # ── Reinvestment ─────────────────────────────────────────────────────────
    sales_to_capital:     float = 1.5    # Revenue / Invested Capital
    #  = ยิ่งสูง ยิ่งใช้เงินลงทุนน้อยในการโต  (Capital-light)

    # ── Terminal value ───────────────────────────────────────────────────────
    terminal_growth:      float = 0.025  # อัตราโตระยะยาว (ควร ≤ GDP growth)
    terminal_roic:        float = 0.12   # ROIC ระยะยาว (ใช้คำนวณ Reinvestment Rate ใน TV)

    # ── Cost of capital ──────────────────────────────────────────────────────
    wacc:                 float = 0.10   # Weighted Average Cost of Capital

    # ── Equity bridge ────────────────────────────────────────────────────────
    net_debt:             float = 0.0    # Net Debt = Total Debt − Cash (ล้าน)  (ลบได้ถ้า net cash)
    minority_interest:    float = 0.0    # Minority Interest (ล้าน)
    shares_outstanding:   float = 1.0   # จำนวนหุ้น (ล้านหุ้น)

    # ── Margin of Safety ─────────────────────────────────────────────────────
    margin_of_safety:     float = 0.20   # ส่วนลดความปลอดภัย เช่น 0.20 = 20%

    # ── Reverse DCF ──────────────────────────────────────────────────────────
    current_price:        float = 0.0    # ราคาตลาดปัจจุบันต่อหุ้น (0 = ไม่ระบุ → ข้าม)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "DCFInputs":
        known = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        return cls(**known)


# ─────────────────────────────────────────────────────────────────────────────
# Output Dataclass
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class DCFOutputs:
    # ── Per-year projection ──────────────────────────────────────────────────
    years:             List[int]   = field(default_factory=list)
    revenues:          List[float] = field(default_factory=list)
    ebit_margins:      List[float] = field(default_factory=list)
    nopats:            List[float] = field(default_factory=list)
    reinvestments:     List[float] = field(default_factory=list)
    fcffs:             List[float] = field(default_factory=list)
    discount_factors:  List[float] = field(default_factory=list)
    pv_fcffs:          List[float] = field(default_factory=list)

    # ── Terminal value ───────────────────────────────────────────────────────
    terminal_fcff:     float = 0.0
    terminal_value:    float = 0.0
    pv_terminal:       float = 0.0

    # ── Enterprise Value breakdown ───────────────────────────────────────────
    pv_fcff_sum:       float = 0.0
    enterprise_value:  float = 0.0

    # ── Equity bridge ────────────────────────────────────────────────────────
    equity_value:      float = 0.0
    intrinsic_per_share: float = 0.0
    mos_price:         float = 0.0   # หลังหัก Margin of Safety

    # ── Helpers ──────────────────────────────────────────────────────────────
    error: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "DCFOutputs":
        known = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        return cls(**known)


# ─────────────────────────────────────────────────────────────────────────────
# Core Calculation
# ─────────────────────────────────────────────────────────────────────────────

def run_dcf(inp: DCFInputs) -> DCFOutputs:
    """
    คำนวณ DCF valuation แบบ FCFF  คืน DCFOutputs

    ถ้า input ผิดพลาด (WACC ≤ terminal_growth ฯลฯ) จะคืน DCFOutputs ที่มี .error != ""
    """
    out = DCFOutputs()

    # ── Validation ────────────────────────────────────────────────────────────
    if inp.wacc <= inp.terminal_growth:
        out.error = f"WACC ({inp.wacc:.1%}) ต้องมากกว่า Terminal Growth ({inp.terminal_growth:.1%})"
        return out
    if inp.revenue_base <= 0:
        out.error = "Revenue Base ต้องมากกว่า 0"
        return out
    if inp.shares_outstanding <= 0:
        out.error = "Shares Outstanding ต้องมากกว่า 0"
        return out
    if inp.sales_to_capital <= 0:
        out.error = "Sales-to-Capital ต้องมากกว่า 0"
        return out

    n = max(1, inp.growth_years)

    # ── Growth rate interpolation ─────────────────────────────────────────────
    # Linear interpolation: yr1_growth → final_growth ใน n ปี
    def _growth(yr: int) -> float:
        if n == 1:
            return inp.revenue_growth_final
        t = (yr - 1) / (n - 1)           # 0 → 1
        return inp.revenue_growth_yr1 + t * (inp.revenue_growth_final - inp.revenue_growth_yr1)

    # ── EBIT Margin interpolation ─────────────────────────────────────────────
    def _margin(yr: int) -> float:
        if n == 1:
            return inp.ebit_margin_target
        t = (yr - 1) / (n - 1)
        return inp.ebit_margin_base + t * (inp.ebit_margin_target - inp.ebit_margin_base)

    # ── Year-by-year projection ───────────────────────────────────────────────
    revenue_prev = inp.revenue_base
    for yr in range(1, n + 1):
        g       = _growth(yr)
        revenue = revenue_prev * (1 + g)
        margin  = _margin(yr)
        ebit    = revenue * margin
        nopat   = ebit * (1 - inp.tax_rate)

        # Reinvestment = ΔRevenue / Sales-to-Capital  (เงินที่ต้องลงทุนเพื่อรายได้เพิ่ม)
        delta_rev    = revenue - revenue_prev
        reinvestment = delta_rev / inp.sales_to_capital if inp.sales_to_capital else 0.0
        reinvestment = max(0.0, reinvestment)   # ไม่ให้ติดลบ (ถ้า revenue ลด ไม่บังคับลงทุนเพิ่ม)

        fcff            = nopat - reinvestment
        discount_factor = 1 / (1 + inp.wacc) ** yr
        pv_fcff         = fcff * discount_factor

        out.years.append(yr)
        out.revenues.append(round(revenue, 2))
        out.ebit_margins.append(round(margin, 6))
        out.nopats.append(round(nopat, 2))
        out.reinvestments.append(round(reinvestment, 2))
        out.fcffs.append(round(fcff, 2))
        out.discount_factors.append(round(discount_factor, 6))
        out.pv_fcffs.append(round(pv_fcff, 2))

        revenue_prev = revenue

    # ── Terminal Value ────────────────────────────────────────────────────────
    # FCFF_terminal = NOPAT_terminal * (1 − Reinvestment Rate)
    # Reinvestment Rate (terminal) = terminal_growth / terminal_roic
    terminal_rev     = revenue_prev * (1 + inp.terminal_growth)
    terminal_ebit    = terminal_rev * inp.ebit_margin_target
    terminal_nopat   = terminal_ebit * (1 - inp.tax_rate)
    terminal_reinv_r = inp.terminal_growth / inp.terminal_roic if inp.terminal_roic else 0.0
    terminal_reinv_r = min(max(terminal_reinv_r, 0.0), 1.0)   # clamp 0–100%
    terminal_fcff    = terminal_nopat * (1 - terminal_reinv_r)

    terminal_value   = terminal_fcff / (inp.wacc - inp.terminal_growth)
    pv_terminal      = terminal_value / (1 + inp.wacc) ** n

    out.terminal_fcff   = round(terminal_fcff,  2)
    out.terminal_value  = round(terminal_value, 2)
    out.pv_terminal     = round(pv_terminal,    2)

    # ── Enterprise Value ──────────────────────────────────────────────────────
    pv_fcff_sum        = sum(out.pv_fcffs)
    enterprise_value   = pv_fcff_sum + pv_terminal

    out.pv_fcff_sum    = round(pv_fcff_sum,      2)
    out.enterprise_value = round(enterprise_value, 2)

    # ── Equity Bridge ─────────────────────────────────────────────────────────
    equity_value         = enterprise_value - inp.net_debt - inp.minority_interest
    intrinsic_per_share  = equity_value / inp.shares_outstanding if inp.shares_outstanding else 0.0
    mos_price            = intrinsic_per_share * (1 - inp.margin_of_safety)

    out.equity_value         = round(equity_value,        2)
    out.intrinsic_per_share  = round(intrinsic_per_share, 4)
    out.mos_price            = round(mos_price,           4)

    return out


# ─────────────────────────────────────────────────────────────────────────────
# Scenario convenience wrapper
# ─────────────────────────────────────────────────────────────────────────────

_SCENARIO_PRESETS = {
    "Base": {},          # no override — use inputs as-is
    "Bull": {
        "revenue_growth_yr1":   +0.05,  # บวกเพิ่ม 5% จาก Base
        "revenue_growth_final": +0.01,
        "ebit_margin_target":   +0.03,
        "wacc":                 -0.01,
    },
    "Bear": {
        "revenue_growth_yr1":   -0.05,
        "revenue_growth_final": -0.01,
        "ebit_margin_target":   -0.03,
        "wacc":                 +0.01,
    },
}


def run_scenarios(
    base_inp: DCFInputs,
    overrides: dict | None = None,
) -> dict[str, DCFOutputs]:
    """
    คำนวณ 3 scenarios: Bull / Base / Bear
    overrides: dict ที่ override delta ของแต่ละ scenario ได้ เช่น
        {"Bull": {"wacc": -0.02}, "Bear": {"revenue_growth_yr1": -0.08}}
    คืน  {"Base": out, "Bull": out, "Bear": out}
    """
    presets = dict(_SCENARIO_PRESETS)
    if overrides:
        for sc, deltas in overrides.items():
            if sc in presets:
                presets[sc] = {**presets[sc], **deltas}

    results = {}
    base_dict = base_inp.to_dict()

    for name, deltas in presets.items():
        inp_dict = dict(base_dict)
        for k, delta in deltas.items():
            if k in inp_dict and isinstance(inp_dict[k], (int, float)):
                inp_dict[k] = inp_dict[k] + delta
        inp = DCFInputs.from_dict(inp_dict)
        results[name] = run_dcf(inp)

    return results


# ─────────────────────────────────────────────────────────────────────────────
# Sensitivity helpers
# ─────────────────────────────────────────────────────────────────────────────

def sensitivity_table(
    base_inp: DCFInputs,
    row_param: str,
    row_values: list,
    col_param: str,
    col_values: list,
    metric: str = "intrinsic_per_share",
) -> dict:
    """
    สร้าง sensitivity table  2 มิติ เช่น WACC vs Terminal Growth
    คืน {
        "row_param": str,
        "col_param": str,
        "row_values": list,
        "col_values": list,
        "table": [[float, ...], ...],   # [row][col]
    }
    """
    table = []
    base_dict = base_inp.to_dict()
    for rv in row_values:
        row_out = []
        for cv in col_values:
            d = dict(base_dict)
            d[row_param] = rv
            d[col_param] = cv
            res = run_dcf(DCFInputs.from_dict(d))
            val = getattr(res, metric, 0.0) if not res.error else None
            row_out.append(val)
        table.append(row_out)
    return {
        "row_param":  row_param,
        "col_param":  col_param,
        "row_values": row_values,
        "col_values": col_values,
        "table":      table,
        "metric":     metric,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Tornado chart helper  (Phase 3)
# ─────────────────────────────────────────────────────────────────────────────

_TORNADO_PARAMS = [
    # (param_key,    label,                low_delta,  high_delta)
    ("revenue_growth_yr1",   "Revenue Growth Yr1",  -0.05,  +0.05),
    ("ebit_margin_target",   "EBIT Margin Target",  -0.03,  +0.03),
    ("wacc",                 "WACC",                +0.02,  -0.02),   # note: higher WACC → lower value
    ("terminal_growth",      "Terminal Growth",     -0.005, +0.005),
    ("terminal_roic",        "Terminal ROIC",       -0.03,  +0.03),
    ("sales_to_capital",     "Sales-to-Capital",    -0.30,  +0.30),
    ("tax_rate",             "Tax Rate",            +0.05,  -0.05),   # higher tax → lower value
    ("margin_of_safety",     "Margin of Safety",    +0.10,  -0.10),   # higher MOS → lower MOS price
]


def tornado_data(
    base_inp: DCFInputs,
    metric: str = "intrinsic_per_share",
    params: list | None = None,
) -> list[dict]:
    """
    สร้างข้อมูล Tornado chart
    คืน list[dict] เรียงจาก impact สูงสุด → ต่ำสุด:
    [{"label": str, "low": float, "high": float, "base": float}, ...]
    """
    param_list = params or _TORNADO_PARAMS
    base_val   = getattr(run_dcf(base_inp), metric, 0.0)
    rows = []
    base_dict = base_inp.to_dict()

    for p_key, label, low_delta, high_delta in param_list:
        d_low  = dict(base_dict);  d_low[p_key]  = base_dict[p_key] + low_delta
        d_high = dict(base_dict);  d_high[p_key] = base_dict[p_key] + high_delta

        out_low  = run_dcf(DCFInputs.from_dict(d_low))
        out_high = run_dcf(DCFInputs.from_dict(d_high))

        val_low  = getattr(out_low,  metric, base_val) if not out_low.error  else base_val
        val_high = getattr(out_high, metric, base_val) if not out_high.error else base_val

        # sort so val_low < val_high in returned dict
        rows.append({
            "label":   label,
            "low":     min(val_low, val_high),
            "high":    max(val_low, val_high),
            "base":    base_val,
            "range":   abs(val_high - val_low),
        })

    rows.sort(key=lambda r: r["range"], reverse=True)
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Export helper  (Phase 3)
# ─────────────────────────────────────────────────────────────────────────────
# Reverse DCF
# ─────────────────────────────────────────────────────────────────────────────

def reverse_dcf(inp: DCFInputs, market_price: float = 0.0) -> dict:
    """
    Multi-year Reverse DCF (Primary method — แม่นกว่า)
    Binary search หา revenue_growth_yr1 ที่ทำให้ intrinsic_per_share ≈ market_price

    Returns dict:
        implied_growth_yr1  : float  (เช่น 0.35 = 35% ต่อปี)
        vs_user_growth      : float  (implied − user assumption)
        signal              : "undervalued" | "fairly_valued" | "overvalued"
        market_price        : float
        converged           : bool
        error               : str (ถ้ามี)
    """
    price = market_price if market_price > 0 else inp.current_price
    if price <= 0:
        return {"error": "ไม่มี market_price — กรอกราคาตลาดใน Step 1"}

    lo, hi = -0.50, 3.00   # search range: −50% ถึง +300% growth
    converged = False
    implied_g = float("nan")

    for _ in range(60):   # max iterations
        mid = (lo + hi) / 2.0
        d   = {**inp.to_dict(), "revenue_growth_yr1": mid}
        out = run_dcf(DCFInputs.from_dict(d))
        if out.error:
            break
        val = out.intrinsic_per_share
        if abs(val - price) < price * 0.0001:   # tolerance 0.01%
            implied_g  = mid
            converged  = True
            break
        if val < price:
            lo = mid
        else:
            hi = mid
    else:
        implied_g = (lo + hi) / 2.0
        converged = abs(implied_g - lo) < 0.0005

    diff = implied_g - inp.revenue_growth_yr1
    if diff < -0.03:
        signal = "undervalued"    # ตลาดคาดโตน้อยกว่าที่เรา assume → เราเห็น upside
    elif diff > 0.03:
        signal = "overvalued"     # ตลาดคาด imply growth สูงกว่า assumption ของเรา
    else:
        signal = "fairly_valued"

    return {
        "implied_growth_yr1": implied_g,
        "vs_user_growth":     diff,
        "signal":             signal,
        "market_price":       price,
        "converged":          converged,
        "error":              "" if converged else "binary search ไม่ converge — ลองปรับ assumption",
    }


def reverse_dcf_single_stage(inp: DCFInputs, market_price: float = 0.0) -> dict:
    """
    Single-stage Reverse DCF — RKLB-style (Secondary / Sanity Check)
    สูตร: EV = FCFF_ss / (WACC − g)  →  แก้หา implied Steady-State Revenue

    Returns dict:
        implied_ev           : float  (ล้าน)
        implied_fcff         : float  (ล้าน)
        implied_nopat        : float  (ล้าน)
        implied_ebit         : float  (ล้าน)
        implied_revenue      : float  (ล้าน)  — ที่ ebit_margin_target
        revenue_multiple     : float  — implied_revenue / revenue_base
        reinvestment_rate    : float
        margin_scenarios     : list[dict]  [{margin, implied_revenue, multiple}]
        error                : str
    """
    price = market_price if market_price > 0 else inp.current_price
    if price <= 0:
        return {"error": "ไม่มี market_price"}

    wacc = inp.wacc
    g    = inp.terminal_growth
    if wacc <= g:
        return {"error": "WACC ต้องมากกว่า Terminal Growth Rate"}

    # ── Equity Value → Enterprise Value ──────────────────────────────────────
    equity_value_m  = price * inp.shares_outstanding          # ล้าน
    implied_ev      = equity_value_m + inp.net_debt + inp.minority_interest

    # ── EV → FCFF (Gordon Growth) ─────────────────────────────────────────────
    implied_fcff    = implied_ev * (wacc - g)

    # ── FCFF → NOPAT  (Reinvestment = g / RONIC) ─────────────────────────────
    ronic               = inp.terminal_roic
    reinvestment_rate   = g / ronic if ronic > 0 else 0.25
    reinvestment_rate   = max(0.0, min(reinvestment_rate, 0.99))
    implied_nopat       = implied_fcff / (1 - reinvestment_rate) if reinvestment_rate < 1 else 0.0

    # ── NOPAT → EBIT ──────────────────────────────────────────────────────────
    t             = inp.tax_rate
    implied_ebit  = implied_nopat / (1 - t) if t < 1 else 0.0

    # ── EBIT → Revenue (at target margin + sensitivity range) ─────────────────
    base_margin     = inp.ebit_margin_target if inp.ebit_margin_target > 0 else 0.15
    implied_revenue = implied_ebit / base_margin if base_margin > 0 else 0.0
    revenue_base    = inp.revenue_base if inp.revenue_base > 0 else 1.0
    revenue_multiple = implied_revenue / revenue_base

    # Sensitivity: margin scenarios
    margin_scenarios = []
    for m in [base_margin * 0.75, base_margin, base_margin * 1.25]:
        m = round(m, 4)
        rev = implied_ebit / m if m > 0 else 0.0
        margin_scenarios.append({
            "margin":   m,
            "implied_revenue": rev,
            "multiple": rev / revenue_base,
        })

    return {
        "implied_ev":        implied_ev,
        "implied_fcff":      implied_fcff,
        "implied_nopat":     implied_nopat,
        "implied_ebit":      implied_ebit,
        "implied_revenue":   implied_revenue,
        "revenue_multiple":  revenue_multiple,
        "reinvestment_rate": reinvestment_rate,
        "margin_scenarios":  margin_scenarios,
        "market_price":      price,
        "error":             "",
    }


# ─────────────────────────────────────────────────────────────────────────────

def export_to_csv(inp: DCFInputs, out: DCFOutputs, scenarios: dict) -> str:
    """
    สร้าง CSV string สำหรับ download
    """
    import io, csv
    buf = io.StringIO()
    w   = csv.writer(buf)

    # ── Header info ───────────────────────────────────────────────────────
    w.writerow(["DCF Valuation Report"])
    w.writerow(["Company", inp.company_name, "Ticker", inp.ticker, "Currency", inp.currency])
    w.writerow([])

    # ── Key results ───────────────────────────────────────────────────────
    w.writerow(["Metric", "Value"])
    w.writerow(["Intrinsic Value / Share", out.intrinsic_per_share])
    w.writerow([f"MOS Price (−{inp.margin_of_safety:.0%})", out.mos_price])
    w.writerow(["Enterprise Value (M)", out.enterprise_value])
    w.writerow(["Equity Value (M)", out.equity_value])
    w.writerow(["PV of FCFFs (M)", out.pv_fcff_sum])
    w.writerow(["PV of Terminal Value (M)", out.pv_terminal])
    w.writerow([])

    # ── Scenarios ─────────────────────────────────────────────────────────
    w.writerow(["Scenario", "Intrinsic/Share", "MOS Price", "Enterprise Value"])
    for sc_name, sc_out in scenarios.items():
        if not sc_out.error:
            w.writerow([sc_name, sc_out.intrinsic_per_share, sc_out.mos_price, sc_out.enterprise_value])
    w.writerow([])

    # ── Year-by-year projection ───────────────────────────────────────────
    w.writerow(["Year", "Revenue", "EBIT Margin", "NOPAT", "Reinvestment", "FCFF", "Discount Factor", "PV FCFF"])
    for i, yr in enumerate(out.years):
        w.writerow([
            yr,
            out.revenues[i],
            f"{out.ebit_margins[i]:.4f}",
            out.nopats[i],
            out.reinvestments[i],
            out.fcffs[i],
            out.discount_factors[i],
            out.pv_fcffs[i],
        ])
    w.writerow(["Terminal", "", "", "", "", out.terminal_fcff, "", ""])
    w.writerow(["Terminal Value", "", "", "", "", out.terminal_value, "", out.pv_terminal])
    w.writerow([])

    # ── Inputs ────────────────────────────────────────────────────────────
    w.writerow(["--- Inputs ---"])
    for k, v in inp.to_dict().items():
        w.writerow([k, v])

    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# Yahoo Finance auto-fill  (Phase 2)
# ─────────────────────────────────────────────────────────────────────────────

def fetch_yf_financials(ticker: str) -> dict:
    """
    ดึงข้อมูลพื้นฐานจาก Yahoo Finance สำหรับ pre-fill Wizard
    คืน dict ที่ตรงกับ key ของ DCFInputs  (เฉพาะที่ดึงได้)
    ถ้า error คืน {"_error": str}

    ข้อมูลที่ดึง:
    - company_name, currency
    - revenue_base   (TTM Revenue หรือ latest annual)
    - ebit_margin_base  (Operating Margin TTM)
    - tax_rate          (Effective Tax Rate 3yr avg)
    - net_debt          (Total Debt − Cash and Equivalents)
    - minority_interest (Minority Interest from balance sheet)
    - shares_outstanding (Shares Outstanding)
    """
    try:
        import yfinance as yf
    except ImportError:
        return {"_error": "yfinance ไม่ได้ติดตั้ง — pip install yfinance"}

    import time as _time
    info = {}
    last_err = ""
    for _attempt in range(3):
        try:
            tk   = yf.Ticker(ticker.strip())
            info = tk.info or {}
            if info:
                break
        except Exception as e:
            last_err = str(e)
            _time.sleep(2 ** _attempt)   # 1s, 2s, 4s backoff
    if not info:
        return {"_error": f"ดึงข้อมูลไม่ได้: {last_err or 'ไม่พบข้อมูล (Yahoo Finance rate-limit — ลองใหม่อีกครั้ง)'}"}

    result = {}

    # ── Company identity ───────────────────────────────────────────────────
    result["company_name"] = info.get("longName") or info.get("shortName") or ticker
    result["ticker"]       = ticker.upper()
    result["currency"]     = info.get("currency") or info.get("financialCurrency") or "USD"

    # ── Current Market Price ────────────────────────────────────────────────
    price_raw = (
        info.get("currentPrice") or
        info.get("regularMarketPrice") or
        info.get("previousClose")
    )
    if price_raw:
        result["current_price"] = round(float(price_raw), 4)

    # ── Revenue (TTM) ──────────────────────────────────────────────────────
    rev_raw = (
        info.get("totalRevenue") or
        info.get("revenueQuarterlyGrowth")  # fallback
    )
    if rev_raw:
        result["revenue_base"] = round(float(rev_raw) / 1_000_000, 2)   # → ล้าน

    # ── EBIT Margin ────────────────────────────────────────────────────────
    op_margin = info.get("operatingMargins")
    if op_margin is not None:
        result["ebit_margin_base"] = round(float(op_margin), 4)

    # ── Tax Rate — try financials income statement ─────────────────────────
    try:
        fin = tk.financials          # Annual Income Statement  (DataFrame)
        if fin is not None and not fin.empty:
            # หา Pretax Income และ Tax Provision ย้อนหลัง 3 ปี
            pre_tax_rows = [r for r in fin.index if "pretax" in r.lower() or "before tax" in r.lower()]
            tax_rows     = [r for r in fin.index if ("tax" in r.lower() and "provision" in r.lower())
                            or r.lower() == "income tax expense"]
            if pre_tax_rows and tax_rows:
                pre_tax = fin.loc[pre_tax_rows[0]].dropna().astype(float)
                tax_exp = fin.loc[tax_rows[0]].dropna().astype(float)
                common_cols = pre_tax.index.intersection(tax_exp.index)
                if len(common_cols) >= 1:
                    rates = []
                    for col in common_cols[:3]:
                        pt = float(pre_tax[col])
                        tx = float(tax_exp[col])
                        if pt > 0 and tx >= 0:
                            rates.append(tx / pt)
                    if rates:
                        result["tax_rate"] = round(sum(rates) / len(rates), 4)
    except Exception:
        pass   # ไม่ได้ก็ใช้ default

    # ── Shares Outstanding ─────────────────────────────────────────────────
    shares = info.get("sharesOutstanding") or info.get("impliedSharesOutstanding")
    if shares:
        result["shares_outstanding"] = round(float(shares) / 1_000_000, 4)   # → ล้านหุ้น

    # ── Net Debt ───────────────────────────────────────────────────────────
    total_debt = info.get("totalDebt") or 0.0
    cash       = (info.get("totalCash") or
                  info.get("cashAndCashEquivalents") or 0.0)
    net_debt   = float(total_debt) - float(cash)
    result["net_debt"] = round(net_debt / 1_000_000, 2)

    # ── Minority Interest — try balance sheet ─────────────────────────────
    try:
        bs = tk.balance_sheet
        if bs is not None and not bs.empty:
            mi_rows = [r for r in bs.index if "minority" in r.lower()]
            if mi_rows:
                mi_val = bs.loc[mi_rows[0]].dropna().astype(float)
                if len(mi_val) >= 1:
                    result["minority_interest"] = round(float(mi_val.iloc[0]) / 1_000_000, 2)
    except Exception:
        pass

    # ── Analyst growth estimate (optional) ────────────────────────────────
    # ใช้ 5yr EPS growth estimate เป็น hint สำหรับ revenue_growth_yr1
    growth_hint = info.get("earningsQuarterlyGrowth") or info.get("revenueGrowth")
    if growth_hint is not None:
        result["_growth_hint"] = round(float(growth_hint), 4)

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Comparable Company Multiples  (Phase 4 — Peer Cross-Validation)
# ─────────────────────────────────────────────────────────────────────────────

def fetch_multiples(ticker: str) -> dict:
    """
    ดึง valuation multiples ของ peer company จาก Yahoo Finance

    คืน dict:
      ticker, company_name, currency
      ev_ebitda       — Enterprise Value / EBITDA (TTM)
      pe_ratio        — Trailing P/E
      ev_revenue      — EV / Revenue (TTM)
      market_cap_m    — Market Cap (ล้านหน่วยเงิน)
      enterprise_value_m  — EV (ล้าน)
      revenue_m       — Revenue TTM (ล้าน)
      ebitda_m        — EBITDA TTM (ล้าน)
      net_income_m    — Net Income TTM (ล้าน)
      _error          — ถ้า error คืน string นี้
    """
    try:
        import yfinance as yf
    except ImportError:
        return {"ticker": ticker.upper(), "_error": "yfinance ไม่ได้ติดตั้ง"}

    import time as _time
    info = {}
    last_err = ""
    for _attempt in range(3):
        try:
            tk   = yf.Ticker(ticker.strip())
            info = tk.info or {}
            if info:
                break
        except Exception as e:
            last_err = str(e)
            _time.sleep(2 ** _attempt)
    if not info:
        return {"ticker": ticker.upper(), "_error": last_err or "ไม่พบข้อมูล (ลองใหม่อีกครั้ง)"}

    out: dict = {}
    out["ticker"]       = ticker.strip().upper()
    out["company_name"] = info.get("longName") or info.get("shortName") or ticker.upper()
    out["currency"]     = info.get("currency") or "USD"

    # ── Market Cap & EV ───────────────────────────────────────────────────
    mc = info.get("marketCap")
    ev = info.get("enterpriseValue")
    out["market_cap_m"]        = round(float(mc) / 1_000_000, 2) if mc else None
    out["enterprise_value_m"]  = round(float(ev) / 1_000_000, 2) if ev else None

    # ── Revenue ──────────────────────────────────────────────────────────
    rev = info.get("totalRevenue")
    out["revenue_m"] = round(float(rev) / 1_000_000, 2) if rev else None

    # ── EBITDA ───────────────────────────────────────────────────────────
    ebitda = info.get("ebitda")
    out["ebitda_m"] = round(float(ebitda) / 1_000_000, 2) if ebitda else None

    # ── Net Income ───────────────────────────────────────────────────────
    ni = info.get("netIncomeToCommon")
    out["net_income_m"] = round(float(ni) / 1_000_000, 2) if ni else None

    # ── Multiples — prefer pre-calculated, fallback to computed ──────────
    # EV/EBITDA
    ev_ebitda = info.get("enterpriseToEbitda")
    if ev_ebitda is None and out["enterprise_value_m"] and out["ebitda_m"] and out["ebitda_m"] > 0:
        ev_ebitda = out["enterprise_value_m"] / out["ebitda_m"]
    out["ev_ebitda"] = round(float(ev_ebitda), 2) if ev_ebitda is not None else None

    # EV/Revenue
    ev_rev = info.get("enterpriseToRevenue")
    if ev_rev is None and out["enterprise_value_m"] and out["revenue_m"] and out["revenue_m"] > 0:
        ev_rev = out["enterprise_value_m"] / out["revenue_m"]
    out["ev_revenue"] = round(float(ev_rev), 2) if ev_rev is not None else None

    # P/E (trailing)
    pe = info.get("trailingPE")
    out["pe_ratio"] = round(float(pe), 2) if pe is not None else None

    return out


def implied_value_from_multiples(
    inp: "DCFInputs",
    peers: list[dict],
    shares_outstanding_m: float,
) -> dict:
    """
    คำนวณ implied equity value per share จาก peer median multiples

    Args:
        inp: DCFInputs ของบริษัทเป้าหมาย (ใช้ revenue_base, ebitda, net_income)
        peers: list ของ dict จาก fetch_multiples()
        shares_outstanding_m: จำนวนหุ้น (ล้านหุ้น)

    Returns dict:
        median_ev_ebitda, implied_ev_from_ebitda, implied_equity_ev_ebitda, implied_price_ev_ebitda
        median_pe, implied_equity_pe, implied_price_pe
        median_ev_revenue, implied_ev_from_revenue, implied_equity_ev_rev, implied_price_ev_rev
        valid_peers_count
    """
    valid = [p for p in peers if not p.get("_error")]
    if not valid:
        return {"_error": "ไม่มีข้อมูล peer ที่ถูกต้อง"}

    def _median(vals):
        clean = sorted([v for v in vals if v is not None and v > 0])
        n = len(clean)
        if n == 0:
            return None
        return clean[n // 2] if n % 2 == 1 else (clean[n // 2 - 1] + clean[n // 2]) / 2

    ev_ebitdas  = [p.get("ev_ebitda")  for p in valid]
    pes         = [p.get("pe_ratio")   for p in valid]
    ev_revs     = [p.get("ev_revenue") for p in valid]

    med_ev_ebitda  = _median(ev_ebitdas)
    med_pe         = _median(pes)
    med_ev_revenue = _median(ev_revs)

    nd   = inp.net_debt
    mi   = inp.minority_interest
    sh   = shares_outstanding_m if shares_outstanding_m > 0 else 1.0

    # ── Target company estimates ─────────────────────────────────────────
    # EBITDA ≈ Revenue × EBIT_margin + D&A  (เราไม่มี D&A → ใช้ EBIT as proxy)
    target_ebit   = inp.revenue_base * inp.ebit_margin_target
    target_ebitda = target_ebit * 1.15     # +15% D&A rough proxy
    target_net_inc = target_ebit * (1 - inp.tax_rate)

    res: dict = {"valid_peers_count": len(valid)}

    # EV/EBITDA
    if med_ev_ebitda and target_ebitda > 0:
        impl_ev = med_ev_ebitda * target_ebitda
        impl_eq = impl_ev - nd - mi
        res["median_ev_ebitda"]          = round(med_ev_ebitda, 2)
        res["implied_ev_from_ebitda"]    = round(impl_ev, 2)
        res["implied_equity_ev_ebitda"]  = round(impl_eq, 2)
        res["implied_price_ev_ebitda"]   = round(impl_eq / sh, 2)

    # P/E
    if med_pe and target_net_inc > 0:
        impl_mktcap = med_pe * target_net_inc
        res["median_pe"]               = round(med_pe, 2)
        res["implied_equity_pe"]       = round(impl_mktcap, 2)
        res["implied_price_pe"]        = round(impl_mktcap / sh, 2)

    # EV/Revenue
    if med_ev_revenue and inp.revenue_base > 0:
        impl_ev_r = med_ev_revenue * inp.revenue_base
        impl_eq_r = impl_ev_r - nd - mi
        res["median_ev_revenue"]          = round(med_ev_revenue, 2)
        res["implied_ev_from_revenue"]    = round(impl_ev_r, 2)
        res["implied_equity_ev_rev"]      = round(impl_eq_r, 2)
        res["implied_price_ev_rev"]       = round(impl_eq_r / sh, 2)

    return res


# ─────────────────────────────────────────────────────────────────────────────
# Quick self-test
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # ตัวอย่าง: Almarai-like (สมมติตัวเลขเพื่อทดสอบ)
    inp = DCFInputs(
        company_name         = "Almarai",
        ticker               = "2280.SR",
        currency             = "SAR",
        revenue_base         = 18_000,    # 18,000 ล้าน SAR
        ebit_margin_base     = 0.12,
        tax_rate             = 0.20,
        revenue_growth_yr1   = 0.10,
        revenue_growth_final = 0.04,
        growth_years         = 10,
        ebit_margin_target   = 0.15,
        sales_to_capital     = 1.2,
        terminal_growth      = 0.03,
        terminal_roic        = 0.12,
        wacc                 = 0.09,
        net_debt             = 15_000,    # 15,000 ล้าน SAR
        minority_interest    = 500,
        shares_outstanding   = 2_500,    # 2,500 ล้านหุ้น
        margin_of_safety     = 0.20,
    )

    out = run_dcf(inp)
    if out.error:
        print(f"Error: {out.error}")
    else:
        print(f"Intrinsic Value per Share : {out.intrinsic_per_share:.2f} {inp.currency}")
        print(f"MOS Price (−{inp.margin_of_safety:.0%})         : {out.mos_price:.2f} {inp.currency}")
        print(f"Enterprise Value          : {out.enterprise_value:,.0f} M {inp.currency}")
        print(f"Equity Value              : {out.equity_value:,.0f} M {inp.currency}")
        print(f"PV of FCFFs               : {out.pv_fcff_sum:,.0f} M {inp.currency}")
        print(f"PV of Terminal Value      : {out.pv_terminal:,.0f} M {inp.currency}")

    print("\n── Scenarios ──")
    scs = run_scenarios(inp)
    for name, r in scs.items():
        if not r.error:
            print(f"  {name:4s}: {r.intrinsic_per_share:.2f} {inp.currency}/share")

    print("\n── Sensitivity (WACC × Terminal Growth) ──")
    tbl = sensitivity_table(
        inp,
        row_param  = "wacc",
        row_values = [0.08, 0.09, 0.10, 0.11],
        col_param  = "terminal_growth",
        col_values = [0.02, 0.025, 0.03, 0.035],
    )
    header = "WACC \\ TG " + "".join(f"  {v:.1%}" for v in tbl["col_values"])
    print(header)
    for rv, row_vals in zip(tbl["row_values"], tbl["table"]):
        vals = "".join(f"  {v:6.2f}" if v is not None else "    N/A" for v in row_vals)
        print(f"  {rv:.0%}       {vals}")
