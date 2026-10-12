# LearnMate AI
An AI-powered study assistant that helps students learn from their study materials, previous-year question papers, and uploaded documents.

## Features
- AI Chat Assistant with RAG (document-based Q&A)
- Document Management (PDF, TXT, DOCX upload & processing)
- PYQ Analyzer (topic frequency, patterns, clustering)
- Quiz Generator (auto-generated MCQs)
- Study Planner (task management)
- Analytics Dashboard (charts & performance tracking)

## Tech Stack
- **Frontend:** HTML5, CSS3, JavaScript, Chart.js
- **Backend:** FastAPI, Python
- **AI/ML:** Groq LLM, LangChain, Sentence Transformers, FAISS, Scikit-learn
- **Database:** PostgreSQL, SQLAlchemy
- **Deployment:** Docker, Docker Compose

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL (or use Docker)
- Groq API key ([Get one free](https://console.groq.com/keys))

### 1. Clone & Setup
```bash
git clone <your-repo-url>
cd learnmate-ai
```

### 2. Configure Environment
```bash
cp .env.example .env
```

Edit `.env` and add your Groq API key:
```
GROQ_API_KEY=gsk_your_key_here
```

### 3. Setup Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Initialize Database
```bash
# If using PostgreSQL directly
psql -U postgres -c "CREATE DATABASE learnmate_db;"
psql -U postgres -c "CREATE USER learnmate WITH PASSWORD 'learnmate123';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE learnmate_db TO learnmate;"
```

### 5. Run the Application
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Open http://localhost:8000 in your browser.

## Docker Deployment
```bash
# Set your Groq API key
$env:GROQ_API_KEY="your_key_here"

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop
docker-compose down
```

## Project Structure
```
learnmate-ai/
├── backend/
│   ├── api/           # REST API endpoints
│   │   ├── health.py
│   │   ├── chat.py
│   │   ├── documents.py
│   │   ├── pyq.py
│   │   ├── quiz.py
│   │   ├── planner.py
│   │   └── analytics.py
│   ├── rag/           # Document processing & RAG
│   │   ├── embeddings.py
│   │   └── pipeline.py
│   ├── pyq_analyzer/  # PYQ analysis
│   │   └── analyzer.py
│   ├── ml/            # ML utilities
│   │   └── analytics.py
│   ├── services/      # Business logic
│   │   └── llm_service.py
│   ├── database/      # DB models & config
│   │   ├── config.py
│   │   └── models.py
│   ├── utils/         # Helpers
│   │   └── helpers.py
│   └── main.py        # FastAPI app entry
├── frontend/
│   ├── index.html
│   ├── css/styles.css
│   └── js/
│       ├── api.js
│       ├── app.js
│       ├── chat.js
│       ├── documents.js
│       ├── pyq.js
│       ├── quiz.js
│       ├── planner.js
│       └── analytics.js
├── docker/
│   ├── Dockerfile.backend
│   └── .env
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Health check |
| `/api/v1/chat/ask` | POST | Ask AI a question |
| `/api/v1/chat/history/{session_id}` | GET | Get chat history |
| `/api/v1/chat/clear` | POST | Clear chat history |
| `/api/v1/documents/` | GET | List documents |
| `/api/v1/documents/upload` | POST | Upload document |
| `/api/v1/documents/{id}` | DELETE | Delete document |
| `/api/v1/pyq/` | GET | List PYQ analyses |
| `/api/v1/pyq/upload` | POST | Upload & analyze PYQ |
| `/api/v1/quiz/generate` | POST | Generate quiz |
| `/api/v1/quiz/submit` | POST | Submit quiz answers |
| `/api/v1/quiz/history` | GET | Quiz attempt history |
| `/api/v1/planner/tasks` | GET/POST | List/create tasks |
| `/api/v1/planner/tasks/{id}` | PUT/DELETE | Update/delete task |
| `/api/v1/planner/summary` | GET | Planner summary |
| `/api/v1/analytics/dashboard` | GET | Dashboard analytics |

## Configuration
See `.env.example` for all configuration options:
- `GROQ_API_KEY` — Required for AI features
- `DATABASE_URL` — PostgreSQL connection string
- `UPLOAD_DIR` — Document storage directory
- `CHUNK_SIZE` / `CHUNK_OVERLAP` — RAG chunking parameters
- `EMBEDDING_MODEL` — Sentence transformer model
- `LLM_MODEL` — Groq model name

## License
MIT
