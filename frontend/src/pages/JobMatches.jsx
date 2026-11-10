import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { api, clearToken } from "../api/client";
import Navbar from "../components/Navbar";

function scoreColor(percentage) {
  if (percentage >= 75) return "#22c55e";
  if (percentage >= 50) return "#f59e0b";
  return "#ef4444";
}

function levelClass(level) {
  if (level === "Intern") return "bg-accent/10 text-accent-soft";
  if (level === "Junior") return "bg-success/10 text-success";
  return "bg-warning/10 text-warning";
}

function SkillChip({ skill, tone }) {
  const className =
    tone === "matched"
      ? "border-success/30 bg-success/10 text-success"
      : "border-warning/30 bg-warning/10 text-warning";
  return (
    <span
      className={`rounded-full border px-2.5 py-1 text-[11px] font-medium ${className}`}
    >
      {skill}
    </span>
  );
}

export default function JobMatches() {
  const { analysisId } = useParams();
  const navigate = useNavigate();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [level, setLevel] = useState("all");
  const [query, setQuery] = useState("");
  const [sortBy, setSortBy] = useState("score");

  useEffect(() => {
    let active = true;

    api
      .getJobMatches(analysisId)
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

  const matches = data?.matches || [];

  const levels = useMemo(
    () => Array.from(new Set(matches.map((item) => item.level))).sort(),
    [matches]
  );

  const visible = useMemo(() => {
    const needle = query.trim().toLowerCase();
    const filtered = matches.filter((item) => {
      if (level !== "all" && item.level !== level) return false;
      if (!needle) return true;
      const haystack = [
        item.title,
        item.company,
        ...item.matched_skills,
        ...item.missing_skills,
      ]
        .join(" ")
        .toLowerCase();
      return haystack.includes(needle);
    });

    return [...filtered].sort((left, right) => {
      if (sortBy === "company") {
        return left.company.localeCompare(right.company);
      }
      if (sortBy === "title") {
        return left.title.localeCompare(right.title);
      }
      return right.match_score - left.match_score;
    });
  }, [matches, level, query, sortBy]);

  if (loading) {
    return (
      <div className="min-h-screen bg-navy">
        <Navbar />
        <main className="mx-auto max-w-5xl px-6 py-12">
          <p className="text-sm text-slate-400">Menghitung kecocokan lowongan...</p>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-navy">
      <Navbar />

      <main className="mx-auto max-w-6xl px-6 py-10">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-accent-soft">
              Job Matches
            </p>
            <h1 className="mt-2 text-3xl font-bold text-white">
              Lowongan yang paling cocok
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-400">
              Persentase dihitung dari 60% kecocokan skill dan 40% kemiripan
              semantik. Kedua komponen ditampilkan terpisah.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link to={`/analysis/${analysisId}`} className="btn-ghost">
              Analisis
            </Link>
            <Link
              to={`/analysis/${analysisId}/skill-gap`}
              className="btn-ghost"
            >
              Skill gap
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

        {data && (
          <>
            <section className="mt-6 card">
              <div className="grid gap-4 sm:grid-cols-3">
                <div>
                  <label className="label" htmlFor="level-filter">
                    Level
                  </label>
                  <select
                    id="level-filter"
                    className="input"
                    value={level}
                    onChange={(event) => setLevel(event.target.value)}
                  >
                    <option value="all">Semua level</option>
                    {levels.map((item) => (
                      <option key={item} value={item}>
                        {item}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="label" htmlFor="skill-filter">
                    Cari skill / lowongan
                  </label>
                  <input
                    id="skill-filter"
                    className="input"
                    placeholder="Contoh: React"
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                  />
                </div>
                <div>
                  <label className="label" htmlFor="sort-by">
                    Urutkan
                  </label>
                  <select
                    id="sort-by"
                    className="input"
                    value={sortBy}
                    onChange={(event) => setSortBy(event.target.value)}
                  >
                    <option value="score">Kecocokan tertinggi</option>
                    <option value="company">Nama perusahaan</option>
                    <option value="title">Judul lowongan</option>
                  </select>
                </div>
              </div>
              <p className="mt-4 text-xs text-slate-500">
                Menampilkan {visible.length} dari {matches.length} lowongan.
              </p>
            </section>

            <div className="mt-6 space-y-4">
              {visible.map((item) => {
                const color = scoreColor(item.match_percentage);
                return (
                  <article key={item.job_id} className="card">
                    <div className="flex flex-wrap items-start justify-between gap-4">
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <h2 className="text-lg font-semibold text-white">
                            {item.title}
                          </h2>
                          <span
                            className={`rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider ${levelClass(item.level)}`}
                          >
                            {item.level}
                          </span>
                        </div>
                        <p className="mt-1 text-sm text-slate-400">
                          {item.company}
                        </p>
                      </div>
                      <div className="text-right">
                        <p
                          className="text-2xl font-bold"
                          style={{ color }}
                        >
                          {item.match_percentage.toFixed(1)}%
                        </p>
                        <p className="text-[10px] uppercase tracking-wider text-slate-500">
                          kecocokan
                        </p>
                      </div>
                    </div>

                    <div className="mt-4 h-2 overflow-hidden rounded-full bg-navy">
                      <div
                        className="h-full rounded-full transition-all"
                        style={{
                          width: `${Math.max(0, Math.min(100, item.match_percentage))}%`,
                          backgroundColor: color,
                        }}
                      />
                    </div>

                    <div className="mt-4 grid gap-3 sm:grid-cols-2">
                      <div className="rounded-xl border border-border bg-navy/60 p-3">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-slate-400">
                            Kecocokan skill
                          </span>
                          <span className="font-semibold text-slate-200">
                            {(item.skill_coverage * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-navy">
                          <div
                            className="h-full rounded-full bg-accent"
                            style={{
                              width: `${item.skill_coverage * 100}%`,
                            }}
                          />
                        </div>
                      </div>
                      <div className="rounded-xl border border-border bg-navy/60 p-3">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-slate-400">
                            Kemiripan semantik
                          </span>
                          <span className="font-semibold text-slate-200">
                            {(item.semantic_similarity * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-navy">
                          <div
                            className="h-full rounded-full bg-accent-soft"
                            style={{
                              width: `${item.semantic_similarity * 100}%`,
                            }}
                          />
                        </div>
                      </div>
                    </div>

                    <div className="mt-4 space-y-2">
                      <div>
                        <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                          Skill cocok
                        </p>
                        <div className="mt-1.5 flex flex-wrap gap-1.5">
                          {item.matched_skills.length ? (
                            item.matched_skills.map((skill) => (
                              <SkillChip
                                key={`matched-${skill}`}
                                skill={skill}
                                tone="matched"
                              />
                            ))
                          ) : (
                            <span className="text-xs text-slate-600">
                              Belum ada
                            </span>
                          )}
                        </div>
                      </div>
                      <div>
                        <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                          Skill kurang
                        </p>
                        <div className="mt-1.5 flex flex-wrap gap-1.5">
                          {item.missing_skills.length ? (
                            item.missing_skills.map((skill) => (
                              <SkillChip
                                key={`missing-${skill}`}
                                skill={skill}
                                tone="missing"
                              />
                            ))
                          ) : (
                            <span className="text-xs text-success">
                              Semua skill terpenuhi
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    <p className="mt-4 text-xs leading-relaxed text-slate-400">
                      {item.description}
                    </p>
                  </article>
                );
              })}

              {!visible.length && (
                <p className="card text-sm text-slate-400">
                  Tidak ada lowongan yang sesuai filter.
                </p>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
