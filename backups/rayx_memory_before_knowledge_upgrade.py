
import json
import re
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parent

SOURCE_FILES = [
    ROOT / "dataset.txt",
    ROOT / "extra_data.txt",
    ROOT / "approved_examples.txt",
]

MEMORY_FILE = ROOT / "knowledge_memory.json"


def normalize(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def read_conversations():
    records = []
    seen = set()

    for path in SOURCE_FILES:
        if not path.exists():
            continue

        content = path.read_text(encoding="utf-8")

        # Each conversation ends at ### End.
        blocks = re.split(r"###\s*End\b", content, flags=re.IGNORECASE)

        for block in blocks:
            user_match = re.search(
                r"###\s*User:\s*(.*?)(?=\n\s*###\s*RayX:)",
                block,
                flags=re.IGNORECASE | re.DOTALL,
            )

            answer_match = re.search(
                r"###\s*RayX:\s*(.*)",
                block,
                flags=re.IGNORECASE | re.DOTALL,
            )

            if not user_match or not answer_match:
                continue

            question = user_match.group(1).strip()
            answer = answer_match.group(1).strip()

            # Prevent another conversation or marker leaking into an answer.
            answer = re.split(
                r"\n\s*###\s*(?:User|RayX|End)\b",
                answer,
                maxsplit=1,
                flags=re.IGNORECASE,
            )[0].strip()

            if not question or not answer:
                continue

            key = (normalize(question), normalize(answer))

            if key in seen:
                continue

            seen.add(key)

            records.append({
                "question": question,
                "answer": answer,
                "source": path.name,
            })

    return records


def rebuild_memory():
    records = read_conversations()

    MEMORY_FILE.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Memory rebuilt successfully: {len(records)} examples")
    print(f"Saved to: {MEMORY_FILE}")


def load_memory():
    if not MEMORY_FILE.exists():
        rebuild_memory()

    try:
        return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        print("Memory file is invalid. Rebuilding it...")
        rebuild_memory()
        return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))


def find_answer(question, threshold=0.88):
    query = normalize(question)

    if not query:
        return None

    records = load_memory()
    best_record = None
    best_score = 0.0

    for record in records:
        saved_question = normalize(record.get("question", ""))

        if not saved_question:
            continue

        score = SequenceMatcher(
            None, query, saved_question
        ).ratio()

        if score > best_score:
            best_score = score
            best_record = record

    if best_record and best_score >= threshold:
        return {
            "answer": best_record["answer"],
            "score": round(best_score, 3),
            "source": best_record.get("source", "memory"),
        }

    return None


if __name__ == "__main__":
    rebuild_memory()
