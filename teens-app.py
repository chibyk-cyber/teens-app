# teens_app.py
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

# Dark background + light gray text + sky-blue accents
BASE_CSS = """
<style>
html, body, [class*="css"]  {
  background-color: #121212 !important;
  color: #E0E0E0 !important;
}
.stApp {
  background-color: #121212;
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
    background-color: #1E1E1E;
    color: #E0E0E0;
    padding: 10px;
    border-radius: 12px;
    margin: 6px 0;
    max-width: 78%;
}
.small-muted { color: #a0a0a0; font-size:12px; }
</style>
"""
st.markdown(BASE_CSS, unsafe_allow_html=True)

# -------------------------
# Supabase client (from secrets)
# -------------------------
if "supabase" not in st.session_state:
    try:
        supa_url = st.secrets["supabase"]["https://vkvwxnnirqtkwfhuskvo.supabase.co"]
        supa_key = st.secrets["supabase"]["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZrdnd4bm5pcnF0a3dmaHVza3ZvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTYzMDAzMTcsImV4cCI6MjA3MTg3NjMxN30.-yAV2mYDcesXM5wncmbcq1GlpD60q32lx6pe1bPDKfg"]
        st.session_state["supabase"] = create_client(supa_url, supa_key)
    except Exception as e:
        st.error("Supabase credentials not found in st.secrets. Add them to .streamlit/secrets.toml or your host's secrets.")
        st.stop()

supabase: Client = st.session_state["supabase"]

# -------------------------
# Helper functions (Supabase)
# -------------------------
def signup_user(email: str, password: str, username: str = None):
    """Sign up user via Supabase Auth and create profile row."""
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        # res may require email confirmation depending on your Supabase settings
        user = getattr(res, "user", None) or res.get("user") if isinstance(res, dict) else None
        # If user created, try to insert profile (if profiles table exists)
        if user:
            try:
                supabase.table("profiles").insert({
                    "user_id": user["id"],
                    "email": email,
                    "username": username or email.split("@")[0]
                }).execute()
            except Exception:
                # table may not exist or RLS; ignore here
                pass
        return res
    except Exception as e:
        return {"error": str(e)}

def login_user(email: str, password: str):
    """Sign in and store session user in st.session_state['user']"""
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        user = getattr(res, "user", None) or res.get("user") if isinstance(res, dict) else None
        session = getattr(res, "session", None) or res.get("session") if isinstance(res, dict) else None
        if user:
            # store user object and access token if available
            st.session_state["user"] = user
            if session and session.get("access_token"):
                st.session_state["access_token"] = session["access_token"]
            return {"user": user}
        else:
            return {"error": "Login failed (check credentials or confirm email)."}
    except Exception as e:
        return {"error": str(e)}

def get_my_profile():
    """Try to fetch row from profiles for current user_id; fallback to auth user minimal info."""
    u = st.session_state.get("user")
    if not u:
        return None
    try:
        rows = supabase.table("profiles").select("*").eq("user_id", u["id"]).execute()
        if rows.data and len(rows.data) > 0:
            return rows.data[0]
    except Exception:
        pass
    # fallback
    return {"user_id": u["id"], "email": u.get("email"), "username": u.get("email").split("@")[0]}

def list_profiles(limit=200):
    """Return list of user profiles (id, email, username)."""
    try:
        rows = supabase.table("profiles").select("user_id, email, username").limit(limit).execute()
        return rows.data or []
    except Exception:
        # If profiles table missing or RLS blocks, return empty
        return []

def ensure_tables_exist_check():
    """Quick test to see if required tables exist - returns dict of booleans."""
    ok = {"profiles": False, "groups": False, "group_members": False, "messages": False}
    try:
        # attempt simple selects; if table doesn't exist this will error
        for t in ok.keys():
            try:
                r = supabase.table(t).select("count(*)", count="estimated").limit(1).execute()
                ok[t] = True
            except Exception:
                ok[t] = False
    except Exception:
        pass
    return ok

# -------------------------
# Chat helpers
# -------------------------
def create_group(name: str):
    try:
        res = supabase.table("groups").insert({"name": name, "created_by": st.session_state["user"]["id"]}).execute()
        if res.error:
            st.error(f"Could not create group: {res.error}")
            return None
        gid = res.data[0]["id"]
        # add creator as member
        supabase.table("group_members").insert({"group_id": gid, "user_id": st.session_state["user"]["id"]}).execute()
        return gid
    except Exception as e:
        st.error(f"Error creating group: {e}")
        return None

