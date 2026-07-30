"""
tests/test_skills.py - Unit tests for skills.py
------------------------------------------------
Tests skill extraction regex accuracy, boundary matching,
and skill gap analysis calculations.
"""

import unittest
import os
import json
from skills import extract_skills, compare_skills, load_skills_db, format_skill_report

class TestSkills(unittest.TestCase):

    def setUp(self):
        self.sample_dir = os.path.join(os.path.dirname(__file__), "..", "sample_data")
        self.resume_path = os.path.join(self.sample_dir, "sample_resume.txt")
        self.jd_path = os.path.join(self.sample_dir, "sample_jd.txt")

        with open(self.resume_path, 'r', encoding='utf-8') as f:
            self.resume_text = f.read()

        with open(self.jd_path, 'r', encoding='utf-8') as f:
            self.jd_text = f.read()

    def test_load_skills_db(self):
        """Test loading skills database taxonomy JSON."""
        db = load_skills_db()
        self.assertIn("Programming Languages", db)
        self.assertIn("Web Development", db)
        self.assertIn("Databases", db)
        self.assertIn("Cloud & DevOps", db)
        self.assertIn("Computer Science Fundamentals", db)

    def test_extract_skills_from_resume(self):
        """Test extracting skills from sample resume text."""
        result = extract_skills(self.resume_text)
        found_skills = result["all_skills"]

        # Check core skills present in sample resume
        self.assertIn("Python", found_skills)
        self.assertIn("JavaScript", found_skills)
        self.assertIn("TypeScript", found_skills)
        self.assertIn("C++", found_skills)
        self.assertIn("React", found_skills)
        self.assertIn("FastAPI", found_skills)
        self.assertIn("PostgreSQL", found_skills)
        self.assertIn("Docker", found_skills)
        self.assertIn("PyTorch", found_skills)
        self.assertIn("Git", found_skills)

    def test_regex_boundary_accuracy(self):
        """Test that regex boundary matching avoids false positive substrings (e.g. Java inside JavaScript)."""
        # Test 1: Text contains JavaScript only
        text_js_only = "Candidate knows JavaScript and CSS."
        res_js = extract_skills(text_js_only)
        self.assertIn("JavaScript", res_js["all_skills"])
        self.assertNotIn("Java", res_js["all_skills"])

        # Test 2: Text contains C++ and C# only
        text_cpp_cs = "Experience with C++ and C# backend services."
        res_cpp = extract_skills(text_cpp_cs)
        self.assertIn("C++", res_cpp["all_skills"])
        self.assertIn("C#", res_cpp["all_skills"])
        self.assertNotIn("C", res_cpp["all_skills"])

        # Test 3: Standalone C
        text_standalone_c = "Strong in C programming and Linux kernel."
        res_c = extract_skills(text_standalone_c)
        self.assertIn("C", res_c["all_skills"])

    def test_compare_skills_gap_analysis(self):
        """Test skill comparison between resume and job description."""
        comparison = compare_skills(self.resume_text, self.jd_text)

        # Check returned dictionary structure and new statistical fields
        self.assertIn("matching_skills", comparison)
        self.assertIn("missing_skills", comparison)
        self.assertIn("additional_skills", comparison)
        self.assertIn("matched_count", comparison)
        self.assertIn("missing_count", comparison)
        self.assertIn("additional_count", comparison)
        self.assertIn("total_required_skills", comparison)
        self.assertIn("skill_match_percentage", comparison)

        # Verify counts match length of lists
        self.assertEqual(comparison["matched_count"], len(comparison["matching_skills"]))
        self.assertEqual(comparison["missing_count"], len(comparison["missing_skills"]))
        self.assertEqual(comparison["additional_count"], len(comparison["additional_skills"]))

        # Matching skills between sample resume & sample JD
        self.assertIn("Python", comparison["matching_skills"])
        self.assertIn("React", comparison["matching_skills"])
        self.assertIn("Docker", comparison["matching_skills"])

        # Match percentage should be positive float
        self.assertGreater(comparison["skill_match_percentage"], 0.0)
        self.assertLessEqual(comparison["skill_match_percentage"], 100.0)

    def test_format_skill_report(self):
        """Test text report generation function."""
        comparison = compare_skills(self.resume_text, self.jd_text)
        report = format_skill_report(comparison)
        self.assertIn("TECHNICAL SKILL GAP REPORT", report)
        self.assertIn("Matching Skills", report)
        self.assertIn("Missing Skills", report)

if __name__ == "__main__":
    unittest.main()
