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
    <form
      onSubmit={handleSubmit}
      className="w-full rounded-2xl border bg-white p-4 shadow-sm"
    >
      <div className="mb-3 flex flex-col gap-2">
        <Label htmlFor="prompt" className="text-xs uppercase tracking-wide text-slate-500">
          Prompt
        </Label>
        <Textarea
          id="prompt"
          placeholder="Explain gradient descent to a beginner with a geometric intuition."
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          rows={4}
          className="resize-none border-0 bg-transparent px-0 text-base shadow-none focus-visible:ring-0"
          required
        />
      </div>

      <div className="flex flex-col gap-3 border-t pt-3 md:flex-row md:items-end">
        <div className="flex flex-1 flex-col gap-2">
          <Label htmlFor="duration" className="text-xs uppercase tracking-wide text-slate-500">
            Duration
          </Label>
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
          <Label htmlFor="audience" className="text-xs uppercase tracking-wide text-slate-500">
            Audience
          </Label>
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

        <Button type="submit" disabled={loading || !prompt.trim()} className="w-full md:w-auto">
          {loading ? "Generating..." : "Generate"}
        </Button>
      </div>
    </form>
  );
}