def join_group(group_id: str):
    try:
        # ensure not already member
        exists = supabase.table("group_members").select("*").eq("group_id", group_id).eq("user_id", st.session_state["user"]["id"]).limit(1).execute()
        if exists.data:
            return True
        supabase.table("group_members").insert({"group_id": group_id, "user_id": st.session_state["user"]["id"]}).execute()
        return True
    except Exception as e:
        st.error(f"Error joining group: {e}")
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
    except Exception as e:
        st.error(f"Error sending message: {e}")
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
    except Exception as e:
        st.error(f"Error sending group message: {e}")
        return False

def fetch_private_conversation(other_user_id: str, limit=200):
    """Return messages between current user and other_user_id ordered ascending by created_at."""
    me = st.session_state["user"]["id"]
    try:
        q = f"""
            (sender_id.eq.{me}.and.receiver_id.eq.{other_user_id}))|((sender_id.eq.{other_user_id}.and.receiver_id.eq.{me}))
        """
        # supabase-py doesn't accept raw filter string easily — use two queries and merge
        a = supabase.table("messages").select("*").eq("sender_id", me).eq("receiver_id", other_user_id).order("created_at", desc=False).limit(limit).execute()
        b = supabase.table("messages").select("*").eq("sender_id", other_user_id).eq("receiver_id", me).order("created_at", desc=False).limit(limit).execute()
        rows = []
        if a.data:
            rows.extend(a.data)
        if b.data:
            rows.extend(b.data)
        # sort by created_at
        rows_sorted = sorted(rows, key=lambda r: r["created_at"])
        return rows_sorted
    except Exception:
        return []

def fetch_group_messages(group_id: str, limit=200):
    try:
        res = supabase.table("messages").select("*").eq("group_id", group_id).order("created_at", desc=False).limit(limit).execute()
        return res.data or []
    except Exception:
        return []

# -------------------------
# Small helpers
# -------------------------
def iso_to_readable(ts: str):
    try:
        return ts.split(".")[0].replace("T", " ")
    except Exception:
        return str(ts)

