const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const TOKEN_KEY = "careerlens_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

function extractError(data, fallback) {
  if (!data) return fallback;
  if (typeof data === "string") return data;
  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.detail)) {
    return data.detail.map((item) => item.msg).join(", ");
  }
  return fallback;
}

async function request(path, { method = "GET", body, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();

  if (auth && token) {
    headers.Authorization = `Bearer ${token}`;
  }

  let response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new Error(
      "Tidak bisa terhubung ke server. Pastikan API berjalan di " + API_URL
    );
  }

  const text = await response.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!response.ok) {
    const error = new Error(extractError(data, "Terjadi kesalahan"));
    error.status = response.status;
    throw error;
  }

  return data;
}

export const api = {
  register: (payload) =>
    request("/auth/register", { method: "POST", body: payload, auth: false }),
  login: (payload) =>
    request("/auth/login", { method: "POST", body: payload, auth: false }),
  me: () => request("/auth/me"),
  getProfile: (profileId) => request(`/profile/${profileId}`),
  updateProfile: (profileId, payload) =>
    request(`/profile/${profileId}`, { method: "PUT", body: payload }),
  deleteCV: (cvId) => request(`/cv/${cvId}`, { method: "DELETE" }),
  createAnalysis: (cvId) =>
    request(`/analysis/${cvId}`, { method: "POST" }),
  getAnalysis: (analysisId) => request(`/analysis/${analysisId}`),
  getAnalyses: () => request("/analysis"),
  getDashboard: (analysisId) => request(`/dashboard/${analysisId}`),
  compareAnalyses: (analysisId, otherId) =>
    request(`/analysis/${analysisId}/compare/${otherId}`),
  getJobMatches: (analysisId) =>
    request(`/jobs/match/${analysisId}`),
  getSkillGap: (analysisId) =>
    request(`/skills/gap/${analysisId}`),
};

export function uploadCV(file, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_URL}/cv/upload`);

    const token = getToken();
    if (token) {
      xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    }

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && onProgress) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    };

    xhr.onload = () => {
      let data = null;
      if (xhr.responseText) {
        try {
          data = JSON.parse(xhr.responseText);
        } catch {
          data = xhr.responseText;
        }
      }

      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(data);
        return;
      }

      const error = new Error(extractError(data, "Upload gagal"));
      error.status = xhr.status;
      reject(error);
    };

    xhr.onerror = () => {
      reject(
        new Error(
          "Tidak bisa terhubung ke server. Pastikan API berjalan di " + API_URL
        )
      );
    };

    const formData = new FormData();
    formData.append("file", file);
    xhr.send(formData);
  });
}
