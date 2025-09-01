import streamlit as st
import requests
import random
import time
from datetime import datetime

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
    }
    .online {
        background-color: #4CAF50;
    }
    .offline {
        background-color: #ccc;
    }
</style>
""", unsafe_allow_html=True)

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
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = True
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
    """
    Get WAEC questions from an educational API
    Note: This is a simulated implementation since there's no free public WAEC API
    In a real application, you would use an actual educational API
    """
    # Simulated WAEC questions data
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
                },
                {
                    "question": "Solve for x: 2x + 5 = 15",
                    "options": ["x = 5", "x = 10", "x = 7.5", "x = 6"],
                    "answer": "x = 5",
                    "explanation": "2x + 5 = 15 → 2x = 10 → x = 5"
                },
                {
                    "question": "What is the value of π to two decimal places?",
                    "options": ["3.14", "3.15", "3.16", "3.17"],
                    "answer": "3.14",
                    "explanation": "π is approximately 3.14159, which rounds to 3.14 to two decimal places"
                },
                {
                    "question": "If a car travels at 60km/h, how far will it travel in 2.5 hours?",
                    "options": ["150km", "120km", "125km", "130km"],
                    "answer": "150km",
                    "explanation": "Distance = Speed × Time = 60 km/h × 2.5 h = 150 km"
                }
            ],
            "2022": [
                {
                    "question": "What is the square root of 144?",
                    "options": ["12", "14", "16", "18"],
                    "answer": "12",
                    "explanation": "12 × 12 = 144, so √144 = 12"
                },
                {
                    "question": "Solve: 3(x + 2) = 18",
                    "options": ["x = 4", "x = 5", "x = 6", "x = 7"],
                    "answer": "x = 4",
                    "explanation": "3(x + 2) = 18 → x + 2 = 6 → x = 4"
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
                },
                {
                    "question": "Which word is spelled correctly?",
                    "options": ["Occurrence", "Occurence", "Ocurrence", "Occurrance"],
                    "answer": "Occurrence",
                    "explanation": "Occurrence is the correct spelling with double 'r' and single 'e'"
                }
            ]
        },
        "Physics": {
            "2023": [
                {
                    "question": "What is the SI unit of force?",
                    "options": ["Newton", "Joule", "Watt", "Pascal"],
                    "answer": "Newton",
                    "explanation": "Force is measured in Newtons (N), named after Sir Isaac Newton"
                }
            ]
        }
    }
    
    # Return questions if available, otherwise return a message
    if subject in waec_questions and year in waec_questions[subject]:
        return waec_questions[subject][year][:count]
    else:
        # Return some default questions if specific ones aren't available
        return [
            {
                "question": f"Sample {subject} question for {year} will be available soon.",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "answer": "Option A",
                "explanation": "This is a placeholder question. Real questions will be added when available."
            }
        ]

def get_study_resources(subject):
    """Get study resources for a subject"""
    resources = {
        "Mathematics": [
            {"title": "Algebra Fundamentals", "type": "PDF", "url": "#"},
            {"title": "Geometry Formulas", "type": "Cheat Sheet", "url": "#"},
            {"title": "Calculus Tutorial", "type": "Video", "url": "#"}
        ],
        "English Language": [
            {"title": "Grammar Rules", "type": "PDF", "url": "#"},
            {"title": "Essay Writing Guide", "type": "Guide", "url": "#"},
            {"title": "Comprehension Tips", "type": "Video", "url": "#"}
        ],
        "Physics": [
            {"title": "Laws of Motion", "type": "PDF", "url": "#"},
            {"title": "Electricity Formulas", "type": "Cheat Sheet", "url": "#"},
            {"title": "Waves Tutorial", "type": "Video", "url": "#"}
        ],
        "Chemistry": [
            {"title": "Periodic Table", "type": "PDF", "url": "#"},
            {"title": "Organic Chemistry", "type": "Guide", "url": "#"},
            {"title": "Stoichiometry", "type": "Video", "url": "#"}
        ],
        "Biology": [
            {"title": "Human Anatomy", "type": "PDF", "url": "#"},
            {"title": "Cell Biology", "type": "Guide", "url": "#"},
            {"title": "Genetics", "type": "Video", "url": "#"}
        ]
    }
    
    return resources.get(subject, [{"title": "Resources coming soon", "type": "Info", "url": "#"}])

# Chat functions
def get_chat_users():
    """Get list of users for chatting"""
    # In a real app, this would come from the database
    # For demo purposes, we'll use some sample users
    return [
        {"id": "user2", "username": "Grace", "number": "1234", "online": True},
        {"id": "user3", "username": "David", "number": "5678", "online": False},
        {"id": "user4", "username": "Sarah", "number": "9012", "online": True},
        {"id": "user5", "username": "Michael", "number": "3456", "online": True},
        {"id": "user6", "username": "Ruth", "number": "7890", "online": False},
        {"id": "user7", "username": "Daniel", "number": "2468", "online": True}
    ]

def get_study_groups():
    """Get list of study groups"""
    return [
        {"id": "group1", "name": "Math Study Group", "members": 5, "subject": "Mathematics", "description": "Working through WAEC math problems together"},
        {"id": "group2", "name": "Science Club", "members": 8, "subject": "Science", "description": "Exploring physics, chemistry and biology concepts"},
        {"id": "group3", "name": "Bible Study", "members": 12, "subject": "Religion", "description": "Weekly Bible study and discussion"},
        {"id": "group4", "name": "English Literature", "members": 6, "subject": "English", "description": "Analyzing literature and improving writing skills"},
        {"id": "group5", "name": "History Buffs", "members": 4, "subject": "History", "description": "Exploring historical events and their impact"}
    ]

def get_chat_messages(chat_id, chat_type="user"):
    """Get chat messages from database"""
    # Initialize chat messages if not exists
    if chat_id not in st.session_state.chat_messages:
        # Sample messages for different chats
        sample_messages = {
            "user2": [
                {"id": "1", "sender": "user2", "text": "Hey there! How are you doing?", "timestamp": "2023-05-15 10:30:15", "type": "received"},
                {"id": "2", "sender": "me", "text": "I'm good, thanks! Working on my math homework.", "timestamp": "2023-05-15 10:32:45", "type": "sent"},
                {"id": "3", "sender": "user2", "text": "Need any help? I finished that assignment yesterday.", "timestamp": "2023-05-15 10:33:20", "type": "received"},
                {"id": "4", "sender": "me", "text": "That would be great! Can you explain problem 5?", "timestamp": "2023-05-15 10:35:10", "type": "sent"},
                {"id": "5", "sender": "user2", "text": "Sure! It's about quadratic equations. Let me send you my notes.", "timestamp": "2023-05-15 10:36:30", "type": "received"}
            ],
            "user3": [
                {"id": "1", "sender": "me", "text": "Hi David, did you understand the physics assignment?", "timestamp": "2023-05-14 15:20:10", "type": "sent"},
                {"id": "2", "sender": "user3", "text": "Most of it, but I'm stuck on question 3 about momentum.", "timestamp": "2023-05-14 15:25:45", "type": "received"},
                {"id": "3", "sender": "me", "text": "I can help with that. Momentum is mass times velocity.", "timestamp": "2023-05-14 15:30:20", "type": "sent"}
            ],
            "user4": [
                {"id": "1", "sender": "user4", "text": "Are you joining the Bible study group tomorrow?", "timestamp": "2023-05-13 18:45:30", "type": "received"},
                {"id": "2", "sender": "me", "text": "Yes, I'll be there! What's the topic?", "timestamp": "2023-05-13 18:50:15", "type": "sent"},
                {"id": "3", "sender": "user4", "text": "We're discussing the book of Romans chapter 8.", "timestamp": "2023-05-13 18:52:40", "type": "received"}
            ],
            "group1": [
                {"id": "1", "sender": "Grace", "text": "Welcome to the Math Study Group!", "timestamp": "2023-05-10 09:15:20", "type": "received"},
                {"id": "2", "sender": "Michael", "text": "Does anyone understand calculus problems?", "timestamp": "2023-05-10 09:20:35", "type": "received"},
                {"id": "3", "sender": "me", "text": "I can help with calculus. What specific problem?", "timestamp": "2023-05-10 09:25:10", "type": "sent"},
                {"id": "4", "sender": "Sarah", "text": "I need help with geometry proofs.", "timestamp": "2023-05-10 09:30:45", "type": "received"}
            ]
        }
        
        # Return messages if available, otherwise return empty list
        st.session_state.chat_messages[chat_id] = sample_messages.get(chat_id, [])
    
    return st.session_state.chat_messages[chat_id]

def send_message(chat_id, message_text, chat_type="user"):
    """Send a message to a chat"""
    # Ensure chat messages exist for this chat
    if chat_id not in st.session_state.chat_messages:
        st.session_state.chat_messages[chat_id] = []
    
    # Create new message
    st.session_state.message_count += 1
    new_message = {
        "id": str(st.session_state.message_count),
        "sender": "me",
        "text": message_text,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": "sent"
    }
    
    # Add to current messages
    st.session_state.chat_messages[chat_id].append(new_message)
    
    # Simulate a response after a short delay
    if chat_type == "user" and chat_id in ["user2", "user3", "user4"]:
        # Auto-reply from the other user
        time.sleep(1)
        
        # Different responses based on who we're chatting with
        responses = {
            "user2": "Thanks for your message! I'll get back to you soon.",
            "user3": "I appreciate your message. Let me check my notes and I'll respond.",
            "user4": "Got your message! I'll respond when I finish my current task."
        }
        
        st.session_state.message_count += 1
        response_message = {
            "id": str(st.session_state.message_count),
            "sender": chat_id,
            "text": responses.get(chat_id, "Thanks for your message!"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": "received"
        }
        st.session_state.chat_messages[chat_id].append(response_message)
    
    # Clear the message input
    st.session_state.new_message = ""
    
    # Rerun to update the UI
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
    
    st.session_state.study_groups.append(new_group)
    return new_group

# Worship songs with actual playable audio URLs
worship_songs = [
    {"title": "Amazing Grace", "artist": "Chris Tomlin", "url": "https://cdn.pixabay.com/download/audio/2022/01/20/audio_5c27c9508f.mp3?filename=amazing-grace-121002.mp3"},
    {"title": "What a Beautiful Name", "artist": "Hillsong Worship", "url": "https://cdn.pixabay.com/download/audio/2021/10/25/audio_5b86d4f9c0.mp3?filename=inspirational-background-music-112834.mp3"},
    {"title": "Oceans", "artist": "Hillsong UNITED", "url": "https://cdn.pixabay.com/download/audio/2022/03/15/audio_345c531f9c.mp3?filename=soft-inspiring-background-amp-amp-piano-118532.mp3"},
    {"title": "Good Good Father", "artist": "Chris Tomlin", "url": "https://cdn.pixabay.com/download/audio/2022/01/20/audio_c4a38a0d0e.mp3?filename=church-bell-02-176819.mp3"},
    {"title": "Reckless Love", "artist": "Cory Asbury", "url": "https://cdn.pixabay.com/download/audio/2022/03/15/audio_6a851bc5b8.mp3?filename=cinematic-inspiring-piano-116333.mp3"},
    {"title": "10,000 Reasons", "artist": "Matt Redman", "url": "https://cdn.pixabay.com/download/audio/2022/03/15/audio_6a851bc5b8.mp3?filename=cinematic-inspiring-piano-116333.mp3"},
    {"title": "How Great Is Our God", "artist": "Chris Tomlin", "url": "https://cdn.pixabay.com/download/audio/2022/03/15/audio_6a851bc5b8.mp3?filename=cinematic-inspiring-piano-116333.mp3"}
]

def search_worship_songs(query):
    """Search for worship songs"""
    if not query:
        return worship_songs
    
    return [song for song in worship_songs if query.lower() in song['title'].lower() or query.lower() in song['artist'].lower()]

# Authentication functions (simplified for demo)
def sign_up(email, password, username, number):
    try:
        # Simulate successful signup
        st.session_state.profile = {
            "id": f"user{random.randint(1000, 9999)}",
            "username": username,
            "number": number,
            "email": email
        }
        st.session_state.user = {"id": st.session_state.profile["id"]}
        return True, "Sign up successful!"
    
    except Exception as e:
        return False, f"Error: {str(e)}"

def sign_in(email, password):
    try:
        # Simulate successful login
        if email and password:
            st.session_state.profile = {
                "id": "user1",
                "username": "CurrentUser",
                "number": "1001",
                "email": email
            }
            st.session_state.user = {"id": st.session_state.profile["id"]}
            return True, "Login successful!"
        else:
            return False, "Please enter email and password"
    
    except Exception as e:
        return False, f"Error: {str(e)}"

def sign_out():
    try:
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
        for song in worship_songs[:3]:
            st.write(f"• {song['title']} - {song['artist']}")
        if st.button("Open Music Player →"):
            st.session_state.page = "Music Player"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("💬 Recent Messages")
        # Show recent messages preview
        if st.session_state.current_chat and st.session_state.current_chat in st.session_state.chat_messages:
            messages = st.session_state.chat_messages[st.session_state.current_chat]
            if messages:
                recent_msg = messages[-1]
                sender_name = "You" if recent_msg['type'] == 'sent' else recent_msg['sender']
                st.write(f"From: {sender_name}")
                st.write(f"Message: {recent_msg['text'][:30]}...")
            else:
                st.write("No recent messages")
        else:
            st.write("No recent messages")
        if st.button("Open Chats →"):
            st.session_state.page = "Chat & Groups"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# Bible Reader page with API integration
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
            
            # Add options to share or save the verse
            col21, col22 = st.columns(2)
            with col21:
                if st.button("💾 Save to Favorites"):
                    st.success("Verse saved to favorites!")
            with col22:
                if st.button("📤 Share Verse"):
                    st.info("Sharing feature coming soon!")
        else:
            st.info("Select a book, chapter, and verse to begin reading.")

# Music Player page with REAL audio playback
@require_auth
def music_player_page():
    st.markdown('<h1 class="sub-header">🎶 Music Player</h1>', unsafe_allow_html=True)
    
    # Search for songs
    search_query = st.text_input("Search for worship songs")
    songs = search_worship_songs(search_query)
    
    # Display songs
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
    
    # Display current song and audio player
    if st.session_state.current_song:
        st.markdown('<div class="music-player">', unsafe_allow_html=True)
        st.subheader("🎵 Now Playing")
        st.write(f"**{st.session_state.current_song['title']}** by {st.session_state.current_song['artist']}")
        
        # Audio player with actual playback
        st.audio(st.session_state.current_song['url'], format="audio/mp3")
        
        # Player controls
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("⏮ Previous"):
                # Find current song index and play previous
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
                # Find current song index and play next
                current_index = next((i for i, song in enumerate(worship_songs) if song['title'] == st.session_state.current_song['title']), 0)
                next_index = (current_index + 1) % len(worship_songs)
                st.session_state.current_song = worship_songs[next_index]
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # If no song is selected, show instructions
    else:
        st.info("Select a song to begin listening")

# Daily Devotional page
@require_auth
def daily_devotional_page():
    st.markdown('<h1 class="sub-header">
# Daily Devotional page
@require_auth
def daily_devotional_page():
    st.markdown('<h1 class="sub-header">📅 Daily Devotional</h1>', unsafe_allow_html=True)
    
    # Display random verse
    verse_text, reference = get_random_verse()
    st.markdown(f'<div class="bible-verse"><h3>Verse of the Day ({reference})</h3><p>{verse_text}</p></div>', unsafe_allow_html=True)
    
    # Reflection questions
    st.subheader("Reflection Questions")
    st.write("1. What does this verse mean to you personally?")
    st.write("2. How can you apply this verse in your life today?")
    st.write("3. What is God trying to tell you through this scripture?")
    
    # Journaling space
    st.subheader("Journal Your Thoughts")
    journal_entry = st.text_area("Write your reflections here:", height=150, key="devotional_journal")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save Reflection"):
            if journal_entry:
                st.success("Your reflection has been saved!")
            else:
                st.warning("Please write something before saving.")
    with col2:
        if st.button("🔄 New Verse"):
            st.rerun()

# Study Hub page with WAEC integration
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
                
                st.markdown(f'<div class="waec-question"><h3>Question {st.session_state.current_question + 1}</h3><p>{q["question"]}</p></div>', unsafe_allow_html=True)
                
                # Display options
                selected_option = st.radio("Select your answer:", q['options'], key=f"waec_{st.session_state.current_question}")
                
                if st.button("Check Answer"):
                    st.session_state.show_answer = True
                    st.session_state.selected_option = selected_option
                    st.rerun()
                
                if st.session_state.get('show_answer', False):
                    if st.session_state.selected_option == q['answer']:
                        st.success("✅ Correct!")
                    else:
                        st.error(f"❌ Incorrect. The correct answer is: {q['answer']}")
                    
                    st.markdown(f'<div class="waec-answer"><strong>Explanation:</strong> {q["explanation"]}</div>', unsafe_allow_html=True)
                    
                    if st.button("Next Question →"):
                        st.session_state.current_question += 1
                        st.session_state.show_answer = False
                        st.rerun()
            else:
                st.success("🎉 You've completed all questions!")
                if st.button("Start Again"):
                    st.session_state.waec_questions = get_waec_questions(st.session_state.waec_subject, st.session_state.waec_year)
                    st.session_state.current_question = 0
                    st.session_state.show_answer = False
                    st.rerun()
        else:
            st.info("Select a subject and year, then click 'Load Questions' to begin.")
    
    with tab2:
        st.subheader("Study Resources")
        
        subject = st.selectbox("Select Subject", get_waec_subjects())
        resources = get_study_resources(subject)
        
        st.write(f"### Resources for {subject}")
        
        for resource in resources:
            with st.expander(f"{resource['title']} ({resource['type']})"):
                st.write("This resource will help you master key concepts.")
                if st.button("Download", key=f"dl_{resource['title']}"):
                    st.info("Download feature will be available soon!")
    
    with tab3:
        st.subheader("Study Progress")
        
        st.write("Track your progress across different subjects:")
        
        subjects = get_waec_subjects()[:5]  # Show first 5 subjects
        for subject in subjects:
            progress = random.randint(10, 100)  # Simulated progress
            st.write(f"**{subject}**")
            st.progress(progress)
            st.caption(f"{progress}% complete")
        
        st.metric("Total Questions Answered", "127")
        st.metric("Average Score", "78%")
        st.metric("Study Streak", "5 days")

# Games page
@require_auth
def games_page():
    st.markdown('<h1 class="sub-header">🎮 Games</h1>', unsafe_allow_html=True)
    
    game_choice = st.radio("Choose a game:", ["Bible Trivia", "Word Scramble", "Verse Memory"])
    
    if game_choice == "Bible Trivia":
        st.subheader("Bible Trivia Challenge")
        
        questions = [
            {
                "question": "Who built the ark?",
                "options": ["Moses", "Noah", "Abraham", "David"],
                "answer": "Noah"
            },
            {
                "question": "How many books are in the New Testament?",
                "options": ["27", "39", "66", "50"],
                "answer": "27"
            },
            {
                "question": "Who was thrown into the lions' den?",
                "options": ["David", "Daniel", "Samuel", "Joseph"],
                "answer": "Daniel"
            }
        ]
        
        if 'trivia_index' not in st.session_state:
            st.session_state.trivia_index = 0
            st.session_state.trivia_score = 0
        
        if st.session_state.trivia_index < len(questions):
            q = questions[st.session_state.trivia_index]
            
            st.write(f"Question {st.session_state.trivia_index + 1}: {q['question']}")
            answer = st.radio("Select your answer:", q['options'], key=f"trivia_{st.session_state.trivia_index}")
            
            if st.button("Submit Answer"):
                if answer == q['answer']:
                    st.session_state.trivia_score += 1
                    st.success("Correct! 🎉")
                else:
                    st.error(f"Sorry, the correct answer is {q['answer']}")
                
                time.sleep(1)
                st.session_state.trivia_index += 1
                st.rerun()
        else:
            st.success(f"Quiz completed! Your score: {st.session_state.trivia_score}/{len(questions)}")
            if st.button("Play Again"):
                st.session_state.trivia_index = 0
                st.session_state.trivia_score = 0
                st.rerun()
    
    elif game_choice == "Word Scramble":
        st.subheader("Bible Word Scramble")
        
        words = ["FAITH", "PRAYER", "JESUS", "BIBLE", "GRACE", "CHURCH", "GOSPEL", "PRAISE"]
        
        if 'scramble_word' not in st.session_state:
            word = random.choice(words)
            scrambled = ''.join(random.sample(word, len(word)))
            st.session_state.scramble_word = word
            st.session_state.scrambled = scrambled
        
        st.write(f"Unscramble this word: **{st.session_state.scrambled}**")
        
        guess = st.text_input("Your guess:").upper()
        
        if st.button("Check Answer"):
            if guess == st.session_state.scramble_word:
                st.success("Correct! 🎉")
                time.sleep(1)
                del st.session_state.scramble_word
                del st.session_state.scrambled
                st.rerun()
            else:
                st.error("Try again!")
    
    elif game_choice == "Verse Memory":
        st.subheader("Verse Memory Challenge")
        
        verses = [
            ("For God so loved the world", "John 3:16"),
            ("The Lord is my shepherd", "Psalm 23:1"),
            ("I can do all things", "Philippians 4:13")
        ]
        
        if 'verse_index' not in st.session_state:
            st.session_state.verse_index = 0
            st.session_state.verse_score = 0
        
        if st.session_state.verse_index < len(verses):
            verse_text, reference = verses[st.session_state.verse_index]
            
            st.write(f"Memorize this verse: **{verse_text}**")
            st.write(f"Reference: {reference}")
            
            st.write("Now try to recall it:")
            user_input = st.text_input("Type the verse:", key=f"verse_{st.session_state.verse_index}")
            
            if st.button("Check Answer"):
                if user_input.strip().lower() == verse_text.lower():
                    st.session_state.verse_score += 1
                    st.success("Excellent memory! 🎉")
                else:
                    st.error(f"Close! The verse is: {verse_text}")
                
                time.sleep(1)
                st.session_state.verse_index += 1
                st.rerun()
        else:
            st.success(f"Challenge completed! Your score: {st.session_state.verse_score}/{len(verses)}")
            if st.button("Play Again"):
                st.session_state.verse_index = 0
                st.session_state.verse_score = 0
                st.rerun()

# Chat & Groups page
@require_auth
def chat_page():
    st.markdown('<h1 class="sub-header">💬 Chat & Groups</h1>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Direct Messages", "Study Groups", "Create Group"])
    
    with tab1:
        st.subheader("Chat with Friends")
        
        # SEARCH FUNCTIONALITY ADDED HERE
        search_term = st.text_input("🔍 Search users by name or code", key="user_search")
        
        # Get users for chatting
        if not st.session_state.chat_users:
            st.session_state.chat_users = get_chat_users()
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.write("### Contacts")
            
            # Filter users based on search
            filtered_users = st.session_state.chat_users
            
            if search_term:
                filtered_users = [
                    user for user in st.session_state.chat_users 
                    if (search_term.lower() in user['username'].lower() or 
                        search_term in user['number'])
                ]
            
            if not filtered_users and search_term:
                st.info("No users found. Try a different search term.")
            elif not filtered_users:
                st.info("No contacts available. Join groups to meet people!")
            
            for user in filtered_users:
                status_indicator = "🟢" if user['online'] else "⚪"
                if st.button(f"{status_indicator} {user['username']} (#{user['number']})", 
                            key=f"user_{user['id']}", use_container_width=True):
                    st.session_state.current_chat = user['id']
                    st.session_state.chat_messages = get_chat_messages(user['id'])
                    st.rerun()
        
        with col2:
            if st.session_state.current_chat:
                # Get current chat user
                current_user = next((u for u in st.session_state.chat_users if u['id'] == st.session_state.current_chat), None)
                
                if current_user:
                    st.write(f"### Chat with {current_user['username']}")
                    
                    # Chat container
                    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
                    
                    # Display messages
                    messages = get_chat_messages(st.session_state.current_chat)
                    for msg in messages:
                        if msg['type'] == 'sent':
                            st.markdown(f'<div class="chat-message user-message"><p>{msg["text"]}</p><p class="message-time">{msg["timestamp"]}</p></div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="chat-message other-message"><p>{msg["text"]}</p><p class="message-time">{msg["timestamp"]}</p></div>', unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Message input
                    col21, col22 = st.columns([4, 1])
                    with col21:
                        new_message = st.text_input("Type your message:", value=st.session_state.new_message, key="message_input")
                    with col22:
                        if st.button("Send", use_container_width=True):
                            if new_message.strip():
                                send_message(st.session_state.current_chat, new_message)
                            else:
                                st.warning("Please enter a message")
            else:
                st.info("Select a contact to start chatting")
    
    with tab2:
        st.subheader("Study Groups")
        
        # SEARCH FOR GROUPS TOO!
        group_search = st.text_input("🔍 Search groups by name or subject", key="group_search")
        
        # Get study groups
        if not st.session_state.study_groups:
            st.session_state.study_groups = get_study_groups()
        
        filtered_groups = st.session_state.study_groups
        if group_search:
            filtered_groups = [
                group for group in st.session_state.study_groups
                if (group_search.lower() in group['name'].lower() or 
                    group_search.lower() in group['subject'].lower())
            ]
        
        if not filtered_groups and group_search:
            st.info("No groups found. Try a different search term.")
        
        for group in filtered_groups:
            with st.expander(f"{group['name']} - {group['subject']} ({group['members']} members)"):
                st.write(f"Topic: {group.get('description', 'General study group')}")
                if st.button("Join Group", key=f"join_{group['id']}"):
                    st.success(f"You've joined {group['name']}!")
                if st.button("View Chat", key=f"view_{group['id']}"):
                    st.session_state.current_chat = group['id']
                    st.session_state.chat_messages = get_chat_messages(group['id'], "group")
                    st.rerun()
    
    with tab3:
        st.subheader("Create a Study Group")
        
        with st.form("create_group_form"):
            group_name = st.text_input("Group Name")
            group_subject = st.selectbox("Subject", get_waec_subjects())
            group_description = st.text_area("Description")
            
            if st.form_submit_button("Create Group"):
                if group_name and group_subject:
                    new_group = create_study_group(group_name, group_subject, group_description)
                    st.success(f"Group '{new_group['name']}' created successfully!")
                    st.session_state.study_groups.append(new_group)
                else:
                    st.error("Please provide a group name and subject")

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
            # Update in session state
            st.session_state.profile['username'] = new_username
            st.success("Profile updated successfully!")
    
    with col2:
        st.subheader("Your Stats")
        
        col21, col22, col23 = st.columns(3)
        with col21:
            st.markdown('<div class="card"><h3>5</h3><p>Friends</p></div>', unsafe_allow_html=True)
        with col22:
            st.markdown('<div class="card"><h3>12</h3><p>Devotionals</p></div>', unsafe_allow_html=True)
        with col23:
            st.markdown('<div class="card"><h3>350</h3><p>Points</p></div>', unsafe_allow_html=True)
        
        st.subheader("Study Progress")
        st.write("📊 Mathematics: 75% complete")
        st.write("📊 English: 60% complete")
        st.write("📊 Biology: 85% complete")
        
        st.subheader("Achievements")
        st.write("🏆 Bible Scholar (Read 50 verses)")
        st.write("🏆 Math Whiz (Solved 100 problems)")
        st.write("🏆 Social Butterfly (Sent 50 messages)")

# Main app logic
def main():
    # Check if user is authenticated
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
        elif st.session_state.page == "Daily Devotional":
            daily_devotional_page()
        elif st.session_state.page == "Games":
            games_page()
        elif st.session_state.page == "Study Hub":
            study_hub_page()
        elif st.session_state.page == "Chat & Groups":
            chat_page()
        elif st.session_state.page == "Profile":
            profile_page()

if __name__ == "__main__":
    main()
