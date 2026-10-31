
"""RayX Grammar Practice Engine

Offline English grammar quizzes with:
- 12 tense questions
- Easy, Medium and Hard levels
- Topic filtering
- Automatic answer checking
- Quiz scoring
- Topic-wise performance
- Persistent JSON progress
"""

import random
import re
import json

from pathlib import Path
from datetime import datetime, timezone


# =========================================================
# 1. QUESTION BANK
# =========================================================

QUESTION_BANK = [
    {
        "id": 1,
        "topic": "present simple",
        "difficulty": "easy",
        "question": "She ___ to school every day.",
        "options": ["go", "goes", "going", "gone"],
        "answer": "goes",
        "explanation": "In Present Simple, he/she/it takes a verb with -s or -es."
    },
    {
        "id": 2,
        "topic": "present continuous",
        "difficulty": "easy",
        "question": "They ___ playing football right now.",
        "options": ["is", "are", "was", "be"],
        "answer": "are",
        "explanation": "Present Continuous uses am/is/are + verb-ing. They takes are."
    },
    {
        "id": 3,
        "topic": "present perfect",
        "difficulty": "medium",
        "question": "I ___ finished my homework.",
        "options": ["has", "have", "had", "having"],
        "answer": "have",
        "explanation": "Present Perfect uses has/have + past participle."
    },
    {
        "id": 4,
        "topic": "present perfect continuous",
        "difficulty": "medium",
        "question": "She ___ been studying for two hours.",
        "options": ["have", "has", "is", "was"],
        "answer": "has",
        "explanation": "Present Perfect Continuous uses has/have + been + verb-ing."
    },
    {
        "id": 5,
        "topic": "past simple",
        "difficulty": "easy",
        "question": "We ___ the museum yesterday.",
        "options": ["visit", "visits", "visited", "visiting"],
        "answer": "visited",
        "explanation": "Past Simple uses the past form of the verb. Yesterday indicates past time."
    },
    {
        "id": 6,
        "topic": "past continuous",
        "difficulty": "easy",
        "question": "I ___ watching television at 8 PM.",
        "options": ["am", "is", "was", "were"],
        "answer": "was",
        "explanation": "Past Continuous uses was/were + verb-ing."
    },
    {
        "id": 7,
        "topic": "past perfect",
        "difficulty": "medium",
        "question": "The train ___ left before we arrived.",
        "options": ["has", "have", "had", "was"],
        "answer": "had",
        "explanation": "Past Perfect uses had + past participle."
    },
    {
        "id": 8,
        "topic": "past perfect continuous",
        "difficulty": "medium",
        "question": "He ___ been working for three hours before lunch.",
        "options": ["has", "have", "had", "is"],
        "answer": "had",
        "explanation": "Past Perfect Continuous uses had been + verb-ing."
    },
    {
        "id": 9,
        "topic": "future simple",
        "difficulty": "hard",
        "question": "I ___ help you tomorrow.",
        "options": ["will", "was", "have", "am"],
        "answer": "will",
        "explanation": "Future Simple commonly uses will + base form of the verb."
    },
    {
        "id": 10,
        "topic": "future continuous",
        "difficulty": "hard",
        "question": "This time tomorrow, we ___ travelling.",
        "options": ["will be", "will have", "are", "were"],
        "answer": "will be",
        "explanation": "Future Continuous uses will be + verb-ing."
    },
    {
        "id": 11,
        "topic": "future perfect",
        "difficulty": "hard",
        "question": "By Monday, she ___ completed the project.",
        "options": ["will", "will have", "has", "had"],
        "answer": "will have",
        "explanation": "Future Perfect uses will have + past participle."
    },
    {
        "id": 12,
        "topic": "future perfect continuous",
        "difficulty": "hard",
        "question": "By June, I ___ have been living here for five years.",
        "options": ["will", "will have", "have", "had"],
        "answer": "will",
        "explanation": "The complete structure is will have been + verb-ing."
    },
]


