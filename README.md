# Interactive Course Agent

AI-powered layout direction for educational video courses. Takes course transcript JSON as input and produces richly-detailed layout decisions with exact percentage-based positions for every visual element.

## Features

- **Hybrid Decision Engine**: 6 deterministic rules + CrewAI LLM agents for ambiguous cases
- **14 Layout Modes**: instructor_only, board_dominant, split_50_50, multi_asset_grid, and more
- **Precise Positioning**: Every element gets a `position_rect` with exact `x%, y%, width%, height%` values — maps directly to CSS
- **Multi-Provider LLM**: Ollama Cloud (default), Groq, OpenAI, Anthropic, Cohere via LiteLLM
- **LLM Review**: Low-confidence rule decisions (< 0.85) get reviewed by an LLM agent
- **User Control**: Force specific paragraphs through LLM with `force_llm_paragraphs`
- **Continuity Engine**: Detects consecutive asset sequences and pins the instructor for visual stability
- **Resolution Independent**: All positions are percentages (0-100%), works on any screen size

## Quick Start

See [QUICKSTART.md](QUICKSTART.md) for full setup instructions, API reference, and curl examples.

```bash
# Install
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your OLLAMA_API_KEY

# Run
uvicorn app.main:app --reload --port 8000

# Test
curl http://localhost:8000/api/health
```

## Architecture

```
Input JSON ──► Ingestion ──► Sequence Analyzer ──►┐
                                                   │
              ┌────────────────────────────────────┘
              │
         For each paragraph:
              │
              ├── Rule Engine (6 rules)
              │   ├── confidence ≥ 0.85 → use rule
              │   ├── confidence < 0.85 → LLM review
              │   └── no match → LLM director
              │
              ├── Position Calculator (exact %)
              ├── Board Layout (assets, keywords, script)
              │
              ▼
         Output Builder ──► PlaybackJSON
```

## Project Structure

```
app/
├── routers/         # FastAPI endpoints
├── schemas/         # Pydantic models (input, output, internal)
├── services/        # Business logic (pipeline, rules, positions)
├── agents/          # CrewAI agents (director, reviewer)
├── llm/             # LiteLLM provider wrapper
└── utils/           # Logger, error codes
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Service health + LLM status |
| `POST` | `/api/process-transcript` | Process full transcript |
| `POST` | `/api/process-paragraph` | Re-process single paragraph |

## Docker

```bash
docker compose up --build
```

## CI/CD

Push to `main` → GitHub Actions builds and pushes Docker image to Docker Hub.

Required secrets: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`

## Tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

## License

Proprietary — internal company use only.
