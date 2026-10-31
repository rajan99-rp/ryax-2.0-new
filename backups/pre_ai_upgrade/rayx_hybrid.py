import re
from difflib import get_close_matches

from rayx_math_engine import solve_math
from rayx_knowledge import search_knowledge
from rayx_validator import validate_answer
from rayx_english_grammar import answer_grammar_question
from rayx_grammar_checker import check_grammar
from rayx_sentence_parser import analyse_sentence


INCOMPLETE_MATH_MESSAGE = (
    "This math expression looks incomplete. "
    "Please finish the expression and try again."
)

UNRELIABLE_ANSWER_MESSAGE = (
    "I couldn't produce a reliable answer yet. "
    "My local model needs more training and better language data."
)

UNCLEAR_INPUT_MESSAGE = (
    "I couldn't understand that input. "
    "Please rephrase it or give me a little more context."
)


def _result(answer, source, verified=False, details=""):
    return {
        "answer": answer,
        "source": source,
        "verified": verified,
        "details": details,
    }


def _normalize(text):
    text = str(text).casefold().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------
# 1. LOCAL CONVERSATION ENGINE
# ---------------------------------------------------------

def _local_chat_response(question):
    text = _normalize(question)

    aliases = {
        "hlo": "hello",
        "helo": "hello",
        "heyy": "hey",
        "heyyy": "hey",
        "hii": "hi",
        "hiii": "hi",
        "hy": "hi",
        "hyyy": "hi",
        "namaste ji": "namaste",
        "wgo are you": "who are you",
        "who r u": "who are you",
        "who r you": "who are you",
        "whos are you": "who are you",
        "name kya h": "what is your name",
        "tumhara naam kya h": "what is your name",
        "aapka naam kya h": "what is your name",
        "kya kar skte ho": "what can you do",
        "kya kar sakte ho": "what can you do",
        "kaise ho": "how are you",
        "kaisa hai": "how are you",
        "kaise hain": "how are you",
        "kya haal hai": "how are you",
        "thx": "thanks",
        "shukriya": "thanks",
        "are u fine": "are you fine",
        "r u fine": "are you fine",
        "are you ok": "are you fine",
        "are you okay": "are you fine",
        "you fine": "are you fine",
        "how r u": "how are you",
    }

    text = aliases.get(text, text)

    # Laughter and casual reactions
    laughter_inputs = {
        "haha", "hahaha", "hahahaha", "haahaa",
        "hehe", "hehehe", "lol", "lmao",
        "rofl", "😂", "🤣"
    }
        # Casual Hinglish conversation
    casual_responses = {
        "allu khaoge": (
            "Haha! 😄 Main AI hoon, kha nahi sakta. "
            "Lekin aloo ki recipe zaroor bata sakta hoon!"
        ),
        "aloo khaoge": (
            "Haha! 😄 Main AI hoon, kha nahi sakta. "
            "Lekin aloo ki recipe zaroor bata sakta hoon!"
        ),
        "chai piyoge": (
            "Main chai nahi pee sakta, par chai par baat zaroor kar sakte hain! ☕"
        ),
        "kya khaoge": (
            "Main AI hoon, khana nahi kha sakta. 😄"
        ),
        "kya kar rahe ho": (
            "Tumhari help ke liye ready hoon! Batao kya karna hai?"
        ),
        "bore ho raha hu": (
            "Chalo kuch interesting karte hain! Coding, science ya koi game?"
        ),
    }

    if text in casual_responses:
        return _result(
            casual_responses[text],
            "local_chat",
            verified=True,
            details="Recognized casual Hinglish conversation"
        )

    if text in laughter_inputs:
        return _result(
            "Haha! 😄 What's so funny?",
            "local_chat",
            verified=True,
            details="Recognized laughter"
        )

    # Common conversational phrases
    known_phrases = [
        "who are you",
        "what is your name",
        "how are you",
        "are you fine",
        "what can you do",
        "who am i",
        "good morning",
        "good afternoon",
        "good evening",
    ]

    if text not in known_phrases:
        matches = get_close_matches(
            text,
            known_phrases,
            n=1,
            cutoff=0.88
        )
        if matches:
            text = matches[0]

    greetings = {
        "hi", "hello", "hey", "hey there",
        "hi there", "hello there",
        "namaste", "namaskar"
    }

    if text in greetings:
        return _result(
            "Hey! How can I help you today?",
            "local_greeting",
            verified=True,
            details="Local greeting response"
        )

    if text in {"good morning", "good afternoon", "good evening"}:
        return _result(
            f"{text.title()}! What would you like to work on?",
            "local_chat",
            verified=True,
            details="Time-based greeting"
        )

    if text in {"how are you", "are you fine"}:
        return _result(
            "I'm working properly and ready to help! "
            "What would you like to explore?",
            "local_chat",
            verified=True,
            details="Local conversational response"
        )

    if text in {"who are you", "what are you"}:
        return _result(
            "I am RayX, a local AI assistant designed to help "
            "with learning, coding, mathematics and problem solving.",
            "local_identity",
            verified=True,
            details="RayX identity response"
        )

    if text in {"what is your name", "your name", "tell me your name"}:
        return _result(
            "My name is RayX.",
            "local_identity",
            verified=True,
            details="RayX name response"
        )

    if text == "who am i":
        return _result(
            "I don't know your identity unless you tell me. "
            "You can tell me what name you'd like me to use.",
            "identity_clarification",
            verified=True,
            details="Does not assume the user's identity"
        )

    if text == "what can you do":
        return _result(
            "I can help with programming, science, mathematics, "
            "English grammar, explanations and creative writing. "
            "I can also retrieve information from my local knowledge base.",
            "local_capabilities",
            verified=True,
            details="RayX capabilities response"
        )

    if text in {"thanks", "thank you", "thankyou"}:
        return _result(
            "You're welcome! What shall we work on next?",
            "local_chat",
            verified=True,
            details="Local acknowledgement"
        )

    if text in {"bye", "goodbye", "see you", "alvida"}:
        return _result(
            "Goodbye! Take care.",
            "local_chat",
            verified=True,
            details="Local goodbye response"
        )

    if text in {
        "ek shayeri likho",
        "ek shayari likho",
        "shayari likho",
        "write a shayari",
        "write a poem",
        "ek poem likho",
    }:
        return _result(
            "Manzil mile ya raaste badal jaayein,\n"
            "Hausle apne kabhi kam na ho paayein.\n"
            "Har nayi subah ek umeed laaye,\n"
            "Mehnat se apne sapne sach ho jaayein.",
            "local_creative",
            verified=True,
            details="Original local shayari"
        )

    return None


