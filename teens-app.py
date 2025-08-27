
import streamlit as st
import sqlite3
from datetime import datetime, date, time
import pandas as pd
import random
import requests
import json

# ---------------- Config ----------------
DB_PATH = "teens_app.db"
BACKGROUND_IMG = "h"  # your Imgur image

# ---------------- Styling (background + overlay) ----------------
st.set_page_config(page_title="Teens App", layout="wide", page_icon="✨")
page_css = f"""
<style>
.stApp {{
  background-image: url("{BACKGROUND_IMG}");
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  position: relative;
}}
/* dark overlay so text is readable */
.stApp::before {{
  content: "";
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.45);
  z-index: -1;
}}
/* make main content sit above overlay */
[data-testid="stAppViewContainer"] > .main {{
  position: relative;
  z-index: 1;
}}
</style>
"""
st.markdown(page_css, unsafe_allow_html=True)

# ---------------- Database helpers ----------------
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

def init_db():
    with get_conn() as conn:
        c = conn.cursor()
        # social links
        c.execute("""
            CREATE TABLE IF NOT EXISTS social_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT,
                username TEXT,
                url TEXT,
                added_at TEXT
            )
        """)
        # schedule / tasks
        c.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                subject TEXT,
                due_date TEXT,
                due_time TEXT,
                priority TEXT,
                status TEXT DEFAULT 'Pending',
                created_at TEXT
            )
        """)
        # question bank
        c.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT,
                question TEXT,
                option_a TEXT,
                option_b TEXT,
                option_c TEXT,
                option_d TEXT,
                correct_option TEXT,
                created_at TEXT
            )
        """)
        # quiz attempts
        c.execute("""
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT,
                total INTEGER,
                correct INTEGER,
                taken_at TEXT
            )
        """)
        # chapters / study material
        c.execute("""
            CREATE TABLE IF NOT EXISTS chapters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT,
                chapter TEXT,
                created_at TEXT
            )
        """)
        # notes
        c.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                content TEXT,
                created_at TEXT
            )
        """)
        conn.commit()

init_db()

# ---------------- Utilities ----------------
def now_iso():
    return datetime.utcnow().isoformat()

def run_query(query, params=(), fetch=False):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        if fetch:
            return cur.fetchall()

# ---------------- Social Hub ----------------
def ui_social_hub():
    st.subheader("🌍 Social Hub")
    st.caption("Store your social profiles (platform, handle, url).")
    with st.form("add_social", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            platform = st.text_input("Platform (Instagram, X, TikTok...)", placeholder="Instagram")
            username = st.text_input("Username / Handle", placeholder="@yourname")
        with col2:
            url = st.text_input("Profile URL", placeholder="https://instagram.com/yourname")
        if st.form_submit_button("Save Platform") and platform and url:
            run_query(
                "INSERT INTO social_links (platform, username, url, added_at) VALUES (?, ?, ?, ?)",
                (platform.strip(), username.strip(), url.strip(), now_iso()),
            )
            st.success("Saved!")

    st.divider()
    rows = run_query("SELECT id, platform, username, url, added_at FROM social_links ORDER BY id DESC", fetch=True)
    if rows:
        for rid, plat, uname, url, added in rows:
            with st.container():
                c1, c2, c3 = st.columns([3,4,2])
                c1.markdown(f"**{plat}** {f'— {uname}' if uname else ''}")
                c2.write(url)
                c3.caption(f"Added {added.split('T')[0]}")
                col_a, col_b = st.columns(2)
                if col_a.button("Open", key=f"open_{rid}"):
                    st.experimental_set_query_params()  # harmless placeholder
                    st.markdown(f"[Open link]({url})")
                if col_b.button("Delete", key=f"del_social_{rid}"):
                    run_query("DELETE FROM social_links WHERE id=?", (rid,))
                    st.toast("Deleted")
                    st.experimental_rerun()
    else:
        st.info("No social links yet — add one above.")

# ---------------- Scheduler ----------------
def ui_scheduler():
    st.subheader("📅 Scheduler")
    st.caption("Add study sessions, deadlines or reminders.")
    with st.form("add_task", clear_on_submit=True):
        t1, t2 = st.columns([3,2])
        with t1:
            title = st.text_input("Title", placeholder="Read Biology Ch 3")
            description = st.text_area("Description (optional)")
        with t2:
            subject = st.text_input("Subject", placeholder="Biology")
            due_date = st.date_input("Due date", value=date.today())
            due_time = st.time_input("Time (optional)", value=time(17,0))
            priority = st.selectbox("Priority", ["Low","Medium","High"], index=1)
        if st.form_submit_button("Add Task") and title:
            run_query(
                "INSERT INTO tasks (title, description, subject, due_date, due_time, priority, status, created_at) VALUES (?, ?, ?, ?, ?, ?, 'Pending', ?)",
                (title.strip(), description.strip(), subject.strip(), due_date.isoformat(), due_time.isoformat(), priority, now_iso()),
            )
            st.success("Task added ✔")

    st.divider()
    col1, col2, col3 = st.columns([2,2,2])
    subj_filter = col1.text_input("Filter by subject", value="")
    status_filter = col2.selectbox("Status", ["All","Pending","Done"], index=0)
    show_overdue = col3.checkbox("Show overdue only", value=False)

    query = "SELECT id, title, subject, due_date, due_time, priority, status FROM tasks"
    rows = run_query(query, fetch=True)
    # filter in python for simplicity
    displayed = []
    for r in rows:
        tid, ttitle, tsubj, ddate, dtime, pri, status = r
        if subj_filter and subj_filter.lower() not in (tsubj or "").lower():
            continue
        if status_filter != "All" and status != status_filter:
            continue
        if show_overdue:
            try:
                dt_str = f"{ddate} {dtime}"
                dt_obj = datetime.fromisoformat(dt_str)
                if dt_obj >= datetime.now():
                    continue
            except Exception:
                pass
        displayed.append(r)

    if displayed:
        for tid, ttitle, tsubj, ddate, dtime, pri, status in displayed:
            with st.container():
                c1, c2 = st.columns([4,2])
                c1.markdown(f"**{ttitle}**")
                c1.caption(f"{tsubj or 'General'} • {ddate} {dtime[:5] if dtime else ''}")
                c2.markdown(f"Priority: {pri} • Status: {status}")
                b1, b2, b3 = st.columns(3)
                if b1.button("Mark Done", key=f"done_{tid}"):
                    run_query("UPDATE tasks SET status='Done' WHERE id=?", (tid,))
                    st.toast("Marked done")
                    st.experimental_rerun()
                if b2.button("Edit", key=f"edit_{tid}"):
                    with st.form(f"edit_task_{tid}", clear_on_submit=True):
                        new_title = st.text_input("Title", value=ttitle)
                        new_desc = st.text_area("Description", value=(run_query("SELECT description FROM tasks WHERE id=?", (tid,), fetch=True)[0][0] or ""))
                        new_subj = st.text_input("Subject", value=(tsubj or ""))
                        new_date = st.date_input("Date", value=date.fromisoformat(ddate))
                        new_time = st.time_input("Time", value=time.fromisoformat(dtime) if dtime else time(17,0))
                        new_pri = st.selectbox("Priority", ["Low","Medium","High"], index=["Low","Medium","High"].index(pri))
                        new_status = st.selectbox("Status", ["Pending","Done"], index=0 if status=="Pending" else 1)
                        if st.form_submit_button("Save"):
                            run_query("UPDATE tasks SET title=?, description=?, subject=?, due_date=?, due_time=?, priority=?, status=? WHERE id=?",
                                      (new_title.strip(), new_desc.strip(), new_subj.strip(), new_date.isoformat(), new_time.isoformat(), new_pri, new_status, tid))
                            st.success("Updated")
                            st.experimental_rerun()
                if b3.button("Delete", key=f"del_t_{tid}"):
                    run_query("DELETE FROM tasks WHERE id=?", (tid,))
                    st.toast("Deleted")
                    st.experimental_rerun()
    else:
        st.info("No tasks to show.")

# ---------------- Exam Prep ----------------
def ui_exam_prep():
    st.subheader("📘 Exam Prep")
    st.caption("Add question bank items and take quizzes by subject.")

    tab1, tab2, tab3 = st.tabs(["Take Quiz","Question Bank","Performance"])
    with tab1:
        with get_conn() as conn:
            subs = [r[0] for r in conn.execute("SELECT DISTINCT subject FROM questions").fetchall()]
        if not subs:
            st.info("No questions yet — add some in Question Bank.")
        else:
            subject = st.selectbox("Subject", subs)
            num = st.slider("Number of questions", 1, 20, 5)
            if st.button("Start Quiz"):
                rows = run_query("SELECT id, question, option_a, option_b, option_c, option_d, correct_option FROM questions WHERE subject=? ORDER BY RANDOM() LIMIT ?", (subject, num), fetch=True)
                if not rows:
                    st.warning("Not enough questions in this subject.")
                else:
                    st.session_state['quiz'] = rows
                    st.session_state['answers'] = {}
                    st.experimental_rerun()
        if st.session_state.get('quiz'):
            rows = st.session_state['quiz']
            for i, r in enumerate(rows, start=1):
                qid, q, a, b, c, d, correct = r
                st.write(f"**Q{i}.** {q}")
                choice = st.radio(f"Q{i}", ["A","B","C","D"], format_func=lambda x: {"A":a,"B":b,"C":c,"D":d}[x], key=f"quiz_{qid}")
                st.session_state['answers'][qid] = choice
            if st.button("Submit Quiz"):
                answers = st.session_state.get('answers', {})
                correct_map = {r[0]: r[6] for r in rows}
                total = len(answers)
                correct_count = sum(1 for qid, ans in answers.items() if ans == correct_map.get(qid))
                run_query("INSERT INTO quiz_attempts (subject, total, correct, taken_at) VALUES (?, ?, ?, ?)",
                          (subject, total, correct_count, now_iso()))
                st.success(f"Score: {correct_count}/{total} ({int((correct_count/total)*100)}%)")
                st.session_state.pop('quiz', None)
                st.session_state.pop('answers', None)

    with tab2:
        st.markdown("### Add Question")
        with st.form("add_q", clear_on_submit=True):
            subj = st.text_input("Subject")
            q = st.text_area("Question")
            a = st.text_input("Option A")
            b = st.text_input("Option B")
            c = st.text_input("Option C")
            d = st.text_input("Option D")
            ans = st.selectbox("Correct Option", ["A","B","C","D"])
            if st.form_submit_button("Save Question") and subj and q and a and b and c and d:
                run_query("INSERT INTO questions (subject, question, option_a, option_b, option_c, option_d, correct_option, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                          (subj.strip(), q.strip(), a.strip(), b.strip(), c.strip(), d.strip(), ans, now_iso()))
                st.success("Question saved")

        st.divider()
        st.markdown("### All Questions")
        rows = run_query("SELECT id, subject, question, option_a, option_b, option_c, option_d, correct_option FROM questions ORDER BY id DESC", fetch=True)
        if rows:
            for qr in rows:
                qid, subj, qtext, a, b, c, d, ans = qr
                with st.container():
                    st.markdown(f"**{subj}** — {qtext}")
                    st.caption(f"A) {a}  |  B) {b}  |  C) {c}  |  D) {d}  •  Answer: {ans}")
                    if st.button("Delete", key=f"del_q_{qid}"):
                        run_query("DELETE FROM questions WHERE id=?", (qid,))
                        st.toast("Deleted")
                        st.experimental_rerun()
        else:
            st.info("No questions yet.")

    with tab3:
        rows = run_query("SELECT subject, total, correct, taken_at FROM quiz_attempts ORDER BY id DESC", fetch=True)
        if rows:
            df = pd.DataFrame(rows, columns=["Subject","Total","Correct","When"])
            df["Score %"] = (df["Correct"] / df["Total"]) * 100
            st.dataframe(df, use_container_width=True)
            st.markdown("#### Average by Subject")
            avg = df.groupby("Subject")["Score %"].mean().reset_index()
            st.bar_chart(avg.rename(columns={"Score %":"score"}).set_index("Subject"))
        else:
            st.info("No quiz attempts yet.")

# ---------------- Study Materials ----------------
def ui_study_materials():
    st.subheader("📚 Study Materials")
    st.caption("Store subjects & chapters for revision.")

    with st.form("add_chapter", clear_on_submit=True):
        subject = st.text_input("Subject", placeholder="Mathematics")
        chapter = st.text_input("Chapter", placeholder="Trigonometry - Ratios")
        if st.form_submit_button("Add Chapter") and subject and chapter:
            run_query("INSERT INTO chapters (subject, chapter, created_at) VALUES (?, ?, ?)",
                      (subject.strip(), chapter.strip(), now_iso()))
            st.success("Chapter added 📖")

    st.divider()
    search = st.text_input("🔍 Search Chapters", placeholder="Type to search...")
    if search:
        rows = run_query("SELECT id, subject, chapter, created_at FROM chapters WHERE subject LIKE ? OR chapter LIKE ? ORDER BY subject, id DESC",
                         (f"%{search}%", f"%{search}%"), fetch=True)
    else:
        rows = run_query("SELECT id, subject, chapter, created_at FROM chapters ORDER BY subject, id DESC", fetch=True)

    if rows:
        subjects = {}
        for sid, subj, chap, created in rows:
            subjects.setdefault(subj, []).append((sid, chap, created))
        for subj, chs in subjects.items():
            with st.expander(subj):
                for sid, chap, created in chs:
                    st.markdown(f"- {chap} _(added {created.split('T')[0]})_")
                    if st.button("Delete", key=f"del_chap_{sid}"):
                        run_query("DELETE FROM chapters WHERE id=?", (sid,))
                        st.toast("Deleted")
                        st.experimental_rerun()
    else:
        st.info("No chapters yet. Add some above.")

# ---------------- Notepad ----------------
def ui_notepad():
    st.subheader("📝 Notepad")
    st.caption("Write and manage personal notes.")

    with st.form("add_note", clear_on_submit=True):
        title = st.text_input("Title")
        content = st.text_area("Content")
        if st.form_submit_button("Save Note") and title and content:
            run_query("INSERT INTO notes (title, content, created_at) VALUES (?, ?, ?)", (title.strip(), content.strip(), now_iso()))
            st.success("Note saved ✍️")

    st.divider()
    search = st.text_input("🔍 Search Notes", placeholder="Search title or content...")
    if search:
        rows = run_query("SELECT id, title, content, created_at FROM notes WHERE title LIKE ? OR content LIKE ? ORDER BY id DESC", (f"%{search}%", f"%{search}%"), fetch=True)
    else:
        rows = run_query("SELECT id, title, content, created_at FROM notes ORDER BY id DESC", fetch=True)

    if rows:
        for nid, title, content, created in rows:
            with st.container():
                st.markdown(f"### {title}")
                st.caption(f"Created {created.split('T')[0]}")
                st.write(content)
                c1, c2, c3 = st.columns([1,1,4])
                if c1.button("Delete", key=f"del_note_{nid}"):
                    run_query("DELETE FROM notes WHERE id=?", (nid,))
                    st.toast("Deleted")
                    st.experimental_rerun()
                if c2.button("Edit", key=f"edit_note_{nid}"):
                    with st.form(f"edit_form_{nid}", clear_on_submit=True):
                        new_title = st.text_input("Edit Title", value=title)
                        new_content = st.text_area("Edit Content", value=content)
                        if st.form_submit_button("Save Changes"):
                            run_query("UPDATE notes SET title=?, content=? WHERE id=?", (new_title.strip(), new_content.strip(), nid))
                            st.success("Note updated ✅")
                            st.experimental_rerun()
    else:
        st.info("No notes yet. Add one above.")

# ---------------- Bible (Bible-API.com) ----------------
def ui_bible():
    st.subheader("📖 Bible (Bible-API.com)")
    st.caption("Enter book, chapter and verse or verse-range (e.g. 16 or 16-18).")

    book = st.text_input("Book (e.g., John, Genesis)", value="John")
    chapter = st.number_input("Chapter", min_value=1, value=3)
    verse_input = st.text_input("Verse or range (e.g., 16 or 16-18)", value="16")

    if st.button("Get Verse"):
        q = f"{book} {chapter}:{verse_input}"
        # format for bible-api: replace spaces with + for book part
        try:
            query = f"{book}+{chapter}:{verse_input}"
            url = f"https://bible-api.com/{query}"
            resp = requests.get(url, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                # If multiple verses returned (verses list), show all
                if "verses" in data:
                    for v in data["verses"]:
                        st.markdown(f"**{v.get('book_name','') } {v.get('chapter','')}: {v.get('verse','')}**")
                        st.write(v.get("text",""))
                else:
                    st.markdown(f"**{data.get('reference','')}**")
                    st.write(data.get("text",""))
                st.caption(f"Translation: {data.get('translation_name', 'N/A')}")
            else:
                st.error("Verse not found. Try another reference.")
        except Exception as e:
            st.error(f"Error fetching verse: {e}")

# ---------------- Data Export / Import ----------------
def ui_settings():
    st.subheader("⚙️ Settings & Backup")
    st.caption("Export or import app data as JSON.")

    if st.button("Export Data (JSON)"):
        with get_conn() as conn:
            data = {}
            for tbl in ["social_links","tasks","questions","quiz_attempts","chapters","notes"]:
                try:
                    rows = conn.execute(f"SELECT * FROM {tbl}").fetchall()
                    cols = [d[0] for d in conn.execute(f"PRAGMA table_info({tbl})").fetchall()]
                    data[tbl] = [dict(zip(cols, r)) for r in rows]
                except Exception:
                    data[tbl] = []
            st.download_button("Download backup.json", json.dumps(data, indent=2), "teens_app_backup.json", "application/json")

    up = st.file_uploader("Import JSON backup", type=["json"])
    if up:
        try:
            payload = json.load(up)
            with get_conn() as conn:
                cur = conn.cursor()
                # simple restore: delete existing and insert if provided
                for tbl in ["social_links","tasks","questions","quiz_attempts","chapters","notes"]:
                    cur.execute(f"DELETE FROM {tbl}")
                    entries = payload.get(tbl, [])
                    if entries:
                        cols = list(entries[0].keys())
                        placeholders = ",".join("?"*len(cols))
                        insert_q = f"INSERT INTO {tbl} ({','.join(cols)}) VALUES ({placeholders})"
                        for e in entries:
                            cur.execute(insert_q, tuple(e.get(c) for c in cols))
                conn.commit()
            st.success("Import complete.")
        except Exception as e:
            st.error(f"Import failed: {e}")

# ---------------- Navigation and Main ----------------
PAGES = {
    "Social Hub": ui_social_hub,
    "Scheduler": ui_scheduler,
    "Exam Prep": ui_exam_prep,
    "Study Materials": ui_study_materials,
    "Notepad": ui_notepad,
    "Bible": ui_bible,
    "Settings": ui_settings,
}

st.sidebar.title("📌 Teens App")
choice = st.sidebar.radio("Navigate", list(PAGES.keys()))
PAGES[choice]()

