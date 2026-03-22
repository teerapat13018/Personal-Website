"""
earnings_engine.py — Fetch earnings call transcripts
======================================================
Sources (in priority order):
  1. SEC EDGAR 8-K Exhibit 99 (free, no API key needed)
  2. Graceful error with helpful fallback links
"""

import re
import time
import requests
from datetime import datetime
from html.parser import HTMLParser

# ── Constants ────────────────────────────────────────────────────────────────

EDGAR_BASE  = "https://www.sec.gov"
DATA_BASE   = "https://data.sec.gov"

_HEADERS_SEC = {
    "User-Agent": "InvestmentDashboard/1.0 teerapat.13018@gmail.com",
    "Accept-Encoding": "gzip, deflate",
}

# Quarter → months when earnings call typically happens (after quarter end)
_CALL_MONTHS = {
    "Q1": [4, 5],    # Q1 ends Mar → call Apr-May
    "Q2": [7, 8],    # Q2 ends Jun → call Jul-Aug
    "Q3": [10, 11],  # Q3 ends Sep → call Oct-Nov
    "Q4": [1, 2, 3], # Q4 ends Dec → call Jan-Mar (next year)
}


# ── Step 1: CIK Lookup ───────────────────────────────────────────────────────

def _get_cik(ticker: str) -> str | None:
    """Resolve ticker → zero-padded 10-digit CIK via SEC company_tickers.json"""
    try:
        resp = requests.get(
            "https://www.sec.gov/files/company_tickers.json",
            headers=_HEADERS_SEC, timeout=12,
        )
        resp.raise_for_status()
        ticker_up = ticker.upper()
        for entry in resp.json().values():
            if entry.get("ticker", "").upper() == ticker_up:
                return str(entry["cik_str"]).zfill(10)
    except Exception:
        pass
    return None


# ── Step 2: List 8-K Filings ─────────────────────────────────────────────────

def _list_8k_filings(cik: str) -> list[dict]:
    """Return list of 8-K filings [{date, accession}] newest first."""
    try:
        url  = f"{DATA_BASE}/submissions/CIK{cik}.json"
        resp = requests.get(url, headers=_HEADERS_SEC, timeout=12)
        resp.raise_for_status()
        data     = resp.json()
        recent   = data.get("filings", {}).get("recent", {})
        forms    = recent.get("form", [])
        dates    = recent.get("filingDate", [])
        accs     = recent.get("accessionNumber", [])
        return [
            {"date": d, "accession": a}
            for f, d, a in zip(forms, dates, accs)
            if f == "8-K"
        ]
    except Exception:
        return []


# ── Step 3: Find Transcript Exhibit in a Filing ──────────────────────────────

class _IndexParser(HTMLParser):
    """Parse SEC filing index page to find exhibit document URLs."""

    def __init__(self):
        super().__init__()
        self.rows: list[list[tuple[str, str]]] = []  # list of rows; row = [(text, href)]
        self._row: list[tuple[str, str]] = []
        self._in_td = False
        self._td_text = ""
        self._td_href = ""

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "tr":
            self._row = []
        elif tag == "td":
            self._in_td  = True
            self._td_text = ""
            self._td_href = ""
        elif tag == "a" and self._in_td:
            self._td_href = d.get("href", "")

    def handle_endtag(self, tag):
        if tag == "td":
            self._row.append((self._td_text.strip(), self._td_href))
            self._in_td = False
        elif tag == "tr" and self._row:
            self.rows.append(self._row)
            self._row = []

    def handle_data(self, data):
        if self._in_td:
            self._td_text += data


def _find_exhibit_url(cik: str, accession: str) -> str | None:
    """
    Given an accession number, open the filing index and find the best
    exhibit that looks like an earnings call transcript.
    Priority: Exhibit 99.2 / any exhibit with 'transcript' in description.
    """
    acc_nodash = accession.replace("-", "")
    index_url  = (
        f"{EDGAR_BASE}/Archives/edgar/data/{int(cik)}"
        f"/{acc_nodash}/{accession}-index.htm"
    )
    try:
        resp = requests.get(index_url, headers=_HEADERS_SEC, timeout=12)
        if resp.status_code != 200:
            return None

        parser = _IndexParser()
        parser.feed(resp.text)

        transcript_links: list[str] = []
        ex99_links:       list[str] = []

        for row in parser.rows:
            row_text = " ".join(t for t, _ in row).lower()
            hrefs    = [h for _, h in row if h and re.search(r'\.(htm|txt)', h, re.I)]
            if not hrefs:
                continue
            href = hrefs[0]
            if not href.startswith("http"):
                href = EDGAR_BASE + href

            if "transcript" in row_text:
                transcript_links.append(href)
            elif re.search(r'ex[\s\-]?99[\.\-]?2', row_text) or "99.2" in row_text:
                ex99_links.append(href)
            elif re.search(r'ex[\s\-]?99', row_text):
                ex99_links.append(href)

        # prefer explicit transcript label, then Exhibit 99.2, then any 99
        for link in (transcript_links or ex99_links):
            return link

    except Exception:
        pass
    return None


# ── Step 4: Fetch & Parse Document ──────────────────────────────────────────

