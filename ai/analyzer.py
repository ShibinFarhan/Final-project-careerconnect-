import os
import re
from pdfminer.high_level import extract_text

# Skill synonyms and multi-word variants mapped to canonical keys
SKILL_SYNONYMS = {
    'python': ['python'],
    'machine_learning': ['machine learning', 'ml', 'deep learning'],
    'java': ['java'],
    'javascript': ['javascript', 'js'],
    'react': ['react', 'react.js', 'reactjs'],
    'node': ['node', 'node.js', 'nodejs'],
    'sql': ['sql', 'structured query language'],
    'aws': ['aws', 'amazon web services'],
    'docker': ['docker', 'containers', 'containerization'],
    'kubernetes': ['kubernetes', 'k8s'],
    'c++': ['c\+\+'],
    'c#': ['c#'],
    'go': ['go', 'golang'],
    'ruby': ['ruby'],
    'php': ['php'],
    'html': ['html'],
    'css': ['css'],
    'tensorflow': ['tensorflow'],
    'pytorch': ['pytorch'],
    'nlp': ['nlp', 'natural language processing'],
    'linux': ['linux']
}

ROLE_MAP = {
    'backend': {'python', 'java', 'node', 'sql', 'docker', 'aws'},
    'frontend': {'javascript', 'react', 'html', 'css', 'typescript'},
    'data_scientist': {'python', 'tensorflow', 'pytorch', 'nlp', 'sql'},
    'devops': {'aws', 'docker', 'kubernetes', 'linux'},
}

# Weights for ATS components (tuneable)
WEIGHTS = {
    'skill': 0.7,
    'experience': 0.2,
    'education': 0.1,
}


def extract_text_from_file(path):
    """Extract plain text from supported file types (pdf, txt)."""
    if not os.path.exists(path):
        return ""
    ext = path.split('.')[-1].lower()
    try:
        if ext == 'pdf':
            text = extract_text(path) or ""
            return text
        elif ext == 'txt':
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        else:
            return ""
    except Exception:
        return ""


def _build_skill_patterns():
    patterns = []
    for canonical, synonyms in SKILL_SYNONYMS.items():
        for syn in synonyms:
            # use word boundaries; synonyms may contain regex escapes already
            pat = r'(?i)\b' + syn + r'\b'
            patterns.append((canonical, re.compile(pat)))
    return patterns


_SKILL_PATTERNS = _build_skill_patterns()


def find_skill_occurrences(text, context_chars=40):
    """Return dict mapping canonical skill -> list of provenance snippets where it was found."""
    occurrences = {}
    for canonical, pattern in _SKILL_PATTERNS:
        for m in pattern.finditer(text):
            start, end = m.start(), m.end()
            snippet = text[max(0, start - context_chars):min(len(text), end + context_chars)].strip()
            occurrences.setdefault(canonical, []).append(snippet)
    # deduplicate snippets
    for k in list(occurrences.keys()):
        uniq = []
        seen = set()
        for s in occurrences[k]:
            if s not in seen:
                uniq.append(s)
                seen.add(s)
        occurrences[k] = uniq
    return occurrences


def extract_skills(text):
    occ = find_skill_occurrences(text)
    skills = sorted([k for k, v in occ.items() if v])
    return skills, occ


def predict_roles(skills):
    scores = {}
    skills_set = set(skills)
    for role, role_skills in ROLE_MAP.items():
        inter = skills_set.intersection(role_skills)
        if inter:
            scores[role] = len(inter)
    return [r for r, _ in sorted(scores.items(), key=lambda kv: kv[1], reverse=True)]


def compute_ats(profile_skills, resume_skills, experience_years, education):
    """Return detailed ATS-like scoring with components and missing skills."""
    try:
        experience = float(experience_years or 0)
    except Exception:
        experience = 0.0

    profile_set = set([s.strip().lower() for s in (profile_skills or '').split(',') if s.strip()])
    resume_set = set([s.strip().lower() for s in (resume_skills or []) if s.strip()])

    if profile_set:
        matched = resume_set.intersection(profile_set)
        skill_match_ratio = len(matched) / max(len(profile_set), 1)
        missing = sorted(profile_set - matched)
    else:
        skill_match_ratio = min(1.0, len(resume_set) / max(len(SKILL_SYNONYMS), 1))
        missing = []

    experience_score = min(experience / 20.0, 1.0)

    edu_score = 0
    if education:
        ed = education.lower()
        if 'phd' in ed:
            edu_score = 1.0
        elif 'master' in ed:
            edu_score = 0.85
        elif 'bachelor' in ed:
            edu_score = 0.7
        else:
            edu_score = 0.5

    # component scores
    comp_skill = round(skill_match_ratio, 3)
    comp_exp = round(experience_score, 3)
    comp_edu = round(edu_score, 3)

    weighted = comp_skill * WEIGHTS['skill'] + comp_exp * WEIGHTS['experience'] + comp_edu * WEIGHTS['education']
    ats = int(min(100, weighted * 100))

    return {
        'ats_score': ats,
        'skill_match_ratio': round(skill_match_ratio, 2),
        'missing_skills': missing,
        'matched_skills': sorted(list(resume_set.intersection(profile_set))) if profile_set else sorted(list(resume_set)),
        'component_scores': {
            'skill_score': comp_skill,
            'experience_score': comp_exp,
            'education_score': comp_edu,
        },
        'weights': WEIGHTS,
    }


def analyze_resume_file(path, profile_skills=None, experience_years=None, education=None):
    text = extract_text_from_file(path) or ''
    skills, provenance = extract_skills(text)
    roles = predict_roles(skills)
    ats = compute_ats(profile_skills, skills, experience_years, education)
    suggestions = []
    if ats['ats_score'] < 60:
        suggestions.append('Add relevant keywords and metrics in your projects')
    if ats['ats_score'] < 40:
        suggestions.append('Consider listing measurable outcomes and technologies used')

    return {
        'text_length': len(text),
        'extracted_skills': skills,
        'skills_provenance': provenance,
        'predicted_roles': roles,
        'ats': ats,
        'suggestions': suggestions,
    }
  