# =========================================================
# 2. CONFIGURATION
# =========================================================

PROGRESS_FILE = Path(__file__).with_name("grammar_progress.json")

DEFAULT_PROGRESS = {
    "total_quizzes": 0,
    "total_questions": 0,
    "correct_answers": 0,
    "incorrect_answers": 0,
    "topics": {},
    "history": [],
}


# =========================================================
# 3. ANSWER NORMALIZATION
# =========================================================

def normalize_answer(value):
    """Normalize an answer for comparison."""

    value = str(value).strip().casefold()
    value = re.sub(r"[.!?]+$", "", value)

    return re.sub(r"\s+", " ", value)


# =========================================================
# 4. TOPIC AND DIFFICULTY INFORMATION
# =========================================================

def get_topics():
    """Return all available grammar topics."""

    return sorted({
        question["topic"]
        for question in QUESTION_BANK
    })


def get_difficulties():
    """Return available difficulty levels."""

    return ["easy", "medium", "hard"]


# =========================================================
# 5. QUIZ GENERATOR
# =========================================================

def create_quiz(
    count=5,
    topic=None,
    shuffle=True,
    difficulty=None
):
    """Create a quiz filtered by topic and difficulty."""

    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        raise ValueError("count must be a positive integer")

    questions = list(QUESTION_BANK)

    if topic:
        topic = normalize_answer(topic)

        questions = [
            q for q in questions
            if q["topic"] == topic
        ]

    if difficulty:
        difficulty = normalize_answer(difficulty)

        if difficulty not in get_difficulties():
            raise ValueError(
                "difficulty must be easy, medium, or hard"
            )

        questions = [
            q for q in questions
            if q["difficulty"] == difficulty
        ]

    if not questions:
        return []

    if shuffle:
        random.shuffle(questions)

    selected = questions[:min(count, len(questions))]

    # Never expose correct answers in quiz questions.
    return [
        {
            "id": q["id"],
            "topic": q["topic"],
            "difficulty": q["difficulty"],
            "question": q["question"],
            "options": list(q["options"]),
        }
        for q in selected
    ]


# =========================================================
# 6. ANSWER CHECKER
# =========================================================

def check_answer(question_id, user_answer):
    """Check one answer and return feedback."""

    try:
        question_id = int(question_id)
    except (TypeError, ValueError):
        return {
            "valid": False,
            "message": "Invalid question ID."
        }

    question = next(
        (
            q for q in QUESTION_BANK
            if q["id"] == question_id
        ),
        None
    )

    if question is None:
        return {
            "valid": False,
            "message": "Question not found."
        }

    correct = (
        normalize_answer(user_answer)
        == normalize_answer(question["answer"])
    )

    return {
        "valid": True,
        "correct": correct,
        "topic": question["topic"],
        "difficulty": question["difficulty"],
        "correct_answer": question["answer"],
        "explanation": question["explanation"],
        "feedback": (
            "Correct!"
            if correct
            else "Not quite. Review the explanation."
        )
    }


# =========================================================
# 7. QUIZ GRADING
# =========================================================

def grade_quiz(answers):
    """Grade submitted quiz answers."""

    if not isinstance(answers, dict):
        raise TypeError("answers must be a dictionary")

    results = []
    correct_count = 0

    for question_id, user_answer in answers.items():

        result = check_answer(question_id, user_answer)

        if not result["valid"]:
            continue

        if result["correct"]:
            correct_count += 1

        results.append({
            "question_id": int(question_id),
            "your_answer": str(user_answer),
            **result
        })

    total = len(results)

    percentage = (
        round((correct_count / total) * 100, 2)
        if total else 0
    )

    return {
        "total": total,
        "correct": correct_count,
        "incorrect": total - correct_count,
        "percentage": percentage,
        "results": results,
    }


# =========================================================
# 8. TOPIC PERFORMANCE
# =========================================================

