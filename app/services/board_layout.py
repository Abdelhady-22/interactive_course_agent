"""Board layout — computes script visibility, keyword badges, and asset arrangement."""

from __future__ import annotations

from app.schemas.enums import LayoutMode
from app.schemas.inputs import NormalizedParagraph
from app.schemas.outputs import (
    AssetOutput,
    KeywordBadge,
    PositionRect,
    ScriptText,
)
from app.services.position_calculator import (
    compute_asset_positions,
    compute_keyword_positions,
    compute_script_text_position,
)


# ── Script visibility ratio per layout mode ──

_VISIBILITY_RATIOS: dict[LayoutMode, float] = {
    LayoutMode.INSTRUCTOR_ONLY: 0.0,
    LayoutMode.BOARD_ONLY: 1.0,
    LayoutMode.BOARD_DOMINANT: 0.3,
    LayoutMode.INSTRUCTOR_DOMINANT: 0.2,
    LayoutMode.SPLIT_50_50: 0.5,
    LayoutMode.SPLIT_60_40: 0.4,
    LayoutMode.INSTRUCTOR_PIP: 0.3,
    LayoutMode.PICTURE_IN_PICTURE_LARGE: 0.3,
    LayoutMode.INSTRUCTOR_BEHIND_BOARD: 0.5,
    LayoutMode.OVERLAY_FLOATING: 0.0,
    LayoutMode.BOARD_WITH_SIDE_STRIP: 0.4,
    LayoutMode.MULTI_ASSET_GRID: 0.2,
    LayoutMode.FULLSCREEN_ASSET: 0.0,
    LayoutMode.STACKED_VERTICAL: 0.5,
}


def compute_board_content(
    paragraph: NormalizedParagraph,
    layout_mode: LayoutMode,
    board_rect: PositionRect,
    suggested_asset_ids: list[str] | None = None,
) -> tuple[list[AssetOutput], list[KeywordBadge], ScriptText]:
    """Compute all board content: arranged assets, keyword badges, script text.

    Args:
        paragraph: The normalized paragraph.
        layout_mode: The chosen layout mode.
        board_rect: The board's position rectangle.
        suggested_asset_ids: Optional list of asset IDs to display (from rules/LLM).

    Returns:
        (assets, keyword_badges, script_text) with all positions computed.
    """
    # ── Assets ──
    assets_to_display = _select_assets(paragraph, suggested_asset_ids)
    asset_positions = compute_asset_positions(len(assets_to_display), board_rect)

    asset_outputs: list[AssetOutput] = []
    for i, asset in enumerate(assets_to_display):
        pos = asset_positions[i] if i < len(asset_positions) else asset_positions[-1]

        # Stagger appearance: first asset appears immediately, others 3s later each
        stagger_ms = i * 3000
        appear = paragraph.start_ms + stagger_ms
        disappear = paragraph.end_ms

        asset_outputs.append(AssetOutput(
            id=asset.id,
            type=asset.type,
            name=asset.name,
            position_rect=pos,
            size=_asset_size(len(assets_to_display)),
            display_instruction=_build_asset_instruction(asset, layout_mode),
            appear_at_ms=appear,
            disappear_at_ms=disappear,
        ))

    # ── Keywords ──
    keyword_badges = _compute_keywords(paragraph, board_rect)

    # ── Script Text ──
    vis_ratio = _get_visibility_ratio(layout_mode, len(assets_to_display))
    script_text_pos = compute_script_text_position(board_rect, vis_ratio)

    script_text = ScriptText(
        position_rect=script_text_pos,
        visibility_ratio=vis_ratio,
        reasoning=_visibility_reasoning(layout_mode, len(assets_to_display)),
        keywords_to_highlight=[kw.word for kw in paragraph.keywords],
    )

    return asset_outputs, keyword_badges, script_text


def _select_assets(
    paragraph: NormalizedParagraph,
    suggested_ids: list[str] | None,
) -> list:
    """Select which assets to display, respecting suggestions."""
    if not paragraph.assets:
        return []

    if suggested_ids:
        # Show suggested assets first, then any remaining
        suggested = [a for a in paragraph.assets if a.id in suggested_ids]
        remaining = [a for a in paragraph.assets if a.id not in suggested_ids]
        return suggested + remaining
    else:
        return paragraph.assets


