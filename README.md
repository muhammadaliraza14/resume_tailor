# Automated Resume Tailoring (CrewAI)

Pipeline: **candidate resume (.txt)** + **job description (.txt)** → structured sections → tailored content → **PDF (and `.txt`) that follows the layout of `input/resume_template.pdf`**.

The template PDF (`resume_template.pdf`) is the **visual reference** (section order, headings, bullets, skill rows, education). Rendering is implemented in code so output is consistent; agents only supply **content** in the `StructuredResumeContent` schema.

## Setup

- Python 3.10–3.12, [uv](https://docs.astral.sh/uv/)
- `uv sync`
- Copy [`.env.example`](.env.example) to `.env` and set `OPENAI_API_KEY`

## Inputs (all plain text + template reference)

| Input | Default path | Notes |
|--------|----------------|------|
| Candidate resume | `input/resume.txt` | Your experience, skills, education as text |
| Job description | `input/job_description.txt` | Posting as text |
| Layout reference | `input/resume_template.pdf` | Sample resume PDF (section structure); passed to the crew as context |

Environment variables: `RESUME_TEXT_PATH` (or legacy `RESUME_PATH`), `JOB_DESCRIPTION_TEXT_PATH` (or `JOB_DESCRIPTION_PATH`), `TEMPLATE_PDF_PATH`, `OUTPUT_DIR`.

## Run

From the project root:

```bash
uv run resume_tailor \
  --resume input/resume.txt \
  --job-description input/job_description.txt \
  --template-pdf input/resume_template.pdf \
  --output-dir output
```

## Outputs

- `output/tailored_resume.pdf` — ReportLab PDF aligned with the template layout (summary, experience with bullets + Tech Used, three skill lines, education)
- `output/tailored_resume.txt` — same content as plain text (for evaluation / similarity)
- `output/resume_parsed.json`, `output/job_description_parsed.json`, `output/tailoring_summary.md`, `output/evaluation.md`

## Agents

1. **Resume parsing** — `read_text_file` → `StructuredResumeContent`
2. **Job description parsing** — `read_text_file` → `JobDescriptionStructure`
3. **Tailoring** — updates structured content, `write_tailored_resume_files` (JSON)
4. **Evaluator** — reads `tailored_resume.txt`, scores vs JD

## Limitations

- Resume and JD must be **`.txt`** for this flow (convert Word/PDF to text first if needed).
- The PDF matches the **designed** template style, not pixel-perfect cloning of arbitrary PDFs.
- `python-docx` remains in dependencies for legacy helpers but is not used in the main path.

## Layout code

See [`src/resume_tailor/documents.py`](src/resume_tailor/documents.py) (`render_structured_resume_pdf`) and schema in [`src/resume_tailor/models.py`](src/resume_tailor/models.py).
