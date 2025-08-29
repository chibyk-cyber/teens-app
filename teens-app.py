import streamlit as st
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
    }
    .other-message {
        background-color: #F1F0F0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'profile' not in st.session_state:
    st.session_state.profile = None
if 'page' not in st.session_state:
    st.session_state.page = 'Home'
if 'messages' not in st.session_state:
    st.session_state.messages = {}
if 'users' not in st.session_state:
    # Sample users for demo
    st.session_state.users = {
        'user1': {'username': 'TeenUser1', 'number': '1234', 'password': 'pass1'},
        'user2': {'username': 'TeenUser2', 'number': '5678', 'password': 'pass2'}
    }
if 'current_song' not in st.session_state:
    st.session_state.current_song = None
if 'audio_playing' not in st.session_state:
    st.session_state.audio_playing = False

# Simple authentication functions
def sign_up(username, number, password):
    try:
        # In a real app, this would save to Supabase
        user_id = f"user{random.randint(1000, 9999)}"
        st.session_state.users[user_id] = {
            'username': username,
            'number': number,
            'password': password  # In real app, hash this
        }
        return True, "Sign up successful! Please log in."
    except Exception as e:
        return False, f"Error: {str(e)}"

def sign_in(username, password):
    try:
        # Simple demo authentication
        for user_id, user_data in st.session_state.users.items():
            if user_data['username'] == username and user_data.get('password') == password:
                st.session_state.user = user_id
                st.session_state.profile = user_data
                return True, "Login successful!"
        return False, "Invalid username or password."
    except Exception as e:
        return False, f"Error: {str(e)}"

def sign_out():
    st.session_state.user = None
    st.session_state.profile = None
    st.session_state.page = 'Home'
    st.session_state.current_song = None
    st.session_state.audio_playing = False
    st.experimental_rerun()

def check_auth():
    return st.session_state.user is not None

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
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Login")
            
            if login_btn:
                success, message = sign_in(username, password)
                if success:
                    st.success(message)
                    time.sleep(1)
                    st.experimental_rerun()
                else:
                    st.error(message)
    
    with tab2:
        with st.form("signup_form"):
            username = st.text_input("Username")
            number = st.text_input("4+ Digit Code", max_chars=6)
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            # Validate inputs
            if number and (not number.isdigit() or len(number) < 4):
                st.error("Please enter a valid 4+ digit code")
            
            if password != confirm_password:
                st.error("Passwords do not match")
            
            signup_btn = st.form_submit_button("Create Account")
            
            if signup_btn:
                if not number.isdigit() or len(number) < 4:
                    st.error("Please enter a valid 4+ digit code")
                elif password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    success, message = sign_up(username, number, password)
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
        pages = {
            "🏠 Home": "Home",
            "📖 Bible Reader": "Bible Reader",
            "🎶 Music Player": "Music Player",
            "🎮 Games": "Games",
            "💬 Chat": "Chat",
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
    
    books_of_bible = [
        "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
        "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel",
        "Matthew", "Mark", "Luke", "John", "Acts",
        "Romans", "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
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
            }
            
            if selected_book in sample_verses and chapter in sample_verses[selected_book] and verse in sample_verses[selected_book][chapter]:
                verse_text = sample_verses[selected_book][chapter][verse]
            else:
                verse_text = "The Lord bless you and keep you; the Lord make his face shine on you and be gracious to you. - Numbers 6:24-25"
            
            st.markdown(f'<div class="card"><h3>{selected_book} {chapter}:{verse}</h3><p>{verse_text}</p></div>', unsafe_allow_html=True)
            
            if st.button("❤️ Add to Favorites"):
                st.success("Verse added to favorites!")
        else:
            st.info("Select a book, chapter, and verse to begin reading.")

# Music Player page
@require_auth
def music_player_page():
    st.markdown('<h1 class="sub-header">🎶 Music Player</h1>', unsafe_allow_html=True)
    
    # Public domain worship songs that can be streamed
    worship_songs = [
        {"title": "Amazing Grace", "artist": "Traditional", "url": "https://www.christiansongs.com.au/mp3/amazing_grace.mp3"},
        {"title": "What a Friend We Have in Jesus", "artist": "Traditional", "url": "https://www.christiansongs.com.au/mp3/what_a_friend.mp3"},
        {"title": "How Great Thou Art", "artist": "Traditional", "url": "https://www.christiansongs.com.au/mp3/how_great_thou_art.mp3"},
    ]
    
    for i, song in enumerate(worship_songs):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**{song['title']}**")
            st.write(f"*{song['artist']}*")
        with col2:
            if st.button("▶️ Play", key=f"play_{i}"):
                st.session_state.current_song = song
                st.session_state.audio_playing = True
                st.success(f"Playing: {song['title']}")
                st.experimental_rerun()
    
    # Display current song and audio player
    if st.session_state.current_song:
        st.divider()
        st.subheader("Now Playing")
        st.write(f"**{st.session_state.current_song['title']}** by {st.session_state.current_song['artist']}")
        
        # Audio player
        st.audio(st.session_state.current_song['url'], format="audio/mp3")
        
        # Player controls
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("⏮ Previous"):
                st.info("Previous song selected")
        with col2:
            if st.button("⏸ Pause" if st.session_state.audio_playing else "▶️ Play"):
                st.session_state.audio_playing = not st.session_state.audio_playing
                st.experimental_rerun()
        with col3:
            if st.button("⏭ Next"):
                st.info("Next song selected")
    
    # If no song is selected, show instructions
    else:
        st.info("Select a song to begin listening")

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
            },
            {
                "question": "How many books are in the New Testament?",
                "options": ["27", "39", "66", "50"],
                "answer": "27"
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
                time.sleep(1)
                del st.session_state.scramble_word
                del st.session_state.scrambled
                st.experimental_rerun()
            else:
                st.error("Try again!")

# Chat page
@require_auth
def chat_page():
    st.markdown('<h1 class="sub-header">💬 Chat</h1>', unsafe_allow_html=True)
    
    st.subheader("Chat with another user")
    
    # Input for receiver's number
    receiver_number = st.text_input("Enter the recipient's code:", max_chars=6)
    
    if receiver_number:
        # Find receiver
        receiver = None
        for user_id, user_data in st.session_state.users.items():
            if user_data['number'] == receiver_number:
                receiver = user_data
                break
        
        if receiver:
            st.write(f"Chat with: {receiver['username']} (#{receiver['number']})")
            
            # Initialize chat if not exists
            chat_id = f"{st.session_state.profile['number']}_{receiver_number}"
            if chat_id not in st.session_state.messages:
                st.session_state.messages[chat_id] = []
            
            # Display messages
            chat_container = st.container()
            with chat_container:
                for msg in st.session_state.messages[chat_id]:
                    if msg['sender'] == st.session_state.profile['number']:
                        st.markdown(f'<div class="chat-message user-message"><b>You:</b> {msg["text"]}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="chat-message other-message"><b>{receiver["username"]}:</b> {msg["text"]}</div>', unsafe_allow_html=True)
            
            # Send message
            new_message = st.text_input("Type your message:")
            if st.button("Send"):
                if new_message:
                    st.session_state.messages[chat_id].append({
                        "sender": st.session_state.profile['number'],
                        "text": new_message,
                        "time": datetime.now().strftime("%H:%M")
                    })
                    st.success("Message sent!")
                    time.sleep(0.5)
                    st.experimental_rerun()
        else:
            st.error("No user found with that code.")

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
        
        st.subheader("Update Profile")
        new_username = st.text_input("New Username", value=st.session_state.profile['username'])
        
        if st.button("Update Profile"):
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
        elif st.session_state.page == "Chat":
            chat_page()
        elif st.session_state.page == "Profile":
            profile_page()

if __name__ == "__main__":
    main()
