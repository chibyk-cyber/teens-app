# -------------------------
# teens_app.py
# -------------------------
import streamlit as st
import sqlite3
from datetime import datetime, date, time
import pandas as pd
import random
import requests
import json
import os
from supabase import create_client, Client

# -------------------------
# CONFIG & STYLING
# -------------------------
st.set_page_config(page_title="Teens App", layout="wide", page_icon="✨")

BASE_CSS = """
<style>
html, body, [class*="css"]  {
  background-color: #121212 !important;
  color: #E0E0E0 !important;
}
.stApp { background-color: #121212; }
h1, h2, h3, h4, h5, h6, label, span, p, div, li { color: #E0E0E0 !important; }
.stButton>button, .stDownloadButton>button {
  background-color: #87CEEB !important; color: #000 !important; border-radius: 8px; font-weight: 600;
}
input, textarea, .stTextInput>div>div, .stTextArea>div>div {
  background-color: rgba(255,255,255,0.04) !important; color: #E0E0E0 !important; border: 1px solid rgba(255,255,255,0.06) !important;
}
.chat-bubble-sent { background-color: #87CEEB; color: #000; padding: 10px; border-radius: 12px; margin: 6px 0; max-width: 78%; margin-left: auto; }
.chat-bubble-recv { background-color: #1E1E1E; color: #E0E0E0; padding: 10px; border-radius: 12px; margin: 6px 0; max-width: 78%; }
.small-muted { color: #a0a0a0; font-size:12px; }
</style>
"""
st.markdown(BASE_CSS, unsafe_allow_html=True)

