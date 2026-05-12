"""Extract evaluation scores and prior-run feedback from a CrewAI kickoff result."""

from __future__ import annotations

from typing import Any, Optional

from resume_tailor.models import ResumeEvaluation


def extract_evaluation_scores(result: Any) -> tuple[Optional[int], Optional[int]]:
    """Recruiter fit (1–10) and ATS readiness (0–100) from CrewOutput or the last task output."""
    pyd = getattr(result, "pydantic", None)
    if pyd is not None and hasattr(pyd, "ats_readiness_score_0_to_100"):
        return getattr(pyd, "score_1_to_10", None), getattr(pyd, "ats_readiness_score_0_to_100", None)
    for out in reversed(getattr(result, "tasks_output", None) or []):
        tp = getattr(out, "pydantic", None)
        if tp is not None and hasattr(tp, "ats_readiness_score_0_to_100"):
            return getattr(tp, "score_1_to_10", None), getattr(tp, "ats_readiness_score_0_to_100", None)
    return None, None


def get_last_resume_evaluation(result: Any) -> Optional[ResumeEvaluation]:
    pyd = getattr(result, "pydantic", None)
    if isinstance(pyd, ResumeEvaluation):
        return pyd
    for out in reversed(getattr(result, "tasks_output", None) or []):
        tp = getattr(out, "pydantic", None)
        if isinstance(tp, ResumeEvaluation):
            return tp
    return None


def prior_feedback_markdown(ev: ResumeEvaluation, max_chars: int = 12000) -> str:
    """Condensed prior evaluation for the tailoring agent on refinement rounds."""
    parts = [
        f"Prior recruiter fit score: {ev.score_1_to_10}/10.",
        f"Prior ATS readiness score: {ev.ats_readiness_score_0_to_100}/100.",
        ev.formatted_report_markdown,
    ]
    if ev.suggestions:
        parts.append("Prior suggestions:\n" + "\n".join(f"- {s}" for s in ev.suggestions))
    text = "\n\n".join(parts)
    if len(text) > max_chars:
        return text[: max_chars - 50].rstrip() + "\n\n[…truncated for length…]"
    return text
