
from pathlib import Path
from collections import Counter
import re
import json

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "cleaned_data"
REPORT_DIR = ROOT / "reports"

TRAIN = DATA_DIR / "train_clean.txt"
VALID = DATA_DIR / "validation_clean.txt"

REPORT_DIR.mkdir(exist_ok=True)


def parse_dataset(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    text = path.read_text(encoding="utf-8")

    pattern = re.compile(
        r"(?:###\s*)?User\s*:\s*(.*?)"
        r"\s*(?:###\s*)?RayX\s*:\s*(.*?)"
        r"(?:\s*(?:###\s*)?End\b|(?=\n\s*(?:###\s*)?User\s*:)|\Z)",
        re.IGNORECASE | re.DOTALL
    )

    return [
        {
            "question": m.group(1).strip(),
            "answer": m.group(2).strip()
        }
        for m in pattern.finditer(text)
    ]


def normalize(text):
    text = text.casefold()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s]", "", text)
    return text.strip()


def inspect_records(records):
    issues = []
    answer_counts = Counter()

    for index, record in enumerate(records, start=1):
        question = record["question"]
        answer = record["answer"]

        if len(question.split()) < 2:
            issues.append({
                "record": index,
                "type": "Very short question",
                "question": question
            })

        if len(answer.split()) < 4:
            issues.append({
                "record": index,
                "type": "Very short answer",
                "question": question
            })

        if len(answer.split()) > 250:
            issues.append({
                "record": index,
                "type": "Very long answer",
                "question": question
            })

        if re.search(r"(.)\1{5,}", answer):
            issues.append({
                "record": index,
                "type": "Suspicious repeated characters",
                "question": question
            })

        answer_counts[normalize(answer)] += 1

    repeated_answers = [
        answer for answer, count in answer_counts.items()
        if answer and count > 1
    ]

    return {
        "total_examples": len(records),
        "issues": issues,
        "repeated_answers": repeated_answers
    }


def main():
    train = parse_dataset(TRAIN)
    validation = parse_dataset(VALID)

    train_report = inspect_records(train)
    validation_report = inspect_records(validation)

    train_questions = {
        normalize(r["question"]) for r in train
    }

    validation_questions = {
        normalize(r["question"]) for r in validation
    }

    overlap = sorted(train_questions & validation_questions)

    report = {
        "training": train_report,
        "validation": validation_report,
        "data_leakage": {
            "overlap_count": len(overlap),
            "overlapping_questions": overlap
        },
        "note": (
            "Heuristic checks only. This report does not prove "
            "semantic correctness or answer quality."
        ),
        "model_checkpoint_modified": False,
        "source_files_modified": False
    }

    output = REPORT_DIR / "dataset_quality_report.json"

    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("\nReport saved:", output)


if __name__ == "__main__":
    main()
