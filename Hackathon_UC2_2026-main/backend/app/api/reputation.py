"""
Reputation Intelligence API Endpoints
"""
import os
import json
import uuid
import asyncio
from fastapi import APIRouter, Request, Header, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..database import SessionLocal
from ..models import ReputationReport
from ..workflows import ReputationWorkflow
from ..utils.logging_config import get_logger

router = APIRouter(prefix="/reputation", tags=["Reputation Intelligence"])

# Configuration
environment = os.getenv("Environment", "dev")
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "dev_secret_key")

# Read token
_key_dev = os.getenv("X_API_KEY", "").strip()
_key_prod = os.getenv("X_API_KEY_Prod", "").strip()
default_token = _key_dev if 'dev' in environment.lower() else _key_prod

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Workflow cache {thread_id: workflow_instance}
workflow_cache = {}


async def get_workflow(api_key: str, thread_id: str) -> ReputationWorkflow:
    """Get or create workflow instance."""
    cache_key = f"{api_key}_{thread_id}"
    if cache_key not in workflow_cache:
        wf = ReputationWorkflow(API_Token=api_key, environment=environment, thread_id=thread_id)
        await wf.initialize()
        workflow_cache[cache_key] = wf
    return workflow_cache[cache_key]


def create_thread_id(api_key: str) -> str:
    """Create a unique thread ID."""
    return f"rep_{uuid.uuid4().hex[:12]}"


@router.post("/analyze_stream")
@limiter.limit("5/minute")
async def reputation_analyze_stream(
    request: Request,
    api_key: str = Header(default=None, alias="x-api-key"),
    thread_id: str = Form(default=None),
    raw_text: str = Form(default=None),
    file: UploadFile = File(default=None),
):
    """
    **Reputation Intelligence — Streaming Analyse-Endpoint (SSE)**.

    Nimmt Presseclipping-Daten entgegen (Text oder Datei-Upload) und streamt
    den Analyse-Fortschritt via Server-Sent Events.

    - **raw_text**: Roher Artikeltext oder CSV-Inhalt (als Form-Feld)
    - **file**: CSV/TXT/PDF-Datei mit Presseclippings (als Datei-Upload)
    - **thread_id**: Optional — für State-Tracking

    Sendet Fortschritts-Events (`type: thinking`) und am Ende das
    fertige HTML-Dashboard als `type: result`.
    """
    user_api_key = api_key if api_key else default_token

    if not thread_id:
        thread_id = create_thread_id(user_api_key)

    # Read input content
    input_content = ""
    filename = None
    if file and file.filename:
        raw_bytes = await file.read()
        filename = file.filename
        filename_lower = file.filename.lower()

        if filename_lower.endswith(".pdf"):
            # Extract text from PDF
            try:
                import io
                from pypdf import PdfReader

                reader = PdfReader(io.BytesIO(raw_bytes))
                pages_text = [page.extract_text() for page in reader.pages if page.extract_text()]
                input_content = "\n\n".join(pages_text)
                get_logger().info(f"PDF '{file.filename}' extracted ({len(input_content)} chars, {len(reader.pages)} pages)")
            except Exception as pdf_err:
                get_logger().error(f"PDF extraction failed: {pdf_err}")
                raise HTTPException(status_code=400, detail=f"PDF konnte nicht gelesen werden: {pdf_err}")
        else:
            try:
                input_content = raw_bytes.decode("utf-8")
            except UnicodeDecodeError:
                input_content = raw_bytes.decode("latin-1")
            get_logger().info(f"File upload '{file.filename}' ({len(input_content)} chars)")
    elif raw_text:
        input_content = raw_text
        get_logger().info(f"Raw text input ({len(input_content)} chars)")
    else:
        raise HTTPException(status_code=400, detail="Provide either 'raw_text' or a 'file' upload.")

    # Get/create workflow
    wf = await get_workflow(user_api_key, thread_id)

    log_queue: asyncio.Queue = asyncio.Queue()

    async def log_callback(msg: dict):
        await log_queue.put(msg)

    async def event_generator():
        workflow_task = asyncio.create_task(
            wf.ask(
                input_content,
                log_callback=log_callback,
                source_files=[filename] if filename else [],
                created_by=user_api_key[:20],
            )
        )
        while True:
            if workflow_task.done() and log_queue.empty():
                break
            try:
                log = await asyncio.wait_for(log_queue.get(), timeout=0.1)
                yield f"data: {json.dumps(log, ensure_ascii=False)}\n\n"
            except asyncio.TimeoutError:
                continue

        # Retrieve result
        try:
            html_output, _, report_id = workflow_task.result()
        except Exception as exc:
            get_logger().error(f"Reputation workflow error: {exc}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"
            return

        final = json.dumps(
            {"type": "result", "html": html_output, "report_id": report_id, "thread_id": thread_id}, ensure_ascii=False
        )
        yield f"data: {final}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/compare_stream")
