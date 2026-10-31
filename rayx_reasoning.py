
import re


TASK_PATTERNS = {
    "coding": [
        "write code", "create a program", "build a website",
        "fix this code", "debug", "python program"
    ],
    "explanation": [
        "explain", "what is", "how does", "kya hai",
        "samjhao", "meaning"
    ],
    "comparison": [
        "difference between", "compare", "versus", "vs"
    ],
    "calculation": [
        "calculate", "solve", "how much", "kitna"
    ],
    "learning": [
        "teach me", "learn", "study", "practice",
        "seekhna", "sikhao"
    ],
}


def normalize(text):
    text = text.casefold().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def identify_task(text):
    normalized = normalize(text)

    matches = []

    for task, patterns in TASK_PATTERNS.items():
        if any(pattern in normalized for pattern in patterns):
            matches.append(task)

    if not matches:
        return "general"

    return matches[0]


def extract_requirements(text):
    requirements = []

    normalized = normalize(text)

    if "simple" in normalized or "easy" in normalized:
        requirements.append("Use simple language")

    if "hinglish" in normalized:
        requirements.append("Respond in Hinglish")

    if "short" in normalized:
        requirements.append("Keep the answer concise")

    if "example" in normalized:
        requirements.append("Include an example")

    if "step by step" in normalized:
        requirements.append("Explain in ordered steps")

    return requirements


def create_plan(text):
    task = identify_task(text)
    requirements = extract_requirements(text)

    plans = {
        "coding": [
            "Understand the requested program",
            "Identify inputs and expected outputs",
            "Choose a suitable approach",
            "Prepare the code",
            "Check the code for obvious errors",
            "Explain how to run it"
        ],
        "explanation": [
            "Identify the concept",
            "Determine the user's requested detail level",
            "Explain the main idea",
            "Add an example when useful",
            "Check that the explanation answers the question"
        ],
        "comparison": [
            "Identify both subjects",
            "Find their comparison criteria",
            "Compare the important differences",
            "Summarize the result"
        ],
        "calculation": [
            "Identify the mathematical expression",
            "Select the appropriate operation",
            "Calculate the result",
            "Check the calculation"
        ],
        "learning": [
            "Identify the learning topic",
            "Check the requested level",
            "Break the topic into smaller lessons",
            "Provide practice examples",
            "Review understanding"
        ],
        "general": [
            "Understand the user's request",
            "Identify missing information",
            "Prepare a relevant response",
            "Check the response for relevance"
        ]
    }

    return {
        "task_type": task,
        "requirements": requirements,
        "plan": plans[task]
    }


def validate_plan(result):
    if not isinstance(result, dict):
        return False

    if not result.get("task_type"):
        return False

    if not isinstance(result.get("plan"), list):
        return False

    return len(result["plan"]) > 0


if __name__ == "__main__":
    tests = [
        "Explain Python functions in simple words with example",
        "Build a website step by step",
        "Compare Python and JavaScript",
        "2 + 2 kitna hota hai?",
        "Teach me programming in Hinglish"
    ]

    for question in tests:
        result = create_plan(question)

        print("\nUser:", question)
        print("Plan:", result)
        print("Valid:", validate_plan(result))
