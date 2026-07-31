"""
matcher.py - Document Matching & Hybrid Suitability Scoring Engine
-------------------------------------------------------------------
This module handles:
1. TF-IDF vectorization and Cosine Similarity calculation between resume and job description text using scikit-learn.
2. Top matching keyword extraction based on weighted TF-IDF term overlaps.
3. Hybrid Suitability Score calculation combining TF-IDF similarity with technical skill match percentage.
4. Flexible weight normalization and transparent individual component score reporting.
"""

import os
from typing import Dict, List, Tuple, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from extractor import clean_text
from skills import compare_skills, load_skills_db


def compute_tfidf_similarity(
    text1: str,
    text2: str,
    stop_words: str = 'english',
    ngram_range: Tuple[int, int] = (1, 2)
) -> Dict[str, Any]:
    """
    Computes Cosine Similarity between TF-IDF representations of two text documents.

    Args:
        text1 (str): First text document (e.g. Resume text).
        text2 (str): Second text document (e.g. Job Description text).
        stop_words (str): Stop words setting for TfidfVectorizer. Defaults to 'english'.
        ngram_range (Tuple[int, int]): Range of n-grams to extract. Defaults to (1, 2).

    Returns:
        Dict[str, Any]:
            - 'similarity_score': float (0.0 to 1.0)
            - 'similarity_percentage': float (0.0 to 100.0%)
            - 'vocabulary_size': int
    """
    cleaned1 = clean_text(text1)
    cleaned2 = clean_text(text2)

    if not cleaned1 or not cleaned2:
        return {
            "similarity_score": 0.0,
            "similarity_percentage": 0.0,
            "vocabulary_size": 0
        }

    try:
        vectorizer = TfidfVectorizer(stop_words=stop_words, ngram_range=ngram_range)
        tfidf_matrix = vectorizer.fit_transform([cleaned1, cleaned2])
        
        # Calculate Cosine Similarity between document 0 and document 1
        sim_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        score = float(sim_matrix[0][0])
        score = max(0.0, min(1.0, score))  # Clamp between 0.0 and 1.0 for safety
        
        vocab_size = len(vectorizer.get_feature_names_out())
        
        return {
            "similarity_score": round(score, 4),
            "similarity_percentage": round(score * 100.0, 2),
            "vocabulary_size": vocab_size
        }
    except ValueError:
        # Handles cases like empty vocabulary after stop word filtering
        return {
            "similarity_score": 0.0,
            "similarity_percentage": 0.0,
            "vocabulary_size": 0
        }


def extract_top_matching_keywords(
    text1: str,
    text2: str,
    top_n: int = 10,
    stop_words: str = 'english',
    ngram_range: Tuple[int, int] = (1, 2)
) -> List[Dict[str, Any]]:
    """
    Extracts and ranks top overlapping keywords/phrases between two text documents
    weighted by TF-IDF vector score products.

    Args:
        text1 (str): First text document (Resume).
        text2 (str): Second text document (Job Description).
        top_n (int): Number of top keywords to return. Defaults to 10.
        stop_words (str): Stop words language. Defaults to 'english'.
        ngram_range (Tuple[int, int]): N-gram range. Defaults to (1, 2).

    Returns:
        List[Dict[str, Any]]: Ranks list of dicts with keyword details:
            - 'keyword': str
            - 'score': float (TF-IDF product)
            - 'resume_tfidf': float
            - 'jd_tfidf': float
    """
    cleaned1 = clean_text(text1)
    cleaned2 = clean_text(text2)

    if not cleaned1 or not cleaned2:
        return []

    try:
        vectorizer = TfidfVectorizer(stop_words=stop_words, ngram_range=ngram_range)
        tfidf_matrix = vectorizer.fit_transform([cleaned1, cleaned2])
        feature_names = vectorizer.get_feature_names_out()

        vec1 = tfidf_matrix[0].toarray()[0]
        vec2 = tfidf_matrix[1].toarray()[0]

        matching_terms = []
        for idx, feature in enumerate(feature_names):
            w1 = vec1[idx]
            w2 = vec2[idx]
            # Overlapping terms present in both documents
            if w1 > 0 and w2 > 0:
                prod_score = float(w1 * w2)
                matching_terms.append({
                    "keyword": feature,
                    "score": round(prod_score, 4),
                    "resume_tfidf": round(float(w1), 4),
                    "jd_tfidf": round(float(w2), 4)
                })

        # Sort terms by product score descending
        matching_terms.sort(key=lambda x: x["score"], reverse=True)
        return matching_terms[:top_n]

    except ValueError:
        return []


