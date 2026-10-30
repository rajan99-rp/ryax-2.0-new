
import unittest

from rayx_math_engine import solve_math
from rayx_knowledge import search_knowledge
from rayx_hybrid import answer_question, INCOMPLETE_MATH_MESSAGE


class RayXHybridTests(unittest.TestCase):
    def test_math_hinglish(self):
        result = solve_math("2+2+6 kitna hota h")
        self.assertIsNotNone(result)
        self.assertTrue(result.endswith("= 10"))

    def test_division_by_zero_is_not_answered(self):
        self.assertIsNone(solve_math("10 / 0"))

    def test_knowledge_lookup(self):
        result = search_knowledge("What is photosynthesis?")
        self.assertIsNotNone(result)
        self.assertIn("plants", result["answer"].lower())

    def test_hybrid_calculator_route(self):
        result = answer_question(
            "2+2+6",
            generate_answer=lambda *args: "wrong",
        )
        self.assertEqual(result["source"], "calculator")
        self.assertIn("= 10", result["answer"])

    def test_incomplete_math_is_rejected(self):
        result = answer_question(
            "5652154-86535+56886599+95959+",
            generate_answer=lambda *args: "random text",
        )
        self.assertEqual(result["source"], "calculator")
        self.assertEqual(result["answer"], INCOMPLETE_MATH_MESSAGE)

    def test_known_gibberish_is_rejected(self):
        result = answer_question(
            "Explain quantum mechanics in detail",
            generate_answer=lambda *args: "blve blve prilt asult",
        )
        self.assertEqual(result["source"], "neural_model")
        self.assertIn("reliable answer", result["answer"].lower())
        self.assertIn("Known gibberish test pattern", result["details"])

    def test_valid_short_neural_answer_is_accepted(self):
        result = answer_question(
            "Give me a greeting",
            generate_answer=lambda *args: "Hello! How are you today?",
        )
        self.assertEqual(result["source"], "neural_model")
        self.assertEqual(result["answer"], "Hello! How are you today?")
        self.assertFalse(result["verified"])


if __name__ == "__main__":
    unittest.main()
