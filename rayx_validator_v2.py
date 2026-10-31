
import re
import unicodedata
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    accepted: bool
    score: int
    warnings: list = field(default_factory=list)


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", str(text or ""))
    text = text.strip()
    return re.sub(r"\s+", " ", text)


def words(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9_]+|[\u0900-\u097F]+", text.casefold())


def validate_answer(question: str, answer: str) -> ValidationResult:
    question = normalize(question)
    answer = normalize(answer)

    warnings = []
    score = 100

    # 1. Empty response
    if not answer:
        return ValidationResult(
            accepted=False,
            score=0,
            warnings=["Empty answer"]
        )

    # 2. Very short response
    if len(answer) < 3:
        warnings.append("Answer is too short")
        score -= 35

    # 3. Extremely long response
    if len(answer) > 12000:
        warnings.append("Answer is unusually long")
        score -= 20

    # 4. Repeated characters
    if re.search(r"(.)\1{7,}", answer):
        warnings.append("Suspicious repeated characters")
        score -= 30

    # 5. Repeated words
    tokens = words(answer)

    if len(tokens) >= 8:
        repeated = sum(
            1 for a, b in zip(tokens, tokens[1:])
            if a == b
        )

        if repeated >= 4:
            warnings.append("Too many consecutive repeated words")
            score -= 30

    # 6. Repeated sentence detection
    sentences = [
        s.strip().casefold()
        for s in re.split(r"[.!?\n]+", answer)
        if len(s.strip()) > 5
    ]

    if len(sentences) >= 3:
        unique_ratio = len(set(sentences)) / len(sentences)

        if unique_ratio < 0.5:
            warnings.append("Repeated sentences detected")
            score -= 25

    # 7. Debug or training markers
    suspicious_markers = [
        "### user:",
        "### rayx:",
        "<|endoftext|>",
        "loss:",
        "optimizer:",
        "traceback (most recent call last)"
    ]

    lower_answer = answer.casefold()

    for marker in suspicious_markers:
        if marker in lower_answer:
            warnings.append(f"Internal marker detected: {marker}")
            score -= 25

    # 8. Question and answer availability
    if not question:
        warnings.append("Original question is missing")
        score -= 10

    score = max(0, min(100, score))

    # Reject only clear quality failures.
    hard_fail = (
        not answer
        or len(answer) < 3
        or "traceback (most recent call last)" in lower_answer
    )

    accepted = hard_fail is False and score >= 60

    return ValidationResult(
        accepted=accepted,
        score=score,
        warnings=warnings
    )


if __name__ == "__main__":
    tests = [
        ("What is Python?", "Python is a programming language."),
        ("Explain AI", "AI AI AI AI AI AI AI AI AI AI"),
        ("What is science?", ""),
        ("Hello", "Hello! How can I help you?"),
        ("Explain coding", "aaaaaaaaaaaaaaaaaaaa"),
    ]

    for question, answer in tests:
        result = validate_answer(question, answer)

        print("\nQuestion:", question)
        print("Answer:", answer)
        print("Accepted:", result.accepted)
        print("Score:", result.score)
        print("Warnings:", result.warnings)
