import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";

import { api, clearToken } from "../api/client";
import Navbar from "../components/Navbar";

const EMPTY_EDUCATION = {
  institution: "",
  degree: "",
  period: "",
  details: [],
};
const EMPTY_EXPERIENCE = {
  role: "",
  company: "",
  period: "",
  details: [],
};
const EMPTY_PROJECT = { name: "", period: "", description: "" };

function formFromProfile(profile) {
  return {
    name: profile.name || "",
    email: profile.email || "",
    phone: profile.phone || "",
    summary: profile.summary || "",
    github: profile.links?.github || "",
    linkedin: profile.links?.linkedin || "",
  };
}

function detailsToText(details) {
  return (details || []).join("\n");
}

function textToDetails(text) {
  return text.split("\n");
}

function cleanDetails(details) {
  return (details || []).map((item) => item.trim()).filter(Boolean);
}

function SectionCard({ title, description, action, children }) {
  return (
    <section className="card">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-white">{title}</h2>
          {description && (
            <p className="mt-1 text-xs text-slate-500">{description}</p>
          )}
        </div>
        {action}
      </div>
      <div className="mt-5 space-y-4">{children}</div>
    </section>
  );
}

function LabeledField({ label, className = "", ...props }) {
  return (
    <label className={`block ${className}`}>
      <span className="label">{label}</span>
      <input className="input" {...props} />
    </label>
  );
}

