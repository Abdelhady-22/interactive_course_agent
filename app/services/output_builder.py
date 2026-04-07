"""Output builder — assembles the final PlaybackJSON response."""

from __future__ import annotations

import uuid
from collections import Counter

from app.schemas.outputs import (
    CourseSummary,
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
    """Assemble the final PlaybackJSON with statistics and course summary."""
    stats = _compute_stats(decisions, processing_time_ms)
    summary = _compute_course_summary(decisions)

    return PlaybackJSON(
        course_id=str(uuid.uuid4()),
        title=title,
        total_paragraphs=len(decisions),
        stats=stats,
        summary=summary,
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


def _compute_course_summary(decisions: list[DecisionOutput]) -> CourseSummary:
    """Compute a course-level quality summary across all decisions."""
    if not decisions:
        return CourseSummary()

    # Total duration
    total_duration = 0
    if decisions:
        total_duration = decisions[-1].time_range["end_ms"] - decisions[0].time_range["start_ms"]

    # Layout mode distribution
    mode_counts: Counter[str] = Counter()
    for d in decisions:
        mode_counts[d.layout.mode.value] += 1

    # Asset tracking
    all_asset_ids: list[str] = []
    asset_name_by_id: dict[str, str] = {}
    asset_paragraph_map: dict[str, list[int]] = {}
    paragraphs_without_assets: list[int] = []

    for d in decisions:
        if not d.assets:
            paragraphs_without_assets.append(d.paragraph_index)
        for asset in d.assets:
            all_asset_ids.append(asset.id)
            asset_name_by_id[asset.id] = asset.name
            asset_paragraph_map.setdefault(asset.id, []).append(d.paragraph_index)

    unique_assets = len(set(all_asset_ids))
    duplicate_assets = [
        asset_name_by_id[aid]
        for aid, paragraphs in asset_paragraph_map.items()
        if len(paragraphs) > 1
    ]

    # Animation variety (how many different entrance animations used)
    all_animations: set[str] = set()
    for d in decisions:
        for asset in d.assets:
            all_animations.add(asset.entrance.value)
        for kw in d.keyword_badges:
            all_animations.add(kw.entrance.value)
    total_possible_animations = 9  # fade_in, scale_in, slide_up, etc.
    animation_variety = min(1.0, len(all_animations) / max(1, total_possible_animations))

    # Visual variety score (layout diversity + asset spread)
    unique_modes = len(mode_counts)
    total_modes = 14
    layout_diversity = min(1.0, unique_modes / max(1, min(total_modes, len(decisions))))

    # Penalize for too many same layout in a row
    max_consecutive = _max_consecutive_same_mode(decisions)
    consecutive_penalty = max(0, (max_consecutive - 3) * 0.1)  # Penalty if 4+ same in a row

    visual_variety = max(0.0, min(1.0,
        (layout_diversity * 0.5 + animation_variety * 0.3 + (1 - len(paragraphs_without_assets) / max(1, len(decisions))) * 0.2)
        - consecutive_penalty
    ))

    # Average confidence
    avg_confidence = sum(d.confidence for d in decisions) / max(1, len(decisions))

    # Warnings
    warnings: list[str] = []
    if max_consecutive >= 4:
        dominant_mode = max(mode_counts, key=mode_counts.get)
        warnings.append(
            f"Layout '{dominant_mode}' used {max_consecutive} times consecutively — consider adding variety."
        )
    if duplicate_assets:
        warnings.append(
            f"Duplicate assets detected: {', '.join(duplicate_assets)}. Consider using unique visuals."
        )
    if len(paragraphs_without_assets) > len(decisions) * 0.5:
        warnings.append(
            f"{len(paragraphs_without_assets)}/{len(decisions)} paragraphs have no visual assets."
        )
    if avg_confidence < 0.7:
        warnings.append(
            f"Average confidence is low ({avg_confidence:.2f}). Consider manual review."
        )

    return CourseSummary(
        total_duration_ms=total_duration,
        layout_mode_distribution=dict(mode_counts),
        unique_assets_used=unique_assets,
        duplicate_assets=duplicate_assets,
        paragraphs_without_assets=paragraphs_without_assets,
        animation_variety_score=round(animation_variety, 2),
        visual_variety_score=round(visual_variety, 2),
        avg_confidence=round(avg_confidence, 2),
        warnings=warnings,
    )


def _max_consecutive_same_mode(decisions: list[DecisionOutput]) -> int:
    """Find the longest run of consecutive paragraphs with the same layout mode."""
    if not decisions:
        return 0

    max_run = 1
    current_run = 1
    for i in range(1, len(decisions)):
        if decisions[i].layout.mode == decisions[i - 1].layout.mode:
            current_run += 1
            max_run = max(max_run, current_run)
        else:
            current_run = 1

    return max_run

