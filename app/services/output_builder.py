"""Output builder — assembles the final PlaybackJSON response."""

from __future__ import annotations

import uuid

from app.schemas.outputs import (
    DecisionOutput,
    PlaybackJSON,
    ProcessingStats,
    TokenUsage,
)
from app.schemas.enums import DecisionSource


def build_playback_json(
    decisions: list[DecisionOutput],
    title: str = "",
    processing_time_ms: int = 0,
) -> PlaybackJSON:
    """Assemble the final PlaybackJSON with statistics."""
    stats = _compute_stats(decisions, processing_time_ms)

    return PlaybackJSON(
        course_id=str(uuid.uuid4()),
        title=title,
        total_paragraphs=len(decisions),
        stats=stats,
        decisions=decisions,
    )


def _compute_stats(decisions: list[DecisionOutput], processing_time_ms: int) -> ProcessingStats:
    """Compute processing statistics from all decisions."""
    rule_count = 0
    llm_count = 0
    fallback_count = 0
    reviewed_count = 0
    overrode_count = 0
    total_prompt = 0
    total_completion = 0

    for d in decisions:
        if d.decided_by == DecisionSource.RULE:
            rule_count += 1
        elif d.decided_by == DecisionSource.LLM:
            llm_count += 1
        elif d.decided_by == DecisionSource.FALLBACK:
            fallback_count += 1

        if d.reviewed_by_llm:
            reviewed_count += 1
            if d.llm_agreed is False:
                overrode_count += 1

        total_prompt += d.token_usage.prompt_tokens
        total_completion += d.token_usage.completion_tokens

    return ProcessingStats(
        decided_by_rule=rule_count,
        decided_by_llm=llm_count,
        decided_by_fallback=fallback_count,
        rule_reviewed_by_llm=reviewed_count,
        llm_overrode_rule=overrode_count,
        tokens=TokenUsage(prompt_tokens=total_prompt, completion_tokens=total_completion),
        processing_time_ms=processing_time_ms,
    )
