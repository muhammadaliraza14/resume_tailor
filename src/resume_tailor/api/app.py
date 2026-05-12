from __future__ import annotations

import os
import traceback
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from resume_tailor.crew_scores import extract_evaluation_scores
from resume_tailor.main import kickoff_crew
from resume_tailor.paths import project_root as _project_root


class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


@dataclass
class JobRecord:
    id: str
    status: JobStatus = JobStatus.pending
    created_at: str = ""
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    output_dir: Optional[str] = None
    resume_path: str = ""
    job_description_path: str = ""
    template_pdf_path: str = ""
    error: Optional[str] = None
    result_preview: Optional[str] = None
    score_1_to_10: Optional[int] = None
    ats_readiness_score_0_to_100: Optional[int] = None
    refinement_rounds_used: Optional[int] = None
    score_targets_met: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "id": self.id,
            "status": self.status.value,
            "created_at": self.created_at,
        }
        if self.started_at:
            d["started_at"] = self.started_at
        if self.finished_at:
            d["finished_at"] = self.finished_at
        if self.output_dir:
            d["output_dir"] = self.output_dir
        if self.error:
            d["error"] = self.error
        if self.result_preview:
            d["result_preview"] = self.result_preview[:4000]
        if self.score_1_to_10 is not None:
            d["score_1_to_10"] = self.score_1_to_10
        if self.ats_readiness_score_0_to_100 is not None:
            d["ats_readiness_score_0_to_100"] = self.ats_readiness_score_0_to_100
        if self.refinement_rounds_used is not None:
            d["refinement_rounds_used"] = self.refinement_rounds_used
        if self.score_targets_met is not None:
            d["score_targets_met"] = self.score_targets_met
        if self.status == JobStatus.completed and self.output_dir:
            base = f"/api/jobs/{self.id}/files"
            d["downloads"] = {
                "pdf": f"{base}/tailored_resume.pdf",
                "txt": f"{base}/tailored_resume.txt",
                "evaluation": f"{base}/evaluation.md",
                "summary": f"{base}/tailoring_summary.md",
            }
        return d


_jobs: Dict[str, JobRecord] = {}
_lock = Lock()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _job_root() -> Path:
    return _project_root() / "output" / "web_jobs"


def _cors_config() -> tuple[list[str], bool]:
    """
    CORS_ORIGINS: comma-separated list, or * for any origin (credentials disabled).
    Unset: local Vite dev defaults only.
    """
    raw = os.getenv("CORS_ORIGINS", "").strip()
    if raw == "*":
        return ["*"], False
    if raw:
        origins = [o.strip() for o in raw.split(",") if o.strip()]
        if origins:
            return origins, True
    return [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:4173",
        "http://localhost:4173",
        "http://127.0.0.1:8765",
        "http://localhost:8765",
    ], True


def _execute_job(job_id: str) -> None:
    with _lock:
        rec = _jobs.get(job_id)
        if not rec:
            return
        rec.status = JobStatus.running
        rec.started_at = _utc_now()
        resume_path = rec.resume_path
        jd_path = rec.job_description_path
        template_path = rec.template_pdf_path
        out_dir = rec.output_dir or ""

    try:
        outcome = kickoff_crew(
            resume_text_path=resume_path,
            job_description_text_path=jd_path,
            template_pdf_path=template_path,
            output_dir=out_dir,
        )
        result = outcome.result
        preview = str(getattr(result, "raw", result))
        fit_score, ats_score = extract_evaluation_scores(result)
        with _lock:
            r = _jobs.get(job_id)
            if r:
                r.status = JobStatus.completed
                r.finished_at = _utc_now()
                r.result_preview = preview
                r.score_1_to_10 = fit_score
                r.ats_readiness_score_0_to_100 = ats_score
                r.refinement_rounds_used = outcome.rounds_run
                r.score_targets_met = outcome.score_targets_met
    except Exception as e:  # noqa: BLE001
        tb = traceback.format_exc()
        with _lock:
            r = _jobs.get(job_id)
            if r:
                r.status = JobStatus.failed
                r.finished_at = _utc_now()
                r.error = f"{e}\n\n{tb}"


