# =============================================================================
# db_gsheets.py — Google Sheets drop-in replacement สำหรับ SQLite helpers
# =============================================================================
# วิธีใช้:
#   1. ติดตั้ง:  pip install gspread gspread-dataframe
#   2. สร้าง Google Service Account + แชร์ Spreadsheet ให้ SA email (Editor)
#   3. ใส่ credentials ใน .streamlit/secrets.toml  (ดูตัวอย่างด้านล่าง)
#   4. ใน app.py  แทนที่ Section 2 ด้วย:
#        from db_gsheets import *
# =============================================================================
#
# secrets.toml ตัวอย่าง:
# ─────────────────────────────────────────────────────────────────────────────
# [gsheets]
# spreadsheet_id = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms"
#
# [gcp_service_account]
# type                        = "service_account"
# project_id                  = "my-project-123"
# private_key_id              = "abc123..."
# private_key                 = "-----BEGIN RSA PRIVATE KEY-----\n..."
# client_email                = "my-sa@my-project.iam.gserviceaccount.com"
# client_id                   = "123456789"
# auth_uri                    = "https://accounts.google.com/o/oauth2/auth"
# token_uri                   = "https://oauth2.googleapis.com/token"
# auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
# client_x509_cert_url        = "https://..."
# =============================================================================

import uuid
import streamlit as st
import pandas as pd
from datetime import datetime

# ── ติดตั้ง library ──────────────────────────────────────────────────────────
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSHEETS_OK = True
except ImportError:
    GSHEETS_OK = False

# ── Worksheet names ──────────────────────────────────────────────────────────
WS_DIARY    = "diary"
WS_ALERTS   = "alerts"
WS_WATCHLIST= "watchlist"
WS_PORTFOLIO= "portfolio"
WS_TRADES   = "planned_trades"
WS_ETF      = "etf_holdings"
WS_REBAL    = "rebalancing"

# ── Headers ต่อ sheet (ต้องตรงกับ Column A ใน Spreadsheet) ──────────────────
HEADERS = {
    WS_DIARY:     ["id","ticker","entry_date","entry_type","price_ref","note","created_at"],
    WS_ALERTS:    ["id","ticker","alert_type","price","note","active","created_at","triggered_at"],
    WS_WATCHLIST: ["id","ticker","note","added_at"],
    WS_PORTFOLIO: ["id","ticker","qty","avg_cost"],
    WS_TRADES:    ["id","ticker","support_price","usd_amount","shares","created_at"],
    WS_ETF:       ["etf_ticker","symbol","weight_pct"],
    WS_REBAL:     ["ticker","target_pct"],
}

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


# ─── Client (cached ตลอด session) ───────────────────────────────────────────

@st.cache_resource
def _get_client():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )
    return gspread.authorize(creds)


@st.cache_resource
def _get_spreadsheet():
    """Cache spreadsheet object ตลอด session — ลด open_by_key calls"""
    client = _get_client()
    return client.open_by_key(st.secrets["gsheets"]["spreadsheet_id"])


def _get_ws(sheet_name: str):
    """
    คืน Worksheet object — ใช้ ss.worksheets() (fresh API call) เสมอ
    เพราะ ss เป็น @cache_resource และ internal list อาจ stale
    หากยังไม่มีให้สร้างใหม่พร้อม header
    """
    ss = _get_spreadsheet()
    # ดึง worksheet list สด ๆ จาก API (ไม่ใช้ internal cache ของ ss)
    for ws in ss.worksheets():
        if ws.title == sheet_name:
            return ws
    # ไม่เจอ → สร้างใหม่
    headers = HEADERS.get(sheet_name, [])
    try:
        ws = ss.add_worksheet(title=sheet_name, rows=1000, cols=max(len(headers), 1))
        if headers:
            ws.append_row(headers)
        return ws
    except Exception as _e:
        if "already exists" in str(_e).lower():
            # race condition — ดึง fresh list อีกรอบ
            for ws in ss.worksheets():
                if ws.title == sheet_name:
                    return ws
        raise


# ─── Utility ─────────────────────────────────────────────────────────────────

def _new_id() -> str:
    """สร้าง unique ID แทน AUTO INCREMENT"""
    return str(uuid.uuid4())[:8]


@st.cache_data(ttl=30)
def _ws_to_df(sheet_name: str) -> pd.DataFrame:
    """อ่าน worksheet ทั้งหมดแล้วคืนเป็น DataFrame — cached 30 วินาที เพื่อลด API quota"""
    ws = _get_ws(sheet_name)
    records = ws.get_all_records()            # list[dict]
    if not records:
        return pd.DataFrame(columns=HEADERS[sheet_name])
    return pd.DataFrame(records)


