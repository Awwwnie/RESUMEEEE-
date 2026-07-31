"""
tests/test_matcher.py - Unit tests for matcher.py
--------------------------------------------------
Tests TF-IDF similarity, top keyword extraction, weight normalization,
transparent component score breakdown, and hybrid suitability scoring.
"""

import unittest
import os
from matcher import (
    compute_tfidf_similarity,
    extract_top_matching_keywords,
    calculate_hybrid_score,
    format_match_report
)

class TestMatcher(unittest.TestCase):

    def setUp(self):
        self.sample_dir = os.path.join(os.path.dirname(__file__), "..", "sample_data")
        self.resume_path = os.path.join(self.sample_dir, "sample_resume.txt")
        self.jd_path = os.path.join(self.sample_dir, "sample_jd.txt")

        with open(self.resume_path, 'r', encoding='utf-8') as f:
            self.resume_text = f.read()

        with open(self.jd_path, 'r', encoding='utf-8') as f:
            self.jd_text = f.read()

    def test_compute_tfidf_similarity_identical(self):
        """Test that identical documents yield 100% TF-IDF cosine similarity."""
        text = "Experienced Senior Python Developer with FastAPI and PostgreSQL expertise."
        res = compute_tfidf_similarity(text, text)
        self.assertEqual(res["similarity_percentage"], 100.0)
        self.assertEqual(res["similarity_score"], 1.0)
        self.assertGreater(res["vocabulary_size"], 0)

    def test_compute_tfidf_similarity_disjoint(self):
        """Test that completely disjoint texts yield 0% TF-IDF similarity."""
        text1 = "Python JavaScript React Docker Kubernetes"
        text2 = "Gardening Agriculture Organic Soil Fertilizer"
        res = compute_tfidf_similarity(text1, text2)
        self.assertEqual(res["similarity_percentage"], 0.0)
        self.assertEqual(res["similarity_score"], 0.0)

    def test_compute_tfidf_similarity_empty(self):
        """Test graceful handling of empty or whitespace input strings."""
        res = compute_tfidf_similarity("", "Python Developer")
        self.assertEqual(res["similarity_score"], 0.0)
        self.assertEqual(res["similarity_percentage"], 0.0)

    def test_extract_top_matching_keywords(self):
        """Test extracting top overlapping keywords and n-grams."""
        text1 = "Python developer experienced in Machine Learning and Data Science with PyTorch."
        text2 = "Looking for a Python engineer skilled in Machine Learning and PyTorch models."
        
        keywords = extract_top_matching_keywords(text1, text2, top_n=5)
        self.assertTrue(len(keywords) > 0)
        
        kw_names = [kw["keyword"] for kw in keywords]
        self.assertIn("python", kw_names)
        self.assertIn("machine learning", kw_names)
        
        # Verify term dictionary structure
        first_kw = keywords[0]
        self.assertIn("keyword", first_kw)
        self.assertIn("score", first_kw)
        self.assertIn("resume_tfidf", first_kw)
        self.assertIn("jd_tfidf", first_kw)

    def test_calculate_hybrid_score_transparent_breakdown(self):
        """Test calculate_hybrid_score returns transparent individual component scores."""
        res = calculate_hybrid_score(self.resume_text, self.jd_text, tfidf_weight=0.5, skill_weight=0.5)

        # Check transparent component score keys exist
        self.assertIn("hybrid_score_percentage", res)
        self.assertIn("hybrid_score", res)
        self.assertIn("tfidf_similarity_percentage", res)
        self.assertIn("tfidf_similarity_score", res)
        self.assertIn("skill_match_percentage", res)
        self.assertIn("tfidf_weight", res)
        self.assertIn("skill_weight", res)
        self.assertIn("top_matching_keywords", res)
        self.assertIn("skill_gap_analysis", res)

        # Check numeric bounds
        self.assertGreaterEqual(res["hybrid_score_percentage"], 0.0)
        self.assertLessEqual(res["hybrid_score_percentage"], 100.0)
        self.assertEqual(res["tfidf_weight"], 0.5)
        self.assertEqual(res["skill_weight"], 0.5)

        # Verify mathematical combination formula
        expected_hybrid = round((res["tfidf_similarity_percentage"] * 0.5) + (res["skill_match_percentage"] * 0.5), 2)
        self.assertEqual(res["hybrid_score_percentage"], expected_hybrid)

    def test_weight_normalization(self):
        """Test automatic weight normalization when tfidf_weight + skill_weight != 1.0."""
        # Unnormalized weights 0.6 and 1.4 -> total = 2.0 -> normalized: 0.3 and 0.7
        res = calculate_hybrid_score(self.resume_text, self.jd_text, tfidf_weight=0.6, skill_weight=1.4)
        self.assertEqual(res["tfidf_weight"], 0.3)
        self.assertEqual(res["skill_weight"], 0.7)

        expected_hybrid = round((res["tfidf_similarity_percentage"] * 0.3) + (res["skill_match_percentage"] * 0.7), 2)
        self.assertEqual(res["hybrid_score_percentage"], expected_hybrid)

    def test_invalid_weights_handling(self):
        """Test that negative weights or zero total weight raise ValueError."""
        with self.assertRaises(ValueError):
            calculate_hybrid_score(self.resume_text, self.jd_text, tfidf_weight=-0.5, skill_weight=0.5)

        with self.assertRaises(ValueError):
            calculate_hybrid_score(self.resume_text, self.jd_text, tfidf_weight=0.0, skill_weight=0.0)

    def test_format_match_report(self):
        """Test report formatting contains clear component breakdowns."""
        res = calculate_hybrid_score(self.resume_text, self.jd_text)
        report = format_match_report(res)

        self.assertIn("CANDIDATE & JOB MATCHING REPORT", report)
        self.assertIn("HYBRID SUITABILITY SCORE", report)
        self.assertIn("TF-IDF Vector Similarity", report)
        self.assertIn("Technical Skill Match", report)
        self.assertIn("Top Matching Keywords", report)
        self.assertIn("Technical Skill Gap Breakdown", report)

    def test_sample_data_integration(self):
        """End-to-end test on sample dataset."""
        res = calculate_hybrid_score(self.resume_text, self.jd_text)
        self.assertGreater(res["hybrid_score_percentage"], 0.0)
        self.assertTrue(len(res["top_matching_keywords"]) > 0)

if __name__ == "__main__":
    unittest.main()
