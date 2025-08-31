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
    st.warning("Supabase package not installed. Using local storage.")

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
        else:
            st.warning("Supabase credentials not found. Using local storage.")
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
if 'group_messages' not in st.session_state:
    st.session_state.group_messages = {}
if 'users' not in st.session_state:
    st.session_state.users = {}
if 'current_song' not in st.session_state:
    st.session_state.current_song = None
if 'study_groups' not in st.session_state:
    st.session_state.study_groups = {
        'math_group': {'name': 'Mathematics Club', 'members': []},
        'science_group': {'name': 'Science Squad', 'members': []},
        'english_group': {'name': 'English Masters', 'members': []}
    }

# WAEC Questions
waec_questions = {
    "Mathematics": [
        "1. Simplify: 2⅓ ÷ (2⅔ of 1⅕)",
        "2. If 2x + y = 10 and y = 4, find the value of x",
        "3. Solve the equation: 3x - 5 = 16",
        "4. Factorize completely: 6x² - 13x + 6",
        "5. Find the area of a circle with radius 7cm (Take π = 22/7)",
    ],
    "English": [
        "1. Which of these is not a part of speech?",
        "2. Change to indirect speech: 'I will come tomorrow,' she said",
        "3. Identify the figure of speech: 'The stars danced playfully in the moonlit sky'",
        "4. Correct the sentence: 'Neither of the boys are coming'",
        "5. What is the plural of 'cactus'?",
    ],
    "Biology": [
        "1. What is the basic unit of life?",
        "2. Name the process by which plants make their own food",
        "3. Which cell organelle is called the powerhouse of the cell?",
        "4. What is the function of the red blood cells?",
        "5. Name the blood vessels that carry blood away from the heart",
    ]
}

# Study Topics
study_topics = {
    "Mathematics": ["Algebra", "Geometry", "Calculus", "Statistics", "Trigonometry"],
    "Biology": ["Cell Biology", "Genetics", "Ecology", "Human Anatomy", "Photosynthesis"],
    "Physics": ["Mechanics", "Thermodynamics", "Electricity", "Waves", "Optics"]
}

worship_songs = [
    {"title": "Amazing Grace", "artist": "Chris Tomlin", "url": "https://cdn.pixabay.com/download/audio/2022/01/20/audio_5c27c9508f.mp3?filename=amazing-grace-121002.mp3"},
    {"title": "What a Beautiful Name", "artist": "Hillsong Worship", "url": "https://cdn.pixabay.com/download/audio/2021/10/25/audio_5b86d4f9c0.mp3?filename=inspirational-background-music-112834.mp3"}
]

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
                # Try to create profile in Supabase
                try:
                    supabase_client.table("profiles").insert({
                        "id": auth_response.user.id,
                        "username": username,
                        "number": number
                    }).execute()
                except Exception as e:
                    st.warning(f"Could not save to Supabase: {e}. Using local storage.")
                
                # Always save to session state
                st.session_state.profile = {
                    'username': username,
                    'number': number,
                    'id': auth_response.user.id,
                    'email': email
                }
                return True, "Sign up successful! Please check your email to verify your account."
            else:
                return False, "Error creating account."
        else:
            # Fallback to session state if Supabase is not available
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
        if supabase_client:
            # Try Supabase authentication first
            try:
                response = supabase_client.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                
                if response.user:
                    st.session_state.user = response.user
                    # Get user profile from Supabase
                    try:
                        profile = supabase_client.table("profiles").select("*").eq("id", response.user.id).execute()
                        if profile.data:
                            profile_data = profile.data[0]
                            st.session_state.profile = {
                                'username': profile_data.get('username', email.split('@')[0]),
                                'number': profile_data.get('number', '0000'),
                                'id': response.user.id,
                                'email': email
                            }
                    except:
                        # If Supabase profile doesn't exist, create a basic one
                        st.session_state.profile = {
                            'username': email.split('@')[0],
                            'number': '0000',
                            'id': response.user.id,
                            'email': email
                        }
                    return True, "Login successful!"
            except:
                # Supabase auth failed, fall back to local storage
                pass
        
        # Fallback to local storage authentication
        for user_id, user_data in st.session_state.users.items():
            if user_data.get('email') == email and user_data.get('password') == password:
                st.session_state.user = user_id
                st.session_state.profile = user_data
                return True, "Login successful!"
        
        return False, "Invalid email or password."
    
    except Exception as e:
        return False, f"Error: {str(e)}"

