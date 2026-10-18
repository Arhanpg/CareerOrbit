/**
 * CareerOrbit API Client
 * Supports dynamic environment routing for Vercel deployment and local development.
 */
export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
).replace(/\/+$/, "");

export function getApiUrl(path: string): string {
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE_URL}${cleanPath}`;
}

export async function apiFetch<T = any>(path: string, options?: RequestInit): Promise<T> {
  const fullUrl = getApiUrl(path);
  const isFormData = options?.body instanceof FormData;

  const res = await fetch(fullUrl, {
    ...options,
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...(options?.headers || {}),
    },
  });

  if (!res.ok) {
    const errText = await res.text().catch(() => res.statusText);
    throw new Error(`API Error (${res.status}): ${errText}`);
  }

  return res.json();
}
