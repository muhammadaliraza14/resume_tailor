#!/usr/bin/env python
from __future__ import annotations

import argparse
import os
import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from resume_tailor.crew import ResumeTailorCrew
from resume_tailor.crew_outcome import CrewRunOutcome
from resume_tailor.crew_scores import (
    extract_evaluation_scores,
    get_last_resume_evaluation,
    prior_feedback_markdown,
)
from resume_tailor.paths import project_root as _project_root

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def kickoff_crew(
    resume_text_path: str | None = None,
    job_description_text_path: str | None = None,
    template_pdf_path: str | None = None,
    output_dir: str | None = None,
) -> CrewRunOutcome:
    """
    Load env, chdir to project root, build inputs, run the crew (possibly multiple full passes).

    Re-runs the full crew until recruiter fit >= MIN_RECRUITER_SCORE (default 8) and
    ATS readiness >= MIN_ATS_SCORE (default 80), or MAX_CREW_SCORE_ROUNDS full runs are exhausted.
    """
    root = _project_root()
    load_dotenv(root / ".env")
    load_dotenv()
    os.chdir(root)

    resume = resume_text_path or os.getenv("RESUME_TEXT_PATH", os.getenv("RESUME_PATH", str(root / "input" / "resume.txt")))
    jd = job_description_text_path or os.getenv(
        "JOB_DESCRIPTION_TEXT_PATH",
        os.getenv("JOB_DESCRIPTION_PATH", str(root / "input" / "job_description.txt")),
    )
    template = template_pdf_path or os.getenv(
        "TEMPLATE_PDF_PATH", str(root / "input" / "resume_template.pdf")
    )
    out = output_dir or os.getenv("OUTPUT_DIR", str(root / "output"))

    min_recruiter = int(os.getenv("MIN_RECRUITER_SCORE", "8"))
    min_ats = int(os.getenv("MIN_ATS_SCORE", "80"))
    max_rounds = int(os.getenv("MAX_CREW_SCORE_ROUNDS", "6"))
    if max_rounds < 1:
        max_rounds = 1

    base_inputs = {
        "resume_text_path": str(Path(resume).expanduser().resolve()),
        "job_description_text_path": str(Path(jd).expanduser().resolve()),
        "template_pdf_path": str(Path(template).expanduser().resolve()),
        "output_dir": str(Path(out).expanduser().resolve()),
        "current_date": str(datetime.now()),
    }

    Path(base_inputs["output_dir"]).mkdir(parents=True, exist_ok=True)

    prior_feedback = (
        "None (first tailoring pass — no prior evaluation). "
        f"Pipeline targets: recruiter fit >= {min_recruiter}/10 and ATS readiness >= {min_ats}/100."
    )
    last_result: Any = None

    for round_idx in range(max_rounds):
        inputs = {
            **base_inputs,
            "refinement_round": str(round_idx),
            "prior_evaluation_feedback": prior_feedback,
            "min_recruiter_score": str(min_recruiter),
            "min_ats_score": str(min_ats),
        }
        last_result = ResumeTailorCrew().crew().kickoff(inputs=inputs)
        rec, ats = extract_evaluation_scores(last_result)
        targets_met = (
            rec is not None and ats is not None and rec >= min_recruiter and ats >= min_ats
        )
        if targets_met:
            return CrewRunOutcome(last_result, round_idx + 1, True)
        if round_idx >= max_rounds - 1:
            return CrewRunOutcome(last_result, round_idx + 1, False)
        ev = get_last_resume_evaluation(last_result)
        if ev is None:
            return CrewRunOutcome(last_result, round_idx + 1, False)
        prior_feedback = prior_feedback_markdown(ev)

    return CrewRunOutcome(last_result, max_rounds, False)


def run(
    resume_text_path: str | None = None,
    job_description_text_path: str | None = None,
    template_pdf_path: str | None = None,
    output_dir: str | None = None,
) -> None:
    outcome = kickoff_crew(
        resume_text_path=resume_text_path,
        job_description_text_path=job_description_text_path,
        template_pdf_path=template_pdf_path,
        output_dir=output_dir,
    )
    print("\n\n=== CREW FINISHED ===\n\n")
    print(outcome.result.raw)
    if not outcome.score_targets_met:
        print(
            f"\nNote: after {outcome.rounds_run} full run(s), scores did not reach "
            f"MIN_RECRUITER_SCORE/MIN_ATS_SCORE (see .env.example). Last evaluation is still saved.\n",
            file=sys.stderr,
        )


def _cli() -> None:
    p = argparse.ArgumentParser(description="Automated resume tailoring (CrewAI)")
    p.add_argument("--resume", dest="resume_text", help="Path to candidate resume (.txt)")
    p.add_argument("--job-description", dest="job_description", help="Path to job description (.txt)")
    p.add_argument(
        "--template-pdf",
        dest="template_pdf",
        help="Reference layout PDF (e.g. input/resume_template.pdf)",
    )
    p.add_argument("--output-dir", dest="output_dir", help="Output directory")
    args = p.parse_args()
    run(
        resume_text_path=args.resume_text,
        job_description_text_path=args.job_description,
        template_pdf_path=args.template_pdf,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    _cli()
