"""Input schemas — supports both flat-array and structured input formats."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any


# ─────────────────────────────────────────────
# Format A: Flat array (example.json style)
# ─────────────────────────────────────────────

class WordTimestamp(BaseModel):
    """A single word with its timing in the video."""
    word: str = ""
    text: str = ""  # alternative field name in some inputs
    start: float = 0.0
    end: float = 0.0
    word_type: str = "text"
    id: str = ""
    segment_id: str = ""

    @property
    def resolved_word(self) -> str:
        return (self.word or self.text).strip()


class KeywordInput(BaseModel):
    """A keyword attached to a paragraph."""
    word: str
    type: str = "main"


class VisualInput(BaseModel):
    """A single visual asset embedded in a paragraph (flat format)."""
    type: str = "image"
    src: str = ""
    title: str = ""
    alt: str = ""
    startTime: float = 0.0
    assist_image_id: str = ""


class FlatParagraphInput(BaseModel):
    """One paragraph in the flat-array input format."""
    id: int | str
    startTime: float
    endTime: float
    text: str
    keywords: list[KeywordInput] = []
    wordTimestamps: list[WordTimestamp] = []
    visual: VisualInput | None = None


# ─────────────────────────────────────────────
# Format B: Structured (plan/input.json style)
# ─────────────────────────────────────────────

class VideoContextInput(BaseModel):
    """Course-level video context."""
    description: str = ""


class StructuredParagraphInput(BaseModel):
    """Paragraph in the structured input format."""
    id: str
    start_ms: int
    end_ms: int
    text: str
    keywords: list[str] = []


class AssetInput(BaseModel):
    """An asset in the structured input format."""
    id: str
    type: str = "image"
    name: str = ""
    description: str = ""
    content: str | None = None
    src: str = ""
    title: str = ""
    alt: str = ""
    startTime: float = 0.0
    assist_image_id: str = ""


class StructuredInput(BaseModel):
    """The structured input format (plan/input.json)."""
    video_context: VideoContextInput = VideoContextInput()
    paragraph: StructuredParagraphInput | None = None
    paragraphs: list[StructuredParagraphInput] = []
    assets: list[AssetInput] = []


# ─────────────────────────────────────────────
# Normalized internal representation
# ─────────────────────────────────────────────

class NormalizedAsset(BaseModel):
    """Unified asset representation used internally."""
    id: str
    type: str
    name: str = ""
    description: str = ""
    content: str | None = None
    src: str = ""

    model_config = {"extra": "ignore"}


class NormalizedKeyword(BaseModel):
    """Unified keyword representation."""
    word: str
    type: str = "main"


class NormalizedWordTimestamp(BaseModel):
    """Unified word timestamp."""
    word: str
    start_ms: int
    end_ms: int


class NormalizedParagraph(BaseModel):
    """Unified paragraph representation — all input formats normalize to this."""
    id: str
    index: int = 0
    start_ms: int
    end_ms: int
    text: str
    keywords: list[NormalizedKeyword] = []
    word_timestamps: list[NormalizedWordTimestamp] = []
    assets: list[NormalizedAsset] = []


class NormalizedTranscript(BaseModel):
    """The fully normalized transcript ready for the pipeline."""
    paragraphs: list[NormalizedParagraph]
    video_context: str = ""


# ─────────────────────────────────────────────
# API request model
# ─────────────────────────────────────────────

class ProcessTranscriptRequest(BaseModel):
    """Request body for POST /api/process-transcript."""
    transcript: list[dict[str, Any]] | dict[str, Any]
    force_llm_paragraphs: list[int | str] = Field(
        default=[],
        description="Paragraph IDs/indexes to force through LLM instead of rules",
    )
    review_rules: bool = Field(
        default=True,
        description="Enable LLM review of low-confidence rule decisions",
    )


class ProcessParagraphRequest(BaseModel):
    """Request body for POST /api/process-paragraph (re-process single paragraph)."""
    paragraph: dict[str, Any]
    assets: list[dict[str, Any]] = []
    video_context: str = ""
    previous_decisions: list[dict[str, Any]] = []
    use_llm: bool = Field(default=True, description="Force LLM decision for this paragraph")
