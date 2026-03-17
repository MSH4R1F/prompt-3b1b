# Manimator Open-Source Readiness Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Manimator repository safe and welcoming for public open-source release on GitHub.

**Architecture:** No code changes — this plan is entirely file management, `.gitignore` hardening, credential cleanup, and documentation creation. Each task produces a clean git commit.

**Tech Stack:** Markdown, MIT License, bash (for file moves and git ops)

**Spec:** `docs/superpowers/specs/2026-03-17-opensource-ready-design.md`

---

## File Map

| Action | Path | Purpose |
|--------|------|---------|
| Modify | `.gitignore` | Add missing ignore patterns |
| Delete | `.gitignore 2` | Stray macOS duplicate |
| Create | `docs/internal/` | Gitignored home for internal planning docs |
| Move | `plan.md` → `docs/internal/plan.md` | Remove from public view |
| Move | `manim-guide.md` → `docs/internal/manim-guide.md` | Remove from public view |
| Move | `docs/plans/` → `docs/internal/plans/` | Remove from public view |
| Create | `manimator/.env.example` | Template for backend secrets (mirrors `manimator/.env`) |
| Create | `LICENSE` | MIT license |
| Create | `CONTRIBUTING.md` | Contributor guide |
| Create | `manimator/backend/README.md` | Backend architecture docs |
| Create | `README.md` | Root project documentation |

---

## Task 1: Harden `.gitignore` and remove stray file

**Files:**
- Modify: `.gitignore`
- Delete: `.gitignore 2`

- [ ] **Step 1: Read the current `.gitignore`**

```bash
cat .gitignore
```

Expected output:
```
.env
.env.example
manimator/backend/.venv-modal
.venv-modal
```

- [ ] **Step 2: Replace `.gitignore` with hardened version**

Write the following content to `.gitignore`:

```
# Secrets
.env
manimator/frontend/.env

# Python
__pycache__/
*.pyc
*.pyo
.venv/
.venv-modal
manimator/backend/.venv-modal

# Node / Next.js
node_modules/
manimator/frontend/.next/
manimator/frontend/.open-next/

# Internal planning docs (not for public)
docs/internal/

# Editor
.DS_Store
```

- [ ] **Step 3: Delete the stray `.gitignore 2` file**

```bash
rm ".gitignore 2"
```

- [ ] **Step 4: Verify git status looks clean**

```bash
git status
```

Expected: `.gitignore` shown as modified, `.gitignore 2` shown as deleted.

- [ ] **Step 5: Commit**

```bash
git add .gitignore
git rm ".gitignore 2"
git commit -m "chore: harden gitignore and remove stray duplicate file"
```

---

## Task 2: Move internal planning docs to `docs/internal/`

**Files:**
- Create: `docs/internal/` (directory)
- Move: `plan.md` → `docs/internal/plan.md`
- Move: `manim-guide.md` → `docs/internal/manim-guide.md`
- Move: `docs/plans/` → `docs/internal/plans/`

> Note: `docs/internal/` is gitignored, so these files will be untracked after the move.

- [ ] **Step 1: Check if these files are currently tracked by git**

```bash
git ls-files plan.md manim-guide.md docs/plans/
```

If any filenames appear, they are tracked and will need to be `git rm`'d from the index after moving.

- [ ] **Step 2: Create `docs/internal/` and move files**

```bash
mkdir -p docs/internal/plans
mv plan.md docs/internal/plan.md
mv manim-guide.md docs/internal/manim-guide.md
mv docs/plans/2026-03-08-manimai-v4.md docs/internal/plans/2026-03-08-manimai-v4.md
```

- [ ] **Step 3: If files were tracked, remove them from git index**

If `git ls-files` in Step 1 returned results, run:

```bash
git rm --cached plan.md manim-guide.md
git rm --cached -r docs/plans/
```

- [ ] **Step 4: Verify the files are now gitignored**

```bash
git status
```

Expected: `plan.md`, `manim-guide.md`, `docs/plans/` no longer appear (gitignored). If they were tracked, they should show as deleted from git's perspective.

- [ ] **Step 5: Commit**

```bash
git commit -m "chore: move internal planning docs out of public tree"
```

(If nothing to commit because files were never tracked, skip this step.)

---

## Task 3: Create `manimator/.env.example`

**Files:**
- Create: `manimator/.env.example`

> This gives contributors a clear template. The actual `manimator/.env` remains gitignored and is not touched.

