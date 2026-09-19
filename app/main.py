# -*- coding: utf-8 -*-
import os
import uuid
import shutil
import logging
import threading
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from engine.transliterator import full_pipeline
from extractors.extract import extract_text
from renderers.render import render_for_format

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("osmanlica")

APP_DIR = Path(__file__).parent
WORK_DIR = Path(os.environ.get("WORK_DIR", "/data/jobs"))
WORK_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Osmanlıca Çevirici")

# job_id -> {"status": ..., "progress": (done,total), "error": ..., "output_path": ...}
JOBS = {}


def process_job(job_id: str, input_path: str, output_ext: str, use_ollama: bool):
    job = JOBS[job_id]
    try:
        job["status"] = "metin_cikariliyor"
        raw_text = extract_text(input_path)
        if not raw_text.strip():
            raise RuntimeError("Dosyadan metin çıkarılamadı (boş içerik).")

        job["status"] = "cevriliyor"

        def progress_cb(done, total):
            job["progress"] = {"done": done, "total": total}

        result = full_pipeline(raw_text, use_ollama_refine=use_ollama, progress_callback=progress_cb)

        job["status"] = "render_ediliyor"
        out_dir = WORK_DIR / job_id
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = str(out_dir / f"osmanlica_ceviri{output_ext}")
        render_for_format(result["ottoman_text"], output_ext, out_path)

        # jpg/png girdiler pdf olarak çıkıyor, gerçek yolu güncelle
        if output_ext.lower() in (".jpg", ".jpeg", ".png") and not os.path.exists(out_path):
            out_path = out_path.rsplit(".", 1)[0] + ".pdf"

        job["output_path"] = out_path
        job["detected_lang"] = result["detected_lang"]
        job["status"] = "tamamlandi"
    except Exception as e:
        logger.exception("İşlem hatası (job %s)", job_id)
        job["status"] = "hata"
        job["error"] = str(e)


@app.post("/api/upload")
async def upload(file: UploadFile = File(...), use_ollama: bool = Form(True)):
    job_id = str(uuid.uuid4())
    job_dir = WORK_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".pdf", ".txt", ".epub", ".jpg", ".jpeg", ".png"):
        raise HTTPException(400, f"Desteklenmeyen dosya türü: {ext}")

    input_path = str(job_dir / f"input{ext}")
    with open(input_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    JOBS[job_id] = {"status": "kuyrukta", "progress": None, "error": None, "output_path": None}
    t = threading.Thread(target=process_job, args=(job_id, input_path, ext, use_ollama), daemon=True)
    t.start()

    return {"job_id": job_id}


@app.post("/api/upload-text")
async def upload_text(text: str = Form(...), use_ollama: bool = Form(True)):
    job_id = str(uuid.uuid4())
    job_dir = WORK_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    input_path = str(job_dir / "input.txt")
    with open(input_path, "w", encoding="utf-8") as f:
        f.write(text)

    JOBS[job_id] = {"status": "kuyrukta", "progress": None, "error": None, "output_path": None}
    t = threading.Thread(target=process_job, args=(job_id, input_path, ".txt", use_ollama), daemon=True)
    t.start()

    return {"job_id": job_id}


@app.get("/api/status/{job_id}")
async def status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "İş bulunamadı")
    return JSONResponse({
        "status": job["status"],
        "progress": job.get("progress"),
        "error": job.get("error"),
        "detected_lang": job.get("detected_lang"),
        "ready": job["status"] == "tamamlandi",
    })


@app.get("/api/download/{job_id}")
async def download(job_id: str):
    job = JOBS.get(job_id)
    if not job or job["status"] != "tamamlandi":
        raise HTTPException(404, "Dosya hazır değil")
    path = job["output_path"]
    return FileResponse(path, filename=os.path.basename(path))


app.mount("/", StaticFiles(directory=str(APP_DIR / "static"), html=True), name="static")
