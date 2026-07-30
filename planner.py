from datetime import datetime, timedelta
import storage


def build_plan(course: str, topics: list[dict], exam_date: str):
    exam_dt = datetime.fromisoformat(exam_date)
    today = datetime.now()
    days_available = max((exam_dt - today).days, 0)

    entries = []
    if not topics:
        return [{"warning": "No topics provided."}]

    step = max(days_available // max(len(topics), 1), 1) if days_available else 1

    for i, t in enumerate(topics):
        topic_name = t.get("topic", f"Topic {i+1}")
        difficulty = t.get("difficulty", "medium")
        review_date = (today + timedelta(days=min(i * step + 1, max(days_available - 1, 0)))).date().isoformat()
        storage.add_schedule_entry(course, topic_name, review_date, difficulty)
        entries.append({"topic": topic_name, "date": review_date, "difficulty": difficulty})

    return entries


def reprioritize_from_weak_topics(course: str):
    weak = storage.get_weak_topics(course)
    today = datetime.now()
    added = []
    for topic in weak:
        review_date = (today + timedelta(days=1)).date().isoformat()
        storage.add_schedule_entry(course, topic, review_date, difficulty="hard")
        added.append({"topic": topic, "date": review_date})
    return added