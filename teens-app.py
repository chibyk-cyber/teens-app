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
