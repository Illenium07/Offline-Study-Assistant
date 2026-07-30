import re
import random

STOPWORDS = {
    "the", "and", "a", "an", "to", "of", "in", "is", "it", "that", "this",
    "for", "with", "as", "on", "by", "at", "from", "or", "be", "are", "was",
    "were", "been", "has", "have", "had", "but", "not", "they", "their", "its",
    "these", "those", "here", "there", "case", "cases", "include", "includes",
    "show", "shows", "study", "studies", "test", "tests", "using", "use", "used",
    "involves", "involve", "about", "into", "over", "under", "within", "rather",
    "two", "one", "more", "most", "less", "many", "much",
    "die", "der", "das", "und", "ist", "ein", "eine", "einer", "eines", "einem",
    "einen", "mit", "auf", "von", "zu", "im", "am", "an", "als", "auch", "sich",
    "sind", "war", "waren", "wird", "werden", "wurde", "wurden", "aber", "oder",
    "nicht", "nur", "so", "wie", "was", "wer", "wo", "wann", "wenn", "dass",
    "diese", "dieser", "dieses", "ich", "sie", "wir", "ihnen", "ihr", "ihre",
    "über", "für", "kann", "können", "muss", "müssen", "hat", "haben"
}


def _extract_sentences(summary_text: str) -> list[str]:
    sentences = []
    for raw in summary_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("-"):
            line = line.lstrip("- ").strip()
        if line and len(line.split()) >= 3:
            sentences.append(line)
    return sentences


def _word_freq(summary_text: str) -> dict:
    words = re.findall(r"[A-Za-zÀ-ÿ0-9_]+", summary_text.lower())
    freq = {}
    for w in words:
        if w in STOPWORDS or len(w) < 4:
            continue
        freq[w] = freq.get(w, 0) + 1
    return freq


def _candidate_words(sentence: str, freq: dict, exclude: set) -> list[str]:
    candidates = re.findall(r"[A-Za-zÀ-ÿ0-9_]+", sentence)
    scored = []
    for w in candidates:
        lw = w.lower()
        if lw in STOPWORDS or len(w) < 4 or lw in exclude:
            continue
        scored.append((freq.get(lw, 0), w))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [w for _, w in scored]


def _make_cloze(sentence: str, word: str) -> str:
    pattern = re.compile(re.escape(word))
    return pattern.sub("_____", sentence, count=1)


def _make_fill_blank(sentence: str, word: str, topic: str, level: str) -> dict:
    return {
        "question": f"Fill in the blank ({topic}): {_make_cloze(sentence, word)}",
        "answer": word,
        "difficulty": level,
        "type": "fill_blank"
    }


def _make_true_false(sentence: str, word: str, freq: dict, topic: str, level: str) -> dict:
    other_words = [w for w in freq.keys() if w != word.lower()]
    is_true = random.random() < 0.5 or not other_words
    if is_true:
        statement = sentence
        answer = "True"
    else:
        fake_word = random.choice(other_words)
        statement = re.sub(re.escape(word), fake_word, sentence, count=1, flags=re.IGNORECASE)
        answer = "False"
    return {
        "question": f"True or False ({topic}): {statement}",
        "answer": answer,
        "difficulty": level,
        "type": "true_false"
    }


def _make_multiple_choice(sentence: str, word: str, freq: dict, topic: str, level: str) -> dict:
    distractors = [w for w in freq.keys() if w != word.lower()]
    random.shuffle(distractors)
    options = [word] + distractors[:3]
    random.shuffle(options)
    return {
        "question": f"Choose the correct word ({topic}): {_make_cloze(sentence, word)}",
        "options": options,
        "answer": word,
        "difficulty": level,
        "type": "multiple_choice"
    }


def _make_short_answer(sentence: str, word: str, topic: str, level: str) -> dict:
    return {
        "question": f"What does the note say about \"{word}\" in {topic}?",
        "answer": sentence,
        "difficulty": level,
        "type": "short_answer"
    }


def _build_question(builder_id: int, sentence: str, word: str, freq: dict, topic: str, level: str) -> dict:
    if builder_id == 0:
        return _make_fill_blank(sentence, word, topic, level)
    if builder_id == 1:
        return _make_true_false(sentence, word, freq, topic, level)
    if builder_id == 2:
        if len(freq) < 4:
            return _make_fill_blank(sentence, word, topic, level)
        return _make_multiple_choice(sentence, word, freq, topic, level)
    return _make_short_answer(sentence, word, topic, level)


def generate_quiz(summary_text: str, topic: str, num_questions: int = 5, difficulty: str = "mixed") -> list[dict]:
    sentences = _extract_sentences(summary_text)
    freq = _word_freq(summary_text)

    questions = []
    used_words = set()
    used_sentences = set()
    builder_id = 0

    if sentences:
        for round_idx in range(3):
            for idx, sentence in enumerate(sentences):
                if len(questions) >= num_questions:
                    break
                sentence_key = (idx, round_idx)
                if sentence_key in used_sentences:
                    continue

                candidates = _candidate_words(sentence, freq, used_words)
                if not candidates:
                    continue
                word = candidates[0]
                used_words.add(word.lower())
                used_sentences.add(sentence_key)

                level = difficulty if difficulty != "mixed" else (["easy", "medium", "hard"][len(questions) % 3])
                q = _build_question(builder_id % 4, sentence, word, freq, topic, level)
                builder_id += 1
                questions.append(q)

            if len(questions) >= num_questions:
                break

    if not questions:
        questions.append({
            "question": f"What is the main topic of these notes on {topic}?",
            "answer": topic,
            "difficulty": "easy",
            "type": "short_answer"
        })

    return questions[:num_questions]


def score_attempt(questions: list[dict], user_answers: list[str]) -> dict:
    correct = 0
    weak_topics = []
    for q, user_ans in zip(questions, user_answers):
        expected = str(q.get("answer", "")).strip().lower()
        given = str(user_ans).strip().lower()
        q_type = q.get("type", "short_answer")

        if q_type == "short_answer":
            is_correct = expected in given or given in expected
        else:
            is_correct = expected == given

        if expected and is_correct:
            correct += 1
        else:
            weak_topics.append(q.get("question", "")[:60])

    total = len(questions)
    score = correct / total if total else 0
    return {"score": score, "correct": correct, "total": total, "weak_topics": weak_topics}