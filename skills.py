"""
skills.py - Technical Skill Extraction & Skill Gap Analysis Engine
-------------------------------------------------------------------
This module handles:
1. Loading the technical skills taxonomy from data/skills_db.json
2. Extracting technical skills from text using boundary-safe regex matching
3. Comparing candidate resume skills against job description requirements
4. Returning structured skill gap analysis (Matching, Missing, Additional, Match %)
"""

import json
import os
import re
from typing import Dict, List, Set, Any

# Path to the technical skills JSON taxonomy
DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "data", "skills_db.json")


def load_skills_db(db_path: str = DEFAULT_DB_PATH) -> Dict[str, Dict[str, List[str]]]:
    """
    Loads the skills taxonomy JSON file.
    Structure: Category -> Canonical Skill Name -> List of Aliases/Patterns

    Args:
        db_path (str): File path to skills_db.json.

    Returns:
        Dict: Skill taxonomy dictionary.
    """
    if os.path.exists(db_path):
        with open(db_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        raise FileNotFoundError(f"Skills database file not found at: {db_path}")


def _build_skill_regex(alias: str) -> re.Pattern:
    """
    Constructs a boundary-safe regular expression for a skill keyword/alias.
    Prevents false substring matches (e.g. 'Java' inside 'JavaScript' or 'C' inside 'C++' / 'C#').

    Args:
        alias (str): Skill pattern alias string.

    Returns:
        re.Pattern: Case-insensitive compiled regex object.
    """
    start_boundary = r'(?<![a-zA-Z0-9_])'

    # If alias ends with special chars like +, #, ., we allow those in the match itself,
    # but for standard aliases (like 'c' or 'java'), we disallow trailing +, #, or alnum
    if alias.endswith('+') or alias.endswith('#') or alias.endswith('.'):
        end_boundary = r'(?![a-zA-Z0-9_])'
    else:
        end_boundary = r'(?![a-zA-Z0-9_+#])'

    pattern_str = f"{start_boundary}{alias}{end_boundary}"
    return re.compile(pattern_str, re.IGNORECASE)


def extract_skills(text: str, skills_db: Dict[str, Dict[str, List[str]]] = None) -> Dict[str, Any]:
    """
    Detects technical skills present in the input text across all categories.

    Args:
        text (str): Resume text or Job Description text.
        skills_db (Dict, optional): Custom skill taxonomy dictionary.

    Returns:
        Dict[str, Any]:
            - 'categorized': { CategoryName: [Skill Names] }
            - 'all_skills': List of unique canonical skill names detected
            - 'total_skills_count': int
    """
    if not text:
        return {"categorized": {}, "all_skills": [], "total_skills_count": 0}

    if skills_db is None:
        skills_db = load_skills_db()

    categorized_skills: Dict[str, List[str]] = {}
    all_found_skills: Set[str] = set()

    for category, skills_dict in skills_db.items():
        found_in_category = []
        for canonical_name, aliases in skills_dict.items():
            # Check if any alias for this skill appears in the text
            is_found = False
            for alias in aliases:
                regex = _build_skill_regex(alias)
                if regex.search(text):
                    is_found = True
                    break

            if is_found:
                found_in_category.append(canonical_name)
                all_found_skills.add(canonical_name)

        if found_in_category:
            categorized_skills[category] = sorted(found_in_category)

    sorted_all_skills = sorted(list(all_found_skills))

    return {
        "categorized": categorized_skills,
        "all_skills": sorted_all_skills,
        "total_skills_count": len(sorted_all_skills)
    }


def compare_skills(resume_text: str, jd_text: str, skills_db: Dict[str, Dict[str, List[str]]] = None) -> Dict[str, Any]:
    """
    Compares candidate resume skills against job description required skills.

    Args:
        resume_text (str): Extracted resume text.
        jd_text (str): Extracted job description text.
        skills_db (Dict, optional): Skills taxonomy database.

    Returns:
        Dict[str, Any]:
            - 'matching_skills': Skills present in both Resume & JD
            - 'missing_skills': Required JD skills missing from Resume
            - 'additional_skills': Candidate skills not required by JD
            - 'matched_count': int count of matched skills
            - 'missing_count': int count of missing skills
            - 'additional_count': int count of additional skills
            - 'total_required_skills': int total count of required JD skills
            - 'skill_match_percentage': float (0.0 to 100.0%)
            - 'resume_skills_count': int total count of candidate skills
            - 'jd_skills_count': int total count of JD skills
            - 'resume_skills': Full extracted resume skill details
            - 'jd_skills': Full extracted JD skill details
    """
    if skills_db is None:
        skills_db = load_skills_db()

    resume_extracted = extract_skills(resume_text, skills_db)
    jd_extracted = extract_skills(jd_text, skills_db)

    resume_set = set(resume_extracted["all_skills"])
    jd_set = set(jd_extracted["all_skills"])

    matching = sorted(list(resume_set.intersection(jd_set)))
    missing = sorted(list(jd_set.difference(resume_set)))
    additional = sorted(list(resume_set.difference(jd_set)))

    # Match score = Matched Skills / Total Required JD Skills * 100
    if jd_set:
        match_percentage = round((len(matching) / len(jd_set)) * 100.0, 2)
    else:
        match_percentage = 0.0

    return {
        "matching_skills": matching,
        "missing_skills": missing,
        "additional_skills": additional,
        "matched_count": len(matching),
        "missing_count": len(missing),
        "additional_count": len(additional),
        "total_required_skills": len(jd_set),
        "skill_match_percentage": match_percentage,
        "resume_skills_count": len(resume_set),
        "jd_skills_count": len(jd_set),
        "resume_skills": resume_extracted,
        "jd_skills": jd_extracted
    }


def format_skill_report(comparison: Dict[str, Any]) -> str:
    """
    Formats the comparison result into a clean, human-readable summary string.

    Args:
        comparison (Dict): Result dictionary from compare_skills().

    Returns:
        str: Formatted report text.
    """
    lines = [
        "==================================================",
        "          TECHNICAL SKILL GAP REPORT              ",
        "==================================================",
        f"Skill Match Percentage : {comparison['skill_match_percentage']}%",
        f"Matched Skills Count   : {comparison['matched_count']}",
        f"Missing Skills Count   : {comparison['missing_count']}",
        f"Additional Skills Count: {comparison['additional_count']}",
        f"Total Required (JD)    : {comparison['total_required_skills']}",
        "--------------------------------------------------",
        f"Matching Skills ({comparison['matched_count']}):",
        "  " + (", ".join(comparison['matching_skills']) if comparison['matching_skills'] else "None"),
        "",
        f"Missing Skills ({comparison['missing_count']}):",
        "  " + (", ".join(comparison['missing_skills']) if comparison['missing_skills'] else "None"),
        "",
        f"Additional Skills ({comparison['additional_count']}):",
        "  " + (", ".join(comparison['additional_skills']) if comparison['additional_skills'] else "None"),
        "=================================================="
    ]
    return "\n".join(lines)
