import { GenerateRequest, GenerateResponse, StatusResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";
const GENERATE_URL = `${API_BASE}`;
const STATUS_URL = API_BASE.replace("api-generate", "api-status");

export async function generateVideo(req: GenerateRequest): Promise<GenerateResponse> {
  const res = await fetch(GENERATE_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    throw new Error(`Generate failed: ${res.status}`);
  }
  return res.json();
}

export async function getStatus(jobId: string): Promise<StatusResponse> {
  const res = await fetch(`${STATUS_URL}?job_id=${encodeURIComponent(jobId)}`);
  if (!res.ok) {
    throw new Error(`Status failed: ${res.status}`);
  }
  return res.json();
}
