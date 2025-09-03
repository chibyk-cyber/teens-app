import streamlit as st
import requests
import random
import time
from datetime import datetime

# Try to import supabase with error handling
try:
    from supabase import create_client, Client
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
        margin-left: 20%;
    }
    .other-message {
        background-color: #F1F0F0;
        margin-right: 20%;
    }
    .message-time {
        font-size: 0.7rem;
        color: #777;
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
    .bible-verse {
        font-style: italic;
        background-color: #e8f5e9;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .waec-question {
        background-color: #e3f2fd;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .waec-answer {
        background-color: #bbdefb;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    .chat-container {
        height: 400px;
        overflow-y: auto;
        padding: 10px;
        border: 1px solid #ddd;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .online-status {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 5px;
        background-color: #4CAF50;
    }
    .offline-status {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 5px;
        background-color: #ccc;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Supabase client
supabase_client = None
if SUPABASE_AVAILABLE:
    try:
        # Get credentials from Streamlit secrets
        SUPABASE_URL = st.secrets.get("supabase", {}).get("url", "")
        SUPABASE_KEY = st.secrets.get("supabase", {}).get("key", "")
        
        if SUPABASE_URL and SUPABASE_KEY:
            supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
            st.success("✅ Connected to Supabase successfully!")
        else:
            st.warning("⚠️ Supabase credentials not found. Using demo mode.")
    except Exception as e:
        st.error(f"❌ Could not connect to Supabase: {str(e)}")

# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'profile' not in st.session_state:
    st.session_state.profile = {}
if 'page' not in st.session_state:
    st.session_state.page = 'Home'
if 'current_song' not in st.session_state:
    st.session_state.current_song = None
if 'audio_playing' not in st.session_state:
    st.session_state.audio_playing = False
if 'lookup_verse' not in st.session_state:
    st.session_state.lookup_verse = False
if 'waec_subject' not in st.session_state:
    st.session_state.waec_subject = "Mathematics"
if 'waec_year' not in st.session_state:
    st.session_state.waec_year = "2023"
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = {}
if 'current_chat' not in st.session_state:
    st.session_state.current_chat = None
if 'chat_users' not in st.session_state:
    st.session_state.chat_users = []
if 'study_groups' not in st.session_state:
    st.session_state.study_groups = []
if 'new_message' not in st.session_state:
    st.session_state.new_message = ""
if 'user_search' not in st.session_state:
    st.session_state.user_search = ""
if 'group_search' not in st.session_state:
    st.session_state.group_search = ""
if 'message_count' not in st.session_state:
    st.session_state.message_count = 0

# Bible API functions
def get_bible_books():
    """Get list of Bible books from API"""
    try:
        response = requests.get("https://bible-api.com/books")
        if response.status_code == 200:
            data = response.json()
            return [book['name'] for book in data]
        return ["Genesis", "Exodus", "Matthew", "John", "Romans", "Psalms"]
    except:
        return ["Genesis", "Exodus", "Matthew", "John", "Romans", "Psalms"]

def get_bible_verse(book, chapter, verse):
    """Get specific Bible verse from API"""
    try:
        # Format book name for API (remove spaces)
        book_formatted = book.replace(" ", "")
        url = f"https://bible-api.com/{book_formatted}+{chapter}:{verse}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            return data['text'], data['reference']
        return "For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life.", "John 3:16"
    except:
        return "The Lord bless you and keep you; the Lord make his face shine on you and be gracious to you.", "Numbers 6:24-25"

def get_random_verse():
    """Get a random inspirational verse"""
    verses = [
        ("For I know the plans I have for you, declares the Lord, plans to prosper you and not to harm you, plans to give you hope and a future.", "Jeremiah 29:11"),
        ("I can do all this through him who gives me strength.", "Philippians 4:13"),
        ("Trust in the Lord with all your heart and lean not on your own understanding.", "Proverbs 3:5"),
        ("The Lord is my shepherd, I lack nothing.", "Psalm 23:1"),
        ("Do not be anxious about anything, but in every situation, by prayer and petition, with thanksgiving, present your requests to God.", "Philippians 4:6")
    ]
    return random.choice(verses)

# WAEC API functions
def get_waec_subjects():
    """Get list of available WAEC subjects"""
    return [
        "Mathematics", "English Language", "Physics", "Chemistry", "Biology",
        "Economics", "Geography", "Government", "Literature in English",
        "Financial Accounting", "Commerce", "Agricultural Science",
        "Further Mathematics", "Christian Religious Studies", "History"
    ]

def get_waec_years():
    """Get list of available WAEC years"""
    return ["2023", "2022", "2021", "2020", "2019", "2018", "2017", "2016"]

def get_waec_questions(subject, year, count=5):
    """Get WAEC questions (simulated)"""
    waec_questions = {
        "Mathematics": {
            "2023": [
                {
                    "question": "Simplify: (3x² - 2x + 5) + (2x² + 4x - 3)",
                    "options": ["5x² + 2x + 2", "5x² + 2x - 2", "5x² - 2x + 2", "x² + 6x + 8"],
                    "answer": "5x² + 2x + 2",
                    "explanation": "Combine like terms: 3x² + 2x² = 5x², -2x + 4x = 2x, 5 - 3 = 2"
                },
                {
                    "question": "If a right-angled triangle has sides 3cm, 4cm and 5cm, what is the area?",
                    "options": ["6cm²", "12cm²", "10cm²", "15cm²"],
                    "answer": "6cm²",
                    "explanation": "Area of triangle = 1/2 × base × height = 1/2 × 3 × 4 = 6cm²"
                }
            ]
        },
        "English Language": {
            "2023": [
                {
                    "question": "Choose the correct option: Neither the teacher nor the students _____ present.",
                    "options": ["was", "were", "has", "have"],
                    "answer": "were",
                    "explanation": "When using 'neither/nor', the verb agrees with the subject closest to it (students - plural)"
                }
            ]
        }
    }
    
    if subject in waec_questions and year in waec_questions[subject]:
        return waec_questions[subject][year][:count]
    else:
        return [
            {
                "question": f"Sample {subject} question for {year}",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "answer": "Option A",
                "explanation": "This is a placeholder question."
            }
        ]

def get_study_resources(subject):
    """Get study resources for a subject"""
    resources = {
        "Mathematics": [
            {"title": "Algebra Fundamentals", "type": "PDF", "url": "#"},
            {"title": "Geometry Formulas", "type": "Cheat Sheet", "url": "#"}
        ],
        "English Language": [
            {"title": "Grammar Rules", "type": "PDF", "url": "#"},
            {"title": "Essay Writing Guide", "type": "Guide", "url": "#"}
        ]
    }
    return resources.get(subject, [{"title": "Resources coming soon", "type": "Info", "url": "#"}])

# Chat functions with Supabase integration
def get_chat_users():
    """Get list of users for chatting"""
    try:
        if supabase_client:
            # Try to get users from Supabase
            response = supabase_client.table("profiles").select("*").neq("id", st.session_state.user.id).execute()
            if response.data:
                return [
                    {
                        "id": user["id"],
                        "username": user.get("username", "Unknown"),
                        "number": user.get("number", "0000"),
                        "online": random.choice([True, False])
                    }
                    for user in response.data
                ]
    except:
        pass
    
    # Fallback to demo users
    return [
        {"id": "user2", "username": "Grace", "number": "1234", "online": True},
        {"id": "user3", "username": "David", "number": "5678", "online": False},
        {"id": "user4", "username": "Sarah", "number": "9012", "online": True}
    ]

def get_study_groups():
    """Get list of study groups"""
    try:
        if supabase_client:
            # Try to get groups from Supabase
            response = supabase_client.table("study_groups").select("*").execute()
            if response.data:
                return response.data
    except:
        pass
    
    # Fallback to demo groups
    return [
        {"id": "group1", "name": "Math Study Group", "members": 5, "subject": "Mathematics", "description": "Math help"},
        {"id": "group2", "name": "Science Club", "members": 8, "subject": "Science", "description": "Science discussions"}
    ]

def get_chat_messages(chat_id):
    """Get chat messages for a specific chat"""
    # Initialize chat_messages as dictionary if not already
    if not isinstance(st.session_state.chat_messages, dict):
        st.session_state.chat_messages = {}
    
    if chat_id not in st.session_state.chat_messages:
        try:
            if supabase_client:
                # Try to get messages from Supabase
                response = supabase_client.table("messages").select("*").eq("chat_id", chat_id).order("created_at").execute()
                if response.data:
                    messages = []
                    for msg in response.data:
                        messages.append({
                            "id": msg["id"],
                            "sender": msg["sender_id"],
                            "text": msg["content"],
                            "timestamp": msg["created_at"],
                            "type": "received" if msg["sender_id"] != st.session_state.user.id else "sent"
                        })
                    st.session_state.chat_messages[chat_id] = messages
                    return messages
        except:
            pass
        
        # Fallback to demo messages
        sample_messages = {
            "user2": [
                {"id": "1", "sender": "user2", "text": "Hey there! How are you?", "timestamp": "2023-05-15 10:30:15", "type": "received"},
                {"id": "2", "sender": "me", "text": "I'm good, thanks!", "timestamp": "2023-05-15 10:32:45", "type": "sent"}
            ],
            "user3": [
                {"id": "1", "sender": "me", "text": "Hi David!", "timestamp": "2023-05-14 15:20:10", "type": "sent"}
            ],
            "user4": [
                {"id": "1", "sender": "user4", "text": "Hello! How can I help you?", "timestamp": "2023-05-13 18:45:30", "type": "received"}
            ],
            "group1": [
                {"id": "1", "sender": "Grace", "text": "Welcome to the Math Study Group!", "timestamp": "2023-05-10 09:15:20", "type": "received"},
                {"id": "2", "sender": "me", "text": "Thanks! I'm excited to join.", "timestamp": "2023-05-10 09:20:35", "type": "sent"}
            ]
        }
        
        # Make sure we're working with a dictionary
        if not isinstance(st.session_state.chat_messages, dict):
            st.session_state.chat_messages = {}
        
        st.session_state.chat_messages[chat_id] = sample_messages.get(chat_id, [])
    
    return st.session_state.chat_messages[chat_id]

def send_message(chat_id, message_text):
    """Send a message to a chat"""
    if chat_id not in st.session_state.chat_messages:
        st.session_state.chat_messages[chat_id] = []
    
    # Create message object
    st.session_state.message_count += 1
    new_message = {
        "id": str(st.session_state.message_count),
        "sender": "me",
        "text": message_text,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": "sent"
    }
    
    # Add to session state
    st.session_state.chat_messages[chat_id].append(new_message)
    
    # Save to Supabase if available
    try:
        if supabase_client:
            supabase_client.table("messages").insert({
                "chat_id": chat_id,
                "sender_id": st.session_state.user.id,
                "content": message_text,
                "created_at": datetime.now().isoformat()
            }).execute()
    except:
        pass
    
    # Simulate response
    if chat_id in ["user2", "user3", "user4"]:
        time.sleep(1)
        st.session_state.message_count += 1
        response_message = {
            "id": str(st.session_state.message_count),
            "sender": chat_id,
            "text": "Thanks for your message!",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": "received"
        }
        st.session_state.chat_messages[chat_id].append(response_message)
    
    st.session_state.new_message = ""
    st.rerun()

def create_study_group(name, subject, description):
    """Create a new study group"""
    new_group = {
        "id": f"group{len(st.session_state.study_groups) + 1}",
        "name": name,
        "subject": subject,
        "description": description,
        "members": 1,
        "created_by": st.session_state.profile.get('username', 'User')
    }
    
    # Save to Supabase if available
    try:
        if supabase_client:
            supabase_client.table("study_groups").insert({
                "name": name,
                "subject": subject,
                "description": description,
                "members": 1,
                "created_by": st.session_state.user.id
            }).execute()
    except:
        pass
    
    st.session_state.study_groups.append(new_group)
    return new_group

# Worship songs
worship_songs = [
    {"title": "Amazing Grace", "artist": "Chris Tomlin", "url": "https://cdn.pixabay.com/download/audio/2022/01/20/audio_5c27c9508f.mp3?filename=amazing-grace-121002.mp3"},
    {"title": "What a Beautiful Name", "artist": "Hillsong Worship", "url": "https://cdn.pixabay.com/download/audio/2021/10/25/audio_5b86d4f9c0.mp3?filename=inspirational-background-music-112834.mp3"},
    {"title": "Oceans", "artist": "Hillsong UNITED", "url": "https://cdn.pixabay.com/download/audio/2022/03/15/audio_345c531f9c.mp3?filename=soft-inspiring-background-amp-amp-piano-118532.mp3"}
]

def search_worship_songs(query):
    """Search for worship songs"""
    if not query:
        return worship_songs
    return [song for song in worship_songs if query.lower() in song['title'].lower() or query.lower() in song['artist'].lower()]

# Authentication functions with Supabase integration
def sign_up(email, password, username, number):
    try:
        if supabase_client:
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
                    "number": number,
                    "email": email
                }).execute()
                
                if profile_response.data:
                    st.session_state.profile = profile_response.data[0]
                    st.session_state.user = auth_response.user
                    return True, "Sign up successful! Please check your email to verify your account."
                else:
                    return False, "Error creating profile."
            else:
                return False, "Error creating account."
        else:
            # Demo mode
            st.session_state.profile = {
                "id": f"user{random.randint(1000, 9999)}",
                "username": username,
                "number": number,
                "email": email
            }
            st.session_state.user = {"id": st.session_state.profile["id"]}
            return True, "Sign up successful! (Demo mode)"
    
    except Exception as e:
        return False, f"Error: {str(e)}"

