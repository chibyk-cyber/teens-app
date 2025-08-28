# teens_app_full.py
import streamlit as st
import sqlite3
from datetime import datetime, date, time
import pandas as pd
import random
import requests
from supabase import create_client, Client

# -------------------------
# PAGE CONFIG & STYLING
# -------------------------
st.set_page_config(page_title="Teens App", layout="wide", page_icon="✨")
BASE_CSS = """
<style>
html, body, [class*="css"]  {
  background-color: #1E1E1E !important;
  color: #E0E0E0 !important;
  font-family: 'Segoe UI', sans-serif;
}
.stApp {
  background-color: #1E1E1E;
}
h1, h2, h3, h4, h5, h6, label, span, p, div, li {
  color: #E0E0E0 !important;
}
.stButton>button, .stDownloadButton>button {
  background-color: #87CEEB !important;
  color: #000 !important;
  border-radius: 8px;
  font-weight: 600;
}
input, textarea, .stTextInput>div>div, .stTextArea>div>div {
  background-color: rgba(255,255,255,0.04) !important;
  color: #E0E0E0 !important;
  border: 1px solid rgba(255,255,255,0.06) !important;
}
.chat-bubble-sent {
    background-color: #87CEEB;
    color: #000;
    padding: 10px;
    border-radius: 12px;
    margin: 6px 0;
    max-width: 78%;
    margin-left: auto;
}
.chat-bubble-recv {
    background-color: #2A2A2A;
    color: #E0E0E0;
    padding: 10px;
    border-radius: 12px;
    margin: 6px 0;
    max-width: 78%;
}
.small-muted { color: #a0a0a0; font-size:12px; }
.stSidebar .css-1d391kg { background-color: #252525; }
</style>
"""
st.markdown(BASE_CSS, unsafe_allow_html=True)

# -------------------------
# SUPABASE CLIENT
# -------------------------
if "supabase" not in st.session_state:
    try:
        supa_url = st.secrets["supabase"]["url"]
        supa_key = st.secrets["supabase"]["key"]
        st.session_state["supabase"] = create_client(supa_url, supa_key)
    except Exception:
        st.error("Supabase credentials not found in st.secrets. Add them to .streamlit/secrets.toml or your host's secrets.")
        st.stop()

supabase: Client = st.session_state["supabase"]

# -------------------------
# HELPER FUNCTIONS
# -------------------------
def signup_user(email: str, password: str, username: str = None, number: str = None):
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        user = getattr(res, "user", None) or res.get("user") if isinstance(res, dict) else None
        if user:
            try:
                supabase.table("profiles").insert({
                    "user_id": user["id"],
                    "email": email,
                    "username": username or email.split("@")[0],
                    "number": number
                }).execute()
            except Exception:
                pass
        return res
    except Exception as e:
        return {"error": str(e)}

def login_user(email: str, password: str):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        user = getattr(res, "user", None) or res.get("user") if isinstance(res, dict) else None
        session = getattr(res, "session", None) or res.get("session") if isinstance(res, dict) else None
        if user:
            st.session_state["user"] = user
            if session and session.get("access_token"):
                st.session_state["access_token"] = session["access_token"]
            return {"user": user}
        else:
            return {"error": "Login failed (check credentials or confirm email)."}
    except Exception as e:
        return {"error": str(e)}

def get_my_profile():
    u = st.session_state.get("user")
    if not u:
        return None
    try:
        rows = supabase.table("profiles").select("*").eq("user_id", u["id"]).execute()
        if rows.data and len(rows.data) > 0:
            return rows.data[0]
    except Exception:
        pass
    return {"user_id": u["id"], "email": u.get("email"), "username": u.get("email").split("@")[0]}

def list_profiles(limit=200):
    try:
        rows = supabase.table("profiles").select("user_id, email, username, number").limit(limit).execute()
        return rows.data or []
    except Exception:
        return []

def create_group(name: str):
    try:
        res = supabase.table("groups").insert({"name": name, "created_by": st.session_state["user"]["id"]}).execute()
        gid = res.data[0]["id"]
        supabase.table("group_members").insert({"group_id": gid, "user_id": st.session_state["user"]["id"]}).execute()
        return gid
    except Exception:
        return None

