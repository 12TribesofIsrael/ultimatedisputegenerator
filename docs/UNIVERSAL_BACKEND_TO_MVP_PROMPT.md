## Universal Prompt: Turn Any Backend into a Web MVP (API + UI)

Copy/paste and adapt this prompt for any backend project to quickly ship a working MVP with a minimal API, containerization, hosting, and a Lovable front end.

---

You are an expert software architect and implementation partner. I have an existing backend codebase (CLI, library, or scripts). I want you to transform it into a production-ready MVP with:

1) A minimal web API around the core functionality
2) Containerization (Docker) including all system dependencies
3) Hosting instructions (Render/Railway/Fly.io/Cloud Run acceptable)
4) A simple Lovable front end to call the API and display results

Output requirements:

- Create an `api/` module exposing HTTP endpoints using FastAPI (or a lightweight equivalent) with request validation. Endpoints must be non-interactive: accept all required inputs as parameters and do not prompt.
- Refactor any CLI-only logic into callable functions that accept input/output directories and structured inputs. Avoid global state.
- Return JSON responses that include primary outputs, key metrics, and any download URLs for files generated during processing.
- Provide a Dockerfile that installs system packages (if needed: `tesseract-ocr`, `poppler-utils`, `libgl1`, etc.) and starts the API with Uvicorn.
- Provide a deployment guide with one-click style steps for one host (e.g., Render) and alternatives.
- Provide a Lovable integration guide describing form fields, file upload mapping, and results rendering, including error handling.
- Enforce privacy-by-default: process data in temp folders, avoid persisting inputs, and redact internal/system markers from user-facing content.

Deliverables checklist:

- `api/app.py` (or `api/main.py`) with endpoints and clear TODOs for wiring into the core logic
- `Dockerfile` ready for build/run
- Documentation: `docs/DEPLOYMENT.md` or `docs/LOVABLE_DEPLOYMENT.md`
- If applicable: sample curl scripts for local testing
- If applicable: graceful long-running job support (job id + polling)

Interface contract (example):

- `POST /process`: Multipart form-data (files + JSON fields) or `application/json` with URLs/params
- Response: `{ status, results[], metrics{}, downloads[] }`
- Optional: `GET /health` returns `{ status: "ok" }`
- Optional: `POST /jobs` → `{ job_id }`, `GET /jobs/{id}` → `{ status, progress, result? }`

Quality and security:

- Validate inputs, size limits, mime-types; return clear errors
- Log request ids and durations; avoid logging sensitive content
- Support CORS for the Lovable origin; support an optional API key header
- Add timeouts and circuit breakers where appropriate

Testing:

- Include local run instructions and a `curl` example for the main endpoint
- Add minimal smoke tests or a test harness if available

Finally, propose the exact code edits and file additions needed, then implement them.