# -------------------------
# App: Auth UI
# -------------------------
def ui_auth():
    st.sidebar.header("🔐 Account")
    if st.session_state.get("user"):
        prof = get_my_profile()
        st.sidebar.markdown(f"**{prof.get('username') if prof else st.session_state['user'].get('email')}**")
        if st.sidebar.button("Sign out"):
            try:
                supabase.auth.sign_out()
            except Exception:
                pass
            st.session_state.pop("user", None)
            st.experimental_rerun()
        return

    choice = st.sidebar.radio("Sign in / up", ["Login", "Sign Up"])
    email = st.sidebar.text_input("Email", key="auth_email")
    password = st.sidebar.text_input("Password", type="password", key="auth_pass")

    if choice == "Sign Up":
        username = st.sidebar.text_input("Username (optional)", key="auth_un")
        if st.sidebar.button("Create account"):
            if not email or not password:
                st.sidebar.error("Email and password required.")
            else:
                res = signup_user(email, password, username)
                # res may be dict or object - try to inspect
                if isinstance(res, dict) and res.get("error"):
                    st.sidebar.error(res["error"])
                else:
                    st.sidebar.success("Account created — check your email for confirmation if required.")
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
# UI: Chat & Groups (Main)
# -------------------------
def ui_chat_and_groups():
    st.header("💬 Chat & Study Groups (WhatsApp-like)")

    # check tables presence
    ok = ensure_tables_exist_check()
    if not all(ok.values()):
        st.warning("Supabase tables may not be fully set up (profiles/groups/messages...). Some features may not work. See instructions.")
    # left: contacts & groups; right: chat view
    left, right = st.columns([1.4, 3])

    # load profiles
    profiles = list_profiles()
    # build mapping user_id -> username/email
    profile_map = {p["user_id"]: p.get("username") or p.get("email") for p in profiles}

    me = get_my_profile()
    my_id = me.get("user_id") if me else None

    with left:
        st.subheader("Contacts")
        # show all profiles except current
        other_profiles = [p for p in profiles if p.get("user_id") != my_id]
        if other_profiles:
            for p in other_profiles:
                name = p.get("username") or p.get("email")
                if st.button(f"Chat: {name}", key=f"chat_btn_{p['user_id']}"):
                    st.session_state["open_chat_user"] = p["user_id"]
                    st.session_state.pop("open_group", None)
        else:
            st.info("No other users found. Ask friends to sign up.")

        st.divider()
        st.subheader("Groups")
        groups = list_groups()
        if groups:
            for g in groups:
                if st.button(f"{g['name']}", key=f"group_btn_{g['id']}"):
                    st.session_state["open_group"] = g["id"]
                    st.session_state.pop("open_chat_user", None)
            st.write("---")
        else:
            st.info("No groups yet.")

        # create/join group
        with st.form("create_group", clear_on_submit=True):
            new_name = st.text_input("Create group (name)")
            create = st.form_submit_button("Create Group")
            if create and new_name:
                gid = create_group(new_name)
                if gid:
                    st.success("Group created")
                    st.experimental_rerun()

        st.divider()
        st.write("Quick actions")
        if st.button("Refresh contacts/groups"):
            st.experimental_rerun()

    with right:
        # if private chat selected
        if st.session_state.get("open_chat_user"):
            other_id = st.session_state["open_chat_user"]
            display_name = profile_map.get(other_id, other_id)
            st.subheader(f"Chat with {display_name}")
            # show history
            msgs = fetch_private_conversation(other_id)
            if msgs:
                for m in msgs:
                    sender = m["sender_id"]
                    content = m["content"]
                    ts = iso_to_readable(m["created_at"])
                    if sender == my_id:
                        st.markdown(f'<div class="chat-bubble-sent">{content}<div class="small-muted">{ts}</div></div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="chat-bubble-recv"><b>{profile_map.get(sender, sender)}</b><br/>{content}<div class="small-muted">{ts}</div></div>', unsafe_allow_html=True)
            else:
                st.info("No messages yet — say hi!")

            # send message
            with st.form("send_priv", clear_on_submit=True):
                msg = st.text_area("Message", key="pm_txt", height=90)
                if st.form_submit_button("Send"):
                    if msg.strip():
                        ok = send_message_private(other_id, msg.strip())
                        if ok:
                            st.success("Sent")
                            st.experimental_rerun()
                        else:
                            st.error("Could not send message.")
                    else:
                        st.warning("Type a message first.")

        # if group selected
        elif st.session_state.get("open_group"):
            gid = st.session_state["open_group"]
            ginfo = next((g for g in groups if g["id"] == gid), None)
            st.subheader(f"Group: {ginfo['name'] if ginfo else gid}")
            members = get_group_members(gid)
            # show members (names)
            if members:
                mnames = [profile_map.get(mid, mid) for mid in members]
                st.caption("Members: " + ", ".join(mnames))
            else:
                st.caption("No members listed.")

            # join group if not a member
            if my_id and my_id not in members:
                if st.button("Join Group"):
                    join_group(gid)
                    st.success("Joined group")
                    st.experimental_rerun()

            # show messages
            msgs = fetch_group_messages(gid)
            if msgs:
                for m in msgs:
                    sender = m["sender_id"]
                    content = m["content"]
                    ts = iso_to_readable(m["created_at"])
                    if sender == my_id:
                        st.markdown(f'<div class="chat-bubble-sent">{content}<div class="small-muted">{ts}</div></div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="chat-bubble-recv"><b>{profile_map.get(sender, sender)}</b><br/>{content}<div class="small-muted">{ts}</div></div>', unsafe_allow_html=True)
            else:
                st.info("No messages in this group yet.")

            # send group message
            with st.form("send_group_msg", clear_on_submit=True):
                gm = st.text_area("Message to group", key="g_txt", height=90)
                if st.form_submit_button("Send"):
                    if gm.strip():
                        ok = send_message_group(gid, gm.strip())
                        if ok:
                            st.success("Sent to group")
                            st.experimental_rerun()
                        else:
                            st.error("Could not send message.")
                    else:
                        st.warning("Type a message first.")
        else:
            st.info("Select a contact or group on the left to start chatting.")

# -------------------------
# Other app UI: Notes, Schedule, Study, Exam, Bible
# -------------------------
# (Light implementations, still backed by Supabase where appropriate;
# keep local sqlite for quick notes or use Supabase 'notes' table depending on your preference.
# For simplicity we'll use local SQLite for offline notes and Supabase for chat & profiles.)

# Local SQLite for notes & schedule (keeps data local to app instance)
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

def ui_notes():
    st.header("📝 Notes (local)")
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
        else:
            st.info("No notes yet.")

def ui_schedule():
    st.header("📅 Schedule (local)")
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
    if not df.empty:
        st.table(df)
    else:
        st.info("No scheduled tasks.")

