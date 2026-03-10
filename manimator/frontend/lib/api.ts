import { GenerateRequest, GenerateResponse, StatusResponse } from "./types";

const GENERATE_URL = (process.env.NEXT_PUBLIC_API_URL ?? "").trim();
const STATUS_URL = (
  process.env.NEXT_PUBLIC_STATUS_URL ??
  (GENERATE_URL.includes("api-generate")
    ? GENERATE_URL.replace("api-generate", "api-status")
    : "")
).trim();

export async function generateVideo(req: GenerateRequest): Promise<GenerateResponse> {
  if (!GENERATE_URL) {
    throw new Error("NEXT_PUBLIC_API_URL is not configured.");
  }
  const res = await fetch(GENERATE_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Generate failed: ${res.status}`);
  }
  return res.json();
}

export async function getStatus(jobId: string): Promise<StatusResponse> {
  if (!STATUS_URL) {
    throw new Error(
      "Status endpoint is not configured. Set NEXT_PUBLIC_STATUS_URL or use an API URL containing 'api-generate'.",
    );
  }
  const res = await fetch(`${STATUS_URL}?job_id=${encodeURIComponent(jobId)}`);
  if (!res.ok) {
    throw new Error(`Status failed: ${res.status}`);
  }
  return res.json();
}
