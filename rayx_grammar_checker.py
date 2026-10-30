"""Safe adapter around RayX's existing grammar correction engine."""

from rayx_english_grammar import correct_english_sentence
from rayx_sentence_parser import analyse_sentence


def check_grammar(sentence):
    original = str(sentence or "").strip()

    if not original:
        return {
            "status": "empty",
            "original": original,
            "corrected": original,
            "issues": [],
            "explanation": "Please enter a sentence.",
        }

    try:
        result = correct_english_sentence(original)
    except Exception as error:
        return {
            "status": "error",
            "original": original,
            "corrected": original,
            "issues": [],
            "explanation": (
                "The local grammar correction engine encountered an error: "
                + type(error).__name__
            ),
        }

    if not isinstance(result, dict) or not result.get("answer"):
        return {
            "status": "not_checked",
            "original": original,
            "corrected": original,
            "issues": [],
            "explanation": (
                "No confident correction rule matched this sentence. "
                "This does not prove that the sentence is grammatically correct."
            ),
        }

    analysis = analyse_sentence(original)

    return {
        "status": "corrected",
        "original": original,
        "corrected": result["answer"],
        "issues": [
            {
                "type": "rule_based_correction",
                "message": result.get("topic", "Grammar correction"),
            }
        ],
        "explanation": result["answer"],
        "topic": result.get("topic", "sentence correction"),
        "verified": bool(result.get("verified", False)),
        "analysis": analysis,
    }
