"""
file_timeline_engine.py  v2
───────────────────────────
Parse Excel/CSV ที่ผู้ใช้ upload → list[TimelineEvent]
- ตรวจหาคอลัมน์วันที่ / เหตุการณ์ / ประเภท / รายละเอียด อัตโนมัติ (4 cols)
- รองรับไฟล์ที่ header อยู่ใน data row (ไม่ใช่ Excel header row)
- Map category จากไฟล์ผู้ใช้ → CATEGORIES ของเรา
- รองรับ ค.ศ. / พ.ศ. / "ปี XXXX" / datetime
"""

from __future__ import annotations
import re
import pandas as pd

from timeline_engine import TimelineEvent

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────

_YEAR_PAT = re.compile(r"\b(19[5-9]\d|20[0-2]\d)\b")

_DATE_HINTS = {
    "date", "year", "ปี", "วันที่", "เดือน", "month",
    "period", "quarter", "time", "when", "เวลา", "งวด", "ไตรมาส",
}
_EVENT_HINTS = {
    "event", "title", "เหตุการณ์", "หัวข้อ", "topic", "name",
    "description", "รายละเอียด", "detail", "news", "ข่าว",
    "เรื่อง", "subject", "headline", "content", "เนื้อหา", "ชื่อ",
}
_CAT_HINTS = {
    "category", "type", "ประเภท", "หมวด", "หมวดหมู่", "kind", "class",
}
_DESC_HINTS = {
    "detail", "รายละเอียด", "description", "note", "หมายเหตุ",
    "ตัวเลข", "ข้อมูล", "summary", "สรุป",
}

# Map ค่าในคอลัมน์ประเภทของไฟล์ผู้ใช้ → category key ของเรา
_FILE_CAT_MAP: dict[str, str] = {
    # English
    "innovation":    "product",
    "product":       "product",
    "technology":    "product",
    "tech":          "product",
    "launch":        "product",
    "financial":     "ipo",
    "finance":       "ipo",
    "ipo":           "ipo",
    "split":         "ipo",
    "m&a":           "acquisition",
    "merger":        "acquisition",
    "acquisition":   "acquisition",
    "deal":          "acquisition",
    "crisis":        "crisis",
    "geopolitical":  "crisis",
    "risk":          "crisis",
    "strategic":     "milestone",
    "strategy":      "milestone",
    "milestone":     "milestone",
    "achievement":   "milestone",
    "expansion":     "expansion",
    "growth":        "expansion",
    "leadership":    "leadership",
    "management":    "leadership",
    "funding":       "funding",
    "investment":    "funding",
    "founding":      "founding",
    "pivot":         "pivot",
    "restructure":   "pivot",
    # Thai
    "นวัตกรรม":      "product",
    "ผลิตภัณฑ์":     "product",
    "การเงิน":       "ipo",
    "ควบรวม":        "acquisition",
    "ซื้อกิจการ":    "acquisition",
    "วิกฤต":         "crisis",
    "ภูมิรัฐศาสตร์": "crisis",
    "ยุทธศาสตร์":    "milestone",
    "ความสำเร็จ":    "milestone",
    "ขยายธุรกิจ":    "expansion",
    "ผู้บริหาร":     "leadership",
    "ระดมทุน":       "funding",
    "ก่อตั้ง":       "founding",
}

_MONTH_MAP: dict[str, int] = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    "january": 1, "february": 2, "march": 3, "april": 4,
    "june": 6, "july": 7, "august": 8, "september": 9,
    "october": 10, "november": 11, "december": 12,
    "ม.ค.": 1, "ก.พ.": 2, "มี.ค.": 3, "เม.ย.": 4,
    "พ.ค.": 5, "มิ.ย.": 6, "ก.ค.": 7, "ส.ค.": 8,
    "ก.ย.": 9, "ต.ค.": 10, "พ.ย.": 11, "ธ.ค.": 12,
    "มกราคม": 1, "กุมภาพันธ์": 2, "มีนาคม": 3, "เมษายน": 4,
    "พฤษภาคม": 5, "มิถุนายน": 6, "กรกฎาคม": 7, "สิงหาคม": 8,
    "กันยายน": 9, "ตุลาคม": 10, "พฤศจิกายน": 11, "ธันวาคม": 12,
}

