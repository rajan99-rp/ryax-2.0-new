
import re
import unicodedata


ALIASES = {
    "hlo": "hello",
    "helo": "hello",
    "heyy": "hey",
    "hiii": "hi",
    "hii": "hi",
    "h": "hai",
    "kya h": "kya hai",
    "kya hai": "kya hai",
    "kya": "what",
    "kyu": "why",
    "kaise": "how",
    "btao": "batao",
    "bta": "batao",
    "btw": "by the way",
    "plz": "please",
    "pls": "please",
    "thx": "thanks",
}


GREETINGS = {
    "hi", "hello", "hey", "hello there",
    "good morning", "good afternoon",
    "good evening", "namaste", "hii", "heyy"
}


def normalize(text):
    text = unicodedata.normalize("NFKC", str(text or ""))
    text = text.casefold().strip()
    text = re.sub(r"\s+", " ", text)
    return ALIASES.get(text, text)


def is_random_text(text):
    cleaned = re.sub(r"[^a-zA-Z]", "", text)

    if len(cleaned) < 2:
        return False

    # A simple heuristic, not a perfect language detector.
    vowels = sum(c in "aeiou" for c in cleaned.lower())
    vowel_ratio = vowels / len(cleaned)

    if len(cleaned) >= 6 and vowel_ratio < 0.10:
        return True

    if re.search(r"(.)\1{4,}", cleaned.lower()):
        return True

    return False


def understand(user_input):
    text = normalize(user_input)

    if not text:
        return {
            "intent": "empty",
            "normalized": "",
            "confidence": 1.0
        }

    if text in GREETINGS:
        return {
            "intent": "greeting",
            "normalized": text,
            "confidence": 1.0
        }

    if text in {"thanks", "thank you", "shukriya", "dhanyawad"}:
        return {
            "intent": "thanks",
            "normalized": text,
            "confidence": 1.0
        }

    if text in {"bye", "goodbye", "see you", "alvida"}:
        return {
            "intent": "goodbye",
            "normalized": text,
            "confidence": 1.0
        }

    if text in {"kya hai", "what", "why", "how"}:
        return {
            "intent": "short_question",
            "normalized": text,
            "confidence": 0.8
        }

    if is_random_text(text):
        return {
            "intent": "unclear",
            "normalized": text,
            "confidence": 0.85
        }

    return {
        "intent": "question",
        "normalized": text,
        "confidence": 0.5
    }


if __name__ == "__main__":
    tests = [
        "hey",
        "hlo",
        "kya h",
        "cfjggs",
        "gfzdhgfjf",
        "What is Python?",
        "photosynthesis",
        "ht",
    ]

    for item in tests:
        print(item, "=>", understand(item))
