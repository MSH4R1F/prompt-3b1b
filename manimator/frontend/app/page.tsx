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
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto flex min-h-screen w-full max-w-[1280px]">
        <aside className="hidden w-72 border-r bg-white p-5 md:flex md:flex-col">
          <div className="mb-6">
            <h1 className="text-lg font-semibold">3b1b Video Maker</h1>
            <p className="mt-1 text-xs text-slate-500">Codex-style narration workflow</p>
          </div>
          <button
            onClick={reset}
            className="rounded-lg border bg-slate-900 px-3 py-2 text-sm font-medium text-white"
          >
            New Chat
          </button>
          <div className="mt-6 text-xs text-slate-500">
            <p>Stages</p>
            <p className="mt-2">1. Planning</p>
            <p>2. Coding</p>
            <p>3. Rendering</p>
            <p>4. Uploading</p>
          </div>
        </aside>

        <section className="flex flex-1 flex-col">
          <header className="border-b bg-white px-4 py-3 md:px-8">
            <h2 className="text-sm font-medium text-slate-700">3b1b Video Maker</h2>
          </header>

          <div className="flex flex-1 flex-col gap-4 px-4 py-6 md:px-8">
            <div className="max-w-3xl rounded-2xl border bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-700">
                Build a narrated explainer video from a single prompt.
              </p>
            </div>

            {state === "generating" && !jobId && (
              <div className="max-w-3xl rounded-2xl border bg-white p-4 text-sm text-slate-500 shadow-sm">
                Submitting job...
              </div>
            )}

            {state === "generating" && jobId && (
              <div className="max-w-3xl">
                <ProgressTracker jobId={jobId} onComplete={handleComplete} onError={handleError} />
              </div>
            )}

            {state === "complete" && videoUrl && (
              <div className="max-w-3xl">
                <VideoPlayer videoUrl={videoUrl} onReset={reset} />
              </div>
            )}

            {state === "error" && (
              <div className="max-w-3xl rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                <p className="font-medium">Generation failed</p>
                <p className="mt-1">{error}</p>
                <button onClick={reset} className="mt-3 text-sm underline">
                  Try again
                </button>
              </div>
            )}
          </div>

          <div className="border-t bg-slate-50 p-4 md:px-8 md:py-6">
            <div className="mx-auto w-full max-w-3xl">
              <PromptForm onSubmit={handleSubmit} loading={state === "generating"} />
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
