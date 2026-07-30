"""
Offline orchestrator for the study assistant.
It uses simple keyword rules instead of a live AI model.
"""

import json
import re
import summarizer
import planner
import quiz
import storage


def _extract_course(text: str) -> str:
    m = re.search(r"(?:for|course)\s+([A-Za-z0-9_\- ]{2,40})", text, re.IGNORECASE)
    return m.group(1).strip() if m else "General"


def _extract_topic(text: str) -> str:
    m = re.search(r"(?:on|about)\s+([A-Za-z0-9_\- ]{2,60})", text, re.IGNORECASE)
    return m.group(1).strip() if m else "General topic"


def _extract_text_after_colon(text: str) -> str:
    parts = text.split(":", 1)
    return parts[1].strip() if len(parts) > 1 else text.strip()


def _looks_like_plan(text: str) -> bool:
    return any(k in text.lower() for k in ["plan", "schedule", "revision", "study plan"])


def _looks_like_quiz(text: str) -> bool:
    return any(k in text.lower() for k in ["quiz", "question", "test me", "flashcard"])


def _looks_like_summary(text: str) -> bool:
    return any(k in text.lower() for k in ["summarize", "summary", "note", "notes"])


def run_agent(user_request: str, max_turns: int = 1) -> str:
    text = user_request.strip()
    course = _extract_course(text)
    topic = _extract_topic(text)

    if _looks_like_quiz(text):
        notes = storage.get_notes(course=course, topic=topic)
        if notes and notes[-1].get("summary"):
            summary_text = notes[-1]["summary"]
        else:
            summary_text = f"# {course} - {topic}\n\nNo saved summary found."
        questions = quiz.generate_quiz(summary_text, topic, num_questions=5)
        quiz_id = storage.save_quiz(course, topic, questions)
        return json.dumps({"quiz_id": quiz_id, "questions": questions}, indent=2)

    if _looks_like_plan(text):
        exam_date_match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", text)
        exam_date = exam_date_match.group(0) if exam_date_match else None
        if not exam_date:
            return "Please include an exam date in YYYY-MM-DD format."

        topics = [{"topic": topic, "difficulty": "medium"}]
        entries = planner.build_plan(course, topics, exam_date)
        return json.dumps({"schedule": entries}, indent=2)

    if _looks_like_summary(text):
        raw_text = _extract_text_after_colon(text)
        summary = summarizer.summarize(raw_text, course, topic)
        note_id = storage.save_note(course, topic, raw_text, summary)
        return summary + f"\n\nSaved as note #{note_id}."

    return (
        "I can help with:\n"
        "- summarize notes\n"
        "- build a revision plan\n"
        "- generate quiz questions\n\n"
        "Try: 'summarize: your notes here' or 'quiz me on physics' or 'make a plan for 2026-08-10'"
    )