@limiter.limit("5/minute")
async def reputation_compare_stream(
    request: Request,
    api_key: str = Header(default=None, alias="x-api-key"),
    report_id_a: str = Form(..., description="ID des aktuellen Monats-Reports"),
    report_id_b: str = Form(..., description="ID des Vormonats-Reports"),
    thread_id: str = Form(default=None),
):
    """**MoM Vergleich (SSE)** — Vergleicht zwei gespeicherte Reports und streamt das Ergebnis."""
    user_api_key = api_key if api_key else API_SECRET_KEY
    if not thread_id:
        thread_id = create_thread_id(user_api_key)

    # Load both reports from DB
    db = SessionLocal()
    try:
        rep_a = db.query(ReputationReport).filter_by(report_id=report_id_a).first()
        rep_b = db.query(ReputationReport).filter_by(report_id=report_id_b).first()
        if not rep_a or not rep_b:
            raise HTTPException(status_code=404, detail="Einer oder beide Report-IDs nicht gefunden.")
        json_a = rep_a.report_json
        json_b = rep_b.report_json
    finally:
        db.close()

    wf = await get_workflow(user_api_key, thread_id)
    log_queue: asyncio.Queue = asyncio.Queue()

    async def log_callback(msg: dict):
        await log_queue.put(msg)

    async def event_generator():
        workflow_task = asyncio.create_task(wf.compare(json_a, json_b, log_callback=log_callback))
        while True:
            if workflow_task.done() and log_queue.empty():
                break
            try:
                log = await asyncio.wait_for(log_queue.get(), timeout=0.1)
                yield f"data: {json.dumps(log, ensure_ascii=False)}\n\n"
            except asyncio.TimeoutError:
                continue
        try:
            html_output, _ = workflow_task.result()
        except Exception as exc:
            yield f"data: {json.dumps({'type':'error','message':str(exc)})}\n\n"
            return
        yield f"data: {json.dumps({'type':'result','html':html_output,'thread_id':thread_id}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/chat_stream")
@limiter.limit("10/minute")
async def reputation_chat_stream(
    request: Request,
    api_key: str = Header(default=None, alias="x-api-key"),
    report_id: str = Form(..., description="ID des Reports für die Frage"),
    question: str = Form(..., description="Die Frage über den Report"),
    thread_id: str = Form(default=None),
):
    """**Chat über Report (SSE)** — Beantwortet eine Frage über einen gespeicherten Report."""
    user_api_key = api_key if api_key else API_SECRET_KEY
    if not thread_id:
        thread_id = create_thread_id(user_api_key)

    db = SessionLocal()
    try:
        rep = db.query(ReputationReport).filter_by(report_id=report_id).first()
        if not rep:
            raise HTTPException(status_code=404, detail="Report nicht gefunden.")
        report_json = rep.report_json
    finally:
        db.close()

    wf = await get_workflow(user_api_key, thread_id)
    log_queue: asyncio.Queue = asyncio.Queue()

    async def log_callback(msg: dict):
        await log_queue.put(msg)

    async def event_generator():
        workflow_task = asyncio.create_task(wf.chat_about(report_json, question, log_callback=log_callback))
        while True:
            if workflow_task.done() and log_queue.empty():
                break
            try:
                log = await asyncio.wait_for(log_queue.get(), timeout=0.1)
                yield f"data: {json.dumps(log, ensure_ascii=False)}\n\n"
            except asyncio.TimeoutError:
                continue
        try:
            answer, _ = workflow_task.result()
        except Exception as exc:
            yield f"data: {json.dumps({'type':'error','message':str(exc)})}\n\n"
            return
        yield f"data: {json.dumps({'type':'chat_result','answer':answer}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/reports")
async def reputation_list_reports(limit: int = 20):
    """Liste aller gespeicherten Reputation-Reports (neueste zuerst)."""
    db = SessionLocal()
    try:
        reports = (
            db.query(ReputationReport)
            .order_by(ReputationReport.created_at.desc())
            .limit(limit)
            .all()
        )
        return {"reports": [r.to_dict() for r in reports]}
    finally:
        db.close()


@router.get("/reports/{report_id}/html", response_class=HTMLResponse)
async def reputation_get_report_html(report_id: str):
    """Gibt das HTML-Dashboard eines gespeicherten Reports zurück."""
    db = SessionLocal()
    try:
        rep = db.query(ReputationReport).filter_by(report_id=report_id).first()
        if not rep:
            raise HTTPException(status_code=404, detail="Report nicht gefunden.")
        return HTMLResponse(content=rep.html_output)
    finally:
        db.close()


@router.delete("/reports/{report_id}")
async def reputation_delete_report(report_id: str):
    """Löscht einen gespeicherten Report."""
    db = SessionLocal()
    try:
        rep = db.query(ReputationReport).filter_by(report_id=report_id).first()
        if not rep:
            raise HTTPException(status_code=404, detail="Report nicht gefunden.")
        db.delete(rep)
        db.commit()
        return {"message": "Report gelöscht.", "report_id": report_id}
    finally:
        db.close()
