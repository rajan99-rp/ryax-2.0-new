
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import torch

from model import RayXModel, DEFAULT_CONFIG
from rayx_memory import find_answer

ROOT = Path(__file__).resolve().parent
CHECKPOINT = ROOT / "artifacts" / "rayx_model.pt"
EXPERIENCE_FILE = ROOT / "experience_log.jsonl"

DEVICE = torch.device("cpu")
MAX_NEW_TOKENS = 220
TEMPERATURE = 0.8
TOP_K = 40


def evaluate_answer(answer):
    text = answer.strip()
    words = text.split()
    warnings = []
    score = 100

    if not text:
        return 0, ["Empty answer"]

    if len(words) < 3:
        score -= 20
        warnings.append("Very short answer")

    if len(words) >= 12:
        unique_ratio = len(set(w.lower() for w in words)) / len(words)
        if unique_ratio < 0.45:
            score -= 30
            warnings.append("Possible repetition")

    if re.search(r"(.)\1{7,}", text):
        score -= 20
        warnings.append("Repeated characters")

    if "### User:" in text or "### RayX:" in text:
        score -= 25
        warnings.append("Conversation marker leak")

    if len(text) > 1800:
        score -= 10
        warnings.append("Unusually long answer")

    return max(0, score), warnings


def load_model():
    if not CHECKPOINT.exists():
        raise FileNotFoundError(f"Missing checkpoint: {CHECKPOINT}")

    checkpoint = torch.load(
        CHECKPOINT,
        map_location=DEVICE,
        weights_only=True,
    )

    config = {**DEFAULT_CONFIG, **checkpoint.get("config", {})}
    model = RayXModel(config).to(DEVICE)
    model.load_state_dict(checkpoint["model_state"])
    model.eval()

    print(f"RayX checkpoint loaded. Step: {checkpoint.get('step', '?')}")
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
        logits = model(idx[:, -block_size:])[:, -1, :][0].float()
        logits = logits / TEMPERATURE

        k = min(TOP_K, logits.numel())
        top_values, _ = torch.topk(logits, k)
        logits[logits < top_values[-1]] = float("-inf")

        probs = torch.softmax(logits, dim=-1)
        token = torch.multinomial(probs, num_samples=1).item()
        generated.append(token)

        next_token = torch.tensor(
            [[token]], dtype=torch.long, device=DEVICE
        )
        idx = torch.cat([idx, next_token], dim=1)

        if generated.endswith(b"### End"):
            del generated[-len(b"### End"):]
            break

    answer = bytes(generated).decode("utf-8", errors="ignore").strip()

    # Remove accidental conversation markers from the visible answer.
    answer = re.split(r"### (?:User|RayX):", answer, maxsplit=1)[0]
    answer = answer.split("### End", 1)[0]
    return answer.strip()


def log_experience(question, answer, source, score, warnings):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "answer": answer,
        "source": source,
        "basic_quality_score": score,
        "warnings": warnings,
        "truth_verified": source == "trusted_memory",
    }

    with EXPERIENCE_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main():
    model, config = load_model()

    print("\nRayX Auto-Learning is ready.")
    print("Type 'exit' to quit.\n")

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nRayX stopped.")
            break

        if question.lower() in {"exit", "quit"}:
            break

        if not question:
            continue

        memory_result = find_answer(question)

        if memory_result:
            answer = memory_result["answer"]
            source = "trusted_memory"
            print(f"\nRayX [Memory]: {answer}")
        else:
            answer = generate_answer(model, config, question)
            source = "neural_model"
            print(f"\nRayX: {answer or '[No answer generated]'}")

        score, warnings = evaluate_answer(answer)

        if warnings:
            print("Self-check:", "; ".join(warnings))
        else:
            print("Self-check: no basic formatting issues detected")

        print(f"Basic quality score: {score}/100")

        if source == "neural_model":
            print("Verification: not independently verified")
        else:
            print("Source: stored training example")

        log_experience(question, answer, source, score, warnings)
        print()

    print(f"Experience log: {EXPERIENCE_FILE.name}")


if __name__ == "__main__":
    main()
