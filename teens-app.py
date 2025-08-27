# teens_app.py
import streamlit as st
import sqlite3
from datetime import datetime, date, time
import pandas as pd
import random
import requests
from supabase import create_client, Client

# -------------------------
# CONFIG & STYLING
# -------------------------
st.set_page_config(page_title="Teens App", layout="wide", page_icon="✨")

BASE_CSS = """
<style>
html, body, [class*="css"]  {
  background-color: #1E1E1E !important;
  color: #D0D0D0 !important;
}
.stApp { background-color: #1E1E1E; }
h1, h2, h3, h4, h5, h6, label, span, p, div, li {
  color: #D0D0D0 !important;
}
.stButton>button, .stDownloadButton>button {
  background-color: #4CAF50 !important;
  color: #fff !important;
  border-radius: 8px;
  font-weight: 600;
}
input, textarea, .stTextInput>div>div, .stTextArea>div>div {
  background-color: rgba(255,255,255,0.05) !important;
  color: #D0D0D0 !important;
  border: 1px solid rgba(255,255,255,0.08) !important;
}
.chat-bubble-sent { background-color: #4CAF50; color: #fff; padding: 10px; border-radius: 12px; margin: 6px 0; max-width: 78%; margin-left: auto; }
.chat-bubble-recv { background-color: #2C2C2C; color: #D0D0D0; padding: 10px; border-radius: 12px; margin: 6px 0; max-width: 78%; }
.small-muted { color: #a0a0a0; font-size:12px; }
</style>
"""
st.markdown(BASE_CSS, unsafe_allow_html=True)

# -------------------------
# Supabase client
# -------------------------
if "supabase" not in st.session_state:
    try:
        supa_url = st.secrets["supabase"]["url"]
        supa_key = st.secrets["supabase"]["key"]
        st.session_state["supabase"] = create_client(supa_url, supa_key)
    except Exception:
        st.error("Supabase credentials missing in st.secrets.")
        st.stop()

supabase: Client = st.session_state["supabase"]

# -------------------------
# Helper functions
# -------------------------
def signup_user(email, password, username=None):
    res = supabase.auth.sign_up({"email": email, "password": password})
    user = getattr(res, "user", None) or res.get("user", None)
    if user:
        try:
            supabase.table("profiles").insert({
                "user_id": user["id"],
                "email": email,
                "username": username or email.split("@")[0]
            }).execute()
        except Exception: pass
    return res

def login_user(email, password):
    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
    user = getattr(res, "user", None) or res.get("user", None)
    if user: st.session_state["user"] = user
    return res

def get_my_profile():
    u = st.session_state.get("user")
    if not u: return None
    try:
        rows = supabase.table("profiles").select("*").eq("user_id", u["id"]).execute()
        if rows.data: return rows.data[0]
    except Exception: pass
    return {"user_id": u["id"], "email": u.get("email"), "username": u.get("email").split("@")[0]}

def iso_to_readable(ts: str):
    try: return ts.split(".")[0].replace("T", " ")
    except: return str(ts)

