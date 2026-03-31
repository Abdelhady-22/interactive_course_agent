"""Pipeline service — main orchestrator: ingest → analyze → decide → output."""

from __future__ import annotations

import time
import uuid
from typing import Any

from app.config import Settings
from app.agents.director import LayoutDirector
from app.agents.reviewer import LayoutReviewer
from app.llm.provider import LLMProvider
from app.llm.token_tracker import TokenTracker
from app.schemas.enums import DecisionSource, LayoutMode, TransitionType
from app.schemas.inputs import NormalizedParagraph, NormalizedTranscript
from app.schemas.internals import ContinuityHint, LLMResponse, RuleResult
from app.schemas.outputs import (
    AssetOutput,
    ContinuityOutput,
    DecisionOutput,
    InstructorLayout,
    KeywordBadge,
    LayoutOutput,
    PlaybackJSON,
    PositionRect,
    ScriptText,
    TokenUsage,
    TransitionOutput,
)
from app.services.board_layout import compute_board_content
from app.services.ingestion import ingest_transcript
from app.services.output_builder import build_playback_json
from app.services.position_calculator import compute_layout_positions
from app.services.rule_engine import evaluate_rules
from app.services.sequence_analyzer import analyze_sequences
from app.utils.logger import logger


class Pipeline:
    """Orchestrates the full transcript processing pipeline."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm = LLMProvider(settings)
        self.director = LayoutDirector(self.llm)
        self.reviewer = LayoutReviewer(self.llm)
        self.tracker = TokenTracker()

    def process_transcript(
        self,
        raw_input: list[dict[str, Any]] | dict[str, Any],
        force_llm_paragraphs: list[int | str] | None = None,
        review_rules: bool = True,
    ) -> PlaybackJSON:
        """Process an entire transcript and return the PlaybackJSON.

        Args:
            raw_input: The raw JSON input (flat array or structured).
            force_llm_paragraphs: Paragraph IDs/indexes to force through LLM.
            review_rules: Whether to LLM-review low-confidence rule decisions.
        """
        start_time = time.time()
        self.tracker.reset()
        force_ids = set(str(x) for x in (force_llm_paragraphs or []))

        # ── Phase 1: Ingest ──
        logger.info("═══ Phase 1: Ingesting transcript ═══")
        transcript = ingest_transcript(raw_input)

        # ── Phase 2: Sequence Analysis ──
        logger.info("═══ Phase 2: Analyzing sequences ═══")
        hints = analyze_sequences(transcript.paragraphs)

        # ── Phase 3: Per-paragraph decisions ──
        logger.info("═══ Phase 3: Processing %d paragraphs ═══", len(transcript.paragraphs))
        decisions: list[DecisionOutput] = []
        previous_decision_context: list[dict] = []

        for i, paragraph in enumerate(transcript.paragraphs):
            hint = hints[i] if i < len(hints) else ContinuityHint()

            decision = self._process_paragraph(
                paragraph=paragraph,
                hint=hint,
                previous_decisions=previous_decision_context,
                force_llm=str(paragraph.id) in force_ids or str(paragraph.index) in force_ids,
                review_rules=review_rules and self.settings.enable_llm_review,
            )
            decisions.append(decision)

            # Track context for next paragraph (sliding window of last 3)
            previous_decision_context.append({
                "layout_mode": decision.layout.mode.value,
                "instructor_position": decision.layout.instructor.position_rect.anchor,
            })
            if len(previous_decision_context) > 3:
                previous_decision_context.pop(0)

        # ── Phase 4: Build output ──
        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.info("═══ Phase 4: Building output (%dms elapsed) ═══", elapsed_ms)

        # Extract title from first paragraph text (first 60 chars)
        title = ""
        if transcript.paragraphs:
            first_text = transcript.paragraphs[0].text
            title = first_text[:60].strip() + ("..." if len(first_text) > 60 else "")

        return build_playback_json(decisions=decisions, title=title, processing_time_ms=elapsed_ms)

    def process_single_paragraph(
        self,
        paragraph: NormalizedParagraph,
        previous_decisions: list[dict] | None = None,
        use_llm: bool = True,
    ) -> DecisionOutput:
        """Process a single paragraph (for re-processing)."""
        self.tracker.reset()
        hint = ContinuityHint()
        return self._process_paragraph(
            paragraph=paragraph,
            hint=hint,
            previous_decisions=previous_decisions or [],
            force_llm=use_llm,
            review_rules=False,
        )

    def _process_paragraph(
        self,
        paragraph: NormalizedParagraph,
        hint: ContinuityHint,
        previous_decisions: list[dict],
        force_llm: bool,
        review_rules: bool,
    ) -> DecisionOutput:
        """Process a single paragraph through the rule → LLM → fallback pipeline."""
        logger.info("── Processing paragraph '%s' (index=%d) ──", paragraph.id, paragraph.index)

        layout_mode: LayoutMode
        confidence: float
        decided_by: DecisionSource
        director_note: str
        reviewed_by_llm: bool = False
        llm_agreed: bool | None = None
        token_usage = TokenUsage()
        suggested_asset_ids: list[str] = []

        if force_llm:
            # User forced LLM for this paragraph
            logger.info("Paragraph '%s' forced to LLM by user", paragraph.id)
            layout_mode, confidence, director_note, suggested_asset_ids, token_usage = (
                self._call_director(paragraph, previous_decisions, hint)
            )
            decided_by = DecisionSource.LLM
        else:
            # Try rules first
            rule_result = evaluate_rules(paragraph)

            if rule_result.matched:
                layout_mode = rule_result.layout_mode
                confidence = rule_result.confidence
                director_note = rule_result.reason
                decided_by = DecisionSource.RULE
                suggested_asset_ids = rule_result.suggested_assets

                # Review low-confidence rule decisions
                if review_rules and confidence < self.settings.review_confidence_threshold:
                    reviewed_by_llm = True
                    review_result, p_tok, c_tok = self.reviewer.review(
                        paragraph, rule_result, previous_decisions,
                    )
                    token_usage = self.tracker.record(p_tok, c_tok, is_review=True)

                    if not review_result.approved and review_result.override:
                        # LLM overrides the rule
                        llm_agreed = False
                        override = review_result.override
                        layout_mode = override.layout_mode
                        confidence = override.confidence
                        director_note = f"[Rule overridden by reviewer] {override.director_note}"
                        decided_by = DecisionSource.LLM
                        logger.info("Reviewer overrode rule for paragraph '%s': %s → %s",
                                    paragraph.id, rule_result.layout_mode, layout_mode)
                    else:
                        llm_agreed = True
                        logger.info("Reviewer approved rule for paragraph '%s'", paragraph.id)
            else:
                # No rule matched — call the director LLM
                layout_mode, confidence, director_note, suggested_asset_ids, token_usage = (
                    self._call_director(paragraph, previous_decisions, hint)
                )
                decided_by = DecisionSource.LLM

        # ── Apply continuity enforcement ──
        instructor, board = compute_layout_positions(layout_mode)

        if hint.pin_instructor and hint.is_in_sequence:
            instructor.position_rect = hint.pin_position
            instructor.size = hint.pin_size
            instructor.style = hint.pin_style

        # ── Compute board content ──
        assets, keyword_badges, script_text = compute_board_content(
            paragraph, layout_mode, board.position_rect, suggested_asset_ids,
        )

        # ── Build transition ──
        transition = self._compute_transition(hint, paragraph.index == 0)

        # ── Build continuity output ──
        continuity = ContinuityOutput(
            pin_instructor=hint.pin_instructor,
            pin_from_paragraph=hint.sequence_start_paragraph_id,
            transition_instructor=not hint.pin_instructor or hint.sequence_position.value == "start",
            sequence_position=hint.sequence_position.value,
            sequence_length=hint.sequence_length,
            sequence_note=self._sequence_note(hint),
        )

        return DecisionOutput(
            id=str(uuid.uuid4()),
            paragraph_id=paragraph.id,
            paragraph_index=paragraph.index,
            time_range={"start_ms": paragraph.start_ms, "end_ms": paragraph.end_ms},
            layout=LayoutOutput(
                mode=layout_mode,
                description=director_note,
                instructor=instructor,
                board=board,
            ),
            assets=assets,
            keyword_badges=keyword_badges,
            script_text=script_text,
            transition=transition,
            continuity=continuity,
            director_note=director_note,
            confidence=confidence,
            decided_by=decided_by,
            reviewed_by_llm=reviewed_by_llm,
            llm_agreed=llm_agreed,
            is_approved=False,
            token_usage=token_usage,
        )

    def _call_director(
        self,
        paragraph: NormalizedParagraph,
        previous_decisions: list[dict],
        hint: ContinuityHint,
    ) -> tuple[LayoutMode, float, str, list[str], TokenUsage]:
        """Call the director agent, with fallback on failure."""
        try:
            response, p_tok, c_tok = self.director.decide(paragraph, previous_decisions, hint)
            token_usage = self.tracker.record(p_tok, c_tok)
            asset_ids = [a.get("id", "") for a in response.assets if a.get("id")]
            return response.layout_mode, response.confidence, response.director_note, asset_ids, token_usage

        except Exception as exc:
            logger.error("Director failed for paragraph '%s': %s — using fallback", paragraph.id, exc)
            return (
                LayoutMode.SPLIT_50_50,
                0.3,
                f"FALLBACK: AI agent failed ({exc}). Using safe split layout. Please review manually.",
                [],
                TokenUsage(),
            )

    def _compute_transition(self, hint: ContinuityHint, is_first: bool) -> TransitionOutput:
        """Determine the transition type."""
        if is_first:
            return TransitionOutput(type=TransitionType.FADE, duration_ms=400, instruction="Opening fade in.")

        if hint.pin_instructor and hint.sequence_position.value in ("middle", "end"):
            return TransitionOutput(
                type=TransitionType.NONE, duration_ms=0,
                instruction="Instructor pinned — no transition, only board content changes.",
            )

        return TransitionOutput(type=TransitionType.FADE, duration_ms=400, instruction="Smooth fade transition.")

    def _sequence_note(self, hint: ContinuityHint) -> str:
        """Generate a human-readable sequence note."""
        if not hint.is_in_sequence:
            return "Standalone paragraph — no sequence context."

        pos = hint.sequence_position.value
        length = hint.sequence_length

        if pos == "start":
            return f"Starting {length}-paragraph asset sequence. Instructor pinned for visual stability."
        elif pos == "middle":
            return f"Continuing pinned sequence ({length} paragraphs total)."
        elif pos == "end":
            return f"End of {length}-paragraph sequence. Instructor position may change next."
        return ""
