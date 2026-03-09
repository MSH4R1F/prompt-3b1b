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
  const onCompleteRef = useRef(onComplete);
  const onErrorRef = useRef(onError);
  onCompleteRef.current = onComplete;
  onErrorRef.current = onError;

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      while (!cancelled) {
        try {
          const s = await getStatus(jobId);
          if (!cancelled) setStatus(s);

          if (s.status === "completed" && s.video_url) {
            onCompleteRef.current(s.video_url);
            return;
          }
          if (s.status === "failed") {
            onErrorRef.current(s.error ?? "Unknown error");
            return;
          }
        } catch {
          // Keep polling through transient errors.
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
    <div className="flex w-full max-w-xl flex-col gap-3">
      <p className="text-sm text-muted-foreground">{STAGE_LABELS[stage] ?? "Processing..."}</p>
      <Progress value={progress} />
      <p className="text-xs text-muted-foreground">Job ID: {jobId}</p>
    </div>
  );
}
