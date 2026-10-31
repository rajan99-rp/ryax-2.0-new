"""RayX Model 2: local-first hybrid chat.

Order: safe local calculator -> local knowledge base -> saved examples -> local
neural model. No external AI API is called by this program.
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import torch

from model import RayXModel, DEFAULT_CONFIG
from rayx_memory import find_answer
from rayx_math_engine import solve_math
from rayx_knowledge import search_knowledge

ROOT = Path(__file__).resolve().parent
CHECKPOINT = ROOT / "artifacts" / "rayx_model.pt"
EXPERIENCE_FILE = ROOT / "experience_log.jsonl"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MAX_NEW_TOKENS = 180
TEMPERATURE = 0.7
TOP_K = 30

_model = None
_config = None


def load_model():
    """Load the existing checkpoint only when neural generation is needed."""
    global _model, _config
    if _model is not None:
        return _model, _config
    if not CHECKPOINT.exists():
        raise FileNotFoundError(f"Missing checkpoint: {CHECKPOINT}")
    checkpoint = torch.load(CHECKPOINT, map_location=DEVICE, weights_only=True)
    config = {**DEFAULT_CONFIG, **checkpoint.get("config", {})}
    model = RayXModel(config).to(DEVICE)
    state = checkpoint.get("model_state", checkpoint.get("model_state_dict"))
    if state is None:
        raise ValueError("Checkpoint does not contain model weights.")
    model.load_state_dict(state)
    model.eval()
    _model, _config = model, config
    print(f"[RayX] Loaded local checkpoint on {DEVICE}; step={checkpoint.get('step', '?')}")
    return _model, _config


def evaluate_answer(answer):
    text = str(answer).strip()
    words = text.split()
    warnings = []
    score = 100
    if not text:
        return 0, ["Empty answer"]
    if len(words) < 3:
        score -= 15
        warnings.append("Very short answer")
    if len(words) >= 12 and len(set(w.casefold() for w in words)) / len(words) < 0.45:
        score -= 30
        warnings.append("Possible repetition")
    if re.search(r"(.)\1{7,}", text):
        score -= 20
        warnings.append("Repeated characters")
    if re.search(r"###\s*(?:User|RayX|End)\s*:?", text, re.I):
        score -= 30
        warnings.append("Conversation marker leak")
    if len(text) > 1800:
        score -= 10
        warnings.append("Unusually long answer")
    return max(0, score), warnings


@torch.inference_mode()
def generate_answer(model, config, question):
    """Generate from the existing byte-level model; this is not a guaranteed fact source."""
    block_size = int(config["block_size"])
    prompt = f"### User: {question.strip()}\n### RayX:"
    context_bytes = prompt.encode("utf-8")[-block_size:]
    idx = torch.tensor(list(context_bytes), dtype=torch.long, device=DEVICE).unsqueeze(0)
    generated = bytearray()

    for _ in range(MAX_NEW_TOKENS):
        logits = model(idx[:, -block_size:])[:, -1, :][0].float()
        logits = logits / TEMPERATURE
        k = min(TOP_K, logits.numel())
        values, _ = torch.topk(logits, k)
        logits[logits < values[-1]] = float("-inf")
        probs = torch.softmax(logits, dim=-1)
        token = int(torch.multinomial(probs, 1).item())
        generated.append(token)
        idx = torch.cat((idx, torch.tensor([[token]], device=DEVICE)), dim=1)
        if generated.endswith(b"### End"):
            del generated[-len(b"### End"):]
            break

    answer = bytes(generated).decode("utf-8", errors="ignore").strip()
    answer = re.split(r"###\s*(?:User|RayX)\s*:", answer, maxsplit=1, flags=re.I)[0]
    answer = re.split(r"###\s*End\b", answer, maxsplit=1, flags=re.I)[0]
    return answer.strip()


def _memory_lookup(question):
    # Calculator gets first priority so "2+2+6" can never retrieve an old "2+2" answer.
    if solve_math(question) is not None:
        return None
    try:
        return find_answer(question, threshold=0.92)
    except TypeError:
        return find_answer(question)


def _neural_fallback(_model, _config, question):
    model, config = load_model()
    return generate_answer(model, config, question)


def log_experience(question, result, score, warnings):
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "answer": result["answer"],
        "source": result["source"],
        "verified": bool(result.get("verified", False)),
        "basic_quality_score": score,
        "warnings": warnings,
        "details": result.get("details", ""),
    }
    with EXPERIENCE_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


def answer(question):
    from rayx_hybrid import answer_question
    return answer_question(
        question,
        model=None,
        config=None,
        generate_answer=_neural_fallback,
        find_memory_answer=_memory_lookup,
    )


def main():
    print("\nRayX Model 2 — Local Hybrid Assistant")
    print("Calculator + local knowledge + saved examples + your trained model")
    print("No external AI API. Type 'exit' to stop.\n")

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nRayX stopped.")
            break
        if question.casefold() in {"exit", "quit", "bye"}:
            print("RayX stopped.")
            break
        if not question:
            continue

        result = answer(question)
        text = result.get("answer", "").strip()
        score, warnings = evaluate_answer(text)
        print(f"\nRayX: {text or '[No answer generated]'}")
        print(f"Source: {result.get('source', 'unknown')}")
        print(f"Verified: {'yes' if result.get('verified') else 'not independently verified'}")
        if result.get("details"):
            print(f"Details: {result['details']}")
        if warnings:
            print("Quality warnings: " + "; ".join(warnings))
        log_experience(question, result, score, warnings)
        print()

if __name__ == "__main__":
    main()
