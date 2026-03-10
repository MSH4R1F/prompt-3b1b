"use client";

import { Button } from "@/components/ui/button";

interface Props {
  videoUrl: string;
  onReset: () => void;
}

export function VideoPlayer({ videoUrl, onReset }: Props) {
  return (
    <div className="w-full rounded-2xl border bg-white p-4 shadow-sm">
      <video src={videoUrl} controls autoPlay className="w-full rounded-xl border bg-black/5" />
      <div className="mt-4 flex flex-wrap gap-3">
        <a href={videoUrl} download>
          <Button variant="outline">Download</Button>
        </a>
        <Button onClick={onReset}>New Video</Button>
      </div>
    </div>
  );
}