def sign_in(email, password):
    try:
        if supabase_client:
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
        else:
            # Demo mode
            if email and password:
                st.session_state.profile = {
                    "id": "user1",
                    "username": "CurrentUser",
                    "number": "1001",
                    "email": email
                }
                st.session_state.user = {"id": st.session_state.profile["id"]}
                return True, "Login successful! (Demo mode)"
            else:
                return False, "Please enter email and password"
    
    except Exception as e:
        return False, f"Error: {str(e)}"

def sign_out():
    try:
        if supabase_client:
            supabase_client.auth.sign_out()
        st.session_state.user = None
        st.session_state.profile = {}
        st.session_state.page = 'Home'
        st.session_state.current_song = None
        st.session_state.audio_playing = False
        st.session_state.lookup_verse = False
        st.session_state.waec_subject = "Mathematics"
        st.session_state.waec_year = "2023"
        st.session_state.chat_messages = {}
        st.session_state.current_chat = None
        st.session_state.new_message = ""
        st.session_state.message_count = 0
        st.rerun()
    except Exception as e:
        st.error(f"Error signing out: {str(e)}")

def check_auth():
    if st.session_state.user is not None:
        return True
    
    # Try to get session from Supabase
    if supabase_client:
        try:
            session = supabase_client.auth.get_session()
            if session and session.user:
                st.session_state.user = session.user
                # Get user profile
                profile = supabase_client.table("profiles").select("*").eq("id", session.user.id).execute()
                if profile.data:
                    st.session_state.profile = profile.data[0]
                    return True
        except:
            pass
    
    return False

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
    
    if not SUPABASE_AVAILABLE:
        st.warning("⚠️ Supabase not available. Running in demo mode.")
    
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
        
        if supabase_client:
            st.caption("🔐 Authenticated via Supabase")
        else:
            st.caption("🔐 Demo Mode")
        
        st.divider()
        
        pages = {
            "🏠 Home": "Home",
            "📖 Bible Reader": "Bible Reader",
            "🎶 Music Player": "Music Player",
            "📅 Daily Devotional": "Daily Devotional",
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
        verse_text, reference = get_random_verse()
        st.markdown(f'<div class="bible-verse"><p>{verse_text}</p><p>- {reference}</p></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("🎵 Today's Playlist")
        for song in worship_songs[:2]:
            st.write(f"• {song['title']} - {song['artist']}")
        if st.button("Open Music Player →"):
            st.session_state.page = "Music Player"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("💬 Recent Messages")
        if st.session_state.current_chat and st.session_state.current_chat in st.session_state.chat_messages:
            messages = st.session_state.chat_messages[st.session_state.current_chat]
            if messages:
                recent_msg = messages[-1]
                sender_name = "You" if recent_msg['type'] == 'sent' else recent_msg['sender']
                st.write(f"From: {sender_name}")
                st.write(f"Message: {recent_msg['text'][:30]}...")
        else:
            st.write("No recent messages")
        if st.button("Open Chats →"):
            st.session_state.page = "Chat & Groups"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# Bible Reader page
@require_auth
def bible_reader_page():
    st.markdown('<h1 class="sub-header">📖 Bible Reader</h1>', unsafe_allow_html=True)
    
    bible_books = get_bible_books()
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        selected_book = st.selectbox("Select Book", bible_books)
        chapter = st.number_input("Chapter", min_value=1, max_value=150, value=1)
        verse = st.number_input("Verse", min_value=1, max_value=176, value=1)
        
        if st.button("Lookup Verse"):
            st.session_state.lookup_verse = True
    
    with col2:
        if st.session_state.get('lookup_verse', False):
            verse_text, reference = get_bible_verse(selected_book, chapter, verse)
            st.markdown(f'<div class="bible-verse"><h3>{reference}</h3><p>{verse_text}</p></div>', unsafe_allow_html=True)
            
            col21, col22 = st.columns(2)
            with col21:
                if st.button("💾 Save to Favorites"):
                    # Save to Supabase if available
                    try:
                        if supabase_client:
                            supabase_client.table("saved_verses").insert({
                                "user_id": st.session_state.user.id,
                                "book": selected_book,
                                "chapter": chapter,
                                "verse": verse,
                                "verse_text": verse_text,
                                "reference": reference
                            }).execute()
                            st.success("Verse saved to favorites!")
                        else:
                            st.success("Verse saved to favorites! (Demo mode)")
                    except Exception as e:
                        st.error(f"Error saving verse: {str(e)}")
            with col22:
                if st.button("📤 Share Verse"):
                    st.info("Sharing feature coming soon!")
        else:
            st.info("Select a book, chapter, and verse to begin reading.")

# Music Player page
@require_auth
def music_player_page():
    st.markdown('<h1 class="sub-header">🎶 Music Player</h1>', unsafe_allow_html=True)
    
    search_query = st.text_input("Search for worship songs")
    songs = search_worship_songs(search_query)
    
    for i, song in enumerate(songs):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**{song['title']}**")
            st.write(f"*{song['artist']}*")
        with col2:
            if st.button("▶️ Play", key=f"play_{i}"):
                st.session_state.current_song = song
                st.session_state.audio_playing = True
                st.success(f"Playing: {song['title']}")
    
    if st.session_state.current_song:
        st.markdown('<div class="music-player">', unsafe_allow_html=True)
        st.subheader("🎵 Now Playing")
        st.write(f"**{st.session_state.current_song['title']}** by {st.session_state.current_song['artist']}")
        
        st.audio(st.session_state.current_song['url'], format="audio/mp3")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("⏮ Previous"):
                current_index = next((i for i, song in enumerate(worship_songs) if song['title'] == st.session_state.current_song['title']), 0)
                prev_index = (current_index - 1) % len(worship_songs)
                st.session_state.current_song = worship_songs[prev_index]
                st.rerun()
        with col2:
            if st.button("⏸ Pause" if st.session_state.audio_playing else "▶️ Play"):
                st.session_state.audio_playing = not st.session_state.audio_playing
                st.rerun()
        with col3:
            if st.button("⏭ Next"):
                current_index = next((i for i, song in enumerate(worship_songs) if song['title'] == st.session_state.current_song['title']), 0)
                next_index = (current_index + 1) % len(worship_songs)
                st.session_state.current_song = worship_songs[next_index]
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Select a song to begin listening")

# Daily Devotional page
@require_auth
def daily_devotional_page():
    st.markdown('<h1 class="sub-header">📅 Daily Devotional</h1>', unsafe_allow_html=True)
    
    verse_text, reference = get_random_verse()
    st.markdown(f'<div class="bible-verse"><h3>Verse of the Day ({reference})</h3><p>{verse_text}</p></div>', unsafe_allow_html=True)
    
    st.subheader("Reflection Questions")
    st.write("1. What does this verse mean to you personally?")
    st.write("2. How can you apply this verse in your life today?")
    st.write("3. What is God trying to tell you through this scripture?")
    
    st.subheader("Journal Your Thoughts")
    journal_entry = st.text_area("Write your reflections here:", height=150, key="devotional_journal")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save Reflection"):
            if journal_entry:
                # Save to Supabase if available
                try:
                    if supabase_client:
                        supabase_client.table("devotionals").insert({
                            "user_id": st.session_state.user.id,
                            "verse_text": verse_text,
                            "reference": reference,
                            "reflection": journal_entry,
                            "date": datetime.now().isoformat()
                        }).execute()
                        st.success("Your reflection has been saved!")
                    else:
                        st.success("Your reflection has been saved! (Demo mode)")
                except Exception as e:
                    st.error(f"Error saving reflection: {str(e)}")
            else:
                st.warning("Please write something before saving.")
    with col2:
        if st.button("🔄 New Verse"):
            st.rerun()

# Study Hub page
@require_auth
def study_hub_page():
    st.markdown('<h1 class="sub-header">📚 Study Hub</h1>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["WAEC Questions", "Study Resources", "Progress Tracking"])
    
    with tab1:
        st.subheader("WAEC Past Questions")
        
        col1, col2 = st.columns(2)
        with col1:
            subjects = get_waec_subjects()
            st.session_state.waec_subject = st.selectbox("Select Subject", subjects, index=subjects.index(st.session_state.waec_subject))
        
        with col2:
            years = get_waec_years()
            st.session_state.waec_year = st.selectbox("Select Year", years, index=years.index(st.session_state.waec_year))
        
        if st.button("Load Questions"):
            st.session_state.waec_questions = get_waec_questions(st.session_state.waec_subject, st.session_state.waec_year)
            st.session_state.current_question = 0
            st.session_state.show_answer = False
            st.rerun()
        
        if 'waec_questions' in st.session_state and st.session_state.waec_questions:
            if st.session_state.current_question < len(st.session_state.waec_questions):
                q = st.session_state.waec_questions[st.session_state.current_question]
                
                st.markdown(f'<div class="waec-question"><h3>Question {st.session_state.current_question + 1}</h3><p>{q["question"]</p></div>', unsafe_allow_html=True)
                
                selected_option = st.radio("Select your answer:", q['options'], key
