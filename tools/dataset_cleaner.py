
from pathlib import Path
from collections import OrderedDict
import re
import json

ROOT = Path(__file__).resolve().parent.parent

TRAIN_FILE = ROOT / "backups/train_before_self_improvement.txt"
VALID_FILE = ROOT / "backups/validation_before_self_improvement.txt"

OUTPUT_DIR = ROOT / "cleaned_data"
OUTPUT_DIR.mkdir(exist_ok=True)

def normalize(text):
    text = text.casefold().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s]", "", text)
    return text

def parse_dataset(path):
    content = path.read_text(encoding="utf-8")

    pattern = re.compile(
        r"(?:###\s*)?User\s*:\s*(.*?)"
        r"\s*(?:###\s*)?RayX\s*:\s*(.*?)"
        r"(?:\s*(?:###\s*)?End\b|(?=\n\s*(?:###\s*)?User\s*:)|\Z)",
        re.IGNORECASE | re.DOTALL
    )

    records = []

    for match in pattern.finditer(content):
        question = match.group(1).strip()
        answer = match.group(2).strip()

        if question and answer:
            records.append({
                "question": question,
                "answer": answer
            })

    return records

def clean_records(records):
    cleaned = OrderedDict()
    removed = []

    for record in records:
        question = record["question"]
        answer = record["answer"]

        key = normalize(question)

        if not key or not answer.strip():
            removed.append({
                "question": question,
                "reason": "Empty question or answer"
            })
            continue

        if key in cleaned:
            removed.append({
                "question": question,
                "reason": "Duplicate question"
            })
            continue

        cleaned[key] = {
            "question": question,
            "answer": answer
        }

    return list(cleaned.values()), removed

def save_dataset(records, path):
    blocks = []

    for record in records:
        blocks.append(
            f"### User: {record['question']}\n"
            f"### RayX: {record['answer']}\n"
            f"### End"
        )

    path.write_text(
        "\n\n".join(blocks) + "\n",
        encoding="utf-8"
    )

def main():
    if not TRAIN_FILE.exists() or not VALID_FILE.exists():
        raise FileNotFoundError("Backup dataset files not found.")

    train = parse_dataset(TRAIN_FILE)
    validation = parse_dataset(VALID_FILE)

    clean_train, removed_train = clean_records(train)
    clean_validation, removed_validation = clean_records(validation)

    train_keys = {
        normalize(r["question"]) for r in clean_train
    }

    # Keep validation separate; do not silently delete overlap.
    overlap = [
        r["question"] for r in clean_validation
        if normalize(r["question"]) in train_keys
    ]

    save_dataset(
        clean_train,
        OUTPUT_DIR / "train_clean.txt"
    )

    save_dataset(
        clean_validation,
        OUTPUT_DIR / "validation_clean.txt"
    )

    report = {
        "training": {
            "original": len(train),
            "cleaned": len(clean_train),
            "removed": removed_train
        },
        "validation": {
            "original": len(validation),
            "cleaned": len(clean_validation),
            "removed": removed_validation
        },
        "train_validation_overlap": overlap,
        "checkpoint_modified": False,
        "backup_files_modified": False
    }

    (OUTPUT_DIR / "cleaning_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("\nCleaned files saved in:", OUTPUT_DIR)
    print("Original backups and checkpoint remain untouched.")

if __name__ == "__main__":
    main()
