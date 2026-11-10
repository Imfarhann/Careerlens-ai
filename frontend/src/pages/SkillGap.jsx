import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { api, clearToken } from "../api/client";
import Navbar from "../components/Navbar";

export default function SkillGap() {
  const { analysisId } = useParams();
  const navigate = useNavigate();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const storageKey = `careerlens:roadmap:${analysisId}`;
  const [learned, setLearned] = useState([]);

  useEffect(() => {
    try {
      const stored = JSON.parse(localStorage.getItem(storageKey) || "[]");
      setLearned(Array.isArray(stored) ? stored : []);
    } catch {
      setLearned([]);
    }
  }, [storageKey]);

  useEffect(() => {
    let active = true;

    api
      .getSkillGap(analysisId)
      .then((result) => {
        if (active) setData(result);
      })
      .catch((err) => {
        if (!active) return;
        if (err.status === 401) {
          clearToken();
          navigate("/login", { replace: true });
          return;
        }
        setError(err.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [analysisId, navigate]);

  function toggleLearned(skill) {
    setLearned((previous) => {
      const next = previous.includes(skill)
        ? previous.filter((item) => item !== skill)
        : [...previous, skill];
      try {
        localStorage.setItem(storageKey, JSON.stringify(next));
      } catch {
        return next;
      }
      return next;
    });
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-navy">
        <Navbar />
        <main className="mx-auto max-w-5xl px-6 py-12">
          <p className="text-sm text-slate-400">Menyusun roadmap skill...</p>
        </main>
      </div>
    );
  }

  const gaps = data?.gaps || [];
  const topJobs = data?.top_jobs || [];
  const maxFrequency = gaps.reduce(
    (highest, item) => Math.max(highest, item.frequency),
    1
  );
  const learnedCount = gaps.filter((item) =>
    learned.includes(item.skill)
  ).length;

  return (
    <div className="min-h-screen bg-navy">
      <Navbar />

      <main className="mx-auto max-w-6xl px-6 py-10">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-accent-soft">
              Skill Gap &amp; Roadmap
            </p>
            <h1 className="mt-2 text-3xl font-bold text-white">
              Skill yang perlu dipelajari
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-400">
              Diurutkan dari skill yang paling sering kurang pada 10 lowongan
              teratas. Setiap skill dilengkapi sumber belajar resmi atau kursus
              gratis.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link to={`/analysis/${analysisId}`} className="btn-ghost">
              Analisis
            </Link>
            <Link to={`/analysis/${analysisId}/jobs`} className="btn-ghost">
              Job matches
            </Link>
            <Link to="/dashboard" className="btn-ghost">
              Dashboard
            </Link>
          </div>
        </div>

        {error && (
          <p
            role="alert"
            className="mt-6 rounded-lg border border-danger/40 bg-danger/10 px-4 py-3 text-sm text-red-300"
          >
            {error}
          </p>
        )}

        <div className="mt-8 grid gap-6 lg:grid-cols-3">
          <section className="card lg:col-span-2">
            <h2 className="text-lg font-semibold text-white">
              Roadmap belajar
            </h2>
            <p className="mt-1 text-xs text-slate-500">
              Prioritaskan dari atas. Angka menunjukkan berapa lowongan teratas
              yang membutuhkan skill tersebut.
            </p>

            {gaps.length > 0 && (
              <div className="mt-4 rounded-xl border border-border bg-navy/60 p-3">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400">Sudah dipelajari</span>
                  <span className="font-semibold text-slate-200">
                    {learnedCount}/{gaps.length}
                  </span>
                </div>
                <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-navy">
                  <div
                    className="h-full rounded-full bg-success transition-all"
                    style={{
                      width: `${gaps.length ? Math.round((learnedCount / gaps.length) * 100) : 0}%`,
                    }}
                  />
                </div>
              </div>
            )}

            <ol className="mt-5 space-y-4">
              {gaps.map((item, index) => (
                <li
                  key={item.skill}
                  className="rounded-xl border border-border bg-navy/60 p-4"
                >
                  <div className="flex flex-wrap items-start gap-3">
                    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent/15 text-xs font-bold text-accent-soft">
                      {index + 1}
                    </span>
                    <input
                      type="checkbox"
                      checked={learned.includes(item.skill)}
                      onChange={() => toggleLearned(item.skill)}
                      aria-label={`Tandai ${item.skill} sudah dipelajari`}
                      className="mt-1.5 h-4 w-4 shrink-0 cursor-pointer accent-accent"
                    />
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3
                          className={`text-sm font-semibold ${
                            learned.includes(item.skill)
                              ? "text-slate-500 line-through"
                              : "text-white"
                          }`}
                        >
                          {item.skill}
                        </h3>
                        <span className="rounded-full border border-border px-2 py-0.5 text-[10px] uppercase tracking-wider text-slate-400">
                          {item.category}
                        </span>
                        {learned.includes(item.skill) && (
                          <span className="rounded-full border border-success/30 bg-success/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-success">
                            Sudah dipelajari
                          </span>
                        )}
                      </div>
                      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-navy">
                        <div
                          className="h-full rounded-full bg-warning"
                          style={{
                            width: `${Math.round((item.frequency / maxFrequency) * 100)}%`,
                          }}
                        />
                      </div>
                      <p className="mt-2 text-xs text-slate-400">
                        Kurang di {item.frequency} dari {topJobs.length || 10}{" "}
                        lowongan teratas
                        {item.job_count > 0
                          ? `, ${item.job_count} di antaranya wajib`
                          : ""}
                        .
                      </p>

                      <div className="mt-3 space-y-1">
                        {item.resources.map((resource) => (
                          <a
                            key={resource.url}
                            href={resource.url}
                            target="_blank"
                            rel="noreferrer"
                            className="block text-xs font-medium text-accent-soft underline-offset-2 hover:text-white hover:underline"
                          >
                            {resource.title}
                          </a>
                        ))}
                        {!item.resources.length && (
                          <p className="text-xs text-slate-600">
                            Belum ada sumber belajar.
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                </li>
              ))}

              {!gaps.length && (
                <p className="rounded-xl border border-border bg-navy/60 p-4 text-sm text-success">
                  Semua skill pada lowongan teratas sudah terpenuhi.
                </p>
              )}
            </ol>
          </section>

          <aside className="space-y-6">
            <div className="card">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
                10 lowongan teratas
              </h2>
              <ol className="mt-4 space-y-3">
                {topJobs.map((job, index) => (
                  <li key={job.job_id} className="flex items-start gap-3">
                    <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-navy text-[10px] font-bold text-slate-400">
                      {index + 1}
                    </span>
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-slate-200">
                        {job.title}
                      </p>
                      <p className="text-xs text-slate-500">
                        {job.company} · {job.level}
                      </p>
                    </div>
                    <span className="ml-auto text-xs font-semibold text-accent-soft">
                      {job.match_percentage.toFixed(1)}%
                    </span>
                  </li>
                ))}
              </ol>
            </div>

            <div className="card border-accent/30 bg-accent/5">
              <h2 className="text-sm font-semibold text-white">Cara membaca</h2>
              <p className="mt-2 text-sm leading-relaxed text-slate-400">
                Skill gap dihitung dari perbandingan himpunan skill, bukan dari
                LLM. Perbaiki profil CV lalu jalankan analisis ulang untuk
                memperbarui roadmap.
              </p>
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
}
