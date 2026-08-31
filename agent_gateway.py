#!/usr/bin/env python3
"""Minimal Agent Gateway.

GitHub stores the control-plane code. The actual Agent runtime must be
installed on a user-owned PC/VPS and explicitly connected to this service.
"""
from __future__ import annotations

import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Personal Agent Gateway", version="0.1.0")

API_TOKEN = os.getenv("AGENT_GATEWAY_TOKEN", "")


@dataclass
class Job:
    id: str
    task: str
    target: str = "local"
    status: str = "queued"
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)


jobs: Dict[str, Job] = {}
lock = threading.Lock()


class JobRequest(BaseModel):
    task: str = Field(min_length=1, max_length=10_000)
    target: str = Field(default="local", min_length=1, max_length=100)


class JobResult(BaseModel):
    status: str
    result: Optional[str] = None
    error: Optional[str] = None


def auth(token: str | None) -> None:
    if not API_TOKEN:
        return
    if token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid agent gateway token")


@app.get("/health")
def health():
    return {"status": "ok", "version": app.version}


@app.post("/jobs")
def create_job(req: JobRequest, x_agent_token: str | None = None):
    auth(x_agent_token)
    job = Job(id=str(uuid.uuid4()), task=req.task, target=req.target)
    with lock:
        jobs[job.id] = job
    return {"job_id": job.id, "status": job.status, "target": job.target}


@app.get("/jobs/{job_id}", response_model=JobResult)
def get_job(job_id: str, x_agent_token: str | None = None):
    auth(x_agent_token)
    with lock:
        job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResult(status=job.status, result=job.result, error=job.error)


@app.post("/jobs/{job_id}/result")
def set_job_result(job_id: str, payload: JobResult, x_agent_token: str | None = None):
    auth(x_agent_token)
    with lock:
        job = jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        job.status = payload.status
        job.result = payload.result
        job.error = payload.error
    return {"ok": True}


@app.get("/jobs")
def list_jobs(x_agent_token: str | None = None):
    auth(x_agent_token)
    with lock:
        return [
            {"job_id": j.id, "task": j.task, "target": j.target, "status": j.status}
            for j in jobs.values()
        ]
