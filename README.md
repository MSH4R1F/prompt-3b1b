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
