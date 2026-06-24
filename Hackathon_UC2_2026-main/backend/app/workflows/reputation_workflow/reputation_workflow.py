"""
Reputation Intelligence Workflow
Standalone LangGraph workflow for press clipping analysis.

Modes:
  "analyze" : raw_input → ingest → analysis → html → END
  "compare" : report_json_a + report_json_b → comparison → comparison_html → END
  "chat"    : report_json + question → chat_response → END
"""

import os
import json
import re
import asyncio
import uuid
from typing import Any, TypedDict, Callable, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel
from dotenv import load_dotenv

from ...utils.logging_config import get_logger
from ...Omni_Helper.OmniAPI_helper import OmniAPI_Helper
from .reputation_workflow_configs import config as workflow_config
from .html_generator import generate_html
from .comparison_html_generator import generate_comparison_html
from ...models import ReputationReport
from ...database import SessionLocal

load_dotenv()


# ── State ────────────────────────────────────────────────────
class State(TypedDict):
    # analyze mode
    raw_input: str
    parsed_articles: str
    report_json: str
    html_output: str
    report_id: str
    # compare mode
    report_json_a: str
    report_json_b: str
    comparison_json: str
    # chat mode
    question: str
    chat_response: str
    # routing
    mode: str


# ── Workflow ──────────────────────────────────────────────────
class ReputationWorkflow:
    """Reputation Intelligence Workflow."""

    def __init__(self, API_Token: str = None, environment: str = "dev", thread_id: str = None):
        self.thread_id = thread_id or f"reputation_{uuid.uuid4().hex[:8]}"
        self.API_Token = API_Token or os.getenv("X_API_KEY") or os.getenv("API_Token")
        self.environment = environment
        self.omni_helper = OmniAPI_Helper(
            conversation_token=self.API_Token,
            semantic_token=None,
            environment=self.environment,
        )
        self.base_config = workflow_config
        self.agents = {}
        self.router_workflow = None
        self.initialization = False

        get_logger().info(f"Creating {self.base_config.get('workflow_name', 'Reputation Workflow')}...")

    async def initialize(self):
        """Async initialization."""
        if self.initialization:
            return
        try:
            await self._create_nodes()
            await self._create_workflow()
            self.initialization = True
            get_logger().info("Reputation Workflow initialized successfully.")
        except Exception as e:
            self.initialization = False
            get_logger().error(f"Reputation Workflow initialization error: {e}")
            raise

    async def _create_nodes(self):
        """Create LLM agents for each node using OmniAPI_Helper."""
        nodes_cfg = self.base_config.get("nodes", {})
        for node_name, cfg in nodes_cfg.items():
            self.agents[node_name] = self.omni_helper.create_chatbot(
                engine=cfg.get("engine", "gemini-2.5-flash-lite"),
                system_text=cfg.get("system_text", ""),
                temperature=cfg.get("temperature", 0.3),
            )
        get_logger().info(f"Reputation agents created: {list(self.agents.keys())}")

    async def _create_workflow(self):
        """Build the LangGraph workflow."""
        builder = StateGraph(State)

        # analyze path
        builder.add_node("ingest", self._ingest_node)
        builder.add_node("analysis", self._analysis_node)
        builder.add_node("html", self._html_node)

        # compare path
        builder.add_node("comparison", self._comparison_node)
        builder.add_node("comparison_html", self._comparison_html_node)

        # chat path
        builder.add_node("chat", self._chat_node)

        # router from START
        builder.add_conditional_edges(
            START,
            self._route_by_mode,
            {"ingest": "ingest", "comparison": "comparison", "chat": "chat"},
        )

        # analyze path
        builder.add_edge("ingest", "analysis")
        builder.add_edge("analysis", "html")
        builder.add_edge("html", END)

        # compare path
        builder.add_edge("comparison", "comparison_html")
        builder.add_edge("comparison_html", END)

        # chat path
        builder.add_edge("chat", END)

        self.router_workflow = builder.compile(checkpointer=InMemorySaver())

    # ── Router ───────────────────────────────────────────────
    @staticmethod
    def _route_by_mode(state: State) -> str:
        mode = state.get("mode", "analyze")
        if mode == "compare":
            return "comparison"
        if mode == "chat":
            return "chat"
        return "ingest"

    # ── Nodes ───────────────────────────────────────────────
    async def _ingest_node(self, state: State, config: RunnableConfig) -> dict[str, Any]:
        get_logger().info("*** Reputation: Ingest Node ***")
        log_callback = config.get("configurable", {}).get("log_callback")
        raw_input = state.get("raw_input", "")
        node_cfg = self.base_config["nodes"]["ingest"]

        if log_callback:
            await self._send_log(log_callback, step_id=1, loading=node_cfg["log_message"]["loading"], content="")

        prompt = f"Verarbeite folgende Presseclippings und gib strukturiertes JSON zurück:\n\n{raw_input}"
        result = self.agents["ingest"].ask(prompt)

        if log_callback:
            await self._send_log(log_callback, step_id=1, loading="", content="Artikel geparst", finished=True)

        return {"parsed_articles": result}

    async def _analysis_node(self, state: State, config: RunnableConfig) -> dict[str, Any]:
        get_logger().info("*** Reputation: Analysis Node ***")
        log_callback = config.get("configurable", {}).get("log_callback")
        parsed = state.get("parsed_articles", "")
        node_cfg = self.base_config["nodes"]["analysis"]

        if log_callback:
            await self._send_log(log_callback, step_id=2, loading=node_cfg["log_message"]["loading"], content="")

        prompt = (
            "Analysiere die folgenden geparsten Presseartikel und erstelle den vollständigen "
            f"Reputation Intelligence Report als JSON:\n\n{parsed}"
        )
        result = self.agents["analysis"].ask(prompt)

        if log_callback:
            await self._send_log(log_callback, step_id=2, loading="", content="Analyse abgeschlossen", finished=True)

        return {"report_json": result}

    async def _html_node(self, state: State, config: RunnableConfig) -> dict[str, Any]:
        get_logger().info("*** Reputation: HTML Node ***")
        log_callback = config.get("configurable", {}).get("log_callback")
        report_json_str = state.get("report_json", "")

        if log_callback:
            await self._send_log(log_callback, step_id=3, loading="Report-Dashboard wird gerendert...", content="")

        try:
            clean = re.sub(r"^```(?:json)?\s*", "", report_json_str.strip())
            clean = re.sub(r"\s*```$", "", clean)
            report_data = json.loads(clean)
        except Exception as e:
            get_logger().error(f"JSON parse error in html_node: {e}")
            report_data = {
                "meta": {"period": "Unbekannt", "company": "OMG Germany", "generated_at": "", "total_articles": 0},
                "northstar": {"score": 0, "delta": "0", "verdict": "Analyse fehlgeschlagen.", "components": []},
                "primary_kpis": [],
                "strategic_issues": [],
                "coverage_footprint": [],
                "sov_data": [],
                "sov_context": [],
                "topic_ownership": {},
                "speaker_race": [],
                "speed_events": [],
                "clusters": [],
                "momentum": [],
                "risks_matrix": {},
                "risk_register": [],
                "actions": {},
            }

        html = generate_html(report_data)

        # Persist to DB
        saved_id = None
        try:
            meta = report_data.get("meta", {})
            db = SessionLocal()
            report_id = str(uuid.uuid4())
            db_report = ReputationReport(
                report_id=report_id,
                period=meta.get("period", ""),
                company=meta.get("company", "OMG Germany"),
                source_files=", ".join(config.get("configurable", {}).get("source_files", [])),
                report_json=json.dumps(report_data, ensure_ascii=False),
                html_output=html,
                northstar_score=report_data.get("northstar", {}).get("score"),
                created_by=config.get("configurable", {}).get("created_by", "api")[:50],
            )
            db.add(db_report)
            db.commit()
            saved_id = report_id
            db.close()
            get_logger().info(f"Report saved to DB: {saved_id}")
        except Exception as e:
            get_logger().warning(f"DB save skipped: {e}")

        if log_callback:
            await self._send_log(log_callback, step_id=3, loading="", content="Dashboard fertig", finished=True)

        return {"html_output": html, "report_id": saved_id or ""}

    async def _comparison_node(self, state: State, config: RunnableConfig) -> dict[str, Any]:
        get_logger().info("*** Reputation: Comparison Node ***")
        log_callback = config.get("configurable", {}).get("log_callback")
        node_cfg = self.base_config["nodes"]["comparison"]

        if log_callback:
            await self._send_log(log_callback, step_id=1, loading=node_cfg["log_message"]["loading"], content="")

        prompt = (
            "Führe einen Month-over-Month Vergleich der folgenden zwei Reputation Intelligence Reports durch.\n\n"
            f"AKTUELLER MONAT:\n{state.get('report_json_a','')}\n\n"
            f"VORHERIGER MONAT:\n{state.get('report_json_b','')}"
        )
        result = self.agents["comparison"].ask(prompt)

        if log_callback:
            await self._send_log(log_callback, step_id=1, loading="", content="Vergleich abgeschlossen", finished=True)

        return {"comparison_json": result}

    async def _comparison_html_node(self, state: State, config: RunnableConfig) -> dict[str, Any]:
        get_logger().info("*** Reputation: Comparison HTML Node ***")
        log_callback = config.get("configurable", {}).get("log_callback")

        if log_callback:
            await self._send_log(log_callback, step_id=2, loading="Vergleichs-Dashboard wird gerendert...", content="")

        comparison_json_str = state.get("comparison_json", "")
        try:
            clean = re.sub(r"^```(?:json)?\s*", "", comparison_json_str.strip())
            clean = re.sub(r"\s*```$", "", clean)
            comparison_data = json.loads(clean)
        except Exception as e:
            get_logger().error(f"Comparison JSON parse error: {e}")
            comparison_data = {
                "meta": {},
                "executive_summary": "Fehler beim Parsen.",
                "northstar_comparison": {},
                "kpi_deltas": [],
                "new_strategic_issues": [],
                "resolved_issues": [],
                "sov_movement": [],
                "topic_ownership_changes": [],
                "risk_changes": {},
                "momentum_shifts": [],
                "action_completion": {},
                "key_wins": [],
                "key_risks_forward": [],
                "recommendations": [],
            }

        html = generate_comparison_html(comparison_data)

        if log_callback:
            await self._send_log(log_callback, step_id=2, loading="", content="Vergleichs-Dashboard fertig", finished=True)

        return {"html_output": html}

    async def _chat_node(self, state: State, config: RunnableConfig) -> dict[str, Any]:
        get_logger().info("*** Reputation: Chat Node ***")
        log_callback = config.get("configurable", {}).get("log_callback")
        node_cfg = self.base_config["nodes"]["chat"]

        if log_callback:
            await self._send_log(log_callback, step_id=1, loading=node_cfg["log_message"]["loading"], content="")

        prompt = f"Report-Kontext:\n{state.get('report_json','')}\n\nFrage: {state.get('question','')}"
        result = self.agents["chat"].ask(prompt)

        if log_callback:
            await self._send_log(log_callback, step_id=1, loading="", content="Antwort bereit", finished=True)

        return {"chat_response": result}

    # ── Public API ───────────────────────────────────────────
    async def ask(
        self, raw_input: str, log_callback: Callable = None, source_files: list = None, created_by: str = "api"
    ) -> tuple[str, dict, str]:
        """Analyze mode: ingest + analysis + html. Returns (html_output, token_usage, report_id)."""
        if not self.router_workflow:
            await self.initialize()

        if log_callback:
            await self._send_log(log_callback, step_id=0, loading="Reputation Intelligence Workflow gestartet", content="")

        response = await self.router_workflow.ainvoke(
            {
                "mode": "analyze",
                "raw_input": raw_input,
                "parsed_articles": "",
                "report_json": "",
                "html_output": "",
                "report_id": "",
                "report_json_a": "",
                "report_json_b": "",
                "comparison_json": "",
                "question": "",
                "chat_response": "",
            },
            config={
                "configurable": {
                    "thread_id": self.thread_id,
                    "log_callback": log_callback,
                    "source_files": source_files or [],
                    "created_by": created_by,
                }
            },
        )

        html_output = response.get("html_output", "")
        report_id = response.get("report_id", "")
        token_usage = {"model": "reputation_workflow", "total_tokens": 0}
        return html_output, token_usage, report_id

    async def compare(self, report_json_a: str, report_json_b: str, log_callback: Callable = None) -> tuple[str, dict]:
        """Compare mode: two report JSONs → MoM comparison HTML."""
        if not self.router_workflow:
            await self.initialize()

        if log_callback:
            await self._send_log(log_callback, step_id=0, loading="Monatsvergleich wird gestartet...", content="")

        response = await self.router_workflow.ainvoke(
            {
                "mode": "compare",
                "raw_input": "",
                "parsed_articles": "",
                "report_json": "",
                "html_output": "",
                "report_id": "",
                "report_json_a": report_json_a,
                "report_json_b": report_json_b,
                "comparison_json": "",
                "question": "",
                "chat_response": "",
            },
            config={"configurable": {"thread_id": self.thread_id + "_compare", "log_callback": log_callback}},
        )
        return response.get("html_output", ""), {"model": "comparison_workflow", "total_tokens": 0}

    async def chat_about(self, report_json: str, question: str, log_callback: Callable = None) -> tuple[str, dict]:
        """Chat mode: Q&A about a specific report. Returns (markdown_answer, token_usage)."""
        if not self.router_workflow:
            await self.initialize()

        response = await self.router_workflow.ainvoke(
            {
                "mode": "chat",
                "raw_input": "",
                "parsed_articles": "",
                "report_json": report_json,
                "html_output": "",
                "report_id": "",
                "report_json_a": "",
                "report_json_b": "",
                "comparison_json": "",
                "question": question,
                "chat_response": "",
            },
            config={"configurable": {"thread_id": self.thread_id + "_chat", "log_callback": log_callback}},
        )
        return response.get("chat_response", ""), {"model": "chat_workflow", "total_tokens": 0}

    # ── Helpers ──────────────────────────────────────────────
    @staticmethod
    async def _send_log(callback, step_id: int, loading: str, content: str, finished: bool = False):
        msg = {"type": "thinking", "step_id": step_id, "loading": loading, "content": content, "finished": finished}
        if asyncio.iscoroutinefunction(callback):
            await callback(msg)
        else:
            callback(msg)

    def set_thread_id(self, thread_id: str):
        self.thread_id = thread_id
