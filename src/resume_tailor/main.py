#!/usr/bin/env python
from __future__ import annotations

import argparse
import os
import warnings
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from resume_tailor.crew import ResumeTailorCrew

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def run(
    resume_text_path: str | None = None,
    job_description_text_path: str | None = None,
    template_pdf_path: str | None = None,
    output_dir: str | None = None,
) -> None:

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

    inputs = {
        "resume_text_path": str(Path(resume).expanduser().resolve()),
        "job_description_text_path": str(Path(jd).expanduser().resolve()),
        "template_pdf_path": str(Path(template).expanduser().resolve()),
        "output_dir": str(Path(out).expanduser().resolve()),
        "current_date": str(datetime.now()),
    }

    Path(inputs["output_dir"]).mkdir(parents=True, exist_ok=True)

    result = ResumeTailorCrew().crew().kickoff(inputs=inputs)

    print("\n\n=== CREW FINISHED ===\n\n")
    print(result.raw)


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
