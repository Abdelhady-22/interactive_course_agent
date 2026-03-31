"""Output schemas — the final JSON structure consumed by the frontend."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional

from app.schemas.enums import (
    LayoutMode, TransitionType, DecisionSource,
    PipShape, PipBorder, AnimationType,
    ScriptPosition, ScriptStyle, BoardBackground,
    InstructorEnergy, InstructorGesture, FocusTarget,
)


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
    """Instructor camera position, style, and PiP options."""
    visible: bool = True
    fullscreen: bool = Field(default=False, description="True if instructor is the background layer")
    position_rect: PositionRect = PositionRect(
        x_percent=0, y_percent=0, width_percent=100, height_percent=100,
        z_index=1, anchor="center",
    )
    size: str = "full"
    style: str = "normal"
    opacity: float = Field(default=1.0, ge=0.0, le=1.0)

    # PiP styling (V2)
    pip_shape: PipShape = Field(default=PipShape.ROUNDED_RECT, description="PiP overlay shape")
    pip_border: PipBorder = Field(default=PipBorder.THIN_WHITE, description="PiP border style")
    pip_shadow: bool = Field(default=True, description="Show drop shadow on PiP")
    entrance_animation: AnimationType = Field(default=AnimationType.FADE_IN, description="Entrance animation")


class BoardLayout(BaseModel):
    """Board/content area position and style."""
    visible: bool = True
    fullscreen: bool = Field(default=False, description="True if board is the background layer")
    position_rect: PositionRect = PositionRect(
        x_percent=0, y_percent=0, width_percent=100, height_percent=100,
        z_index=1, anchor="center",
    )

    # Board styling (V2)
    background: BoardBackground = Field(default=BoardBackground.DARK_GRADIENT, description="Board background style")
    border_radius: int = Field(default=12, description="Border radius in px")
    shadow: str = Field(default="medium", description="Shadow: none, small, medium, large")
    board_opacity: float = Field(default=0.95, ge=0.0, le=1.0)


class LayoutOutput(BaseModel):
    """Complete layout specification for a paragraph."""
    mode: LayoutMode
    description: str = ""
    instructor: InstructorLayout = InstructorLayout()
    board: BoardLayout = BoardLayout()


# ─────────────────────────────────────────────
# Assets with animations
# ─────────────────────────────────────────────

class AssetOutput(BaseModel):
    """An asset placed on the board with exact position and animation."""
    id: str
    type: str
    name: str = ""
    position_rect: PositionRect
    size: str = "medium"
    display_instruction: str = ""
    appear_at_ms: int = 0
    disappear_at_ms: int = 0

    # Animation (V2)
    entrance: AnimationType = Field(default=AnimationType.FADE_IN, description="Entrance animation")
    exit: AnimationType = Field(default=AnimationType.FADE_OUT, description="Exit animation")
    entrance_delay_ms: int = Field(default=0, description="Delay before entrance animation starts")
    entrance_duration_ms: int = Field(default=400, description="Duration of entrance animation")


class KeywordBadge(BaseModel):
    """A keyword badge positioned on screen with animation."""
    word: str
    type: str = "main"
    position_rect: PositionRect
    appear_at_ms: int = 0
    disappear_at_ms: int = 0
    style: str = "badge"
    spoken_at_ms: int = Field(default=0, description="When this keyword is spoken in the video")
    highlight_in_script: bool = Field(default=True, description="Highlight this word in script text")

    # Animation (V2)
    entrance: AnimationType = Field(default=AnimationType.POP_IN, description="Entrance animation")
    entrance_delay_ms: int = Field(default=0, description="Delay before entrance")
    entrance_duration_ms: int = Field(default=300, description="Duration of entrance animation")


class ScriptText(BaseModel):
    """The paragraph script text area with display options."""
    show: bool = Field(default=True, description="Whether to show script text")
    full_text: str = Field(default="", description="The full script text for this paragraph")
    position: ScriptPosition = Field(default=ScriptPosition.BOTTOM, description="Where to display")
    script_style: ScriptStyle = Field(default=ScriptStyle.SUBTITLE, description="Display style")
    font_size: str = Field(default="medium", description="Font size: small, medium, large")
    background: str = Field(default="glassmorphism", description="Text background style")
    position_rect: PositionRect = PositionRect()
    keywords_to_highlight: list[str] = []


# ─────────────────────────────────────────────
# Instructor Behavior Hints (V2)
# ─────────────────────────────────────────────

class InstructorBehavior(BaseModel):
    """Suggested instructor behavior for this paragraph."""
    energy: InstructorEnergy = Field(default=InstructorEnergy.NEUTRAL, description="Energy level")
    gesture: InstructorGesture = Field(default=InstructorGesture.NONE, description="Suggested gesture")
    eye_contact: str = Field(default="camera", description="Where to look: camera, board, asset")
    movement: str = Field(default="still", description="Body movement: still, lean_forward, step_back")
    note: str = Field(default="", description="Human-readable behavior instruction")


# ─────────────────────────────────────────────
# Focus Zone (V2)
# ─────────────────────────────────────────────

class FocusZone(BaseModel):
    """Where the learner should focus attention."""
    primary: FocusTarget = Field(default=FocusTarget.INSTRUCTOR, description="Primary attention target")
    highlight_rect: Optional[PositionRect] = Field(default=None, description="Optional highlight area")
    dim_background: bool = Field(default=False, description="Dim areas outside focus zone")
    attention_cue: str = Field(default="none", description="Visual cue: none, arrow, glow, pulse")


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

    # V2 enhancements
    instructor_behavior: InstructorBehavior = Field(default_factory=InstructorBehavior)
    focus_zone: FocusZone = Field(default_factory=FocusZone)

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
