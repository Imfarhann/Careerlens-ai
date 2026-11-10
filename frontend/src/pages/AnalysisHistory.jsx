import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { api, clearToken } from "../api/client";
import Navbar from "../components/Navbar";

const TOOLTIP_STYLE = {
  backgroundColor: "#111A2E",
  border: "1px solid #1E2A44",
  borderRadius: "8px",
  color: "#f8fafc",
  fontSize: 12,
};

function formatDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return date.toLocaleDateString("id-ID", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function deltaClass(value) {
  if (value > 0) return "text-success";
  if (value < 0) return "text-danger";
  return "text-slate-400";
}

export default function AnalysisHistory() {
  const navigate = useNavigate();

  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [baseId, setBaseId] = useState("");
  const [compareId, setCompareId] = useState("");
  const [comparison, setComparison] = useState(null);
  const [compareError, setCompareError] = useState("");
  const [comparing, setComparing] = useState(false);

  useEffect(() => {
    let active = true;

    api
      .getAnalyses()
      .then((result) => {
        if (!active) return;
        const analyses = result.analyses || [];
        setHistory(analyses);
        if (analyses.length) {
          setBaseId(analyses[0].id);
          setCompareId(analyses[1]?.id || analyses[0].id);
        }
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
  }, [navigate]);

  async function handleCompare() {
    if (!baseId || !compareId || baseId === compareId) return;
    setComparing(true);
    setCompareError("");
    try {
      const result = await api.compareAnalyses(baseId, compareId);
      setComparison(result);
    } catch (err) {
      if (err.status === 401) {
        clearToken();
        navigate("/login", { replace: true });
        return;
      }
      setCompareError(err.message);
    } finally {
      setComparing(false);
    }
  }

  const chartData = [...history]
    .reverse()
    .map((item) => ({
      date: formatDate(item.created_at),
      score: item.total_score,
      id: item.id,
    }));

  return (
    <div className="min-h-screen bg-navy">
      <Navbar />

      <main className="mx-auto max-w-6xl px-6 py-10">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-accent-soft">
              Riwayat
            </p>
            <h1 className="mt-2 text-3xl font-bold text-white">
              Perkembangan skor CV
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-400">
              Setiap titik adalah hasil analisis yang benar-benar tersimpan.
              Bandingkan dua analisis untuk melihat perubahan per kriteria.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link to="/dashboard" className="btn-ghost">
              Dashboard
            </Link>
            <Link to="/upload" className="btn-primary">
              Upload CV
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

        {loading && (
          <div className="mt-10 grid gap-6 lg:grid-cols-3">
            <div className="card animate-pulse lg:col-span-2">
              <div className="h-4 w-1/3 rounded bg-navy" />
              <div className="mt-4 h-56 rounded bg-navy" />
            </div>
            <div className="card animate-pulse">
              <div className="h-4 w-1/2 rounded bg-navy" />
              <div className="mt-4 h-56 rounded bg-navy" />
            </div>
          </div>
        )}

        {!loading && !error && !history.length && (
          <section className="card mt-10">
            <h2 className="text-lg font-semibold text-white">
              Belum ada riwayat
            </h2>
            <p className="mt-2 max-w-xl text-sm leading-relaxed text-slate-400">
              Analisis CV pertama Anda akan muncul di sini beserta grafik
              perkembangan skornya.
            </p>
            <Link to="/upload" className="btn-primary mt-5">
              Upload CV
            </Link>
          </section>
        )}

        {!loading && history.length > 0 && (
          <>
            <div className="mt-8 grid gap-6 lg:grid-cols-3">
              <section className="card lg:col-span-2">
                <h2 className="text-lg font-semibold text-white">
                  Grafik perkembangan
                </h2>
                <p className="mt-1 text-xs text-slate-500">
                  Skor total dari waktu ke waktu, skala 0-100.
                </p>
                <div className="mt-4 h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart
                      data={chartData}
                      margin={{ top: 10, right: 20, bottom: 4, left: 0 }}
                    >
                      <CartesianGrid stroke="#1E2A44" vertical={false} />
                      <XAxis
                        dataKey="date"
                        tick={{ fill: "#94a3b8", fontSize: 11 }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <YAxis
                        domain={[0, 100]}
                        tick={{ fill: "#94a3b8", fontSize: 11 }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <Tooltip
                        contentStyle={TOOLTIP_STYLE}
                        formatter={(value) => [`${value}`, "Skor total"]}
                      />
                      <Line
                        type="monotone"
                        dataKey="score"
                        stroke="#3B82F6"
                        strokeWidth={2.5}
                        dot={{ r: 4, fill: "#60A5FA" }}
                        activeDot={{ r: 6 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </section>

              <section className="card">
                <h2 className="text-lg font-semibold text-white">
                  Bandingkan analisis
                </h2>
                <p className="mt-1 text-xs text-slate-500">
                  Pilih analisis dasar dan pembanding.
                </p>
                <div className="mt-4 space-y-3">
                  <div>
                    <label className="label" htmlFor="base-analysis">
                      Analisis dasar
                    </label>
                    <select
                      id="base-analysis"
                      className="input"
                      value={baseId}
                      onChange={(event) => {
                        setBaseId(event.target.value);
                        setComparison(null);
                      }}
                    >
                      {history.map((item) => (
                        <option key={item.id} value={item.id}>
                          {formatDate(item.created_at)} · {item.total_score}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="label" htmlFor="compare-analysis">
                      Pembanding
                    </label>
                    <select
                      id="compare-analysis"
                      className="input"
                      value={compareId}
                      onChange={(event) => {
                        setCompareId(event.target.value);
                        setComparison(null);
                      }}
                    >
                      {history.map((item) => (
                        <option key={item.id} value={item.id}>
                          {formatDate(item.created_at)} · {item.total_score}
                        </option>
                      ))}
                    </select>
                  </div>
                  <button
                    type="button"
                    className="btn-primary w-full"
                    onClick={handleCompare}
                    disabled={
                      comparing || !baseId || !compareId || baseId === compareId
                    }
                  >
                    {comparing ? "Membandingkan..." : "Bandingkan"}
                  </button>
                  {baseId === compareId && (
                    <p className="text-xs text-slate-500">
                      Pilih dua analisis yang berbeda.
                    </p>
                  )}
                  {compareError && (
                    <p
                      role="alert"
                      className="rounded-lg border border-danger/40 bg-danger/10 px-3 py-2 text-xs text-red-300"
                    >
                      {compareError}
                    </p>
                  )}
                </div>
              </section>
            </div>

            <section className="card mt-6">
              <h2 className="text-lg font-semibold text-white">
                Daftar analisis
              </h2>
              <div className="mt-4 divide-y divide-border/70">
                {history.map((item) => (
                  <div
                    key={item.id}
                    className="flex flex-wrap items-center gap-3 py-3"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-semibold text-white">
                        {formatDate(item.created_at)}
                      </p>
                      <p className="truncate text-xs text-slate-500">
                        {item.original_filename}
                      </p>
                    </div>
                    <span className="rounded-full border border-accent/30 bg-accent/10 px-3 py-1 text-xs font-semibold text-accent-soft">
                      {item.total_score}/100
                    </span>
                    <Link
                      to={`/dashboard?analysis=${item.id}`}
                      className="text-xs font-semibold text-slate-300 hover:text-white"
                    >
                      Dashboard
                    </Link>
                    <Link
                      to={`/analysis/${item.id}`}
                      className="text-xs font-semibold text-slate-300 hover:text-white"
                    >
                      Detail
                    </Link>
                  </div>
                ))}
              </div>
            </section>

            {comparison && (
              <section className="card mt-6">
                <div className="flex flex-wrap items-end justify-between gap-4">
                  <div>
                    <h2 className="text-lg font-semibold text-white">
                      Hasil perbandingan
                    </h2>
                    <p className="mt-1 text-xs text-slate-500">
                      Urutan: analisis dasar → pembanding.
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs uppercase tracking-wider text-slate-500">
                      Selisih skor total
                    </p>
                    <p
                      className={`text-3xl font-bold ${deltaClass(comparison.total_score_delta)}`}
                    >
                      {comparison.total_score_delta > 0 ? "+" : ""}
                      {comparison.total_score_delta}
                    </p>
                    <p className="text-xs text-slate-500">
                      {comparison.base_total_score} →{" "}
                      {comparison.compare_total_score}
                    </p>
                  </div>
                </div>

                <div className="mt-5 grid gap-3 sm:grid-cols-2">
                  {comparison.criteria.map((item) => (
                    <div
                      key={item.key}
                      className="rounded-xl border border-border bg-navy/60 p-3"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-sm font-medium text-slate-200">
                          {item.label}
                        </p>
                        <span
                          className={`text-xs font-bold ${deltaClass(item.delta)}`}
                        >
                          {item.delta > 0 ? "+" : ""}
                          {item.delta}
                        </span>
                      </div>
                      <p className="mt-1 text-xs text-slate-500">
                        {item.base_score} → {item.compare_score} dari{" "}
                        {item.max_score}
                      </p>
                    </div>
                  ))}
                </div>

                <div className="mt-5 grid gap-4 sm:grid-cols-2">
                  <div>
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                      Skill bertambah
                    </p>
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {comparison.skills_added.length ? (
                        comparison.skills_added.map((skill) => (
                          <span
                            key={skill}
                            className="rounded-full border border-success/30 bg-success/10 px-2.5 py-1 text-[11px] font-medium text-success"
                          >
                            {skill}
                          </span>
                        ))
                      ) : (
                        <span className="text-xs text-slate-600">
                          Tidak ada
                        </span>
                      )}
                    </div>
                  </div>
                  <div>
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                      Skill berkurang
                    </p>
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {comparison.skills_removed.length ? (
                        comparison.skills_removed.map((skill) => (
                          <span
                            key={skill}
                            className="rounded-full border border-warning/30 bg-warning/10 px-2.5 py-1 text-[11px] font-medium text-warning"
                          >
                            {skill}
                          </span>
                        ))
                      ) : (
                        <span className="text-xs text-slate-600">
                          Tidak ada
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </section>
            )}
          </>
        )}
      </main>
    </div>
  );
}