def _find_row(ws, col_name: str, value, headers: list) -> int | None:
    """
    หา row index (1-based, นับ header ด้วย) ของ record ที่ตรงเงื่อนไข
    คืน None ถ้าไม่เจอ
    """
    col_idx = headers.index(col_name) + 1       # gspread ใช้ 1-based
    col_values = ws.col_values(col_idx)          # ['header', 'val1', 'val2', ...]
    for row_i, v in enumerate(col_values[1:], start=2):   # data เริ่ม row 2
        if str(v) == str(value):
            return row_i
    return None


def _ensure_sheets() -> tuple[bool, str]:
    """
    ตรวจสอบ/สร้าง sheets ทุกครั้งที่ init_db() ถูกเรียก
    (ไม่ใช้ @cache_resource เพื่อป้องกัน cache ผลล้มเหลว)
    คืน (ok, error_message)
    """
    try:
        ss = _get_spreadsheet()
        existing = [ws.title for ws in ss.worksheets()]
        for sheet_name, headers in HEADERS.items():
            if sheet_name not in existing:
                try:
                    ws = ss.add_worksheet(title=sheet_name, rows=1000, cols=len(headers))
                    ws.append_row(headers)
                except Exception as _inner:
                    # sheet ถูกสร้างไปแล้ว (race condition) — ไม่ใช่ error จริง
                    if "already exists" in str(_inner).lower():
                        pass
                    else:
                        raise
        return True, ""
    except Exception as e:
        return False, str(e)


def init_db():
    """
    ตรวจสอบว่า Spreadsheet มีทุก sheet ครบ ถ้าไม่มีให้สร้างพร้อม header
    เรียกครั้งเดียวตอน app start  (แทน SQLite init_db)
    """
    if not GSHEETS_OK:
        st.error("กรุณาติดตั้ง: pip install gspread google-auth")
        st.stop()

    ok, err = _ensure_sheets()
    if not ok:
        st.error(f"เปิด Spreadsheet ไม่ได้: {err}")
        st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# DIARY helpers
# ─────────────────────────────────────────────────────────────────────────────

def db_save(ticker, entry_date, entry_type, price_ref, note):
    ws = _get_ws(WS_DIARY)
    ws.append_row([
        _new_id(),
        ticker,
        str(entry_date),
        entry_type,
        price_ref if price_ref else "",
        note,
        datetime.now().strftime("%Y-%m-%d %H:%M"),
    ])
    _ws_to_df.clear()


def db_load(ticker_filter="") -> pd.DataFrame:
    df = _ws_to_df(WS_DIARY)
    if df.empty:
        return df
    df["created_at"] = df["created_at"].astype(str)
    df = df.sort_values("created_at", ascending=False)
    if ticker_filter:
        df = df[df["ticker"].str.upper() == ticker_filter.upper()]
    return df.reset_index(drop=True)


def db_delete_diary(entry_id):
    ws = _get_ws(WS_DIARY)
    row_i = _find_row(ws, "id", entry_id, HEADERS[WS_DIARY])
    if row_i:
        ws.delete_rows(row_i)
    _ws_to_df.clear()


# ─────────────────────────────────────────────────────────────────────────────
# ALERT helpers
# ─────────────────────────────────────────────────────────────────────────────

def alert_add(ticker, alert_type, price, note=""):
    ws = _get_ws(WS_ALERTS)
    ws.append_row([
        _new_id(),
        ticker.upper(),
        alert_type,
        float(price),
        note,
        1,                                        # active = 1
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        "",                                       # triggered_at
    ])
    _ws_to_df.clear()


def alert_load_active(ticker="") -> pd.DataFrame:
    df = _ws_to_df(WS_ALERTS)
    if df.empty:
        return df
    df["active"] = pd.to_numeric(df["active"], errors="coerce").fillna(0).astype(int)
    df["price"]  = pd.to_numeric(df["price"],  errors="coerce")
    df = df[df["active"] == 1]
    if ticker:
        df = df[df["ticker"].str.upper() == ticker.upper()]
    return df.sort_values("price", ascending=False).reset_index(drop=True)


def alert_load_all() -> pd.DataFrame:
    df = _ws_to_df(WS_ALERTS)
    if df.empty:
        return df
    df["price"]  = pd.to_numeric(df["price"],  errors="coerce")
    df["active"] = pd.to_numeric(df["active"],  errors="coerce").fillna(0).astype(int)
    return df.sort_values("created_at", ascending=False).reset_index(drop=True)


