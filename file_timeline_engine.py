"""
file_timeline_engine.py
───────────────────────
Parse Excel/CSV ที่ผู้ใช้ upload → list[TimelineEvent]
- ตรวจหาคอลัมน์วันที่และเหตุการณ์อัตโนมัติ (ไม่ต้องมี template)
- ใช้ keyword matching สำหรับ category (ไม่ต้องการ API)
- รองรับ ค.ศ. และ พ.ศ. และหลายรูปแบบวันที่
"""

from __future__ import annotations
import re
import pandas as pd
from typing import Optional

from timeline_engine import TimelineEvent

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────

_YEAR_PAT = re.compile(r"\b(19[5-9]\d|20[0-2]\d)\b")

# ชื่อคอลัมน์ที่บ่งชี้ว่าเป็น "วันที่"
_DATE_HINTS = {
    "date", "year", "ปี", "วันที่", "เดือน", "month",
    "period", "quarter", "q", "time", "when", "เวลา", "งวด", "ไตรมาส",
}

# ชื่อคอลัมน์ที่บ่งชี้ว่าเป็น "เหตุการณ์"
_EVENT_HINTS = {
    "event", "title", "เหตุการณ์", "หัวข้อ", "topic", "name",
    "description", "รายละเอียด", "detail", "news", "ข่าว",
    "เรื่อง", "subject", "headline", "content", "เนื้อหา", "ชื่อ",
}

# ชื่อเดือนไทย/อังกฤษ → เลข
_MONTH_MAP: dict[str, int] = {
    # English abbrev
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    # English full
    "january": 1, "february": 2, "march": 3, "april": 4,
    "june": 6, "july": 7, "august": 8, "september": 9,
    "october": 10, "november": 11, "december": 12,
    # Thai abbrev
    "ม.ค.": 1, "ก.พ.": 2, "มี.ค.": 3, "เม.ย.": 4,
    "พ.ค.": 5, "มิ.ย.": 6, "ก.ค.": 7, "ส.ค.": 8,
    "ก.ย.": 9, "ต.ค.": 10, "พ.ย.": 11, "ธ.ค.": 12,
    # Thai full
    "มกราคม": 1, "กุมภาพันธ์": 2, "มีนาคม": 3, "เมษายน": 4,
    "พฤษภาคม": 5, "มิถุนายน": 6, "กรกฎาคม": 7, "สิงหาคม": 8,
    "กันยายน": 9, "ตุลาคม": 10, "พฤศจิกายน": 11, "ธันวาคม": 12,
}

# Keyword → category
_CAT_KEYWORDS: dict[str, list[str]] = {
    "founding":    ["found", "establish", "incorporat", "ก่อตั้ง", "เริ่มต้น", "จัดตั้ง"],
    "product":     ["launch", "release", "introduc", "unveil", "announc", "เปิดตัว",
                    "ออก", "ประกาศ", "เปิดให้", "เปิดตลาด"],
    "acquisition": ["acquir", "merger", "buy ", "purchas", "takeover",
                    "ซื้อ", "ควบรวม", "เข้าซื้อ", "ซื้อกิจการ", "ควบกิจการ"],
    "ipo":         ["ipo", "public offering", "listed", "จดทะเบียน", "เข้าตลาด"],
    "leadership":  ["ceo", "cfo", "coo", "appoint", "resign", "step down",
                    "ผู้บริหาร", "แต่งตั้ง", "ลาออก", "ประธาน", "กรรมการ"],
    "funding":     ["fund", "invest", "raise", "capital", "series",
                    "ระดมทุน", "ลงทุน", "เงินทุน"],
    "crisis":      ["recall", "fine", "penalty", "bankrupt", "lawsuit", "sued",
                    "crisis", "วิกฤต", "ปรับ", "ฟ้อง", "ล้มละลาย", "ขาดทุน"],
    "milestone":   ["record", "milestone", "first", "award", "breakthrough",
                    "billion", "สำเร็จ", "รางวัล", "แรก", "ครั้งแรก", "ทะลุ"],
    "expansion":   ["expand", "enter", "open", "new market", "branch",
                    "ขยาย", "เปิดสาขา", "บุกตลาด", "เข้าสู่"],
    "pivot":       ["pivot", "restructur", "transform", "rebrand", "spin",
                    "เปลี่ยน", "ปรับโครงสร้าง", "ปรับทิศทาง"],
}


# ─────────────────────────────────────────────
# 1. Column detection
# ─────────────────────────────────────────────

