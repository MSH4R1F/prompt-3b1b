# Manimator Backend

The backend is a [Modal](https://modal.com) serverless application that takes a text prompt and produces an animated educational video `.mp4`.

## Architecture

```
User Prompt
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  Modal Function: generate_video()                       │
│                                                         │
│  1. Planner  ──► LessonPlan (structured JSON)           │
│       │                                                 │
│  2. Coder   ──► Manim scene Python code                 │
│       │                                                 │
│  3. Repair Loop (up to 2 AI-assisted retries)           │
│       │   ├── ElevenLabs init failure → gTTS fallback   │
│       │   └── LaTeX error → sanitize and retry          │
│       │                                                 │
│  4. manim render (subprocess, medium quality)           │
│       │                                                 │
│  5. Uploader ──► Cloudflare R2 (.mp4)                   │
└─────────────────────────────────────────────────────────┘
    │
    ▼
Public video URL
```

## Module Map

| File | Responsibility |
|------|---------------|
| `modal_app.py` | Entry point — defines the Modal app, wires secrets, orchestrates the pipeline, handles render retries and fallbacks |
| `pipeline/planner.py` | Calls Claude to break the prompt into a structured `LessonPlan` (list of segments with topic, narration, duration) |
| `pipeline/coder.py` | Calls Claude to generate a Manim `VoiceoverScene` from the `LessonPlan`; also contains `repair_code()` for AI-assisted fixes |
| `pipeline/uploader.py` | Uploads a rendered `.mp4` to Cloudflare R2 via boto3 and returns the public URL |
| `pipeline/pedagogy.py` | Optional pedagogical scaffolding helpers |
| `pipeline/orchestrator.py` | Higher-level orchestration utilities |
| `pipeline/utils.py` | Shared utilities (e.g. `strip_markdown_fences`) |
| `schemas/lesson.py` | Pydantic model: `LessonPlan`, `LessonSegment` |
| `schemas/job.py` | Pydantic model: job status/result |
| `manim_helpers/tools.py` | Helper functions injected into Claude's coder prompt as function signatures |
| `manim_helpers/templates/` | Few-shot example scenes used in the coder prompt |
| `prompts/` | System prompt text files loaded at runtime |

## Modal Secrets

Secrets are stored as named Modal secrets and injected as environment variables inside the container:

| Modal Secret Name | Environment Variable | Used By |
|-------------------|---------------------|---------|
| `anthropic-key` | `ANTHROPIC_API_KEY` | `planner.py`, `coder.py` |
| `elevenlabs-key` | `ELEVEN_API_KEY` | ElevenLabs TTS in the render container |
| `r2-credentials` | `R2_ACCOUNT_ID`, `R2_ACCESS_KEY`, `R2_SECRET_KEY`, `R2_BUCKET`, `R2_PUBLIC_URL` | `uploader.py` |

Create them before deploying:

```bash
modal secret create anthropic-key ANTHROPIC_API_KEY=sk-ant-...
modal secret create elevenlabs-key ELEVEN_API_KEY=sk_...
modal secret create r2-credentials \
  R2_ACCOUNT_ID=... \
  R2_ACCESS_KEY=... \
  R2_SECRET_KEY=... \
  R2_BUCKET=manim-videos \
  R2_PUBLIC_URL=https://pub-xxxx.r2.dev
```

## Deployment

```bash
cd manimator/backend

# Install Modal CLI
pip install modal

# Authenticate
modal setup

# Deploy
modal deploy modal_app.py
```

After deploying, Modal prints two endpoint URLs — copy these into your frontend `.env`.

## Running Tests Locally

```bash
cd manimator/backend
pip install -r requirements.txt
pytest ../tests/ -v

# Skip tests that call external APIs
pytest ../tests/ -v -m "not slow"
```

## Render Fallback Strategy

The pipeline is designed to be resilient to code generation failures:

1. **ElevenLabs preflight** — if the API key is missing or invalid, the code is rewritten to use gTTS before the first render attempt
2. **LaTeX fallback** — on LaTeX/DVI errors, `Tex(` is replaced with `Text(` and Unicode symbols are ASCII-ified
3. **AI repair loop** — up to 2 attempts where the render error is fed back to Claude via `repair_code()` for a fix
4. **Emergency fallback scene** — if all attempts fail, a minimal valid gTTS scene is substituted so the pipeline always produces output
