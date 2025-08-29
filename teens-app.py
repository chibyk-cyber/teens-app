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
    .subject-card {
        background: linear-gradient(135deg, #6e8efb, #a777e3);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
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
if 'group_messages' not in st.session_state:
    st.session_state.group_messages = {}
if 'users' not in st.session_state:
    # Sample users for demo
    st.session_state.users = {
        'user1': {'username': 'TeenUser1', 'number': '1234', 'password': 'pass1'},
        'user2': {'username': 'TeenUser2', 'number': '5678', 'password': 'pass2'},
        'user3': {'username': 'StudyBuddy', 'number': '9999', 'password': 'pass3'}
    }
if 'current_song' not in st.session_state:
    st.session_state.current_song = None
if 'audio_playing' not in st.session_state:
    st.session_state.audio_playing = False
if 'study_groups' not in st.session_state:
    st.session_state.study_groups = {
        'math_group': {'name': 'Mathematics Club', 'members': ['1234', '5678']},
        'science_group': {'name': 'Science Squad', 'members': ['1234']},
        'english_group': {'name': 'English Masters', 'members': ['5678']}
    }

# WAEC Questions
waec_questions = {
    "Mathematics": [
        "1. Simplify: 2⅓ ÷ (2⅔ of 1⅕)",
        "2. If 2x + y = 10 and y = 4, find the value of x",
        "3. Solve the equation: 3x - 5 = 16",
        "4. Factorize completely: 6x² - 13x + 6",
        "5. Find the area of a circle with radius 7cm (Take π = 22/7)",
        "6. If 5 people can do a piece of work in 6 days, how long will 3 people take?",
        "7. Calculate the mean of these numbers: 12, 15, 18, 20, 25",
        "8. Solve the simultaneous equations: 2x + y = 7, x - y = 2",
        "9. Find the value of x in the equation: 2^(x+1) = 16",
        "10. A rectangle has length 12cm and width 8cm. Find its perimeter"
    ],
    "English": [
        "1. Which of these is not a part of speech?",
        "2. Change to indirect speech: 'I will come tomorrow,' she said",
        "3. Identify the figure of speech: 'The stars danced playfully in the moonlit sky'",
        "4. Correct the sentence: 'Neither of the boys are coming'",
        "5. What is the plural of 'cactus'?",
        "6. Fill in the blank: She has been living here ____ 2010",
        "7. Identify the tense: 'I will have finished my work by tomorrow'",
        "8. What is the synonym of 'benevolent'?",
        "9. Change to passive voice: 'The teacher praised the student'",
        "10. What is the opposite of 'expand'?"
    ],
    "Biology": [
        "1. What is the basic unit of life?",
        "2. Name the process by which plants make their own food",
        "3. Which cell organelle is called the powerhouse of the cell?",
        "4. What is the function of the red blood cells?",
        "5. Name the blood vessels that carry blood away from the heart",
        "6. What is photosynthesis?",
        "7. Which part of the brain controls balance?",
        "8. What is the function of the ribosomes?",
        "9. Name the male and female reproductive parts of a flower",
        "10. What is osmosis?"
    ],
    "Physics": [
        "1. What is the SI unit of force?",
        "2. State Newton's first law of motion",
        "3. Calculate the work done when a force of 10N moves an object 5m",
        "4. What is the law of conservation of energy?",
        "5. Define velocity",
        "6. What is the difference between mass and weight?",
        "7. State Ohm's law",
        "8. What is refraction of light?",
        "9. Name the type of mirror used as a side mirror in cars",
        "10. What is the unit of electric current?"
    ],
    "Chemistry": [
        "1. What is an atom?",
        "2. Name the three states of matter",
        "3. What is the chemical formula for water?",
        "4. Define pH",
        "5. What is the periodic table?",
        "6. Name the elements represented by Na, K, and Fe",
        "7. What is a chemical reaction?",
        "8. Define oxidation",
        "9. What is the difference between an element and a compound?",
        "10. Name the process by which solid changes directly to gas"
    ]
}

# Study Topics
study_topics = {
    "Mathematics": [
        "Algebraic Expressions", "Quadratic Equations", "Simultaneous Equations", 
        "Trigonometry", "Geometry", "Statistics", "Probability", "Calculus",
        "Vectors", "Matrices", "Coordinate Geometry", "Number Bases",
        "Financial Mathematics", "Variation", "Mensuration"
    ],
    "Biology": [
        "Cell Biology", "Genetics", "Ecology", "Evolution", "Human Anatomy",
        "Plant Biology", "Animal Kingdom", "Reproduction", "Photosynthesis",
        "Respiration", "Digestive System", "Nervous System", "Circulatory System",
        "Excretory System", "Endocrine System", "Immunology"
    ],
    "Physics": [
        "Mechanics", "Thermodynamics", "Electricity and Magnetism", "Waves",
        "Optics", "Nuclear Physics", "Quantum Mechanics", "Motion",
        "Forces", "Energy", "Work and Power", "Simple Machines",
        "Sound", "Light", "Electromagnetism", "Modern Physics"
    ]
}

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
    
    st.divider()
    st.subheader("Recent Activity")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("📚 New study materials uploaded")
        st.write("👥 3 new members joined this week")
        st.write("🏆 You earned 50 points in quizzes")
    
    with col2:
        st.write("💬 5 new messages in study groups")
        st.write("⭐ You completed 7 daily devotionals")
        st.write("🎯 3 days until next exam")

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
    
    game_choice = st.radio("Choose a game:", ["Bible Trivia", "Word Scramble", "Math Challenge"])
    
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
    
    elif game_choice == "Math Challenge":
        st.subheader("Math Challenge")
        
        operations = ["Addition", "Subtraction", "Multiplication", "Division"]
        selected_op = st.selectbox("Select operation:", operations)
        
        if st.button("Generate Problem"):
            if selected_op == "Addition":
                a, b = random.randint(10, 100), random.randint(10, 100)
                st.session_state.math_problem = f"{a} + {b} = ?"
                st.session_state.math_answer = a + b
            elif selected_op == "Subtraction":
                a, b = random.randint(10, 100), random.randint(10, 100)
                if a < b:
                    a, b = b, a
                st.session_state.math_problem = f"{a} - {b} = ?"
                st.session_state.math_answer = a - b
            elif selected_op == "Multiplication":
                a, b = random.randint(2, 12), random.randint(2, 12)
                st.session_state.math_problem = f"{a} × {b} = ?"
                st.session_state.math_answer = a * b
            else:  # Division
                b = random.randint(2, 12)
                a = b * random.randint(2, 12)
                st.session_state.math_problem = f"{a} ÷ {b} = ?"
                st.session_state.math_answer = a // b
        
        if 'math_problem' in st.session_state:
            st.write(f"**Problem:** {st.session_state.math_problem}")
            answer = st.number_input("Your answer:", step=1, format="%d")
            
            if st.button("Check Answer"):
                if answer == st.session_state.math_answer:
                    st.success("Correct! 🎉")
                else:
                    st.error(f"Sorry, the correct answer is {st.session_state.math_answer}")

# Study Hub page
@require_auth
def study_hub_page():
    st.markdown('<h1 class="sub-header">📚 Study Hub</h1>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["WAEC Questions", "Study Topics", "Study Resources"])
    
    with tab1:
        st.subheader("WAEC Practice Questions")
        
        subject = st.selectbox("Select Subject:", list(waec_questions.keys()))
        
        if subject:
            st.write(f"**{subject} Questions:**")
            for question in waec_questions[subject]:
                st.write(f"• {question}")
            
            if st.button("Show Answers", key="show_answers"):
                # Sample answers (in a real app, you'd have full answers)
                st.info("Answers will be displayed here after you attempt the questions")
    
    with tab2:
        st.subheader("Study Topics by Subject")
        
        subject = st.selectbox("Select Subject:", list(study_topics.keys()))
        
        if subject:
            st.write(f"**{subject} Topics:**")
            for topic in study_topics[subject]:
                st.markdown(f'<div class="subject-card">{topic}</div>', unsafe_allow_html=True)
    
    with tab3:
        st.subheader("Study Resources")
        
        st.write("**Recommended Textbooks:**")
        st.write("- Comprehensive Mathematics for Senior Secondary Schools")
        st.write("- Essential Biology for Senior Secondary Schools")
        st.write("- New School Physics for Senior Secondary Schools")
        st.write("- Exam Focus: Literature in English")
        
        st.write("**Online Resources:**")
        st.write("- Khan Academy (khanacademy.org)")
        st.write("- Crash Course YouTube Channel")
        st.write("- WAEC e-Learning Portal")
        st.write("- Nerdcampus YouTube Channel")
        
        st.write("**Study Tips:**")
        st.write("- Create a study schedule and stick to it")
        st.write("- Take regular breaks during study sessions")
        st.write("- Practice past questions regularly")
        st.write("- Form study groups with friends")
        st.write("- Teach concepts to others to reinforce your understanding")

# Chat & Groups page
@require_auth
def chat_page():
    st.markdown('<h1 class="sub-header">💬 Chat & Groups</h1>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Direct Message", "Study Groups", "Create Group"])
    
    with tab1:
        st.subheader("Chat with another user")
        
        # Input for receiver's number
        receiver_number = st.text_input("Enter the recipient's code:", max_chars=6, key="dm_code")
        
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
                            st.markdown(f'<div class="chat-message user-message"><b>You:</b> {msg["text"]} <i>({msg["time"]})</i></div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="chat-message other-message"><b>{receiver["username"]}:</b> {msg["text"]} <i>({msg["time"]})</i></div>', unsafe_allow_html=True)
                
                # Send message
                new_message = st.text_input("Type your message:", key="dm_message")
                if st.button("Send", key="dm_send"):
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
    
    with tab2:
        st.subheader("Study Groups")
        
        # Display user's groups
        user_groups = []
        for group_id, group_data in st.session_state.study_groups.items():
            if st.session_state.profile['number'] in group_data['members']:
                user_groups.append((group_id, group_data))
        
        if user_groups:
            st.write("**Your Study Groups:**")
            for group_id, group_data in user_groups:
                with st.expander(f"📚 {group_data['name']} ({len(group_data['members'])} members)"):
                    # Group chat
                    if group_id not in st.session_state.group_messages:
                        st.session_state.group_messages[group_id] = []
                    
                    # Display group messages
                    for msg in st.session_state.group_messages[group_id]:
                        sender_name = "You" if msg['sender'] == st.session_state.profile['number'] else msg['sender_name']
                        st.markdown(f'<div class="chat-message"><b>{sender_name}:</b> {msg["text"]} <i>({msg["time"]})</i></div>', unsafe_allow_html=True)
                    
                    # Send group message
                    group_message = st.text_input("Type your message:", key=f"group_{group_id}")
                    if st.button("Send", key=f"send_{group_id}"):
                        if group_message:
                            st.session_state.group_messages[group_id].append({
                                "sender": st.session_state.profile['number'],
                                "sender_name": st.session_state.profile['username'],
                                "text": group_message,
                                "time": datetime.now().strftime("%H:%M")
                            })
                            st.success("Message sent to group!")
                            time.sleep(0.5)
                            st.experimental_rerun()
        else:
            st.info("You haven't joined any study groups yet.")
    
    with tab3:
        st.subheader("Create a New Study Group")
        
        group_name = st.text_input("Group Name:")
        subject = st.selectbox("Subject Focus:", ["Mathematics", "English", "Biology", "Physics", "Chemistry", "General"])
        
        if st.button("Create Group"):
            if group_name:
                group_id = f"group_{random.randint(1000, 9999)}"
                st.session_state.study_groups[group_id] = {
                    'name': group_name,
                    'subject': subject,
                    'members': [st.session_state.profile['number']]
                }
                st.success(f"Group '{group_name}' created successfully!")
                time.sleep(1)
                st.experimental_rerun()
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
        
        st.subheader("Study Progress")
        st.write("📊 Mathematics: 75% complete")
        st.write("📊 English: 60% complete")
        st.write("📊 Biology: 85% complete")
        st.write("📊 Physics: 50% complete")
        
        st.subheader("Achievements")
        st.write("🏆 Bible Scholar (Read 50 verses)")
        st.write("🏆 Math Whiz (Solved 100 problems)")
        st.write("🏆 Study Buddy (Joined 3 groups)")

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
