"""Layout Director agent — CrewAI agent for ambiguous paragraph layout decisions."""

from __future__ import annotations

from app.agents.prompts import DIRECTOR_SYSTEM_PROMPT, build_director_prompt
from app.llm.provider import LLMProvider
from app.schemas.inputs import NormalizedParagraph
from app.schemas.internals import ContinuityHint, LLMResponse
from app.schemas.outputs import DecisionOutput
from app.utils.errors import LLMError
from app.utils.logger import logger


class LayoutDirector:
    """Decides layout for paragraphs that don't match any rule."""

    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def decide(
        self,
        paragraph: NormalizedParagraph,
        previous_decisions: list[dict],
        continuity_hint: ContinuityHint,
    ) -> tuple[LLMResponse, int, int]:
        """Ask the LLM to decide the layout for an ambiguous paragraph.

        Returns:
            (LLMResponse, prompt_tokens, completion_tokens)

        Raises:
            LLMError if the LLM call fails after all retries.
        """
        # Build context
        keywords = [kw.word for kw in paragraph.keywords]
        assets = [
            {"type": a.type, "name": a.name, "description": a.description}
            for a in paragraph.assets
        ]
        hint_dict = continuity_hint.model_dump() if continuity_hint else {}

        user_prompt = build_director_prompt(
            paragraph_text=paragraph.text,
            keywords=keywords,
            assets=assets,
            previous_decisions=previous_decisions,
            continuity_hint=hint_dict,
        )

        logger.info("Calling LLM Director for paragraph '%s'", paragraph.id)

        raw_text, prompt_tokens, completion_tokens = self.llm.call(
            system_prompt=DIRECTOR_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        parsed = self.llm.parse_json_response(raw_text)
        response = _parse_llm_response(parsed)

        logger.info(
            "Director decided: mode=%s, confidence=%.2f for paragraph '%s'",
            response.layout_mode, response.confidence, paragraph.id,
        )

        return response, prompt_tokens, completion_tokens


def _parse_llm_response(data: dict) -> LLMResponse:
    """Parse the LLM's JSON response into an LLMResponse, with safe defaults."""
    from app.schemas.enums import LayoutMode

    # Get layout mode with fallback
    mode_str = data.get("layout_mode", "split_50_50")
    try:
        layout_mode = LayoutMode(mode_str)
    except ValueError:
        logger.warning("Invalid layout mode from LLM: '%s', using split_50_50", mode_str)
        layout_mode = LayoutMode.SPLIT_50_50

    return LLMResponse(
        layout_mode=layout_mode,
        description=data.get("description", ""),
        instructor_visible=data.get("instructor_visible", True),
        instructor_position=data.get("instructor_position", "center"),
        instructor_size=data.get("instructor_size", "full"),
        instructor_style=data.get("instructor_style", "normal"),
        board_visible=data.get("board_visible", True),
        board_position=data.get("board_position", "left"),
        board_size=data.get("board_size", "large"),
        assets=data.get("assets", []),
        transition_type=data.get("transition_type", "fade"),
        transition_duration_ms=data.get("transition_duration_ms", 400),
        transition_instruction=data.get("transition_instruction", ""),
        script_visibility_ratio=data.get("script_visibility_ratio", 0.5),
        script_visibility_reasoning=data.get("script_visibility_reasoning", ""),
        keywords_to_highlight=data.get("keywords_to_highlight", []),
        continuity_pin=data.get("continuity_pin", False),
        continuity_note=data.get("continuity_note", ""),
        director_note=data.get("director_note", ""),
        confidence=data.get("confidence", 0.5),
    )