export default function Review() {
  const { profileId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();

  const [profile, setProfile] = useState(null);
  const [form, setForm] = useState(null);
  const [education, setEducation] = useState([]);
  const [experience, setExperience] = useState([]);
  const [projects, setProjects] = useState([]);
  const [skills, setSkills] = useState([]);
  const [skillDraft, setSkillDraft] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    let active = true;

    api
      .getProfile(profileId)
      .then((data) => {
        if (!active) return;
        setProfile(data);
        setForm(formFromProfile(data));
        setEducation(data.education || []);
        setExperience(data.experience || []);
        setProjects(data.projects || []);
        setSkills(data.skills || []);
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
  }, [profileId, navigate]);

  function updateForm(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
    setMessage("");
  }

  function updateItem(setter, index, field, value) {
    setter((prev) =>
      prev.map((item, itemIndex) =>
        itemIndex === index ? { ...item, [field]: value } : item
      )
    );
    setMessage("");
  }

  function removeItem(setter, index) {
    setter((prev) => prev.filter((_, itemIndex) => itemIndex !== index));
    setMessage("");
  }

  function addItem(setter, template) {
    setter((prev) => [...prev, { ...template }]);
    setMessage("");
  }

  function addSkill(event) {
    event.preventDefault();
    const name = skillDraft.trim();
    if (!name) return;
    if (skills.some((skill) => skill.name.toLowerCase() === name.toLowerCase())) {
      setSkillDraft("");
      return;
    }
    setSkills((prev) => [...prev, { name, category: null }]);
    setSkillDraft("");
    setMessage("");
  }

  function removeSkill(name) {
    setSkills((prev) => prev.filter((skill) => skill.name !== name));
    setMessage("");
  }

  function buildPayload() {
    return {
      name: form.name.trim(),
      email: form.email.trim(),
      phone: form.phone.trim(),
      summary: form.summary.trim(),
      links: {
        github: form.github.trim(),
        linkedin: form.linkedin.trim(),
        other: profile.links?.other || [],
      },
      education: education.map((item) => ({
        ...item,
        details: cleanDetails(item.details),
      })),
      experience: experience.map((item) => ({
        ...item,
        details: cleanDetails(item.details),
      })),
      projects: projects.map((item) => ({ ...item })),
      skills: skills.map((skill) => ({
        name: skill.name,
        category: skill.category || null,
      })),
    };
  }

  async function handleSave(event) {
    event?.preventDefault();
    if (saving || analyzing || !form) return;

    setSaving(true);
    setError("");
    setMessage("");

    try {
      const payload = buildPayload();

      const updated = await api.updateProfile(profileId, payload);
      setProfile(updated);
      setForm(formFromProfile(updated));
      setEducation(updated.education || []);
      setExperience(updated.experience || []);
      setProjects(updated.projects || []);
      setSkills(updated.skills || []);
      setMessage("Perubahan tersimpan.");
    } catch (err) {
      if (err.status === 401) {
        clearToken();
        navigate("/login", { replace: true });
        return;
      }
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleAnalyze() {
    if (saving || analyzing || !form || !profile) return;

    setAnalyzing(true);
    setError("");
    setMessage("");

    try {
      const updated = await api.updateProfile(profileId, buildPayload());
      const analysis = await api.createAnalysis(updated.cv_id);
      navigate(`/analysis/${analysis.id}`);
    } catch (err) {
      if (err.status === 401) {
        clearToken();
        navigate("/login", { replace: true });
        return;
      }
      setError(err.message);
      setAnalyzing(false);
    }
  }

  async function handleDelete() {
    if (deleting || !profile) return;
    const confirmed = window.confirm(
      "Hapus CV ini beserta seluruh data hasil ekstraksinya?"
    );
    if (!confirmed) return;

    setDeleting(true);
    setError("");
    try {
      await api.deleteCV(profile.cv_id);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err.message);
      setDeleting(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-navy">
        <Navbar />
        <main className="mx-auto max-w-5xl px-6 py-12">
          <p className="text-sm text-slate-400">Memuat hasil ekstraksi...</p>
        </main>
      </div>
    );
  }

  if (!profile || !form) {
    return (
      <div className="min-h-screen bg-navy">
        <Navbar />
        <main className="mx-auto max-w-5xl px-6 py-12">
          <p className="text-sm text-red-300">
            {error || "Profil tidak ditemukan."}
          </p>
          <Link to="/dashboard" className="btn-ghost mt-6">
            Kembali ke dashboard
          </Link>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-navy">
      <Navbar />

      <main className="mx-auto max-w-5xl px-6 py-10">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-accent-soft">
              Review hasil ekstraksi
            </p>
            <h1 className="mt-2 text-3xl font-bold text-white">
              Koreksi data CV
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-400">
              Periksa hasil parsing sebelum dilanjutkan. Semua perubahan
              disimpan ke profil Anda.
            </p>
            {profile.original_filename && (
              <p className="mt-2 text-xs text-slate-500">
                File: {profile.original_filename}
              </p>
            )}
          </div>

          <div className="flex flex-wrap gap-3">
            <Link to="/upload" className="btn-ghost">
              Upload CV lain
            </Link>
            <button
              type="button"
              onClick={handleSave}
              className="btn-ghost"
              disabled={saving || analyzing}
            >
              {saving ? "Menyimpan..." : "Simpan perubahan"}
            </button>
            <button
              type="button"
              onClick={handleAnalyze}
              className="btn-primary"
              disabled={saving || analyzing}
            >
              {analyzing ? "Menganalisis..." : "Analisis CV"}
            </button>
          </div>
        </div>

        {location.state?.uploaded && !message && (
          <p className="mt-6 rounded-lg border border-success/40 bg-success/10 px-4 py-3 text-sm text-green-300">
            CV berhasil diunggah dan diekstrak. Periksa hasilnya di bawah.
          </p>
        )}

        {message && (
          <p
            role="status"
            className="mt-6 rounded-lg border border-success/40 bg-success/10 px-4 py-3 text-sm text-green-300"
          >
            {message}
          </p>
        )}

        {error && (
          <p
            role="alert"
            className="mt-6 rounded-lg border border-danger/40 bg-danger/10 px-4 py-3 text-sm text-red-300"
          >
            {error}
          </p>
        )}

        <form className="mt-8 space-y-6" onSubmit={handleSave}>
          <SectionCard
            title="Identitas dan kontak"
            description="Data ini tidak dikirim ke LLM tanpa anonimisasi."
          >
            <div className="grid gap-4 sm:grid-cols-2">
              <LabeledField
                label="Nama"
                value={form.name}
                onChange={(event) => updateForm("name", event.target.value)}
                placeholder="Nama lengkap"
              />
              <LabeledField
                label="Email"
                type="email"
                value={form.email}
                onChange={(event) => updateForm("email", event.target.value)}
                placeholder="nama@email.com"
              />
              <LabeledField
                label="Telepon"
                value={form.phone}
                onChange={(event) => updateForm("phone", event.target.value)}
                placeholder="+62 ..."
              />
              <LabeledField
                label="GitHub"
                value={form.github}
                onChange={(event) => updateForm("github", event.target.value)}
                placeholder="https://github.com/username"
              />
              <LabeledField
                label="LinkedIn"
                value={form.linkedin}
                onChange={(event) => updateForm("linkedin", event.target.value)}
                placeholder="https://linkedin.com/in/username"
              />
            </div>

            <label className="block">
              <span className="label">Ringkasan</span>
              <textarea
                className="input min-h-24"
                rows={4}
                value={form.summary}
                onChange={(event) => updateForm("summary", event.target.value)}
                placeholder="Ringkasan profil"
              />
            </label>
          </SectionCard>

          <SectionCard
            title="Pendidikan"
            description="Satu entri per institusi."
            action={
              <button
                type="button"
                className="btn-ghost px-3 py-2 text-xs"
                onClick={() => addItem(setEducation, EMPTY_EDUCATION)}
              >
                Tambah pendidikan
              </button>
            }
          >
            {education.length === 0 && (
              <p className="text-sm text-slate-500">
                Belum ada pendidikan terdeteksi.
              </p>
            )}
            {education.map((item, index) => (
              <div
                key={`education-${index}`}
                className="rounded-xl border border-border bg-navy/60 p-4"
              >
                <div className="grid gap-3 sm:grid-cols-3">
                  <LabeledField
                    label="Institusi"
                    value={item.institution || ""}
                    onChange={(event) =>
                      updateItem(setEducation, index, "institution", event.target.value)
                    }
                  />
                  <LabeledField
                    label="Gelar / jurusan"
                    value={item.degree || ""}
                    onChange={(event) =>
                      updateItem(setEducation, index, "degree", event.target.value)
                    }
                  />
                  <LabeledField
                    label="Periode"
                    value={item.period || ""}
                    onChange={(event) =>
                      updateItem(setEducation, index, "period", event.target.value)
                    }
                    placeholder="2016 - 2020"
                  />
                </div>
                <label className="mt-3 block">
                  <span className="label">Detail (satu baris per poin)</span>
                  <textarea
                    className="input min-h-20"
                    rows={3}
                    value={detailsToText(item.details)}
                    onChange={(event) =>
                      updateItem(
                        setEducation,
                        index,
                        "details",
                        textToDetails(event.target.value)
                      )
                    }
                  />
                </label>
                <button
                  type="button"
                  onClick={() => removeItem(setEducation, index)}
                  className="mt-3 text-xs font-semibold uppercase tracking-wider text-slate-400 transition hover:text-danger"
                >
                  Hapus entri
                </button>
              </div>
            ))}
          </SectionCard>

          <SectionCard
            title="Pengalaman"
            description="Urutan bebas; tulis poin pencapaian sebagai baris terpisah."
            action={
              <button
                type="button"
                className="btn-ghost px-3 py-2 text-xs"
                onClick={() => addItem(setExperience, EMPTY_EXPERIENCE)}
              >
                Tambah pengalaman
              </button>
            }
          >
            {experience.length === 0 && (
              <p className="text-sm text-slate-500">
                Belum ada pengalaman terdeteksi.
              </p>
            )}
            {experience.map((item, index) => (
              <div
                key={`experience-${index}`}
                className="rounded-xl border border-border bg-navy/60 p-4"
              >
                <div className="grid gap-3 sm:grid-cols-3">
                  <LabeledField
                    label="Posisi"
                    value={item.role || ""}
                    onChange={(event) =>
                      updateItem(setExperience, index, "role", event.target.value)
                    }
                  />
                  <LabeledField
                    label="Perusahaan"
                    value={item.company || ""}
                    onChange={(event) =>
                      updateItem(setExperience, index, "company", event.target.value)
                    }
                  />
                  <LabeledField
                    label="Periode"
                    value={item.period || ""}
                    onChange={(event) =>
                      updateItem(setExperience, index, "period", event.target.value)
                    }
                    placeholder="2021 - Sekarang"
                  />
                </div>
                <label className="mt-3 block">
                  <span className="label">Detail (satu baris per poin)</span>
                  <textarea
                    className="input min-h-20"
                    rows={3}
                    value={detailsToText(item.details)}
                    onChange={(event) =>
                      updateItem(
                        setExperience,
                        index,
                        "details",
                        textToDetails(event.target.value)
                      )
                    }
                  />
                </label>
                <button
                  type="button"
                  onClick={() => removeItem(setExperience, index)}
                  className="mt-3 text-xs font-semibold uppercase tracking-wider text-slate-400 transition hover:text-danger"
                >
                  Hapus entri
                </button>
              </div>
            ))}
          </SectionCard>

          <SectionCard
            title="Proyek"
            description="Proyek pribadi, akademik, atau portofolio."
            action={
              <button
                type="button"
                className="btn-ghost px-3 py-2 text-xs"
                onClick={() => addItem(setProjects, EMPTY_PROJECT)}
              >
                Tambah proyek
              </button>
            }
          >
            {projects.length === 0 && (
              <p className="text-sm text-slate-500">
                Belum ada proyek terdeteksi.
              </p>
            )}
            {projects.map((item, index) => (
              <div
                key={`project-${index}`}
                className="rounded-xl border border-border bg-navy/60 p-4"
              >
                <div className="grid gap-3 sm:grid-cols-2">
                  <LabeledField
                    label="Nama proyek"
                    value={item.name || ""}
                    onChange={(event) =>
                      updateItem(setProjects, index, "name", event.target.value)
                    }
                  />
                  <LabeledField
                    label="Periode"
                    value={item.period || ""}
                    onChange={(event) =>
                      updateItem(setProjects, index, "period", event.target.value)
                    }
                    placeholder="2023"
                  />
                </div>
                <label className="mt-3 block">
                  <span className="label">Deskripsi</span>
                  <textarea
                    className="input min-h-20"
                    rows={3}
                    value={item.description || ""}
                    onChange={(event) =>
                      updateItem(
                        setProjects,
                        index,
                        "description",
                        event.target.value
                      )
                    }
                  />
                </label>
                <button
                  type="button"
                  onClick={() => removeItem(setProjects, index)}
                  className="mt-3 text-xs font-semibold uppercase tracking-wider text-slate-400 transition hover:text-danger"
                >
                  Hapus entri
                </button>
              </div>
            ))}
          </SectionCard>

          <SectionCard
            title="Keahlian"
            description="Klik silang untuk menghapus. Skill baru dicocokkan ke katalog otomatis saat disimpan."
          >
            <div className="flex flex-wrap gap-2">
              {skills.length === 0 && (
                <p className="text-sm text-slate-500">Belum ada skill.</p>
              )}
              {skills.map((skill) => (
                <span
                  key={skill.name}
                  className="inline-flex items-center gap-2 rounded-full border border-accent/30 bg-accent/10 px-3 py-1 text-xs text-slate-100"
                >
                  {skill.name}
                  {skill.category && (
                    <span className="text-[10px] uppercase tracking-wider text-slate-500">
                      {skill.category}
                    </span>
                  )}
                  <button
                    type="button"
                    onClick={() => removeSkill(skill.name)}
                    aria-label={`Hapus ${skill.name}`}
                    className="text-slate-400 transition hover:text-danger"
                  >
                    x
                  </button>
                </span>
              ))}
            </div>

            <div className="flex flex-col gap-2 sm:flex-row">
              <input
                className="input"
                value={skillDraft}
                onChange={(event) => setSkillDraft(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    event.preventDefault();
                    addSkill(event);
                  }
                }}
                placeholder="Tambah skill, mis. Python atau Komunikasi"
              />
              <button
                type="button"
                className="btn-ghost shrink-0"
                onClick={addSkill}
              >
                Tambah
              </button>
            </div>
          </SectionCard>

          <div className="flex flex-wrap items-center justify-between gap-4 border-t border-border pt-6">
            <button
              type="button"
              onClick={handleDelete}
              disabled={deleting}
              className="rounded-lg border border-danger/40 px-4 py-2 text-sm font-semibold text-red-300 transition hover:bg-danger/10 disabled:opacity-60"
            >
              {deleting ? "Menghapus..." : "Hapus CV ini"}
            </button>
            <button type="submit" className="btn-primary" disabled={saving || analyzing}>
              {saving ? "Menyimpan..." : "Simpan perubahan"}
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