# ---------------------------------------------------------
# 2. LOCAL FILL-IN-THE-BLANK ENGINE
# ---------------------------------------------------------

def _local_completion(question):
    text = str(question).casefold().strip()
    text = re.sub(r"\s+", " ", text)

    # Small starter set. Add more verified examples over time.
    completions = {
        "mango is a": "Mango is a fruit.",
        "the sun is a": "The Sun is a star.",
        "the earth is a": "The Earth is a planet.",
        "water is a": "Water is a substance made of hydrogen and oxygen.",
        "python is a": "Python is a programming language.",
    }

    cleaned = re.sub(r"[_ .]+$", "", text).strip()

    if cleaned in completions:
        return _result(
            completions[cleaned],
            "local_completion",
            verified=True,
            details="Matched a stored fill-in-the-blank fact"
        )

    return None


# ---------------------------------------------------------
# 3. INPUT QUALITY CHECK
# ---------------------------------------------------------

def _input_is_unclear(question):
    text = _normalize(question)

    if not text:
        return True

    words = text.split()

    # Detect a greeting followed by a likely random word.
    greeting_words = {
        "hi", "hello", "hey", "hlo", "helo",
        "hii", "namaste", "namaskar"
    }

    if len(words) >= 2 and words[0] in greeting_words:
        remainder = "".join(words[1:])

        if len(remainder) >= 5:
            vowels = sum(char in "aeiou" for char in remainder)

            if vowels / len(remainder) < 0.15:
                return True

    # Be conservative with single-word inputs.
    # Do not reject normal subject words such as "photosynthesis".
    if len(words) == 1:
        word = words[0]

        if len(word) >= 8 and word.isalpha():
            vowels = sum(char in "aeiou" for char in word)

            if vowels == 0:
                return True

    return False


# ---------------------------------------------------------
# 4. MATH INPUT CHECK
# ---------------------------------------------------------

def _is_incomplete_math(question):
    text = question.strip()

    if not text or not re.search(r"\d", text):
        return False

    if not re.fullmatch(r"[\d\s().,+*/%^\\-]+", text):
        return False

    compact = re.sub(r"\s+", "", text)

    return compact.endswith(("+", "-", "*", "/", "^", "%", "."))


# ---------------------------------------------------------
# 5. NEURAL OUTPUT QUALITY CHECK
# ---------------------------------------------------------

def _looks_like_gibberish(text):
    """
    Heuristic checks for obviously malformed model output.
    It cannot determine whether an answer is factually correct.
    """
    text = str(text).strip()

    if len(text) < 3:
        return True

    lowered = text.casefold()

    # Training-data or model-token leakage
    if re.search(
        r"###\s*(user|rayx|end)\b|<\|[^>]+\|>",
        lowered
    ):
        return True

    words = re.findall(r"[A-Za-z]+", text)

    if not words:
        return False

    # Suspiciously long words with no vowels or long consonant runs
    suspicious_words = 0

    for word in words:
        word_lower = word.casefold()

        if len(word_lower) >= 8:
            vowel_count = sum(c in "aeiou" for c in word_lower)

            if vowel_count == 0:
                suspicious_words += 1

        if re.search(r"[bcdfghjklmnpqrstvwxyz]{6,}", word_lower):
            suspicious_words += 1

    if suspicious_words >= 2:
        return True

    # Excessive repeated words
    normalized_words = [word.casefold() for word in words]

    if len(normalized_words) >= 12:
        unique_ratio = len(set(normalized_words)) / len(normalized_words)

        if unique_ratio < 0.40:
            return True

    # Repeated short phrases
    if re.search(r"\b(\w+(?:\s+\w+){0,2})\b(?:\s+\1\b){2,}", lowered):
        return True

    # Too many malformed long words
    if len(words) >= 8:
        unusual = sum(
            1 for word in words
            if len(word) >= 7
            and sum(c in "aeiou" for c in word.casefold()) <= 1
        )

        if unusual / len(words) > 0.30:
            return True

    return False


