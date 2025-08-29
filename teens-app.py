# app.py
import streamlit as st
import supabase
import os
from datetime import datetime, timezone
import random
import time
import requests
from dotenv import load_dotenv
from streamlit_option_menu import option_menu

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("https://vkvwxnnirqtkwfhuskvo.supabase.co")
SUPABASE_KEY = os.getenv("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZrdnd4bm5pcnF0a3dmaHVza3ZvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTYzMDAzMTcsImV4cCI6MjA3MTg3NjMxN30.-yAV2mYDcesXM5wncmbcq1GlpD60q32lx6pe1bPDKfg")

# Initialize Supabase client
@st.cache_resource
def init_supabase():
    return supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

supabase_client = init_supabase()

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
    .success-message {
        color: #4CAF50;
        padding: 10px;
    }
    .error-message {
        color: #F44336;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Authentication functions
def sign_up(email, password, username, number):
    try:
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
            
            return True, "Sign up successful! Please check your email to verify your account."
        else:
            return False, "Error creating account."
    
    except Exception as e:
        return False, f"Error: {str(e)}"

def sign_in(email, password):
    try:
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
            return False, "Login failed. Please check your credentials."
    
    except Exception as e:
        return False, f"Error: {str(e)}"

def sign_out():
    try:
        supabase_client.auth.sign_out()
        st.session_state.clear()
        st.experimental_rerun()
    except Exception as e:
        st.error(f"Error signing out: {str(e)}")

def check_auth():
    if 'user' not in st.session_state:
        # Try to get the current session
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
    
    return 'user' in st.session_state

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'Home'
if 'messages' not in st.session_state:
    st.session_state.messages = {}

# Authentication wrapper
def require_auth(func):
    def wrapper(*args, **kwargs):
        if not check_auth():
            st.warning("Please sign in to access this page.")
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
                    st.experimental_rerun()
                else:
                    st.error(message)
    
    with tab2:
        with st.form("signup_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            username = st.text_input("Username")
            number = st.text_input("4+ Digit Code", max_chars=6)
            
            # Validate number
            if number and (not number.isdigit() or len(number) < 4):
                st.error("Please enter a valid 4+ digit code")
            
            signup_btn = st.form_submit_button("Create Account")
            
            if signup_btn:
                if not number.isdigit() or len(number) < 4:
                    st.error("Please enter a valid 4+ digit code")
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
        st.title(f"👋 Hi, {st.session_state.profile['username']}!")
        st.write(f"Your code: #{st.session_state.profile['number']}")
        st.divider()
        
        # Navigation options
        selected = option_menu(
            menu_title="Navigate",
            options=["🏠 Home", "📖 Bible Reader", "🎶 Music Player", "🎮 Games", "💬 Chat & Groups", "👤 Profile"],
            icons=["house", "book", "music-note", "controller", "chat", "person"],
            default_index=0,
        )
        
        st.session_state.page = selected
        
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
    
    st.divider()
    
    st.subheader("Recent Activity")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Community Updates**")
        st.write("• New Bible study group forming on Fridays")
        st.write("• Worship night this Saturday at 6 PM")
        st.write("• Summer retreat registration is now open!")
    
    with col2:
        st.markdown("**Your Progress**")
        st.write("• 5 days streak of daily devotionals")
        st.write("• 3 friends added this week")
        st.write("• 100 points earned in games")

# Bible Reader page
@require_auth
def bible_reader_page():
    st.markdown('<h1 class="sub-header">📖 Bible Reader</h1>', unsafe_allow_html=True)
    
    # Sample Bible data (in a real app, you'd use an API)
    books_of_bible = [
        "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
        "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel",
        "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles", "Ezra",
        "Nehemiah", "Esther", "Job", "Psalms", "Proverbs",
        "Ecclesiastes", "Song of Solomon", "Isaiah", "Jeremiah", "Lamentations",
        "Ezekiel", "Daniel", "Hosea", "Joel", "Amos",
        "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk",
        "Zephaniah", "Haggai", "Zechariah", "Malachi",
        "Matthew", "Mark", "Luke", "John", "Acts",
        "Romans", "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
        "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians", "1 Timothy",
        "2 Timothy", "Titus", "Philemon", "Hebrews", "James",
        "1 Peter", "2 Peter", "1 John", "2 John", "3 John",
        "Jude", "Revelation"
    ]
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        selected_book = st.selectbox("Select Book", books_of_bible)
        chapter = st.number_input("Chapter", min_value=1, max_value=150, value=1)
        verse = st.number_input("Verse", min_value=1, max_value=176, value=1)
        
        if st.button("Lookup Verse"):
            st.session_state.lookup_verse = True
    
    with col2:
        if 'lookup_verse' in st.session_state and st.session_state.lookup_verse:
            # In a real app, you would fetch from an API
            st.success(f"Displaying {selected_book} {chapter}:{verse}")
            
            # Sample verse content
            sample_verses = {
                "John": {
                    3: {
                        16: "For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life."
                    }
                },
                "Jeremiah": {
                    29: {
                        11: "For I know the plans I have for you, declares the Lord, plans to prosper you and not to harm you, plans to give you hope and a future."
                    }
                },
                "Philippians": {
                    4: {
                        6: "Do not be anxious about anything, but in every situation, by prayer and petition, with thanksgiving, present your requests to God."
                    }
                }
            }
            
            if selected_book in sample_verses and chapter in sample_verses[selected_book] and verse in sample_verses[selected_book][chapter]:
                verse_text = sample_verses[selected_book][chapter][verse]
            else:
                verse_text = "The Lord bless you and keep you; the Lord make his face shine on you and be gracious to you. - Sample Verse"
            
            st.markdown(f'<div class="card"><h3>{selected_book} {chapter}:{verse}</h3><p>{verse_text}</p></div>', unsafe_allow_html=True)
            
            # Add to favorites
            if st.button("❤️ Add to Favorites"):
                st.success("Verse added to favorites!")
        else:
            st.info("Select a book, chapter, and verse to begin reading.")

# Music Player page
@require_auth
def music_player_page():
    st.markdown('<h1 class="sub-header">🎶 Music Player</h1>', unsafe_allow_html=True)
    
    # Sample worship songs
    worship_songs = [
        {"title": "Good Good Father", "artist": "Chris Tomlin", "url": "https://example.com/goodgoodfather.mp3"},
        {"title": "What a Beautiful Name", "artist": "Hillsong Worship", "url": "https://example.com/beautifulname.mp3"},
        {"title": "No Longer Slaves", "artist": "Bethel Music", "url": "https://example.com/nolongerslaves.mp3"},
        {"title": "Reckless Love", "artist": "Cory Asbury", "url": "https://example.com/recklesslove.mp3"},
        {"title": "Way Maker", "artist": "Sinach", "url": "https://example.com/waymaker.mp3"},
    ]
    
    # Display songs
    for i, song in enumerate(worship_songs):
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            st.write(f"**{song['title']}**")
            st.write(f"*{song['artist']}*")
        with col2:
            st.progress(0)  # Placeholder for progress bar
        with col3:
            if st.button("▶️ Play", key=f"play_{i}"):
                st.session_state.current_song = song
                st.success(f"Playing: {song['title']}")
    
    # Current song display
    if 'current_song' in st.session_state:
        st.divider()
        st.subheader("Now Playing")
        st.write(f"**{st.session_state.current_song['title']}** by {st.session_state.current_song['artist']}")
        
        # Simulated player controls
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("⏮ Previous"):
                st.info("Previous song selected")
        with col2:
            if st.button("⏸ Pause"):
                st.info("Playback paused")
        with col3:
            if st.button("⏭ Next"):
                st.info("Next song selected")
        
        # Volume control
        volume = st.slider("Volume", 0, 100, 80)

# Games page
@require_auth
def games_page():
    st.markdown('<h1 class="sub-header">🎮 Games</h1>', unsafe_allow_html=True)
    
    game_choice = st.radio("Choose a game:", 
                          ["Bible Trivia", "Word Scramble", "Verse Memory"])
    
    if game_choice == "Bible Trivia":
        st.subheader("Bible Trivia Challenge")
        
        # Sample questions
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
                "options": ["Daniel", "David", "Samuel", "Joseph"],
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
                st.experimental_rerun()
        else:
            st.success(f"Quiz completed! Your score: {st.session_state.trivia_score}/{len(questions)}")
            if st.button("Play Again"):
                st.session_state.trivia_index = 0
                st.session_state.trivia_score = 0
                st.experimental_rerun()
    
    elif game_choice == "Word Scramble":
        st.subheader("Bible Word Scramble")
        
        words = ["FAITH", "PRAYER", "JESUS", "BIBLE", "CHURCH", "GRACE"]
        
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
                st.experimental_rerun()
            else:
                st.error("Try again!")
    
    elif game_choice == "Verse Memory":
        st.subheader("Verse Memory Challenge")
        
        verses = [
            "For God so loved the world that he gave his one and only Son - John 3:16",
            "I can do all this through him who gives me strength - Philippians 4:13",
            "Trust in the LORD with all your heart - Proverbs 3:5"
        ]
        
        if 'memory_verse' not in st.session_state:
            st.session_state.memory_verse = random.choice(verses)
            st.session_state.show_verse = True
        
        if st.session_state.show_verse:
            st.info("Memorize this verse in 10 seconds!")
            st.write(f"**{st.session_state.memory_verse}**")
            
            if st.button("I'm ready to test my memory"):
                st.session_state.show_verse = False
                st.session_state.start_time = time.time()
                st.experimental_rerun()
        else:
            st.write("Type the verse from memory:")
            user_input = st.text_area("Your recall:")
            
            if st.button("Check my memory"):
                accuracy = sum(1 for a, b in zip(user_input, st.session_state.memory_verse) if a == b) / len(st.session_state.memory_verse)
                st.success(f"Your accuracy: {accuracy:.0%}")
                
                if accuracy > 0.7:
                    st.balloons()
                
                time.sleep(2)
                del st.session_state.memory_verse
                del st.session_state.show_verse
                st.experimental_rerun()

# Chat & Groups page
@require_auth
def chat_page():
    st.markdown('<h1 class="sub-header">💬 Chat & Groups</h1>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Direct Message", "Group Chat"])
    
    with tab1:
        st.subheader("Chat with another user")
        
        # Input for receiver's number
        receiver_number = st.text_input("Enter the recipient's code:", max_chars=6)
        
        if receiver_number:
            # Check if receiver exists
            receiver_profile = supabase_client.table("profiles").select("*").eq("number", receiver_number).execute()
            
            if receiver_profile.data:
                receiver = receiver_profile.data[0]
                st.write(f"Chat with: {receiver['username']} (#{receiver['number']})")
                
                # Get messages
                messages = supabase_client.table("messages").select("*").or_(f"sender_id.eq.{st.session_state.user.id},receiver_number.eq.{receiver_number}").execute()
                
                # Display messages
                chat_container = st.container()
                with chat_container:
                    for msg in sorted(messages.data, key=lambda x: x['created_at']):
                        if msg['sender_id'] == st.session_state.user.id:
                            st.markdown(f'<div class="chat-message user-message"><b>You:</b> {msg["message"]}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="chat-message other-message"><b>{receiver["username"]}:</b> {msg["message"]}</div>', unsafe_allow_html=True)
                
                # Send message
                new_message = st.text_input("Type your message:")
                if st.button("Send"):
                    if new_message:
                        supabase_client.table("messages").insert({
                            "sender_id": st.session_state.user.id,
                            "receiver_number": receiver_number,
                            "message": new_message
                        }).execute()
                        st.success("Message sent!")
                        time.sleep(0.5)
                        st.experimental_rerun()
            else:
                st.error("No user found with that code.")
    
    with tab2:
        st.subheader("Group Chats")
        
        # Sample groups
        groups = [
            {"name": "Youth Bible Study", "members": 12},
            {"name": "Worship Team", "members": 8},
            {"name": "Prayer Warriors", "members": 20}
        ]
        
        for group in groups:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{group['name']}**")
            with col2:
                if st.button("Join", key=f"join_{group['name']}"):
                    st.success(f"Joined {group['name']}!")
        
        st.divider()
        st.subheader("Create New Group")
        
        group_name = st.text_input("Group Name")
        if st.button("Create Group"):
            if group_name:
                st.success(f"Group '{group_name}' created!")
            else:
                st.error("Please enter a group name.")

# Profile page
@require_auth
def profile_page():
    st.markdown('<h1 class="sub-header">👤 Your Profile</h1>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Profile Info")
        st.write(f"**Username:** {st.session_state.profile['username']}")
        st.write(f"**Your Code:** #{st.session_state.profile['number']}")
        st.write(f"**Member Since:** {datetime.now().strftime('%B %d, %Y')}")
        
        st.divider()
        
        # Update profile form
        st.subheader("Update Profile")
        new_username = st.text_input("New Username", value=st.session_state.profile['username'])
        
        if st.button("Update Profile"):
            # Update in Supabase
            supabase_client.table("profiles").update({
                "username": new_username
            }).eq("id", st.session_state.user.id).execute()
            
            # Update session state
            st.session_state.profile['username'] = new_username
            st.success("Profile updated successfully!")
            time.sleep(1)
            st.experimental_rerun()
    
    with col2:
        st.subheader("Your Stats")
        
        col21, col22, col23 = st.columns(3)
        with col21:
            st.markdown('<div class="card"><h3>5</h3><p>Friends</p></div>', unsafe_allow_html=True)
        with col22:
            st.markdown('<div class="card"><h3>12</h3><p>Devotionals</p></div>', unsafe_allow_html=True)
        with col23:
            st.markdown('<div class="card"><h3>350</h3><p>Points</p></div>', unsafe_allow_html=True)
        
        st.subheader("Recent Activity")
        st.write("• Completed Bible Trivia - 50 points")
        st.write("• Added 2 new friends")
        st.write("• Shared a verse with a friend")
        st.write("• Joined Worship Team group")

# Main app logic
def main():
    if not check_auth():
        login_page()
    else:
        navigation()
        
        if st.session_state.page == "🏠 Home":
            home_page()
        elif st.session_state.page == "📖 Bible Reader":
            bible_reader_page()
        elif st.session_state.page == "🎶 Music Player":
            music_player_page()
        elif st.session_state.page == "🎮 Games":
            games_page()
        elif st.session_state.page == "💬 Chat & Groups":
            chat_page()
        elif st.session_state.page == "👤 Profile":
            profile_page()

if __name__ == "__main__":
    main()

