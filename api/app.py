from __future__ import annotations

from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import tempfile
import shutil
import os
import uuid

from .adapter import process_reports

app = FastAPI(title="Ultimate Dispute Letter Generator API", version="0.1.0")

# CORS (MVP permissive; restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory job store (MVP)
JOBS: dict[str, dict] = {}


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/process-report")
async def process_report_endpoint(
    files: List[UploadFile] = File(...),
    full_name: str = Form(...),
    address: str = Form(...),
    round_number: int = Form(1),
):
    # Save uploaded files to a temporary working directory
    with tempfile.TemporaryDirectory() as tmpdir:
        input_dir = os.path.join(tmpdir, "consumerreport", "input")
        output_dir = os.path.join(tmpdir, "outputletter")
        os.makedirs(input_dir, exist_ok=True)

        saved_files = []
        for f in files:
            dest_path = os.path.join(input_dir, f.filename)
            with open(dest_path, "wb") as out:
                shutil.copyfileobj(f.file, out)
            saved_files.append(dest_path)

        result = process_reports(
            input_dir=input_dir,
            output_base_dir=output_dir,
            full_name=full_name,
            address=address,
            round_number=round_number,
        )

        return JSONResponse(result)



@app.post("/jobs/process-report")
async def create_job(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    full_name: str = Form(...),
    address: str = Form(...),
    round_number: int = Form(1),
):
    job_id = str(uuid.uuid4())
    JOBS[job_id] = {"status": "pending"}

    def _run_job(paths: list[str], name: str, addr: str, round_n: int):
        JOBS[job_id] = {"status": "running"}
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                input_dir = os.path.join(tmpdir, "consumerreport", "input")
                output_dir = os.path.join(tmpdir, "outputletter")
                os.makedirs(input_dir, exist_ok=True)

                for src_path in paths:
                    dest_path = os.path.join(input_dir, os.path.basename(src_path))
                    shutil.copyfile(src_path, dest_path)

                result = process_reports(
                    input_dir=input_dir,
                    output_base_dir=output_dir,
                    full_name=name,
                    address=addr,
                    round_number=round_n,
                )
                JOBS[job_id] = {"status": "done", "result": result}
        except Exception as e:
            JOBS[job_id] = {"status": "error", "error": str(e)}

    persisted: list[str] = []
    for f in files:
        tmpf = tempfile.NamedTemporaryFile(delete=False)
        try:
            with tmpf as out:
                shutil.copyfileobj(f.file, out)
            persisted.append(tmpf.name)
        finally:
            f.file.close()

    background_tasks.add_task(_run_job, persisted, full_name, address, round_number)
    return {"job_id": job_id, "status": "queued"}


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        return JSONResponse({"error": "job not found"}, status_code=404)
    return job

