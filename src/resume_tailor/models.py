from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List


# --- Legacy block model (unused in text+template flow) ---
class ResumeBlock(BaseModel):
    index: int
    text: str
    block_type: str = Field(
        default="normal",
        description="One of: heading, bullet, normal",
    )


class ResumeStructure(BaseModel):
    source_path: str
    source_format: str
    blocks: List[ResumeBlock]
    full_text: str = ""


# --- Current pipeline: plain-text resume + template-styled PDF output ---


class ExperienceRole(BaseModel):
    title: str = Field(description="Job title, e.g. Senior Full Stack Developer")
    company: str
    date_range: str = Field(description="e.g. Sep 2023 – Apr 2026")
    bullets: List[str] = Field(default_factory=list)
    tech_used: str = Field(
        default="",
        description="Comma-separated technologies line after bullets, or empty",
    )


class EducationEntry(BaseModel):
    institution: str
    degree_line: str = Field(description="e.g. Bachelor of Science, Computer Science")
    dates: str = Field(default="", description="e.g. 2012 – 2016")


class StructuredResumeContent(BaseModel):
    """
    Mirrors the section layout of input/resume_template.pdf:
    header, summary, experience (bullets + Tech Used), three skill lines, education.
    """

    full_name: str
    headline: str = Field(
        default="",
        description="One line under name: roles | key skills | years",
    )
    contact_line: str = Field(
        default="",
        description="City, email, phone separated by bullets or similar",
    )
    linkedin_url: str = ""
    professional_summary: str
    experience: List[ExperienceRole] = Field(default_factory=list)
    technical_skills_frontend: str = Field(
        default="",
        description="Skills text after 'Frontend |'",
    )
    technical_skills_backend: str = Field(
        default="",
        description="Skills text after 'Backend |'",
    )
    technical_skills_devops: str = Field(
        default="",
        description="Skills text after 'DBs & DevOps |'",
    )
    education: List[EducationEntry] = Field(default_factory=list)


class JobDescriptionStructure(BaseModel):
    summary: str = ""
    keywords: List[str] = Field(default_factory=list)
    required_skills: List[str] = Field(default_factory=list)
    qualifications: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    raw_excerpt: str = ""


class TailoredBlock(BaseModel):
    index: int
    text: str


class TailoringResult(BaseModel):
    blocks: List[TailoredBlock]


class ResumeEvaluation(BaseModel):
    score_1_to_10: int = Field(
        ge=1,
        le=10,
        description="Holistic recruiter-style fit vs the JD (not the same as ATS readiness).",
    )
    ats_readiness_score_0_to_100: int = Field(
        ge=0,
        le=100,
        description=(
            "Heuristic ATS-oriented score: combine compute_ats_resume_metrics signals, "
            "cosine similarity, and ATS guideline checklist (formatting, keywords in context, ASCII, dates)."
        ),
    )
    keyword_alignment: str = Field(
        description="How well concrete JD terms appear in the tailored resume (in context, not keyword stuffing).",
    )
    content_alignment: str = Field(
        description="How experience and summary map to responsibilities and qualifications.",
    )
    ats_compatibility: str = Field(
        description=(
            "ATS-oriented notes: simple layout, single-column plain text, standard section labels, "
            "avoid accents/special symbols where possible, keyword placement, dates, file-format caveats."
        ),
    )
    ats_metrics_interpretation: str = Field(
        description="Short plain-language readout of the JSON from compute_ats_resume_metrics.",
    )
    cosine_similarity_note: str = Field(
        default="",
        description="Include the numeric value from compute_keyword_similarity (0–1).",
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="Concrete improvements; include ATS items when ats_readiness_score_0_to_100 < 75.",
    )
    formatted_report_markdown: str = Field(
        description=(
            "Polished Markdown for stakeholders: headings, bullet lists, include both scores with brief definitions, "
            "sections for Keyword fit, Role fit, ATS compatibility (reference get_ats_guidelines), and Next steps."
        ),
    )