- [ ] **Step 1: Create `manimator/.env.example`**

Write the following content:

```bash
# ── Backend secrets ────────────────────────────────────────────────────────────
# Set these as Modal named secrets (modal secret create <name> KEY=value)
# OR copy this file to manimator/.env for local development.

# Anthropic API key — used by the planner and coder pipeline stages
# modal secret create anthropic-key ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# ElevenLabs API key — used for text-to-speech voiceover generation
# modal secret create elevenlabs-key ELEVEN_API_KEY=sk_...
ELEVEN_API_KEY=your-elevenlabs-api-key-here

# Cloudflare R2 storage credentials — used to store generated .mp4 files
# modal secret create r2-credentials R2_ACCOUNT_ID=... R2_ACCESS_KEY=... R2_SECRET_KEY=... R2_BUCKET=... R2_PUBLIC_URL=...
R2_ACCOUNT_ID=your-r2-account-id
R2_ACCESS_KEY=your-r2-access-key-id
R2_SECRET_KEY=your-r2-secret-access-key
R2_BUCKET=your-r2-bucket-name
R2_PUBLIC_URL=https://pub-xxxxxxxxxxxxxxxxxxxx.r2.dev

# ── Frontend reference (not used by Modal, set in manimator/frontend/.env) ─────
# The Modal endpoint URL printed after `modal deploy`
NEXT_PUBLIC_API_URL=https://your-modal-app--manimator-api-generate.modal.run
```

- [ ] **Step 2: Verify it is not accidentally gitignored**

```bash
git status manimator/.env.example
```

Expected: shown as an untracked new file (not absent). If gitignored, check `.gitignore` — the pattern `.env.example` should not be present (it was removed in Task 1).

- [ ] **Step 3: Commit**

```bash
git add manimator/.env.example
git commit -m "chore: add backend .env.example with all required variables"
```

---

## Task 4: Create `LICENSE`

**Files:**
- Create: `LICENSE`

- [ ] **Step 1: Create `LICENSE`**

Write the following (year 2026, author from git config: Mohamed Sharif):

```
MIT License

Copyright (c) 2026 Mohamed Sharif

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 2: Commit**

```bash
git add LICENSE
git commit -m "chore: add MIT license"
```

---

## Task 5: Create `CONTRIBUTING.md`

**Files:**
- Create: `CONTRIBUTING.md`

- [ ] **Step 1: Create `CONTRIBUTING.md`**

Write the following content:

```markdown
# Contributing to Manimator

Thank you for your interest in contributing!

## Prerequisites