def _asset_size(count: int) -> str:
    """Determine asset size based on how many are showing."""
    if count == 1:
        return "large"
    elif count == 2:
        return "medium"
    else:
        return "small"


def _build_asset_instruction(asset, layout_mode: LayoutMode) -> str:
    """Generate a human-readable display instruction for the asset."""
    type_label = asset.type.capitalize()
    name = asset.name or "visual asset"

    if layout_mode == LayoutMode.FULLSCREEN_ASSET:
        return f"Display {type_label} '{name}' fullscreen with maximum detail."
    elif layout_mode == LayoutMode.MULTI_ASSET_GRID:
        return f"Show {type_label} '{name}' in grid cell. Size appropriately for comparison."
    elif layout_mode in (LayoutMode.BOARD_DOMINANT, LayoutMode.BOARD_ONLY):
        return f"Show {type_label} '{name}' prominently on the board. It is the main visual focus."
    elif layout_mode in (LayoutMode.OVERLAY_FLOATING, LayoutMode.INSTRUCTOR_DOMINANT):
        return f"Show {type_label} '{name}' as a small overlay — supplementary to the instructor."
    else:
        return f"Display {type_label} '{name}' on the board, sized to balance with the instructor."


def _compute_keywords(
    paragraph: NormalizedParagraph,
    board_rect: PositionRect,
) -> list[KeywordBadge]:
    """Compute keyword badge positions and timing."""
    if not paragraph.keywords:
        return []

    positions = compute_keyword_positions(len(paragraph.keywords), board_rect)
    badges: list[KeywordBadge] = []

    if not positions:
        return badges

    for i, kw in enumerate(paragraph.keywords):
        pos = positions[i] if i < len(positions) else positions[-1]

        # Try to time the keyword to when it's spoken
        appear_ms, disappear_ms = _keyword_timing(kw.word, paragraph)

        style = "badge" if kw.type == "main" else "highlight" if kw.type == "Key Terms" else "floating"

        badges.append(KeywordBadge(
            word=kw.word,
            type=kw.type,
            position_rect=pos,
            appear_at_ms=appear_ms,
            disappear_at_ms=disappear_ms,
            style=style,
        ))

    return badges


def _keyword_timing(
    keyword: str,
    paragraph: NormalizedParagraph,
) -> tuple[int, int]:
    """Find timing for a keyword from word timestamps."""
    kw_lower = keyword.lower().split()

    for wt in paragraph.word_timestamps:
        if wt.word.lower().strip() in kw_lower or keyword.lower() in wt.word.lower():
            return wt.start_ms, max(wt.end_ms, paragraph.end_ms)

    # Fallback: show for the entire paragraph duration
    return paragraph.start_ms, paragraph.end_ms


def _get_visibility_ratio(layout_mode: LayoutMode, asset_count: int) -> float:
    """Get script visibility ratio, adjusted for asset presence."""
    base = _VISIBILITY_RATIOS.get(layout_mode, 0.5)

    # If no assets, show more text
    if asset_count == 0 and base < 0.5:
        return max(base, 0.7)

    # Many assets → less text
    if asset_count >= 3:
        return min(base, 0.2)

    return base


def _visibility_reasoning(layout_mode: LayoutMode, asset_count: int) -> str:
    """Generate human-readable reasoning for visibility ratio."""
    ratio = _get_visibility_ratio(layout_mode, asset_count)

    if ratio == 0.0:
        return "Instructor is the sole focus — no script text needed on screen."
    elif ratio <= 0.3:
        return "Visual assets are the primary focus. Show key phrases only as reinforcement."
    elif ratio <= 0.5:
        return "Balanced layout — show enough text for learners who prefer reading along."
    elif ratio <= 0.8:
        return "Text-heavy moment — most of the script should be visible."
    else:
        return "Full text display — the written content IS the primary learning material."
