
from rayx_math_engine import solve_math
from rayx_knowledge import search_knowledge


def answer_question(
    question,
    model=None,
    config=None,
    generate_answer=None,
    find_memory_answer=None,
):
    question = str(question).strip()

    if not question:
        return {
            "answer": "Please enter a question.",
            "source": "none",
            "verified": False,
            "details": "Empty question",
        }

    # 1. Mathematics
    math_result = solve_math(question)

    if math_result is not None:
        return {
            "answer": math_result,
            "source": "calculator",
            "verified": True,
            "details": "Calculated locally",
        }

    # 2. Knowledge base
    knowledge_result = search_knowledge(question)

    if knowledge_result is not None:
        return {
            "answer": knowledge_result["answer"],
            "source": "knowledge_base",
            "verified": knowledge_result.get("verified", False),
            "details": (
                f"Subject: {knowledge_result.get('subject', 'General')}; "
                f"Source: {knowledge_result.get('source', 'unspecified')}"
            ),
        }

    # 3. Stored memory
    if find_memory_answer is not None:
        memory_result = find_memory_answer(question)

        if memory_result:
            return {
                "answer": memory_result["answer"],
                "source": "memory",
                "verified": False,
                "details": "Retrieved from stored conversation",
            }

    # 4. Existing local model
    if generate_answer is None:
        return {
            "answer": "No model generator was provided.",
            "source": "none",
            "verified": False,
            "details": "Model generation is not configured",
        }

    try:
        generated = generate_answer(model, config, question)
    except Exception as error:
        return {
            "answer": "RayX could not generate an answer.",
            "source": "error",
            "verified": False,
            "details": f"Error type: {type(error).__name__}",
        }

    if not isinstance(generated, str) or not generated.strip():
        return {
            "answer": "No answer generated yet.",
            "source": "none",
            "verified": False,
            "details": "Empty model response",
        }

    return {
        "answer": generated.strip(),
        "source": "neural_model",
        "verified": False,
        "details": "Generated locally; not independently verified",
    }


if __name__ == "__main__":
    print("RayX Hybrid router loaded successfully.")
