"""
Configuration for the Reputation Intelligence Workflow.
"""
from .agents import IngestAgentConfig, AnalysisAgentConfig, ComparisonAgentConfig, ChatAgentConfig

config = {
    "workflow_name": "Reputation Intelligence Workflow",
    "description": "Analysiert Presseclippings und erstellt einen strategischen Reputation-Report im Cockpit-Format.",
    "nodes": {
        "ingest": {
            "engine": IngestAgentConfig.model,
            "temperature": IngestAgentConfig.temperature,
            "system_text": IngestAgentConfig.system_prompt,
            "clients": IngestAgentConfig.clients,
            "agent_name": IngestAgentConfig.name,
            "response_key": "parsed_articles",
            "description": "Parst Rohdaten (Text/CSV/PDF) in strukturierte Artikel-Objekte",
            "log_message": {
                "loading": IngestAgentConfig.log_message,
                "step_id": 1,
            },
        },
        "analysis": {
            "engine": AnalysisAgentConfig.model,
            "temperature": AnalysisAgentConfig.temperature,
            "system_text": AnalysisAgentConfig.system_prompt,
            "clients": AnalysisAgentConfig.clients,
            "agent_name": AnalysisAgentConfig.name,
            "response_key": "report_json",
            "description": "Erstellt die vollständige strategische Analyse und Report-JSON",
            "log_message": {
                "loading": AnalysisAgentConfig.log_message,
                "finished": "Analyse abgeschlossen",
                "step_id": 2,
            },
        },
        "comparison": {
            "engine": ComparisonAgentConfig.model,
            "temperature": ComparisonAgentConfig.temperature,
            "system_text": ComparisonAgentConfig.system_prompt,
            "clients": ComparisonAgentConfig.clients,
            "agent_name": ComparisonAgentConfig.name,
            "response_key": "comparison_json",
            "description": "Vergleicht zwei Monats-Reports und erstellt MoM-Analyse-JSON",
            "log_message": {
                "loading": ComparisonAgentConfig.log_message,
                "step_id": 1,
            },
        },
        "chat": {
            "engine": ChatAgentConfig.model,
            "temperature": ChatAgentConfig.temperature,
            "system_text": ChatAgentConfig.system_prompt,
            "clients": ChatAgentConfig.clients,
            "log_message": {
                "loading": ChatAgentConfig.log_message,
                "step_id": 1,
            },
        },
    },
}
