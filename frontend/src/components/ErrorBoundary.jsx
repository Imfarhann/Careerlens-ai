import { Component } from "react";

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    if (import.meta.env.DEV) {
      console.error("Terjadi error pada UI", error, info);
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen items-center justify-center bg-navy px-6">
          <div className="card max-w-lg text-center">
            <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-danger/15 text-lg font-bold text-danger">
              !
            </span>
            <h1 className="mt-4 text-xl font-bold text-white">
              Terjadi kesalahan tak terduga
            </h1>
            <p className="mt-2 text-sm leading-relaxed text-slate-400">
              Muat ulang halaman. Jika masalah berlanjut, coba masuk kembali
              atau hubungi pengelola aplikasi.
            </p>
            <button
              type="button"
              className="btn-primary mt-5"
              onClick={() => window.location.reload()}
            >
              Muat ulang
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
