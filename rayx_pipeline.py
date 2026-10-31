
from dataclasses import dataclass, field

from rayx_understanding import understand
from rayx_context import RayXContext
from rayx_knowledge import search_knowledge
from rayx_validator_v2 import validate_answer


@dataclass
class PipelineResult:
    answer: str
    source: str
    accepted: bool
    validation_score: int
    warnings: list = field(default_factory=list)


class RayXPipeline:

    def __init__(self):
        self.context = RayXContext()

    def process(self, user_input: str) -> PipelineResult:

        user_input = user_input.strip()

        if not user_input:
            return PipelineResult(
                "Please enter a message.",
                "input_check",
                False,
                0,
                ["Empty input"]
            )

        # STEP 1: Understand input
        understanding = understand(user_input)
        intent = understanding["intent"]

        # STEP 2: Handle conversation intents
        if intent == "greeting":
            answer = "Hello! Main RayX hoon. Kaise help kar sakta hoon?"
            self.context.add_message("user", user_input)
            self.context.add_message("assistant", answer)

            return PipelineResult(
                answer, "greeting", True, 100, []
            )

        if intent == "thanks":
            return PipelineResult(
                "You're welcome!",
                "conversation",
                True,
                100,
                []
            )

        if intent == "goodbye":
            return PipelineResult(
                "Goodbye! Phir milte hain.",
                "conversation",
                True,
                100,
                []
            )

        if intent == "unclear":
            return PipelineResult(
                "I couldn't understand that. Please rephrase your message.",
                "input_check",
                False,
                0,
                ["Input appears unclear"]
            )

        if intent in ("short_question", "empty"):
            return PipelineResult(
                "Apna complete question likho, main samajhne ki koshish karunga.",
                "clarification",
                False,
                0,
                ["Incomplete question"]
            )

        # STEP 3: Save user message
        self.context.add_message("user", user_input)

        # STEP 4: Search local knowledge
        result = search_knowledge(user_input)

        if isinstance(result, dict):
            answer = result.get("answer", "")
        elif result:
            answer = str(result)
        else:
            answer = ""

        if not answer:
            answer = (
                "I don't have a reliable answer for this question "
                "in my current local knowledge."
            )
            source = "knowledge_not_found"
        else:
            source = "local_knowledge"

        # STEP 5: Validate response
        validation = validate_answer(user_input, answer)

        # STEP 6: Save accepted response
        if validation.accepted:
            self.context.add_message("assistant", answer)

        return PipelineResult(
            answer=answer,
            source=source,
            accepted=validation.accepted,
            validation_score=validation.score,
            warnings=validation.warnings
        )

    def clear_context(self):
        self.context.clear()


if __name__ == "__main__":

    rayx = RayXPipeline()

    print("RayX Pipeline Ready. Type 'exit' to stop.")

    while True:
        question = input("\nYou: ").strip()

        if question.lower() == "exit":
            break

        result = rayx.process(question)

        print("\nRayX:", result.answer)
        print("Source:", result.source)
        print("Accepted:", result.accepted)
        print("Heuristic score:", result.validation_score)

        if result.warnings:
            print("Warnings:", result.warnings)