def calculate_hybrid_score(
    resume_text: str,
    jd_text: str,
    tfidf_weight: float = 0.5,
    skill_weight: float = 0.5,
    skills_db: Optional[Dict[str, Any]] = None,
    top_n_keywords: int = 10
) -> Dict[str, Any]:
    """
    Calculates transparent Hybrid Suitability Score combining TF-IDF Cosine Similarity
    and Technical Skill Match Percentage.

    Validates and normalizes weights so tfidf_weight + skill_weight == 1.0.

    Args:
        resume_text (str): Extracted text of resume.
        jd_text (str): Extracted text of job description.
        tfidf_weight (float): Weight for TF-IDF similarity (>= 0). Defaults to 0.5.
        skill_weight (float): Weight for technical skill match (>= 0). Defaults to 0.5.
        skills_db (Dict, optional): Custom skill taxonomy dictionary.
        top_n_keywords (int): Number of top keywords to extract. Defaults to 10.

    Returns:
        Dict[str, Any]:
            - 'hybrid_score_percentage': float (0.0 to 100.0%)
            - 'hybrid_score': float (0.0 to 1.0)
            - 'tfidf_similarity_percentage': float (0.0 to 100.0%)
            - 'tfidf_similarity_score': float (0.0 to 1.0)
            - 'skill_match_percentage': float (0.0 to 100.0%)
            - 'tfidf_weight': float (normalized weight)
            - 'skill_weight': float (normalized weight)
            - 'raw_tfidf_weight': float
            - 'raw_skill_weight': float
            - 'top_matching_keywords': List[Dict]
            - 'skill_gap_analysis': Dict (result from compare_skills)
    """
    if tfidf_weight < 0 or skill_weight < 0:
        raise ValueError("Weights cannot be negative.")

    total_weight = tfidf_weight + skill_weight
    if total_weight <= 0:
        raise ValueError("Sum of tfidf_weight and skill_weight must be greater than zero.")

    # Normalize weights so they sum to 1.0
    norm_tfidf_weight = tfidf_weight / total_weight
    norm_skill_weight = skill_weight / total_weight

    # 1. Compute TF-IDF Cosine Similarity
    tfidf_res = compute_tfidf_similarity(resume_text, jd_text)
    tfidf_percentage = tfidf_res["similarity_percentage"]
    tfidf_score = tfidf_res["similarity_score"]

    # 2. Compute Technical Skill Match Percentage from skills module
    skill_res = compare_skills(resume_text, jd_text, skills_db)
    skill_percentage = skill_res["skill_match_percentage"]

    # 3. Calculate Hybrid Score
    hybrid_percentage = (tfidf_percentage * norm_tfidf_weight) + (skill_percentage * norm_skill_weight)
    hybrid_percentage = round(max(0.0, min(100.0, hybrid_percentage)), 2)
    hybrid_score = round(hybrid_percentage / 100.0, 4)

    # 4. Extract top keywords
    top_keywords = extract_top_matching_keywords(resume_text, jd_text, top_n=top_n_keywords)

    return {
        "hybrid_score_percentage": hybrid_percentage,
        "hybrid_score": hybrid_score,
        "tfidf_similarity_percentage": tfidf_percentage,
        "tfidf_similarity_score": tfidf_score,
        "skill_match_percentage": skill_percentage,
        "tfidf_weight": round(norm_tfidf_weight, 4),
        "skill_weight": round(norm_skill_weight, 4),
        "raw_tfidf_weight": tfidf_weight,
        "raw_skill_weight": skill_weight,
        "top_matching_keywords": top_keywords,
        "skill_gap_analysis": skill_res
    }


