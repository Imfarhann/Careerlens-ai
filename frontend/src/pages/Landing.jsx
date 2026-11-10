import { Link } from "react-router-dom";

import Navbar from "../components/Navbar";

const features = [
  {
    title: "CV Analyzer",
    description:
      "Skor 0-100 dari rubrik terukur: kelengkapan section, kualitas deskripsi, ATS, skill, dan format.",
    stat: "5 kriteria",
  },
  {
    title: "Job Matcher",
    description:
      "Persentase kecocokan dengan lowongan, lengkap dengan skill yang sudah cocok dan yang perlu dikejar.",
    stat: "0.6 skill + 0.4 semantik",
  },
  {
    title: "Skill Gap",
    description:
      "Skill yang kurang dipetakan per kategori, dengan roadmap belajar yang bisa langsung dieksekusi.",
    stat: "Per kategori",
  },
];

const breakdown = [
  { label: "Kelengkapan section", value: 92 },
  { label: "Kualitas deskripsi", value: 78 },
  { label: "Keterbacaan ATS", value: 86 },
  { label: "Skill & relevansi", value: 74 },
  { label: "Format & panjang", value: 80 },
];

const steps = [
  {
    number: "01",
    title: "Upload CV",
    description: "PDF atau DOCX, maksimal 5 MB. Hasil ekstraksi bisa Anda koreksi.",
  },
  {
    number: "02",
    title: "Analisis",
    description: "Skor dihitung kode berdasarkan rubrik, bukan tebakan model bahasa.",
  },
  {
    number: "03",
    title: "Cocokkan",
    description: "Lihat lowongan yang paling relevan dan skill yang perlu ditingkatkan.",
  },
];

