import streamlit as st
import sqlite3
from datetime import datetime, date, time
import pandas as pd
import random
import requests
import json
import os

# ==========================
# Page / Theme Styling
# ==========================
st.set_page_config(page_title="Teens App", layout="wide", page_icon="✨")

# Global: very dark gray + neon green text
GLOBAL_CSS = """
<style>
/* Background */
.stApp {
    background-color: #121212;
    background-attachment: fixed;
}
/* Make default text neon green for readability on dark bg */
h1, h2, h3, h4, h5, h6, p, div, span, label, li, th, td, code, pre {
    color: #00FF00 !important;
    text-shadow: 0 1px 2px rgba(0,0,0,0.6);
}
/* Inputs: dark with green text */
.stTextInput > div > div > input,
.stTextArea textarea,
.stSelectbox div[data-baseweb="select"] div,
.stMultiSelect div[data-baseweb="select"] div,
.stDateInput input, .stTimeInput input, .stNumberInput input {
    background-color: rgba(0,0,0,0.6) !important;
    color: #00FF00 !important;
    border: 1px solid #333 !important;
}
.stDownloadButton button, .stButton button {
    border-radius: 10px;
}
</style>
"""
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ==========================
# SQLite Setup
# ==========================
DB_PATH = "teens_app.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                content TEXT,
                created_at TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT,
                date TEXT,
                time TEXT
            )
        """)
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
        c.execute("""
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT,
                total INTEGER,
                correct INTEGER,
                taken_at TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS chapters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT,
                chapter TEXT,
                created_at TEXT
            )
        """)
        conn.commit()

init_db()

def run_query(q, params=(), fetch=False):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(q, params)
        conn.commit()
        if fetch:
            return cur.fetchall()

def now_iso():
    return datetime.utcnow().isoformat()

# ==========================
# Study Materials (in-app store)
# ==========================
def ui_study_materials():
    st.title("📚 Study Materials")
    st.caption("Store your subjects and chapters.")

    with st.form("add_chapter", clear_on_submit=True):
        subj = st.text_input("Subject", placeholder="Mathematics")
        chap = st.text_input("Chapter", placeholder="Trigonometry - Ratios")
        add = st.form_submit_button("Add Chapter")
        if add and subj and chap:
            run_query("INSERT INTO chapters (subject, chapter, created_at) VALUES (?, ?, ?)",
                      (subj.strip(), chap.strip(), now_iso()))
            st.success("Chapter added ✅")

    st.divider()
    search = st.text_input("🔎 Search subject or chapter")
    if search:
        rows = run_query("""
            SELECT id, subject, chapter, created_at
            FROM chapters
            WHERE subject LIKE ? OR chapter LIKE ?
            ORDER BY subject, id DESC
        """, (f"%{search}%", f"%{search}%"), fetch=True)
    else:
        rows = run_query("""
            SELECT id, subject, chapter, created_at
            FROM chapters
            ORDER BY subject, id DESC
        """, fetch=True)

    if rows:
        subjects = {}
        for r in rows:
            subjects.setdefault(r["subject"], []).append((r["id"], r["chapter"], r["created_at"]))
        for subj, chs in subjects.items():
            with st.expander(subj):
                for cid, chapter, created in chs:
                    st.markdown(f"- {chapter} _(added {created.split('T')[0]})_")
                    if st.button("Delete", key=f"del_chap_{cid}"):
                        run_query("DELETE FROM chapters WHERE id=?", (cid,))
                        st.toast("Deleted")
                        st.experimental_rerun()
    else:
        st.info("No chapters yet — add some above.")

# ==========================
# Notepad
# ==========================
def ui_notepad():
    st.title("📝 Notepad")

    tab1, tab2 = st.tabs(["Add / View", "Search"])
    with tab1:
        with st.form("add_note", clear_on_submit=True):
            title = st.text_input("Title")
            content = st.text_area("Content", height=180)
            if st.form_submit_button("Save Note") and title and content:
                run_query("INSERT INTO notes (title, content, created_at) VALUES (?, ?, ?)",
                          (title.strip(), content.strip(), now_iso()))
                st.success("Note saved ✍️")

        st.divider()
        rows = run_query("SELECT id, title, content, created_at FROM notes ORDER BY id DESC", fetch=True)
        if rows:
            for r in rows:
                nid, title, content, created = r["id"], r["title"], r["content"], r["created_at"]
                with st.container():
                    st.markdown(f"### {title}")
                    st.caption(f"Created {created.split('T')[0]}")
                    st.write(content)
                    c1, c2 = st.columns(2)
                    if c1.button("Delete", key=f"del_note_{nid}"):
                        run_query("DELETE FROM notes WHERE id=?", (nid,))
                        st.toast("Deleted")
                        st.experimental_rerun()
                    if c2.button("Edit", key=f"edit_note_{nid}"):
                        with st.form(f"edit_form_{nid}", clear_on_submit=True):
                            new_t = st.text_input("Edit Title", value=title)
                            new_c = st.text_area("Edit Content", value=content, height=150)
                            if st.form_submit_button("Save Changes"):
                                run_query("UPDATE notes SET title=?, content=? WHERE id=?",
                                          (new_t.strip(), new_c.strip(), nid))
                                st.success("Updated ✅")
                                st.experimental_rerun()
        else:
            st.info("No notes yet.")

    with tab2:
        q = st.text_input("Search notes (title or content)")
        if q:
            rows = run_query("""
                SELECT id, title, content, created_at
                FROM notes
                WHERE title LIKE ? OR content LIKE ?
                ORDER BY id DESC
            """, (f"%{q}%", f"%{q}%"), fetch=True)
            if rows:
                for r in rows:
                    st.markdown(f"**{r['title']}** — {r['created_at'].split('T')[0]}")
                    st.write(r["content"])
            else:
                st.info("No matches.")

# ==========================
# Scheduler
# ==========================
def ui_scheduler():
    st.title("⏰ Scheduler")

    with st.form("new_task", clear_on_submit=True):
        col1, col2 = st.columns([3,2])
        with col1:
            task = st.text_input("Task", placeholder="Read Biology Ch. 3")
        with col2:
            due_date = st.date_input("Date", value=date.today())
            due_time = st.time_input("Time", value=time(17,0))
        if st.form_submit_button("Add Task") and task:
            run_query("INSERT INTO schedule (task, date, time) VALUES (?, ?, ?)",
                      (task.strip(), due_date.isoformat(), due_time.isoformat()))
            st.success("Task added ✅")

    st.divider()
    rows = run_query("SELECT id, task, date, time FROM schedule ORDER BY date, time", fetch=True)
    if rows:
        df = pd.DataFrame(rows)
        df.columns = ["ID", "Task", "Date", "Time"]
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No tasks yet.")

# ==========================
# Exam Prep
# ==========================
def ui_exam_prep():
    st.title("❓ Exam Prep")

    tab1, tab2, tab3 = st.tabs(["Take Quiz", "Question Bank", "Performance"])

    # Take Quiz
    with tab1:
        subs = [r[0] for r in run_query("SELECT DISTINCT subject FROM questions", fetch=True)]
        if not subs:
            st.info("No questions yet. Add some in the Question Bank.")
        else:
            subject = st.selectbox("Subject", subs)
            n = st.slider("Number of questions", 1, 20, 5)
            if st.button("Start Quiz"):
                rows = run_query("""
                    SELECT id, question, option_a, option_b, option_c, option_d, correct_option
                    FROM questions
                    WHERE subject=?
                    ORDER BY RANDOM() LIMIT ?
                """, (subject, n), fetch=True)
                if not rows:
                    st.warning("Not enough questions for that subject.")
                else:
                    st.session_state["quiz_rows"] = rows
                    st.session_state["quiz_answers"] = {}
                    st.experimental_rerun()

        if st.session_state.get("quiz_rows"):
            rows = st.session_state["quiz_rows"]
            for i, r in enumerate(rows, start=1):
                qid = r["id"]
                options = {"A": r["option_a"], "B": r["option_b"], "C": r["option_c"], "D": r["option_d"]}
                st.write(f"**Q{i}.** {r['question']}")
                choice = st.radio(f"Q{i}", ["A","B","C","D"],
                                  format_func=lambda x: options[x], key=f"ans_{qid}")
                st.session_state["quiz_answers"][qid] = choice
            if st.button("Submit Quiz"):
                answers = st.session_state["quiz_answers"]
                key_map = {r["id"]: r["correct_option"] for r in rows}
                total = len(answers)
                correct = sum(1 for qid, ans in answers.items() if ans == key_map.get(qid))
                run_query("INSERT INTO quiz_attempts (subject, total, correct, taken_at) VALUES (?, ?, ?, ?)",
                          (subject, total, correct, now_iso()))
                st.success(f"Score: {correct}/{total}  ({int(correct/total*100)}%)")
                st.session_state.pop("quiz_rows")
                st.session_state.pop("quiz_answers")

    # Question Bank
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
                run_query("""
                    INSERT INTO questions (subject, question, option_a, option_b, option_c, option_d, correct_option, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (subj.strip(), q.strip(), a.strip(), b.strip(), c.strip(), d.strip(), ans, now_iso()))
                st.success("Question saved ✅")

        st.divider()
        rows = run_query("""
            SELECT id, subject, question, option_a, option_b, option_c, option_d, correct_option
            FROM questions ORDER BY id DESC
        """, fetch=True)
        if rows:
            for r in rows:
                st.markdown(f"**{r['subject']}** — {r['question']}")
                st.caption(f"A) {r['option_a']}  |  B) {r['option_b']}  |  C) {r['option_c']}  |  D) {r['option_d']}  •  Answer: {r['correct_option']}")
                if st.button("Delete", key=f"del_q_{r['id']}"):
                    run_query("DELETE FROM questions WHERE id=?", (r["id"],))
                    st.toast("Deleted")
                    st.experimental_rerun()
        else:
            st.info("No questions yet.")

    # Performance
    with tab3:
        rows = run_query("SELECT subject, total, correct, taken_at FROM quiz_attempts ORDER BY id DESC", fetch=True)
        if rows:
            df = pd.DataFrame(rows)
            df.columns = ["Subject", "Total", "Correct", "When"]
            df["Score %"] = (df["Correct"] / df["Total"]) * 100
            st.dataframe(df, use_container_width=True)
            st.markdown("#### Average Score by Subject")
            avg = df.groupby("Subject")["Score %"].mean().reset_index()
            st.bar_chart(avg.rename(columns={"Score %":"score"}).set_index("Subject"))
        else:
            st.info("No quiz attempts yet.")

