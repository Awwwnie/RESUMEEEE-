"""
tests/test_gap_analyzer.py - Unit tests for gap_analyzer.py
--------------------------------------------------------------
"""

import unittest
import os
from gap_analyzer import (
    categorize_missing_skills,
    get_readiness_level,
    get_priority_recommendations,
    analyze_skill_gap,
    format_gap_report,
)


class TestGapAnalyzer(unittest.TestCase):

    def setUp(self):
        self.sample_dir = os.path.join(os.path.dirname(__file__), "..", "sample_data")
        with open(os.path.join(self.sample_dir, "sample_resume.txt"), "r", encoding="utf-8") as f:
            self.resume_text = f.read()
        with open(os.path.join(self.sample_dir, "sample_jd.txt"), "r", encoding="utf-8") as f:
            self.jd_text = f.read()

    def test_categorize_missing_skills(self):
        """Missing skills should be grouped correctly by category."""
        categorized = categorize_missing_skills(["Docker", "AWS", "Python"])
        all_skills_in_output = [s for skills in categorized.values() for s in skills]
        self.assertIn("Docker", all_skills_in_output)
        self.assertIn("AWS", all_skills_in_output)
        self.assertIn("Python", all_skills_in_output)

    def test_readiness_levels(self):
        """Readiness level should scale correctly with match percentage."""
        self.assertEqual(get_readiness_level(90)["level"], "Strong Fit")
        self.assertEqual(get_readiness_level(70)["level"], "Good Fit")
        self.assertEqual(get_readiness_level(50)["level"], "Moderate Fit")
        self.assertEqual(get_readiness_level(20)["level"], "Needs Improvement")

    def test_priority_recommendations_respects_top_n(self):
        """Recommendations list should never exceed top_n."""
        categorized_missing = {
            "Programming Languages": ["Go", "Rust"],
            "Cloud & DevOps": ["AWS", "Docker", "Kubernetes"],
        }
        recs = get_priority_recommendations(categorized_missing, top_n=3)
        self.assertLessEqual(len(recs), 3)

    def test_analyze_skill_gap_structure(self):
        """Full analysis should contain all expected keys."""
        result = analyze_skill_gap(self.resume_text, self.jd_text)
        expected_keys = [
            "skill_match_percentage", "readiness_level", "readiness_description",
            "matching_skills", "missing_skills", "additional_skills",
            "categorized_matching_skills", "categorized_missing_skills",
            "priority_recommendations", "matched_count", "missing_count",
            "total_required_skills",
        ]
        for key in expected_keys:
            self.assertIn(key, result)

    def test_format_gap_report_contains_sections(self):
        """Formatted report should include all major section headers."""
        result = analyze_skill_gap(self.resume_text, self.jd_text)
        report = format_gap_report(result)
        self.assertIn("SKILL GAP ANALYSIS REPORT", report)
        self.assertIn("Readiness Level", report)
        self.assertIn("Missing Skills by Category", report)
        self.assertIn("Top Priority Recommendations", report)


if __name__ == "__main__":
    unittest.main()