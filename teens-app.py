# teens_app.py
import streamlit as st
import sqlite3
from datetime import datetime, date, time
import pandas as pd
import random
import requests
import json
from supabase import create_client, Client

st.set_page_config(page_title="Teens App", layout="wide", page_icon="✨")

# -------------------------
# STYLING: Mature dark theme
# -------------------------
BASE_CSS = """
<style>
html, body, [class*="css"]  {
  background-color: #121212 !important;
  color: #E0E0E0 !important;
}
.stApp { background-color: #121212; }
h1, h2, h3, h4, h5, h6, label, span, p, div, li { color: #E0E0E0 !important; }
.stButton>button, .stDownloadButton>button {
  background-color: #00c853 !important;
  color: #fff !important;
  border-radius: 8px;
  font-weight: 600;
}
input, textarea, .stTextInput>div>div, .stTextArea>div>div {
  background-color: rgba(255,255,255,0.04) !important;
  color: #E0E0E0 !important;
  border: 1px solid rgba(255,255,255,0.06) !important;
}
.chat-bubble-sent {
    background-color: #00c853;
    color: #fff;
    padding: 12px;
    border-radius: 14px;
    margin: 6px 0;
    max-width: 75%;
    margin-left: auto;
    box-shadow: 0 2px 6px rgba(0,0,0,0.5);
}
.chat-bubble-recv {
    background-color: #1e1e1e;
    color: #d0eaff;
    padding: 12px;
    border-radius: 14px;
    margin: 6px 0;
    max-width: 75%;
    box-shadow: 0 1px 4px rgba(0,0,0,0.3);
}
.contact-card, .group-card {
    background-color: #1e1e1e;
    padding: 10px 14px;
    border-radius: 12px;
    margin-bottom: 8px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.6);
    cursor: pointer;
    transition: all 0.2s ease;
}
.contact-card:hover, .group-card:hover { background-color: #272727; }
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
        st.error("Supabase credentials not found in st.secrets.")
        st.stop()

supabase: Client = st.session_state["supabase"]

# -------------------------
# Helper functions (Supabase)
# -------------------------
def signup_user(email: str, password: str, username: str = None):
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        user = getattr(res, "user", None) or res.get("user") if isinstance(res, dict) else None
        if user:
            try:
                supabase.table("profiles").insert({
                    "user_id": user["id"],
                    "email": email,
                    "username": username or email.split("@")[0]
                }).execute()
            except Exception: pass
        return res
    except Exception as e: return {"error": str(e)}

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
            return {"error": "Login failed."}
    except Exception as e: return {"error": str(e)}

def get_my_profile():
    u = st.session_state.get("user")
    if not u: return None
    try:
        rows = supabase.table("profiles").select("*").eq("user_id", u["id"]).execute()
        if rows.data and len(rows.data) > 0: return rows.data[0]
    except Exception: pass
    return {"user_id": u["id"], "email": u.get("email"), "username": u.get("email").split("@")[0]}

def list_profiles(limit=200):
    try:
        rows = supabase.table("profiles").select("user_id,email,username").limit(limit).execute()
        return rows.data or []
    except Exception: return []

def ensure_tables_exist_check():
    ok = {"profiles": False, "groups": False, "group_members": False, "messages": False}
    try:
        for t in ok.keys():
            try: supabase.table(t).select("count(*)", count="estimated").limit(1).execute(); ok[t]=True
            except Exception: ok[t]=False
    except Exception: pass
    return ok

# -------------------------
# Chat helpers
# -------------------------
def create_group(name: str):
    try:
        res = supabase.table("groups").insert({"name": name,"created_by": st.session_state["user"]["id"]}).execute()
        if res.error: st.error(f"Could not create group: {res.error}"); return None
        gid = res.data[0]["id"]
        supabase.table("group_members").insert({"group_id": gid,"user_id": st.session_state["user"]["id"]}).execute()
        return gid
    except Exception as e: st.error(f"Error creating group: {e}"); return None

def join_group(group_id: str):
    try:
        exists = supabase.table("group_members").select("*").eq("group_id", group_id).eq("user_id", st.session_state["user"]["id"]).limit(1).execute()
        if exists.data: return True
        supabase.table("group_members").insert({"group_id": group_id,"user_id": st.session_state["user"]["id"]}).execute()
        return True
    except Exception as e: st.error(f"Error joining group: {e}"); return False

def list_groups():
    try: return supabase.table("groups").select("*").order("created_at", desc=True).execute().data or []
    except Exception: return []

def get_group_members(group_id: str):
    try: return [r["user_id"] for r in supabase.table("group_members").select("user_id").eq("group_id", group_id).execute().data or []]
    except Exception: return []

def send_message_private(receiver_user_id: str, content: str):
    try:
        supabase.table("messages").insert({
            "sender_id": st.session_state["user"]["id"],
            "receiver_id": receiver_user_id,
            "group_id": None,
            "content": content
        }).execute()
        return True
    except Exception as e: st.error(f"Error sending message: {e}"); return False

def send_message_group(group_id: str, content: str):
    try:
        supabase.table("messages").insert({
            "sender_id": st.session_state["user"]["id"],
            "receiver_id": None,
            "group_id": group_id,
            "content": content
        }).execute()
        return True
    except Exception as e: st.error(f"Error sending group message: {e}"); return False

def fetch_private_conversation(other_user_id: str, limit=200):
    me = st.session_state["user"]["id"]
    try:
        a = supabase.table("messages").select("*").eq("sender_id", me).eq("receiver_id", other_user_id).order("created_at", desc=False).limit(limit).execute()
        b = supabase.table("messages").select("*").eq("sender_id", other_user_id).eq("receiver_id", me).order("created_at", desc=False).limit(limit).execute()
        rows = (a.data or []) + (b.data or [])
        return sorted(rows, key=lambda r: r["created_at"])
    except Exception: return []

def fetch_group_messages(group_id: str, limit=200):
    try: return supabase.table("messages").select("*").eq("group_id", group_id).order("created_at", desc=False).limit(limit).execute().data or []
    except Exception: return []

def iso_to_readable(ts: str): return ts.split(".")[0].replace("T"," ") if ts else str(ts)

# -------------------------
# Local SQLite for Notes/Schedule
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
# UI: Auth
# -------------------------
def ui_auth():
    st.sidebar.header("🔐 Account")
    if st.session_state.get("user"):
        prof = get_my_profile()
        st.sidebar.markdown(f"**{prof.get('username') if prof else st.session_state['user'].get('email')}**")
        if st.sidebar.button("Sign out"):
            try: supabase.auth.sign_out()
            except Exception: pass
            st.session_state.pop("user", None)
            st.experimental_rerun()
        return
    choice = st.sidebar.radio("Sign in / up", ["Login", "Sign Up"])
    email = st.sidebar.text_input("Email", key="auth_email")
    password = st.sidebar.text_input("Password", type="password", key="auth_pass")
    if choice=="Sign Up":
        username = st.sidebar.text_input("Username (optional)", key="auth_un")
        if st.sidebar.button("Create account"):
            if not email or not password: st.sidebar.error("Email and password required.")
            else:
                res = signup_user(email,password,username)
                if isinstance(res, dict) and res.get("error"): st.sidebar.error(res["error"])
                else: st.sidebar.success("Account created — check email if required.")
    else:
        if st.sidebar.button("Login"):
            if not email or not password: st.sidebar.error("Email and password required.")
            else:
                res = login_user(email,password)
                if res.get("error"): st.sidebar.error(res["error"])
                else: st.sidebar.success("Logged in"); st.experimental_rerun()

# -------------------------
# UI: Chat & Groups
# -------------------------
def ui_chat_and_groups():
    st.header("💬 Chat & Study Groups")
    ok = ensure_tables_exist_check()
    if not all(ok.values()): st.warning("Supabase tables may be missing.")

    left,right = st.columns([1.4,3])
    profiles = list_profiles()
    profile_map = {p["user_id"]: p.get("username") or p.get("email") for p in profiles}
    me = get_my_profile(); my_id = me.get("user_id") if me else None

    with left:
        st.subheader("Contacts")
        other_profiles = [p for p in profiles if p.get("user_id") != my_id]
        if other_profiles:
            for p in other_profiles:
                name = p.get("username") or p.get("email")
                if st.button(name, key=f"chat_btn_{p['user_id']}"): 
                    st.session_state["open_chat_user"]=p["user_id"]; st.session_state.pop("open_group", None)
                st.markdown(f'<div class="contact-card">{name}</div>', unsafe_allow_html=True)
        else: st.info("No other users found.")
        st.divider()
        st.subheader("Groups")
        groups = list_groups()
        if groups:
            for g in groups:
                if st.button(g['name'], key=f"group_btn_{g['id']}"):
                    st.session_state["open_group"]=g["id"]; st.session_state.pop("open_chat_user", None)
                st.markdown(f'<div class="group-card">{g["name"]}</div>', unsafe_allow_html=True)
        else: st.info("No groups yet.")

        with st.form("create_group", clear_on_submit=True):
            new_name = st.text_input("Create group (name)")
            if st.form_submit_button("Create Group") and new_name:
                gid=create_group(new_name)
                if gid: st.success("Group created"); st.experimental_rerun()
        st.divider()
        if st.button("Refresh contacts/groups"): st.experimental_rerun()

    with right:
        if st.session_state.get("open_chat_user"):
            other_id = st.session_state["open_chat_user"]
            display_name = profile_map.get(other_id, other_id)
            st.subheader(f"Chat with {display_name}")
            msgs = fetch_private_conversation(other_id)
            if msgs:
                for m in msgs:
                    sender = m["sender_id"]; content = m["content"]; ts = iso_to_readable(m["created_at"])
                    if sender==my_id: st.markdown(f'<div class="chat-bubble-sent">{content}<div class="small-muted">{ts}</div></div>', unsafe_allow_html=True)
                    else: st.markdown(f'<div class="chat-bubble-recv"><b>{profile_map.get(sender,sender)}</b><br/>{content}<div class="small-muted">{ts}</div></div>', unsafe_allow_html=True)
            else: st.info("No messages yet — say hi!")
            with st.form("send_priv", clear_on_submit=True):
                msg=st.text_area("Message",key="pm_txt",height=90)
                if st.form_submit_button("Send"):
                    if msg.strip(): ok=send_message_private(other_id,msg.strip()); ok and st.success("Sent") and st.experimental_rerun()
                    else: st.warning("Type a message first.")
        elif st.session_state.get("open_group"):
            gid = st.session_state["open_group"]
            ginfo = next((g for g in groups if g["id"]==gid),None)
            st.subheader(f"Group: {ginfo['name'] if ginfo else gid}")
            members = get_group_members(gid)
            if members: st.caption("Members: "+", ".join([profile_map.get(mid,mid) for mid in members]))
            else: st.caption("No members listed.")
            if my_id and my_id not in members:
                if st.button("Join Group"): join_group(gid); st.success("Joined group"); st.experimental_rerun()
            msgs = fetch_group_messages(gid)
            if msgs:
                for m in msgs:
                    sender = m["sender_id"]; content = m["content"]; ts = iso_to_readable(m["created_at"])
                    if sender==my_id: st.markdown(f'<div class="chat-bubble-sent">{content}<div class="small-muted">{ts}</div></div>', unsafe_allow_html=True)
                    else: st.markdown(f'<div class="chat-bubble-recv"><b>{profile_map.get(sender,sender)}</b><br/>{content}<div class="small-muted">{ts}</div></div>', unsafe_allow_html=True)
            else: st.info("No messages in this group yet.")
            with st.form("send_group_msg", clear_on_submit=True):
                gm=st.text_area("Message to group",key="g_txt",height=90)
                if st.form_submit_button("Send"): gm.strip() and send_message_group(gid,gm.strip()) and st.success("Sent") and st.experimental_rerun() or st.warning("Type a message first.")
        else: st.info("Select a contact or group on the left to start chatting.")

# -------------------------
# Other pages (Notes, Schedule, Study, Exam, Bible)
# -------------------------
# [Similar to your previous code with local SQLite and Bible API]
# ...keep your previous code for ui_notes(), ui_schedule(), ui_study_materials(), ui_exam_prep(), ui_bible_reader() intact
# -------------------------

# -------------------------
# Main Navigation
# -------------------------
PAGES = {
    "Chat & Groups": ui_chat_and_groups,
    "Notes": ui_notes,
    "Scheduler": ui_schedule,
    "Study Materials": ui_study_materials,
    "Exam Prep": ui_exam_prep,
    "Bible": ui_bible_reader
}

ui_auth()
st.sidebar.title("Navigate")
selection = st.sidebar.radio("Go to", list(PAGES.keys()))
st.markdown("---")
st.markdown(f"### Logged in: {get_my_profile().get('username') if st.session_state.get('user') else 'Not signed in'}")
st.markdown("---")
page_func = PAGES.get(selection)
page_func() if page_func else st.info("Select a page")
