import streamlit as st
import requests
from supabase import create_client, Client
import json

# Supabase setup using secrets
supabase_url = st.secrets["SUPABASE_URL"]
supabase_key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(supabase_url, supabase_key)

# Session state for user authentication
if 'user' not in st.session_state:
    st.session_state.user = None

# Authentication functions
def sign_up():
    st.header("Sign Up")
    email = st.text_input("Email", key="signup_email")
    password = st.text_input("Password", type="password", key="signup_password")
    if st.button("Sign Up"):
        try:
            response = supabase.auth.sign_up({"email": email, "password": password})
            st.success("Sign up successful! Please check your email to confirm.")
        except Exception as e:
            st.error(f"Sign up failed: {str(e)}")

def login():
    st.header("Sign In")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")
    if st.button("Sign In"):
        try:
            response = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state.user = response.user
            st.success("Logged in successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Login failed: {str(e)}")

def logout():
    supabase.auth.sign_out()
    st.session_state.user = None
    st.rerun()

# Bible books and chapters (hardcoded for KJV)
bible_books = {
    "Genesis": 50, "Exodus": 40, "Leviticus": 27, "Numbers": 36, "Deuteronomy": 34,
    "Joshua": 24, "Judges": 21, "Ruth": 4, "1 Samuel": 31, "2 Samuel": 24,
    "1 Kings": 22, "2 Kings": 25, "1 Chronicles": 29, "2 Chronicles": 36, "Ezra": 10,
    "Nehemiah": 13, "Esther": 10, "Job": 42, "Psalms": 150, "Proverbs": 31,
    "Ecclesiastes": 12, "Song of Solomon": 8, "Isaiah": 66, "Jeremiah": 52,
    "Lamentations": 5, "Ezekiel": 48, "Daniel": 12, "Hosea": 14, "Joel": 3,
    "Amos": 9, "Obadiah": 1, "Jonah": 4, "Micah": 7, "Nahum": 3,
    "Habakkuk": 3, "Zephaniah": 3, "Haggai": 2, "Zechariah": 14, "Malachi": 4,
    "Matthew": 28, "Mark": 16, "Luke": 24, "John": 21, "Acts": 28,
    "Romans": 16, "1 Corinthians": 16, "2 Corinthians": 13, "Galatians": 6,
    "Ephesians": 6, "Philippians": 4, "Colossians": 4, "1 Thessalonians": 5,
    "2 Thessalonians": 3, "1 Timothy": 6, "2 Timothy": 4, "Titus": 3, "Philemon": 1,
    "Hebrews": 13, "James": 5, "1 Peter": 5, "2 Peter": 3, "1 John": 5,
    "2 John": 1, "3 John": 1, "Jude": 1, "Revelation": 22
}

# Function to fetch chapter from bible-api.com
def fetch_chapter(book, chapter):
    url = f"https://bible-api.com/{book} {chapter}?translation=kjv"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get('verses', [])
    return []

# Function to search Bible using biblesupersearch
def search_bible(query):
    url = "https://api.biblesupersearch.com/api"
    params = {
        "search": query,
        "bible": "kjv",
        "whole_words": "false",
        "page_limit": 20
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data.get('results', [])
    return []

# Supabase favorites functions
def save_favorite(verse_ref, verse_text):
    user_id = st.session_state.user.id
    data = {"user_id": user_id, "verse_ref": verse_ref, "verse_text": verse_text}
    supabase.table("favorites").insert(data).execute()

def get_favorites():
    user_id = st.session_state.user.id
    response = supabase.table("favorites").select("*").eq("user_id", user_id).execute()
    return response.data

def delete_favorite(fav_id):
    supabase.table("favorites").delete().eq("id", fav_id).execute()

# WAEC Quiz functions
subjects = ["mathematics", "biology", "physics", "chemistry"]

def fetch_waec_questions(subject, num_questions=10):
    url = f"https://questions.aloc.ng/api/v2/q/{num_questions}?subject={subject}&type=wassce"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get('data', [])
    return []

# Main app
if st.session_state.user is None:
    tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
    with tab1:
        login()
    with tab2:
        sign_up()
else:
    st.sidebar.button("Log Out", on_click=logout)

    st.header("Welcome to the MVP App!")

    tab_bible, tab_waec, tab_social = st.tabs(["Bible", "WAEC Preparer", "Social Media"])

    with tab_bible:
        st.subheader("Bible App (KJV)")
        bible_subtab1, bible_subtab2, bible_subtab3 = st.tabs(["Search", "Browse", "Favorites"])

        with bible_subtab1:
            search_query = st.text_input("Search keywords (e.g., 'love God')")
            if search_query:
                results = search_bible(search_query)
                if results:
                    for verse in results:
                        st.markdown(f"**{verse['reference']}**: {verse['text']}")
                        if st.button("Save", key=f"save_search_{verse['reference']}"):
                            save_favorite(verse['reference'], verse['text'])
                            st.success("Saved!")
                else:
                    st.info("No results found.")

        with bible_subtab2:
            book = st.selectbox("Select Book", list(bible_books.keys()))
            if book:
                chapter = st.selectbox("Select Chapter", range(1, bible_books[book] + 1))
                if chapter:
                    verses = fetch_chapter(book.lower().replace(" ", ""), chapter)
                    if verses:
                        for v in verses:
                            st.markdown(f"**{v['reference']}**: {v['text']}")
                            if st.button("Save", key=f"save_browse_{v['reference']}"):
                                save_favorite(v['reference'], v['text'])
                                st.success("Saved!")
                    else:
                        st.error("Failed to fetch chapter.")

        with bible_subtab3:
            favorites = get_favorites()
            if favorites:
                for fav in favorites:
                    st.markdown(f"**{fav['verse_ref']}**: {fav['verse_text']}")
                    if st.button("Delete", key=f"del_{fav['id']}"):
                        delete_favorite(fav['id'])
                        st.rerun()
            else:
                st.info("No favorites yet.")

    with tab_waec:
        st.subheader("WAEC Preparer")
        selected_subject = st.selectbox("Select Subject", [s.capitalize() for s in subjects])
        if selected_subject:
            if st.button("Start Quiz (10 Questions)"):
                questions = fetch_waec_questions(selected_subject.lower())
                if questions:
                    st.session_state.quiz_questions = questions
                    st.session_state.quiz_answers = {}
                    st.session_state.quiz_submitted = False
                    st.rerun()
                else:
                    st.error("Failed to fetch questions.")

            if 'quiz_questions' in st.session_state and not st.session_state.quiz_submitted:
                for i, q in enumerate(st.session_state.quiz_questions):
                    st.write(f"**Question {i+1}:** {q['question']}")
                    options = q.get('options', {})
                    selected = st.radio("Options", list(options.values()), key=f"q_{i}")
                    st.session_state.quiz_answers[i] = selected

                if st.button("Submit Quiz"):
                    st.session_state.quiz_submitted = True
                    score = 0
                    for i, q in enumerate(st.session_state.quiz_questions):
                        correct = q['options'][q['answer']]
                        if st.session_state.quiz_answers.get(i) == correct:
                            score += 1
                    st.success(f"Your score: {score}/{len(questions)}")
                    st.rerun()

    with tab_social:
        st.subheader("Social Media Links")
        st.link_button("TikTok", "https://www.tiktok.com/")
        st.link_button("Instagram", "https://www.instagram.com/")
        st.link_button("Facebook", "https://www.facebook.com/")
