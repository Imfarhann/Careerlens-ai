import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { api, clearToken } from "../api/client";
import Navbar from "../components/Navbar";

const GAUGE_RADIUS = 62;
const GAUGE_CIRCUMFERENCE = 2 * Math.PI * GAUGE_RADIUS;
const PIE_COLORS = [
  "#3B82F6",
  "#60A5FA",
  "#22C55E",
  "#F59E0B",
  "#A78BFA",
  "#F472B6",
  "#38BDF8",
];

const TOOLTIP_STYLE = {
  backgroundColor: "#111A2E",
  border: "1px solid #1E2A44",
  borderRadius: "8px",
  color: "#f8fafc",
  fontSize: 12,
};

function scoreColor(score) {
  if (score >= 80) return "#22c55e";
  if (score >= 60) return "#f59e0b";
  return "#ef4444";
}

function ScoreGauge({ score }) {
  const offset = GAUGE_CIRCUMFERENCE * (1 - Math.min(score, 100) / 100);
  const color = scoreColor(score);

  return (
    <div className="flex flex-col items-center">
      <svg
        viewBox="0 0 160 160"
        className="h-44 w-44"
        role="img"
        aria-label={`Skor ${score} dari 100`}
      >
        <circle
          cx="80"
          cy="80"
          r={GAUGE_RADIUS}
          fill="none"
          stroke="#1e293b"
          strokeWidth="13"
        />
        <circle
          cx="80"
          cy="80"
          r={GAUGE_RADIUS}
          fill="none"
          stroke={color}
          strokeWidth="13"
          strokeLinecap="round"
          strokeDasharray={GAUGE_CIRCUMFERENCE}
          strokeDashoffset={offset}
          transform="rotate(-90 80 80)"
        />
        <text
          x="80"
          y="79"
          textAnchor="middle"
          fill="#f8fafc"
          fontSize="38"
          fontWeight="700"
        >
          {score}
        </text>
        <text
          x="80"
          y="102"
          textAnchor="middle"
          fill="#94a3b8"
          fontSize="12"
        >
          dari 100
        </text>
      </svg>
      <p className="mt-1 text-xs font-semibold" style={{ color }}>
        {score >= 80
          ? "Sangat baik"
          : score >= 60
            ? "Cukup baik"
            : score >= 40
              ? "Perlu perbaikan"
              : "Butuh banyak perbaikan"}
      </p>
    </div>
  );
}

function Empty({ children }) {
  return (
    <p className="rounded-xl border border-border bg-navy/60 px-4 py-5 text-sm text-slate-500">
      {children}
    </p>
  );
}

