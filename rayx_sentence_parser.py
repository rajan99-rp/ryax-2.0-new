"""Basic offline English sentence structure analyser."""

import re

PRONOUNS = {
    "i", "you", "he", "she", "it", "we", "they",
    "me", "him", "her", "us", "them",
}

BE_VERBS = {"am", "is", "are", "was", "were", "be", "been", "being"}
COMMON_VERBS = {
    "have", "has", "had", "do", "does", "did",
    "go", "goes", "went", "gone",
    "eat", "eats", "ate", "eaten",
    "play", "plays", "played",
    "study", "studies", "studied",
    "write", "writes", "wrote", "written",
    "make", "makes", "made",
    "like", "likes", "liked",
    "want", "wants", "wanted",
    "need", "needs", "needed",
    "learn", "learns", "learned",
    "work", "works", "worked",
    "speak", "speaks", "spoke",
    "know", "knows", "knew",
    "see", "sees", "saw",
    "run", "runs", "ran",
    "read", "reads",
}


def analyse_sentence(sentence):
    text = str(sentence or "").strip()
    words = re.findall(r"[A-Za-z']+", text)
    lower = [word.lower() for word in words]

    verb_index = None
    verb = None

    for index, word in enumerate(lower):
        if word in BE_VERBS or word in COMMON_VERBS:
            verb_index = index
            verb = words[index]
            break

    subject = None
    if verb_index is not None and verb_index > 0:
        subject = words[verb_index - 1]
    elif words:
        subject = words[0]

    object_text = None
    if verb_index is not None and verb_index + 1 < len(words):
        object_text = " ".join(words[verb_index + 1:])

    if any(word in lower for word in ("will", "shall")):
        tense = "future"
    elif any(word in lower for word in ("was", "were", "had", "did")):
        tense = "past"
    elif any(word in lower for word in ("am", "is", "are", "has", "have", "does")):
        tense = "present"
    elif any(word.endswith("ed") for word in lower):
        tense = "possibly past"
    else:
        tense = "undetermined"

    return {
        "sentence": text,
        "words": words,
        "subject": subject,
        "verb": verb,
        "object": object_text,
        "tense": tense,
        "word_count": len(words),
    }


# US spelling alias
analyze_sentence = analyse_sentence
