export type JobStatus = "processing" | "completed" | "failed";

export interface GenerateRequest {
  prompt: string;
  duration: number;
  audience: "beginner" | "intermediate" | "advanced";
  voice?: string;
}

export interface GenerateResponse {
  job_id: string;
}

export interface StatusResponse {
  status: JobStatus;
  job_id?: string;
  video_url?: string;
  error?: string;
  stage?: string;
}
