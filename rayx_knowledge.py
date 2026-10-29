
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KNOWLEDGE_DIR = ROOT / "knowledge"
KNOWLEDGE_FILE = KNOWLEDGE_DIR / "knowledge.jsonl"


def normalize(text):
    text = unicodedata.normalize("NFKC", text).casefold()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def tokens(text):
    return set(normalize(text).split())


def load_knowledge():
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)

    if not KNOWLEDGE_FILE.exists():
        KNOWLEDGE_FILE.write_text("", encoding="utf-8")

    records = []

    with KNOWLEDGE_FILE.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                print(f"Skipping invalid JSON on line {line_number}")
                continue

            if not isinstance(item, dict):
                continue

            question = str(item.get("question", "")).strip()
            answer = str(item.get("answer", "")).strip()

            if not question or not answer:
                continue

            records.append({
                "question": question,
                "answer": answer,
                "subject": str(item.get("subject", "General")),
                "language": str(item.get("language", "unknown")),
                "source": str(item.get("source", "unspecified")),
                "verified": item.get("verified", False) is True,
                "keywords": item.get("keywords", []),
            })

    return records


def search_knowledge(question, min_score=0.45):
    query = normalize(question)
    query_tokens = tokens(question)

    if not query or not query_tokens:
        return None

    records = load_knowledge()
    best_item = None
    best_score = 0.0

    for item in records:
        # Include answer text so document chunks can be found by topic terms.
        searchable_text = " ".join([
            item["question"],
            item["answer"],
            item["subject"],
            " ".join(map(str, item.get("keywords", []))),
        ])

        record_tokens = tokens(searchable_text)

        if not record_tokens:
            continue

        overlap = len(query_tokens & record_tokens)
        coverage = overlap / len(query_tokens)
        precision = overlap / len(record_tokens)

        # Give greater weight to matching the user's query terms.
        score = (0.75 * coverage) + (0.25 * precision)

        if query == normalize(item["question"]):
            score = 1.0

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
    for question in [
        "What is photosynthesis?",
        "प्रकाश संश्लेषण क्या है?",
        "Explain a Python function",
    ]:
        result = search_knowledge(question)

        print(f"\nQuestion: {question}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
