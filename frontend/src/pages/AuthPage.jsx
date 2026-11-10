import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { api, getToken, setToken } from "../api/client";
import Navbar from "../components/Navbar";

export default function AuthPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const mode = searchParams.get("mode") === "register" ? "register" : "login";
  const isRegister = mode === "register";

  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (getToken()) {
      navigate("/dashboard", { replace: true });
    }
  }, [navigate]);

  useEffect(() => {
    setError("");
  }, [mode]);

  function handleChange(event) {
    setForm((prev) => ({ ...prev, [event.target.name]: event.target.value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (isRegister) {
        await api.register(form);
      }
      const token = await api.login(form);
      setToken(token.access_token);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-navy">
      <Navbar />

      <main className="mx-auto grid min-h-[calc(100vh-4rem)] max-w-6xl items-center gap-12 px-6 py-12 lg:grid-cols-2">
        <section className="hidden lg:block">
          <span className="inline-flex rounded-full border border-accent/30 bg-accent/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-wider text-accent-soft">
            Your Career, Analyzed by AI
          </span>
          <h1 className="mt-6 text-4xl font-bold leading-tight text-white">
            Mulai dari CV yang sudah Anda punya.
          </h1>
          <p className="mt-4 max-w-md text-sm leading-relaxed text-slate-400">
            Upload PDF atau DOCX, koreksi hasil ekstraksi, lalu lihat skor per
            kriteria dan lowongan yang paling cocok.
          </p>

          <ul className="mt-8 space-y-4 text-sm text-slate-300">
            {[
              "Skor 0-100 dari rubrik yang transparan",
              "Skill gap dan roadmap belajar per kategori",
              "Data CV hanya bisa diakses pemilik akun",
            ].map((item) => (
              <li key={item} className="flex items-start gap-3">
                <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-accent/15 text-[10px] font-bold text-accent-soft">
                  OK
                </span>
                {item}
              </li>
            ))}
          </ul>
        </section>

        <section className="w-full max-w-md justify-self-end">
          <div className="card">
            <div className="flex rounded-lg bg-navy p-1">
              <button
                type="button"
                onClick={() => setSearchParams({})}
                className={`flex-1 rounded-md px-4 py-2 text-sm font-semibold transition ${
                  isRegister
                    ? "text-slate-400 hover:text-white"
                    : "bg-surface text-white shadow"
                }`}
              >
                Masuk
              </button>
              <button
                type="button"
                onClick={() => setSearchParams({ mode: "register" })}
                className={`flex-1 rounded-md px-4 py-2 text-sm font-semibold transition ${
                  isRegister
                    ? "bg-surface text-white shadow"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                Daftar
              </button>
            </div>

            <h2 className="mt-6 text-xl font-semibold text-white">
              {isRegister ? "Buat akun baru" : "Selamat datang kembali"}
            </h2>
            <p className="mt-1 text-sm text-slate-400">
              {isRegister
                ? "Gratis untuk MVP. Tidak perlu kartu kredit."
                : "Masuk untuk melanjutkan analisis CV Anda."}
            </p>

            <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
              <div>
                <label htmlFor="email" className="label">
                  Email
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  className="input"
                  placeholder="nama@email.com"
                  value={form.email}
                  onChange={handleChange}
                />
              </div>

              <div>
                <label htmlFor="password" className="label">
                  Password
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete={isRegister ? "new-password" : "current-password"}
                  required
                  minLength={isRegister ? 8 : 1}
                  maxLength={128}
                  className="input"
                  placeholder={isRegister ? "Minimal 8 karakter" : "Password Anda"}
                  value={form.password}
                  onChange={handleChange}
                />
              </div>

              {error && (
                <p
                  role="alert"
                  className="rounded-lg border border-danger/40 bg-danger/10 px-4 py-3 text-sm text-red-300"
                >
                  {error}
                </p>
              )}

              <button type="submit" className="btn-primary w-full" disabled={loading}>
                {loading
                  ? "Memproses..."
                  : isRegister
                    ? "Daftar dan masuk"
                    : "Masuk"}
              </button>
            </form>

            <p className="mt-6 text-center text-xs text-slate-500">
              Dengan melanjutkan, Anda setuju data CV diproses untuk analisis.{" "}
              <Link to="/" className="text-accent-soft hover:text-white">
                Kembali ke beranda
              </Link>
            </p>
          </div>
        </section>
      </main>
    </div>
  );
}
