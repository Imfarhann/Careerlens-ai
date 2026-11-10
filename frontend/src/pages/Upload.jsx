import { useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { uploadCV } from "../api/client";
import Navbar from "../components/Navbar";

const MAX_SIZE = 5 * 1024 * 1024;
const ALLOWED_EXTENSIONS = [".pdf", ".docx"];

function validateFile(file) {
  const name = file.name.toLowerCase();
  const allowed = ALLOWED_EXTENSIONS.some((extension) =>
    name.endsWith(extension)
  );

  if (!allowed) {
    return "Format file harus PDF atau DOCX.";
  }
  if (file.size === 0) {
    return "File kosong. Pilih CV yang berisi teks.";
  }
  if (file.size > MAX_SIZE) {
    return "Ukuran file melebihi batas 5 MB.";
  }
  return null;
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function Upload() {
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef(null);
  const navigate = useNavigate();

  function chooseFile(candidate) {
    if (!candidate) return;
    const message = validateFile(candidate);
    setError(message || "");
    setProgress(0);
    setFile(message ? null : candidate);
  }

  function handleDrop(event) {
    event.preventDefault();
    setDragging(false);
    if (uploading) return;
    chooseFile(event.dataTransfer.files?.[0]);
  }

  function handleInputChange(event) {
    chooseFile(event.target.files?.[0]);
    event.target.value = "";
  }

  async function handleUpload() {
    if (!file || uploading) return;

    const message = validateFile(file);
    if (message) {
      setError(message);
      return;
    }

    setError("");
    setUploading(true);
    setProgress(0);

    try {
      const result = await uploadCV(file, setProgress);
      navigate(`/review/${result.profile.id}`, {
        state: { uploaded: true },
      });
    } catch (err) {
      setError(err.message);
      setProgress(0);
      setUploading(false);
    }
  }

  return (
    <div className="min-h-screen bg-navy">
      <Navbar />

      <main className="mx-auto max-w-3xl px-6 py-12">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-accent-soft">
              Upload CV
            </p>
            <h1 className="mt-2 text-3xl font-bold text-white">
              Unggah CV Anda
            </h1>
            <p className="mt-2 max-w-xl text-sm leading-relaxed text-slate-400">
              Format PDF atau DOCX, maksimal 5 MB. Setelah diproses, Anda bisa
              mengoreksi hasil ekstraksi sebelum analisis.
            </p>
          </div>
          <Link to="/dashboard" className="btn-ghost">
            Dashboard
          </Link>
        </div>

        <div className="mt-8 card">
          <div
            onDragOver={(event) => {
              event.preventDefault();
              if (!uploading) setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            onClick={() => !uploading && inputRef.current?.click()}
            role="button"
            tabIndex={0}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                if (!uploading) inputRef.current?.click();
              }
            }}
            className={`flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-14 text-center transition ${
              dragging
                ? "border-accent bg-accent/10"
                : "border-border bg-navy/60 hover:border-accent/60"
            } ${uploading ? "pointer-events-none opacity-70" : ""}`}
          >
            <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-accent/15 text-accent-soft">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
                className="h-6 w-6"
                aria-hidden="true"
              >
                <path d="M12 16V4m0 0L7 9m5-5 5 5" strokeLinecap="round" />
                <path d="M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" strokeLinecap="round" />
              </svg>
            </span>
            <p className="mt-4 text-sm font-semibold text-white">
              Tarik dan lepas file di sini
            </p>
            <p className="mt-1 text-xs text-slate-500">
              atau klik untuk memilih file dari perangkat
            </p>
            <input
              ref={inputRef}
              type="file"
              accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              className="hidden"
              onChange={handleInputChange}
            />
          </div>

          {file && (
            <div className="mt-5 flex items-center justify-between gap-4 rounded-xl border border-border bg-navy px-4 py-3">
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-white">
                  {file.name}
                </p>
                <p className="mt-0.5 text-xs text-slate-500">
                  {formatSize(file.size)}
                </p>
              </div>
              {!uploading && (
                <button
                  type="button"
                  onClick={() => {
                    setFile(null);
                    setError("");
                    setProgress(0);
                  }}
                  className="shrink-0 text-xs font-semibold uppercase tracking-wider text-slate-400 transition hover:text-danger"
                >
                  Hapus
                </button>
              )}
            </div>
          )}

          {uploading && (
            <div className="mt-5">
              <div className="mb-2 flex items-center justify-between text-xs text-slate-400">
                <span>Mengunggah dan memproses CV...</span>
                <span className="font-semibold text-slate-200">{progress}%</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-navy">
                <div
                  className="h-full rounded-full bg-accent transition-all"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          {error && (
            <p
              role="alert"
              className="mt-5 rounded-lg border border-danger/40 bg-danger/10 px-4 py-3 text-sm text-red-300"
            >
              {error}
            </p>
          )}

          <button
            type="button"
            onClick={handleUpload}
            disabled={!file || uploading}
            className="btn-primary mt-6 w-full"
          >
            {uploading ? "Memproses..." : "Upload dan ekstrak"}
          </button>
        </div>

        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          {[
            ["PDF", "Teks asli, bukan hasil scan"],
            ["DOCX", "Termasuk isi tabel"],
            ["Privasi", "Hanya Anda yang bisa mengakses"],
          ].map(([title, description]) => (
            <div
              key={title}
              className="rounded-xl border border-border bg-surface/50 px-4 py-3"
            >
              <p className="text-sm font-semibold text-white">{title}</p>
              <p className="mt-1 text-xs leading-relaxed text-slate-500">
                {description}
              </p>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