def get_topic_performance(report):
    """Calculate performance grouped by topic."""

    performance = {}

    for result in report.get("results", []):

        topic = result["topic"]

        if topic not in performance:
            performance[topic] = {
                "total": 0,
                "correct": 0,
                "incorrect": 0
            }

        performance[topic]["total"] += 1

        if result["correct"]:
            performance[topic]["correct"] += 1
        else:
            performance[topic]["incorrect"] += 1

    return performance


# =========================================================
# 9. LOAD SAVED PROGRESS
# =========================================================

def load_progress():
    """Load saved grammar progress."""

    if not PROGRESS_FILE.exists():
        return {
            **DEFAULT_PROGRESS,
            "topics": {},
            "history": [],
        }

    try:
        with PROGRESS_FILE.open(
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError(
                "Progress file must contain a JSON object."
            )

        for key, default_value in DEFAULT_PROGRESS.items():

            if key not in data:
                data[key] = (
                    {}
                    if isinstance(default_value, dict)
                    else []
                    if isinstance(default_value, list)
                    else default_value
                )

        if not isinstance(data["topics"], dict):
            raise ValueError("Invalid topics data.")

        if not isinstance(data["history"], list):
            raise ValueError("Invalid history data.")

        return data

    except (json.JSONDecodeError, OSError, ValueError) as error:

        raise RuntimeError(
            f"Could not safely read progress file: {error}"
        ) from error


# =========================================================
# 10. SAVE QUIZ PROGRESS
# =========================================================


def get_next_difficulty(current, percentage):
    """Recommend the next difficulty using quiz performance."""

    levels = ["easy", "medium", "hard"]

    if current not in levels:
        current = "easy"

    index = levels.index(current)

    if percentage >= 80:
        index = min(index + 1, len(levels) - 1)

    elif percentage <= 40:
        index = max(index - 1, 0)

    return levels[index]


def save_progress(report):
    """Save quiz progress and adaptive difficulty."""

    data = load_progress()

    total = report["total"]
    correct = report["correct"]
    incorrect = report["incorrect"]

    # Determine the difficulty of this quiz.
    difficulties = {
        result["difficulty"]
        for result in report["results"]
    }

    current_difficulty = (
        next(iter(difficulties))
        if len(difficulties) == 1
        else "easy"
    )

    next_difficulty = get_next_difficulty(
        current_difficulty,
        report["percentage"]
    )

    data["total_quizzes"] += 1
    data["total_questions"] += total
    data["correct_answers"] += correct
    data["incorrect_answers"] += incorrect

    # Update topic performance.
    topic_stats = data.setdefault("topics", {})

    for topic, stats in get_topic_performance(report).items():

        saved = topic_stats.setdefault(
            topic,
            {
                "total": 0,
                "correct": 0,
                "incorrect": 0
            }
        )

        saved["total"] += stats["total"]
        saved["correct"] += stats["correct"]
        saved["incorrect"] += stats["incorrect"]

    # Save adaptive difficulty.
    data["recommended_difficulty"] = next_difficulty

    history = data.setdefault("history", [])

    history.append({
        "date": datetime.now(timezone.utc).isoformat(),
        "score": correct,
        "total": total,
        "percentage": report["percentage"],
        "difficulty": current_difficulty,
        "next_difficulty": next_difficulty
    })

    data["history"] = history[-100:]

    temporary_file = PROGRESS_FILE.with_suffix(".tmp")

    with temporary_file.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )

    temporary_file.replace(PROGRESS_FILE)

    print(
        f"\nRayX recommends your next level: "
        f"{next_difficulty.upper()}"
    )

    return data



# =========================================================
# 11. DISPLAY SAVED PROGRESS
# =========================================================

