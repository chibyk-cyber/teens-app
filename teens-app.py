# teens_app_full.py
import streamlit as st
import sqlite3
from datetime import datetime, date, time
import pandas as pd
import random
import requests
from supabase import create_client, Client


# ----------------- SUPABASE INIT -----------------
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ----------------- AUTH FUNCTIONS -----------------
def sign_up(email, password, username):
    try:
        auth_response = supabase.auth.sign_up({"email": email, "password": password})
        user = auth_response.user
        if user:
            # save username to profiles table
            supabase.table("profiles").insert({
                "id": user.id,
                "username": username
            }).execute()
            return True, "Account created successfully!"
        else:
            return False, "Error creating account."
    except Exception as e:
        return False, str(e)

def sign_in(email, password):
    try:
        auth_response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return True, auth_response.user
    except Exception as e:
        return False, str(e)

# ----------------- UI PAGE -----------------
def ui_auth_page():
    st.title("🔑 Sign In / Sign Up")
    choice = st.radio("Choose Action", ["Sign In", "Sign Up"])

    if choice == "Sign Up":
        st.subheader("Create New Account")
        email = st.text_input("Email", key="signup_email")
        username = st.text_input("Username", key="signup_username")
        password = st.text_input("Password", type="password", key="signup_password")

        if st.button("Sign Up"):
            ok, msg = sign_up(email, password, username)
            if ok:
                st.success(msg)
            else:
                st.error(msg)

    else:  # Sign In
        st.subheader("Login to your Account")
        email = st.text_input("Email", key="signin_email")
        password = st.text_input("Password", type="password", key="signin_password")

        if st.button("Sign In"):
            ok, result = sign_in(email, password)
            if ok:
                st.session_state["user"] = result
                st.success("✅ Logged in successfully!")
                st.experimental_rerun()
            else:
                st.error(result)