def create_app() -> FastAPI:
    app = FastAPI(title="Resume Tailor API", version="0.1.0")

    cors_origins, cors_credentials = _cors_config()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=cors_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/jobs")
    def create_job(
        background_tasks: BackgroundTasks,
        resume: UploadFile = File(..., description="Candidate resume as .txt"),
        job_description: UploadFile = File(..., description="Job description as .txt"),
        template_pdf: UploadFile | None = File(None, description="Optional layout reference PDF"),
    ) -> JSONResponse:
        if not resume.filename or not resume.filename.lower().endswith(".txt"):
            raise HTTPException(400, "Resume must be a .txt file")
        if not job_description.filename or not job_description.filename.lower().endswith(".txt"):
            raise HTTPException(400, "Job description must be a .txt file")
        if template_pdf and template_pdf.filename and not template_pdf.filename.lower().endswith(".pdf"):
            raise HTTPException(400, "Template must be a .pdf file when provided")

        job_id = str(uuid.uuid4())
        root = _project_root()
        job_dir = _job_root() / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        work = job_dir / "work"
        work.mkdir(parents=True, exist_ok=True)
        out_dir = job_dir / "output"
        out_dir.mkdir(parents=True, exist_ok=True)

        resume_path = work / "resume.txt"
        jd_path = work / "job_description.txt"

        resume_path.write_bytes(resume.file.read())
        jd_path.write_bytes(job_description.file.read())

        if template_pdf and template_pdf.filename:
            tpl_path = work / "resume_template.pdf"
            tpl_path.write_bytes(template_pdf.file.read())
            template_path = str(tpl_path.resolve())
        else:
            default_tpl = root / "input" / "resume_template.pdf"
            if not default_tpl.is_file():
                raise HTTPException(500, "Default input/resume_template.pdf is missing")
            template_path = str(default_tpl.resolve())

        rec = JobRecord(
            id=job_id,
            status=JobStatus.pending,
            created_at=_utc_now(),
            output_dir=str(out_dir.resolve()),
            resume_path=str(resume_path.resolve()),
            job_description_path=str(jd_path.resolve()),
            template_pdf_path=template_path,
        )
        with _lock:
            _jobs[job_id] = rec

        background_tasks.add_task(_execute_job, job_id)

        return JSONResponse(
            status_code=202,
            content={"job": rec.to_dict()},
        )

    @app.get("/api/jobs/{job_id}")
    def get_job(job_id: str) -> dict[str, Any]:
        with _lock:
            rec = _jobs.get(job_id)
        if not rec:
            raise HTTPException(404, "Job not found")
        return rec.to_dict()

    _allowed_files = frozenset(
        {
            "tailored_resume.pdf",
            "tailored_resume.txt",
            "evaluation.md",
            "tailoring_summary.md",
            "resume_parsed.json",
            "job_description_parsed.json",
        }
    )

    @app.get("/api/jobs/{job_id}/files/{filename}")
    def download_file(job_id: str, filename: str) -> FileResponse:
        if filename not in _allowed_files:
            raise HTTPException(400, "Unknown file")
        with _lock:
            rec = _jobs.get(job_id)
        if not rec or not rec.output_dir:
            raise HTTPException(404, "Job not found")
        if rec.status != JobStatus.completed:
            raise HTTPException(409, "Job not completed yet")
        path = Path(rec.output_dir) / filename
        if not path.is_file():
            raise HTTPException(404, "File not generated")
        return FileResponse(
            path,
            filename=filename,
            media_type="application/octet-stream",
        )

    dist = _project_root() / "web" / "frontend" / "dist"
    if dist.is_dir():
        from fastapi.staticfiles import StaticFiles

        app.mount("/", StaticFiles(directory=str(dist), html=True), name="ui")

    return app


app = create_app()


def run_server() -> None:
    import uvicorn

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8765"))
    uvicorn.run(app, host=host, port=port, reload=False)
