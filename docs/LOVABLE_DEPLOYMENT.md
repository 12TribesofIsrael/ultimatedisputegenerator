## Deploying with Lovable + Python API

This guide explains how to deploy a minimal FastAPI backend for the Ultimate Dispute Letter Generator and connect it to a Lovable app UI.

### Backend

- Endpoint: `POST /process-report` (multipart form-data)
  - `files`: One or more credit report PDFs
  - `full_name`: Consumer full name
  - `address`: Consumer address
  - `round_number`: Dispute round (default 1)

Run locally:

```
uvicorn api.app:app --reload
```

Container build:

```
docker build -t udlg-api .
docker run -p 8000:8000 udlg-api
```

Required system packages are installed in the Dockerfile: `tesseract-ocr`, `poppler-utils`, `libgl1`.

### Hosting options

- Render / Railway / Fly.io: Create a new service from the repo using the Dockerfile.
- Google Cloud Run: Build/push then `gcloud run deploy`.

### Lovable front end

In Lovable (`https://lovable.dev/`):

1. Create a new app.
2. Add a File Upload component (allow multiple PDFs).
3. Add Text inputs for Full Name and Address, and a Number input for Round.
4. Add a Button with an HTTP Action:
   - Method: POST
   - URL: `https://<your-api>/process-report`
   - Body: Multipart form-data mapping file input(s) and fields
5. Bind the HTTP response to a Results view that renders returned letters and metadata.
6. Optional: Add a second action to download a ZIP if exposed by the backend.

Async option (recommended for large PDFs):

- Create a first Button calling `POST https://<your-api>/jobs/process-report` with the same form-data. Save `job_id` from the response.
- Poll `GET https://<your-api>/jobs/{job_id}` every 2–3s until `status=done`, then render `result`.

### Non-interactive pipeline

Refactor your processing so it accepts an input directory, consumer info, and round number, and returns a JSON payload instead of prompting. Integrate that function inside `api/app.py` to replace the placeholder response.

### Privacy and compliance

- Do not persist PDFs by default; process in a temporary directory.
- Strip system markers; ensure letters appear consumer-generated.
- Consider rate limiting and an API key header.


