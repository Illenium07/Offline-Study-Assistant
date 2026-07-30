import re

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


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [p.strip() for p in parts if p.strip()]


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().strip("-• ")


def _is_usable_sentence(sentence: str) -> bool:
    words = sentence.split()
    return len(words) >= 3


def _sentence_score(sentence: str, freq: dict) -> int:
    score = 0
    for w in re.findall(r"[A-Za-zÀ-ÿ0-9_]+", sentence.lower()):
        score += freq.get(w, 0)
    return score


def summarize(raw_text: str, course: str, topic: str) -> str:
    sentences = [_clean_text(s) for s in _split_sentences(raw_text)]
    sentences = [s for s in sentences if _is_usable_sentence(s)]

    if not sentences:
        return f"# {course} - {topic}\n\nNo text provided."

    words = re.findall(r"[A-Za-zÀ-ÿ0-9_]+", raw_text.lower())
    freq = {}
    for w in words:
        if w in STOPWORDS or len(w) < 3:
            continue
        freq[w] = freq.get(w, 0) + 1

    scored = sorted(((_sentence_score(s, freq), s) for s in sentences), key=lambda x: x[0], reverse=True)

    top_sentences = []
    seen = set()
    for _, sentence in scored:
        key = sentence.lower()
        if key in seen:
            continue
        seen.add(key)
        top_sentences.append(sentence)
        if len(top_sentences) == 5:
            break

    key_terms = [term for term, _ in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]]

    summary_lines = [
        f"# {course} - {topic}",
        "",
        "## Summary",
    ]

    if top_sentences:
        summary_lines.extend([f"- {s}" for s in top_sentences])
    else:
        summary_lines.append("- No strong summary could be extracted.")

    summary_lines.extend([
        "",
        "## Key terms",
    ])

    if key_terms:
        summary_lines.extend([f"- {term}" for term in key_terms])
    else:
        summary_lines.append("- No key terms found.")

    return "\n".join(summary_lines)