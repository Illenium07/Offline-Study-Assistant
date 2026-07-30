"""
Streamlit front-end for the offline study assistant.
Run with: streamlit run app.py
"""

import streamlit as st
import storage
from orchestrator import run_agent
from summarizer import summarize
from planner import build_plan
from quiz import generate_quiz

storage.init_db()

st.set_page_config(page_title="Study Assistant Agent", layout="wide")
st.title("Study Assistant Agent")
st.caption("Organizes notes, plans revision, and quizzes you.")

chat_tab, notes_tab, quiz_tab, schedule_tab, history_tab = st.tabs([
    "Agent", "Notes", "Quiz", "Schedule", "History"
])

with chat_tab:
    st.write("Use keywords like: summarize, quiz, plan.")
    user_input = st.text_area("Your request", height=120)
    if st.button("Send", type="primary"):
        if user_input.strip():
            with st.spinner("Working..."):
                result = run_agent(user_input)
            st.markdown("### Response")
            st.code(result)
        else:
            st.warning("Enter a request first.")

with notes_tab:
    st.subheader("Save a note")
    note_course = st.text_input("Course", key="note_course")
    note_topic = st.text_input("Topic", key="note_topic")
    raw_text = st.text_area("Paste notes here", height=180, key="note_text")
    if st.button("Summarize and Save", type="secondary"):
        if note_course and note_topic and raw_text.strip():
            summary = summarize(raw_text, note_course, note_topic)
            note_id = storage.save_note(note_course, note_topic, raw_text, summary)
            st.success(f"Saved note #{note_id}")
            st.markdown(summary)
        else:
            st.warning("Fill in course, topic, and notes.")

with quiz_tab:
    st.subheader("Make a quiz from a saved note")
    quiz_course = st.text_input("Course", key="quiz_course")
    quiz_topic = st.text_input("Topic", key="quiz_topic")
    num_questions = st.number_input("Number of questions", min_value=1, max_value=20, value=5, step=1)

    if st.button("Generate Quiz", type="secondary"):
        if quiz_course and quiz_topic:
            notes = storage.get_notes(quiz_course, quiz_topic)
            if notes and notes[-1].get("summary"):
                summary_text = notes[-1]["summary"]
                questions = generate_quiz(summary_text, quiz_topic, int(num_questions))
                quiz_id = storage.save_quiz(quiz_course, quiz_topic, questions)
                st.success(f"Quiz saved as #{quiz_id}")
                st.json({"quiz_id": quiz_id, "questions": questions})
            else:
                st.error("No saved summary found for that exact course and topic.")
        else:
            st.warning("Enter course and topic.")

with schedule_tab:
    st.subheader("Create a revision plan")
    plan_course = st.text_input("Course", key="plan_course")
    exam_date = st.text_input("Exam date (YYYY-MM-DD)", key="plan_exam")
    topics_text = st.text_area("Topics (one per line, optional: topic,difficulty)", height=120)

    if st.button("Build Plan", type="secondary"):
        if plan_course and exam_date.strip() and topics_text.strip():
            topics = []
            for line in topics_text.splitlines():
                line = line.strip()
                if not line:
                    continue
                parts = [p.strip() for p in line.split(",")]
                topic_name = parts[0]
                difficulty = parts[1] if len(parts) > 1 and parts[1] else "medium"
                topics.append({"topic": topic_name, "difficulty": difficulty})
            entries = build_plan(plan_course, topics, exam_date.strip())
            st.success("Plan created")
            st.json(entries)
        else:
            st.warning("Fill in course, exam date, and topics.")

with history_tab:
    st.subheader("Saved notes")
    course_filter = st.text_input("Filter by course (optional)", key="history_course")
    notes = storage.get_notes(course_filter or None)
    if notes:
        for n in notes:
            st.markdown(f"### {n['course']} - {n['topic']}")
            st.write(n.get("summary", "No summary"))
            st.caption(n["created_at"])
    else:
        st.info("No saved notes yet.")

    st.subheader("Upcoming schedule")
    entries = storage.get_upcoming_schedule(course_filter or None)
    if entries:
        st.json(entries)
    else:
        st.info("No scheduled reviews yet.")