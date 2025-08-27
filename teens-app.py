import streamlit as st
import sqlite3
from datetime import datetime, date, timedelta
import pandas as pd
import random
import json
import requests
from typing import List, Dict, Any

# ---------------- Database ----------------
conn = sqlite3.connect("teens_app.db", check_same_thread=False)
c = conn.cursor()

# Create tables
c.execute("""CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    content TEXT,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)""")

c.execute("""CREATE TABLE IF NOT EXISTS schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task TEXT,
    date TEXT,
    time TEXT
)""")

conn.commit()

# ---------------- Notes ----------------
def add_note(title, content):
    c.execute("INSERT INTO notes (title, content) VALUES (?, ?)", (title, content))
    conn.commit()

def view_notes():
    c.execute("SELECT * FROM notes ORDER BY created DESC")
    return c.fetchall()

def delete_note(note_id):
    c.execute("DELETE FROM notes WHERE id=?", (note_id,))
    conn.commit()

def update_note(note_id, new_title, new_content):
    c.execute("UPDATE notes SET title=?, content=? WHERE id=?", (new_title, new_content, note_id))
    conn.commit()

# ---------------- Schedule ----------------
def add_task(task, date_, time_):
    c.execute("INSERT INTO schedule (task, date, time) VALUES (?, ?, ?)", (task, date_, time_))
    conn.commit()

def view_schedule():
    c.execute("SELECT * FROM schedule ORDER BY date, time")
    return c.fetchall()

# ---------------- Study Materials ----------------
study_materials = {
    "Mathematics": ["Algebra", "Geometry", "Trigonometry", "Calculus"],
    "Biology": ["Cell Biology", "Genetics", "Ecology", "Human Anatomy"],
    "Physics": ["Mechanics", "Electricity", "Magnetism", "Waves"],
    "Chemistry": ["Atomic Structure", "Periodic Table", "Chemical Reactions"]
}

# ---------------- Exam Questions ----------------
exam_questions = {
    "Mathematics": [
        "Solve: 2x + 5 = 15",
        "Find the derivative of x² + 3x + 2"
    ],
    "Biology": [
        "What is the powerhouse of the cell?",
        "Explain Mendel’s law of inheritance."
    ]
}

def get_random_question(subject):
    if subject in exam_questions:
        return random.choice(exam_questions[subject])
    return "No questions available for this subject."

# ---------------- Bible API ----------------
def display_bible_verse(book, chapter, verse):
    url = f"https://bible-api.com/{book}+{chapter}:{verse}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            st.success(f"{data['reference']}")
            st.write(data["text"])
            st.caption(f"Translation: {data['translation_name']}")
        else:
            st.error("Verse not found. Try again.")
    except Exception as e:
        st.error("Error connecting to Bible API")

# ---------------- Daily Verse ----------------
def load_daily_verses():
    try:
        with open("daily_verses.json", "r") as f:
            return json.load(f)
    except:
        # fallback default list
        return [
            {"book": "John", "chapter": 3, "verse": "16"},
            {"book": "Psalm", "chapter": 23, "verse": "1"},
            {"book": "Philippians", "chapter": 4, "verse": "13"},
            {"book": "Genesis", "chapter": 1, "verse": "1"},
            {"book": "Romans", "chapter": 8, "verse": "28"},
            {"book": "Isaiah", "chapter": 40, "verse": "31"},
            {"book": "Proverbs", "chapter": 3, "verse": "5-6"}
        ]

def daily_verse():
    verses = load_daily_verses()
    today = date.today()
    index = today.toordinal() % len(verses)
    chosen = verses[index]
    return chosen["book"], chosen["chapter"], chosen["verse"]

# ---------------- UI Sections ----------------
def home_section():
    st.title("👋 Welcome to Teens App")
    st.write("Your all-in-one app for study, notes, activities, and faith.")

    st.subheader("📖 Daily Verse")
    book, chapter, verse = daily_verse()
    display_bible_verse(book, chapter, verse)

def social_media_section():
    st.header("🌍 Social Media Links")
    st.write("Stay connected:")
    st.markdown("[Instagram](https://instagram.com)")
    st.markdown("[Twitter](https://twitter.com)")
    st.markdown("[Facebook](https://facebook.com)")

def notes_section():
    st.header("📝 Notes")

    option = st.radio("Choose action", ["Add Note", "View Notes"])
    if option == "Add Note":
        title = st.text_input("Title")
        content = st.text_area("Content")
        if st.button("Save"):
            add_note(title, content)
            st.success("Note saved!")

    elif option == "View Notes":
        notes = view_notes()
        for note in notes:
            st.subheader(note[1])
            st.write(note[2])
            if st.button(f"Delete {note[0]}"):
                delete_note(note[0])
                st.warning("Note deleted!")
            if st.button(f"Edit {note[0]}"):
                new_title = st.text_input("New Title", value=note[1], key=f"title_{note[0]}")
                new_content = st.text_area("New Content", value=note[2], key=f"content_{note[0]}")
                if st.button(f"Update {note[0]}"):
                    update_note(note[0], new_title, new_content)
                    st.success("Note updated!")

def schedule_section():
    st.header("📅 Schedule Activities")

    task = st.text_input("Task")
    date_ = st.date_input("Date", min_value=date.today())
    time_ = st.time_input("Time")

    if st.button("Add Task"):
        add_task(task, str(date_), str(time_))
        st.success("Task added!")

    st.subheader("Your Schedule")
    tasks = view_schedule()
    df = pd.DataFrame(tasks, columns=["ID", "Task", "Date", "Time"])
    st.table(df)

def study_materials_section():
    st.header("📚 Study Materials")
    subject = st.selectbox("Select Subject", list(study_materials.keys()))
    st.subheader(f"Chapters in {subject}:")
    for chapter in study_materials[subject]:
        st.write(f"- {chapter}")

def exam_section():
    st.header("❓ Exam Practice")
    subject = st.selectbox("Choose Subject", list(exam_questions.keys()))
    if st.button("Get Question"):
        question = get_random_question(subject)
        st.info(question)

def bible_section():
    st.header("📖 Bible Search")
    book = st.text_input("Book (e.g., John)")
    chapter = st.text_input("Chapter (e.g., 3)")
    verse = st.text_input("Verse (e.g., 16 or 16-18)")
    if st.button("Get Verse"):
        display_bible_verse(book, chapter, verse)

# ---------------- Main ----------------
st.set_page_config(page_title="Teens App", layout="wide")

# Background
st.markdown(
    """
    <style>
    .stApp {
        background: url("https://i.imgur.com/BkQXsgc.jpeg");
        background-size: cover;
    }
    </style>
    """,
    unsafe_allow_html=True
)

menu = st.sidebar.radio("Menu", ["Home", "Social Media", "Notes", "Schedule", "Study Materials", "Exam Questions", "Bible"])

if menu == "Home":
    home_section()
elif menu == "Social Media":
    social_media_section()
elif menu == "Notes":
    notes_section()
elif menu == "Schedule":
    schedule_section()
elif menu == "Study Materials":
    study_materials_section()
elif menu == "Exam Questions":
    exam_section()
elif menu == "Bible":
    bible_section()

