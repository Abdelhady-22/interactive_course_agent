"""Output schemas — the final JSON structure consumed by the frontend."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional

from app.schemas.enums import LayoutMode, TransitionType, DecisionSource


# ─────────────────────────────────────────────
# Position system — exact percentages
# ─────────────────────────────────────────────

class PositionRect(BaseModel):
    """Exact position of any element on screen, as percentages of viewport.

    Frontend usage:
        position: absolute;
        left: {x_percent}%;
        top: {y_percent}%;
        width: {width_percent}%;
        height: {height_percent}%;
        z-index: {z_index};
    """
    x_percent: float = Field(default=0, description="Left edge, 0-100% of viewport width")
    y_percent: float = Field(default=0, description="Top edge, 0-100% of viewport height")
    width_percent: float = Field(default=0, description="Element width as % of viewport")
    height_percent: float = Field(default=0, description="Element height as % of viewport")
    z_index: int = Field(default=1, description="Stacking order (higher = in front)")
    anchor: str = Field(default="center", description="Human-friendly reference label")


# ─────────────────────────────────────────────
# Layout sub-components
# ─────────────────────────────────────────────

class InstructorLayout(BaseModel):
    """Instructor camera position and style."""
    visible: bool = True
    position_rect: PositionRect = PositionRect(
        x_percent=0, y_percent=0, width_percent=100, height_percent=100,
        z_index=1, anchor="center",
    )
    size: str = "full"
    style: str = "normal"
    opacity: float = Field(default=1.0, ge=0.0, le=1.0)


class BoardLayout(BaseModel):
    """Board/content area position."""
    visible: bool = True
    position_rect: PositionRect = PositionRect(
        x_percent=0, y_percent=0, width_percent=100, height_percent=100,
        z_index=1, anchor="center",
    )


class LayoutOutput(BaseModel):
    """Complete layout specification for a paragraph."""
    mode: LayoutMode
    description: str = ""
    instructor: InstructorLayout = InstructorLayout()
    board: BoardLayout = BoardLayout()


# ─────────────────────────────────────────────
# Assets, keywords, script text
# ─────────────────────────────────────────────

class AssetOutput(BaseModel):
    """An asset placed on the board with exact position."""
    id: str
    type: str
    name: str = ""
    position_rect: PositionRect
    size: str = "medium"
    display_instruction: str = ""
    appear_at_ms: int = 0
    disappear_at_ms: int = 0


class KeywordBadge(BaseModel):
    """A keyword badge positioned on screen."""
    word: str
    type: str = "main"
    position_rect: PositionRect
    appear_at_ms: int = 0
    disappear_at_ms: int = 0
    style: str = "badge"


class ScriptText(BaseModel):
    """The paragraph script text area."""
    position_rect: PositionRect
    visibility_ratio: float = Field(default=0.5, ge=0.0, le=1.0)
    reasoning: str = ""
    keywords_to_highlight: list[str] = []


# ─────────────────────────────────────────────
# Transition + Continuity
# ─────────────────────────────────────────────

class TransitionOutput(BaseModel):
    """Transition effect between paragraphs."""
    type: TransitionType = TransitionType.FADE
    duration_ms: int = 400
    instruction: str = ""


class ContinuityOutput(BaseModel):
    """Cross-paragraph continuity information."""
    pin_instructor: bool = False
    pin_from_paragraph: Optional[str] = None
    transition_instructor: bool = True
    sequence_position: str = "standalone"
    sequence_length: int = 0
    sequence_note: str = ""


# ─────────────────────────────────────────────
# Token usage
# ─────────────────────────────────────────────

class TokenUsage(BaseModel):
    """Token usage for a single decision."""
    prompt_tokens: int = 0
    completion_tokens: int = 0


# ─────────────────────────────────────────────
# Decision — one per paragraph
# ─────────────────────────────────────────────

class DecisionOutput(BaseModel):
    """Complete layout decision for a single paragraph."""
    id: str
    paragraph_id: str
    paragraph_index: int = 0
    time_range: dict = Field(default_factory=lambda: {"start_ms": 0, "end_ms": 0})

    layout: LayoutOutput
    assets: list[AssetOutput] = []
    keyword_badges: list[KeywordBadge] = []
    script_text: Optional[ScriptText] = None
    transition: TransitionOutput = TransitionOutput()
    continuity: ContinuityOutput = ContinuityOutput()

    director_note: str = ""
    confidence: float = 0.5
    decided_by: DecisionSource = DecisionSource.RULE
    reviewed_by_llm: bool = False
    llm_agreed: Optional[bool] = None
    is_approved: bool = False
    token_usage: TokenUsage = TokenUsage()


# ─────────────────────────────────────────────
# Playback JSON — the final output
# ─────────────────────────────────────────────

class ProcessingStats(BaseModel):
    """Statistics about the processing run."""
    decided_by_rule: int = 0
    decided_by_llm: int = 0
    decided_by_fallback: int = 0
    rule_reviewed_by_llm: int = 0
    llm_overrode_rule: int = 0
    tokens: TokenUsage = TokenUsage()
    processing_time_ms: int = 0


class PlaybackJSON(BaseModel):
    """The complete output — consumed by the frontend video player."""
    course_id: str
    title: str = ""
    total_paragraphs: int = 0
    stats: ProcessingStats = ProcessingStats()
    decisions: list[DecisionOutput] = []
