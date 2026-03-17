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

---