def sign_out():
    try:
        if supabase_client:
            supabase_client.auth.sign_out()
    except:
        pass
    
    st.session_state.user = None
    st.session_state.profile = {}
    st.session_state.page = 'Home'
    st.session_state.current_song = None
    st.rerun()

def check_auth():
    if 'user' not in st.session_state:
        # Try to get session from Supabase
        if supabase_client:
            try:
                session = supabase_client.auth.get_session()
                if session:
                    st.session_state.user = session.user
                    # Get user profile
                    try:
                        profile = supabase_client.table("profiles").select("*").eq("id", session.user.id).execute()
                        if profile.data:
                            profile_data = profile.data[0]
                            st.session_state.profile = {
                                'username': profile_data.get('username', session.user.email.split('@')[0]),
                                'number': profile_data.get('number', '0000'),
                                'id': session.user.id,
                                'email': session.user.email
                            }
                    except:
                        st.session_state.profile = {
                            'username': session.user.email.split('@')[0],
                            'number': '0000',
                            'id': session.user.id,
                            'email': session.user.email
                        }
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
        
        # Show authentication source
        if supabase_client and 'id' in st.session_state.profile:
            st.caption("🔐 Authenticated via Supabase")
        else:
            st.caption("🔐 Using local storage")
        
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
                "John": {3: {16: "For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life."}},
                "Matthew": {5: {16: "In the same way, let your light shine before others, that they may see your good deeds and glorify your Father in heaven."}}
            }
            
            if selected_book in sample_verses and chapter in sample_verses[selected_book] and verse in sample_verses[selected_book][chapter]:
                verse_text = sample_verses[selected_book][chapter][verse]
            else:
                verse_text = "The Lord bless you and keep you; the Lord make his face shine on you and be gracious to you. - Numbers 6:24-25"
            
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
    
    game_choice = st.radio("Choose a game:", ["Bible Trivia", "Word Scramble"])
    
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
    
    elif game_choice == "Word Scramble":
        st.subheader("Bible Word Scramble")
        
        words = ["FAITH", "PRAYER", "JESUS", "BIBLE", "GRACE"]
        
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
            else:
                st.error("Try again!")

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
            # Try to find receiver
            receiver = None
            
            # Check Supabase first
            if supabase_client:
                try:
                    profile_response = supabase_client.table("profiles").select("*").eq("number", receiver_number).execute()
                    if profile_response.data:
                        receiver = profile_response.data[0]
                except:
                    pass
            
            # Check local storage if not found in Supabase
            if not receiver:
                for user_id, user_data in st.session_state.users.items():
                    if user_data.get('number') == receiver_number:
                        receiver = user_data
                        break
            
            if receiver:
                st.success(f"Found user: {receiver.get('username', 'Unknown User')}")
                
                # Initialize chat if not exists
                chat_id = f"{st.session_state.profile.get('number', '0000')}_{receiver_number}"
                if chat_id not in st.session_state.messages:
                    st.session_state.messages[chat_id] = []
                
                # Display messages
                st.subheader(f"Chat with {receiver.get('username', 'Unknown User')}")
                for msg in st.session_state.messages[chat_id]:
                    if msg['sender'] == st.session_state.profile.get('number', '0000'):
                        st.markdown(f'<div class="chat-message user-message"><b>You:</b> {msg["text"]} <i>({msg["time"]})</i></div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="chat-message other-message"><b>{receiver.get("username", "Unknown")}:</b> {msg["text"]} <i>({msg["time"]})</i></div>', unsafe_allow_html=True)
                
                # Send message
                new_message = st.text_input("Type your message:", key="dm_message")
                if st.button("Send", key="dm_send"):
                    if new_message:
                        # Save to Supabase if available
                        if supabase_client and 'id' in st.session_state.profile:
                            try:
                                supabase_client.table("messages").insert({
                                    "sender_id": st.session_state.profile['id'],
                                    "receiver_number": receiver_number,
                                    "message": new_message
                                }).execute()
                            except Exception as e:
                                st.warning(f"Could not save message to Supabase: {e}")
                        
                        # Save to session state
                        st.session_state.messages[chat_id].append({
                            "sender": st.session_state.profile.get('number', '0000'),
                            "text": new_message,
                            "time": datetime.now().strftime("%H:%M")
                        })
                        st.success("Message sent!")
                        st.rerun()
            else:
                st.error("No user found with that code. Please check the code and try again.")
        elif receiver_number and (len(receiver_number) != 4 or not receiver_number.isdigit()):
            st.error("Please enter a valid 4-digit code")
    
    with tab2:
        st.subheader("Study Groups")
        
        # Display available groups
        st.markdown("### Available Study Groups")
        for group_id, group_data in st.session_state.study_groups.items():
            # Check if user is already a member
            is_member = st.session_state.profile.get('number', '0000') in group_data['members']
            
            st.markdown(f'<div class="group-card"><h3>{group_data["name"]}</h3><p>Members: {len(group_data["members"])}</p></div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if is_member:
                    if st.button(f"✅ Joined", key=f"joined_{group_id}", disabled=True):
                        pass
                else:
                    if st.button("Join Group", key=f"join_{group_id}"):
                        st.session_state.study_groups[group_id]['members'].append(st.session_state.profile.get('number', '0000'))
                        st.success(f"Joined {group_data['name']}!")
                        st.rerun()
            
            with col2:
                if is_member:
                    if st.button("Leave Group", key=f"leave_{group_id}"):
                        st.session_state.study_groups[group_id]['members'].remove(st.session_state.profile.get('number', '0000'))
                        st.success(f"Left {group_data['name']}!")
                        st.rerun()
            
            # Show group chat for members
            if is_member:
                with st.expander("Group Chat"):
                    # Initialize group messages if not exists
                    if group_id not in st.session_state.group_messages:
                        st.session_state.group_messages[group_id] = []
                    
                    # Display group messages
                    for msg in st.session_state.group_messages[group_id]:
                        sender_name = "You" if msg['sender'] == st.session_state.profile.get('number', '0000') else msg['sender_name']
                        st.markdown(f'<div class="chat-message"><b>{sender_name}:</b> {msg["text"]} <i>({msg["time"]})</i></div>', unsafe_allow_html=True)
                    
                    # Send group message
                    group_message = st.text_input("Type your message:", key=f"group_{group_id}")
                    if st.button("Send to Group", key=f"send_{group_id}"):
                        if group_message:
                            st.session_state.group_messages[group_id].append({
                                "sender": st.session_state.profile.get('number', '0000'),
                                "sender_name": st.session_state.profile.get('username', 'User'),
                                "text": group_message,
                                "time": datetime.now().strftime("%H:%M")
                            })
                            st.success("Message sent to group!")
                            st.rerun()

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
            # Update in Supabase if available
            if supabase_client and 'id' in st.session_state.profile:
                try:
                    supabase_client.table("profiles").update({
                        "username": new_username
                    }).eq("id", st.session_state.profile['id']).execute()
                except Exception as e:
                    st.warning(f"Could not update Supabase: {e}")
            
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
        elif st.session_state.page == "Chat & Groups":
            chat_page()
        elif st.session_state.page == "Profile":
            profile_page()

if __name__ == "__main__":
    main()