def detect_date_event_cols(df: pd.DataFrame) -> tuple[str | None, str | None]:
    """ตรวจหาคอลัมน์วันที่และเหตุการณ์โดยอัตโนมัติ
    คืน (date_col_name, event_col_name) — None ถ้าหาไม่เจอ
    """
    cols = list(df.columns)
    date_col:  str | None = None
    event_col: str | None = None

    # ── รอบ 1: datetime dtype ──────────────────────────────────────────────
    for col in cols:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            date_col = col
            break

    # ── รอบ 2: ชื่อคอลัมน์ ─────────────────────────────────────────────────
    for col in cols:
        col_lower = str(col).lower().strip()
        if date_col is None and any(h in col_lower for h in _DATE_HINTS):
            date_col = col
        if event_col is None and any(h in col_lower for h in _EVENT_HINTS):
            event_col = col

    # ── รอบ 3: content-based (date) ────────────────────────────────────────
    if date_col is None:
        for col in cols:
            sample = df[col].dropna().head(15).astype(str)
            year_hits = sample.apply(lambda x: bool(_YEAR_PAT.search(x))).sum()
            if year_hits >= max(3, len(sample) // 2):
                date_col = col
                break

    # ── รอบ 4: longest text column (event) ─────────────────────────────────
    if event_col is None:
        str_cols = [c for c in cols if c != date_col
                    and df[c].dtype == object
                    and df[c].dropna().astype(str).str.len().mean() > 5]
        if str_cols:
            event_col = max(
                str_cols,
                key=lambda c: df[c].dropna().astype(str).str.len().mean()
            )

    # ── Fallback ────────────────────────────────────────────────────────────
    if date_col is None and len(cols) >= 1:
        date_col = cols[0]
    if event_col is None and len(cols) >= 2:
        event_col = cols[1] if cols[1] != date_col else (cols[2] if len(cols) > 2 else None)

    return date_col, event_col


# ─────────────────────────────────────────────
# 2. Date parsing
# ─────────────────────────────────────────────

def parse_date_value(val) -> tuple[int | None, int | None]:
    """แปลง value หลากหลายรูปแบบ → (year, month)
    รองรับ: datetime object, ปี ค.ศ., ปี พ.ศ. (25xx), string ผสมเดือน
    """
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None, None

    # datetime / Timestamp object
    if hasattr(val, "year"):
        return int(val.year), int(val.month)

    s = str(val).strip()
    if not s or s.lower() in ("nan", "none", ""):
        return None, None

    # ── พ.ศ. (25xx) → ค.ศ. ────────────────────────────────────────────────
    be_m = re.search(r"\b(25\d{2})\b", s)
    if be_m:
        year = int(be_m.group(1)) - 543
        month = _find_month(s)
        return year, month

    # ── ค.ศ. ───────────────────────────────────────────────────────────────
    yr_m = _YEAR_PAT.search(s)
    if not yr_m:
        return None, None
    year = int(yr_m.group(1))
    month = _find_month(s)
    return year, month


def _find_month(s: str) -> int | None:
    """หาเดือนจาก string — ลองชื่อเดือนก่อน แล้วค่อยลองตัวเลข"""
    sl = s.lower()
    for name, num in _MONTH_MAP.items():
        if name in sl:
            return num
    # ตัวเลข เช่น "03/2022" "2022-03" "Q1" → month null (quarter ไม่แปลง)
    numeric = re.search(r"(?<![0-9])([01]?\d)[/\-](?:[0-9]{2,4})", s)
    if numeric:
        m = int(numeric.group(1))
        if 1 <= m <= 12:
            return m
    return None


# ─────────────────────────────────────────────
# 3. Auto categorize (keyword matching, no API)
# ─────────────────────────────────────────────

def keyword_category(text: str) -> str:
    """Keyword matching → category string"""
    t = text.lower()
    for cat, kws in _CAT_KEYWORDS.items():
        if any(kw in t for kw in kws):
            return cat
    return "other"


# ─────────────────────────────────────────────
# 4. Main conversion
# ─────────────────────────────────────────────

def df_to_events(
    df:        pd.DataFrame,
    date_col:  str,
    event_col: str,
    desc_col:  str | None = None,
) -> list[TimelineEvent]:
    """แปลง DataFrame rows → list[TimelineEvent]
    - ข้าม row ที่ไม่มีปี หรือไม่มีชื่อเหตุการณ์
    - category จาก keyword matching (ผู้ใช้แก้ได้ใน data_editor)
    - importance default = 2 (ผู้ใช้แก้ได้ใน data_editor)
    """
    events: list[TimelineEvent] = []

    for _, row in df.iterrows():
        year, month = parse_date_value(row.get(date_col))
        if year is None:
            continue

        title = str(row.get(event_col, "")).strip()
        if not title or title.lower() == "nan":
            continue

        desc = ""
        if desc_col and desc_col in df.columns:
            raw_desc = str(row.get(desc_col, "")).strip()
            desc = "" if raw_desc.lower() == "nan" else raw_desc

        cat = keyword_category(title + " " + desc)

        events.append(TimelineEvent(
            year        = year,
            month       = month,
            title       = title,
            description = desc,
            category    = cat,
            source_url  = "",
            source_name = "",
            importance  = 2,
        ))

    events.sort(key=lambda e: (e.year, e.month or 0))
    return events


# ─────────────────────────────────────────────
# 5. File reader
# ─────────────────────────────────────────────

def parse_uploaded_file(file_obj) -> tuple[pd.DataFrame, str]:
    """อ่านไฟล์ Excel หรือ CSV ที่ user upload
    คืน (DataFrame, error_message) — error_message = "" ถ้าสำเร็จ
    """
    name = getattr(file_obj, "name", "")
    try:
        if name.lower().endswith(".csv"):
            for enc in ("utf-8", "utf-8-sig", "cp874", "latin-1"):
                try:
                    df = pd.read_csv(file_obj, encoding=enc)
                    return df, ""
                except UnicodeDecodeError:
                    file_obj.seek(0)
            return pd.DataFrame(), "อ่าน CSV ไม่ได้ — ลองบันทึกเป็น UTF-8"
        else:
            df = pd.read_excel(file_obj, sheet_name=0)
            # ลบแถว/คอลัมน์ที่ว่างทั้งหมด
            df = df.dropna(how="all").dropna(axis=1, how="all")
            df.columns = [str(c).strip() for c in df.columns]
            return df, ""
    except Exception as e:
        return pd.DataFrame(), f"อ่านไฟล์ไม่ได้: {e}"
