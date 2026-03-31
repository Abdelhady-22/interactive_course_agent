"""Shared test fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import Settings


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def settings():
    """Test settings with disabled LLM."""
    return Settings(
        llm_provider="ollama",
        llm_model="glm-5:cloud",
        enable_llm_review=False,
    )


@pytest.fixture
def flat_input_sample():
    """Small flat-array input sample (2 paragraphs)."""
    return [
        {
            "startTime": 0,
            "endTime": 28.52,
            "id": 1,
            "text": "Welcome back! In this video, our objective is to explain the main stages of cement clinker production.",
            "keywords": [
                {"word": "Cement production", "type": "main"},
                {"word": "main stages", "type": "Callouts"},
            ],
            "wordTimestamps": [
                {"word": "Welcome", "start": 0, "end": 0.5, "word_type": "text"},
                {"word": "back", "start": 0.5, "end": 1.0, "word_type": "text"},
            ],
            "visual": {
                "type": "image",
                "src": "https://example.com/cement.jpg",
                "title": "Industrial Cement Plant",
                "alt": "An aerial view of an industrial cement plant.",
                "startTime": 0,
                "assist_image_id": "img-001",
            },
        },
        {
            "startTime": 33.16,
            "endTime": 50.36,
            "id": 2,
            "text": "In our previous video, we identified the fundamental raw materials for cement: limestone as the primary source of calcium.",
            "keywords": [
                {"word": "fundamental raw materials", "type": "main"},
                {"word": "limestone", "type": "Key Terms"},
            ],
            "wordTimestamps": [
                {"word": "In", "start": 33.16, "end": 33.5, "word_type": "text"},
                {"word": "our", "start": 33.5, "end": 33.84, "word_type": "text"},
            ],
            "visual": {
                "type": "image",
                "src": "https://example.com/magnetite.jpg",
                "title": "Magnetite Rock Sample",
                "alt": "A dark gray rock sample of magnetite.",
                "startTime": 33,
                "assist_image_id": "img-002",
            },
        },
    ]


@pytest.fixture
def structured_input_sample():
    """Small structured input sample."""
    return {
        "video_context": {"description": "Educational chemistry course"},
        "paragraph": {
            "id": "p_014",
            "start_ms": 142300,
            "end_ms": 158700,
            "text": "When hydrochloric acid reacts with zinc it produces hydrogen gas...",
            "keywords": ["hydrochloric acid", "zinc", "hydrogen gas"],
        },
        "assets": [
            {
                "id": "asset_401",
                "type": "formula",
                "name": "reaction equation",
                "description": "balanced chemical equation",
                "content": "Zn + 2HCl → ZnCl₂ + H₂↑",
            },
        ],
    }
