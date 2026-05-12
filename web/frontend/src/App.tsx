import { useCallback, useEffect, useRef, useState } from "react";

type JobStatus = "pending" | "running" | "completed" | "failed";

type Downloads = {
  pdf: string;
  txt: string;
  evaluation: string;
  summary: string;
};

type Job = {
  id: string;
  status: JobStatus;
  created_at: string;
  started_at?: string;
  finished_at?: string;
  output_dir?: string;
  error?: string;
  result_preview?: string;
  score_1_to_10?: number;
  ats_readiness_score_0_to_100?: number;
  downloads?: Downloads;
};

function statusBadgeClass(status: JobStatus): string {
  const base =
    "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset";
  switch (status) {
    case "completed":
      return `${base} bg-emerald-50 text-emerald-800 ring-emerald-600/20`;
    case "failed":
      return `${base} bg-red-50 text-red-800 ring-red-600/20`;
    case "running":
      return `${base} bg-sky-50 text-sky-800 ring-sky-600/20`;
    default:
      return `${base} bg-amber-50 text-amber-900 ring-amber-600/20`;
  }
}

export default function App() {
  const [resume, setResume] = useState<File | null>(null);
  const [jd, setJd] = useState<File | null>(null);
  const [template, setTemplate] = useState<File | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const pollRef = useRef<number | null>(null);

  const stopPoll = useCallback(() => {
    if (pollRef.current != null) {
      window.clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const fetchJob = useCallback(
    async (id: string) => {
      try {
        const res = await fetch(`/api/jobs/${id}`);
        if (!res.ok) {
          const text = await res.text();
          throw new Error(text || res.statusText);
        }
        const data = (await res.json()) as Job;
        setJob(data);
        if (data.status === "completed" || data.status === "failed") {
          stopPoll();
          setSubmitting(false);
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
        stopPoll();
        setSubmitting(false);
      }
    },
    [stopPoll]
  );

  useEffect(() => {
    return () => stopPoll();
  }, [stopPoll]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!resume || !jd) {
      setError("Please choose a resume (.txt) and job description (.txt).");
      return;
    }
    setSubmitting(true);
    const fd = new FormData();
    fd.append("resume", resume);
    fd.append("job_description", jd);
    if (template) fd.append("template_pdf", template);
    try {
      const res = await fetch("/api/jobs", { method: "POST", body: fd });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || res.statusText);
      }
      const body = (await res.json()) as { job: Job };
      setJob(body.job);
      stopPoll();
      pollRef.current = window.setInterval(() => {
        void fetchJob(body.job.id);
      }, 2500);
      void fetchJob(body.job.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setSubmitting(false);
    }
  };

  const fileInputClass =
    "mt-1 block w-full cursor-pointer rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 file:mr-3 file:rounded-md file:border-0 file:bg-teal-700 file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-white hover:file:bg-teal-800";

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-100 to-slate-200/80 pb-16 pt-10">
      <div className="mx-auto max-w-2xl px-4 sm:px-6">
        <header className="mb-10 text-center sm:text-left">
          <p className="mb-1 text-sm font-medium uppercase tracking-wide text-teal-800">
            CrewAI resume pipeline
          </p>
          <h1 className="text-balance text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Resume Tailor
          </h1>
          <p className="mx-auto mt-3 max-w-xl text-pretty text-slate-600 sm:mx-0">
            Upload your resume and job description as plain text. We tailor content to the role and
            generate a PDF using your project&apos;s template layout.
          </p>
        </header>

        <form
          onSubmit={onSubmit}
          className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-lg shadow-slate-900/5 sm:p-8"
        >
          <div className="space-y-6">
            <div>
              <label className="block">
                <span className="text-sm font-semibold text-slate-800">Resume</span>
                <span className="ml-1 text-xs font-normal text-slate-500">(.txt required)</span>
                <input
                  type="file"
                  accept=".txt,text/plain"
                  onChange={(ev) => setResume(ev.target.files?.[0] ?? null)}
                  className={fileInputClass}
                />
              </label>
              {resume && (
                <p className="mt-1.5 text-xs text-slate-500">Selected: {resume.name}</p>
              )}
            </div>

            <div>
              <label className="block">
                <span className="text-sm font-semibold text-slate-800">Job description</span>
                <span className="ml-1 text-xs font-normal text-slate-500">(.txt required)</span>
                <input
                  type="file"
                  accept=".txt,text/plain"
                  onChange={(ev) => setJd(ev.target.files?.[0] ?? null)}
                  className={fileInputClass}
                />
              </label>
              {jd && <p className="mt-1.5 text-xs text-slate-500">Selected: {jd.name}</p>}
            </div>

            <div>
              <label className="block">
                <span className="text-sm font-semibold text-slate-800">Template PDF</span>
                <span className="ml-1 text-xs font-normal text-slate-500">(optional)</span>
                <input
                  type="file"
                  accept=".pdf,application/pdf"
                  onChange={(ev) => setTemplate(ev.target.files?.[0] ?? null)}
                  className={fileInputClass}
                />
              </label>
              <p className="mt-1.5 text-xs text-slate-500">
                Omit to use the server default template.
                {template && <span className="block pt-0.5">Selected: {template.name}</span>}
              </p>
            </div>
          </div>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center justify-center rounded-xl bg-teal-700 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-teal-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-600 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:bg-slate-400"
            >
              {submitting ? (
                <>
                  <svg
                    className="-ml-1 mr-2 h-4 w-4 animate-spin text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    aria-hidden
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Running crew…
                </>
              ) : (
                "Tailor resume"
              )}
            </button>
            <p className="text-xs text-slate-500">
              Runs can take several minutes. Keep this tab open; status updates automatically.
            </p>
          </div>
        </form>

        {error && (
          <div
            role="alert"
            className="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-900"
          >
            <p className="font-semibold">Something went wrong</p>
            <pre className="mt-2 max-h-48 overflow-auto whitespace-pre-wrap font-mono text-xs text-red-800">
              {error}
            </pre>
          </div>
        )}

        {job && (
          <section className="mt-10 rounded-2xl border border-slate-200/80 bg-white p-6 shadow-md sm:p-8">
            <div className="flex flex-col gap-4 border-b border-slate-100 pb-4 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">Job status</h2>
                <p className="mt-1 break-all font-mono text-xs text-slate-500">{job.id}</p>
              </div>
              <span className={statusBadgeClass(job.status)}>{job.status}</span>
            </div>

            {job.started_at && (
              <p className="mt-3 text-xs text-slate-500">
                Started: {new Date(job.started_at).toLocaleString()}
                {job.finished_at && (
                  <> · Finished: {new Date(job.finished_at).toLocaleString()}</>
                )}
              </p>
            )}

            {job.error && (
              <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3">
                <p className="text-sm font-medium text-red-900">Crew error</p>
                <pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap font-mono text-xs text-red-800">
                  {job.error}
                </pre>
              </div>
            )}

            {job.status === "completed" &&
              (job.score_1_to_10 != null || job.ats_readiness_score_0_to_100 != null) && (
                <div className="mt-6 rounded-xl border border-slate-200 bg-slate-50/80 p-4">
                  <h3 className="text-sm font-semibold text-slate-800">Scores</h3>
                  <p className="mt-1 text-xs text-slate-500">
                    Recruiter fit is a holistic 1–10 rating. ATS readiness is a heuristic 0–100 score from
                    keyword overlap, plain-text signals, and ATS best-practice checklist (see evaluation download).
                  </p>
                  <dl className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
                    {job.score_1_to_10 != null && (
                      <div className="rounded-lg border border-slate-200 bg-white px-3 py-2">
                        <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">
                          Recruiter fit
                        </dt>
                        <dd className="text-2xl font-semibold text-slate-900">{job.score_1_to_10}/10</dd>
                      </div>
                    )}
                    {job.ats_readiness_score_0_to_100 != null && (
                      <div className="rounded-lg border border-slate-200 bg-white px-3 py-2">
                        <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">
                          ATS readiness
                        </dt>
                        <dd className="text-2xl font-semibold text-slate-900">
                          {job.ats_readiness_score_0_to_100}/100
                        </dd>
                      </div>
                    )}
                  </dl>
                </div>
              )}

            {job.downloads && (
              <div className="mt-6">
                <h3 className="text-sm font-semibold text-slate-800">Downloads</h3>
                <ul className="mt-3 divide-y divide-slate-100 rounded-xl border border-slate-200 bg-slate-50/50">
                  {(
                    [
                      ["PDF resume", job.downloads.pdf],
                      ["Plain text", job.downloads.txt],
                      ["Evaluation", job.downloads.evaluation],
                      ["Tailoring summary", job.downloads.summary],
                    ] as const
                  ).map(([label, href]) => (
                    <li key={label}>
                      <a
                        href={href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center justify-between px-4 py-3 text-sm font-medium text-teal-800 transition hover:bg-white hover:text-teal-950"
                      >
                        {label}
                        <span className="text-slate-400" aria-hidden>
                          →
                        </span>
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {job.result_preview && job.status === "completed" && (
              <details className="mt-6 group">
                <summary className="cursor-pointer list-none text-sm font-medium text-slate-700 marker:hidden [&::-webkit-details-marker]:hidden">
                  <span className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 transition group-open:border-teal-200 group-open:bg-teal-50/50">
                    <span className="text-slate-500 group-open:rotate-90">▸</span>
                    Raw crew output (truncated)
                  </span>
                </summary>
                <pre className="mt-3 max-h-72 overflow-auto rounded-lg border border-slate-200 bg-slate-50 p-4 font-mono text-xs leading-relaxed text-slate-700">
                  {job.result_preview}
                </pre>
              </details>
            )}
          </section>
        )}
      </div>
    </div>
  );
}
