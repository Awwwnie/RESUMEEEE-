"""
gap_analyzer.py - Skill Gap Analysis & Readiness Report Engine
-----------------------------------------------------------------
Builds on skills.py (compare_skills) to produce a categorized,
prioritized skill gap report with readiness level and improvement
suggestions, suitable for direct display in the Streamlit dashboard.
"""

from typing import Dict, List, Any
from skills import compare_skills, load_skills_db

# Priority order for categories - higher priority categories are
# surfaced first in recommendations since they typically matter
# more to recruiters for technical roles.
CATEGORY_PRIORITY = [
    "Programming Languages",
    "AI/ML",
    "Data Science",
    "Web Development",
    "Databases",
    "Cloud & DevOps",
    "Mobile Development",
    "Version Control & Tools",
    "Computer Science Fundamentals",
    "Operating Systems",
]


def categorize_missing_skills(
    missing_skills: List[str],
    skills_db: Dict[str, Dict[str, List[str]]] = None
) -> Dict[str, List[str]]:
    """
    Groups a flat list of missing skill names back into their
    taxonomy categories (e.g. Programming Languages, AI/ML).

    Args:
        missing_skills (List[str]): Canonical skill names missing from resume.
        skills_db (Dict, optional): Skills taxonomy database.

    Returns:
        Dict[str, List[str]]: Category -> list of missing skill names.
    """
    if skills_db is None:
        skills_db = load_skills_db()

    missing_set = set(missing_skills)
    categorized: Dict[str, List[str]] = {}

    for category, skills_dict in skills_db.items():
        found = [name for name in skills_dict.keys() if name in missing_set]
        if found:
            categorized[category] = sorted(found)

    return categorized


def get_readiness_level(match_percentage: float) -> Dict[str, str]:
    """
    Converts a numeric match percentage into a human-readable
    readiness label and short description.

    Args:
        match_percentage (float): Overall match percentage (0-100).

    Returns:
        Dict[str, str]: {'level': str, 'description': str}
    """
    if match_percentage >= 85:
        return {
            "level": "Strong Fit",
            "description": "The candidate meets nearly all required skills for this role."
        }
    elif match_percentage >= 65:
        return {
            "level": "Good Fit",
            "description": "The candidate meets most core requirements with a few gaps to address."
        }
    elif match_percentage >= 40:
        return {
            "level": "Moderate Fit",
            "description": "The candidate has a partial skill overlap; noticeable upskilling is needed."
        }
    else:
        return {
            "level": "Needs Improvement",
            "description": "The candidate's current skill set has limited overlap with this role."
        }


def get_priority_recommendations(
    categorized_missing: Dict[str, List[str]],
    top_n: int = 5
) -> List[Dict[str, Any]]:
    """
    Produces a ranked list of the most important skills to learn next,
    ordered by category priority, then alphabetically within category.

    Args:
        categorized_missing (Dict[str, List[str]]): Output of categorize_missing_skills().
        top_n (int): Maximum number of recommendations to return.

    Returns:
        List[Dict[str, Any]]: Ordered list of {'skill', 'category'} dicts.
    """
    ordered_categories = [c for c in CATEGORY_PRIORITY if c in categorized_missing]
    # Include any categories not in the predefined priority list at the end
    ordered_categories += [c for c in categorized_missing if c not in CATEGORY_PRIORITY]

    recommendations = []
    for category in ordered_categories:
        for skill in categorized_missing[category]:
            recommendations.append({"skill": skill, "category": category})
            if len(recommendations) >= top_n:
                return recommendations

    return recommendations


def analyze_skill_gap(
    resume_text: str,
    jd_text: str,
    skills_db: Dict[str, Dict[str, List[str]]] = None,
    top_n_recommendations: int = 5
) -> Dict[str, Any]:
    """
    Full skill gap analysis pipeline: compares resume vs JD skills,
    categorizes gaps, ranks recommendations, and assigns a readiness level.

    Args:
        resume_text (str): Extracted resume text.
        jd_text (str): Extracted job description text.
        skills_db (Dict, optional): Skills taxonomy database.
        top_n_recommendations (int): Max number of priority recommendations.

    Returns:
        Dict[str, Any]: Full structured gap analysis report.
    """
    if skills_db is None:
        skills_db = load_skills_db()

    comparison = compare_skills(resume_text, jd_text, skills_db)

    categorized_missing = categorize_missing_skills(comparison["missing_skills"], skills_db)
    categorized_matching = categorize_missing_skills(comparison["matching_skills"], skills_db)

    readiness = get_readiness_level(comparison["skill_match_percentage"])
    recommendations = get_priority_recommendations(categorized_missing, top_n=top_n_recommendations)

    return {
        "skill_match_percentage": comparison["skill_match_percentage"],
        "readiness_level": readiness["level"],
        "readiness_description": readiness["description"],
        "matching_skills": comparison["matching_skills"],
        "missing_skills": comparison["missing_skills"],
        "additional_skills": comparison["additional_skills"],
        "categorized_matching_skills": categorized_matching,
        "categorized_missing_skills": categorized_missing,
        "priority_recommendations": recommendations,
        "matched_count": comparison["matched_count"],
        "missing_count": comparison["missing_count"],
        "total_required_skills": comparison["total_required_skills"],
    }


def format_gap_report(analysis: Dict[str, Any]) -> str:
    """
    Formats a full skill gap analysis into a clean, readable text report.

    Args:
        analysis (Dict): Result of analyze_skill_gap().

    Returns:
        str: Formatted report string.
    """
    lines = [
        "==================================================",
        "            SKILL GAP ANALYSIS REPORT              ",
        "==================================================",
        f"Skill Match        : {analysis['skill_match_percentage']}%",
        f"Readiness Level    : {analysis['readiness_level']}",
        f"Summary            : {analysis['readiness_description']}",
        "--------------------------------------------------",
        "Missing Skills by Category:",
    ]

    if analysis["categorized_missing_skills"]:
        for category, skill_list in analysis["categorized_missing_skills"].items():
            lines.append(f"  [{category}]")
            for skill in skill_list:
                lines.append(f"    - {skill}")
    else:
        lines.append("  None — all required skills are present.")

    lines.append("--------------------------------------------------")
    lines.append("Top Priority Recommendations:")
    if analysis["priority_recommendations"]:
        for i, rec in enumerate(analysis["priority_recommendations"], start=1):
            lines.append(f"  {i}. {rec['skill']} ({rec['category']})")
    else:
        lines.append("  None needed.")

    lines.append("==================================================")
    return "\n".join(lines)


if __name__ == "__main__":
    import os
    sample_dir = os.path.join(os.path.dirname(__file__), "sample_data")
    with open(os.path.join(sample_dir, "sample_resume.txt"), "r", encoding="utf-8") as f:
        resume_text = f.read()
    with open(os.path.join(sample_dir, "sample_jd.txt"), "r", encoding="utf-8") as f:
        jd_text = f.read()

    result = analyze_skill_gap(resume_text, jd_text)
    print(format_gap_report(result))