def format_match_report(match_results: Dict[str, Any]) -> str:
    """
    Formats the hybrid matching output into a clean, human-readable report.

    Args:
        match_results (Dict[str, Any]): Result dictionary from calculate_hybrid_score().

    Returns:
        str: Formatted report text.
    """
    tfidf_pct = match_results["tfidf_similarity_percentage"]
    tfidf_w = round(match_results["tfidf_weight"] * 100.0, 1)
    
    skill_pct = match_results["skill_match_percentage"]
    skill_w = round(match_results["skill_weight"] * 100.0, 1)

    hybrid_pct = match_results["hybrid_score_percentage"]
    top_keywords = match_results.get("top_matching_keywords", [])
    gap_analysis = match_results.get("skill_gap_analysis", {})

    lines = [
        "==================================================",
        "        CANDIDATE & JOB MATCHING REPORT           ",
        "==================================================",
        f"HYBRID SUITABILITY SCORE : {hybrid_pct}%",
        "--------------------------------------------------",
        "Component Score Breakdown:",
        f"  * TF-IDF Vector Similarity : {tfidf_pct}% (Weight: {tfidf_w}%)",
        f"  * Technical Skill Match    : {skill_pct}% (Weight: {skill_w}%)",
        "--------------------------------------------------",
        f"Top Matching Keywords ({len(top_keywords)}):"
    ]

    if top_keywords:
        for idx, kw_info in enumerate(top_keywords, start=1):
            kw = kw_info["keyword"]
            sc = kw_info["score"]
            r_w = kw_info["resume_tfidf"]
            j_w = kw_info["jd_tfidf"]
            lines.append(f"  {idx:2d}. {kw:<20} (TF-IDF Product: {sc:.4f} | Resume: {r_w:.4f}, JD: {j_w:.4f})")
    else:
        lines.append("  None detected.")

    lines.extend([
        "--------------------------------------------------",
        "Technical Skill Gap Breakdown:",
        f"  * Matched Skills ({gap_analysis.get('matched_count', 0)}) : " +
        (", ".join(gap_analysis.get('matching_skills', [])) if gap_analysis.get('matching_skills') else "None"),
        f"  * Missing Skills ({gap_analysis.get('missing_count', 0)}) : " +
        (", ".join(gap_analysis.get('missing_skills', [])) if gap_analysis.get('missing_skills') else "None"),
        f"  * Additional Skills ({gap_analysis.get('additional_count', 0)}): " +
        (", ".join(gap_analysis.get('additional_skills', [])) if gap_analysis.get('additional_skills') else "None"),
        "=================================================="
    ])

    return "\n".join(lines)


if __name__ == "__main__":
    # Demonstration execution with sample dataset
    sample_dir = os.path.join(os.path.dirname(__file__), "sample_data")
    resume_path = os.path.join(sample_dir, "sample_resume.txt")
    jd_path = os.path.join(sample_dir, "sample_jd.txt")

    if os.path.exists(resume_path) and os.path.exists(jd_path):
        with open(resume_path, 'r', encoding='utf-8') as rf:
            sample_resume = rf.read()
        with open(jd_path, 'r', encoding='utf-8') as jf:
            sample_jd = jf.read()

        results = calculate_hybrid_score(sample_resume, sample_jd, tfidf_weight=0.5, skill_weight=0.5)
        print(format_match_report(results))
    else:
        print("Sample data files not found for demonstration.")
