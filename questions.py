"""
questions.py - Interview Question Generator
------------------------------------------------------------------
Generates targeted technical and scenario-based interview questions
based on skills detected in the resume/JD comparison. Covers:
1. Questions for MATCHED skills (to verify claimed proficiency)
2. Questions for MISSING skills (to probe awareness/willingness to learn)
"""

import random
from typing import Dict, List, Any

# Question templates per skill. Each skill maps to a list of
# (technical_question, scenario_question) template strings.
# {skill} is substituted with the canonical skill name.
QUESTION_TEMPLATES: Dict[str, List[str]] = {
    "default_technical": [
        "Can you explain your practical experience working with {skill}?",
        "What are the core concepts or features of {skill} that you rely on most?",
        "What challenges have you faced while using {skill}, and how did you resolve them?",
    ],
    "default_scenario": [
        "Describe a project where {skill} was critical to solving a problem you faced.",
        "If you had to teach a beginner {skill} in 5 minutes, what would you cover first?",
    ],
    "default_missing_skill": [
        "This role requires {skill}, which isn't listed on your resume. "
        "Have you had any exposure to it, even informally?",
        "How would you approach learning {skill} quickly if it were required in your first month?",
    ],
}

# A few skill-specific overrides for more realistic, less generic questions.
SKILL_SPECIFIC_TEMPLATES: Dict[str, List[str]] = {
    "Python": [
        "How do Python's list and dictionary comprehensions improve code readability?",
        "Explain the difference between deep copy and shallow copy in Python.",
    ],
    "SQL": [
        "Write a query approach to find duplicate rows in a table.",
        "Explain the difference between INNER JOIN and LEFT JOIN with an example.",
    ],
    "React": [
        "Explain the difference between state and props in React.",
        "How does the virtual DOM improve rendering performance?",
    ],
    "Docker": [
        "What's the difference between a Docker image and a Docker container?",
        "How would you reduce the size of a Docker image for a Python app?",
    ],
    "Machine Learning": [
        "How do you handle overfitting in a machine learning model?",
        "Explain the bias-variance tradeoff in simple terms.",
    ],
    "Git": [
        "What's the difference between git merge and git rebase?",
        "How would you resolve a merge conflict in a shared branch?",
    ],
}


def generate_questions_for_skill(skill: str, is_missing: bool = False) -> Dict[str, Any]:
    """
    Generates a small set of interview questions for a single skill.

    Args:
        skill (str): Canonical skill name.
        is_missing (bool): Whether this skill is missing from the resume.

    Returns:
        Dict[str, Any]: {'skill': str, 'questions': List[str], 'type': str}
    """
    questions: List[str] = []

    if is_missing:
        questions.extend(
            t.format(skill=skill) for t in QUESTION_TEMPLATES["default_missing_skill"]
        )
        return {"skill": skill, "questions": questions, "type": "missing_skill_probe"}

    # Prefer skill-specific templates if available
    if skill in SKILL_SPECIFIC_TEMPLATES:
        questions.extend(SKILL_SPECIFIC_TEMPLATES[skill])
    else:
        tech = random.choice(QUESTION_TEMPLATES["default_technical"])
        questions.append(tech.format(skill=skill))

    scenario = random.choice(QUESTION_TEMPLATES["default_scenario"])
    questions.append(scenario.format(skill=skill))

    return {"skill": skill, "questions": questions, "type": "technical_verification"}


def generate_interview_questions(
    matching_skills: List[str],
    missing_skills: List[str],
    max_matching: int = 5,
    max_missing: int = 3,
) -> Dict[str, Any]:
    """
    Builds a full interview question set from matched and missing skills.

    Args:
        matching_skills (List[str]): Skills present in both resume and JD.
        missing_skills (List[str]): Skills required by JD but missing from resume.
        max_matching (int): Max number of matched skills to generate questions for.
        max_missing (int): Max number of missing skills to generate questions for.

    Returns:
        Dict[str, Any]: {
            'technical_questions': List[Dict],
            'gap_probe_questions': List[Dict],
            'total_questions': int
        }
    """
    technical_questions = [
        generate_questions_for_skill(skill, is_missing=False)
        for skill in matching_skills[:max_matching]
    ]

    gap_probe_questions = [
        generate_questions_for_skill(skill, is_missing=True)
        for skill in missing_skills[:max_missing]
    ]

    total = sum(len(q["questions"]) for q in technical_questions) + \
        sum(len(q["questions"]) for q in gap_probe_questions)

    return {
        "technical_questions": technical_questions,
        "gap_probe_questions": gap_probe_questions,
        "total_questions": total,
    }


def format_questions_report(question_set: Dict[str, Any]) -> str:
    """
    Formats the generated question set into a clean, readable text report.

    Args:
        question_set (Dict): Output of generate_interview_questions().

    Returns:
        str: Formatted report string.
    """
    lines = [
        "==================================================",
        "          SUGGESTED INTERVIEW QUESTIONS             ",
        "==================================================",
        "Technical Verification (based on matched skills):",
    ]

    if question_set["technical_questions"]:
        for entry in question_set["technical_questions"]:
            lines.append(f"  [{entry['skill']}]")
            for q in entry["questions"]:
                lines.append(f"    - {q}")
    else:
        lines.append("  None generated.")

    lines.append("--------------------------------------------------")
    lines.append("Skill Gap Probes (based on missing skills):")

    if question_set["gap_probe_questions"]:
        for entry in question_set["gap_probe_questions"]:
            lines.append(f"  [{entry['skill']}]")
            for q in entry["questions"]:
                lines.append(f"    - {q}")
    else:
        lines.append("  None generated.")

    lines.append(f"--------------------------------------------------")
    lines.append(f"Total Questions Generated: {question_set['total_questions']}")
    lines.append("==================================================")
    return "\n".join(lines)


if __name__ == "__main__":
    import os
    from gap_analyzer import analyze_skill_gap

    sample_dir = os.path.join(os.path.dirname(__file__), "sample_data")
    with open(os.path.join(sample_dir, "sample_resume.txt"), "r", encoding="utf-8") as f:
        resume_text = f.read()
    with open(os.path.join(sample_dir, "sample_jd.txt"), "r", encoding="utf-8") as f:
        jd_text = f.read()

    gap_result = analyze_skill_gap(resume_text, jd_text)
    question_set = generate_interview_questions(
        gap_result["matching_skills"], gap_result["missing_skills"]
    )
    print(format_questions_report(question_set))