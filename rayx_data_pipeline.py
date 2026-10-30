
"""RayX Model 2: safe local training-data collector.

Does not call external APIs, train the model, or modify checkpoints.
Only calculator answers and explicitly verified knowledge answers
are eligible for the training dataset.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from rayx_hybrid import answer_question

ROOT = Path(__file__).resolve().parent
DATASET_FILE = ROOT / "rayx_training_data.jsonl"
REPORT_FILE = ROOT / "rayx_data_pipeline_report.json"


def make_hash(question, answer):
    value = question.strip().casefold() + "\n" + answer.strip().casefold()
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_existing_hashes():
    hashes = set()

    if not DATASET_FILE.exists():
        return hashes

    with DATASET_FILE.open("r", encoding="utf-8") as file:
        for line in file:
            try:
                record = json.loads(line)
                hashes.add(record["hash"])
            except (json.JSONDecodeError, KeyError, TypeError):
                continue

    return hashes


def collect_example(question):
    result = answer_question(question)

    answer = str(result.get("answer", "")).strip()
    source = result.get("source", "unknown")
    verified = result.get("verified") is True

    # Do not train on greetings, memory, neural guesses, or error messages.
    eligible = (
        bool(question.strip())
        and bool(answer)
        and (
            source == "calculator"
            or (source == "knowledge_base" and verified)
        )
    )

    if not eligible:
        return {
            "question": question,
            "source": source,
            "status": "skipped_unverified",
        }

    digest = make_hash(question, answer)
    existing = read_existing_hashes()

    if digest in existing:
        return {
            "question": question,
            "source": source,
            "status": "skipped_duplicate",
        }

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "question": question.strip(),
        "answer": answer,
        "source": source,
        "verified": True,
        "hash": digest,
    }

    with DATASET_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")

    return {
        "question": question,
        "source": source,
        "status": "added",
    }


def main():
    # Safe starter examples. Knowledge answers are added only if the
    # local knowledge base explicitly marks them verified.
    questions = [
        "2+2",
        "10*5",
        "What is Python?",
        "What is photosynthesis?",
        "Explain quantum mechanics",
        "hey",
    ]

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dataset": DATASET_FILE.name,
        "checkpoint_modified": False,
        "results": [],
    }

    for question in questions:
        try:
            result = collect_example(question)
        except Exception as error:
            result = {
                "question": question,
                "status": "error",
                "error_type": type(error).__name__,
            }

        report["results"].append(result)
        print(f"{question!r}: {result['status']}")

    REPORT_FILE.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    added = sum(
        item["status"] == "added"
        for item in report["results"]
    )

    print(f"\nNew examples added: {added}")
    print(f"Dataset: {DATASET_FILE}")
    print(f"Report: {REPORT_FILE}")
    print("Model checkpoint was not modified.")


if __name__ == "__main__":
    main()
