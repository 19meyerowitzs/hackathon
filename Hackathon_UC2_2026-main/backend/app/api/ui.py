"""
UI Serving API Endpoints
"""
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["UI"])


@router.get("/", response_class=HTMLResponse)
async def root():
    """Serve the Reputation UI."""
    ui_path = Path(__file__).parent.parent / "static" / "reputation_ui.html"
    if ui_path.exists():
        return HTMLResponse(content=ui_path.read_text(encoding="utf-8"))
    return HTMLResponse(
        content="<h1>Reputation Intelligence API</h1><p>Visit <a href='/docs'>/docs</a> for API documentation.</p>"
    )
