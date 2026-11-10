import { Link, useLocation, useNavigate } from "react-router-dom";

import { clearToken, getToken } from "../api/client";

export default function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();
  const isAuthenticated = Boolean(getToken());

  function handleLogout() {
    clearToken();
    navigate("/");
  }

  return (
    <header className="border-b border-border/70 bg-navy/80 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
        <Link to="/" className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent text-sm font-bold text-white">
            CL
          </span>
          <span className="text-sm font-semibold tracking-wide text-white">
            CareerLens <span className="text-accent-soft">AI</span>
          </span>
        </Link>

        <nav className="flex items-center gap-3">
          {isAuthenticated ? (
            <>
              <Link
                to="/dashboard"
                className="text-sm font-medium text-slate-300 transition hover:text-white"
              >
                Dashboard
              </Link>
              <Link
                to="/history"
                className="text-sm font-medium text-slate-300 transition hover:text-white"
              >
                Riwayat
              </Link>
              <button
                type="button"
                onClick={handleLogout}
                className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-slate-300 transition hover:border-danger/60 hover:text-white"
              >
                Keluar
              </button>
            </>
          ) : (
            <>
              {location.pathname !== "/login" && (
                <Link
                  to="/login"
                  className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-slate-200 transition hover:border-accent/60 hover:text-white"
                >
                  Masuk
                </Link>
              )}
              <Link
                to="/login?mode=register"
                className="rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white transition hover:bg-accent-soft"
              >
                Mulai gratis
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