# -------------------------
# Local SQLite (notes/schedule)
# -------------------------
LOCAL_DB = "teens_local.db"
def get_local_conn(): 
    con = sqlite3.connect(LOCAL_DB, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con

def init_local_db():
    with get_local_conn() as conn:
        cur = conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS local_notes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT,
                        content TEXT,
                        created_at TEXT)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS local_schedule (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task TEXT,
                        date TEXT,
                        time TEXT)""")
        conn.commit()

init_local_db()

# -------------------------
# UI: Authentication
# -------------------------
def ui_auth():
    st.sidebar.header("🔐 Account")
    if st.session_state.get("user"):
        prof = get_my_profile()
        st.sidebar.markdown(f"**{prof.get('username')}**")
        if st.sidebar.button("Sign out"):
            supabase.auth.sign_out()
            st.session_state.pop("user", None)
            st.experimental_rerun()
        return
    choice = st.sidebar.radio("Sign in / up", ["Login", "Sign Up"])
    email = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Password", type="password")
    if choice=="Sign Up":
        username = st.sidebar.text_input("Username (optional)")
        if st.sidebar.button("Create account"):
            if email and password:
                signup_user(email, password, username)
                st.sidebar.success("Account created.")
    else:
        if st.sidebar.button("Login"):
            if email and password:
                login_user(email, password)
                st.experimental_rerun()

# -------------------------
# UI: Notes
# -------------------------
def ui_notes():
    st.header("📝 Notes")
    tab1, tab2 = st.tabs(["New note", "Your notes"])
    with tab1:
        with st.form("new_note", clear_on_submit=True):
            t = st.text_input("Title")
            c = st.text_area("Content")
            if st.form_submit_button("Save"):
                with get_local_conn() as conn:
                    conn.execute("INSERT INTO local_notes (title, content, created_at) VALUES (?, ?, ?)",
                                 (t, c, datetime.utcnow().isoformat()))
                    conn.commit()
                st.success("Saved locally")
    with tab2:
        df = pd.read_sql("SELECT id, title, content, created_at FROM local_notes ORDER BY id DESC", get_local_conn())
        if not df.empty:
            for _, row in df.iterrows():
                st.subheader(row["title"])
                st.write(row["content"])
                st.caption(row["created_at"])
                if st.button("Delete", key=f"del_note_{row['id']}"):
                    with get_local_conn() as conn:
                        conn.execute("DELETE FROM local_notes WHERE id=?", (row["id"],))
                        conn.commit()
                    st.experimental_rerun()
        else: st.info("No notes yet.")

# -------------------------
# UI: Schedule
# -------------------------
def ui_schedule():
    st.header("📅 Schedule")
    with st.form("add_task_local", clear_on_submit=True):
        t = st.text_input("Task")
        d = st.date_input("Date", value=date.today())
        ti = st.time_input("Time", value=time(17,0))
        if st.form_submit_button("Add"):
            with get_local_conn() as conn:
                conn.execute("INSERT INTO local_schedule (task, date, time) VALUES (?, ?, ?)", (t, d.isoformat(), ti.isoformat()))
                conn.commit()
            st.success("Added")
    df = pd.read_sql("SELECT id, task, date, time FROM local_schedule ORDER BY date, time", get_local_conn())
    if not df.empty: st.table(df)
    else: st.info("No scheduled tasks.")

# -------------------------
# UI: Study Materials
# -------------------------
def ui_study_materials():
    st.header("📚 Study Materials")
    materials = {
        "Mathematics": ["Algebra","Geometry","Trigonometry","Calculus"],
        "Biology": ["Cell Biology","Genetics","Ecology"],
        "English": ["Grammar","Comprehension","Essay writing"]
    }
    subj = st.selectbox("Subject", list(materials.keys()))
    st.write("Chapters:")
    for ch in materials[subj]: st.markdown(f"- {ch}")

# -------------------------
# UI: Exam Prep
# -------------------------
def ui_exam_prep():
    st.header("❓ Exam Practice")
    banks = {
        "Math": [("7×8=?","56"),("x+2=5","3")],
        "Biology":[("Photosynthesis?","Process by which plants make food")]
    }
    subject = st.selectbox("Choose subject", list(banks.keys()))
    if st.button("Get Question"):
        q, a = random.choice(banks[subject])
        st.write(q)
        ans = st.text_input("Your answer")
        if st.button("Check"):
            if ans.strip().lower()==a.lower(): st.success("Correct!")
            else: st.error(f"Answer: {a}")

# -------------------------
# UI: Bible Reader
# -------------------------
def _bible_card(reference, text):
    st.markdown(f"""
    <div style="background-color: rgba(255,255,255,0.02); padding:12px; border-radius:10px; margin-bottom:8px; color:#4CAF50; line-height:1.6;">
        <b>{reference}</b><br>{text}
    </div>
    """, unsafe_allow_html=True)

def display_bible_api(book, chapter, verse_or_range):
    url = f"https://bible-api.com/{book}+{chapter}:{verse_or_range}"
    try:
        r = requests.get(url, timeout=8)
        if r.status_code!=200: st.error("Verse not found"); return
        data = r.json()
        verses = data.get("verses", [])
        for v in verses: _bible_card(f"{v.get('book_name')} {v.get('chapter')}:{v.get('verse')}", v.get("text"))
    except Exception as e: st.error(f"Bible API error: {e}")

def display_bible_chapter(book, chapter):
    url = f"https://bible-api.com/{book}+{chapter}"
    try:
        r = requests.get(url, timeout=8)
        data = r.json()
        for v in data.get("verses", []):
            _bible_card(f"{v.get('book_name')} {v.get('chapter')}:{v.get('verse')}", v.get("text"))
    except Exception as e: st.error(f"Bible chapter error: {e}")

def ui_bible_reader():
    st.header("📖 Bible Reader")
    ALL_BOOKS = ["Genesis","Exodus","Leviticus","Numbers","Deuteronomy","Psalms","Proverbs","Isaiah","Matthew","Mark","Luke","John","Acts","Romans","Revelation"]
    book = st.selectbox("Book", ALL_BOOKS)
    chap = st.number_input("Chapter", min_value=1, value=1)
    if st.button("Load Chapter"): display_bible_chapter(book, chap)
    verse = st.text_input("Verse/range (3:16)")
    if st.button("Get Verse"): display_bible_api(book, chap, verse or "1")

# -------------------------
# UI: Chat & Groups
# -------------------------
def ui_chat_groups():
    st.header("💬 Chat & Study Groups")

    # List groups (dummy)
    groups = ["Math Club","Biology Squad","English Circle"]
    group_sel = st.selectbox("Select Group", ["-- Create New --"]+groups)

    if group_sel=="-- Create New --":
        new_group = st.text_input("New Group Name")
        if st.button("Create Group"):
            st.success(f"Group '{new_group}' created (demo)")
    else:
        st.subheader(f"💬 {group_sel}")
        if "chat_history" not in st.session_state: st.session_state.chat_history = []
        chat = st.text_input("Type your message")
        if st.button("Send"):
            if chat:
                st.session_state.chat_history.append(("me", chat))
                # Dummy reply
                st.session_state.chat_history.append(("bot", f"{chat[::-1]}"))
        for sender, msg in st.session_state.chat_history:
            cls = "chat-bubble-sent" if sender=="me" else "chat-bubble-recv"
            st.markdown(f'<div class="{cls}">{msg}</div>', unsafe_allow_html=True)

# -------------------------
# Main Navigation
# -------------------------
PAGES = {
    "Notes": ui_notes,
    "Scheduler": ui_schedule,
    "Study Materials": ui_study_materials,
    "Exam Prep": ui_exam_prep,
    "Bible": ui_bible_reader,
    "Chat & Groups": ui_chat_groups
}

ui_auth()
st.sidebar.title("Navigate")
selection = st.sidebar.radio("Go to", list(PAGES.keys()))
page_func = PAGES.get(selection)
if page_func: page_func()
