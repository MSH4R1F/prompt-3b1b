"use client";

import { Button } from "@/components/ui/button";

interface Props {
  videoUrl: string;
  onReset: () => void;
}

export function VideoPlayer({ videoUrl, onReset }: Props) {
  return (
    <div className="flex w-full max-w-2xl flex-col items-center gap-4">
      <video src={videoUrl} controls autoPlay className="w-full rounded-lg shadow-lg" />
      <div className="flex gap-3">
        <a href={videoUrl} download>
          <Button variant="outline">Download</Button>
        </a>
        <Button onClick={onReset}>Generate Another</Button>
      </div>
    </div>
  );
}