# -------------------------
# SUPABASE SETUP
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
# LOCAL SQLITE SETUP
# -------------------------
LOCAL_DB = "teens_local.db"
def get_local_conn():
    conn = sqlite3.connect(LOCAL_DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn
def init_local_db():
    with get_local_conn() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS local_notes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT, content TEXT, created_at TEXT)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS local_schedule (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task TEXT, date TEXT, time TEXT)""")
init_local_db()

# -------------------------
# HELPER FUNCTIONS
# -------------------------
def signup_user(email, password, username=None):
    try:
        user_res = supabase.auth.sign_up({"email": email, "password": password})
        user = getattr(user_res, "user", None) or user_res.get("user") if isinstance(user_res, dict) else None
        if user:
            uid = random.randint(1000,9999)
            supabase.table("profiles").insert({"user_id": user["id"], "username": username or email.split("@")[0], "chat_id": uid}).execute()
        return user_res
    except Exception as e: return {"error": str(e)}

def login_user(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        user = getattr(res, "user", None) or res.get("user") if isinstance(res, dict) else None
        session = getattr(res, "session", None) or res.get("session") if isinstance(res, dict) else None
        if user:
            st.session_state["user"] = user
            if session and session.get("access_token"):
                st.session_state["access_token"] = session["access_token"]
            return {"user": user}
        else: return {"error": "Login failed"}
    except Exception as e: return {"error": str(e)}

def get_my_profile():
    u = st.session_state.get("user")
    if not u: return None
    try:
        rows = supabase.table("profiles").select("*").eq("user_id", u["id"]).execute()
        if rows.data and len(rows.data) > 0: return rows.data[0]
    except Exception: pass
    return {"user_id": u["id"], "email": u.get("email"), "username": u.get("email").split("@")[0]}

def list_profiles():
    try: return supabase.table("profiles").select("*").execute().data or []
    except Exception: return []

# -------------------------
# UI AUTH
# -------------------------
def ui_auth():
    st.sidebar.header("🔐 Account")
    if st.session_state.get("user"):
        prof = get_my_profile()
        st.sidebar.markdown(f"**{prof.get('username')}**")
        if st.sidebar.button("Sign out"):
            try: supabase.auth.sign_out()
            except Exception: pass
            st.session_state.pop("user", None)
            st.experimental_rerun()
        return

    choice = st.sidebar.radio("Sign in / up", ["Login","Sign Up"])
    email = st.sidebar.text_input("Email", key="auth_email")
    password = st.sidebar.text_input("Password", type="password", key="auth_pass")
    if choice=="Sign Up":
        username = st.sidebar.text_input("Username", key="auth_un")
        if st.sidebar.button("Create account"):
            if not email or not password: st.sidebar.error("Email & password required.")
            else:
                res = signup_user(email, password, username)
                if isinstance(res, dict) and res.get("error"): st.sidebar.error(res["error"])
                else: st.sidebar.success("Account created. Check email for confirmation.")
    else:
        if st.sidebar.button("Login"):
            if not email or not password: st.sidebar.error("Email & password required.")
            else:
                res = login_user(email, password)
                if res.get("error"): st.sidebar.error(res["error"])
                else: st.sidebar.success("Logged in"); st.experimental_rerun()

# -------------------------
# CHAT SYSTEM
# -------------------------
def ui_chat_system():
    st.header("💬 Chat System (Signup required)")
    if not st.session_state.get("user"):
        st.info("Please sign in to chat.")
        return

    me = get_my_profile()
    profiles = list_profiles()
    profile_map = {p["user_id"]: p.get("username") for p in profiles}

    left, right = st.columns([1.4,3])
    with left:
        st.subheader("Contacts")
        others = [p for p in profiles if p["user_id"]!=me["user_id"]]
        for p in others:
            if st.button(f"{p['username']} ({p['chat_id']})", key=f"chat_{p['user_id']}"):
                st.session_state["open_chat_user"]=p["user_id"]
        st.divider()
        st.subheader("Groups")
        try:
            groups = supabase.table("groups").select("*").execute().data or []
        except: groups=[]
        for g in groups:
            if st.button(g["name"], key=f"group_{g['id']}"): st.session_state["open_group"]=g["id"]
        st.write("Create Group")
        with st.form("create_group", clear_on_submit=True):
            name = st.text_input("Group name")
            if st.form_submit_button("Create") and name:
                res = supabase.table("groups").insert({"name":name,"created_by":me["user_id"]}).execute()
                if res.error: st.error(res.error)
                else: st.success("Created"); st.experimental_rerun()

    with right:
        if st.session_state.get("open_chat_user"):
            other_id=st.session_state["open_chat_user"]
            st.subheader(f"Chat with {profile_map.get(other_id)}")
            msgs = fetch_private_conversation(other_id)
            for m in msgs:
                sender=m["sender_id"]; content=m["content"]; ts=m["created_at"]
                cls = "chat-bubble-sent" if sender==me["user_id"] else "chat-bubble-recv"
                st.markdown(f'<div class="{cls}">{content}<div class="small-muted">{ts}</div></div>', unsafe_allow_html=True)
            with st.form("send_pm", clear_on_submit=True):
                msg=st.text_area("Message",height=90)
                if st.form_submit_button("Send") and msg.strip():
                    send_message_private(other_id,msg.strip())
                    st.experimental_rerun()
        elif st.session_state.get("open_group"):
            gid=st.session_state["open_group"]
            st.subheader(f"Group: {gid}")
            msgs=fetch_group_messages(gid)
            for m in msgs:
                sender=m["sender_id"]; content=m["content"]; ts=m["created_at"]
                cls="chat-bubble-sent" if sender==me["user_id"] else "chat-bubble-recv"
                st.markdown(f'<div class="{cls}">{content}<div class="small-muted">{ts}</div></div>', unsafe_allow_html=True)
            with st.form("send_gm",clear_on_submit=True):
                msg=st.text_area("Message",height=90)
                if st.form_submit_button("Send") and msg.strip():
                    send_message_group(gid,msg.strip())
                    st.experimental_rerun()
        else: st.info("Select contact or group to chat.")

# -------------------------
# FETCH MESSAGES
# -------------------------
def send_message_private(rid,content):
    supabase.table("messages").insert({"sender_id":st.session_state["user"]["id"],"receiver_id":rid,"group_id":None,"content":content}).execute()
def send_message_group(gid,content):
    supabase.table("messages").insert({"sender_id":st.session_state["user"]["id"],"receiver_id":None,"group_id":gid,"content":content}).execute()
def fetch_private_conversation(other_id):
    me=get_my_profile()
    a=supabase.table("messages").select("*").eq("sender_id",me["user_id"]).eq("receiver_id",other_id).execute().data or []
    b=supabase.table("messages").select("*").eq("sender_id",other_id).eq("receiver_id",me["user_id"]).execute().data or []
    msgs=sorted(a+b,key=lambda x:x["created_at"])
    return msgs
def fetch_group_messages(gid):
    return supabase.table("messages").select("*").eq("group_id",gid).order("created_at",asc=True).execute().data or []

# -------------------------
# NOTES UI
# -------------------------
def ui_notes():
    st.header("📝 Notes")
    tab1,tab2=st.tabs(["New Note","Your Notes"])
    with tab1:
        with st.form("new_note",clear_on_submit=True):
            t=st.text_input("Title"); c=st.text_area("Content")
            if st.form_submit_button("Save"):
                with get_local_conn() as conn:
                    conn.execute("INSERT INTO local_notes (title,content,created_at) VALUES (?,?,?)",(t,c,datetime.utcnow().isoformat()))
                    conn.commit()
                st.success("Saved")
    with tab2:
        df=pd.read_sql("SELECT * FROM local_notes ORDER BY id DESC",get_local_conn())
        for _,r in df.iterrows():
            st.subheader(r["title"]); st.write(r["content"]); st.caption(r["created_at"])
            if st.button("Delete",key=f"del_{r['id']}"):
                with get_local_conn() as conn:
                    conn.execute("DELETE FROM local_notes WHERE id=?",(r["id"],)); conn.commit()
                st.experimental_rerun()

# -------------------------
# SCHEDULE UI
# -------------------------
def ui_schedule():
    st.header("📅 Schedule")
    with st.form("add_task"):
        t=st.text_input("Task"); d=st.date_input("Date",value=date.today()); ti=st.time_input("Time",value=time(17,0))
        if st.form_submit_button("Add"):
            with get_local_conn() as conn:
                conn.execute("INSERT INTO local_schedule (task,date,time) VALUES (?,?,?)",(t,d.isoformat(),ti.isoformat())); conn.commit()
            st.success("Added")
    df=pd.read_sql("SELECT * FROM local_schedule ORDER BY date,time",get_local_conn())
    st.table(df if not df.empty else pd.DataFrame())

# -------------------------
# STUDY MATERIALS
# -------------------------
def ui_study_materials():
    st.header("📚 Study Materials")
    mats={"Math":["Algebra","Geometry","Trigonometry"],"Biology":["Cell","Genetics"],"English":["Grammar","Comprehension"]}
    subj=st.selectbox("Subject",list(mats.keys()))
    for ch in mats[subj]: st.markdown(f"- {ch}")

# -------------------------
# EXAM PREP
# -------------------------
def ui_exam_prep():
    st.header("❓ Exam Practice")
    banks={"Math":[("7x8?","56")],"Biology":[("Photosynthesis?","Plants make food")]}
    subj=st.selectbox("Choose subject",list(banks.keys()))
    if st.button("Get Question"):
        q,a=random.choice(banks[subj]); st.write(q)
        ans=st.text_input("Answer"); 
        if st.button("Check"): st.success("Correct") if ans.strip().lower()==a.lower() else st.error(f"Wrong, answer: {a}")

# -------------------------
# BIBLE READER
# -------------------------
def ui_bible_reader():
    st.header("📖 Bible Reader")
    books=["Genesis","Exodus","Leviticus","Numbers","Deuteronomy","Psalms","Proverbs","Matthew","Mark","Luke","John","Acts","Romans","Revelation"]
    book=st.selectbox("Book",books); chap=st.number_input("Chapter",1,100,1)
    if st.button("Load Chapter"): display_bible_chapter(book,chap)
def display_bible_chapter(book,chap):
    try:
        r=requests.get(f"https://bible-api.com/{book}+{chap}",timeout=8).json()
        for v in r.get("verses",[]): st.markdown(f"**{v['book_name']} {v['chapter']}:{v['verse']}** {v['text']}")
    except Exception as e: st.error(e)

# -------------------------
# MAIN APP
# -------------------------
PAGES={
    "Chat": ui_chat_system,
    "Notes": ui_notes,
    "Schedule": ui_schedule,
    "Study": ui_study_materials,
    "Exam Prep": ui_exam_prep,
    "Bible": ui_bible_reader
}

ui_auth()
st.sidebar.title("Navigate")
selection=st.sidebar.radio("Go to",list(PAGES.keys()))
st.markdown(f"### Logged in: {get_my_profile().get('username') if st.session_state.get('user') else 'Not signed in'}")
page_func=PAGES.get(selection)
if page_func: page_func()
else: st.info("Select a page")