# -------------------------
# CONFIG / STYLING
# -------------------------
st.set_page_config(page_title="Teens App", layout="wide", page_icon="✨")
CSS = """
<style>
html, body, [class*="css"] { background-color:#121212 !important; color:#E8F6F9 !important; }
.stApp { background-color:#121212; }
h1,h2,h3,h4,h5,h6 { color:#BEEAF9 !important; }
.stButton>button { background-color:#87CEEB!important; color:#000!important; font-weight:600; border-radius:8px; }
input, textarea, .stTextInput>div>div, .stTextArea>div>div { background-color: rgba(255,255,255,0.03)!important; color:#E8F6F9!important; border:1px solid rgba(255,255,255,0.04)!important; }
.chat-bubble-sent { background-color:#87CEEB; color:#000; padding:10px; border-radius:12px; margin:6px 0; max-width:78%; margin-left:auto; }
.chat-bubble-recv { background-color:#1F1F1F; color:#E8F6F9; padding:10px; border-radius:12px; margin:6px 0; max-width:78%; }
.small-muted { color:#A0A0A0; font-size:12px; }
.top-nav { background-color:#121212; padding:10px; border-bottom:1px solid #222; display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }
.top-nav h2 { color:#87CEEB; margin:0; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# -------------------------
# SUPABASE CLIENT (secrets)
# -------------------------
# Put your Supabase credentials in .streamlit/secrets.toml as:
# [supabase]
# url = "https://....supabase.co"
# key = "your-anon-or-service-key"
try:
    supa = st.secrets["supabase"]
    SUPA_URL = supa["url"]
    SUPA_KEY = supa["key"]
except Exception:
    st.error("Add Supabase credentials to .streamlit/secrets.toml under [supabase] (url & key).")
    st.stop()

if "supabase" not in st.session_state:
    st.session_state["supabase"] = create_client(SUPA_URL, SUPA_KEY)
supabase: Client = st.session_state["supabase"]

# -------------------------
# LOCAL SQLITE (notes & schedule)
# -------------------------
LOCAL_DB = "teens_local.db"
def get_local_conn():
    c = sqlite3.connect(LOCAL_DB, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c

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
# SUPABASE HELPERS
# -------------------------
def generate_user_number():
    # generate a 4-6 digit number
    return str(random.randint(1000, 999999))

def signup_user(email: str, password: str, username: str = None):
    """Sign up user and create a profile with a numeric ID."""
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        user = getattr(res, "user", None) or (res.get("user") if isinstance(res, dict) else None)
        if user:
            # create profile row
            number = generate_user_number()
            # try a few times if unique constraint fails
            for _ in range(6):
                try:
                    supabase.table("profiles").insert({
                        "user_id": user["id"],
                        "email": email,
                        "username": username or email.split("@")[0],
                        "number": number
                    }).execute()
                    break
                except Exception:
                    number = generate_user_number()
        return res
    except Exception as e:
        return {"error": str(e)}

def login_user(email: str, password: str):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        user = getattr(res, "user", None) or (res.get("user") if isinstance(res, dict) else None)
        session = getattr(res, "session", None) or (res.get("session") if isinstance(res, dict) else None)
        if user:
            st.session_state["user"] = user
            if session and session.get("access_token"):
                st.session_state["access_token"] = session["access_token"]
            return {"user": user}
        return {"error": "Login failed"}
    except Exception as e:
        return {"error": str(e)}

def get_profile_by_user_id(user_id: str):
    try:
        r = supabase.table("profiles").select("*").eq("user_id", user_id).single().execute()
        return r.data
    except Exception:
        return None

def get_profile_by_number(number: str):
    try:
        r = supabase.table("profiles").select("*").eq("number", number).single().execute()
        return r.data
    except Exception:
        return None

def list_profiles(limit=200):
    try:
        r = supabase.table("profiles").select("user_id,email,username,number").limit(limit).execute()
        return r.data or []
    except Exception:
        return []

# messaging helpers use chat_key field (private: sorted user ids joined; group: group name)
def send_message(chat_key: str, sender_id: str, content: str):
    try:
        supabase.table("messages").insert({
            "chat_key": chat_key,
            "sender_id": sender_id,
            "content": content
        }).execute()
        return True
    except Exception:
        return False

def fetch_messages(chat_key: str, limit=500):
    try:
        r = supabase.table("messages").select("*").eq("chat_key", chat_key).order("created_at", desc=False).limit(limit).execute()
        return r.data or []
    except Exception:
        return []

# -------------------------
# BIBLE API
# -------------------------
def fetch_bible_chapter(book: str, chapter: int):
    url = f"https://bible-api.com/{book}+{chapter}"
    try:
        r = requests.get(url, timeout=8)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None

# -------------------------
# UI: Top nav + demo helper
# -------------------------
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

def demo_chat_area():
    st.info("Demo chat (read-only): how chat messages will look.")
    demo_msgs = [
        ("System", "Welcome to Teens App."),
        ("System", "Use the left panel to select contacts or groups."),
        ("System", "Private chats use numeric IDs (4+ digits).")
    ]
    for s, t in demo_msgs:
        st.markdown(f'<div class="chat-bubble-recv"><b>{s}</b><br/>{t}</div>', unsafe_allow_html=True)

# -------------------------
# UI: Auth sidebar
# -------------------------
def ui_auth_sidebar():
    st.sidebar.header("Account")
    if st.session_state.get("user"):
        prof = get_profile_by_user_id(st.session_state["user"]["id"])
        display_name = (prof.get("username") if prof else st.session_state["user"].get("email"))
        number = prof.get("number") if prof else ""
        st.sidebar.markdown(f"**{display_name}**  \nID: `{number}`")
        if st.sidebar.button("Sign out"):
            try:
                supabase.auth.sign_out()
            except Exception:
                pass
            st.session_state.pop("user", None)
            st.experimental_rerun()
        return

    mode = st.sidebar.radio("Sign in / Sign up", ["Login", "Sign Up"])
    if mode == "Sign Up":
        st.sidebar.markdown("Create account")
        email = st.sidebar.text_input("Email", key="su_email")
        password = st.sidebar.text_input("Password", type="password", key="su_pass")
        username = st.sidebar.text_input("Username (optional)", key="su_un")
        if st.sidebar.button("Create account"):
            if not email or not password:
                st.sidebar.error("Email & password required")
            else:
                r = signup_user(email, password, username)
                if isinstance(r, dict) and r.get("error"):
                    st.sidebar.error(r["error"])
                else:
                    st.sidebar.success("Account created — verify email if required. Then log in.")
    else:
        st.sidebar.markdown("Log in")
        email = st.sidebar.text_input("Email", key="li_email")
        password = st.sidebar.text_input("Password", type="password", key="li_pass")
        if st.sidebar.button("Login"):
            if not email or not password:
                st.sidebar.error("Email & password required")
            else:
                res = login_user(email, password)
                if res.get("error"):
                    st.sidebar.error(res["error"])
                else:
                    st.sidebar.success("Logged in")
                    st.experimental_rerun()

ui_auth_sidebar()

# -------------------------
# UI: Chat & Groups (integrated)
# -------------------------
def ui_chat_and_groups():
    st.header("💬 Chat & Groups")
    if "user" not in st.session_state:
        st.info("Sign in to use chat features. Demo below:")
        demo_chat_area()
        return

    # load profiles and mapping
    profiles = list_profiles()
    me_profile = get_profile_by_user_id(st.session_state["user"]["id"])
    my_id = st.session_state["user"]["id"]
    my_number = me_profile.get("number") if me_profile else None
    profile_map = {p["user_id"]: f"{p.get('username') or p.get('email')} ({p.get('number')})" for p in profiles}

    left, right = st.columns([1.4, 3])

    # LEFT: contacts, quick start by number
    with left:
        st.subheader("Quick start (Private)")
        target_num = st.text_input("Friend's Chat ID (4+ digits)", key="private_target")
        if st.button("Open Private Chat"):
            if not target_num:
                st.warning("Enter a valid ID")
            else:
                partner = get_profile_by_number(target_num)
                if not partner:
                    st.error("No user found with that ID")
                else:
                    # set chat_key (sorted user ids)
                    a, b = sorted([my_id, partner["user_id"]])
                    st.session_state["open_chat_key"] = f"{a}_{b}"
                    st.session_state.pop("open_group", None)
                    st.experimental_rerun()

        st.divider()
        st.subheader("Contacts")
        for p in profiles:
            if p["user_id"] == my_id: continue
            label = f'{p.get("username") or p.get("email")} ({p.get("number")})'
            if st.button(label, key=f"c_{p['user_id']}"):
                a, b = sorted([my_id, p["user_id"]])
                st.session_state["open_chat_key"] = f"{a}_{b}"
                st.session_state.pop("open_group", None)
                st.experimental_rerun()

        st.divider()
        st.subheader("Create / Open Group")
        group_name = st.text_input("Group name", key="group_name")
        if st.button("Open/Create Group"):
            if group_name.strip():
                st.session_state["open_group"] = group_name.strip()
                st.session_state.pop("open_chat_key", None)
                st.experimental_rerun()

        st.divider()
        if st.button("Refresh lists"):
            st.experimental_rerun()

    # RIGHT: chat pane
    with right:
        # Private chat mode
        if st.session_state.get("open_chat_key"):
            chat_key = st.session_state["open_chat_key"]
            st.subheader(f"Private chat — {chat_key}")
            msgs = fetch_messages(chat_key)
            if not msgs:
                st.info("No messages yet — say hi!")
            for m in msgs:
                sender = m.get("sender_id")
                ts = m.get("created_at", "")
                if sender == my_id:
                    st.markdown(f'<div class="chat-bubble-sent">{m.get("content")}<div class="small-muted">{ts}</div></div>', unsafe_allow_html=True)
                else:
                    who = profile_map.get(sender, sender)
                    st.markdown(f'<div class="chat-bubble-recv"><b>{who}</b><br/>{m.get("content")}<div class="small-muted">{ts}</div></div>', unsafe_allow_html=True)

            with st.form("send_priv", clear_on_submit=True):
                txt = st.text_area("Message", key="priv_msg", height=90)
                if st.form_submit_button("Send"):
                    if txt.strip():
                        ok = send_message(chat_key, my_id, txt.strip())
                        if not ok:
                            st.error("Could not send message (check Supabase).")
                        else:
                            st.experimental_rerun()
                    else:
                        st.warning("Type a message first.")

        # Group chat mode
        elif st.session_state.get("open_group"):
            group = st.session_state["open_group"]
            st.subheader(f"Group: {group}")
            msgs = fetch_messages(group)
            if not msgs:
                st.info("No messages yet in this group.")
            for m in msgs:
                sender = m.get("sender_id")
                prof = profile_map.get(sender, sender)
                ts = m.get("created_at", "")
                if sender == my_id:
                    st.markdown(f'<div class="chat-bubble-sent">{m.get("content")}<div class="small-muted">{ts}</div></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-bubble-recv"><b>{prof}</b><br/>{m.get("content")}<div class="small-muted">{ts}</div></div>', unsafe_allow_html=True)

            with st.form("send_group", clear_on_submit=True):
                gtxt = st.text_area("Message to group", key="group_msg", height=90)
                if st.form_submit_button("Send"):
                    if gtxt.strip():
                        ok = send_message(group, my_id, gtxt.strip())
                        if not ok:
                            st.error("Could not send message.")
                        else:
                            st.experimental_rerun()
                    else:
                        st.warning("Type a message first.")

        else:
            st.info("Select a contact or create/open a group. Demo below:")
            demo_chat_area()

# -------------------------
# UI: Notes
# -------------------------
def ui_notes():
    st.header("📝 Notes")
    a,b = st.columns([2,1])
    with a:
        with st.form("new_note", clear_on_submit=True):
            title = st.text_input("Title")
            content = st.text_area("Content")
            if st.form_submit_button("Save"):
                with get_local_conn() as conn:
                    conn.execute("INSERT INTO local_notes (title, content, created_at) VALUES (?, ?, ?)",
                                 (title, content, datetime.utcnow().isoformat()))
                    conn.commit()
                st.success("Saved locally")
    with b:
        st.write("Quick actions")
        if st.button("Refresh notes"):
            st.experimental_rerun()

    df = pd.read_sql("SELECT id, title, content, created_at FROM local_notes ORDER BY id DESC", get_local_conn())
    if not df.empty:
        for _, row in df.iterrows():
            st.subheader(row["title"])
            st.write(row["content"])
            st.caption(row["created_at"])
            if st.button("Delete", key=f"del_{row['id']}"):
                with get_local_conn() as conn:
                    conn.execute("DELETE FROM local_notes WHERE id=?", (row["id"],))
                    conn.commit()
                st.experimental_rerun()
    else:
        st.info("No notes yet.")

# -------------------------
# UI: Scheduler
# -------------------------
def ui_schedule():
    st.header("📅 Scheduler")
    with st.form("add_task", clear_on_submit=True):
        task = st.text_input("Task")
        d = st.date_input("Date", value=date.today())
        t = st.time_input("Time", value=time(17,0))
        if st.form_submit_button("Add"):
            with get_local_conn() as conn:
                conn.execute("INSERT INTO local_schedule (task, date, time) VALUES (?, ?, ?)",
                             (task, d.isoformat(), t.isoformat()))
                conn.commit()
            st.success("Added")
    df = pd.read_sql("SELECT id, task, date, time FROM local_schedule ORDER BY date, time", get_local_conn())
    if not df.empty:
        st.table(df)
    else:
        st.info("No tasks scheduled.")

# -------------------------
# UI: Study & Exam
# -------------------------
def ui_study_materials():
    st.header("📚 Study Materials")
    materials = {
        "Mathematics": ["Algebra", "Geometry", "Calculus"],
        "Biology": ["Cell Biology", "Genetics"],
        "English": ["Grammar", "Comprehension"]
    }
    subj = st.selectbox("Subject", list(materials.keys()))
    st.write("Chapters:")
    for ch in materials[subj]:
        st.markdown(f"- {ch}")

def ui_exam_prep():
    st.header("❓ Exam Practice")
    banks = {
        "Math": [("What is 7×8?", "56"), ("Solve x+2=5", "3")],
        "Biology": [("What is photosynthesis?", "Process by which plants make food")]
    }
    subject = st.selectbox("Subject", list(banks.keys()))
    if st.button("Get Question"):
        q, a = random.choice(banks[subject])
        st.write(q)
        ans = st.text_input("Your answer")
        if st.button("Check"):
            if ans.strip().lower() == a.lower():
                st.success("Correct!")
            else:
                st.error(f"Not quite. Answer: {a}")

# -------------------------
# UI: Bible Reader
# -------------------------
def ui_bible():
    st.header("📖 Bible Reader")
    BOOKS = ["Genesis","Exodus","Psalms","Proverbs","Matthew","Mark","Luke","John"]
    book = st.selectbox("Book", BOOKS)
    chap = st.number_input("Chapter", min_value=1, value=1)
    if st.button("Load Chapter"):
        data = fetch_bible_chapter(book, chap)
        if not data:
            st.error("Could not fetch chapter.")
            return
        verses = data.get("verses", [])
        for v in verses:
            ref = f'{v.get("book_name","")} {v.get("chapter","")}:{v.get("verse","")}'
            st.markdown(f"<div style='background-color:rgba(255,255,255,0.02);padding:8px;border-radius:8px;color:#87CEEB'>{ref}: {v.get('text','')}</div>", unsafe_allow_html=True)
# -------------------------
# UI: Auth Page
# -------------------------
def ui_auth_page():
    st.title("🔑 Welcome to Teens App")
    st.write("Please sign in or create an account to continue.")

    tabs = st.tabs(["Login", "Sign Up"])

    # LOGIN TAB
    with tabs[0]:
        st.subheader("Login")
        email = st.text_input("Email", key="auth_email")
        password = st.text_input("Password", type="password", key="auth_pass")
        if st.button("Sign In", key="auth_login"):
            if not email or not password:
                st.error("Email and password required")
            else:
                res = login_user(email, password)
                if res.get("error"):
                    st.error(res["error"])
                else:
                    st.success("✅ Logged in successfully!")
                    st.experimental_rerun()

    # SIGNUP TAB
    with tabs[1]:
        st.subheader("Create Account")
        email = st.text_input("Email", key="auth_su_email")
        password = st.text_input("Password", type="password", key="auth_su_pass")
        username = st.text_input("Username (optional)", key="auth_su_un")
        if st.button("Sign Up", key="auth_signup"):
            if not email or not password:
                st.error("Email and password required")
            else:
                r = signup_user(email, password, username)
                if isinstance(r, dict) and r.get("error"):
                    st.error(r["error"])
                else:
                    st.success("🎉 Account created — check your email if verification required.")
def ui_auth_sidebar():
    st.sidebar.header("Account")

    if st.session_state.get("user"):
        prof = get_profile_by_user_id(st.session_state["user"]["id"])
        display_name = (prof.get("username") if prof else st.session_state["user"].get("email"))
        number = prof.get("number") if prof else ""
        st.sidebar.markdown(f"**{display_name}**  \nID: `{number}`")

        # SIGN OUT BUTTON
        if st.sidebar.button("Sign Out"):
            try:
                supabase.auth.sign_out()
            except Exception:
                pass
            st.session_state.pop("user", None)
            st.success("✅ You have signed out.")
            st.experimental_rerun()  # refresh app
        return

    # If not logged in, show login/signup tabs
    mode = st.sidebar.radio("Sign in / Sign up", ["Login", "Sign Up"])
    if mode == "Sign Up":
        st.sidebar.markdown("Create account")
        email = st.sidebar.text_input("Email", key="su_email")
        password = st.sidebar.text_input("Password", type="password", key="su_pass")
        username = st.sidebar.text_input("Username (optional)", key="su_un")
        if st.sidebar.button("Create account"):
            if not email or not password:
                st.sidebar.error("Email & password required")
            else:
                r = signup_user(email, password, username)
                if isinstance(r, dict) and r.get("error"):
                    st.sidebar.error(r["error"])
                else:
                    st.sidebar.success("🎉 Account created — verify email if required. Then log in.")
    else:
        st.sidebar.markdown("Log in")
        email = st.sidebar.text_input("Email", key="li_email")
        password = st.sidebar.text_input("Password", type="password", key="li_pass")
        if st.sidebar.button("Login"):
            if not email or not password:
                st.sidebar.error("Email & password required")
            else:
                res = login_user(email, password)
                if res.get("error"):
                    st.sidebar.error(res["error"])
                else:
                    st.sidebar.success("✅ Logged in successfully!")
                    st.experimental_rerun()

# -------------------------
# PAGES & RUN
# -------------------------
PAGES = {
    "Chat & Groups": ui_chat_and_groups,
    "Notes": ui_notes,
    "Scheduler": ui_schedule,
    "Study Materials": ui_study_materials,
    "Exam Prep": ui_exam_prep,
    "Bible": ui_bible
}

st.sidebar.title("Navigate")
page = st.sidebar.radio("Go to", list(PAGES.keys()))
st.markdown("---")
if st.session_state.get("user"):
    prof = get_profile_by_user_id(st.session_state["user"]["id"])
    st.sidebar.write(f"Signed in: **{prof.get('username') if prof else st.session_state['user'].get('email')}**")
else:
    st.sidebar.write("Not signed in")
st.markdown("---")
PAGES[page]()


