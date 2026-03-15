"""
timeline_engine.py
──────────────────
Company Timeline Generator
- ดึงข้อมูลจาก Tavily (web search) + Wikipedia API
- ส่งข้อมูลดิบให้ Groq (Llama) จัดหมวดหมู่และแปลเป็นไทย
- คืนค่า list of TimelineEvent พร้อม render
"""

from __future__ import annotations
import json
import re
import time
import requests
from dataclasses import dataclass, field
from typing import Optional

# ─────────────────────────────────────────────
# Data model
# ─────────────────────────────────────────────

CATEGORIES = {
    "founding":    ("🏗️", "ก่อตั้งบริษัท",    "#7c3aed"),
    "product":     ("🚀", "ผลิตภัณฑ์",          "#0ea5e9"),
    "funding":     ("💰", "การระดมทุน",          "#f59e0b"),
    "leadership":  ("👤", "ผู้บริหาร",           "#8b5cf6"),
    "crisis":      ("⚠️", "วิกฤต / ความท้าทาย", "#ef4444"),
    "pivot":       ("🔄", "เปลี่ยนทิศทาง",       "#f97316"),
    "milestone":   ("🏆", "ความสำเร็จ",          "#22c55e"),
    "expansion":   ("🌍", "การขยายธุรกิจ",       "#06b6d4"),
    "acquisition": ("🤝", "ควบรวมกิจการ",        "#a855f7"),
    "ipo":         ("📈", "IPO / การเงิน",        "#10b981"),
    "other":       ("📌", "อื่นๆ",               "#6b7280"),
}