def join_group(group_id: str):
    try:
        exists = supabase.table("group_members").select("*").eq("group_id", group_id).eq("user_id", st.session_state["user"]["id"]).limit(1).execute()
        if exists.data:
            return True
        supabase.table("group_members").insert({"group_id": group_id, "user_id": st.session_state["user"]["id"]}).execute()
        return True
    except Exception:
        return False

def list_groups():
    try:
        res = supabase.table("groups").select("*").order("created_at", desc=True).execute()
        return res.data or []
    except Exception:
        return []

def get_group_members(group_id: str):
    try:
        res = supabase.table("group_members").select("user_id").eq("group_id", group_id).execute()
        return [r["user_id"] for r in (res.data or [])]
    except Exception:
        return []

def send_message_private(receiver_user_id: str, content: str):
    try:
        supabase.table("messages").insert({
            "sender_id": st.session_state["user"]["id"],
            "receiver_id": receiver_user_id,
            "group_id": None,
            "content": content
        }).execute()
        return True
    except Exception:
        return False

def send_message_group(group_id: str, content: str):
    try:
        supabase.table("messages").insert({
            "sender_id": st.session_state["user"]["id"],
            "receiver_id": None,
            "group_id": group_id,
            "content": content
        }).execute()
        return True
    except Exception:
        return False

def fetch_private_conversation(other_user_id: str, limit=200):
    me = st.session_state["user"]["id"]
    a = supabase.table("messages").select("*").eq("sender_id", me).eq("receiver_id", other_user_id).order("created_at", desc=False).limit(limit).execute()
    b = supabase.table("messages").select("*").eq("sender_id", other_user_id).eq("receiver_id", me).order("created_at", desc=False).limit(limit).execute()
    rows = []
    if a.data: rows.extend(a.data)
    if b.data: rows.extend(b.data)
    rows_sorted = sorted(rows, key=lambda r: r["created_at"])
    return rows_sorted

def fetch_group_messages(group_id: str, limit=200):
    try:
        res = supabase.table("messages").select("*").eq("group_id", group_id).order("created_at", desc=False).limit(limit).execute()
        return res.data or []
    except Exception:
        return []

def iso_to_readable(ts: str):
    try:
        return ts.split(".")[0].replace("T", " ")
    except Exception:
        return str(ts)

# -------------------------
# LOCAL SQLITE DB
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
# AUTH UI
# -------------------------
def ui_auth():
    st.sidebar.header("🔐 Account")
    if st.session_state.get("user"):
        prof = get_my_profile()
        st.sidebar.markdown(f"**{prof.get('username') if prof else st.session_state['user'].get('email')} ({prof.get('number','')})**")
        if st.sidebar.button("Sign out"):
            try: supabase.auth.sign_out()
            except Exception: pass
            st.session_state.pop("user", None)
            st.experimental_rerun()
        return

    choice = st.sidebar.radio("Sign in / up", ["Login", "Sign Up"])
    email = st.sidebar.text_input("Email", key="auth_email")
    password = st.sidebar.text_input("Password", type="password", key="auth_pass")

    if choice == "Sign Up":
        username = st.sidebar.text_input("Username", key="auth_un")
        number = st.sidebar.text_input("4-digit Number", key="auth_num")
        if st.sidebar.button("Create account"):
            if not email or not password or not number or len(number)<4:
                st.sidebar.error("Email, password, and 4-digit number required.")
            else:
                res = signup_user(email, password, username, number)
                if isinstance(res, dict) and res.get("error"):
                    st.sidebar.error(res["error"])
                else:
                    st.sidebar.success("Account created. Check your email.")
    else:
        if st.sidebar.button("Login"):
            if not email or not password:
                st.sidebar.error("Email and password required.")
            else:
                res = login_user(email, password)
                if res.get("error"):
                    st.sidebar.error(res["error"])
                else:
                    st.sidebar.success("Logged in")
                    st.experimental_rerun()

# -------------------------
# NAVIGATION PAGES
# -------------------------
# ... (Include the full chat, notes, scheduler, study materials, exam prep, Bible reader here, just like previous code)

