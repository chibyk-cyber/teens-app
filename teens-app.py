import streamlit as st
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
</style>
""", unsafe_allow_html=True)

# Initialize Supabase client (if available)
supabase_client = None
if SUPABASE_AVAILABLE:
    try:
        # Get credentials from Streamlit secrets
        SUPABASE_URL = st.secrets["supabase"]["url"]
        SUPABASE_KEY = st.secrets["supabase"]["key"]
        
        if SUPABASE_URL and SUPABASE_KEY:
            supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)
            st.success("✅ Connected to Supabase successfully!")
    except Exception as e:
        st.warning(f"⚠️ Could not connect to Supabase: {str(e)}. Using local storage.")

# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'profile' not in st.session_state:
    st.session_state.profile = {}
if 'page' not in st.session_state:
    st.session_state.page = 'Home'
if 'messages' not in st.session_state:
    st.session_state.messages = {}
if 'users' not in st.session_state:
    st.session_state.users = {}
if 'current_song' not in st.session_state:
    st.session_state.current_song = None

# Sample data
waec_questions = {
    "Mathematics": [
        "1. Simplify: 2⅓ ÷ (2⅔ of 1⅕)",
        "2. If 2x + y = 10 and y = 4, find the value of x",
        "3. Solve the equation: 3x - 5 = 16",
    ],
    "English": [
        "1. Which of these is not a part of speech?",
        "2. Change to indirect speech: 'I will come tomorrow,' she said",
        "3. Identify the figure of speech: 'The stars danced playfully in the moonlit sky'",
    ]
}

study_topics = {
    "Mathematics": ["Algebra", "Geometry", "Calculus"],
    "Biology": ["Cell Biology", "Genetics", "Ecology"],
    "Physics": ["Mechanics", "Thermodynamics", "Electricity"]
}

worship_songs = [
    {"title": "Amazing Grace", "artist": "Chris Tomlin", "url": "https://cdn.pixabay.com/download/audio/2022/01/20/audio_5c27c9508f.mp3?filename=amazing-grace-121002.mp3"},
    {"title": "What a Beautiful Name", "artist": "Hillsong Worship", "url": "https://cdn.pixabay.com/download/audio/2021/10/25/audio_5b86d4f9c0.mp3?filename=inspirational-background-music-112834.mp3"}
]

# Authentication functions
def sign_up(email, password, username, number):
    try:
        # Always use local storage for Streamlit Cloud compatibility
        user_id = f"user{random.randint(1000, 9999)}"
        st.session_state.users[user_id] = {
            'username': username,
            'number': number,
            'password': password,
            'email': email
        }
        st.session_state.profile = st.session_state.users[user_id]
        return True, "Sign up successful! Please log in."
    
    except Exception as e:
        return False, f"Error: {str(e)}"

def sign_in(email, password):
    try:
        # Check local storage users
        for user_id, user_data in st.session_state.users.items():
            if user_data.get('email') == email and user_data.get('password') == password:
                st.session_state.user = user_id
                st.session_state.profile = user_data
                return True, "Login successful!"
        return False, "Invalid email or password."
    
    except Exception as e:
        return False, f"Error: {str(e)}"

def sign_out():
    st.session_state.user = None
    st.session_state.profile = {}
    st.session_state.page = 'Home'
    st.rerun()

def check_auth():
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
        st.divider()
        
        pages = {
            "🏠 Home": "Home",
            "📖 Bible Reader": "Bible Reader",
            "🎶 Music Player": "Music Player",
            "🎮 Games": "Games",
            "📚 Study Hub": "Study Hub",
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
        st.write("*For I know the plans I have for you, declares the Lord, plans for welfare and not for evil, to give you a future and a hope. - Jeremiah 29:11*")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("🎵 Today's Playlist")
        st.write("• Good Good Father - Chris Tomlin")
        st.write("• You Say - Lauren Daigle")
        st.write("• Oceans - Hillsong UNITED")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("🎮 Game of the Day")
        st.write("Try our new Bible Trivia game! Test your knowledge and earn points.")
        st.markdown('</div>', unsafe_allow_html=True)

# Bible Reader page
@require_auth
def bible_reader_page():
    st.markdown('<h1 class="sub-header">📖 Bible Reader</h1>', unsafe_allow_html=True)
    
    books_of_bible = ["Genesis", "Exodus", "Matthew", "John"]
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        selected_book = st.selectbox("Select Book", books_of_bible)
        chapter = st.number_input("Chapter", min_value=1, max_value=50, value=1)
        verse = st.number_input("Verse", min_value=1, max_value=50, value=1)
        
        if st.button("Lookup Verse"):
            st.session_state.lookup_verse = True
    
    with col2:
        if st.session_state.get('lookup_verse', False):
            sample_verses = {
                "John": {3: {16: "For God so loved the world that he gave his one and only Son..."}},
                "Matthew": {5: {16: "Let your light shine before others..."}}
            }
            
            if selected_book in sample_verses and chapter in sample_verses[selected_book] and verse in sample_verses[selected_book][chapter]:
                verse_text = sample_verses[selected_book][chapter][verse]
            else:
                verse_text = "The Lord bless you and keep you..."
            
            st.markdown(f'<div class="card"><h3>{selected_book} {chapter}:{verse}</h3><p>{verse_text}</p></div>', unsafe_allow_html=True)
        else:
            st.info("Select a book, chapter, and verse to begin reading.")

# Music Player page
@require_auth
def music_player_page():
    st.markdown('<h1 class="sub-header">🎶 Music Player</h1>', unsafe_allow_html=True)
    
    for i, song in enumerate(worship_songs):
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

# Games page
@require_auth
def games_page():
    st.markdown('<h1 class="sub-header">🎮 Games</h1>', unsafe_allow_html=True)
    
    game_choice = st.radio("Choose a game:", ["Bible Trivia"])
    
    if game_choice == "Bible Trivia":
        st.subheader("Bible Trivia Challenge")
        
        questions = [
            {
                "question": "Who built the ark?",
                "options": ["Moses", "Noah", "Abraham", "David"],
                "answer": "Noah"
            }
        ]
        
        if st.session_state.get('trivia_index', 0) < len(questions):
            q = questions[st.session_state.trivia_index]
            
            st.write(f"Question {st.session_state.trivia_index + 1}: {q['question']}")
            answer = st.radio("Select your answer:", q['options'], key="trivia")
            
            if st.button("Submit Answer"):
                if answer == q['answer']:
                    st.success("Correct! 🎉")
                else:
                    st.error(f"Sorry, the correct answer is {q['answer']}")

# Study Hub page
@require_auth
def study_hub_page():
    st.markdown('<h1 class="sub-header">📚 Study Hub</h1>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["WAEC Questions", "Study Topics"])
    
    with tab1:
        st.subheader("WAEC Practice Questions")
        subject = st.selectbox("Select Subject:", list(waec_questions.keys()))
        
        if subject:
            for question in waec_questions[subject]:
                st.write(f"• {question}")
    
    with tab2:
        st.subheader("Study Topics by Subject")
        subject = st.selectbox("Select Subject:", list(study_topics.keys()))
        
        if subject:
            for topic in study_topics[subject]:
                st.markdown(f'<div class="subject-card">{topic}</div>', unsafe_allow_html=True)

# Profile page
@require_auth
def profile_page():
    st.markdown('<h1 class="sub-header">👤 Your Profile</h1>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Profile Info")
        st.write(f"**Username:** {st.session_state.profile.get('username', 'N/A')}")
        st.write(f"**Your Code:** #{st.session_state.profile.get('number', '0000')}")
        
        st.divider()
        
        st.subheader("Update Profile")
        new_username = st.text_input("New Username", value=st.session_state.profile.get('username', ''))
        
        if st.button("Update Profile"):
            st.session_state.profile['username'] = new_username
            st.success("Profile updated successfully!")

# Main app logic
def main():
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
        elif st.session_state.page == "Games":
            games_page()
        elif st.session_state.page == "Study Hub":
            study_hub_page()
        elif st.session_state.page == "Profile":
            profile_page()

if __name__ == "__main__":
    main()
