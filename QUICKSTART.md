# QUICKSTART — Interactive Course Agent

## What This App Does

Takes a structured course transcript (JSON) → runs it through an AI-powered hybrid pipeline (Rule Engine + LLM) → outputs layout decisions with **exact percentage-based positions** for every visual element.

The output JSON tells a frontend video player exactly where to place the instructor, board, assets, keywords, and script text on screen — using `position_rect` values that map directly to CSS.

---

## 1. Setup

### Prerequisites
- Python 3.11+
- [Ollama Cloud](https://ollama.com) API key (free tier)

### Install

```bash
# Clone the repo
git clone <-repo-url>
cd interactive_course_agent

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configure

```bash
# Copy the example env file
cp .env.example .env

# Edit .env with your Ollama Cloud API key
# ── .env ──
LLM_PROVIDER=ollama
LLM_MODEL=glm-5:cloud
OLLAMA_API_KEY=your_key_here
```

---

## 2. Run Locally

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open http://localhost:8000/docs for Swagger UI.

---

## 3. Run with Docker

```bash
# Build and run
docker compose up --build

# Or just build the image
docker build -t interactive-course-agent .
docker run -p 8000:8000 --env-file .env interactive-course-agent
```

---

## 4. API Reference

### Health Check

```bash
curl http://localhost:8000/api/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "llm": {"reachable": true, "provider": "ollama", "model": "ollama/glm-5:cloud"},
  "settings": {"provider": "ollama", "model": "glm-5:cloud", "review_enabled": true, "review_threshold": 0.85}
}
```

---

### Process Full Transcript

```bash
curl -X POST http://localhost:8000/api/process-transcript \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": [
      {
        "startTime": 0, "endTime": 28.52, "id": 1,
        "text": "Welcome back! In this video we will learn about cement production.",
        "keywords": [{"word": "Cement production", "type": "main"}],
        "wordTimestamps": [{"word": "Welcome", "start": 0, "end": 0.5, "word_type": "text"}],
        "visual": {"type": "image", "src": "https://example.com/cement.jpg", "title": "Cement Plant", "alt": "Aerial view", "startTime": 0, "assist_image_id": "img-001"}
      }
    ],
    "force_llm_paragraphs": [],
    "review_rules": true
  }'
```

**Parameters:**
| Field | Type | Description |
|-------|------|-------------|
| `transcript` | array or object | The course transcript (auto-detects format) |
| `force_llm_paragraphs` | array | Paragraph IDs/indexes to force through LLM |
| `review_rules` | bool | Enable LLM review of low-confidence rule decisions |

---

### Re-Process Single Paragraph

```bash
curl -X POST http://localhost:8000/api/process-paragraph \
  -H "Content-Type: application/json" \
  -d '{
    "paragraph": {"id": "p_014", "start_ms": 142300, "end_ms": 158700, "text": "When acid reacts with zinc...", "keywords": ["acid", "zinc"]},
    "assets": [{"id": "a1", "type": "formula", "name": "equation", "description": "Zn + HCl reaction"}],
    "use_llm": true,
    "previous_decisions": []
  }'
```

---

### Force Specific Paragraphs to LLM

If you want paragraphs 1, 5, and 8 to skip rules and go directly to the LLM:

```bash
curl -X POST http://localhost:8000/api/process-transcript \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": [...],
    "force_llm_paragraphs": [1, 5, 8]
  }'