_CAT_KEYWORDS: dict[str, list[str]] = {
    "founding":    ["found", "establish", "incorporat", "ก่อตั้ง", "เริ่มต้น"],
    "product":     ["launch", "release", "introduc", "unveil", "เปิดตัว", "ออก"],
    "acquisition": ["acquir", "merger", "buy ", "purchas", "ซื้อ", "ควบรวม"],
    "ipo":         ["ipo", "public offering", "listed", "จดทะเบียน", "split"],
    "leadership":  ["ceo", "cfo", "appoint", "resign", "ผู้บริหาร", "แต่งตั้ง", "ลาออก"],
    "funding":     ["fund", "invest", "raise", "capital", "ระดมทุน", "ลงทุน"],
    "crisis":      ["recall", "fine", "bankrupt", "lawsuit", "crisis", "วิกฤต", "ปรับ", "ฟ้อง"],
    "milestone":   ["record", "milestone", "first", "award", "สำเร็จ", "รางวัล", "แรก"],
    "expansion":   ["expand", "enter", "open", "new market", "ขยาย", "เปิดสาขา"],
    "pivot":       ["pivot", "restructur", "transform", "เปลี่ยน", "ปรับโครงสร้าง"],
}


# ─────────────────────────────────────────────
# 1. File reader (auto-detect header row)
# ─────────────────────────────────────────────

def parse_uploaded_file(file_obj) -> tuple[pd.DataFrame, str]:
    """อ่าน Excel/CSV → DataFrame
    จัดการกรณี header อยู่ใน data row (pandas อ่านได้ Unnamed:* columns)
    """
    name = getattr(file_obj, "name", "")
    try:
        if name.lower().endswith(".csv"):
            for enc in ("utf-8", "utf-8-sig", "cp874", "latin-1"):
                try:
                    df = pd.read_csv(file_obj, encoding=enc)
                    return _fix_unnamed_headers(df), ""
                except UnicodeDecodeError:
                    file_obj.seek(0)
            return pd.DataFrame(), "อ่าน CSV ไม่ได้ — ลองบันทึกเป็น UTF-8"
        else:
            df = pd.read_excel(file_obj, sheet_name=0)
            df = df.dropna(how="all").dropna(axis=1, how="all")
            df.columns = [str(c).strip() for c in df.columns]
            df = _fix_unnamed_headers(df)
            return df, ""
    except Exception as e:
        return pd.DataFrame(), f"อ่านไฟล์ไม่ได้: {e}"


def _fix_unnamed_headers(df: pd.DataFrame) -> pd.DataFrame:
    """ถ้าทุก column เป็น Unnamed:* → หา row แรกที่เป็น header จริง แล้ว promote"""
    if not all(str(c).startswith("Unnamed") for c in df.columns):
        return df  # columns ดีอยู่แล้ว

    for idx, row in df.iterrows():
        non_null = row.dropna()
        # row ที่เป็น header มักมีค่าเป็น string หลายตัว
        if len(non_null) >= 2 and sum(isinstance(v, str) for v in non_null) >= 2:
            new_cols = []
            for c in df.columns:
                val = row[c]
                new_cols.append(str(val).strip() if not pd.isna(val) else f"_col{c}")
            df.columns = new_cols
            df = df.drop(index=idx).reset_index(drop=True)
            break

    # ลบคอลัมน์ที่ว่างหรือชื่อ _col*
    df = df.loc[:, ~df.columns.str.startswith("_col")]
    return df


# ─────────────────────────────────────────────
# 2. Column detection
# ─────────────────────────────────────────────

