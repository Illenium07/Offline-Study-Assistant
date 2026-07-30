# Study Assistant Agent

A fully offline study assistant built with Python and Streamlit. It summarizes lecture
notes, generates quiz questions, and builds a revision schedule — no API key or internet
connection required.

## Architecture

```
User (Streamlit UI)
      |
      v
Orchestrator (keyword-based router)
      |  -- checks the request text for keywords like
      |     "summarize", "quiz", "plan"
      v
Functions: summarize() | build_plan() | generate_quiz()
      |
      v
Task modules: summarizer.py, planner.py, quiz.py
      |
      v
Storage (SQLite: notes, schedule, quizzes, quiz_attempts)
```

The orchestrator does not use any external AI model or tool-calling. It reads the
user's request, matches it against simple keyword rules (`_looks_like_summary`,
`_looks_like_quiz`, `_looks_like_plan`), and routes it to the matching function.
This keeps the whole app runnable offline with zero API cost.

## What it does

- Summarizes lecture notes into short bullet points and key terms
- Generates a mixed quiz (fill-in-the-blank, true/false, multiple choice,
  short answer) from a saved summary
- Builds a revision schedule spaced out before an exam date
- Stores notes, quizzes, and schedules locally in SQLite

## Project structure

- `app.py` - Streamlit user interface (Agent, Notes, Quiz, Schedule, History tabs)
- `orchestrator.py` - Routes free-text requests to the right feature by keyword
- `summarizer.py` - Offline extractive summarizer (English and German stopwords)
- `quiz.py` - Offline quiz generator (cloze, true/false, multiple choice, short answer)
- `planner.py` - Builds a spaced revision schedule before an exam
- `storage.py` - SQLite storage layer for notes, schedule, and quizzes
- `llm_client.py` - Optional AI client stub, not used in offline mode

## How to run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## How to use

### Save a note
Open the **Notes** tab, enter course, topic, and paste your notes, then click
**Summarize and Save**.

### Make a quiz
Open the **Quiz** tab, enter the same course and topic used for a saved note,
then click **Generate Quiz**.

### Build a revision plan
Open the **Schedule** tab, enter course, exam date, and topics (one per line,
optionally `topic, difficulty`), then click **Build Plan**.

### Use the Agent tab
Type a free-text request such as:
- `summarize: paste your notes here`
- `quiz me on physics`
- `make a plan for 2026-08-10`

The orchestrator detects the keyword and calls the matching feature directly.

## Notes

This app is fully offline and does not require any API key. `llm_client.py` is
included as a placeholder for a future upgrade path if a live LLM is added later,
but it is not called anywhere in the current code.
