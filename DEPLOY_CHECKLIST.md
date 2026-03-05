# 🚀 Streamlit Community Cloud — Deploy Checklist

> Portfolio App | `app.py` + `investment_diary.db`
> ตรวจสอบทุกข้อก่อนกด Deploy

---

## ⚠️ ปัญหาใหญ่สุด: SQLite ไม่ persistent บน Cloud

Streamlit Community Cloud ใช้ **ephemeral filesystem** — ทุกครั้งที่ app sleep/restart ไฟล์ `.db` จะหายหมด
ต้องตัดสินใจ **1 ใน 3 วิธี** ก่อนทำอย่างอื่นต่อ:

| # | วิธี | ความยาก | เหมาะกับ |
|---|------|----------|----------|
| A | **Supabase (PostgreSQL)** — แก้ code ให้ใช้ `psycopg2` แทน SQLite | ★★★ | ใช้งานจริงระยะยาว |
| B | **GitHub commit DB** — app auto-push `.db` ขึ้น repo ผ่าน GitHub API | ★★★★ | แฮ็กมาก ไม่แนะนำ |
| C | **ยอมรับว่า data หาย** — ใช้ได้แค่ Tab วิเคราะห์, Diary/Alert ไม่ persist | ★ | demo / ทดสอบเท่านั้น |

> **แนะนำ: วิธี A (Supabase)** — มี Free Tier, SQL ใกล้เคียง SQLite มาก

---

## 📋 TODO List

### 🔴 Phase 0 — ตัดสินใจเรื่อง Database (ทำก่อนทุกอย่าง)

- [ ] เลือกวิธีจัดการ Database (A / B / C จากตารางด้านบน)
- [ ] ถ้าเลือก **Supabase**: สมัคร account ที่ [supabase.com](https://supabase.com) และสร้าง Project
- [ ] ถ้าเลือก **Supabase**: แปลง schema SQLite → PostgreSQL (5 ตาราง: diary, alerts, watchlist, portfolio, planned_trades)
- [ ] ถ้าเลือก **Supabase**: แก้ helper functions ใน app.py ให้ใช้ `psycopg2` / `supabase-py`

---

### 🟡 Phase 1 — เตรียม Repository

- [ ] สร้าง GitHub repo ใหม่ (public หรือ private ก็ได้)
- [ ] สร้างไฟล์ `.gitignore` — ต้องมี:
  ```
  investment_diary.db
  backups/
  __pycache__/
  .env
  *.pyc
  .DS_Store
  ```
- [ ] **อย่า** push ไฟล์ `.db` ขึ้น repo (ข้อมูลส่วนตัว)
- [ ] Push `app.py` ขึ้น GitHub

---

### 🟡 Phase 2 — สร้าง `requirements.txt`

- [ ] สร้างไฟล์ `requirements.txt` ในโฟลเดอร์เดียวกับ `app.py`:
  ```
  streamlit>=1.32.0
  yfinance>=0.2.40
  pandas>=2.0.0
  numpy>=1.24.0
  plotly>=5.18.0
  openpyxl>=3.1.0
  ```
  *(ถ้าเลือก Supabase ให้เพิ่ม `supabase` หรือ `psycopg2-binary`)*

- [ ] ทดสอบ install บนเครื่องสะอาด:
  ```bash
  pip install -r requirements.txt
  streamlit run app.py
  ```

---

### 🟡 Phase 3 — จัดการ Secrets

- [ ] ตรวจว่า app.py ไม่มี API key / password เขียนตรงๆ ใน code
- [ ] ถ้ามี key (เช่น Supabase URL, password): ใส่ใน **Streamlit Secrets** แทน
  - Local: สร้างไฟล์ `.streamlit/secrets.toml`:
    ```toml
    [supabase]
    url = "https://xxxx.supabase.co"
    key = "your-anon-key"
    ```
  - Cloud: กรอกใน Streamlit Cloud → App Settings → Secrets
- [ ] เพิ่ม `.streamlit/secrets.toml` ใน `.gitignore`

---

### 🟢 Phase 4 — Deploy บน Streamlit Community Cloud

- [ ] ไปที่ [share.streamlit.io](https://share.streamlit.io) → Sign in ด้วย GitHub
- [ ] กด **"New app"** → เลือก repo, branch (`main`), และไฟล์ (`app.py`)
- [ ] รอ build เสร็จ (~2-5 นาที)
- [ ] เปิด app URL ทดสอบ

---

### 🟢 Phase 5 — ทดสอบหลัง Deploy

- [ ] **Tab 1** — Chart & Analysis โหลดกราฟได้
- [ ] **Tab 2** — Portfolio แสดงข้อมูลได้ (ถ้าใช้ Supabase)
- [ ] **Tab 3** — Diary เขียน/อ่าน entry ได้
- [ ] **Tab 4** — Strategic Entry Planner โหลดกราฟ + แนวรับได้
- [ ] **Tab 5** — Advanced Analytics Benchmark / Correlation ทำงานได้
- [ ] Price Alert trigger แล้วโชว์ 🔔 ใน sidebar
- [ ] ดาวน์โหลด Excel (ETF Holdings) ได้
- [ ] ทดสอบบน Mobile (Streamlit Cloud responsive ดีมาก)

---

### 🔵 Phase 6 — Optional แต่แนะนำ

- [ ] ตั้ง Custom Domain (ถ้ามี domain ของตัวเอง)
- [ ] เพิ่ม `README.md` อธิบาย app เป็น portfolio piece
- [ ] ตั้ง GitHub Actions CI — auto syntax check ทุก push:
  ```yaml
  # .github/workflows/lint.yml
  - run: python -m py_compile app.py
  ```
- [ ] เปิด "Reboot app" schedule ใน Streamlit Cloud settings (ป้องกัน sleep)

---

## 📌 สรุปลำดับความสำคัญ

```
Phase 0 (ตัดสินใจ DB)  ←  ทำก่อน ถ้าไม่ตัดสินใจ ทำต่อไม่ได้
    ↓
Phase 1 + 2 (repo + requirements)  ←  30 นาที
    ↓
Phase 3 (secrets)  ←  ถ้าใช้ Supabase
    ↓
Phase 4 (deploy)  ←  5 นาที
    ↓
Phase 5 (test)
```

---

*สร้าง: {today} | Investment Dashboard v3*
