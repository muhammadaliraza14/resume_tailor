from __future__ import annotations

import json
from pathlib import Path
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from resume_tailor.documents import (
    compute_ats_metrics_json,
    loads_structured_resume_json,
    read_text_file_strict,
    render_structured_resume_pdf,
    simple_cosine_similarity,
    structured_resume_to_plain_text,
)

_ATS_GUIDELINES_PATH = Path(__file__).resolve().parent.parent / "knowledge" / "ats_guidelines.txt"


class GetAtsGuidelinesInput(BaseModel):
    """No parameters; tool returns bundled ATS guidance text."""

    pass


class GetAtsGuidelinesTool(BaseTool):
    name: str = "get_ats_guidelines"
    description: str = (
        "Return bundled ATS-oriented resume best practices (formatting, keywords, submission). "
        "Call once when evaluating; cite these principles in ats_compatibility and in formatted_report_markdown."
    )
    args_schema: Type[BaseModel] = GetAtsGuidelinesInput

    def _run(self) -> str:
        if not _ATS_GUIDELINES_PATH.is_file():
            return "ERROR: ats_guidelines.txt missing from package."
        return _ATS_GUIDELINES_PATH.read_text(encoding="utf-8")


class ReadTextFileInput(BaseModel):
    file_path: str = Field(description="Path to a UTF-8 .txt file")


class ReadTextFileTool(BaseTool):
    name: str = "read_text_file"
    description: str = (
        "Read a plain-text (.txt) file. Use for candidate resume or job description paths from crew inputs."
    )
    args_schema: Type[BaseModel] = ReadTextFileInput

    def _run(self, file_path: str) -> str:
        return read_text_file_strict(file_path)


class WriteStructuredResumeInput(BaseModel):
    tailored_resume_json: str = Field(
        description=(
            "Single JSON object matching StructuredResumeContent: full_name, headline, contact_line, "
            "linkedin_url, professional_summary, experience[], technical_skills_* , education[]. "
            "Use \\n escapes inside strings when needed; the tool repairs minor JSON issues."
        )
    )
    output_dir: str = Field(description="Directory for tailored_resume.pdf and tailored_resume.txt")


class WriteStructuredResumeTool(BaseTool):
    name: str = "write_tailored_resume_files"
    description: str = (
        "Validate tailored resume JSON and write tailored_resume.pdf (template layout) and "
        "tailored_resume.txt for evaluation."
    )
    args_schema: Type[BaseModel] = WriteStructuredResumeInput

    def _run(self, tailored_resume_json: str, output_dir: str) -> str:
        content = loads_structured_resume_json(tailored_resume_json)
        out = Path(output_dir).expanduser().resolve()
        out.mkdir(parents=True, exist_ok=True)
        pdf_path = out / "tailored_resume.pdf"
        txt_path = out / "tailored_resume.txt"
        render_structured_resume_pdf(content, pdf_path)
        txt_path.write_text(structured_resume_to_plain_text(content), encoding="utf-8")
        return json.dumps({"pdf": str(pdf_path), "txt": str(txt_path)})


class ReadTailoredResumeInput(BaseModel):
    output_dir: str = Field(description="Directory containing tailored_resume.txt")


class ReadTailoredResumeTextTool(BaseTool):
    name: str = "read_tailored_resume_text"
    description: str = "Load tailored_resume.txt from the output directory for evaluation."
    args_schema: Type[BaseModel] = ReadTailoredResumeInput

    def _run(self, output_dir: str) -> str:
        p = Path(output_dir).expanduser().resolve() / "tailored_resume.txt"
        if not p.is_file():
            return f"ERROR: {p} not found"
        return p.read_text(encoding="utf-8", errors="replace")


class AtsMetricsInput(BaseModel):
    resume_text: str = Field(description="Full tailored resume plain text")
    job_description_text: str = Field(description="Full job description plain text")


class AtsResumeMetricsTool(BaseTool):
    name: str = "compute_ats_resume_metrics"
    description: str = (
        "Deterministic ATS-oriented signals: JD token match rate in resume, ASCII ratio, "
        "bullet markers, date-like tokens, whitespace layout hints. Returns JSON string."
    )
    args_schema: Type[BaseModel] = AtsMetricsInput

    def _run(self, resume_text: str, job_description_text: str) -> str:
        return compute_ats_metrics_json(resume_text, job_description_text)


class KeywordSimilarityInput(BaseModel):
    resume_text: str = Field(description="Resume plain text")
    job_description_text: str = Field(description="Job description plain text")


class KeywordSimilarityTool(BaseTool):
    name: str = "compute_keyword_similarity"
    description: str = (
        "Compute a simple word-overlap cosine similarity (0–1) between resume and job description text."
    )
    args_schema: Type[BaseModel] = KeywordSimilarityInput

    def _run(self, resume_text: str, job_description_text: str) -> str:
        score = simple_cosine_similarity(resume_text, job_description_text)
        return f"{score:.4f}"