# ==========================
# Social Media (simple links)
# ==========================
def ui_social():
    st.title("🌐 Social Media")
    st.write("Stay connected with your favorite platforms.")
    st.markdown("- [Instagram](https://instagram.com)")
    st.markdown("- [X / Twitter](https://twitter.com)")
    st.markdown("- [Facebook](https://facebook.com)")
    st.markdown("- [TikTok](https://tiktok.com)")

# ==========================
# Bible Helpers (Daily + Search)
# ==========================
DAILY_VERSES_FILE = "daily_verses.json"
DEFAULT_DAILY = [
    {"book": "John", "chapter": 3, "verse": "16"},
    {"book": "Psalm", "chapter": 23, "verse": "1"},
    {"book": "Philippians", "chapter": 4, "verse": "13"},
    {"book": "Genesis", "chapter": 1, "verse": "1"},
    {"book": "Romans", "chapter": 8, "verse": "28"},
    {"book": "Isaiah", "chapter": 40, "verse": "31"},
    {"book": "Proverbs", "chapter": 3, "verse": "5-6"}
]

def load_daily_list():
    if os.path.exists(DAILY_VERSES_FILE):
        try:
            with open(DAILY_VERSES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and data:
                    return data
        except Exception:
            pass
    return DEFAULT_DAILY

def get_daily_today():
    verses = load_daily_list()
    idx = date.today().toordinal() % len(verses)
    v = verses[idx]
    return v["book"], v["chapter"], v["verse"]

def display_bible_api(book, chapter, verse_or_range):
    """Fetch from bible-api.com and display in a styled card (sky blue text)."""
    book_q = book.replace(" ", "+")
    url = f"https://bible-api.com/{book_q}+{chapter}:{verse_or_range}"
    try:
        r = requests.get(url, timeout=8)
        if r.status_code != 200:
            st.error("⚠️ Verse not found. Try a different reference.")
            return
        data = r.json()
        # Handle single or multiple verses
        if isinstance(data, dict) and "verses" in data:
            for v in data["verses"]:
                _card_bible(f"{v.get('book_name','')} {v.get('chapter','')}:{v.get('verse','')}", v.get("text",""))
        elif isinstance(data, dict) and "text" in data:
            _card_bible(data.get("reference",""), data.get("text",""))
        else:
            st.error("No text returned.")
        # Translation footer if present
        if isinstance(data, dict) and data.get("translation_name"):
            st.caption(f"Translation: {data['translation_name']}")
    except Exception as e:
        st.error(f"Error contacting Bible API: {e}")

def display_bible_chapter(book, chapter):
    """Fetch an entire chapter and show verses (sky blue)."""
    book_q = book.replace(" ", "+")
    url = f"https://bible-api.com/{book_q}+{chapter}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            st.error("⚠️ Could not fetch chapter. Try another book/chapter.")
            return
        data = r.json()
        verses = data.get("verses", [])
        if not verses:
            st.info("No verses returned.")
            return
        for v in verses:
            _card_bible(f"{v['book_name']} {v['chapter']}:{v['verse']}", v['text'])
        if data.get("translation_name"):
            st.caption(f"Translation: {data['translation_name']}")
    except Exception as e:
        st.error(f"Error fetching chapter: {e}")

def _card_bible(reference, text):
    """Render a verse box with sky blue text on dark background."""
    st.markdown(f"""
        <div style="
            background-color: rgba(0,0,0,0.7);
            padding: 16px;
            border-radius: 12px;
            box-shadow: 2px 2px 6px rgba(0,0,0,0.8);
            margin-bottom: 10px;
            text-align: left;
            color: #87CEEB;  /* sky blue text */
            line-height: 1.6;
        ">
            <b>{reference}</b><br/>{text}
        </div>
    """, unsafe_allow_html=True)

# ==========================
# UI: Home (Daily Verse)
# ==========================
def ui_home():
    st.title("👋 Welcome to Teens App")
    st.write("Your all-in-one space for studying, notes, schedules, quizzes — plus a daily Bible verse for inspiration.")

    st.subheader("📖 Daily Verse")
    book, chap, ver = get_daily_today()
    # Show daily verse in sky blue card
    display_bible_api(book, chap, ver)

# ==========================
# UI: Bible Tab (Selectable Book & Chapter)
# ==========================
ALL_BOOKS = [
    "Genesis","Exodus","Leviticus","Numbers","Deuteronomy","Joshua","Judges","Ruth",
    "1 Samuel","2 Samuel","1 Kings","2 Kings","1 Chronicles","2 Chronicles","Ezra",
    "Nehemiah","Esther","Job","Psalms","Proverbs","Ecclesiastes","Song of Solomon",
    "Isaiah","Jeremiah","Lamentations","Ezekiel","Daniel","Hosea","Joel","Amos",
    "Obadiah","Jonah","Micah","Nahum","Habakkuk","Zephaniah","Haggai","Zechariah",
    "Malachi","Matthew","Mark","Luke","John","Acts","Romans","1 Corinthians",
    "2 Corinthians","Galatians","Ephesians","Philippians","Colossians",
    "1 Thessalonians","2 Thessalonians","1 Timothy","2 Timothy","Titus","Philemon",
    "Hebrews","James","1 Peter","2 Peter","1 John","2 John","3 John","Jude","Revelation"
]

def ui_bible():
    st.title("📖 Bible")
    st.caption("Select a Book and Chapter to read (text shows in sky blue).")

    book = st.selectbox("Book", ALL_BOOKS, index=42)  # default 'John'
    chapter = st.number_input("Chapter", min_value=1, max_value=150, value=3, step=1)

    c1, c2 = st.columns([1,1])
    with c1:
        if st.button("📥 Load Chapter"):
            display_bible_chapter(book, chapter)
    with c2:
        st.write("")  # spacing
        verse = st.text_input("Or fetch specific verse/range (e.g., 16 or 16-18)")
        if st.button("🔎 Fetch Verse/Range"):
            if verse.strip():
                display_bible_api(book, chapter, verse.strip())
            else:
                st.warning("Enter a verse or range.")

# ==========================
# Navigation
# ==========================
PAGES = {
    "Home": ui_home,
    "Study Materials": ui_study_materials,
    "Notepad": ui_notepad,
    "Scheduler": ui_scheduler,
    "Exam Prep": ui_exam_prep,
    "Bible": ui_bible,
    "Social Media": ui_social,
}

st.sidebar.title("📌 Teens App")
choice = st.sidebar.radio("Navigate", list(PAGES.keys()))
PAGES[choice]()
