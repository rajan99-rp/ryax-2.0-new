
"""RayX Model 2: automatic, conservative self-improvement.

- No user feedback or approval prompts.
- No external AI APIs.
- Suspicious neural answers are recorded for analysis, not trusted as facts.
- Only deterministic calculator results and explicitly verified local
  knowledge answers can enter approved_examples.txt automatically.
- Never modifies or overwrites model checkpoints.
"""

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import torch

from model import RayXModel, DEFAULT_CONFIG
from rayx_hybrid import answer_question


ROOT = Path(__file__).resolve().parent
CHECKPOINT = ROOT / "artifacts" / "rayx_model.pt"
APPROVED_FILE = ROOT / "approved_examples.txt"
PENDING_FILE = ROOT / "pending_examples.jsonl"
HISTORY_FILE = ROOT / "improvement_history.jsonl"
DEVICE = torch.device("cpu")

MAX_NEW_TOKENS = 180
TEMPERATURE = 0.7
TOP_K = 30

model = None
config = None


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def log_jsonl(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


def text_hash(question, answer):
    content = question.strip().casefold() + "\n" + answer.strip().casefold()
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def evaluate_answer(answer):
    """Basic formatting checks, not a factuality test."""
    text = str(answer).strip()
    words = text.split()
    warnings = []
    score = 100

    if not text:
        return 0, ["Empty answer"]

    if len(words) < 3:
        score -= 15
        warnings.append("Very short answer")

    if len(words) >= 12:
        unique_ratio = len({word.casefold() for word in words}) / len(words)
        if unique_ratio < 0.40:
            score -= 35
            warnings.append("Excessive word repetition")

    if re.search(r"(.)\1{7,}", text):
        score -= 25
        warnings.append("Repeated characters")

    if re.search(r"###\s*(?:User|RayX|End)\s*:?", text, re.I):
        score -= 35
        warnings.append("Conversation marker leak")

    if len(text) > 1800:
        score -= 10
        warnings.append("Unusually long answer")

    return max(0, score), warnings


def load_model():
    """Load the current checkpoint; this function never saves model weights."""
    global model, config

    if model is not None:
        return model, config

    if not CHECKPOINT.exists():
        raise FileNotFoundError(f"Checkpoint not found: {CHECKPOINT}")

    checkpoint = torch.load(
        CHECKPOINT,
        map_location=DEVICE,
        weights_only=True,
    )

    config = {**DEFAULT_CONFIG, **checkpoint.get("config", {})}
    model = RayXModel(config).to(DEVICE)

    state = checkpoint.get(
        "model_state",
        checkpoint.get("model_state_dict"),
    )
    if state is None:
        raise ValueError("Checkpoint contains no model weights.")

    model.load_state_dict(state)
    model.eval()

    print(
        f"[RayX] Loaded {CHECKPOINT.name}; "
        f"step={checkpoint.get('step', 'unknown')}"
    )
    return model, config


@torch.inference_mode()
def generate_answer(active_model, active_config, question):
    block_size = int(active_config["block_size"])
    prompt = f"### User: {question.strip()}\n### RayX:"
    prompt_bytes = prompt.encode("utf-8")[-block_size:]

    idx = torch.tensor(
        list(prompt_bytes),
        dtype=torch.long,
        device=DEVICE,
    ).unsqueeze(0)

    generated = bytearray()

    for _ in range(MAX_NEW_TOKENS):
        logits = active_model(idx[:, -block_size:])[:, -1, :][0].float()
        logits = logits / TEMPERATURE

        k = min(TOP_K, logits.numel())
        values, _ = torch.topk(logits, k)
        logits[logits < values[-1]] = float("-inf")

        probabilities = torch.softmax(logits, dim=-1)
        token = int(torch.multinomial(probabilities, 1).item())
        generated.append(token)

        next_token = torch.tensor([[token]], dtype=torch.long, device=DEVICE)
        idx = torch.cat((idx, next_token), dim=1)

        if generated.endswith(b"### End"):
            del generated[-len(b"### End"):]
            break

    answer = bytes(generated).decode("utf-8", errors="ignore").strip()
    answer = re.split(
        r"###\s*(?:User|RayX|End)\s*:?",
        answer,
        maxsplit=1,
        flags=re.I,
    )[0]

    return answer.strip()


def _known_hashes():
    """Collect hashes already present in the training examples file."""
    known = set()

    if not APPROVED_FILE.exists():
        return known

    content = APPROVED_FILE.read_text(encoding="utf-8")
    pattern = re.compile(
        r"### User:\s*(.*?)\n### RayX:\s*(.*?)\n### End",
        re.S,
    )

    for match in pattern.finditer(content):
        known.add(text_hash(match.group(1), match.group(2)))

    return known


def save_trusted_example(question, answer, source, verified):
    """Save only deterministic calculations or explicitly verified KB facts."""
    if source != "calculator" and not (
        source == "knowledge_base" and verified is True
    ):
        return False

    question = str(question).strip()
    answer = str(answer).strip()

    if not question or not answer:
        return False

    digest = text_hash(question, answer)
    if digest in _known_hashes():
        return False

    with APPROVED_FILE.open("a", encoding="utf-8") as file:
        file.write(
            f"\n### User: {question}\n"
            f"### RayX: {answer}\n"
            "### End\n"
        )

    log_jsonl(HISTORY_FILE, {
        "timestamp": timestamp(),
        "question": question,
        "answer": answer,
        "source": source,
        "verified": verified,
        "hash": digest,
        "status": "automatically_added",
        "note": "Eligible deterministic or explicitly verified local answer",
    })

    return True


def process_question(question):
    """Answer, evaluate, and record learning signals without asking the user."""
    active_model, active_config = load_model()

    result = answer_question(
        question,
        model=active_model,
        config=active_config,
        generate_answer=generate_answer,
    )

    answer = str(result.get("answer", "")).strip()
    source = result.get("source", "unknown")
    verified = result.get("verified") is True

    score, warnings = evaluate_answer(answer)

    # Trust routing metadata, not the score alone.
    saved = save_trusted_example(
        question=question,
        answer=answer,
        source=source,
        verified=verified,
    )

    record = {
        "timestamp": timestamp(),
        "question": question,
        "answer": answer,
        "source": source,
        "verified": verified,
        "quality_score": score,
        "warnings": warnings,
        "trusted_example_saved": saved,
    }

    if source == "neural_model" or warnings:
        record["status"] = "needs_automatic_review"
        log_jsonl(PENDING_FILE, record)
    else:
        record["status"] = "processed"
        log_jsonl(HISTORY_FILE, record)

    return result, score, warnings, saved


def chat_loop():
    print("\nRayX Automatic Learning Mode")
    print("Local-only; no approval prompts; checkpoint is read-only.")
    print("Type 'exit' to stop.\n")

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSession ended.")
            break

        if question.casefold() in {"exit", "quit", "bye"}:
            print("RayX stopped.")
            break

        if not question:
            continue

        try:
            result, score, warnings, saved = process_question(question)
        except Exception as error:
            log_jsonl(HISTORY_FILE, {
                "timestamp": timestamp(),
                "question": question,
                "status": "processing_error",
                "error_type": type(error).__name__,
            })
            print("RayX could not process this question.")
            print(f"Error type: {type(error).__name__}\n")
            continue

        print(f"\nRayX: {result.get('answer', '')}")
        print(f"Source: {result.get('source', 'unknown')}")
        print(f"Verified: {'yes' if result.get('verified') else 'no'}")
        print(f"Basic quality score: {score}/100")

        if warnings:
            print("Warnings: " + "; ".join(warnings))

        if saved:
            print("Eligible example added to the training examples.")
        elif result.get("source") == "neural_model":
            print("Neural output saved for automatic review; not trusted as a fact.")

        print()


def main():
    chat_loop()


if __name__ == "__main__":
    main()