export default function Landing() {
  return (
    <div className="min-h-screen bg-navy">
      <Navbar />

      <main>
        <section className="relative overflow-hidden">
          <div className="pointer-events-none absolute -top-40 left-1/2 h-96 w-[42rem] -translate-x-1/2 rounded-full bg-accent/20 blur-3xl" />

          <div className="relative mx-auto grid max-w-6xl items-center gap-12 px-6 py-20 lg:grid-cols-2 lg:py-28">
            <div>
              <span className="inline-flex items-center gap-2 rounded-full border border-accent/30 bg-accent/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-wider text-accent-soft">
                Your Career, Analyzed by AI
              </span>

              <h1 className="mt-6 text-4xl font-bold leading-tight text-white sm:text-5xl">
                CV Anda dinilai dengan rubrik yang{" "}
                <span className="text-accent-soft">bisa dijelaskan.</span>
              </h1>

              <p className="mt-5 max-w-xl text-base leading-relaxed text-slate-400">
                CareerLens AI mengekstrak CV, menghitung skor 0-100 per kriteria,
                lalu mencocokkannya dengan lowongan nyata. Semua angka berasal dari
                kode, bukan dari LLM.
              </p>

              <div className="mt-8 flex flex-wrap gap-3">
                <Link to="/login?mode=register" className="btn-primary">
                  Analisis CV sekarang
                </Link>
                <a href="#cara-kerja" className="btn-ghost">
                  Lihat cara kerja
                </a>
              </div>

              <dl className="mt-10 grid max-w-md grid-cols-3 gap-4 border-t border-border pt-6">
                <div>
                  <dt className="text-xs uppercase tracking-wider text-slate-500">
                    Rubrik
                  </dt>
                  <dd className="mt-1 text-lg font-semibold text-white">100 poin</dd>
                </div>
                <div>
                  <dt className="text-xs uppercase tracking-wider text-slate-500">
                    Format
                  </dt>
                  <dd className="mt-1 text-lg font-semibold text-white">PDF/DOCX</dd>
                </div>
                <div>
                  <dt className="text-xs uppercase tracking-wider text-slate-500">
                    Privasi
                  </dt>
                  <dd className="mt-1 text-lg font-semibold text-white">Milik Anda</dd>
                </div>
              </dl>
            </div>

            <div className="relative">
              <div className="absolute inset-0 -rotate-3 rounded-3xl bg-accent/10 blur-xl" />
              <div className="card relative">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-wider text-slate-500">
                      Contoh hasil analisis
                    </p>
                    <p className="mt-1 text-sm text-slate-400">
                      Product Designer · CV 1 halaman
                    </p>
                  </div>
                  <span className="rounded-full bg-success/10 px-3 py-1 text-xs font-semibold text-success">
                    Siap dikirim
                  </span>
                </div>

                <div className="mt-6 flex items-center gap-6">
                  <div className="relative flex h-28 w-28 items-center justify-center rounded-full bg-gradient-to-br from-accent/30 via-surface to-surface">
                    <div className="flex h-24 w-24 flex-col items-center justify-center rounded-full border border-border bg-navy">
                      <span className="text-3xl font-bold text-white">82</span>
                      <span className="text-[10px] uppercase tracking-wider text-slate-500">
                        / 100
                      </span>
                    </div>
                  </div>
                  <div className="flex-1 space-y-3">
                    {breakdown.slice(0, 3).map((item) => (
                      <div key={item.label}>
                        <div className="mb-1 flex justify-between text-xs text-slate-400">
                          <span>{item.label}</span>
                          <span className="font-semibold text-slate-200">
                            {item.value}
                          </span>
                        </div>
                        <div className="h-1.5 overflow-hidden rounded-full bg-navy">
                          <div
                            className="h-full rounded-full bg-accent"
                            style={{ width: `${item.value}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="mt-6 space-y-3 border-t border-border pt-5">
                  {breakdown.slice(3).map((item) => (
                    <div key={item.label}>
                      <div className="mb-1 flex justify-between text-xs text-slate-400">
                        <span>{item.label}</span>
                        <span className="font-semibold text-slate-200">
                          {item.value}
                        </span>
                      </div>
                      <div className="h-1.5 overflow-hidden rounded-full bg-navy">
                        <div
                          className="h-full rounded-full bg-accent/70"
                          style={{ width: `${item.value}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-6 py-16">
          <div className="grid gap-5 md:grid-cols-3">
            {features.map((feature) => (
              <article key={feature.title} className="card">
                <span className="text-xs font-semibold uppercase tracking-wider text-accent-soft">
                  {feature.stat}
                </span>
                <h2 className="mt-3 text-lg font-semibold text-white">
                  {feature.title}
                </h2>
                <p className="mt-2 text-sm leading-relaxed text-slate-400">
                  {feature.description}
                </p>
              </article>
            ))}
          </div>
        </section>

        <section id="cara-kerja" className="border-t border-border/70 bg-surface/30">
          <div className="mx-auto max-w-6xl px-6 py-16">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <h2 className="text-2xl font-bold text-white">Cara kerja</h2>
                <p className="mt-2 max-w-xl text-sm text-slate-400">
                  Tiga langkah, tanpa mengirim nama atau kontak Anda ke model bahasa.
                </p>
              </div>
              <Link
                to="/login?mode=register"
                className="text-sm font-semibold text-accent-soft hover:text-white"
              >
                Buat akun gratis
              </Link>
            </div>

            <ol className="mt-8 grid gap-5 md:grid-cols-3">
              {steps.map((step) => (
                <li key={step.number} className="card">
                  <span className="text-sm font-bold text-accent">{step.number}</span>
                  <h3 className="mt-3 font-semibold text-white">{step.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-slate-400">
                    {step.description}
                  </p>
                </li>
              ))}
            </ol>
          </div>
        </section>
      </main>

      <footer className="border-t border-border/70">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-6 py-8 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between">
          <p>CareerLens AI — Your Career, Analyzed by AI.</p>
          <p>Skor dihitung kode berdasarkan rubrik. LLM hanya menulis saran.</p>
        </div>
      </footer>
    </div>
  );
}