- Python 3.10+
- Node.js 18+
- A [Modal](https://modal.com) account (free tier works for testing)
- Anthropic API key
- ElevenLabs API key
- Cloudflare R2 bucket

## Backend Setup

```bash
cd manimator/backend

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy env template and fill in your credentials
cp ../.env.example ../.env
# Edit manimator/.env with your actual values
```

## Frontend Setup

```bash
cd manimator/frontend

# Install dependencies
npm install

# Copy env template and fill in your Modal endpoint URLs
cp .env.local.example .env
# Edit manimator/frontend/.env with the URLs from `modal deploy`
```

## Running Tests

From the repo root:

```bash
cd manimator/backend
source .venv/bin/activate
pytest ../tests/ -v
```

To skip tests that call external APIs (Claude, ElevenLabs):

```bash
pytest ../tests/ -v -m "not slow"
```

## Submitting a Pull Request

1. Fork the repo and create a branch: `git checkout -b feat/my-feature`
2. Make your changes
3. Run the test suite and make sure it passes
4. Open a PR against the `main` branch with a clear description of what you changed and why

## Code Style

- Python: follow PEP 8, keep functions focused and small
- TypeScript: follow the existing patterns in `manimator/frontend/`
- No new dependencies without discussion in the PR
```

- [ ] **Step 2: Commit**

```bash
git add CONTRIBUTING.md
git commit -m "docs: add CONTRIBUTING guide"
```

---

## Task 6: Create `manimator/backend/README.md`

**Files:**
- Create: `manimator/backend/README.md`

- [ ] **Step 1: Create `manimator/backend/README.md`**

Write the following content:

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add manimator/backend/README.md
git commit -m "docs: add backend README with architecture and module map"
```

---

## Task 7: Create root `README.md`

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create `README.md`**

Write the following content:

```markdown
# Manimator

**Manimator** turns a text prompt into an animated educational video using [Manim](https://www.manim.community/), [Claude](https://www.anthropic.com/), and [ElevenLabs](https://elevenlabs.io/).

Type a topic → get a narrated, animated explainer video in under 5 minutes.

## How It Works

```
Your prompt
    │
    ▼
Claude plans the lesson
    │
    ▼
Claude generates Manim animation code
    │
    ▼
Manim renders the video (on Modal)
    │
    ▼
ElevenLabs narrates each segment
    │
    ▼
Video uploaded to Cloudflare R2
    │
    ▼
Streamed back to the browser
```

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15 + TypeScript, deployed to Cloudflare Workers |
| Backend | Python on [Modal](https://modal.com) serverless |
| AI | [Anthropic Claude](https://www.anthropic.com/) (lesson planning + code generation + repair) |
| TTS | [ElevenLabs](https://elevenlabs.io/) (with gTTS fallback) |
| Storage | Cloudflare R2 |
| Animation | [Manim Community](https://www.manim.community/) v0.20 |

## Prerequisites

- [Modal](https://modal.com) account (free tier works)
- [Anthropic API key](https://console.anthropic.com/)
- [ElevenLabs API key](https://elevenlabs.io/)
- Cloudflare account with R2 bucket and Workers enabled

## Quickstart

### 1. Clone

```bash
git clone https://github.com/your-username/manimator.git
cd manimator
```

### 2. Backend — deploy to Modal

```bash
cd manimator/backend
pip install modal
modal setup  # authenticates your Modal account

# Create named secrets in Modal
modal secret create anthropic-key ANTHROPIC_API_KEY=sk-ant-...
modal secret create elevenlabs-key ELEVEN_API_KEY=sk_...
modal secret create r2-credentials \
  R2_ACCOUNT_ID=your-account-id \
  R2_ACCESS_KEY=your-access-key \
  R2_SECRET_KEY=your-secret-key \
  R2_BUCKET=your-bucket-name \
  R2_PUBLIC_URL=https://pub-xxxx.r2.dev

# Deploy
modal deploy modal_app.py
```

Modal will print two endpoint URLs after deploying:
```
├── manimator-api-generate  https://your-app--manimator-api-generate.modal.run
└── manimator-api-status    https://your-app--manimator-api-status.modal.run
```

### 3. Frontend — deploy to Cloudflare

```bash
cd manimator/frontend
npm install

# Copy the env template and fill in your Modal endpoint URLs
cp .env.local.example .env
# Edit .env:
#   NEXT_PUBLIC_API_URL=https://your-app--manimator-api-generate.modal.run
#   NEXT_PUBLIC_STATUS_URL=https://your-app--manimator-api-status.modal.run

# Deploy to Cloudflare Workers
npm run deploy
```

## Environment Variables

### Backend (`manimator/.env` or Modal secrets)

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude |
| `ELEVEN_API_KEY` | ElevenLabs API key for TTS |
| `R2_ACCOUNT_ID` | Cloudflare account ID |
| `R2_ACCESS_KEY` | R2 access key ID |
| `R2_SECRET_KEY` | R2 secret access key |
| `R2_BUCKET` | R2 bucket name |
| `R2_PUBLIC_URL` | Public base URL for the R2 bucket |

### Frontend (`manimator/frontend/.env`)

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Modal endpoint for video generation |
| `NEXT_PUBLIC_STATUS_URL` | Modal endpoint for job status polling |

Copy `manimator/.env.example` and `manimator/frontend/.env.local.example` for templates.

## Backend Architecture

See [`manimator/backend/README.md`](manimator/backend/README.md) for a detailed breakdown of the pipeline, module map, and render fallback strategy.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

MIT — see [`LICENSE`](LICENSE).
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add root README with quickstart and architecture overview"
```

---

## Verification Checklist

After all tasks are complete, verify:

- [ ] `git status` is clean
- [ ] `cat .gitignore` shows all new patterns
- [ ] `git ls-files | grep "\.env"` returns nothing (no `.env` files tracked)
- [ ] `git ls-files | grep "plan\.md\|manim-guide"` returns nothing
- [ ] `ls docs/internal/` shows the moved files locally
- [ ] `cat LICENSE` shows MIT with correct name and year
- [ ] `cat README.md` renders correctly (check headers, code blocks)
- [ ] `cat manimator/backend/README.md` renders correctly
- [ ] `cat manimator/.env.example` has all 7 required variables
