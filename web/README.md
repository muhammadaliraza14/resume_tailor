# Resume Tailor — Web UI

## Stack

- **Backend:** FastAPI (`src/resume_tailor/api/app.py`), in-memory job store, background CrewAI runs
- **Frontend:** React + TypeScript + Vite + **Tailwind CSS v4** (`web/frontend/`)

## Development

Terminal A — API (project root `resume_tailor/`):

```bash
uv sync
uv run resume_tailor_api
```

Terminal B — UI:

```bash
cd web/frontend
npm install
npm run dev
```

Open **http://localhost:5173**. The Vite dev server proxies `/api` to **http://127.0.0.1:8765**.

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Liveness |
| POST | `/api/jobs` | `multipart/form-data`: `resume` (.txt), `job_description` (.txt), optional `template_pdf` (.pdf). Returns `202` + `job` |
| GET | `/api/jobs/{id}` | Job status and download URLs when complete |
| GET | `/api/jobs/{id}/files/{filename}` | Download `tailored_resume.pdf`, `.txt`, `evaluation.md`, etc. |

Open **http://127.0.0.1:8765/docs** for interactive OpenAPI.

## Production notes

- Job state is **in-memory**; restarting the API loses pending job metadata (files remain on disk under `output/web_jobs/`).
- Crew runs are **long**; increase reverse-proxy timeouts if you deploy behind nginx.
- Set `OPENAI_API_KEY` (and any other keys) in the server environment or `.env` next to the project root.
