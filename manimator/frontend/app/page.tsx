"use client";

import { useCallback, useState } from "react";

import { ProgressTracker } from "@/components/ProgressTracker";
import { PromptForm } from "@/components/PromptForm";
import { VideoPlayer } from "@/components/VideoPlayer";
import { generateVideo } from "@/lib/api";
import { GenerateRequest } from "@/lib/types";

type AppState = "idle" | "generating" | "complete" | "error";

export default function Home() {
  const [state, setState] = useState<AppState>("idle");
  const [jobId, setJobId] = useState<string | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(req: GenerateRequest) {
    setState("generating");
    setError(null);
    try {
      const { job_id } = await generateVideo(req);
      setJobId(job_id);
    } catch (e) {
      setError(String(e));
      setState("error");
    }
  }

  const handleComplete = useCallback((url: string) => {
    setVideoUrl(url);
    setState("complete");
  }, []);

  const handleError = useCallback((err: string) => {
    setError(err);
    setState("error");
  }, []);

  function reset() {
    setState("idle");
    setJobId(null);
    setVideoUrl(null);
    setError(null);
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-8 p-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold">ManimAI</h1>
        <p className="mt-2 text-muted-foreground">Type a topic. Get a narrated explainer video.</p>
      </div>

      {state === "idle" && <PromptForm onSubmit={handleSubmit} loading={false} />}

      {state === "generating" && jobId && (
        <ProgressTracker jobId={jobId} onComplete={handleComplete} onError={handleError} />
      )}

      {state === "complete" && videoUrl && <VideoPlayer videoUrl={videoUrl} onReset={reset} />}

      {state === "error" && (
        <div className="flex flex-col items-center gap-3">
          <p className="text-destructive">Error: {error}</p>
          <button onClick={reset} className="text-sm underline">
            Try again
          </button>
        </div>
      )}
    </main>
  );
}
