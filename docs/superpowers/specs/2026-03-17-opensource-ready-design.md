# Manimator — Open-Source Readiness Design

**Date:** 2026-03-17
**Approach:** Option B — Full open-source polish
**License:** MIT

---

## Goal

Make the Manimator repository safe and welcoming for public open-source release on GitHub. This covers credential hygiene, `.gitignore` hardening, internal doc cleanup, and documentation creation.

---

## Section 1 — Security & Cleanup

### Credential hygiene
- `manimator/.env` contains live credentials (Anthropic API key, ElevenLabs API key, Cloudflare R2 keys). These were **never committed** to git, so history is clean.
- Owner must manually rotate all three sets of credentials before publishing.
- Replace `manimator/.env` with `manimator/.env.example` containing placeholder values and comments.

### `.gitignore` hardening (root)
Add the following patterns that are currently missing:
- `node_modules/`
- `.next/`
- `.open-next/`
- `__pycache__/`
- `*.pyc`
- `manimator/frontend/.env`
- `docs/internal/`

### Stray file cleanup
- Delete `.gitignore 2` from the repo root (stray macOS duplicate).

### Internal doc relocation
Move the following to `docs/internal/` (which is gitignored):
- `plan.md`
- `manim-guide.md`
- `docs/plans/2026-03-08-manimai-v4.md`

---

## Section 2 — Files to Create

### `LICENSE`
MIT license, attributed to the repository owner.

### `README.md` (root)
Covers:
- What Manimator is: AI-powered animated educational video generator using Manim + Claude + ElevenLabs
- Architecture overview (text diagram): user prompt → Modal backend (plan → code → render) → Cloudflare R2 → Next.js frontend on Cloudflare Workers
- Prerequisites: Modal account, Anthropic API key, ElevenLabs API key, Cloudflare R2 bucket, Cloudflare Workers
- Backend quickstart: clone, create Modal secrets, `modal deploy`
- Frontend quickstart: copy `.env.local.example`, fill in Modal URLs, `npm run deploy`
- Environment variables reference table (all required vars, what they're for)
- Link to `CONTRIBUTING.md`

### `manimator/backend/README.md`
Covers:
- Pipeline architecture deep-dive with stage-by-stage explanation:
  1. **Planner** (`pipeline/planner.py`) — Claude breaks the prompt into lesson segments
  2. **Coder** (`pipeline/coder.py`) — Claude generates Manim scene code per segment
  3. **Repair loop** (`modal_app.py`) — up to 2 AI-assisted repair attempts on render failure, plus LaTeX and ElevenLabs fallbacks
  4. **Renderer** — `manim render` subprocess inside Modal container
  5. **Uploader** (`pipeline/uploader.py`) — uploads final `.mp4` to Cloudflare R2
- Module map: what each file in `backend/` does
- How Modal secrets are wired (named secrets → env vars inside container)
- How to run tests locally: `pytest manimator/tests/`
- How to run the smoke test: `python manimator/backend/smoke_test.py`

### `manimator/backend/.env.example`
All required environment variables with placeholder values and inline comments:
- `ANTHROPIC_API_KEY` — for Claude API calls
- `ELEVEN_API_KEY` — for ElevenLabs TTS
- `R2_ACCOUNT_ID`, `R2_ACCESS_KEY`, `R2_SECRET_KEY`, `R2_BUCKET`, `R2_PUBLIC_URL` — for Cloudflare R2 storage
- `NEXT_PUBLIC_API_URL` — Modal endpoint URL (for frontend reference)

### `CONTRIBUTING.md`
Covers:
- How to fork and clone
- Backend local setup (Python venv, `pip install -r requirements.txt`)
- Frontend local setup (`npm install`, copy `.env.local.example`)
- Running tests
- PR guidelines

---

## Out of Scope

- No changes to application code
- No new features
- No restructuring of the codebase beyond moving internal docs