# -------------------------
# MAIN NAVIGATION
# -------------------------
PAGES = {
    "Chat & Groups": ui_chat_and_groups,
    "Notes": ui_notes,
    "Scheduler": ui_schedule,
    "Study Materials": ui_study_materials,
    "Exam Prep": ui_exam_prep,
    "Bible": ui_bible_reader,  # -------------------------
}

# TOP NAVIGATION BAR (MATURE DARK THEME)
# -------------------------
NAV_CSS = """
<style>
.top-nav {
  background-color: #1E1E1E;
  padding: 10px;
  border-bottom: 1px solid #333;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.top-nav h2 {
  color: #87CEEB;
  margin: 0;
}
.top-nav button {
  background-color: #87CEEB;
  color: #000;
  border: none;
  padding: 6px 12px;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
}
.top-nav button:hover {
  background-color: #00BFFF;
}
</style>
"""
st.markdown(NAV_CSS, unsafe_allow_html=True)

def top_nav_bar():
    st.markdown("""
    <div class="top-nav">
        <h2>Teens App</h2>
        <div>
            <button onclick="window.location.reload();">Refresh</button>
        </div>
    </div>
    """, unsafe_allow_html=True)

top_nav_bar()

# -------------------------
# DEMO CHAT (prefilled for new users)
# -------------------------
def demo_chat():
    if "demo_done" not in st.session_state:
        st.session_state["demo_done"] = True
        demo_msgs = [
            {"sender": "System", "text": "Welcome to Teens App! This is a demo chat."},
            {"sender": "System", "text": "You can create study groups and chat with friends."},
            {"sender": "System", "text": "Try sending your first message!"}
        ]
        for msg in demo_msgs:
            st.markdown(f'<div class="chat-bubble-recv"><b>{msg["sender"]}</b>: {msg["text"]}</div>', unsafe_allow_html=True)

# Inject demo chat at top if no messages exist
if st.session_state.get("user") and not st.session_state.get("open_chat_user") and not st.session_state.get("open_group"):
    st.info("Select a contact or group to start chatting, or see the demo below:")
    demo_chat()

# -------------------------
# RUN APP
# -------------------------
ui_auth()
st.sidebar.title("Navigate")
selection = st.sidebar.radio("Go to", list(PAGES.keys()))
st.markdown("---")
st.markdown(f"### Logged in: {get_my_profile().get('username') if st.session_state.get('user') else 'Not signed in'}")
st.markdown("---")
page_func = PAGES.get(selection)
if page_func: 
    page_func()
else: 
    st.info("Select a page")

PAGES = {
    "Chat & Groups": ui_chat_and_groups,
    "Notes": ui_notes,
    "Scheduler": ui_schedule,
    "Study Materials": ui_study_materials,
    "Exam Prep": ui_exam_prep,
    "Bible": ui_bible_reader
}

# -------------------------
# TOP NAV BAR
# -------------------------
NAV_CSS = """
<style>
.top-nav {
  background-color: #1E1E1E;
  padding: 10px;
  border-bottom: 1px solid #333;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.top-nav h2 {
  color: #87CEEB;
  margin: 0;
}
.top-nav button {
  background-color: #87CEEB;
  color: #000;
  border: none;
  padding: 6px 12px;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
}
.top-nav button:hover {
  background-color: #00BFFF;
}
</style>
"""
st.markdown(NAV_CSS, unsafe_allow_html=True)

def top_nav_bar():
    st.markdown("""
    <div class="top-nav">
        <h2>Teens App</h2>
        <div>
            <button onclick="window.location.reload();">Refresh</button>
        </div>
    </div>
    """, unsafe_allow_html=True)

top_nav_bar()
ui_auth()
st.sidebar.title("Navigate")
selection = st.sidebar.radio("Go to", list(PAGES.keys()))
st.markdown("---")
st.markdown(f"### Logged in: {get_my_profile().get('username') if st.session_state.get('user') else 'Not signed in'}")
st.markdown("---")
page_func = PAGES.get(selection)
if page_func:
    page_func()
else:
    st.info("Select a page")

