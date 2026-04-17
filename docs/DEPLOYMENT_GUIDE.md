# Deployment Guide

## Runtime requirements

- Python 3.11+
- Docker + Docker Compose (recommended)
- Optional: Gemini API key for AI guidance/remediation

## Environment

Create `.env` in repository root:

```bash
GEMINI_API_KEY=your_key_here
FLASK_ENV=production
```

`GEMINI_API_KEY` is optional; when omitted, fallback remediation text is used.

## Docker deployment (recommended)

```bash
docker compose up --build -d
```

Verify:

```bash
curl http://localhost:8000/health
```

Open UI:

```text
http://localhost:8000/
```

Stop:

```bash
docker compose down
```

## Local deployment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.app
```

## Container details

- Port: `8000`
- Entrypoint: Gunicorn serving `src.app:app`
- Docker healthcheck: `GET /health`
- Fixtures volume (compose): `./docs/fixtures -> /evaluator/assets` (read-only)

## Production notes

- Keep `GEMINI_API_KEY` in secret management, not in committed files.
- Tune Gunicorn workers/timeouts in `Dockerfile` if needed.
- Monitor memory when analyzing large PDFs (`MAX_MEMORY_MB` config).
