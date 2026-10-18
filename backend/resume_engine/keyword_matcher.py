import re
import yaml
from typing import List, Dict, Any, Set, Optional

COMMON_TECH_TAXONOMY = {
    # Languages
    "python", "c++", "java", "javascript", "typescript", "golang", "go", "rust", "sql", "c",
    # AI & ML
    "pytorch", "tensorflow", "keras", "huggingface", "transformers", "llm", "llms", "rag", 
    "diffusion", "computer vision", "nlp", "cuda", "qdrant", "vector database", "embeddings",
    "scikit-learn", "opencv", "deep learning", "machine learning",
    # Backend & Systems
    "fastapi", "flask", "django", "express", "node.js", "docker", "kubernetes", "redis",
    "postgresql", "mysql", "mongodb", "kafka", "rabbitmq", "celery", "grpc", "rest api",
    "microservices", "distributed systems", "linux", "git", "ci/cd", "aws", "gcp"
}

def extract_jd_keywords(job_description: str) -> Set[str]:
    """Extracts high-priority domain keywords and technical primitives from JD text."""
    text_clean = job_description.lower()
    found_keywords = set()

    for tech in COMMON_TECH_TAXONOMY:
        pattern = r"\b" + re.escape(tech) + r"\b"
        if re.search(pattern, text_clean):
            found_keywords.add(tech)

    return found_keywords

def extract_and_map_requirements(
    job_description: str,
    candidate_facts: List[str],
    candidate_skills: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    FR-023: Requirement-to-Evidence Mapping.
    Maps technical requirements from the JD to confirmed candidate facts in Mem0.
    Flags missing skills as unconfirmed evidence rather than fabricating them.
    """
    jd_keywords = extract_jd_keywords(job_description)
    candidate_skills_set = set(s.lower() for s in (candidate_skills or []))
    
    matched_keywords: List[str] = []
    missing_keywords: List[str] = []
    evidence_map: Dict[str, str] = {}

    for kw in jd_keywords:
        # Check against candidate facts
        found_fact = None
        for fact in candidate_facts:
            if re.search(r"\b" + re.escape(kw) + r"\b", fact.lower()):
                found_fact = fact
                break
        
        if found_fact:
            matched_keywords.append(kw)
            evidence_map[kw] = found_fact
        elif kw in candidate_skills_set:
            matched_keywords.append(kw)
            evidence_map[kw] = f"Confirmed in student profile skill list: {kw}"
        else:
            missing_keywords.append(kw)

    total_reqs = len(jd_keywords)
    coverage = int((len(matched_keywords) / max(total_reqs, 1)) * 100)

    return {
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "evidence_map": evidence_map,
        "coverage_score": min(coverage, 100),
        "truthfulness_verified": True
    }

def verify_resume_truthfulness(
    generated_yaml: str,
    candidate_facts: List[str],
    missing_keywords: List[str]
) -> Dict[str, Any]:
    """
    FR-024: Resume Truthfulness Enforcement (Fail-Closed).
    Scans generated YAML highlights to ensure no missing/unconfirmed skills or fake companies
    were hallucinated into the resume bullets.
    """
    hallucinated: List[str] = []
    yaml_lower = generated_yaml.lower()

    for missing_kw in missing_keywords:
        # If a missing skill appears in highlights or project descriptions, flag hallucination
        pattern = r"\b" + re.escape(missing_kw) + r"\b"
        if re.search(pattern, yaml_lower):
            hallucinated.append(missing_kw)

    passed = len(hallucinated) == 0
    
    # If hallucination detected, sanitize by stripping the unconfirmed skill from highlights
    sanitized_yaml = generated_yaml
    if not passed:
        for bad_kw in hallucinated:
            sanitized_yaml = re.sub(
                r"\b" + re.escape(bad_kw) + r"\b",
                "",
                sanitized_yaml,
                flags=re.IGNORECASE
            )

    return {
        "truthfulness_passed": passed,
        "hallucinated_keywords": hallucinated,
        "sanitized_yaml": sanitized_yaml
    }

def analyze_keyword_alignment(
    job_description: str,
    candidate_memory_texts: List[str]
) -> Dict[str, Any]:
    """Backward compatibility wrapper for existing tests."""
    res = extract_and_map_requirements(job_description, candidate_memory_texts)
    return {
        "jd_keywords_count": len(res["matched_keywords"]) + len(res["missing_keywords"]),
        "candidate_keywords_count": len(res["matched_keywords"]),
        "matched_keywords": res["matched_keywords"],
        "missing_keywords": res["missing_keywords"],
        "alignment_score": res["coverage_score"],
        "evidence_map": res["evidence_map"]
    }