def detect_date_event_cols(
    df: pd.DataFrame,
) -> tuple[str | None, str | None, str | None, str | None]:
    """ตรวจหาคอลัมน์ date / event / category / description อัตโนมัติ
    คืน (date_col, event_col, cat_col, desc_col)
    """
    cols = list(df.columns)
    date_col = event_col = cat_col = desc_col = None

    # รอบ 1: datetime dtype → date แน่นอน
    for col in cols:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            date_col = col
            break

    # รอบ 2: ชื่อคอลัมน์
    for col in cols:
        cl = str(col).lower().strip()
        if date_col  is None and any(h in cl for h in _DATE_HINTS):  date_col  = col
        if event_col is None and any(h in cl for h in _EVENT_HINTS): event_col = col
        if cat_col   is None and any(h in cl for h in _CAT_HINTS):   cat_col   = col
        if desc_col  is None and any(h in cl for h in _DESC_HINTS):  desc_col  = col

    # รอบ 3: content-based สำหรับ date
    if date_col is None:
        for col in cols:
            sample = df[col].dropna().head(15).astype(str)
            if sample.apply(lambda x: bool(_YEAR_PAT.search(x))).sum() >= max(3, len(sample) // 2):
                date_col = col
                break

    # รอบ 4: longest text → event (ถ้ายังไม่เจอ)
    if event_col is None:
        str_cols = [c for c in cols if c not in (date_col, cat_col, desc_col)
                    and df[c].dtype == object
                    and df[c].dropna().astype(str).str.len().mean() > 5]
        if str_cols:
            event_col = max(str_cols, key=lambda c: df[c].dropna().astype(str).str.len().mean())

    # Fallback
    if date_col  is None and len(cols) >= 1: date_col  = cols[0]
    if event_col is None and len(cols) >= 2:
        event_col = next((c for c in cols if c != date_col), None)

    return date_col, event_col, cat_col, desc_col


# ─────────────────────────────────────────────
# 3. Date parsing
# ─────────────────────────────────────────────

def parse_date_value(val) -> tuple[int | None, int | None]:
    """แปลง value → (year, month) รองรับหลาย format"""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None, None
    if hasattr(val, "year"):           # datetime / Timestamp
        return int(val.year), int(val.month)

    s = str(val).strip()
    if not s or s.lower() in ("nan", "none", ""):
        return None, None

    # พ.ศ. 25xx → ค.ศ.
    be = re.search(r"\b(25\d{2})\b", s)
    if be:
        return int(be.group(1)) - 543, _find_month(s)

    yr = _YEAR_PAT.search(s)
    if not yr:
        return None, None
    return int(yr.group(1)), _find_month(s)


def _find_month(s: str) -> int | None:
    sl = s.lower()
    for name, num in _MONTH_MAP.items():
        if name in sl:
            return num
    m = re.search(r"(?<![0-9])([01]?\d)[/\-](?:[0-9]{2,4})", s)
    if m:
        n = int(m.group(1))
        if 1 <= n <= 12:
            return n
    return None


# ─────────────────────────────────────────────
# 4. Category mapping
# ─────────────────────────────────────────────

def map_category(file_cat_val: str | None, title: str = "", desc: str = "") -> str:
    """Map ค่าในไฟล์ → category key
    ลำดับ: ค่าในไฟล์ก่อน → fallback keyword matching ถ้าหาไม่เจอ
    """
    if file_cat_val and str(file_cat_val).lower() not in ("nan", "none", ""):
        cl = str(file_cat_val).lower().strip()
        # exact match
        if cl in _FILE_CAT_MAP:
            return _FILE_CAT_MAP[cl]
        # partial match
        for key, cat in _FILE_CAT_MAP.items():
            if key in cl:
                return cat

    # fallback: keyword matching จาก title + desc
    t = (title + " " + desc).lower()
    for cat, kws in _CAT_KEYWORDS.items():
        if any(kw in t for kw in kws):
            return cat
    return "other"


# ─────────────────────────────────────────────
# 5. Main conversion
# ─────────────────────────────────────────────

def df_to_events(
    df:        pd.DataFrame,
    date_col:  str,
    event_col: str,
    cat_col:   str | None = None,
    desc_col:  str | None = None,
) -> list[TimelineEvent]:
    """แปลง DataFrame → list[TimelineEvent]
    ทุก row ที่มีวันที่และชื่อเหตุการณ์จะถูก include (importance=2 ทั้งหมด)
    """
    from timeline_engine import CATEGORIES
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
            raw = str(row.get(desc_col, "")).strip()
            desc = "" if raw.lower() == "nan" else raw

        # ดึงค่าจากคอลัมน์ประเภท (ถ้ามี)
        file_cat = str(row.get(cat_col, "")) if cat_col and cat_col in df.columns else ""
        cat = map_category(file_cat, title, desc)
        if cat not in CATEGORIES:
            cat = "other"

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
