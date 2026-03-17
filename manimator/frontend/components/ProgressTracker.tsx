"use client";

import { useEffect, useRef, useState } from "react";

import { Progress } from "@/components/ui/progress";
import { getStatus } from "@/lib/api";
import { StatusResponse } from "@/lib/types";

const STAGES = ["planning", "coding", "rendering", "uploading"];
const STAGE_LABELS: Record<string, string> = {
  planning: "Planning lesson...",
  coding: "Writing animation code...",
  rendering: "Rendering video...",
  uploading: "Uploading video...",
};

interface Props {
  jobId: string;
  onComplete: (videoUrl: string) => void;
  onError: (error: string) => void;
}

export function ProgressTracker({ jobId, onComplete, onError }: Props) {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [pollFailures, setPollFailures] = useState(0);
  const onCompleteRef = useRef(onComplete);
  const onErrorRef = useRef(onError);
  onCompleteRef.current = onComplete;
  onErrorRef.current = onError;

  useEffect(() => {
    let cancelled = false;
    const deadline = Date.now() + 5 * 60 * 1000; // 5-minute hard limit
    let consecutiveFailures = 0;

    async function poll() {
      while (!cancelled) {
        if (Date.now() > deadline) {
          onErrorRef.current("Timed out after 5 minutes. Please try again.");
          return;
        }
        try {
          const s = await getStatus(jobId);
          if (!cancelled) setStatus(s);
          consecutiveFailures = 0;
          setPollFailures(0);

          if (s.status === "completed" && s.video_url) {
            onCompleteRef.current(s.video_url);
            return;
          }
          if (s.status === "failed") {
            onErrorRef.current(s.error ?? "Unknown error");
            return;
          }
        } catch (err) {
          // Keep polling through transient errors, but fail fast if endpoint is misconfigured.
          consecutiveFailures += 1;
          setPollFailures(consecutiveFailures);
          if (consecutiveFailures >= 5) {
            const message = err instanceof Error ? err.message : "Failed to poll job status.";
            onErrorRef.current(message);
            return;
          }
        }
        await new Promise((resolve) => setTimeout(resolve, 3000));
      }
    }

    poll();
    return () => {
      cancelled = true;
    };
  }, [jobId]);

  const stage = status?.stage ?? "planning";
  const stageIndex = STAGES.indexOf(stage);
  const progress = stageIndex < 0 ? 10 : ((stageIndex + 1) / STAGES.length) * 90;

  return (
    <div className="w-full rounded-2xl border bg-white p-4 shadow-sm">
      <p className="mb-2 text-sm font-medium text-slate-700">{STAGE_LABELS[stage] ?? "Processing..."}</p>
      <Progress value={progress} />
      <p className="mt-2 text-xs text-slate-500">Job ID: {jobId}</p>
      {pollFailures > 0 && (
        <p className="mt-1 text-xs text-amber-600">Reconnecting to status endpoint...</p>
      )}
    </div>
  );
}
