"""Internal schemas — used between services, never exposed in the API."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional

from app.schemas.enums import LayoutMode, SequencePosition
from app.schemas.outputs import PositionRect


class RuleResult(BaseModel):
    """Result from a single rule evaluation."""
    matched: bool = False
    rule_name: str = ""
    layout_mode: Optional[LayoutMode] = None
    confidence: float = 0.0
    reason: str = ""
    suggested_assets: list[str] = Field(default_factory=list, description="Asset IDs to display")


class ContinuityHint(BaseModel):
    """Cross-paragraph continuity hint produced by SequenceAnalyzer."""
    is_in_sequence: bool = False
    sequence_position: SequencePosition = SequencePosition.STANDALONE
    sequence_length: int = 0
    sequence_start_paragraph_id: Optional[str] = None
    pin_instructor: bool = False
    pin_position: PositionRect = PositionRect(
        x_percent=75, y_percent=73, width_percent=22, height_percent=22,
        z_index=10, anchor="bottom_right",
    )
    pin_size: str = "small"
    pin_style: str = "pip"


class LLMResponse(BaseModel):
    """Parsed response from the LLM agent."""
    layout_mode: LayoutMode = LayoutMode.SPLIT_50_50
    description: str = ""
    instructor_visible: bool = True
    instructor_position: str = "center"
    instructor_size: str = "full"
    instructor_style: str = "normal"
    board_visible: bool = True
    board_position: str = "left"
    board_size: str = "large"
    assets: list[dict] = Field(default_factory=list)
    transition_type: str = "fade"
    transition_duration_ms: int = 400
    transition_instruction: str = ""
    script_visibility_ratio: float = 0.5
    script_visibility_reasoning: str = ""
    keywords_to_highlight: list[str] = Field(default_factory=list)
    continuity_pin: bool = False
    continuity_note: str = ""
    director_note: str = ""
    confidence: float = 0.5


class ReviewResult(BaseModel):
    """Result from the LLM review agent."""
    approved: bool = True
    override: Optional[LLMResponse] = None
    review_note: str = ""


class SessionTokenUsage(BaseModel):
    """Aggregated token usage for an entire pipeline run."""
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    llm_calls: int = 0
    review_calls: int = 0

    def add(self, prompt_tokens: int, completion_tokens: int, is_review: bool = False) -> None:
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        if is_review:
            self.review_calls += 1
        else:
            self.llm_calls += 1
