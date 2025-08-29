import streamlit as st
from supabase import create_client, Client
from datetime import datetime

# -----------------------------
# Supabase Setup
# -----------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------
# Authentication
# -----------------------------
def ui_auth():
    st.title("🔑 Authentication")

    auth_choice = st.radio("Choose Action", ["Sign In", "Sign Up"])

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if auth_choice == "Sign Up":
        if st.button("Sign Up"):
            try:
                auth_response = supabase.auth.sign_up({"email": email, "password": password})
                if "user" in auth_response and auth_response.user:
                    st.success("✅ Account created! Please check your email to confirm.")
            except Exception as e:
                st.error(f"Error: {e}")

    if auth_choice == "Sign In":
        if st.button("Sign In"):
            try:
                auth_response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                if auth_response.user:
                    st.session_state["user"] = email
                    st.success("✅ Logged in successfully!")
            except Exception as e:
                st.error(f"Error: {e}")

    if "user" in st.session_state:
        st.info(f"Logged in as {st.session_state['user']}")
        if st.button("Log Out"):
            st.session_state.pop("user", None)
            st.success("Logged out.")

# -----------------------------
# Home Page
# -----------------------------
def ui_home():
    st.title("🏠 Home")
    st.write("Welcome to Teens App!")

# -----------------------------
# Bible Reader
# -----------------------------
def ui_bible_reader():
    st.title("📖 Bible Reader")
    verse = st.text_area("Enter a verse reference (e.g., John 3:16)")
    if st.button("Read Verse"):
        st.success(f"📖 Showing verse: {verse}")

# -----------------------------
# Notes
# -----------------------------
def ui_notes():
    st.title("📝 Notes")
    if "notes" not in st.session_state:
        st.session_state.notes = []
    note = st.text_area("Write your note here:")
    if st.button("Save Note"):
        st.session_state.notes.append(note)
    st.write("### Your Notes:")
    for i, n in enumerate(st.session_state.notes, 1):
        st.write(f"{i}. {n}")

# -----------------------------
# Profile
# -----------------------------
def ui_profile():
    st.title("👤 Profile")
    if "user" in st.session_state:
        st.write(f"Logged in as: {st.session_state['user']}")
    else:
        st.warning("You need to log in to see your profile.")

# -----------------------------
# Chat (Supabase Integrated)
# -----------------------------
def ui_chat_and_groups():
    st.header("💬 Chat & Groups")

    if "user" not in st.session_state:
        st.warning("You must log in to use the chat feature.")
        return

    username = st.session_state.user

    tab1, tab2 = st.tabs(["Direct Chat", "Group Chat"])

    # DIRECT CHAT
    with tab1:
        st.subheader("Direct Chat")
        friend_id = st.text_input("Enter Friend's ID (at least 4 digits):")
        message = st.text_input("Type your message:")

        if st.button("Send Direct"):
            if friend_id and len(friend_id) >= 4 and message:
                supabase.table("messages").insert({
                    "sender": username,
                    "receiver": friend_id,
                    "message": message,
                    "timestamp": datetime.utcnow().isoformat()
                }).execute()
                st.success(f"Message sent to {friend_id} ✅")

        st.write("### 📥 Your Chats")
        direct_msgs = supabase.table("messages").select("*")\
            .or_(f"sender.eq.{username},receiver.eq.{username}")\
            .order("timestamp", desc=True).execute()

        if direct_msgs.data:
            for msg in direct_msgs.data:
                st.write(f"**{msg['sender']} → {msg['receiver']}**: {msg['message']} ({msg['timestamp']})")
        else:
            st.info("No messages yet.")

    # GROUP CHAT
    with tab2:
        st.subheader("Group Chat")
        group_name = st.text_input("Enter Group Name:")
        group_msg = st.text_input("Type your group message:")

        if st.button("Send to Group"):
            if group_name and group_msg:
                supabase.table("group_messages").insert({
                    "sender": username,
                    "group": group_name,
                    "message": group_msg,
                    "timestamp": datetime.utcnow().isoformat()
                }).execute()
                st.success(f"Message sent to group {group_name} ✅")

        st.write("### 📥 Group Messages")
        if group_name:
            msgs = supabase.table("group_messages").select("*")\
                .eq("group", group_name)\
                .order("timestamp", desc=True).execute()

            if msgs.data:
                for msg in msgs.data:
                    st.write(f"**{msg['sender']}**: {msg['message']} ({msg['timestamp']})")
            else:
                st.info(f"No messages in {group_name} yet.")

# -----------------------------
# Navigation
# -----------------------------
PAGES = {
    "Auth": ui_auth,
    "Home": ui_home,
    "Bible": ui_bible_reader,
    "Notes": ui_notes,
    "Profile": ui_profile,
    "Chat & Groups": ui_chat_and_groups
}
# -----------------------------
# Store (Orders)
# -----------------------------
def ui_store():
    st.title("🛒 Store")

    # Categories
    categories = {
        "Clothes": [
            {"name": "T-shirt", "price": 15},
            {"name": "Jeans", "price": 40},
            {"name": "Hoodie", "price": 35}
        ],
        "Generators": [
            {"name": "Small Generator", "price": 250},
            {"name": "Medium Generator", "price": 500},
            {"name": "Large Generator", "price": 850}
        ]
    }

    # Ensure cart exists
    if "cart" not in st.session_state:
        st.session_state.cart = []

    tab1, tab2 = st.tabs(["🛍️ Browse Products", "🛒 Cart"])

    with tab1:
        for cat, products in categories.items():
            st.subheader(cat)
            for product in products:
                col1, col2 = st.columns([3,1])
                with col1:
                    st.write(f"{product['name']} - **${product['price']}**")
                with col2:
                    if st.button(f"Add {product['name']}", key=product['name']):
                        st.session_state.cart.append(product)
                        st.success(f"✅ {product['name']} added to cart!")

    with tab2:
        st.subheader("Your Cart")
        if not st.session_state.cart:
            st.info("Your cart is empty.")
        else:
            total = 0
            for i, item in enumerate(st.session_state.cart, 1):
                st.write(f"{i}. {item['name']} - ${item['price']}")
                total += item["price"]

            st.write(f"### 💵 Total: ${total}")

            if "user" not in st.session_state:
                st.warning("⚠️ You must log in to checkout.")
            else:
                if st.button("Checkout"):
                    try:
                        order = {
                            "user": st.session_state.user,
                            "items": [item["name"] for item in st.session_state.cart],
                            "total": total,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        supabase.table("orders").insert(order).execute()
                        st.success("✅ Order placed successfully!")
                        st.session_state.cart = []  # Clear cart
                    except Exception as e:
                        st.error(f"Error saving order: {e}")

st.sidebar.title("📌 Navigation")
choice = st.sidebar.radio("Go to", list(PAGES.keys()))
PAGES[choice]()
