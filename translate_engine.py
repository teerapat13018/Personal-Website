"""
translate_engine.py — Chunk & translate earnings call transcripts with Groq
============================================================================
Pipeline:
  1. split_chunks()  : break text into ~700-word sentence-boundary chunks
  2. translate_transcript() : call Groq for each chunk (EN → TH)
  3. generate_mindmap_data() : ask Groq to produce markmap-compatible markdown
"""

import re
import time
from typing import Callable

CHUNK_WORDS = 700       # target words per translation chunk
GROQ_MODEL  = "meta-llama/llama-4-scout-17b-16e-instruct"


# ── 1. Chunker ───────────────────────────────────────────────────────────────

def split_chunks(text: str, chunk_words: int = CHUNK_WORDS) -> list[str]:
    """
    Split text into chunks of ~chunk_words words at sentence boundaries.
    Avoids cutting mid-sentence so translation quality stays high.
    """
    # Normalise whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Split at sentence boundaries (. ! ?) followed by whitespace
    sentences = re.split(r'(?<=[.!?])\s+', text)

    chunks: list[str] = []
    current: list[str] = []
    count = 0

    for sent in sentences:
        wc = len(sent.split())
        if count + wc > chunk_words and current:
            chunks.append(" ".join(current))
            current = [sent]
            count   = wc
        else:
            current.append(sent)
            count  += wc

    if current:
        chunks.append(" ".join(current))

    return [c for c in chunks if c.strip()]


# ── 2. Translate ─────────────────────────────────────────────────────────────

def translate_transcript(
    text: str,
    groq_key: str,
    ticker: str = "",
    progress_callback: Callable[[int, int], None] | None = None,
) -> dict:
    """
    Translate full transcript from English → Thai using Groq.

    Args:
        text             : raw English transcript
        groq_key         : Groq API key
        ticker           : company ticker (for context in prompt)
        progress_callback: called with (chunks_done, chunks_total) each iteration

    Returns dict:
        success      : bool
        translated   : str  (full Thai text)
        chunks_total : int
        error        : str
    """
    result = {"success": False, "translated": "", "chunks_total": 0, "error": ""}

    if not groq_key:
        result["error"] = "❌ ไม่พบ GROQ_API_KEY"
        return result

    try:
        from groq import Groq
        client = Groq(api_key=groq_key)
    except Exception as e:
        result["error"] = f"❌ เชื่อมต่อ Groq ไม่ได้: {e}"
        return result

    chunks = split_chunks(text)
    total  = len(chunks)
    result["chunks_total"] = total

    if progress_callback:
        progress_callback(0, total)

    parts: list[str] = []

    for i, chunk in enumerate(chunks):
        try:
            prompt = (
                f"คุณเป็นนักแปลการเงินมืออาชีพ แปล Earnings Call transcript "
                f"ของ {ticker} ต่อไปนี้จากภาษาอังกฤษเป็นภาษาไทย\n\n"
                f"กฎการแปล:\n"
                f"- แปลให้ครบทุกประโยค ไม่ตัดทอน\n"
                f"- รักษาชื่อบุคคล ชื่อบริษัท ตัวเลข ศัพท์เทคนิคเป็นภาษาอังกฤษ\n"
                f"- ภาษาไทยต้องอ่านง่าย เป็นธรรมชาติ\n"
                f"- ไม่ต้องใส่คำอธิบายเพิ่ม — แปลตรงๆ เท่านั้น\n\n"
                f"ส่วนที่ {i + 1}/{total}:\n{chunk}"
            )
            resp = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.15,
                max_tokens=1600,
            )
            parts.append(resp.choices[0].message.content.strip())
            time.sleep(0.6)   # respect rate limit

        except Exception as e:
            # Don't abort — insert error marker and continue
            parts.append(
                f"[⚠️ แปลส่วนที่ {i + 1} ไม่สำเร็จ: {e}]\n\n"
                f"--- ต้นฉบับ ---\n{chunk}"
            )

        if progress_callback:
            progress_callback(i + 1, total)

    result["success"]    = True
    result["translated"] = "\n\n---\n\n".join(parts)
    return result


# ── 3. Mindmap Generator ─────────────────────────────────────────────────────

def generate_mindmap_data(
    text: str,
    groq_key: str,
    ticker: str,
    quarter: str,
    year: int,
) -> dict:
    """
    Summarise transcript and produce markmap-compatible markdown for mindmap.

    Returns dict:
        success  : bool
        markdown : str  (markmap markdown with # ## ### hierarchy)
        error    : str
    """
    result = {"success": False, "markdown": "", "error": ""}

    if not groq_key:
        result["error"] = "❌ ไม่พบ GROQ_API_KEY"
        return result

    try:
        from groq import Groq
        client = Groq(api_key=groq_key)
    except Exception as e:
        result["error"] = f"❌ เชื่อมต่อ Groq ไม่ได้: {e}"
        return result

    # Feed first ~4 000 words to keep within token limit
    sample = " ".join(text.split()[:4000])

    prompt = f"""วิเคราะห์ Earnings Call transcript ของ {ticker} {quarter} {year} แล้วสรุปเป็น mindmap

ใช้ markdown heading hierarchy ดังนี้ (ห้ามใส่ content นอกโครงสร้าง):

# {ticker} {quarter} {year} Earnings Call

## 📈 Financial Highlights
### (ตัวชี้วัดสำคัญ เช่น Revenue, EPS, Margin พร้อมตัวเลขจริง)

## 🔭 Guidance & Outlook
### (เป้าหมาย revenue, margin, หรือ guidance ที่ management ให้ไว้)

## 🚀 Growth Drivers
### (ปัจจัยขับเคลื่อนการเติบโต)

## ⚠️ ความเสี่ยงและความท้าทาย
### (risk factors ที่ management กล่าวถึง)

## 💬 Q&A สำคัญ
### (สรุปคำถาม-คำตอบที่น่าสนใจจาก analyst)

## 💡 Key Takeaways
### (สรุปประเด็นสำคัญ 3-5 ข้อ)

กฎ:
- แต่ละ bullet (###) ต้องกระชับ ไม่เกิน 15 คำ
- ใส่ตัวเลขจริงจาก transcript (เช่น revenue $X.Xbn, +XX% YoY)
- เขียนภาษาไทย ยกเว้นคำศัพท์เทคนิคและตัวเลข
- ไม่ต้องใส่ backtick หรือ code block

Transcript:
{sample}"""

    try:
        resp = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.25,
            max_tokens=1200,
        )
        md = resp.choices[0].message.content.strip()
        # Strip accidental code fences
        md = re.sub(r'^```[^\n]*\n?', '', md, flags=re.M)
        md = md.replace("```", "")
        result["success"]  = True
        result["markdown"] = md.strip()
    except Exception as e:
        result["error"] = f"❌ สร้าง mindmap ไม่สำเร็จ: {e}"

    return result