def show_saved_progress():
    """Display saved overall and topic-wise progress."""

    data = load_progress()

    total = data["total_questions"]
    correct = data["correct_answers"]

    accuracy = (
        round((correct / total) * 100, 2)
        if total else 0
    )

    print("\n===== RAYX SAVED PROGRESS =====")

    print("Quizzes attempted:", data["total_quizzes"])
    print("Questions answered:", total)
    print("Correct answers:", correct)
    print("Incorrect answers:", data["incorrect_answers"])
    print("Overall accuracy:", f"{accuracy}%")

    print("\n===== TOPIC-WISE PROGRESS =====")

    if not data["topics"]:
        print("No topic progress yet.")

    else:
        for topic, stats in data["topics"].items():

            print(
                f"{topic}: "
                f"{stats['correct']}/{stats['total']} correct"
            )


# =========================================================
# 12. INTERACTIVE QUIZ
# =========================================================

def run_interactive_quiz(
    count=5,
    topic=None,
    difficulty=None
):
    """Run an interactive quiz with instant feedback."""

    quiz = create_quiz(
        count=count,
        topic=topic,
        difficulty=difficulty
    )

    if not quiz:
        print("No questions found for these filters.")
        return None

    answers = {}
    live_score = 0

    print("\nRayX Grammar Practice")
    print("=====================")
    print("Questions:", len(quiz))
    print("Instant feedback: ON")

    for position, question in enumerate(quiz, start=1):

        print("\n" + "=" * 45)
        print(f"Question {position}/{len(quiz)}")

        print(
            f"\n{question['id']}. "
            f"[{question['difficulty'].upper()} | "
            f"{question['topic']}]"
        )

        print(question["question"])

        for index, option in enumerate(
            question["options"],
            start=1
        ):
            print(f"  {index}. {option}")

        choice = input(
            "\nYour answer (option number or answer): "
        ).strip()

        if choice.isdigit():
            number = int(choice)

            if 1 <= number <= len(question["options"]):
                choice = question["options"][number - 1]

        answers[question["id"]] = choice

        # Instant answer checking.
        result = check_answer(
            question["id"],
            choice
        )

        print("\n----- RAYX FEEDBACK -----")

        if result["correct"]:
            live_score += 1
            print("Result: CORRECT!")
        else:
            print("Result: INCORRECT")

        print("Your answer:", choice)
        print("Correct answer:", result["correct_answer"])
        print("Explanation:", result["explanation"])

        print(f"Live score: {live_score}/{position}")

    # Final grading.
    report = grade_quiz(answers)

    print("\n" + "=" * 45)
    print("RAYX FINAL RESULT")
    print("=" * 45)

    print(f"Score: {report['correct']}/{report['total']}")
    print(f"Percentage: {report['percentage']}%")
    print("Correct answers:", report["correct"])
    print("Incorrect answers:", report["incorrect"])

    # Topic performance.
    print("\n===== CURRENT QUIZ PERFORMANCE =====")

    for topic_name, stats in get_topic_performance(report).items():
        print(
            f"{topic_name}: "
            f"{stats['correct']}/{stats['total']} correct"
        )

    # Save progress.
    save_progress(report)

    print("\nProgress saved successfully!")

    # Show saved progress.
    show_saved_progress()

    return report


# =========================================================
# 13. MAIN PROGRAM
# =========================================================


if __name__ == "__main__":

    print("\nRAYX GRAMMAR PRACTICE")
    print("====================")

    progress = load_progress()

    recommended = progress.get(
        "recommended_difficulty",
        "easy"
    )

    if recommended not in get_difficulties():
        recommended = "easy"

    print("\nRayX Adaptive Learning: ON")
    print("Recommended level:", recommended.upper())

    choice = input(
        "\nUse recommended level? (yes/no): "
    ).strip().lower()

    if choice in ("no", "n"):

        print(
            "\nAvailable levels:",
            ", ".join(get_difficulties())
        )

        level = input(
            "Choose difficulty: "
        ).strip().lower()

        if level not in get_difficulties():
            print("Invalid level. Using recommended level.")
            level = recommended

    else:
        level = recommended

    run_interactive_quiz(
        count=5,
        difficulty=level
    )
