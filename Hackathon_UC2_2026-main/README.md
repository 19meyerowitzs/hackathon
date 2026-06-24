## Technologie-Stack

| Layer | Technologie |
|-------|------------|
| **Frontend** | Standalone HTML/CSS/JavaScript |
| **Backend** | FastAPI, Python 3.11+, Pydantic |
| **AI/ML** | LangGraph, LangChain, Gemini 2.5 Flash |
| **Database** | PostgreSQL 15 |
| **Deployment** | Docker, Docker Compose |

## Schnellstart

### Voraussetzungen

- Docker & Docker Compose
- Python 3.11+ (für lokale Entwicklung)
- Google Cloud API Key (für Gemini AI)

### Mit Docker starten

```bash
# 1. Environment-Variablen konfigurieren
cp .env.example .env
# Bearbeiten Sie .env und fügen Sie Ihre Credentials hinzu

# 2. Starten Sie alle Services
docker-compose up -d

# 3. Öffnen Sie die Anwendung
# UI: http://localhost:8080
# API Docs: http://localhost:8000/docs
```

### Lokale Entwicklung

```bash
# Backend
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
# Öffnen Sie app/static/reputation_ui.html im Browser
```

## Konfiguration

Erstellen Sie eine `.env` Datei im Root-Verzeichnis:

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=reputation_db
DB_USER=postgres
DB_PASSWORD=your_password

# AI/ML
LITELLM_API_KEY=Hackathon_litellm_key


```

## API Endpoints

### Reputation Analysis

- `POST /reputation/analyze_stream` - Analyse-Stream (SSE)
- `POST /reputation/compare_stream` - Vergleichs-Stream (SSE)
- `POST /reputation/chat_stream` - Chat-Stream (SSE)
- `GET /reputation/reports` - Liste aller Reports
- `GET /reputation/reports/{id}/html` - HTML-Report abrufen
- `DELETE /reputation/reports/{id}` - Report löschen

### UI

- `GET /` - Reputation Intelligence UI

Vollständige API-Dokumentation: http://localhost:8000/docs

## Projekt-Struktur

```
reputation-app/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI App
│   │   ├── models.py                # SQLAlchemy Models
│   │   ├── database.py              # DB-Konfiguration
│   │   ├── workflows/               # LangGraph Workflows
│   │   │   └── reputation_workflow/
│   │   │       ├── reputation_workflow.py
│   │   │       ├── reputation_workflow_configs.py
│   │   │       ├── html_generator.py
│   │   │       ├── comparison_html_generator.py
│   │   │       └── agents/
│   │   │           ├── ingest_agent.py
│   │   │           ├── analysis_agent.py
│   │   │           ├── chat_agent.py
│   │   │           └── comparison_agent.py
│   │   ├── static/
│   │   │   └── reputation_ui.html   # Frontend UI
│   │   └── utils/
│   │       └── logging_config.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── docker-compose.yml
└── README.md
```

## Usage Examples

### Analyse-Modus

```bash
curl -X POST "http://localhost:8000/reputation/analyze_stream" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@presseclippings.csv"
```

### Vergleichs-Modus

```bash
curl -X POST "http://localhost:8000/reputation/compare_stream" \
  -H "Content-Type: multipart/form-data" \
  -F "report_id_a=uuid-current-month" \
  -F "report_id_b=uuid-previous-month"
```

### Chat-Modus

```bash
curl -X POST "http://localhost:8000/reputation/chat_stream" \
  -H "Content-Type: multipart/form-data" \
  -F "report_id=uuid" \
  -F "question=Was ist unser größtes Risiko?"
```

