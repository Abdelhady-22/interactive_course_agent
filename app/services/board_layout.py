"""Board layout — computes script visibility, keyword badges, asset arrangement, and V2 enhancements."""

from __future__ import annotations

from app.schemas.enums import (
    LayoutMode, AnimationType, ScriptPosition, ScriptStyle,
    InstructorEnergy, InstructorGesture, FocusTarget,
)
from app.schemas.inputs import NormalizedParagraph
from app.schemas.outputs import (
    AssetOutput,
    FocusZone,
    InstructorBehavior,
    KeywordBadge,
    PositionRect,
    ScriptText,
)
from app.services.position_calculator import (
    compute_asset_positions,
    compute_keyword_positions,
    compute_script_text_position,
)


# ── Script show/hide rules per layout mode ──

_SCRIPT_SHOW: dict[LayoutMode, bool] = {
    LayoutMode.INSTRUCTOR_ONLY: False,
    LayoutMode.BOARD_ONLY: True,
    LayoutMode.BOARD_DOMINANT: True,
    LayoutMode.INSTRUCTOR_DOMINANT: True,
    LayoutMode.SPLIT_50_50: True,
    LayoutMode.SPLIT_60_40: True,
    LayoutMode.INSTRUCTOR_PIP: True,
    LayoutMode.PICTURE_IN_PICTURE_LARGE: True,
    LayoutMode.INSTRUCTOR_BEHIND_BOARD: True,
    LayoutMode.OVERLAY_FLOATING: False,
    LayoutMode.BOARD_WITH_SIDE_STRIP: True,
    LayoutMode.MULTI_ASSET_GRID: False,
    LayoutMode.FULLSCREEN_ASSET: False,
    LayoutMode.STACKED_VERTICAL: True,
}

# ── Animation presets per asset count ──

_ASSET_ANIMATIONS: dict[int, list[AnimationType]] = {
    1: [AnimationType.SCALE_IN],
    2: [AnimationType.SLIDE_LEFT, AnimationType.SLIDE_RIGHT],
    3: [AnimationType.ZOOM_IN, AnimationType.SLIDE_LEFT, AnimationType.SLIDE_RIGHT],
    4: [AnimationType.FADE_IN, AnimationType.SLIDE_LEFT, AnimationType.FADE_IN, AnimationType.SLIDE_RIGHT],
}

# ── Keyword animation by type ──