def _fetch_document(url: str, max_bytes: int = 800_000) -> str:
    """Download HTML document and return clean plain text."""
    try:
        resp = requests.get(url, headers=_HEADERS_SEC, timeout=20, stream=True)
        resp.raise_for_status()
        raw_bytes = b""
        for chunk in resp.iter_content(8192):
            raw_bytes += chunk
            if len(raw_bytes) >= max_bytes:
                break
        html = raw_bytes.decode("utf-8", errors="replace")

        # Strip boilerplate
        html = re.sub(r'<style[^>]*>.*?</style>', ' ', html, flags=re.S | re.I)
        html = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.S | re.I)
        html = re.sub(r'<[^>]+>', ' ', html)
        html = html.replace("&nbsp;", " ").replace("&amp;", "&")
        html = html.replace("&lt;", "<").replace("&gt;", ">")
        html = re.sub(r'&#\d+;', ' ', html)
        text = re.sub(r'\s+', ' ', html).strip()
        return text
    except Exception:
        return ""


def _extract_call_section(text: str) -> str:
    """
    Trim boilerplate before/after the actual earnings call.
    Looks for typical opening phrases and closing phrases.
    """
    low = text.lower()

    # Find call start
    start_markers = [
        "good morning", "good afternoon", "good evening",
        "welcome to", "thank you for joining", "ladies and gentlemen",
        "thank you for standing by", "greetings and welcome",
    ]
    start = 0
    for m in start_markers:
        idx = low.find(m)
        if 0 < idx < len(text) // 2:   # must be in first half
            start = max(0, idx - 30)
            break

    # Find call end
    end_markers = [
        "this concludes", "that concludes", "end of the call",
        "thank you for participating", "have a good day", "have a great day",
        "this conference call has concluded", "this conference has now concluded",
    ]
    end = len(text)
    for m in end_markers:
        idx = low.rfind(m)
        if idx > start:
            end = min(len(text), idx + 300)
            break

    trimmed = text[start:end].strip()
    return trimmed if len(trimmed) > 300 else text


def _looks_like_transcript(text: str) -> bool:
    """Heuristic: does this text look like an earnings call?"""
    low = text.lower()
    keywords = ["revenue", "earnings", "quarter", "operator", "analyst",
                "guidance", "eps", "net income", "fiscal"]
    hits = sum(1 for k in keywords if k in low)
    return len(text) > 1000 and hits >= 3


# ── Public API ───────────────────────────────────────────────────────────────

def fetch_transcript(ticker: str, year: int, quarter: str) -> dict:
    """
    Fetch earnings call transcript for ticker/quarter/year.

    Returns dict:
      success   : bool
      text      : str   (plain text transcript)
      source    : str   (human-readable source description)
      word_count: int
      error     : str   (non-empty on failure)
    """
    out = {"success": False, "text": "", "source": "", "word_count": 0, "error": ""}

    # ── 1. CIK ──────────────────────────────────────────────────────────────
    cik = _get_cik(ticker)
    if not cik:
        out["error"] = (
            f"❌ ไม่พบ {ticker} ใน SEC EDGAR\n"
            f"💡 ลองค้นหาด้วยตนเองที่: efts.sec.gov/LATEST/search-index?q=%22{ticker}%22&dateRange=custom"
        )
        return out

    # ── 2. 8-K list ─────────────────────────────────────────────────────────
    filings = _list_8k_filings(cik)
    if not filings:
        out["error"] = f"❌ ไม่พบ 8-K filings สำหรับ {ticker}"
        return out

    # ── 3. Filter by expected call date ─────────────────────────────────────
    call_months = _CALL_MONTHS.get(quarter, list(range(1, 13)))
    call_year   = year + 1 if quarter == "Q4" else year

    def _score(filing):
        try:
            fd = datetime.strptime(filing["date"], "%Y-%m-%d")
            yr_match = 2 if fd.year == call_year else (1 if abs(fd.year - call_year) == 1 else 0)
            mo_match = 2 if fd.month in call_months else 0
            return yr_match + mo_match
        except Exception:
            return 0

    ranked = sorted(filings, key=_score, reverse=True)[:8]

    # ── 4. Try each filing ──────────────────────────────────────────────────
    for filing in ranked:
        time.sleep(0.3)
        exhibit_url = _find_exhibit_url(cik, filing["accession"])
        if not exhibit_url:
            continue

        text = _fetch_document(exhibit_url)
        if not text or not _looks_like_transcript(text):
            continue

        text = _extract_call_section(text)
        out["success"]    = True
        out["text"]       = text
        out["source"]     = f"SEC EDGAR 8-K · {filing['date']}"
        out["word_count"] = len(text.split())
        return out

    # ── 5. Fallback message ──────────────────────────────────────────────────
    out["error"] = (
        f"❌ ไม่พบ transcript ของ {ticker} {quarter} {year} ใน SEC EDGAR\n\n"
        f"บางบริษัทไม่ได้ยื่น transcript ผ่าน EDGAR ลองหาที่:\n"
        f"• quartr.com → ค้นหา {ticker}\n"
        f"• fool.com/earnings-call-transcripts → ค้น {ticker}\n"
        f"• seekingalpha.com → ค้น \"{ticker} {quarter} {year} earnings call transcript\""
    )
    return out
