
import re

from rayx_math_engine import solve_math
from rayx_knowledge import search_knowledge
from rayx_validator import validate_answer
from rayx_english_grammar import answer_grammar_question


INCOMPLETE_MATH_MESSAGE = (
    "This math expression looks incomplete. "
    "Please finish the expression and try again."
)

UNRELIABLE_ANSWER_MESSAGE = (
    "I couldn't produce a reliable answer to that question yet. "
    "My local model may need more training data."
)


def _result(answer, source, verified=False, details=""):
    return {
        "answer": answer,
        "source": source,
        "verified": verified,
        "details": details,
    }


def _greeting_response(question):
    normalized = re.sub(
        r"[^\w\s]",
        " ",
        question.casefold(),
    ).strip()

    normalized = re.sub(r"\s+", " ", normalized)

    greetings = {
        "hey", "hi", "hello", "hey there",
        "hi there", "hello there", "hii",
        "hiii", "namaste", "namaskar",
    }

    if normalized in greetings:
        return _result(
            "Hey! How can I help you today?",
            "local_greeting",
            verified=True,
            details="Deterministic local greeting response",
        )

    return None


def _is_incomplete_math(question):
    text = question.strip()

    if not text or not re.search(r"\d", text):
        return False

    if not re.fullmatch(r"[\d\s().,+\-*/%^]+", text):
        return False

    compact = re.sub(r"\s+", "", text)

    return compact.endswith(("+", "-", "*", "/", "^", "%", "."))


def answer_question(
    question,
    model=None,
    config=None,
    generate_answer=None,
    find_memory_answer=None,
):
    question = str(question).strip()

    if not question:
        return _result("Please enter a question.", "none")

    # 1. Greetings
    greeting = _greeting_response(question)

    if greeting is not None:
        return greeting

    # 2. English grammar lessons
    try:
        grammar_result = answer_grammar_question(question)
    except Exception as error:
        grammar_result = None
        grammar_error = type(error).__name__
    else:
        grammar_error = None

    if grammar_result is not None:
        return _result(
            grammar_result["answer"],
            "grammar_engine",
            verified=grammar_result.get("verified", False),
            details=f"Grammar topic: {grammar_result['topic']}",
        )

    # 3. Calculator
    try:
        math_result = solve_math(question)
    except Exception:
        math_result = None

    if math_result is not None:
        return _result(
            math_result,
            "calculator",
            verified=True,
            details="Calculated locally",
        )

    # 4. Incomplete arithmetic
    if _is_incomplete_math(question):
        return _result(
            INCOMPLETE_MATH_MESSAGE,
            "calculator",
            details="Incomplete arithmetic expression",
        )

    # 5. Local knowledge
    knowledge_error = None

    try:
        knowledge_result = search_knowledge(question)
    except Exception as error:
        knowledge_result = None
        knowledge_error = type(error).__name__

    if knowledge_result is not None:
        return _result(
            knowledge_result["answer"],
            "knowledge_base",
            verified=knowledge_result.get("verified", False),
            details=(
                f"Subject: {knowledge_result.get('subject', 'General')}; "
                f"Source: {knowledge_result.get('source', 'unspecified')}"
            ),
        )

    # 6. Saved memory
    if find_memory_answer is not None:
        try:
            memory_result = find_memory_answer(question)
        except Exception:
            memory_result = None

        if isinstance(memory_result, dict):
            memory_answer = str(
                memory_result.get("answer", "")
            ).strip()

            if memory_answer:
                return _result(
                    memory_answer,
                    "memory",
                    verified=False,
                    details="Retrieved from stored conversation",
                )

    # 7. Local neural model
    if generate_answer is None:
        return _result(
            "No local model generator is configured.",
            "none",
            details="Model generation is not configured",
        )

    try:
        generated = generate_answer(model, config, question)
    except Exception as error:
        return _result(
            "RayX could not generate an answer.",
            "error",
            details=f"Error type: {type(error).__name__}",
        )

    if not isinstance(generated, str) or not generated.strip():
        return _result(
            "No answer generated yet.",
            "none",
            details="Empty model response",
        )

    generated = generated.strip()
    validation = validate_answer(question, generated)

    if not validation.accepted:
        warnings = validation.warnings or ["Quality checks failed"]

        return _result(
            UNRELIABLE_ANSWER_MESSAGE,
            "neural_model",
            details=(
                f"Rejected output: {'; '.join(warnings)}; "
                f"basic quality score: {validation.score}/100"
            ),
        )

    details = (
        "Generated locally; not independently verified; "
        f"basic quality score: {validation.score}/100"
    )

    if knowledge_error:
        details += f"; knowledge lookup unavailable: {knowledge_error}"

    if grammar_error:
        details += f"; grammar lookup unavailable: {grammar_error}"

    return _result(
        generated,
        "neural_model",
        verified=False,
        details=details,
    )


if __name__ == "__main__":
    print("RayX Hybrid router loaded successfully.")
