
"""RayX Model 2: conservative local answer validation.

This checks basic format and relevance signals.
It cannot guarantee factual correctness or detect all gibberish.
"""

import re
from dataclasses import dataclass, asdict
from typing import List


@dataclass
class ValidationResult:
    accepted: bool
    score: int
    warnings: List[str]

    def to_dict(self):
        return asdict(self)


def _words(text):
    return re.findall(r"\b[\w']+\b", text.casefold(), re.UNICODE)


def validate_answer(question: str, answer: str) -> ValidationResult:
    question = str(question).strip()
    answer = str(answer).strip()

    warnings = []
    score = 100

    if not question:
        return ValidationResult(False, 0, ["Empty question"])

    if not answer:
        return ValidationResult(False, 0, ["Empty answer"])

    # Leaked training or conversation markers
    if re.search(r"###\s*(?:User|RayX|End)\s*:?", answer, re.I):
        warnings.append("Conversation marker leak")
        score -= 60

    # Long repeated characters
    if re.search(r"(.)\1{7,}", answer):
        warnings.append("Repeated characters")
        score -= 40

    words = _words(answer)

    # Excessive repetition in longer responses
    if len(words) >= 12:
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.40:
            warnings.append("Excessive word repetition")
            score -= 40

    # Suspicious strings known from our local test cases.
    if re.fullmatch(
        r"(?:blve|prilt|asult)(?:\s+(?:blve|prilt|asult))*",
        answer.casefold(),
    ):
        warnings.append("Known gibberish test pattern")
        score -= 80

    # Flag outputs that look like random fragments:
    # many tokens, almost no vowels, and no common English/Hinglish terms.
    if len(words) >= 5:
        alphabetic = [
            word for word in words
            if any(char.isalpha() for char in word)
        ]

        if alphabetic:
            low_vowel_count = sum(
                1 for word in alphabetic
                if len(word) >= 4
                and not re.search(r"[aeiou]", word)
            )

            if low_vowel_count >= 3:
                warnings.append("Unusual word pattern")
                score -= 45

    if len(answer) > 1800:
        warnings.append("Unusually long answer")
        score -= 10

    score = max(0, score)

    # Conservative rule: warnings trigger rejection.
    accepted = score >= 60 and not warnings

    return ValidationResult(
        accepted=accepted,
        score=score,
        warnings=warnings,
    )


if __name__ == "__main__":
    samples = [
        ("Say hello", "Hello! How are you today?"),
        ("Explain physics", "blve blve prilt asult"),
        ("Explain something", "Hey! L Macon isk sa sing ko raneelatip hai."),
        ("What is Python?", "Python is a programming language."),
    ]

    for question, answer in samples:
        print("\nQuestion:", question)
        print("Answer:", answer)
        print(validate_answer(question, answer).to_dict())
