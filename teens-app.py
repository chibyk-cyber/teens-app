import streamlit as st
import requests
import os
import random
import time
from datetime import datetime

# Try to import supabase with error handling
try:
    import supabase
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    st.error("Supabase package not installed. Please install it with: pip install supabase")

# Page configuration
st.set_page_config(
    page_title="TeenConnect",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #4CAF50;
        text-align: center;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2196F3;
    }
    .card {
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
        margin: 10px 0;
        background-color: #f9f9f9;
    }
    .chat-message {
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
    }
    .user-message {
        background-color: #DCF8C6;
        text-align: right;
    }
    .other-message {
        background-color: #F1F0F0;
    }
    .subject-card {
        background: linear-gradient(135deg, #6e8efb, #a777e3);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .music-player {
        background: linear-gradient(135deg, #ff7e5f, #feb47b);
        padding: 15px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    .group-card {
        background: linear-gradient(135deg, #a8edea, #fed6e3);
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Supabase client
supabase_client = None
if SUPABASE_AVAILABLE:
    try:
        # Get credentials from Streamlit secrets
        SUPABASE_URL = st.secrets["supabase"]["url"]
        SUPABASE_KEY = st.secrets["supabase"]["key"]
        
        if SUPABASE_URL and SUPABASE_KEY:
            supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)
            st.success("✅ Connected to Supabase successfully!")
        else:
            st.error("❌ Supabase credentials not found. Please check your secrets.")
    except Exception as e:
        st.error(f"❌ Could not connect to Supabase: {str(e)}")

# API Keys (you should add these to your Streamlit secrets)
BIBLE_API_KEY = st.secrets.get("bible_api", {}).get("key", "free_key")  # Using free tier
MUSIC_API_KEY = st.secrets.get("music_api", {}).get("key", "demo_key")

# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'profile' not in st.session_state:
    st.session_state.profile = {}
if 'page' not in st.session_state:
    st.session_state.page = 'Home'

# Bible API function
def get_bible_verse(book, chapter, verse):
    try:
        url = f"https://api.scripture.api.bible/v1/bibles/06125adad2d5898a-01/passages/{book}.{chapter}.{verse}"
        headers = {"api-key": BIBLE_API_KEY}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            return data['data']['content']
        else:
            return "For God so loved the world that he gave his one and only Son... - John 3:16"
    except:
        return "The Lord bless you and keep you... - Numbers 6:24-25"

# Music API function (using YouTube Data API as example)
def search_worship_music(query):
    try:
        # This is a simplified example - you'd need to set up YouTube Data API properly
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": f"{query} worship song",
            "type": "video",
            "maxResults": 5,
            "key": MUSIC_API_KEY
        }
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            return [{
                "title": item['snippet']['title'],
                "artist": item['snippet']['channelTitle'],
                "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
            } for item in data['items']]
        else:
            # Fallback to predefined songs
            return [
                {"title": "Amazing Grace", "artist": "Chris Tomlin", "url": "https://cdn.pixabay.com/download/audio/2022/01/20/audio_5c27c9508f.mp3?filename=amazing-grace-121002.mp3"},
                {"title": "What a Beautiful Name", "artist": "Hillsong Worship", "url": "https://cdn.pixabay.com/download/audio/2021/10/25/audio_5b86d4f9c0.mp3?filename=inspirational-background-music-112834.mp3"}
            ]
    except:
        # Fallback if API fails
        return [
            {"title": "Amazing Grace", "artist": "Chris Tomlin", "url": "https://cdn.pixabay.com/download/audio/2022/01/20/audio_5c27c9508f.mp3?filename=amazing-grace-121002.mp3"},
            {"title": "What a Beautiful Name", "artist": "Hillsong Worship", "url": "https://cdn.pixabay.com/download/audio/2021/10/25/audio_5b86d4f9c0.mp3?filename=inspirational-background-music-112834.mp3"}
        ]

# Authentication functions with FULL Supabase integration
def sign_up(email, password, username, number):
    try:
        if not supabase_client:
            return False, "Supabase not configured. Please check your settings."
        
        # Create user with Supabase Auth
        auth_response = supabase_client.auth.sign_up({
            "email": email,
            "password": password,
        })
        
        if auth_response.user:
            # Create profile in profiles table
            profile_response = supabase_client.table("profiles").insert({
                "id": auth_response.user.id,
                "username": username,
                "number": number
            }).execute()
            
            # Get the created profile
            if profile_response.data:
                st.session_state.profile = profile_response.data[0]
                st.session_state.user = auth_response.user
                return True, "Sign up successful! Please check your email to verify your account."
            else:
                return False, "Error creating profile."
        else:
            return False, "Error creating account."
    
    except Exception as e:
        return False, f"Error: {str(e)}"

def sign_in(email, password):
    try:
        if not supabase_client:
            return False, "Supabase not configured. Please check your settings."
        
        response = supabase_client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user:
            st.session_state.user = response.user
            
            # Get user profile
            profile = supabase_client.table("profiles").select("*").eq("id", response.user.id).execute()
            if profile.data:
                st.session_state.profile = profile.data[0]
                return True, "Login successful!"
            else:
                return False, "Profile not found. Please contact support."
        else:
            return False, "Login failed. Please check your credentials."
    
    except Exception as e:
        return False, f"Error: {str(e)}"

def sign_out():
    try:
        if supabase_client:
            supabase_client.auth.sign_out()
        st.session_state.user = None
        st.session_state.profile = {}
        st.session_state.page = 'Home'
        st.rerun()
    except Exception as e:
        st.error(f"Error signing out: {str(e)}")

def check_auth():
    if 'user' not in st.session_state:
        # Try to get the current session from Supabase
        if supabase_client:
            try:
                session = supabase_client.auth.get_session()
                if session:
                    st.session_state.user = session.user
                    # Get user profile
                    profile = supabase_client.table("profiles").select("*").eq("id", session.user.id).execute()
                    if profile.data:
                        st.session_state.profile = profile.data[0]
            except:
                pass
    
    return st.session_state.user is not None

# Authentication wrapper
def require_auth(func):
    def wrapper(*args, **kwargs):
        if not check_auth():
            login_page()
            return
        return func(*args, **kwargs)
    return wrapper

# Login page
def login_page():
    st.title("👥 TeenConnect")
    st.markdown("### Welcome! Please sign in or create an account.")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Login")
            
            if login_btn:
                success, message = sign_in(email, password)
                if success:
                    st.success(message)
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(message)
    
    with tab2:
        with st.form("signup_form"):
            email = st.text_input("Email")
            username = st.text_input("Username")
            number = st.text_input("4+ Digit Code", max_chars=6)
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            signup_btn = st.form_submit_button("Create Account")
            
            if signup_btn:
                if not number.isdigit() or len(number) < 4:
                    st.error("Please enter a valid 4+ digit code")
                elif password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    success, message = sign_up(email, password, username, number)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

# Navigation sidebar
@require_auth
def navigation():
    with st.sidebar:
        username = st.session_state.profile.get('username', 'User')
        user_code = st.session_state.profile.get('number', '0000')
        
        st.title(f"👋 Hi, {username}!")
        st.write(f"Your code: #{user_code}")
        st.caption("🔐 Authenticated via Supabase")
        
        st.divider()
        
        pages = {
            "🏠 Home": "Home",
            "📖 Bible Reader": "Bible Reader",
            "🎶 Music Player": "Music Player",
            "🎮 Games": "Games",
            "📚 Study Hub": "Study Hub",
            "💬 Chat & Groups": "Chat & Groups",
            "👤 Profile": "Profile"
        }
        
        selected = st.radio("Navigate", list(pages.keys()))
        st.session_state.page = pages[selected]
        
        st.divider()
        if st.button("🚪 Logout"):
            sign_out()

# Home page
@require_auth
def home_page():
    st.markdown('<h1 class="main-header">👥 TeenConnect</h1>', unsafe_allow_html=True)
    st.markdown("### Welcome to your safe space for connection, inspiration, and fun!")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📖 Bible Verse of the Day")
        verse_text = get_bible_verse("JHN", 3, 16)  # John 3:16
        st.write(verse_text)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("🎵 Today's Playlist")
        songs = search_worship_music("christian worship")
        for song in songs[:3]:
            st.write(f"• {song['title']} - {song['artist']}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("🎮 Game of the Day")
        st.write("Try our new Bible Trivia game! Test your knowledge and earn points.")
        st.markdown('</div>', unsafe_allow_html=True)

# Bible Reader page with API integration
@require_auth
def bible_reader_page():
    st.markdown('<h1 class="sub-header">📖 Bible Reader</h1>', unsafe_allow_html=True)
    
    books_of_bible = [
        {"name": "Genesis", "abbr": "GEN"},
        {"name": "Exodus", "abbr": "EXO"},
        {"name": "Matthew", "abbr": "MAT"},
        {"name": "John", "abbr": "JHN"},
        {"name": "Romans", "abbr": "ROM"}
    ]
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        selected_book = st.selectbox("Select Book", books_of_bible, format_func=lambda x: x["name"])
        chapter = st.number_input("Chapter", min_value=1, max_value=50, value=1)
        verse = st.number_input("Verse", min_value=1, max_value=50, value=1)
        
        if st.button("Lookup Verse"):
            st.session_state.lookup_verse = True
    
    with col2:
        if st.session_state.get('lookup_verse', False):
            verse_text = get_bible_verse(selected_book["abbr"], chapter, verse)
            st.markdown(f'<div class="card"><h3>{selected_book["name"]} {chapter}:{verse}</h3><p>{verse_text}</p></div>', unsafe_allow_html=True)
        else:
            st.info("Select a book, chapter, and verse to begin reading.")

# Music Player page with API integration
@require_auth
def music_player_page():
    st.markdown('<h1 class="sub-header">🎶 Music Player</h1>', unsafe_allow_html=True)
    
    # Search for worship music
    search_query = st.text_input("Search for worship songs:", "Hillsong")
    songs = search_worship_music(search_query)
    
    for i, song in enumerate(songs):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**{song['title']}**")
            st.write(f"*{song['artist']}*")
        with col2:
            if st.button("▶️ Play", key=f"play_{i}"):
                st.session_state.current_song = song
                st.success(f"Playing: {song['title']}")
    
    if st.session_state.current_song:
        st.audio(st.session_state.current_song['url'], format="audio/mp3")

# Chat & Groups page with Supabase integration
@require_auth
def chat_page():
    st.markdown('<h1 class="sub-header">💬 Chat & Groups</h1>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Direct Message", "Study Groups"])
    
    with tab1:
        st.subheader("Chat with another user")
        
        # Input for receiver's number
        receiver_number = st.text_input("Enter the recipient's 4-digit code:", max_chars=4, key="dm_code")
        
        if receiver_number and len(receiver_number) == 4 and receiver_number.isdigit():
            # Find receiver in Supabase
            try:
                profile_response = supabase_client.table("profiles").select("*").eq("number", receiver_number).execute()
                if profile_response.data:
                    receiver = profile_response.data[0]
                    
                    st.success(f"Found user: {receiver.get('username', 'Unknown User')}")
                    
                    # Get messages from Supabase
                    messages_response = supabase_client.table("messages").select("*").or_(f"sender_id.eq.{st.session_state.profile['id']},receiver_number.eq.{receiver_number}").execute()
                    
                    # Display messages
                    st.subheader(f"Chat with {receiver.get('username', 'Unknown User')}")
                    for msg in messages_response.data:
                        if msg['sender_id'] == st.session_state.profile['id']:
                            st.markdown(f'<div class="chat-message user-message"><b>You:</b> {msg["message"]} <i>({msg.get("created_at", "")})</i></div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="chat-message other-message"><b>{receiver.get("username", "Unknown")}:</b> {msg["message"]} <i>({msg.get("created_at", "")})</i></div>', unsafe_allow_html=True)
                    
                    # Send message
                    new_message = st.text_input("Type your message:", key="dm_message")
                    if st.button("Send", key="dm_send"):
                        if new_message:
                            # Save to Supabase
                            supabase_client.table("messages").insert({
                                "sender_id": st.session_state.profile['id'],
                                "receiver_number": receiver_number,
                                "message": new_message
                            }).execute()
                            st.success("Message sent!")
                            st.rerun()
                else:
                    st.error("No user found with that code.")
            except Exception as e:
                st.error(f"Error accessing database: {str(e)}")
    
    with tab2:
        st.subheader("Study Groups")
        st.info("Study groups feature coming soon!")

# Main app logic
def main():
    if not supabase_client:
        st.error("""
        ## Supabase not configured
        Please make sure you have:
        1. Added your Supabase URL and key to Streamlit secrets
        2. Installed the supabase package: `pip install supabase`
        3. Created the required tables in Supabase
        """)
        return
    
    if not check_auth():
        login_page()
    else:
        navigation()
        
        if st.session_state.page == "Home":
            home_page()
        elif st.session_state.page == "Bible Reader":
            bible_reader_page()
        elif st.session_state.page == "Music Player":
            music_player_page()
        elif st.session_state.page == "Chat & Groups":
            chat_page()
        elif st.session_state.page == "Profile":
            st.info("Profile page coming soon!")

if __name__ == "__main__":
    main()
