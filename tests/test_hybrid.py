import unittest

from rayx_math_engine import solve_math
from rayx_knowledge import search_knowledge
from rayx_hybrid import answer_question


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
        result = answer_question("2+2+6", generate_answer=lambda *args: "wrong")
        self.assertEqual(result["source"], "calculator")
        self.assertIn("= 10", result["answer"])


if __name__ == "__main__":
    unittest.main()