# ---------------------------------------------------------
# 6. MAIN RAYX ROUTER
# ---------------------------------------------------------

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

    # 1. Local conversation
    local_response = _local_chat_response(question)

    if local_response is not None:
        return local_response

    # 2. Fill in the blanks
    completion = _local_completion(question)

    if completion is not None:
        return completion

    # 3. Reject obvious unclear input
    if _input_is_unclear(question):
        return _result(
            UNCLEAR_INPUT_MESSAGE,
            "input_guard",
            verified=False,
            details="Input appears incomplete or unclear"
        )

    # 4. English grammar lessons
    try:
        grammar_result = answer_grammar_question(question)
    except Exception:
        grammar_result = None

    if grammar_result is not None:
        return _result(
            grammar_result["answer"],
            "grammar_engine",
            verified=grammar_result.get("verified", False),
            details=f"Grammar topic: {grammar_result.get('topic', 'General')}"
        )

    # 5. English sentence correction
    try:
        correction = check_grammar(question)
    except Exception:
        correction = None

    if correction and correction.get("status") == "corrected":
        try:
            analysis = correction.get("analysis") or analyse_sentence(question)
        except Exception:
            analysis = {}

        return _result(
            correction["explanation"],
            "grammar_checker",
            verified=correction.get("verified", False),
            details=(
                f"Rule: {correction.get('topic', 'sentence correction')}; "
                f"Words: {analysis.get('word_count', 0)}; "
                f"Estimated tense: {analysis.get('tense', 'undetermined')}"
            )
        )

    # 6. Calculator
    try:
        math_result = solve_math(question)
    except Exception:
        math_result = None

    if math_result is not None:
        return _result(
            math_result,
            "calculator",
            verified=True,
            details="Calculated locally"
        )

    # 7. Incomplete arithmetic
    if _is_incomplete_math(question):
        return _result(
            INCOMPLETE_MATH_MESSAGE,
            "calculator",
            details="Incomplete arithmetic expression"
        )

    # 8. Local knowledge
    try:
        knowledge_result = search_knowledge(question)
    except Exception:
        knowledge_result = None

    if knowledge_result is not None:
        return _result(
            knowledge_result["answer"],
            "knowledge_base",
            verified=knowledge_result.get("verified", False),
            details=(
                f"Subject: {knowledge_result.get('subject', 'General')}; "
                f"Source: {knowledge_result.get('source', 'unspecified')}"
            )
        )

    # 9. Saved memory
    if find_memory_answer is not None:
        try:
            memory_result = find_memory_answer(question)
        except Exception:
            memory_result = None

        if isinstance(memory_result, dict):
            memory_answer = str(
                memory_result.get("answer", "")
            ).strip()

            if (
                memory_answer
                and not _looks_like_gibberish(memory_answer)
            ):
                return _result(
                    memory_answer,
                    "memory",
                    verified=False,
                    details="Retrieved from stored conversation"
                )

        # 10. Avoid unreliable neural guesses for short casual messages
    words = _normalize(question).split()

    if len(words) <= 4:
        return _result(
            "I'm not sure what you mean yet. "
            "Thoda aur context do, main better answer dene ki koshish karunga!",
            "clarification",
            verified=False,
            details="Short conversational input was not recognized"
        )

    # 11. Local neural model
    if generate_answer is None:
        return _result(
            "No local model generator is configured.",
            "none",
            details="Model generation is not configured"
        )

    try:
        generated = generate_answer(model, config, question)

    except Exception as error:
        return _result(
            "RayX could not generate an answer.",
            "error",
            details=f"Error type: {type(error).__name__}"
        )

    if not isinstance(generated, str) or not generated.strip():
        return _result(
            "No answer generated yet.",
            "none",
            details="Empty model response"
        )

    generated = generated.strip()

    if _looks_like_gibberish(generated):
        return _result(
            UNRELIABLE_ANSWER_MESSAGE,
            "neural_model",
            verified=False,
            details="Rejected: output appears linguistically malformed"
        )

    try:
        validation = validate_answer(question, generated)

    except Exception as error:
        return _result(
            UNRELIABLE_ANSWER_MESSAGE,
            "neural_model",
            verified=False,
            details=f"Answer validation failed: {type(error).__name__}"
        )

    if not validation.accepted:
        warnings = validation.warnings or ["Quality checks failed"]

        return _result(
            UNRELIABLE_ANSWER_MESSAGE,
            "neural_model",
            verified=False,
            details=f"Rejected output: {'; '.join(warnings)}"
        )

    return _result(
        generated,
        "neural_model",
        verified=False,
        details=(
            "Generated locally; not independently verified. "
            "Passing basic checks does not guarantee correctness."
        )
    )





if __name__ == "__main__":
    print("RayX Hybrid Router loaded successfully.")