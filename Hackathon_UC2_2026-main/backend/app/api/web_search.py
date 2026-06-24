"""
Web Search API Endpoints for Competitive Intelligence
"""
import os
import json
import asyncio
from fastapi import APIRouter, Request, Header, Form, HTTPException
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..database import SessionLocal
from ..Omni_Helper.OmniAPI_helper import OmniAPI_Helper
from ..utils.logging_config import get_logger

router = APIRouter(prefix="/web_search", tags=["Web Search"])

# Configuration
environment = os.getenv("Environment", "dev")
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "dev_secret_key")

# Read token
_key_dev = os.getenv("X_API_KEY", "").strip()
_key_prod = os.getenv("X_API_KEY_Prod", "").strip()
default_token = _key_dev if 'dev' in environment.lower() else _key_prod

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Web search agent cache
web_search_agents = {}


async def get_web_search_agent(api_key: str) -> object:
    """Get or create web search agent instance."""
    cache_key = f"web_search_{api_key}"
    if cache_key not in web_search_agents:
        omni_helper = OmniAPI_Helper(
            conversation_token=api_key,
            semantic_token=None,
            environment=environment
        )
        # Create agent with web search capability (tools parameter enables web_search_preview)
        agent = omni_helper.create_assistant(
            engine="gemini-2.0-flash",
            system_text="""
Du bist der Competitive Intelligence & Web Search Assistent für OMG Germany.

## Deine Aufgabe:
Führe relevante Web-Suchen durch, um aktuelle Informationen zu finden.

## Dein Verhalten:
- Antworte auf Deutsch (außer die Frage ist auf Englisch)
- Nutze Web Search für aktuelle Informationen
- Gib immer die verwendeten URLs in deiner Antwort an
- Strukturiere Ergebnisse in Markdown (Headlines, Listen)
- Beziehe dich auf Datum und Quelle
""",
            temperature=0.3,
            tools=[{"type": "web_search_preview"}]
        )
        web_search_agents[cache_key] = agent
    return web_search_agents[cache_key]


@router.post("/competitive_intel_stream")
@limiter.limit("15/minute")
async def web_search_competitive_intel(
    request: Request,
    api_key: str = Header(default=None, alias="x-api-key"),
    query: str = Form(..., description="Competitive intelligence search query"),
):
    """
    **Web Search for Competitive Intelligence (SSE)**.

    Führe eine Web-Suche zu Wettbewerbern, Markttrends oder spezifischen Themen durch.

    - **query**: Such-Query (z.B. "Publicis Marktposition 2026", "Omnicom Übernahmen")

    Sendet Fortschritts-Events und das Ergebnis mit URLs via Server-Sent Events.
    """
    user_api_key = api_key if api_key else default_token

    if not user_api_key:
        raise HTTPException(status_code=401, detail="API Key erforderlich")

    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query ist erforderlich")

    get_logger().info(f"Web search query: {query}")

    log_queue: asyncio.Queue = asyncio.Queue()

    async def log_callback(msg: dict):
        await log_queue.put(msg)

    async def event_generator():
        try:
            agent = await get_web_search_agent(user_api_key)
            
            # Send thinking event
            await log_queue.put({
                "type": "thinking",
                "step_id": 1,
                "loading": "Durchsuche Web nach: " + query,
                "content": ""
            })

            # Execute web search with explicit URL request
            search_prompt = f"""
Führe eine Web-Suche durch für: {query}

Wichtig: Gib in deiner Antwort immer die verwendeten URL-Quellen an.
Formatiere die Antwort in Markdown mit klaren Headlines und Listen.
"""
            result = agent.ask(search_prompt)

            # Send completion
            await log_queue.put({
                "type": "thinking",
                "step_id": 1,
                "loading": "",
                "content": "Web-Suche abgeschlossen",
                "finished": True
            })

            # Stream result
            yield f"data: {json.dumps({'type':'result','content':result}, ensure_ascii=False)}\n\n"

        except Exception as e:
            get_logger().error(f"Web search error: {e}")
            yield f"data: {json.dumps({'type':'error','message':str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/competitor_tracker_stream")
@limiter.limit("10/minute")
async def web_search_competitor_tracker(
    request: Request,
    api_key: str = Header(default=None, alias="x-api-key"),
    competitor: str = Form(..., description="Competitor name"),
    topic: str = Form(default="", description="Optional topic filter"),
):
    """
    **Competitor Activity Tracking (SSE)**.

    Überwache aktuelle Aktivitäten eines spezifischen Competitors.

    - **competitor**: Name des Competitors (z.B. "Publicis", "Havas")
    - **topic**: Optional - spezifisches Thema (z.B. "Übernahmen", "Kampagnen")
    """
    user_api_key = api_key if api_key else default_token

    if not user_api_key:
        raise HTTPException(status_code=401, detail="API Key erforderlich")

    if not competitor or not competitor.strip():
        raise HTTPException(status_code=400, detail="Competitor name erforderlich")

    query_text = f"{competitor} Neuigkeiten 2026"
    if topic:
        query_text = f"{competitor} {topic} 2026"

    get_logger().info(f"Competitor tracker: {query_text}")

    log_queue: asyncio.Queue = asyncio.Queue()

    async def log_callback(msg: dict):
        await log_queue.put(msg)

    async def event_generator():
        try:
            agent = await get_web_search_agent(user_api_key)

            await log_queue.put({
                "type": "thinking",
                "step_id": 1,
                "loading": f"Tracker: {competitor}",
                "content": ""
            })

            search_prompt = f"""
Suche nach aktuellen Nachrichten und Entwicklungen über: {query_text}

Fokussiere auf:
- Pressemitteilungen
- Geschäftstransaktionen
- Personelle Veränderungen
- Neue Partnerschaften
- Strategische Ankündigungen

Gib alle relevanten URLs an. Strukturiere nach Datum (neueste zuerst).
"""
            result = agent.ask(search_prompt)

            await log_queue.put({
                "type": "thinking",
                "step_id": 1,
                "loading": "",
                "content": "Tracker abgeschlossen",
                "finished": True
            })

            yield f"data: {json.dumps({'type':'result','content':result,'competitor':competitor}, ensure_ascii=False)}\n\n"

        except Exception as e:
            get_logger().error(f"Competitor tracker error: {e}")
            yield f"data: {json.dumps({'type':'error','message':str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
