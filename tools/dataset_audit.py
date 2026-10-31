
from pathlib import Path
from collections import Counter
import re
import json
import hashlib

ROOT = Path(__file__).resolve().parent.parent

TRAIN_FILE = ROOT / "backups/train_before_self_improvement.txt"
VALID_FILE = ROOT / "backups/validation_before_self_improvement.txt"

REPORT_DIR = ROOT / "reports"
REPORT_DIR.mkdir(exist_ok=True)

def normalize(text):
    text = text.casefold().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s]", "", text)
    return text

def parse_dataset(path):
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    content = path.read_text(encoding="utf-8")
    records = []

    # Supports both ### User: and User: formats.
    pattern = re.compile(
        r"(?:###\s*)?User\s*:\s*(.*?)"
        r"(?:\n\s*(?:###\s*)?RayX\s*:\s*)(.*?)"
        r"(?:\n\s*(?:###\s*)?End\b|(?=\n\s*(?:###\s*)?User\s*:)|\Z)",
        re.IGNORECASE | re.DOTALL
    )

    for match in pattern.finditer(content):
        question = match.group(1).strip()
        answer = match.group(2).strip()

        if question or answer:
            records.append({
                "question": question,
                "answer": answer
            })

    return records

def audit_records(records):
    question_counts = Counter(
        normalize(r["question"]) for r in records
        if r["question"]
    )

    duplicate_questions = [
        question for question, count in question_counts.items()
        if count > 1
    ]

    missing_questions = [
        i + 1 for i, r in enumerate(records)
        if not r["question"]
    ]

    missing_answers = [
        i + 1 for i, r in enumerate(records)
        if not r["answer"]
    ]

    languages = Counter()

    for record in records:
        text = record["question"] + " " + record["answer"]

        if re.search(r"[\u0900-\u097F]", text):
            languages["Hindi/Hinglish"] += 1
        else:
            languages["English/Other"] += 1

    return {
        "total_examples": len(records),
        "unique_questions": len(question_counts),
        "duplicate_questions": duplicate_questions,
        "missing_questions": missing_questions,
        "missing_answers": missing_answers,
        "languages": dict(languages)
    }

def main():
    print("\n========== RAYX DATASET AUDIT ==========\n")

    train = parse_dataset(TRAIN_FILE)
    validation = parse_dataset(VALID_FILE)

    train_report = audit_records(train)
    validation_report = audit_records(validation)

    train_questions = {
        normalize(r["question"])
        for r in train if r["question"]
    }

    validation_questions = {
        normalize(r["question"])
        for r in validation if r["question"]
    }

    overlap = sorted(train_questions & validation_questions)

    report = {
        "training": train_report,
        "validation": validation_report,
        "train_validation_overlap": overlap,
        "overlap_count": len(overlap),
        "checkpoint_modified": False,
        "source_files_modified": False
    }

    print("TRAINING DATA")
    print(json.dumps(train_report, indent=2, ensure_ascii=False))

    print("\nVALIDATION DATA")
    print(json.dumps(validation_report, indent=2, ensure_ascii=False))

    print("\nTRAIN / VALIDATION OVERLAP")
    print("Overlapping questions:", len(overlap))

    for question in overlap:
        print("-", question)

    output = REPORT_DIR / "dataset_audit.json"
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print("\nAudit saved:", output)
    print("Original datasets and model checkpoint were not modified.")
    print("\n========== AUDIT COMPLETE ==========\n")

if __name__ == "__main__":
    main()
