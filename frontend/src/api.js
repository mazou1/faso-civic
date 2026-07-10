// Petit client API : en dev Vite proxe /api → FastAPI ; en prod nginx fait pareil.
const BASE = "/api";

export async function apiGet(chemin, params = {}) {
  const url = new URL(BASE + chemin, window.location.origin);
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, v);
  }
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`API ${resp.status} sur ${chemin}`);
  return resp.json();
}