_KEYWORD_ANIMATIONS: dict[str, AnimationType] = {
    "main": AnimationType.POP_IN,
    "Key Terms": AnimationType.SLIDE_UP,
    "Callouts": AnimationType.FADE_IN,
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
    # ── Assets with animations ──
    assets_to_display = _select_assets(paragraph, suggested_asset_ids)
    asset_positions = compute_asset_positions(len(assets_to_display), board_rect)
    anim_presets = _ASSET_ANIMATIONS.get(len(assets_to_display), [AnimationType.FADE_IN])

    asset_outputs: list[AssetOutput] = []
    for i, asset in enumerate(assets_to_display):
        pos = asset_positions[i] if i < len(asset_positions) else asset_positions[-1]

        # Stagger appearance: first asset appears immediately, others 2s later each
        stagger_ms = i * 2000
        appear = paragraph.start_ms + stagger_ms
        disappear = paragraph.end_ms

        # Pick animation (cycle through presets)
        entrance_anim = anim_presets[i % len(anim_presets)]

        asset_outputs.append(AssetOutput(
            id=asset.id,
            type=asset.type,
            name=asset.name,
            position_rect=pos,
            size=_asset_size(len(assets_to_display)),
            display_instruction=_build_asset_instruction(asset, layout_mode),
            appear_at_ms=appear,
            disappear_at_ms=disappear,
            entrance=entrance_anim,
            exit=AnimationType.FADE_OUT,
            entrance_delay_ms=stagger_ms,
            entrance_duration_ms=400,
        ))

    # ── Keywords with animations ──
    keyword_badges = _compute_keywords(paragraph, board_rect)

    # ── Script Text with options ──
    show_script = _should_show_script(layout_mode, len(assets_to_display))
    script_position = _choose_script_position(layout_mode, len(assets_to_display))
    script_style = _choose_script_style(layout_mode, len(assets_to_display))
    script_text_pos = compute_script_text_position(board_rect, show_script, script_position)

    script_text = ScriptText(
        show=show_script,
        full_text=paragraph.text,
        position=ScriptPosition(script_position),
        script_style=script_style,
        font_size=_choose_font_size(layout_mode),
        background="glassmorphism" if show_script else "transparent",
        position_rect=script_text_pos,
        keywords_to_highlight=[kw.word for kw in paragraph.keywords],
    )

    return asset_outputs, keyword_badges, script_text


def compute_instructor_behavior(
    paragraph: NormalizedParagraph,
    layout_mode: LayoutMode,
    has_assets: bool,
) -> InstructorBehavior:
    """Compute suggested instructor behavior for this paragraph."""

    text_lower = paragraph.text.lower()

    # Detect energy level
    if _is_greeting(text_lower):
        energy = InstructorEnergy.ENTHUSIASTIC
        gesture = InstructorGesture.HANDS_OPEN
        eye_contact = "camera"
        movement = "lean_forward"
        note = "Welcome the learners warmly. Make eye contact with the camera."
    elif any(w in text_lower for w in ["important", "critical", "warning", "danger", "careful"]):
        energy = InstructorEnergy.SERIOUS
        gesture = InstructorGesture.EMPHASIZING
        eye_contact = "camera"
        movement = "still"
        note = "Emphasize the importance. Slow down and make direct eye contact."
    elif any(w in text_lower for w in ["amazing", "incredible", "fascinating", "exciting"]):
        energy = InstructorEnergy.EXCITED
        gesture = InstructorGesture.HANDS_OPEN
        eye_contact = "camera"
        movement = "lean_forward"
        note = "Show genuine excitement about the topic."
    elif has_assets:
        energy = InstructorEnergy.NEUTRAL
        gesture = InstructorGesture.POINTING_AT_BOARD
        eye_contact = "board"
        movement = "still"
        note = "Point toward the board/asset while explaining. Glance at the visual."
    elif _has_numbers_or_lists(text_lower):
        energy = InstructorEnergy.CALM
        gesture = InstructorGesture.COUNTING
        eye_contact = "camera"
        movement = "still"
        note = "Use counting gestures when listing items or numbers."
    else:
        energy = InstructorEnergy.NEUTRAL
        gesture = InstructorGesture.NONE
        eye_contact = "camera"
        movement = "still"
        note = "Maintain natural speaking posture with steady eye contact."

    return InstructorBehavior(
        energy=energy,
        gesture=gesture,
        eye_contact=eye_contact,
        movement=movement,
        note=note,
    )


def compute_focus_zone(
    layout_mode: LayoutMode,
    has_assets: bool,
    board_rect: PositionRect,
    instructor_visible: bool,
) -> FocusZone:
    """Compute where the learner should focus attention."""

    if layout_mode in (LayoutMode.INSTRUCTOR_ONLY, LayoutMode.OVERLAY_FLOATING):
        return FocusZone(
            primary=FocusTarget.INSTRUCTOR,
            dim_background=False,
            attention_cue="none",
        )

    if layout_mode in (LayoutMode.BOARD_ONLY, LayoutMode.FULLSCREEN_ASSET):
        return FocusZone(
            primary=FocusTarget.BOARD,
            highlight_rect=board_rect if has_assets else None,
            dim_background=False,
            attention_cue="none",
        )

    if layout_mode in (LayoutMode.BOARD_DOMINANT, LayoutMode.INSTRUCTOR_PIP, LayoutMode.MULTI_ASSET_GRID):
        return FocusZone(
            primary=FocusTarget.ASSET if has_assets else FocusTarget.BOARD,
            highlight_rect=board_rect,
            dim_background=has_assets,
            attention_cue="glow" if has_assets else "none",
        )

    if layout_mode == LayoutMode.INSTRUCTOR_DOMINANT:
        return FocusZone(
            primary=FocusTarget.INSTRUCTOR,
            dim_background=False,
            attention_cue="none",
        )

    if layout_mode in (LayoutMode.SPLIT_50_50, LayoutMode.SPLIT_60_40, LayoutMode.STACKED_VERTICAL):
        return FocusZone(
            primary=FocusTarget.SPLIT,
            dim_background=False,
            attention_cue="none",
        )

    return FocusZone(
        primary=FocusTarget.INSTRUCTOR,
        dim_background=False,
        attention_cue="none",
    )


# ─────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────

def _select_assets(
    paragraph: NormalizedParagraph,
    suggested_ids: list[str] | None,
) -> list:
    """Select which assets to display, respecting suggestions."""
    if not paragraph.assets:
        return []

    if suggested_ids:
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
    """Compute keyword badge positions, timing, and animations."""
    if not paragraph.keywords:
        return []

    positions = compute_keyword_positions(len(paragraph.keywords), board_rect)
    badges: list[KeywordBadge] = []

    if not positions:
        return badges

    for i, kw in enumerate(paragraph.keywords):
        pos = positions[i] if i < len(positions) else positions[-1]

        # Time the keyword to when it's spoken
        appear_ms, spoken_ms, disappear_ms = _keyword_timing(kw.word, paragraph)

        style = "badge" if kw.type == "main" else "highlight" if kw.type == "Key Terms" else "floating"
        entrance = _KEYWORD_ANIMATIONS.get(kw.type, AnimationType.FADE_IN)

        badges.append(KeywordBadge(
            word=kw.word,
            type=kw.type,
            position_rect=pos,
            appear_at_ms=appear_ms,
            disappear_at_ms=disappear_ms,
            style=style,
            spoken_at_ms=spoken_ms,
            highlight_in_script=True,
            entrance=entrance,
            entrance_delay_ms=i * 500,  # Stagger keyword entrances
            entrance_duration_ms=300,
        ))

    return badges


def _keyword_timing(
    keyword: str,
    paragraph: NormalizedParagraph,
) -> tuple[int, int, int]:
    """Find timing for a keyword from word timestamps.

    Returns: (appear_ms, spoken_ms, disappear_ms)
    """
    kw_lower = keyword.lower().split()

    for wt in paragraph.word_timestamps:
        if wt.word.lower().strip() in kw_lower or keyword.lower() in wt.word.lower():
            return wt.start_ms, wt.start_ms, max(wt.end_ms, paragraph.end_ms)

    # Fallback: show for the entire paragraph duration
    return paragraph.start_ms, paragraph.start_ms, paragraph.end_ms


def _should_show_script(layout_mode: LayoutMode, asset_count: int) -> bool:
    """Determine if script text should be shown."""
    base_show = _SCRIPT_SHOW.get(layout_mode, True)

    # Override: if many assets, hide script to avoid clutter
    if asset_count >= 3:
        return False

    return base_show


def _choose_script_position(layout_mode: LayoutMode, asset_count: int) -> str:
    """Choose the best script text position."""
    if layout_mode in (LayoutMode.STACKED_VERTICAL,):
        return "overlay_center"
    elif layout_mode in (LayoutMode.BOARD_WITH_SIDE_STRIP,):
        return "side_panel"
    elif layout_mode in (LayoutMode.INSTRUCTOR_BEHIND_BOARD,):
        return "top"
    else:
        return "bottom"


def _choose_script_style(layout_mode: LayoutMode, asset_count: int) -> ScriptStyle:
    """Choose the best script display style."""
    if layout_mode in (LayoutMode.INSTRUCTOR_ONLY, LayoutMode.OVERLAY_FLOATING):
        return ScriptStyle.CAPTION
    elif asset_count >= 2:
        return ScriptStyle.SUBTITLE
    elif layout_mode == LayoutMode.BOARD_ONLY:
        return ScriptStyle.FULL_TEXT
    else:
        return ScriptStyle.SUBTITLE


def _choose_font_size(layout_mode: LayoutMode) -> str:
    """Choose font size based on layout."""
    if layout_mode in (LayoutMode.INSTRUCTOR_PIP, LayoutMode.MULTI_ASSET_GRID):
        return "small"
    elif layout_mode in (LayoutMode.BOARD_ONLY, LayoutMode.STACKED_VERTICAL):
        return "large"
    else:
        return "medium"


def _is_greeting(text: str) -> bool:
    """Check if text is a greeting."""
    import re
    greeting_words = ["welcome", "hello", "hey", "good morning", "good evening", "greetings"]
    return any(re.search(rf'\b{word}\b', text, re.IGNORECASE) for word in greeting_words)


def _has_numbers_or_lists(text: str) -> bool:
    """Check if text contains numbered lists or quantities."""
    import re
    return bool(re.search(r'\b(first|second|third|four|five|step \d|stage \d|\d+%|\d+ degrees)', text))