function SkillChip({ skill, tone }) {
  const className =
    tone === "matched"
      ? "border-success/30 bg-success/10 text-success"
      : "border-warning/30 bg-warning/10 text-warning";
  return (
    <span
      className={`rounded-full border px-2 py-0.5 text-[10px] font-medium ${className}`}
    >
      {skill}
    </span>
  );
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const requestedId = searchParams.get("analysis");

  const [history, setHistory] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    setLoading(true);
    setError("");
    setDashboard(null);
    setHistory([]);

    api
      .getAnalyses()
      .then(async (result) => {
        if (!active) return;
        const analyses = result.analyses || [];
        setHistory(analyses);
        if (!analyses.length) {
          setLoading(false);
          return null;
        }

        const target =
          requestedId && analyses.some((item) => item.id === requestedId)
            ? requestedId
            : analyses[0].id;
        const summary = await api.getDashboard(target);
        if (active) {
          setDashboard(summary);
          setLoading(false);
        }
        return null;
      })
      .catch((err) => {
        if (!active) return;
        if (err.status === 401) {
          clearToken();
          navigate("/login", { replace: true });
          return;
        }
        setError(err.message);
        setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [requestedId, navigate]);

  const criteria = dashboard?.score_breakdown?.criteria || [];
  const breakdownData = criteria.map((item) => ({
    label: item.label,
    value: item.max_score
      ? Math.round((item.score / item.max_score) * 100)
      : 0,
    score: item.score,
    max: item.max_score,
  }));
  const coverageData = dashboard?.category_coverage || [];
  const skillCounts = dashboard?.skill_by_category || [];
  const topMatches = dashboard?.top_matches || [];
  const topGaps = dashboard?.top_gaps || [];
  const suggestions = dashboard?.suggestions?.items || [];
  const latestId = history[0]?.id;
  const showingOlder = dashboard && latestId && dashboard.analysis_id !== latestId;

  return (
    <div className="min-h-screen bg-navy">
      <Navbar />

      <main className="mx-auto max-w-6xl px-6 py-10">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-accent-soft">
              Dashboard
            </p>
            <h1 className="mt-2 text-3xl font-bold text-white">
              Ringkasan karier Anda
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-400">
              Semua angka di halaman ini berasal dari rubrik skor dan
              perhitungan skill, bukan estimasi LLM.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link to="/upload" className="btn-primary">
              Upload CV
            </Link>
            <Link to="/history" className="btn-ghost">
              Riwayat analisis
            </Link>
            {dashboard && (
              <Link
                to={`/analysis/${dashboard.analysis_id}`}
                className="btn-ghost"
              >
                Detail analisis
              </Link>
            )}
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
            {[0, 1, 2].map((item) => (
              <div key={item} className="card animate-pulse">
                <div className="h-4 w-1/2 rounded bg-navy" />
                <div className="mt-4 h-40 rounded bg-navy" />
              </div>
            ))}
          </div>
        )}

        {!loading && !error && !history.length && (
          <section className="card mt-10">
            <h2 className="text-lg font-semibold text-white">
              Belum ada analisis
            </h2>
            <p className="mt-2 max-w-xl text-sm leading-relaxed text-slate-400">
              Upload CV terlebih dahulu, koreksi hasil ekstraksi, lalu jalankan
              analisis. Dashboard akan otomatis menampilkan ringkasan terbaru.
            </p>
            <Link to="/upload" className="btn-primary mt-5">
              Upload CV
            </Link>
          </section>
        )}

        {!loading && dashboard && (
          <>
            {showingOlder && (
              <p className="mt-6 rounded-lg border border-accent/30 bg-accent/10 px-4 py-3 text-xs text-accent-soft">
                Menampilkan analisis pilihan.{" "}
                <Link
                  to={`/dashboard?analysis=${latestId}`}
                  className="font-semibold underline underline-offset-2"
                >
                  Kembali ke analisis terbaru
                </Link>
              </p>
            )}

            <div className="mt-8 grid gap-6 lg:grid-cols-3">
              <section className="card flex flex-col items-center justify-center">
                <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
                  Skor total
                </h2>
                <div className="mt-3">
                  <ScoreGauge score={dashboard.total_score} />
                </div>
                <p className="mt-3 text-center text-xs leading-relaxed text-slate-500">
                  Dihitung dari 5 kriteria rubrik dengan bobot tetap.
                </p>
              </section>

              <section className="card lg:col-span-2">
                <h2 className="text-lg font-semibold text-white">
                  Breakdown 5 kriteria
                </h2>
                <p className="mt-1 text-xs text-slate-500">
                  Nilai dinormalisasi ke 0-100 dari skor maksimum tiap
                  kriteria.
                </p>
                {breakdownData.length ? (
                  <div className="mt-4 h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={breakdownData}
                        layout="vertical"
                        margin={{ top: 4, right: 20, bottom: 4, left: 8 }}
                      >
                        <CartesianGrid
                          horizontal={false}
                          stroke="#1E2A44"
                        />
                        <XAxis
                          type="number"
                          domain={[0, 100]}
                          tick={{ fill: "#94a3b8", fontSize: 11 }}
                          axisLine={false}
                          tickLine={false}
                        />
                        <YAxis
                          type="category"
                          dataKey="label"
                          width={128}
                          tick={{ fill: "#cbd5e1", fontSize: 11 }}
                          axisLine={false}
                          tickLine={false}
                        />
                        <Tooltip
                          contentStyle={TOOLTIP_STYLE}
                          cursor={{ fill: "rgba(59,130,246,0.08)" }}
                          formatter={(value, name, props) => [
                            `${props.payload.score}/${props.payload.max}`,
                            "Skor",
                          ]}
                        />
                        <Bar
                          dataKey="value"
                          fill="#3B82F6"
                          radius={[0, 6, 6, 0]}
                          maxBarSize={20}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="mt-4">
                    <Empty>Breakdown skor belum tersedia.</Empty>
                  </div>
                )}
              </section>
            </div>

            <div className="mt-6 grid gap-6 lg:grid-cols-2">
              <section className="card">
                <h2 className="text-lg font-semibold text-white">
                  Coverage per kategori
                </h2>
                <p className="mt-1 text-xs text-slate-500">
                  Persentase skill wajib yang dimiliki dibanding skill wajib
                  pada 10 lowongan teratas.
                </p>
                {coverageData.length ? (
                  <div className="mt-2 h-72 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart
                        data={coverageData}
                        outerRadius="70%"
                        margin={{ top: 10, right: 20, bottom: 10, left: 20 }}
                      >
                        <PolarGrid stroke="#1E2A44" />
                        <PolarAngleAxis
                          dataKey="category"
                          tick={{ fill: "#94a3b8", fontSize: 11 }}
                        />
                        <PolarRadiusAxis
                          domain={[0, 100]}
                          angle={90}
                          tick={false}
                          axisLine={false}
                        />
                        <Radar
                          dataKey="percentage"
                          stroke="#3B82F6"
                          fill="#3B82F6"
                          fillOpacity={0.35}
                        />
                        <Tooltip
                          contentStyle={TOOLTIP_STYLE}
                          formatter={(value, name, props) => [
                            `${value}% (${props.payload.owned}/${props.payload.total})`,
                            props.payload.category,
                          ]}
                        />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="mt-4">
                    <Empty>
                      Belum ada lowongan acuan untuk menghitung coverage.
                    </Empty>
                  </div>
                )}
              </section>

              <section className="card">
                <h2 className="text-lg font-semibold text-white">
                  Skill per kategori
                </h2>
                <p className="mt-1 text-xs text-slate-500">
                  Jumlah skill yang benar-benar terdeteksi pada profil Anda.
                </p>
                {skillCounts.length ? (
                  <div className="mt-2 h-72 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={skillCounts}
                          dataKey="count"
                          nameKey="category"
                          innerRadius="50%"
                          outerRadius="78%"
                          paddingAngle={2}
                          stroke="#0B1220"
                        >
                          {skillCounts.map((entry, index) => (
                            <Cell
                              key={entry.category}
                              fill={
                                PIE_COLORS[index % PIE_COLORS.length]
                              }
                            />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={TOOLTIP_STYLE}
                          formatter={(value, name) => [
                            `${value} skill`,
                            name,
                          ]}
                        />
                        <Legend
                          verticalAlign="bottom"
                          iconType="circle"
                          wrapperStyle={{
                            fontSize: 11,
                            color: "#94a3b8",
                          }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="mt-4">
                    <Empty>
                      Belum ada skill terdeteksi. Lengkapi profil lalu analisis
                      ulang.
                    </Empty>
                  </div>
                )}
              </section>
            </div>

            <div className="mt-6 grid gap-6 lg:grid-cols-2">
              <section className="card">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h2 className="text-lg font-semibold text-white">
                    Top 5 lowongan
                  </h2>
                  <Link
                    to={`/analysis/${dashboard.analysis_id}/jobs`}
                    className="text-xs font-semibold text-accent-soft hover:text-white"
                  >
                    Lihat semua
                  </Link>
                </div>
                <div className="mt-4 space-y-3">
                  {topMatches.map((item) => {
                    const color = scoreColor(item.match_percentage);
                    return (
                      <article
                        key={item.job_id}
                        className="rounded-xl border border-border bg-navy/60 p-3"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <p className="truncate text-sm font-semibold text-white">
                              {item.title}
                            </p>
                            <p className="text-xs text-slate-500">
                              {item.company} · {item.level}
                            </p>
                          </div>
                          <span
                            className="text-sm font-bold"
                            style={{ color }}
                          >
                            {item.match_percentage.toFixed(1)}%
                          </span>
                        </div>
                        <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-navy">
                          <div
                            className="h-full rounded-full"
                            style={{
                              width: `${Math.max(0, Math.min(100, item.match_percentage))}%`,
                              backgroundColor: color,
                            }}
                          />
                        </div>
                        <div className="mt-2 flex flex-wrap gap-1">
                          {item.matched_skills.slice(0, 5).map((skill) => (
                            <SkillChip
                              key={`m-${item.job_id}-${skill}`}
                              skill={skill}
                              tone="matched"
                            />
                          ))}
                          {item.missing_skills.slice(0, 5).map((skill) => (
                            <SkillChip
                              key={`x-${item.job_id}-${skill}`}
                              skill={skill}
                              tone="missing"
                            />
                          ))}
                        </div>
                      </article>
                    );
                  })}
                  {!topMatches.length && (
                    <Empty>Belum ada lowongan yang bisa dicocokkan.</Empty>
                  )}
                </div>
              </section>

              <section className="card">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h2 className="text-lg font-semibold text-white">
                    Top skill gap
                  </h2>
                  <Link
                    to={`/analysis/${dashboard.analysis_id}/skill-gap`}
                    className="text-xs font-semibold text-accent-soft hover:text-white"
                  >
                    Roadmap lengkap
                  </Link>
                </div>
                <ol className="mt-4 space-y-3">
                  {topGaps.map((item, index) => (
                    <li
                      key={item.skill}
                      className="rounded-xl border border-border bg-navy/60 p-3"
                    >
                      <div className="flex items-start gap-3">
                        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-warning/15 text-[10px] font-bold text-warning">
                          {index + 1}
                        </span>
                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <p className="text-sm font-semibold text-white">
                              {item.skill}
                            </p>
                            <span className="rounded-full border border-border px-2 py-0.5 text-[10px] uppercase tracking-wider text-slate-500">
                              {item.category}
                            </span>
                          </div>
                          <p className="mt-1 text-xs text-slate-500">
                            Kurang di {item.frequency} lowongan teratas
                            {item.job_count > 0
                              ? `, ${item.job_count} wajib`
                              : ""}
                            .
                          </p>
                          <div className="mt-1 space-y-0.5">
                            {item.resources.slice(0, 2).map((resource) => (
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
                          </div>
                        </div>
                      </div>
                    </li>
                  ))}
                  {!topGaps.length && (
                    <Empty>
                      Tidak ada skill yang kurang pada lowongan teratas.
                    </Empty>
                  )}
                </ol>
              </section>
            </div>

            <section className="card mt-6">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h2 className="text-lg font-semibold text-white">
                  Saran perbaikan
                </h2>
                <span className="rounded-full border border-accent/30 bg-accent/10 px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-accent-soft">
                  {dashboard.suggestions?.source === "llm"
                    ? "Saran AI"
                    : "Saran otomatis"}
                </span>
              </div>
              <ol className="mt-4 space-y-3">
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
                {!suggestions.length && (
                  <Empty>Belum ada saran untuk analisis ini.</Empty>
                )}
              </ol>
            </section>
          </>
        )}
      </main>
    </div>
  );
}
