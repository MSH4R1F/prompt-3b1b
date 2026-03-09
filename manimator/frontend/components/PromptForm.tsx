"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { GenerateRequest } from "@/lib/types";

interface Props {
  onSubmit: (req: GenerateRequest) => void;
  loading: boolean;
}

export function PromptForm({ onSubmit, loading }: Props) {
  const [prompt, setPrompt] = useState("");
  const [duration, setDuration] = useState("60");
  const [audience, setAudience] = useState<"beginner" | "intermediate" | "advanced">("beginner");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!prompt.trim()) return;
    onSubmit({ prompt: prompt.trim(), duration: parseInt(duration, 10), audience });
  }

  return (
    <form onSubmit={handleSubmit} className="flex w-full max-w-xl flex-col gap-4">
      <div className="flex flex-col gap-2">
        <Label htmlFor="prompt">What should we explain?</Label>
        <Textarea
          id="prompt"
          placeholder="e.g. Explain gradient descent to a beginner in 60 seconds"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          rows={3}
          required
        />
      </div>

      <div className="flex gap-4">
        <div className="flex flex-1 flex-col gap-2">
          <Label htmlFor="duration">Duration (seconds)</Label>
          <Select value={duration} onValueChange={setDuration}>
            <SelectTrigger id="duration">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="30">30s</SelectItem>
              <SelectItem value="60">60s</SelectItem>
              <SelectItem value="90">90s</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex flex-1 flex-col gap-2">
          <Label htmlFor="audience">Audience</Label>
          <Select value={audience} onValueChange={(v) => setAudience(v as typeof audience)}>
            <SelectTrigger id="audience">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="beginner">Beginner</SelectItem>
              <SelectItem value="intermediate">Intermediate</SelectItem>
              <SelectItem value="advanced">Advanced</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <Button type="submit" disabled={loading || !prompt.trim()}>
        {loading ? "Generating..." : "Generate Video"}
      </Button>
    </form>
  );
}