def alert_trigger(alert_id):
    ws = _get_ws(WS_ALERTS)
    headers = HEADERS[WS_ALERTS]
    row_i = _find_row(ws, "id", alert_id, headers)
    if row_i:
        active_col      = headers.index("active")       + 1
        triggered_col   = headers.index("triggered_at") + 1
        ws.update_cell(row_i, active_col, 0)
        ws.update_cell(row_i, triggered_col, datetime.now().strftime("%Y-%m-%d %H:%M"))
    _ws_to_df.clear()


def alert_delete(alert_id):
    ws = _get_ws(WS_ALERTS)
    row_i = _find_row(ws, "id", alert_id, HEADERS[WS_ALERTS])
    if row_i:
        ws.delete_rows(row_i)
    _ws_to_df.clear()


# ─────────────────────────────────────────────────────────────────────────────
# PORTFOLIO helpers
# ─────────────────────────────────────────────────────────────────────────────

def portfolio_load() -> list:
    df = _ws_to_df(WS_PORTFOLIO)
    if df.empty:
        return []
    df["qty"]      = pd.to_numeric(df["qty"],      errors="coerce").fillna(0)
    df["avg_cost"] = pd.to_numeric(df["avg_cost"], errors="coerce").fillna(0)
    return df[["ticker", "qty", "avg_cost"]].to_dict("records")


def portfolio_save(items: list):
    ws = _get_ws(WS_PORTFOLIO)
    # ลบ data rows ทั้งหมด (เก็บ header)
    total_rows = len(ws.get_all_values())
    if total_rows > 1:
        ws.delete_rows(2, total_rows)
    # เขียนใหม่ด้วย batch (1 write request แทนที่จะ N requests)
    rows = []
    for item in items:
        if item.get("ticker"):
            rows.append([
                _new_id(),
                item["ticker"],
                item.get("qty", 0),
                item.get("avg_cost", 0.0),
            ])
    if rows:
        ws.append_rows(rows, value_input_option="USER_ENTERED")
    _ws_to_df.clear()


# ─────────────────────────────────────────────────────────────────────────────
# WATCHLIST helpers
# ─────────────────────────────────────────────────────────────────────────────

def wl_add(ticker, note=""):
    df = _ws_to_df(WS_WATCHLIST)
    if not df.empty and ticker.upper() in df["ticker"].str.upper().values:
        return                                   # unique constraint
    ws = _get_ws(WS_WATCHLIST)
    ws.append_row([
        _new_id(),
        ticker.upper(),
        note,
        datetime.now().strftime("%Y-%m-%d %H:%M"),
    ])
    _ws_to_df.clear()


def wl_load() -> pd.DataFrame:
    df = _ws_to_df(WS_WATCHLIST)
    if df.empty:
        return df
    return df.sort_values("added_at", ascending=False).reset_index(drop=True)


def wl_delete(wl_id):
    ws = _get_ws(WS_WATCHLIST)
    row_i = _find_row(ws, "id", wl_id, HEADERS[WS_WATCHLIST])
    if row_i:
        ws.delete_rows(row_i)
    _ws_to_df.clear()


# ─────────────────────────────────────────────────────────────────────────────
# PLANNED TRADES helpers
# ─────────────────────────────────────────────────────────────────────────────

def pt_add(ticker: str, support_price: float, usd_amount: float, shares: float):
    ws = _get_ws(WS_TRADES)
    ws.append_row([
        _new_id(),
        ticker.upper(),
        float(support_price),
        float(usd_amount),
        float(shares),
        datetime.now().strftime("%Y-%m-%d %H:%M"),
    ])
    _ws_to_df.clear()


