# Study Assistant Agent

An AI agent that organizes coursework, summarizes notes, builds a spaced-repetition
revision schedule, and generates quiz questions -- deciding what to do next itself
via Claude tool-calling, rather than following a fixed script.

## Architecture

```
User (Streamlit UI)
      |
      v
Orchestrator (agent loop)
      |  -- uses Claude tool-calling to pick the next action
      v
Tools: summarize_notes | build_revision_plan | generate_quiz | check_progress
      |
      v
Task modules (modules/summarizer.py, planner.py, quiz.py)
      |
      v
Storage (SQLite: notes, schedule, quizzes, quiz_attempts)
```

The key difference from a fixed pipeline: the orchestrator doesn't hardcode
"summarize -> then plan -> then quiz". Claude reads the user's request and
decides which tool(s) to call, in what order, and can chain them (e.g.
summarize notes, then immediately generate a quiz from that summary) in a
single request.

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here
streamlit run app.py
```

## Example requests to try in the Agent tab

- "Here are my notes on [topic]: [paste text] -- summarize them for [course]."
- "I have an exam on 2026-08-15 for Netzwerktechnik, topics: OSI model (hard),
  subnetting (medium), routing protocols (easy). Build me a revision plan."
- "Quiz me on [topic] with 5 questions."
- "What should I study next?"

## Extending this

- **Grading**: `quiz.score_attempt` does simple string matching -- swap in an
  LLM-graded rubric for short-answer questions.
- **Ingestion**: currently notes are pasted as text; add a PDF/slide upload
  path (`pdf` skill / PyPDF2) to feed in real lecture material.
- **Spaced repetition**: `planner.py` uses fixed intervals by difficulty --
  a real SM-2 algorithm would adapt intervals based on quiz performance over time.
- **Multi-course dashboard**: the schedule/history tabs currently show one
  course at a time; a combined view across courses would be a natural next step.
