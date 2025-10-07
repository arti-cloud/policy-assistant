from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Header
from typing import List
from app.schemas import AskRequest, AskResponse, IngestResponse, Feedback
from app.retriever import ask_question
from app.ingestion import ingest_file
from app.config import settings
import uuid, os

router = APIRouter()

def check_api_key(x_api_key: str = Header(None)):
    if settings.API_KEY and x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

@router.get("/healthz")
def healthz():
    return {"status": "ok"}

@router.post("/ask", response_model=AskResponse)
def ask(req: AskRequest, x_api_key: str = Header(None)):
    # Optional API key check
    if settings.API_KEY:
        check_api_key(x_api_key)
    resp = ask_question(req.question, filters=req.filters, top_k=req.top_k)
    return resp

@router.post("/ingest", response_model=IngestResponse)
async def ingest(files: List[UploadFile] = File(...), x_api_key: str = Header(None)):
    if settings.API_KEY:
        check_api_key(x_api_key)
    upserted = 0
    errors = []
    for f in files:
        dest = f"/tmp/{uuid.uuid4().hex}_{f.filename}"
        content = await f.read()
        with open(dest, "wb") as fh:
            fh.write(content)
        try:
            upserted += ingest_file(dest, metadata={"filename": f.filename})
        except Exception as e:
            errors.append(f"{f.filename}: {str(e)}")
    return {"upserted": upserted, "errors": errors}

@router.get("/docs")
def list_docs():
    # in prod return metadata from DB
    return {"docs": ["leave_policy_v3.pdf", "exit_policy_v2.pdf"]}

@router.get("/docs/{doc_id}")
def get_doc(doc_id: str):
    # Return metadata and optionally a secure deep link (signed URL)
    return {"doc_id": doc_id, "title": doc_id, "owner": "HR", "url": None}

@router.post("/feedback")
def feedback(payload: Feedback):
    # store feedback in DB or file
    print("FB:", payload)
    return {"status": "ok"}