```

---

## 5. Input Formats

The API accepts **two formats** (auto-detected):

### Format A: Flat Array (production format)

```json
[
  {
    "startTime": 0, "endTime": 28.52, "id": 1,
    "text": "Paragraph text...",
    "keywords": [{"word": "keyword", "type": "main"}],
    "wordTimestamps": [{"word": "word", "start": 0, "end": 0.5, "word_type": "text"}],
    "visual": {"type": "image", "src": "url", "title": "Title", "alt": "Description", "startTime": 0, "assist_image_id": "uuid"}
  }
]
```

### Format B: Structured

```json
{
  "video_context": {"description": "Course description"},
  "paragraph": {"id": "p_014", "start_ms": 142300, "end_ms": 158700, "text": "...", "keywords": ["kw1", "kw2"]},
  "assets": [{"id": "a1", "type": "formula", "name": "equation", "description": "..."}]
}
```

---

## 6. Output JSON — Frontend Developer Guide

Every element in the output has a `position_rect` that maps directly to CSS:

```css
.element {
  position: absolute;
  left: {x_percent}%;
  top: {y_percent}%;
  width: {width_percent}%;
  height: {height_percent}%;
  z-index: {z_index};
}
```

### Output Structure

```json
{
  "course_id": "uuid",
  "title": "Course title",
  "total_paragraphs": 12,
  "stats": {
    "decided_by_rule": 8,
    "decided_by_llm": 4,
    "decided_by_fallback": 0,
    "rule_reviewed_by_llm": 2,
    "llm_overrode_rule": 1,
    "tokens": {"prompt_tokens": 12400, "completion_tokens": 3200},
    "processing_time_ms": 45200
  },
  "decisions": [
    {
      "id": "uuid",
      "paragraph_id": "1",
      "paragraph_index": 0,
      "time_range": {"start_ms": 0, "end_ms": 28520},

      "layout": {
        "mode": "board_dominant",
        "description": "Board 70% left, instructor PiP bottom-right",
        "instructor": {
          "visible": true,
          "position_rect": {"x_percent": 72, "y_percent": 72, "width_percent": 25, "height_percent": 25, "z_index": 10, "anchor": "bottom_right"},
          "size": "small", "style": "pip", "opacity": 1.0
        },
        "board": {
          "visible": true,
          "position_rect": {"x_percent": 0, "y_percent": 0, "width_percent": 70, "height_percent": 100, "z_index": 1, "anchor": "left"}
        }
      },

      "assets": [{
        "id": "img-001", "type": "image", "name": "Cement Plant",
        "position_rect": {"x_percent": 3, "y_percent": 3, "width_percent": 64, "height_percent": 65, "z_index": 5, "anchor": "board_center"},
        "display_instruction": "Show Image 'Cement Plant' prominently on the board.",
        "appear_at_ms": 0, "disappear_at_ms": 28520
      }],

      "keyword_badges": [{
        "word": "Cement production", "type": "main",
        "position_rect": {"x_percent": 2, "y_percent": 2, "width_percent": 15, "height_percent": 4, "z_index": 8, "anchor": "board_top"},
        "appear_at_ms": 0, "disappear_at_ms": 28520, "style": "badge"
      }],

      "script_text": {
        "position_rect": {"x_percent": 3, "y_percent": 82.5, "width_percent": 64, "height_percent": 13.5, "z_index": 12, "anchor": "board_bottom"},
        "visibility_ratio": 0.3,
        "reasoning": "Visual assets are the primary focus. Show key phrases only.",
        "keywords_to_highlight": ["Cement production", "main stages"]
      },

      "transition": {"type": "fade", "duration_ms": 400, "instruction": "Opening fade in."},
      "continuity": {"pin_instructor": false, "sequence_position": "start", "sequence_length": 2},
      "director_note": "Greeting with assets — instructor dominant...",
      "confidence": 0.78,
      "decided_by": "rule",
      "reviewed_by_llm": false,
      "is_approved": false,
      "token_usage": {"prompt_tokens": 0, "completion_tokens": 0}
    }
  ]
}
```

### Key Fields for Frontend

| Field | What It Tells You |
|-------|-------------------|
| `layout.mode` | One of 14 layout modes (see below) |
| `layout.instructor.position_rect` | Where to place the instructor camera |
| `layout.board.position_rect` | Where the content board sits |
| `assets[].position_rect` | Where each asset goes on the board |
| `assets[].appear_at_ms / disappear_at_ms` | When to show/hide each asset |
| `keyword_badges[].position_rect` | Where keyword badges appear |
| `keyword_badges[].appear_at_ms` | When to show each keyword |
| `script_text.position_rect` | Where the transcript text sits |
| `script_text.visibility_ratio` | How much text to show (0.0=hidden, 1.0=full) |
| `transition.type` | How to animate between paragraphs |
| `continuity.pin_instructor` | Whether instructor stays in same position |

### The 14 Layout Modes

| Mode | Instructor | Board |
|------|-----------|-------|
| `instructor_only` | 100% full screen | hidden |
| `board_only` | hidden | 100% full screen |
| `board_dominant` | 25% PiP bottom-right | 70% left |
| `instructor_dominant` | 70% left | 25% overlay top-right |
| `split_50_50` | 50% right | 50% left |
| `split_60_40` | 40% right | 60% left |
| `instructor_pip` | 15% PiP bottom-right | 100% |
| `picture_in_picture_large` | 30% PiP bottom-right | 100% |
| `instructor_behind_board` | 100% (opacity 30%) | 100% on top |
| `overlay_floating` | 100% full screen | 30% floating top-right |
| `board_with_side_strip` | 25% strip right | 75% left |
| `multi_asset_grid` | 15% PiP bottom-right | 100% grid |
| `fullscreen_asset` | hidden | 100% full screen |
| `stacked_vertical` | 100% top half | 100% bottom half |

---

## 7. Switching LLM Provider

Edit `.env`:

```bash
# Ollama Cloud (default, free)
LLM_PROVIDER=ollama
LLM_MODEL=glm-5:cloud
OLLAMA_API_KEY=your_key

# Groq (fast, cheap)
LLM_PROVIDER=groq
LLM_MODEL=llama-3.1-70b-versatile
LLM_API_KEY=your_groq_key

# OpenAI (high quality)
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
LLM_API_KEY=your_openai_key

# Anthropic
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-sonnet-20240229
LLM_API_KEY=your_anthropic_key

# Cohere
LLM_PROVIDER=cohere
LLM_MODEL=command-r
LLM_API_KEY=your_cohere_key
```

Restart the server after changing providers.

---

## 8. Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `ollama` | LLM provider name |
| `LLM_MODEL` | `glm-5:cloud` | Model name |
| `OLLAMA_API_KEY` | | Ollama Cloud API key |
| `LLM_API_KEY` | | API key for other providers |
| `LLM_API_BASE` | | Custom API base URL |
| `LLM_TIMEOUT` | `120` | LLM call timeout (seconds) |
| `LLM_TEMPERATURE` | `0.3` | LLM temperature |
| `LLM_MAX_RETRIES` | `3` | Max retry attempts |
| `ENABLE_LLM_REVIEW` | `true` | Enable LLM review of rule decisions |
| `REVIEW_CONFIDENCE_THRESHOLD` | `0.85` | Rules below this confidence get reviewed |
| `APP_HOST` | `0.0.0.0` | Server host |
| `APP_PORT` | `8000` | Server port |
| `LOG_LEVEL` | `INFO` | Logging level |
| `CORS_ORIGINS` | `*` | Allowed CORS origins |

---

## 9. Run Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_rule_engine.py -v
```

---

## 10. Docker Hub CI/CD

On every push to `main`, the GitHub Actions workflow:
1. Builds the Docker image
2. Pushes to Docker Hub as `<username>/interactive-course-agent:latest`

**Required GitHub Secrets:**
- `DOCKERHUB_USERNAME` — your Docker Hub username
- `DOCKERHUB_TOKEN` — your Docker Hub access token ([create one here](https://hub.docker.com/settings/security))

To set secrets: Repo → Settings → Secrets and variables → Actions → New repository secret.