@dataclass
class TimelineEvent:
    year:        int
    month:       Optional[int]
    title:       str                      # ภาษาไทย
    description: str                      # ภาษาไทย ≤ 3 ประโยค
    category:    str                      # key ใน CATEGORIES
    source_url:  str  = ""
    source_name: str  = ""
    importance:  int  = 2                 # 1=minor 2=normal 3=major

    @property
    def icon(self) -> str:
        return CATEGORIES.get(self.category, CATEGORIES["other"])[0]

    @property
    def category_label(self) -> str:
        return CATEGORIES.get(self.category, CATEGORIES["other"])[1]

    @property
    def color(self) -> str:
        return CATEGORIES.get(self.category, CATEGORIES["other"])[2]

    @property
    def date_label(self) -> str:
        month_th = ["", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
                    "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
        if self.month:
            return f"{month_th[self.month]} {self.year}"
        return str(self.year)


# ─────────────────────────────────────────────
# 1. Wikipedia — ดึงเฉพาะ section ที่ต้องการ
# ─────────────────────────────────────────────

# Section ที่ต้องการดึง (lowercase matching)
_WIKI_TARGET_SECTIONS = {
    "history", "company history", "corporate history", "background",
    "timeline", "milestones", "products", "services",
    "products and services", "acquisitions", "mergers and acquisitions",
    "expansion", "growth", "recent history", "recent developments",
    "business overview", "operations",
}

def _extract_wiki_sections(full_text: str) -> str:
    """แยก section จาก Wikipedia plaintext แล้วเลือกเฉพาะ section ที่ตรงกับ _WIKI_TARGET_SECTIONS"""
    # plaintext ของ Wikipedia ใช้ == Header == และ === Sub === เป็น section markers
    sections: list[tuple[str, str]] = []
    current_header = "_intro"
    current_lines:  list[str] = []

    for line in full_text.split("\n"):
        m = re.match(r"^(={2,4})\s*(.+?)\s*\1\s*$", line)
        if m:
            sections.append((current_header, "\n".join(current_lines).strip()))
            current_header = m.group(2).strip()
            current_lines  = []
        else:
            current_lines.append(line)
    sections.append((current_header, "\n".join(current_lines).strip()))

    selected: list[str] = []
    total_chars = 0
    MAX_TOTAL   = 16_000
    MAX_SECTION = 5_000   # cap per section เพื่อไม่ให้ section ใดยาวเกินไป

    # เก็บ intro เสมอ (ย่อหน้าแรกสุด ~1,000 chars)
    if sections and sections[0][0] == "_intro":
        intro_snippet = sections[0][1][:1_200]
        selected.append(f"[Introduction]\n{intro_snippet}")
        total_chars += len(intro_snippet)

    # เก็บ section ที่ตรงกับ target
    for header, content in sections[1:]:
        if total_chars >= MAX_TOTAL:
            break
        h_lower = header.lower()
        if h_lower in _WIKI_TARGET_SECTIONS or any(t in h_lower for t in _WIKI_TARGET_SECTIONS):
            chunk = content[:MAX_SECTION]
            selected.append(f"[{header}]\n{chunk}")
            total_chars += len(chunk)

    # ถ้าหาไม่เจอ section เลย ให้ fallback เป็น raw text 8,000 chars
    if len(selected) <= 1:
        return full_text[:8_000]

    return "\n\n".join(selected)


def _fetch_wikipedia(company_name: str) -> str:
    """ดึง Wikipedia เฉพาะ section History / Products / Acquisitions"""
    try:
        api_url = "https://en.wikipedia.org/w/api.php"

        # Step 1 — ค้นหาชื่อบทความ
        r = requests.get(api_url, params={
            "action": "query", "list": "search",
            "srsearch": company_name, "srlimit": 3, "format": "json",
        }, timeout=10)
        results = r.json().get("query", {}).get("search", [])
        if not results:
            return ""
        title = results[0]["title"]

        # Step 2 — ดึงเนื้อหาทั้งบทความเป็น plaintext (ไม่จำกัดที่นี่ จำกัดในฟังก์ชัน extract)
        r2 = requests.get(api_url, params={
            "action": "query", "prop": "extracts",
            "exintro": False, "explaintext": True,
            "titles": title, "format": "json",
        }, timeout=15)
        pages = r2.json().get("query", {}).get("pages", {})
        full_text = ""
        for page in pages.values():
            full_text = page.get("extract", "")
            break

        if not full_text:
            return ""

        # Step 3 — ดึงเฉพาะ section ที่ต้องการ
        return _extract_wiki_sections(full_text)

    except Exception:
        return ""


# ─────────────────────────────────────────────
# 2. Tavily — web search
# ─────────────────────────────────────────────

def _filter_date_sentences(content: str, max_chars: int = 1_000) -> str:
    """ดึงเฉพาะประโยคที่มีปี พ.ศ./ค.ศ. อยู่ — ลด token โดยไม่เสียข้อมูลวันที่"""
    year_pat = re.compile(r"\b(19[5-9]\d|20[0-2]\d)\b")
    # แบ่งประโยคด้วย . ! ? แต่ไม่ตัดกลางตัวเลขเช่น "$2.5B"
    sentences = re.split(r"(?<=[a-zA-Z\d])\.\s+(?=[A-Z])", content)
    # เก็บ 2 ประโยคแรกไว้เสมอ (context ของบทความ) + ประโยคที่มีปี
    first_two   = sentences[:2]
    dated       = [s for s in sentences[2:] if year_pat.search(s)]
    combined    = first_two + dated
    result      = " ".join(combined)
    return result[:max_chars]


def _fetch_tavily(company_name: str, api_key: str) -> list[dict]:
    """ดึงข่าว/บทความจาก Tavily แบ่งเป็น early (น้อย) และ recent (เยอะ)"""
    import datetime
    from tavily import TavilyClient
    client = TavilyClient(api_key=api_key)

    cy = datetime.datetime.now().year   # current year

    # (query, max_results)
    # Early history — 3 results ต่อ query
    early_queries: list[tuple[str, int]] = [
        (f"{company_name} founding history origin early years IPO", 3),
        (f"{company_name} key milestones turning points 1980s 1990s 2000s", 3),
    ]
    # Recent — 5 results ต่อ query เน้นปีล่าสุด
    recent_queries: list[tuple[str, int]] = [
        (f"{company_name} acquisitions mergers deals partnerships growth", 4),
        (f"{company_name} new products AI technology innovation {cy-3} {cy-2} {cy-1} {cy}", 5),
        (f"{company_name} strategy business expansion {cy-4} {cy-3} {cy-2}", 4),
        (f"{company_name} latest news breakthroughs leadership {cy-1} {cy}", 5),
    ]

    all_results: list[dict] = []
    seen_urls:   set[str]   = set()

    for q, n in early_queries + recent_queries:
        try:
            resp = client.search(query=q, search_depth="basic", max_results=n)
            for r in resp.get("results", []):
                url = r.get("url", "")
                if url not in seen_urls:
                    seen_urls.add(url)
                    raw_content = r.get("content", "")
                    all_results.append({
                        "title":   r.get("title", ""),
                        "url":     url,
                        # กรองเฉพาะประโยคที่มีปี → ลด token ~60%
                        "content": _filter_date_sentences(raw_content, max_chars=1_000),
                    })
        except Exception as _te:
            all_results.append({"title": f"[Tavily error: {_te}]", "url": "", "content": ""})
        time.sleep(0.3)

    return all_results


# ─────────────────────────────────────────────
# 3. Groq — parse & categorize → Thai
# ─────────────────────────────────────────────

def _build_system_prompt() -> str:
    import datetime
    cy = datetime.datetime.now().year
    return f"""
You are a business historian assistant. Today's year is {cy}.
Your task: extract key historical events about a company from the provided text,
then return them as a JSON array. Output ONLY valid JSON — no markdown, no explanation.

Each event object must have these fields:
  year (int), month (int or null),
  title_th (Thai string ≤ 10 words),
  description_th (Thai string, 2–3 sentences — BE SPECIFIC: name the actual product, deal size, person, country),
  category (one of: founding, product, funding, leadership, crisis, pivot, milestone, expansion, acquisition, ipo, other),
  source_url (string or ""), source_name (string or ""),
  importance (1=minor, 2=normal, 3=major turning point)

TIME-WEIGHTED extraction rules (CRITICAL):
- BEFORE {cy - 14} (before ~10 years ago): include ONLY the 8–10 most important events
  → Only founding, IPO, first major product, biggest acquisition, major pivot/crisis — skip minor ones
- {cy - 14} to {cy - 5}: include up to 12 events — product lines, expansions, key M&A
- {cy - 5} to {cy} (last 5 years): include ALL significant events, aim for 10–15 events minimum
  → Be especially thorough here: AI products, new business lines, leadership changes, major deals

Total target: 30–40 events. Distribution should be roughly 20% historical / 30% mid / 50% recent.

Additional rules:
- Translate ALL text to Thai
- CRITICAL: MUST include events up to {cy} — never stop before the current year
- Be SPECIFIC: e.g. "Microsoft Copilot" not "AI assistant", "ซื้อ Activision $68.7B" not "ซื้อบริษัทเกม"
- If multiple sources describe the SAME event, include it ONLY ONCE (use the most detailed description)
- Do NOT include near-duplicate events with the same topic in the same year
- Sort by year ascending
- If year is unknown, estimate — do not skip

Return format example:
[
  {{
    "year": 1994, "month": null,
    "title_th": "ก่อตั้ง Amazon ในโรงรถ",
    "description_th": "Jeff Bezos ลาออกจากงาน Wall Street เพื่อก่อตั้ง Amazon ในโรงรถที่ Bellevue รัฐ Washington โดยเริ่มต้นจากการขายหนังสือออนไลน์ แรงบันดาลใจมาจากการเห็นการเติบโตของอินเทอร์เน็ต 2,300% ต่อปี",
    "category": "founding",
    "source_url": "", "source_name": "Wikipedia",
    "importance": 3
  }}
]
"""

def _parse_with_groq(
    company_name: str,
    wiki_text: str,
    tavily_results: list[dict],
    api_key: str,
) -> list[TimelineEvent]:
    """ส่งข้อมูลดิบให้ Groq (Llama) แปลงเป็น TimelineEvent list"""
    from groq import Groq

    # สร้าง context จาก raw data
    context_parts = [f"Company: {company_name}\n"]

    if wiki_text:
        context_parts.append(f"=== Wikipedia (History & Products sections) ===\n{wiki_text}\n")

    for i, r in enumerate(tavily_results[:18]):
        context_parts.append(
            f"=== Article {i+1}: {r['title']} ({r['url']}) ===\n{r['content']}\n"
        )

    context = "\n".join(context_parts)

    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model    = "meta-llama/llama-4-scout-17b-16e-instruct",
        messages = [
            {"role": "system", "content": _build_system_prompt()},
            {"role": "user",   "content": context},
        ],
        temperature = 0.3,
        max_tokens  = 6000,
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$",          "", raw)

    events_json: list[dict] = json.loads(raw)

    events: list[TimelineEvent] = []
    for e in events_json:
        try:
            cat = e.get("category", "other")
            if cat not in CATEGORIES:
                cat = "other"

            # Find source_url from tavily results if not provided
            src_url  = e.get("source_url", "")
            src_name = e.get("source_name", "")
            if not src_url:
                # Try to match with tavily results by scanning title keywords
                title_words = e.get("title_th", "").split()[:3]
                for r in tavily_results:
                    if any(w.lower() in r["content"].lower() for w in title_words if len(w) > 3):
                        src_url  = r["url"]
                        src_name = r["title"][:60]
                        break

            events.append(TimelineEvent(
                year        = int(e["year"]),
                month       = e.get("month"),
                title       = e.get("title_th", ""),
                description = e.get("description_th", ""),
                category    = cat,
                source_url  = src_url,
                source_name = src_name,
                importance  = int(e.get("importance", 2)),
            ))
        except (KeyError, ValueError, TypeError):
            continue

    events.sort(key=lambda x: (x.year, x.month or 0))
    return events


# ─────────────────────────────────────────────
# 4. Public API
# ─────────────────────────────────────────────

def _clean_search_name(company_name: str) -> str:
    """ตัด suffix และ ticker ออกเพื่อให้ search ได้ผลดีขึ้น"""
    import re
    # ตัด (TICKER) ออก เช่น "Amazon.com, Inc. (AMZN)" → "Amazon.com, Inc."
    name = re.sub(r'\s*\([A-Z]{1,5}\)\s*$', '', company_name).strip()
    # ตัด suffix บริษัท
    for suffix in [", Inc.", " Inc.", ", Corp.", " Corp.", " Corporation",
                   ", Ltd.", " Ltd.", ", LLC", " LLC", ", PLC", " PLC",
                   ".com", ", N.V.", " N.V."]:
        name = name.replace(suffix, "")
    return name.strip().strip(",").strip()


def _deduplicate_events(events: list[TimelineEvent]) -> list[TimelineEvent]:
    """ลบ event ซ้ำโดยเปรียบเทียบ year + title similarity"""
    result: list[TimelineEvent] = []
    for ev in events:
        is_dup = False
        for kept in result:
            if kept.year == ev.year:
                t1 = set(kept.title.lower().split())
                t2 = set(ev.title.lower().split())
                if t1 and t2:
                    overlap = len(t1 & t2) / min(len(t1), len(t2))
                    if overlap >= 0.5:          # คำซ้ำ 50%+ = duplicate
                        is_dup = True
                        if ev.importance > kept.importance:
                            result.remove(kept)
                            result.append(ev)
                        break
        if not is_dup:
            result.append(ev)
    result.sort(key=lambda x: (x.year, x.month or 0))
    return result


def generate_timeline(
    company_name:   str,
    tavily_api_key: str,
    groq_api_key:   str,
) -> tuple[list[TimelineEvent], str]:
    """
    Main function — คืนค่า (events, error_message)
    error_message เป็น "" ถ้าไม่มี error
    """
    if not company_name.strip():
        return [], "กรุณากรอกชื่อบริษัท"

    # ทำความสะอาดชื่อก่อนใช้ search
    search_name = _clean_search_name(company_name)

    # Step 1: ดึงข้อมูล
    wiki_text      = _fetch_wikipedia(search_name)
    tavily_results = _fetch_tavily(search_name, tavily_api_key)

    # กรองเฉพาะ error entries ออกก่อนเช็ค
    real_results = [r for r in tavily_results if not r["title"].startswith("[Tavily error")]
    tavily_errors = [r["title"] for r in tavily_results if r["title"].startswith("[Tavily error")]

    if not wiki_text and not real_results:
        err_detail = f" ({tavily_errors[0]})" if tavily_errors else ""
        return [], f"ไม่พบข้อมูลของบริษัทนี้{err_detail} — ลองปรับ Ticker หรือตรวจสอบ Tavily API key"

    tavily_results = real_results

    # Step 2: Parse ด้วย Groq
    try:
        events = _parse_with_groq(company_name, wiki_text, tavily_results, groq_api_key)
    except json.JSONDecodeError as e:
        return [], f"Groq คืนค่า JSON ไม่ถูกต้อง: {e}"
    except Exception as e:
        return [], f"เกิดข้อผิดพลาด: {e}"

    if not events:
        return [], "Groq สกัดข้อมูลไม่ได้ — ลองบริษัทที่มีชื่อเสียงมากกว่านี้"

    # Step 3: Deduplication
    events = _deduplicate_events(events)

    return events, ""


def render_timeline_html(
    events: list[TimelineEvent],
    filter_cats: list[str] | None  = None,
    year_min:    int | None        = None,
    year_max:    int | None        = None,
) -> str:
    """สร้าง HTML string ของ timeline พร้อม filter"""

    filtered = events
    if filter_cats:
        filtered = [e for e in filtered if e.category in filter_cats]
    if year_min is not None:
        filtered = [e for e in filtered if e.year >= year_min]
    if year_max is not None:
        filtered = [e for e in filtered if e.year <= year_max]

    if not filtered:
        return "<p style='color:#888;text-align:center;padding:40px'>ไม่มี event ในช่วงที่เลือก</p>"

    items_html = ""
    for e in filtered:
        importance_scale = {1: "0.85", 2: "1.0", 3: "1.08"}.get(e.importance, "1.0")
        border_width     = {1: "2px",  2: "3px", 3: "4px"}.get(e.importance, "3px")

        source_html = ""
        if e.source_url:
            domain = re.sub(r"https?://(www\.)?", "", e.source_url).split("/")[0]
            source_html = (
                f'<a href="{e.source_url}" target="_blank" '
                f'style="color:{e.color};font-size:0.72rem;text-decoration:none;opacity:0.8">'
                f'🔗 {e.source_name or domain}</a>'
            )

        items_html += f"""
<div class="tl-item" style="--event-color:{e.color}; transform:scale({importance_scale});">
  <div class="tl-dot" style="border-color:{e.color};border-width:{border_width}">
    <span class="tl-icon">{e.icon}</span>
  </div>
  <div class="tl-card" style="border-left:3px solid {e.color}">
    <div class="tl-date">{e.date_label}</div>
    <div class="tl-badge" style="background:{e.color}22;color:{e.color};border:1px solid {e.color}44">
      {e.icon} {e.category_label}
    </div>
    <div class="tl-title">{e.title}</div>
    <div class="tl-desc">{e.description}</div>
    <div class="tl-source">{source_html}</div>
  </div>
</div>
"""

    css = """
<style>
.tl-wrap {
  position: relative;
  padding: 8px 0 8px 52px;
  max-width: 780px;
  margin: 0 auto;
}
.tl-wrap::before {
  content: '';
  position: absolute;
  left: 20px;
  top: 0; bottom: 0;
  width: 2px;
  background: linear-gradient(180deg, #7c3aed44, #0ea5e944, #22c55e44);
}
.tl-item {
  position: relative;
  margin-bottom: 28px;
  transition: transform 0.2s;
  transform-origin: left center;
}
.tl-item:hover { transform: scale(1.02) !important; }
.tl-dot {
  position: absolute;
  left: -40px;
  top: 12px;
  width: 36px; height: 36px;
  border-radius: 50%;
  border: 3px solid;
  background: #0d0d1a;
  display: flex; align-items: center; justify-content: center;
  font-size: 1rem;
  box-shadow: 0 0 10px var(--event-color, #7c3aed44);
}
.tl-card {
  background: #12122a;
  border-radius: 10px;
  padding: 14px 16px;
  box-shadow: 0 2px 12px #0004;
}
.tl-date {
  font-size: 0.75rem;
  color: #888;
  margin-bottom: 4px;
  font-weight: 600;
  letter-spacing: 0.05em;
}
.tl-badge {
  display: inline-block;
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: 20px;
  margin-bottom: 6px;
  font-weight: 600;
}
.tl-title {
  font-size: 1rem;
  font-weight: 700;
  color: #e8e8f0;
  margin-bottom: 6px;
  line-height: 1.4;
}
.tl-desc {
  font-size: 0.85rem;
  color: #aaa;
  line-height: 1.6;
  margin-bottom: 6px;
}
.tl-source { margin-top: 4px; }
@media (max-width: 640px) {
  .tl-wrap { padding-left: 40px; }
  .tl-dot  { left: -32px; width: 28px; height: 28px; font-size: 0.8rem; }
  .tl-title { font-size: 0.9rem; }
}
</style>
"""

    return css + f'<div class="tl-wrap">{items_html}</div>'
