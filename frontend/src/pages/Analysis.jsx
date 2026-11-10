import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { api, clearToken } from "../api/client";
import Navbar from "../components/Navbar";

const GAUGE_RADIUS = 70;
const GAUGE_CIRCUMFERENCE = 2 * Math.PI * GAUGE_RADIUS;

function scoreColor(score, maxScore = 100) {
  const ratio = maxScore > 0 ? score / maxScore : 0;
  if (ratio >= 0.8) return "#22c55e";
  if (ratio >= 0.6) return "#f59e0b";
  return "#ef4444";
}

function scoreLabel(score) {
  if (score >= 80) return "Sangat baik";
  if (score >= 60) return "Cukup baik";
  if (score >= 40) return "Perlu perbaikan";
  return "Butuh banyak perbaikan";
}

function ScoreGauge({ score }) {
  const offset = GAUGE_CIRCUMFERENCE * (1 - Math.min(score, 100) / 100);
  const color = scoreColor(score);

  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 180 180" className="h-52 w-52" role="img" aria-label={`Skor ${score} dari 100`}>
        <circle
          cx="90"
          cy="90"
          r={GAUGE_RADIUS}
          fill="none"
          stroke="#1e293b"
          strokeWidth="14"
        />
        <circle
          cx="90"
          cy="90"
          r={GAUGE_RADIUS}
          fill="none"
          stroke={color}
          strokeWidth="14"
          strokeLinecap="round"
          strokeDasharray={GAUGE_CIRCUMFERENCE}
          strokeDashoffset={offset}
          transform="rotate(-90 90 90)"
        />
        <text
          x="90"
          y="88"
          textAnchor="middle"
          fill="#f8fafc"
          fontSize="40"
          fontWeight="700"
        >
          {score}
        </text>
        <text
          x="90"
          y="112"
          textAnchor="middle"
          fill="#94a3b8"
          fontSize="13"
        >
          dari 100
        </text>
      </svg>
      <p className="mt-2 text-sm font-semibold" style={{ color }}>
        {scoreLabel(score)}
      </p>
    </div>
  );
}

function CriterionBar({ criterion }) {
  const ratio =
    criterion.max_score > 0
      ? Math.round((criterion.score / criterion.max_score) * 100)
      : 0;

  return (
    <div className="rounded-xl border border-border bg-navy/60 p-4">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-sm font-semibold text-white">{criterion.label}</h3>
        <span className="text-xs font-semibold text-slate-300">
          {criterion.score}/{criterion.max_score}
        </span>
      </div>
      <div className="mt-3 h-2 overflow-hidden rounded-full bg-navy">
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${ratio}%`, backgroundColor: scoreColor(criterion.score, criterion.max_score) }}
        />
      </div>
      <ul className="mt-3 space-y-1">
        {criterion.reasons.map((reason, index) => (
          <li key={index} className="text-xs leading-relaxed text-slate-400">
            {reason}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function Analysis() {
  const { analysisId } = useParams();
  const navigate = useNavigate();

  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [rerunning, setRerunning] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    api
      .getAnalysis(analysisId)
      .then((data) => {
        if (active) setAnalysis(data);
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

  async function handleRerun() {
    if (!analysis || rerunning) return;
    setRerunning(true);
    setError("");
    try {
      const created = await api.createAnalysis(analysis.cv_id);
      navigate(`/analysis/${created.id}`, { replace: true });
    } catch (err) {
      if (err.status === 401) {
        clearToken();
        navigate("/login", { replace: true });
        return;
      }
      setError(err.message);
      setRerunning(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-navy">
        <Navbar />
        <main className="mx-auto max-w-5xl px-6 py-12">
          <p className="text-sm text-slate-400">Menganalisis CV...</p>
        </main>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="min-h-screen bg-navy">
        <Navbar />
        <main className="mx-auto max-w-5xl px-6 py-12">
          <p className="text-sm text-red-300">
            {error || "Analisis tidak ditemukan."}
          </p>
          <Link to="/dashboard" className="btn-ghost mt-6">
            Kembali ke dashboard
          </Link>
        </main>
      </div>
    );
  }

  const criteria = analysis.score_breakdown?.criteria || [];
  const suggestions = analysis.suggestions?.items || [];
  const sourceLabel =
    analysis.suggestions?.source === "llm" ? "Saran AI" : "Saran otomatis";

  return (
    <div className="min-h-screen bg-navy">
      <Navbar />

      <main className="mx-auto max-w-5xl px-6 py-10">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-accent-soft">
              Hasil analisis
            </p>
            <h1 className="mt-2 text-3xl font-bold text-white">
              Skor dan saran CV
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-400">
              Skor dihitung otomatis dari rubrik terukur. Saran teks tidak
              mengubah angka apa pun.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link to="/dashboard" className="btn-ghost">
              Dashboard
            </Link>
            <Link
              to={`/analysis/${analysis.id}/jobs`}
              className="btn-ghost"
            >
              Job matches
            </Link>
            <Link
              to={`/analysis/${analysis.id}/skill-gap`}
              className="btn-ghost"
            >
              Skill gap
            </Link>
            <button
              type="button"
              onClick={handleRerun}
              className="btn-primary"
              disabled={rerunning}
            >
              {rerunning ? "Menganalisis..." : "Analisis ulang"}
            </button>
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
          <section className="card flex flex-col items-center justify-center lg:col-span-1">
            <ScoreGauge score={analysis.total_score} />
          </section>

          <section className="card lg:col-span-2">
            <h2 className="text-lg font-semibold text-white">
              Breakdown per kriteria
            </h2>
            <p className="mt-1 text-xs text-slate-500">
              Setiap kriteria dihitung dengan aturan tetap, bukan oleh LLM.
            </p>
            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              {criteria.map((criterion) => (
                <CriterionBar key={criterion.key} criterion={criterion} />
              ))}
            </div>
          </section>
        </div>

        <section className="mt-6 card">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-lg font-semibold text-white">
              Saran perbaikan
            </h2>
            <span className="rounded-full border border-accent/30 bg-accent/10 px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-accent-soft">
              {sourceLabel}
            </span>
          </div>
          <ol className="mt-5 space-y-3">
            {suggestions.map((suggestion, index) => (
              <li
                key={index}
                className="flex gap-3 rounded-xl border border-border bg-navy/60 px-4 py-3"
              >
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-accent/15 text-xs font-bold text-accent-soft">
                  {index + 1}
                </span>
                <p className="text-sm leading-relaxed text-slate-200">
                  {suggestion}
                </p>
              </li>
            ))}
          </ol>
        </section>

        <p className="mt-6 text-xs leading-relaxed text-slate-500">
          Ingin memperbaiki data dulu? Koreksi hasil ekstraksi dari halaman
          review, lalu jalankan analisis ulang.
        </p>
      </main>
    </div>
  );
}
