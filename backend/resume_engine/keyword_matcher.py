import re
from typing import List, Dict, Any, Set

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
    """
    Extracts high-priority domain keywords and technical primitives from JD text.
    """
    text_clean = job_description.lower()
    found_keywords = set()

    for tech in COMMON_TECH_TAXONOMY:
        # Match as whole word or phrase
        pattern = r"\b" + re.escape(tech) + r"\b"
        if re.search(pattern, text_clean):
            found_keywords.add(tech)

    return found_keywords

def analyze_keyword_alignment(
    job_description: str,
    candidate_memory_texts: List[str]
) -> Dict[str, Any]:
    """
    FR-15: Modeled on srbhr/Resume-Matcher.
    Compares JD keywords with candidate project bullets and skills,
    identifying matched and missing high-priority ATS nouns.
    """
    jd_keywords = extract_jd_keywords(job_description)
    candidate_combined = " ".join(candidate_memory_texts).lower()
    
    candidate_keywords = set()
    for tech in COMMON_TECH_TAXONOMY:
        if re.search(r"\b" + re.escape(tech) + r"\b", candidate_combined):
            candidate_keywords.add(tech)

    matched = list(jd_keywords.intersection(candidate_keywords))
    missing = list(jd_keywords.difference(candidate_keywords))

    score = int((len(matched) / max(len(jd_keywords), 1)) * 100)

    return {
        "jd_keywords_count": len(jd_keywords),
        "candidate_keywords_count": len(candidate_keywords),
        "matched_keywords": matched,
        "missing_keywords": missing,
        "alignment_score": min(score, 100)
    }
