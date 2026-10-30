
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KNOWLEDGE_DIR = ROOT / "knowledge"
KNOWLEDGE_FILE = KNOWLEDGE_DIR / "knowledge.jsonl"

STOP_WORDS = {
    "what", "is", "a", "an", "the", "about", "explain",
    "tell", "me", "please", "define", "meaning", "of",
    "kya", "hai", "he", "ka", "ki", "ke", "ko", "batao",
    "samjhao", "mujhe", "aur", "mein", "h", "ho",
}

ALIASES = {
    "py": "python",
    "pythn": "python",
    "pythin": "python",
    "photosynthsis": "photosynthesis",
    "photosynthesis": "photosynthesis",
}


def normalize(text):
    text = unicodedata.normalize("NFKC", str(text)).casefold()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    words = text.split()
    words = [ALIASES.get(word, word) for word in words]
    return " ".join(words)


def meaningful_tokens(text):
    return {
        word for word in normalize(text).split()
        if word not in STOP_WORDS and len(word) > 1
    }


def load_knowledge():
    if not KNOWLEDGE_FILE.exists():
        return []

    records = []

    with KNOWLEDGE_FILE.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            if not line.strip():
                continue

            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                print(f"Warning: invalid JSON at line {line_number}")
                continue

            if not isinstance(item, dict):
                continue

            question = str(item.get("question", "")).strip()
            answer = str(item.get("answer", "")).strip()

            if not question or not answer:
                continue

            keywords = item.get("keywords", [])
            if not isinstance(keywords, list):
                keywords = []

            records.append({
                "question": question,
                "answer": answer,
                "subject": str(item.get("subject", "General")),
                "language": str(item.get("language", "unknown")),
                "source": str(item.get("source", "unspecified")),
                "verified": item.get("verified") is True,
                "keywords": [str(word) for word in keywords],
            })

    return records


def search_knowledge(question, min_score=0.70):
    query = normalize(question)
    query_tokens = meaningful_tokens(question)

    if not query or not query_tokens:
        return None

    records = load_knowledge()
    best_item = None
    best_score = 0.0

    for item in records:
        title = normalize(item["question"])
        title_tokens = meaningful_tokens(item["question"])
        keyword_tokens = meaningful_tokens(
            " ".join(item["keywords"])
        )

        # Exact question match is the strongest signal.
        if query == title:
            score = 1.0
        else:
            searchable = title_tokens | keyword_tokens

            if not searchable:
                continue

            overlap = query_tokens & searchable
            coverage = len(overlap) / len(query_tokens)
            precision = len(overlap) / len(searchable)

            score = 0.80 * coverage + 0.20 * precision

            # Avoid answering a broad topic question with a
            # narrower subtopic answer.
            if len(query_tokens) == 1 and query_tokens != title_tokens:
                score = min(score, 0.30)

            # "What is Python?" should not match a record
            # specifically about a Python function.
            if (
                "python" in query_tokens
                and "function" in title_tokens
                and "function" not in query_tokens
            ):
                score = min(score, 0.30)

        if score > best_score:
            best_score = score
            best_item = item

    if best_item is None or best_score < min_score:
        return None

    return {
        "answer": best_item["answer"],
        "subject": best_item["subject"],
        "language": best_item["language"],
        "source": best_item["source"],
        "verified": best_item["verified"],
        "score": round(best_score, 3),
    }


if __name__ == "__main__":
    questions = [
        "what is python",
        "what is pythin",
        "what is a Python function",
        "what is photosynthesis",
        "Tell me about quantum mechanics",
    ]

    for question in questions:
        result = search_knowledge(question)
        print(f"\nQ: {question}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