def pt_load() -> pd.DataFrame:
    df = _ws_to_df(WS_TRADES)
    if df.empty:
        return df
    for col in ["support_price", "usd_amount", "shares"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df.sort_values("created_at", ascending=False).reset_index(drop=True)


def pt_clear():
    ws = _get_ws(WS_TRADES)
    total_rows = len(ws.get_all_values())
    if total_rows > 1:
        ws.delete_rows(2, total_rows)
    _ws_to_df.clear()


# ─────────────────────────────────────────────────────────────────────────────
# ETF HOLDINGS helpers
# ─────────────────────────────────────────────────────────────────────────────

def etf_holdings_load() -> dict:
    """
    คืน dict { 'ETF_TICKER': [{'symbol': str, 'weight_pct': float}, ...] }
    ใช้กับ Advanced Analytics (ETF Look-through / True Exposure)
    """
    df = _ws_to_df(WS_ETF)
    if df.empty:
        return {}
    df["weight_pct"] = pd.to_numeric(df["weight_pct"], errors="coerce").fillna(0)
    df = df[df["etf_ticker"].astype(str).str.strip() != ""]
    df = df[df["symbol"].astype(str).str.strip() != ""]
    df = df[df["weight_pct"] > 0]
    result = {}
    for etk, grp in df.groupby(df["etf_ticker"].str.upper().str.strip()):
        result[etk] = grp[["symbol", "weight_pct"]].to_dict("records")
    return result


def etf_holdings_save(items: list):
    """
    บันทึก ETF Holdings ทั้งหมด (overwrite)
    items: [{"etf_ticker": str, "symbol": str, "weight_pct": float}, ...]
    """
    ws = _get_ws(WS_ETF)
    total_rows = len(ws.get_all_values())
    if total_rows > 1:
        ws.delete_rows(2, total_rows)
    rows = []
    for item in items:
        etk = str(item.get("etf_ticker", "")).strip().upper()
        sym = str(item.get("symbol", "")).strip().upper()
        pct = float(item.get("weight_pct", 0))
        if etk and sym and pct > 0:
            rows.append([etk, sym, pct])
    if rows:
        ws.append_rows(rows, value_input_option="USER_ENTERED")
    _ws_to_df.clear()


# ─────────────────────────────────────────────────────────────────────────────
# REBALANCING helpers
# ─────────────────────────────────────────────────────────────────────────────

def rebalancing_load() -> dict:
    """
    คืน dict { 'TICKER': target_pct_float }
    ใช้กับ Advanced Analytics (Sub-tab C: Rebalancing)
    """
    df = _ws_to_df(WS_REBAL)
    if df.empty:
        return {}
    df["target_pct"] = pd.to_numeric(df["target_pct"], errors="coerce").fillna(0)
    df = df[df["ticker"].astype(str).str.strip() != ""]
    df = df[df["target_pct"] > 0]
    return {
        str(r["ticker"]).strip().upper(): float(r["target_pct"])
        for _, r in df.iterrows()
    }


def rebalancing_save(items: list):
    """
    บันทึก Rebalancing targets ทั้งหมด (overwrite)
    items: [{"ticker": str, "target_pct": float}, ...]
    """
    ws = _get_ws(WS_REBAL)
    total_rows = len(ws.get_all_values())
    if total_rows > 1:
        ws.delete_rows(2, total_rows)
    rows = []
    for item in items:
        tk  = str(item.get("ticker", "")).strip().upper()
        pct = float(item.get("target_pct", 0))
        if tk and pct > 0:
            rows.append([tk, pct])
    if rows:
        ws.append_rows(rows, value_input_option="USER_ENTERED")
    _ws_to_df.clear()


# ─────────────────────────────────────────────────────────────────────────────
# MIGRATION: SQLite  →  Google Sheets (รันครั้งเดียว)
# ─────────────────────────────────────────────────────────────────────────────

def migrate_from_sqlite(db_path: str = "investment_diary.db"):
    """
    ย้ายข้อมูลจาก SQLite ขึ้น Google Sheets ครั้งเดียว
    เรียกใน Streamlit UI ด้วยปุ่ม "Migrate to Google Sheets"
    """
    import sqlite3
    try:
        con = sqlite3.connect(db_path)
    except Exception as e:
        st.error(f"เปิด SQLite ไม่ได้: {e}")
        return

    results = {}

    def _migrate_table(table: str, ws_name: str, headers: list):
        try:
            df = pd.read_sql(f"SELECT * FROM {table}", con)
        except Exception:
            results[table] = "⚠️ ไม่มีตาราง"
            return

        if df.empty:
            results[table] = "✅ ว่างเปล่า ไม่มีอะไรย้าย"
            return

        ws = _get_ws(ws_name)
        total_rows = len(ws.get_all_values())
        if total_rows > 1:
            ws.delete_rows(2, total_rows)   # ล้างข้อมูลเก่าออกก่อน

        rows_to_write = []
        for _, r in df.iterrows():
            row_id = r.get("id", _new_id())
            row = [str(row_id)] + [str(r.get(h, "")) for h in headers[1:]]
            rows_to_write.append(row)

        if rows_to_write:
            ws.append_rows(rows_to_write, value_input_option="USER_ENTERED")
        results[table] = f"✅ ย้าย {len(rows_to_write)} rows"

    _migrate_table("diary",         WS_DIARY,     HEADERS[WS_DIARY])
    _migrate_table("alerts",        WS_ALERTS,    HEADERS[WS_ALERTS])
    _migrate_table("watchlist",     WS_WATCHLIST, HEADERS[WS_WATCHLIST])
    _migrate_table("portfolio",     WS_PORTFOLIO, HEADERS[WS_PORTFOLIO])
    _migrate_table("planned_trades",WS_TRADES,    HEADERS[WS_TRADES])

    con.close()

    for table, msg in results.items():
        st.write(f"**{table}**: {msg}")
    st.success("Migration เสร็จสิ้น! ลบ `from db_gsheets import *` ทดสอบก่อน commit")
