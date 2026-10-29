
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import torch

from model import RayXModel, DEFAULT_CONFIG


ROOT = Path(__file__).resolve().parent
CHECKPOINT = ROOT / "artifacts" / "rayx_model.pt"
APPROVED_FILE = ROOT / "approved_examples.txt"
PENDING_FILE = ROOT / "pending_examples.jsonl"
HISTORY_FILE = ROOT / "improvement_history.jsonl"

DEVICE = torch.device("cpu")
MAX_NEW_TOKENS = 250
TEMPERATURE = 0.8
TOP_K = 40


def log_jsonl(path, record):
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def evaluate_answer(answer):
    """Simple quality signals, not a true understanding test."""
    text = answer.strip()
    words = text.split()
    unique_words = set(w.lower() for w in words)

    score = 100
    warnings = []

    if not text:
        score -= 70
        warnings.append("Empty answer")

    if len(words) < 3:
        score -= 20
        warnings.append("Very short answer")

    if len(words) >= 12 and len(unique_words) / len(words) < 0.45:
        score -= 30
        warnings.append("Possible repetition")

    if re.search(r"(.)\1{7,}", text):
        score -= 20
        warnings.append("Repeated characters")

    if "### User:" in text or "### RayX:" in text:
        score -= 25
        warnings.append("Conversation markers leaked into answer")

    if len(text) > 1800:
        score -= 10
        warnings.append("Unusually long answer")

    return max(0, min(100, score)), warnings


def load_model():
    if not CHECKPOINT.exists():
        raise FileNotFoundError(
            f"Checkpoint not found: {CHECKPOINT}\n"
            "Train your existing model first."
        )

    checkpoint = torch.load(
        CHECKPOINT,
        map_location=DEVICE,
        weights_only=True,
    )

    config = {
        **DEFAULT_CONFIG,
        **checkpoint.get("config", {}),
    }

    model = RayXModel(config).to(DEVICE)
    model.load_state_dict(checkpoint["model_state"])
    model.eval()

    print(f"Loaded checkpoint: {CHECKPOINT.name}")
    print(f"Training step: {checkpoint.get('step', 'unknown')}")

    return model, config


@torch.inference_mode()
def generate_answer(model, config, question):
    block_size = int(config["block_size"])

    prompt = f"### User: {question.strip()}\n### RayX:"
    prompt_bytes = prompt.encode("utf-8")[-block_size:]

    idx = torch.tensor(
        list(prompt_bytes),
        dtype=torch.long,
        device=DEVICE,
    ).unsqueeze(0)

    generated = bytearray()

    for _ in range(MAX_NEW_TOKENS):
        logits = model(idx[:, -block_size:])[:, -1, :]
        logits = logits[0].float() / TEMPERATURE

        k = min(TOP_K, logits.numel())
        values, _ = torch.topk(logits, k)
        logits[logits < values[-1]] = float("-inf")

        probabilities = torch.softmax(logits, dim=-1)
        next_token = torch.multinomial(probabilities, 1).item()

        generated.append(next_token)

        idx = torch.cat(
            [
                idx,
                torch.tensor(
                    [[next_token]],
                    dtype=torch.long,
                    device=DEVICE,
                ),
            ],
            dim=1,
        )

        if generated.endswith(b"### End"):
            del generated[-len(b"### End"):]
            break

    answer = bytes(generated).decode("utf-8", errors="ignore").strip()

    # Do not show accidental conversation markers as part of the answer.
    answer = answer.split("### User:", 1)[0].strip()
    answer = answer.split("### RayX:", 1)[0].strip()

    return answer


def approve_example(question, answer):
    timestamp = datetime.now(timezone.utc).isoformat()

    # The text file is used by the existing byte-level training pipeline.
    with APPROVED_FILE.open("a", encoding="utf-8") as f:
        f.write(
            f"\n### User: {question.strip()}\n"
            f"### RayX: {answer.strip()}\n"
            f"### End\n"
        )

    record = {
        "timestamp": timestamp,
        "question": question.strip(),
        "approved_answer": answer.strip(),
        "status": "approved",
    }
    log_jsonl(HISTORY_FILE, record)

    print("\nApproved example saved.")
    print(f"File: {APPROVED_FILE.name}")
    print("It will be used for training after you rebuild the dataset.")


def chat_loop(model, config):
    print("\nRayX Self-Improvement is running.")
    print("Enter 'exit' to stop.\n")

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSession ended.")
            break

        if question.lower() in {"exit", "quit"}:
            break

        if not question:
            continue

        answer = generate_answer(model, config, question)
        score, warnings = evaluate_answer(answer)

        print(f"\nRayX: {answer or '[No answer generated]'}")
        print(f"\nBasic quality signals: {score}/100")

        if warnings:
            print("Warnings: " + "; ".join(warnings))
        else:
            print("No basic formatting warnings detected.")

        print(
            "\nNote: this score checks simple patterns, "
            "not whether the answer is factually correct."
        )

        try:
            useful = input(
                "\nWas this answer correct and useful? [y/n/skip]: "
            ).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nSession ended.")
            break

        if useful in {"skip", "s", ""}:
            log_jsonl(PENDING_FILE, {
                "question": question,
                "model_answer": answer,
                "status": "needs_review",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            print("Saved for review; not added to training.")
            continue

        if useful in {"y", "yes"}:
            approved_answer = answer
            if not approved_answer:
                print("Empty answer cannot be approved.")
                continue
        elif useful in {"n", "no"}:
            print("\nWrite a corrected answer.")
            print("Type END on a separate line when finished.")

            lines = []
            while True:
                line = input()
                if line.strip() == "END":
                    break
                lines.append(line)

            approved_answer = "\n".join(lines).strip()

            if not approved_answer:
                print("No correction entered; example not saved.")
                continue
        else:
            print("Please enter y, n, or skip.")
            continue

        confirm = input(
            "\nApprove this exact answer for future training? [y/n]: "
        ).strip().lower()

        if confirm in {"y", "yes"}:
            approve_example(question, approved_answer)
        else:
            log_jsonl(PENDING_FILE, {
                "question": question,
                "model_answer": answer,
                "suggested_answer": approved_answer,
                "status": "not_approved",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            print("Not approved. Nothing added to training data.")


def main():
    model, config = load_model()
    chat_loop(model, config)


if __name__ == "__main__":
    main()
