import streamlit as st
import sqlite3
from datetime import datetime, date, timedelta
import pandas as pd
import random
import json
import requests

# ---------------- CUSTOM STYLING ----------------
page_bg = """
<style>
.stApp {
    background-image: url("https://i.imgur.com/gny6JlY.jpeg");
    background-size: cover;
    background-attachment: fixed;
}

h1, h2, h3, h4, h5, h6, p, div, span, label {
    color: white !important;
    text-shadow: 1px 1px 2px black;
}

textarea, input, .stTextInput, .stTextArea, .stSelectbox, .stMultiSelect {
    background-color: rgba(0,0,0,0.6) !important;
    color: white !important;
}
</style>
"""
st.markdown(page_bg, unsafe_allow_html=True)

# ---------------- DATABASE SETUP ----------------
conn = sqlite3.connect("teens_app.db")
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    content TEXT,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)""")

c.execute("""CREATE TABLE IF NOT EXISTS schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task TEXT,
    date DATE,
    time TIME
)""")
conn.commit()

# ---------------- STUDY MATERIALS ----------------
study_materials = {
    "Mathematics": ["Algebra", "Geometry", "Trigonometry", "Calculus"],
    "English": ["Grammar", "Comprehension", "Essay Writing"],
    "Biology": ["Cell Biology", "Genetics", "Human Anatomy"],
    "Physics": ["Mechanics", "Electricity", "Waves"],
    "Chemistry": ["Atomic Structure", "Organic Chemistry", "Inorganic Chemistry"]
}

# ---------------- DAILY VERSES ----------------
def load_daily_verses():
    verses = [
        {"book": "John", "chapter": 3, "verse": "16"},
        {"book": "Psalm", "chapter": 23, "verse": "1"},
        {"book": "Philippians", "chapter": 4, "verse": "13"},
        {"book": "Genesis", "chapter": 1, "verse": "1"},
        {"book": "Romans", "chapter": 8, "verse": "28"},
        {"book": "Isaiah", "chapter": 40, "verse": "31"},
        {"book": "Proverbs", "chapter": 3, "verse": "5-6"}
    ]
    return verses

def daily_verse():
    verses = load_daily_verses()
    today = date.today()
    index = today.toordinal() % len(verses)
    return verses[index]

def display_bible_verse(book, chapter, verse):
    url = f"https://bible-api.com/{book}+{chapter}:{verse}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            st.success(f"{data['reference']}: {data['text']}")
        else:
            st.error("Unable to fetch verse right now.")
    except:
        st.error("Error connecting to Bible API.")

# ---------------- HOME ----------------
def home_section():
    st.title("👋 Welcome to Teens App")
    st.write("Your all-in-one app for study, notes, activities, and faith.")

    st.subheader("📖 Daily Verse")
    v = daily_verse()
    display_bible_verse(v["book"], v["chapter"], v["verse"])

# ---------------- STUDY MATERIALS ----------------
def study_section():
    st.title("📚 Study Materials")
    subject = st.selectbox("Choose a subject", list(study_materials.keys()))
    if subject:
        st.write(f"### {subject} Chapters")
        for chap in study_materials[subject]:
            st.write(f"- {chap}")

# ---------------- NOTES ----------------
def notes_section():
    st.title("📝 Notepad")
    option = st.radio("Options", ["Add Note", "View Notes", "Search Notes"])

    if option == "Add Note":
        title = st.text_input("Note Title")
        content = st.text_area("Write your note here...")
        if st.button("Save Note"):
            c.execute("INSERT INTO notes (title, content) VALUES (?, ?)", (title, content))
            conn.commit()
            st.success("Note saved!")

    elif option == "View Notes":
        c.execute("SELECT * FROM notes ORDER BY created DESC")
        rows = c.fetchall()
        for r in rows:
            st.write(f"### {r[1]} ({r[3]})")
            st.write(r[2])
            if st.button(f"Delete {r[0]}"):
                c.execute("DELETE FROM notes WHERE id=?", (r[0],))
                conn.commit()
                st.success("Note deleted.")

    elif option == "Search Notes":
        keyword = st.text_input("Enter keyword")
        if keyword:
            c.execute("SELECT * FROM notes WHERE title LIKE ? OR content LIKE ?", 
                      (f"%{keyword}%", f"%{keyword}%"))
            results = c.fetchall()
            for r in results:
                st.write(f"### {r[1]} ({r[3]})")
                st.write(r[2])

# ---------------- SCHEDULE ----------------
def schedule_section():
    st.title("⏰ Schedule / Activities")
    task = st.text_input("Task")
    date_sel = st.date_input("Date", date.today())
    time_sel = st.time_input("Time", datetime.now().time())
    if st.button("Add Task"):
        c.execute("INSERT INTO schedule (task, date, time) VALUES (?, ?, ?)", (task, date_sel, time_sel))
        conn.commit()
        st.success("Task added!")

    c.execute("SELECT * FROM schedule ORDER BY date, time")
    tasks = c.fetchall()
    if tasks:
        df = pd.DataFrame(tasks, columns=["ID", "Task", "Date", "Time"])
        st.table(df)

# ---------------- EXAM QUESTIONS ----------------
def exam_section():
    st.title("❓ Exam Practice")
    questions = {
        "Math": [
            ("What is 2+2?", "4"),
            ("Solve: 5*6", "30")
        ],
        "Biology": [
            ("What is the powerhouse of the cell?", "Mitochondria"),
            ("What carries genetic information?", "DNA")
        ]
    }
    subject = st.selectbox("Choose subject", list(questions.keys()))
    if subject:
        q, ans = random.choice(questions[subject])
        st.write(q)
        user_ans = st.text_input("Your Answer")
        if st.button("Check Answer"):
            if user_ans.strip().lower() == ans.lower():
                st.success("Correct ✅")
            else:
                st.error(f"Wrong ❌ Correct Answer: {ans}")

# ---------------- SOCIAL MEDIA ----------------
def social_media_section():
    st.title("🌐 Social Media")
    st.write("Stay connected!")
    st.markdown("[Instagram](https://instagram.com)")
    st.markdown("[Twitter](https://twitter.com)")
    st.markdown("[Facebook](https://facebook.com)")

# ---------------- BIBLE SEARCH ----------------
def bible_section():
    st.title("📖 Bible Search")
    book = st.text_input("Book (e.g., John)")
    chapter = st.text_input("Chapter (e.g., 3)")
    verse = st.text_input("Verse (e.g., 16)")
    if st.button("Search Verse"):
        if book and chapter and verse:
            display_bible_verse(book, chapter, verse)
        else:
            st.warning("Please enter book, chapter, and verse.")

# ---------------- MAIN ----------------
menu = ["Home", "Study", "Notes", "Schedule", "Exams", "Bible", "Social Media"]
choice = st.sidebar.radio("📌 Menu", menu)

if choice == "Home":
    home_section()
elif choice == "Study":
    study_section()
elif choice == "Notes":
    notes_section()
elif choice == "Schedule":
    schedule_section()
elif choice == "Exams":
    exam_section()
elif choice == "Bible":
    bible_section()
elif choice == "Social Media":
    social_media_section()