def ui_study_materials():
    st.header("📚 Study Materials")
    # We'll use a small in-code list for simplicity
    materials = {
        "Mathematics": ["Algebra", "Geometry", "Trigonometry", "Calculus"],
        "Biology": ["Cell Biology", "Genetics", "Ecology"],
        "English": ["Grammar", "Comprehension", "Essay writing"]
    }
    subj = st.selectbox("Subject", list(materials.keys()))
    st.write("Chapters:")
    for ch in materials[subj]:
        st.markdown(f"- {ch}")

def ui_exam_prep():
    st.header("❓ Exam Practice")
    banks = {
        "Math": [("What is 7×8?","56"),("Solve: x+2=5","3")],
        "Biology":[("What is photosynthesis?","Process by which plants make food")]
    }
    subject = st.selectbox("Choose subject", list(banks.keys()))
    if st.button("Get Question"):
        q, a = random.choice(banks[subject])
        st.write(q)
        ans = st.text_input("Your answer")
        if st.button("Check"):
            if ans.strip().lower() == a.lower():
                st.success("Correct!")
            else:
                st.error(f"Not quite. Answer: {a}")

# Bible (Daily Verse on home + Bible tab handled separately)
def ui_bible_reader():
    st.header("📖 Bible Reader (select book & chapter)")
    ALL_BOOKS = ["Genesis","Exodus","Leviticus","Numbers","Deuteronomy","Psalms","Proverbs","Isaiah","Matthew","Mark","Luke","John","Acts","Romans","Revelation"]
    book = st.selectbox("Book", ALL_BOOKS, index=ALL_BOOKS.index("John") if "John" in ALL_BOOKS else 0)
    chap = st.number_input("Chapter", min_value=1, value=1)
    if st.button("Load Chapter"):
        display_bible_chapter(book, chap)
    verse = st.text_input("Or specific verse/range (e.g. 3:16 or 3:16-18)")
    if st.button("Get Verse/Range"):
        # interpret verse input
        if ":" in verse:
            try:
                cpart, vpart = verse.split(":",1)
                display_bible_api(book, int(cpart), vpart)
            except Exception:
                st.error("Format should be Chapter:Verse or Chapter:Verse-Range")
        else:
            display_bible_api(book, chap, verse)

# Daily verse for homepage
def display_bible_api(book, chapter, verse_or_range):
    book_q = book.replace(" ", "+")
    url = f"https://bible-api.com/{book_q}+{chapter}:{verse_or_range}"
    try:
        r = requests.get(url, timeout=8)
        if r.status_code != 200:
            st.error("Verse not found.")
            return
        data = r.json()
        if isinstance(data, dict) and "verses" in data:
            for v in data["verses"]:
                reference = f"{v.get('book_name','')} {v.get('chapter','')}:{v.get('verse','')}"
                _bible_card(reference, v.get("text",""))
        elif isinstance(data, dict) and "text" in data:
            _bible_card(data.get("reference",""), data.get("text",""))
        if data.get("translation_name"):
            st.caption(f"Translation: {data.get('translation_name')}")
    except Exception as e:
        st.error(f"Bible API error: {e}")

def display_bible_chapter(book, chapter):
    book_q = book.replace(" ", "+")
    url = f"https://bible-api.com/{book_q}+{chapter}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            st.error("Could not fetch chapter.")
            return
        data = r.json()
        verses = data.get("verses", [])
        for v in verses:
            reference = f"{v.get('book_name','')} {v.get('chapter','')}:{v.get('verse','')}"
            _bible_card(reference, v.get("text",""))
        if data.get("translation_name"):
            st.caption(f"Translation: {data.get('translation_name')}")
    except Exception as e:
        st.error(f"Error: {e}")

def _bible_card(reference, text):
    st.markdown(f"""
        <div style="
            background-color: rgba(255,255,255,0.02);
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 8px;
            color: #87CEEB;
            line-height: 1.6;
        ">
            <b>{reference}</b><br>{text}
        </div>
    """, unsafe_allow_html=True)

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

# Authentication controls in sidebar
ui_auth()

st.sidebar.title("Navigate")
selection = st.sidebar.radio("Go to", list(PAGES.keys()))

# Home card with daily verse
if selection is None:
    selection = "Chat & Groups"

# show a home summary on top
st.markdown("---")
st.markdown(f"### Logged in: {get_my_profile().get('username') if st.session_state.get('user') else 'Not signed in'}")
st.markdown("---")

# call selected page
page_func = PAGES.get(selection)
if page_func:
    page_func()
else:
    st.info("Select a page")


