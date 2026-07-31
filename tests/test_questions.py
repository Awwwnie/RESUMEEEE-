"""
tests/test_questions.py - Unit tests for questions.py
------------------------------------------------------------------
"""

import unittest
from questions import (
    generate_questions_for_skill,
    generate_interview_questions,
    format_questions_report,
)


class TestQuestions(unittest.TestCase):

    def test_generate_questions_for_matched_skill(self):
        """Matched skill should produce technical_verification type questions."""
        result = generate_questions_for_skill("Python", is_missing=False)
        self.assertEqual(result["type"], "technical_verification")
        self.assertTrue(len(result["questions"]) >= 1)
        self.assertEqual(result["skill"], "Python")

    def test_generate_questions_for_missing_skill(self):
        """Missing skill should produce missing_skill_probe type questions."""
        result = generate_questions_for_skill("Kubernetes", is_missing=True)
        self.assertEqual(result["type"], "missing_skill_probe")
        self.assertTrue(len(result["questions"]) >= 1)

    def test_skill_specific_templates_used(self):
        """Skills with dedicated templates should use them instead of generic ones."""
        result = generate_questions_for_skill("SQL", is_missing=False)
        self.assertIn(
            "Write a query approach to find duplicate rows in a table.",
            result["questions"]
        )

    def test_generate_interview_questions_respects_limits(self):
        """Question generation should respect max_matching and max_missing caps."""
        matching = ["Python", "SQL", "Git", "React", "Docker", "AWS"]
        missing = ["Kubernetes", "Terraform", "GraphQL", "Redis"]

        result = generate_interview_questions(
            matching, missing, max_matching=2, max_missing=1
        )
        self.assertEqual(len(result["technical_questions"]), 2)
        self.assertEqual(len(result["gap_probe_questions"]), 1)
        self.assertGreater(result["total_questions"], 0)

    def test_generate_interview_questions_empty_lists(self):
        """Empty skill lists should not raise errors and should return zero questions."""
        result = generate_interview_questions([], [])
        self.assertEqual(result["technical_questions"], [])
        self.assertEqual(result["gap_probe_questions"], [])
        self.assertEqual(result["total_questions"], 0)

    def test_format_questions_report_contains_sections(self):
        """Formatted report should contain all expected section headers."""
        result = generate_interview_questions(["Python"], ["Docker"])
        report = format_questions_report(result)
        self.assertIn("SUGGESTED INTERVIEW QUESTIONS", report)
        self.assertIn("Technical Verification", report)
        self.assertIn("Skill Gap Probes", report)
        self.assertIn("Total Questions Generated", report)


if __name__ == "__main__":
    unittest.main()