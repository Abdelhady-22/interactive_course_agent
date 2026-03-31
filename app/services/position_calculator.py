"""Position calculator — computes exact percentage-based positions for all 14 layout modes.

Supports both:
  - Standard layout: side-by-side splits (original)
  - Fullscreen-first: primary element 100%, secondary as overlay
"""

from __future__ import annotations

from app.schemas.enums import LayoutMode, PipShape, PipBorder, AnimationType, BoardBackground
from app.schemas.outputs import (
    BoardLayout,
    InstructorLayout,
    PositionRect,
)


# ────────────────────────────────────────────────────────────
# Standard layout templates:  instructor=(x, y, w, h, z, anchor, size, style, opacity)
#                              board=(x, y, w, h, z, anchor)
# ────────────────────────────────────────────────────────────

_LAYOUT_TEMPLATES: dict[LayoutMode, dict] = {
    LayoutMode.INSTRUCTOR_ONLY: {
        "instructor": (0, 0, 100, 100, 1, "center", "full", "normal", 1.0),
        "board": None,
    },
    LayoutMode.BOARD_ONLY: {
        "instructor": None,
        "board": (0, 0, 100, 100, 1, "center"),
    },
    LayoutMode.BOARD_DOMINANT: {
        "instructor": (72, 72, 25, 25, 10, "bottom_right", "small", "pip", 1.0),
        "board": (0, 0, 70, 100, 1, "left"),
    },
    LayoutMode.INSTRUCTOR_DOMINANT: {
        "instructor": (0, 0, 70, 100, 1, "left", "large", "normal", 1.0),
        "board": (72, 5, 25, 30, 5, "top_right"),
    },
    LayoutMode.SPLIT_50_50: {
        "instructor": (50, 0, 50, 100, 1, "right", "medium", "normal", 1.0),
        "board": (0, 0, 50, 100, 1, "left"),
    },
    LayoutMode.SPLIT_60_40: {
        "instructor": (60, 0, 40, 100, 1, "right", "medium", "normal", 1.0),
        "board": (0, 0, 60, 100, 1, "left"),
    },
    LayoutMode.INSTRUCTOR_PIP: {
        "instructor": (82, 77, 15, 20, 10, "bottom_right", "small", "pip", 1.0),
        "board": (0, 0, 100, 100, 1, "full"),
    },
    LayoutMode.PICTURE_IN_PICTURE_LARGE: {
        "instructor": (67, 65, 30, 30, 10, "bottom_right", "medium", "pip", 1.0),
        "board": (0, 0, 100, 100, 1, "full"),
    },
    LayoutMode.INSTRUCTOR_BEHIND_BOARD: {
        "instructor": (0, 0, 100, 100, 1, "center", "full", "semi_transparent", 0.3),
        "board": (0, 0, 100, 100, 5, "full"),
    },
    LayoutMode.OVERLAY_FLOATING: {
        "instructor": (0, 0, 100, 100, 1, "center", "full", "normal", 1.0),
        "board": (65, 5, 30, 25, 10, "top_right"),
    },
    LayoutMode.BOARD_WITH_SIDE_STRIP: {
        "instructor": (75, 0, 25, 100, 5, "right", "medium", "normal", 1.0),
        "board": (0, 0, 75, 100, 1, "left"),
    },
    LayoutMode.MULTI_ASSET_GRID: {
        "instructor": (82, 77, 15, 20, 10, "bottom_right", "small", "pip", 1.0),
        "board": (0, 0, 100, 100, 1, "full"),
    },
    LayoutMode.FULLSCREEN_ASSET: {
        "instructor": None,
        "board": (0, 0, 100, 100, 1, "full"),
    },
    LayoutMode.STACKED_VERTICAL: {
        "instructor": (0, 0, 100, 50, 1, "top", "medium", "normal", 1.0),
        "board": (0, 50, 100, 50, 1, "bottom"),
    },
}

# ────────────────────────────────────────────────────────────
# Fullscreen-first templates: primary=100%, secondary=overlay
# ────────────────────────────────────────────────────────────

_FULLSCREEN_TEMPLATES: dict[LayoutMode, dict] = {
    LayoutMode.INSTRUCTOR_ONLY: {
        "instructor": (0, 0, 100, 100, 1, "center", "full", "normal", 1.0),
        "instructor_fullscreen": True,
        "board": None,
    },
    LayoutMode.BOARD_ONLY: {
        "instructor": None,
        "board": (0, 0, 100, 100, 1, "center"),
        "board_fullscreen": True,
    },
    LayoutMode.BOARD_DOMINANT: {
        "instructor": (75, 73, 22, 22, 10, "bottom_right", "small", "pip", 1.0),
        "board": (0, 0, 100, 100, 1, "full"),
        "board_fullscreen": True,
    },
    LayoutMode.INSTRUCTOR_DOMINANT: {
        "instructor": (0, 0, 100, 100, 1, "center", "full", "normal", 1.0),
        "instructor_fullscreen": True,
        "board": (55, 5, 42, 50, 8, "right_panel"),
    },
    LayoutMode.SPLIT_50_50: {
        "instructor": (50, 0, 50, 100, 1, "right", "medium", "normal", 1.0),
        "board": (0, 0, 50, 100, 1, "left"),
    },
    LayoutMode.SPLIT_60_40: {
        "instructor": (60, 0, 40, 100, 1, "right", "medium", "normal", 1.0),
        "board": (0, 0, 60, 100, 1, "left"),
    },
    LayoutMode.INSTRUCTOR_PIP: {
        "instructor": (80, 76, 17, 20, 10, "bottom_right", "small", "pip", 1.0),
        "board": (0, 0, 100, 100, 1, "full"),
        "board_fullscreen": True,
    },
    LayoutMode.PICTURE_IN_PICTURE_LARGE: {
        "instructor": (65, 63, 32, 32, 10, "bottom_right", "medium", "pip", 1.0),
        "board": (0, 0, 100, 100, 1, "full"),
        "board_fullscreen": True,
    },
    LayoutMode.INSTRUCTOR_BEHIND_BOARD: {
        "instructor": (0, 0, 100, 100, 1, "center", "full", "semi_transparent", 0.3),
        "instructor_fullscreen": True,
        "board": (0, 0, 100, 100, 5, "full"),
        "board_fullscreen": True,
    },
    LayoutMode.OVERLAY_FLOATING: {
        "instructor": (0, 0, 100, 100, 1, "center", "full", "normal", 1.0),
        "instructor_fullscreen": True,
        "board": (60, 5, 37, 35, 10, "top_right"),
    },
    LayoutMode.BOARD_WITH_SIDE_STRIP: {
        "instructor": (0, 0, 100, 100, 1, "center", "full", "normal", 1.0),
        "instructor_fullscreen": True,
        "board": (60, 3, 38, 94, 8, "right_panel"),
    },
    LayoutMode.MULTI_ASSET_GRID: {
        "instructor": (80, 76, 17, 20, 10, "bottom_right", "small", "pip", 1.0),
        "board": (0, 0, 100, 100, 1, "full"),
        "board_fullscreen": True,
    },
    LayoutMode.FULLSCREEN_ASSET: {
        "instructor": None,
        "board": (0, 0, 100, 100, 1, "full"),
        "board_fullscreen": True,
    },
    LayoutMode.STACKED_VERTICAL: {
        "instructor": (0, 0, 100, 45, 1, "top", "medium", "normal", 1.0),
        "board": (0, 48, 100, 52, 1, "bottom"),
    },
}

# ── PiP shape defaults by size ──
_PIP_DEFAULTS = {
    "small": {"shape": PipShape.CIRCLE, "border": PipBorder.GLOW_BLUE, "shadow": True},
    "medium": {"shape": PipShape.ROUNDED_RECT, "border": PipBorder.THIN_WHITE, "shadow": True},
    "large": {"shape": PipShape.ROUNDED_RECT, "border": PipBorder.NONE, "shadow": False},
    "full": {"shape": PipShape.ROUNDED_RECT, "border": PipBorder.NONE, "shadow": False},
}


def compute_layout_positions(
    mode: LayoutMode,
    use_fullscreen: bool = True,
) -> tuple[InstructorLayout, BoardLayout]:
    """Compute instructor and board positions for a layout mode.

    Args:
        mode: The layout mode to compute positions for.
        use_fullscreen: If True, use fullscreen-first templates (primary=100%).
                        If False, use standard side-by-side splits.

    Returns:
        (InstructorLayout, BoardLayout) with exact PositionRect values.
    """
    templates = _FULLSCREEN_TEMPLATES if use_fullscreen else _LAYOUT_TEMPLATES
    template = templates.get(mode, templates[LayoutMode.SPLIT_50_50])

    # Instructor
    inst_data = template.get("instructor")
    if inst_data is None:
        instructor = InstructorLayout(
            visible=False,
            fullscreen=False,
            position_rect=PositionRect(x_percent=0, y_percent=0, width_percent=0, height_percent=0, z_index=0, anchor="hidden"),
            size="none",
            style="normal",
            opacity=0.0,
        )
    else:
        x, y, w, h, z, anchor, size, style, opacity = inst_data
        is_fullscreen = template.get("instructor_fullscreen", False)
        pip_defaults = _PIP_DEFAULTS.get(size, _PIP_DEFAULTS["medium"])
        instructor = InstructorLayout(
            visible=True,
            fullscreen=is_fullscreen,
            position_rect=PositionRect(x_percent=x, y_percent=y, width_percent=w, height_percent=h, z_index=z, anchor=anchor),
            size=size,
            style=style,
            opacity=opacity,
            pip_shape=pip_defaults["shape"],
            pip_border=pip_defaults["border"],
            pip_shadow=pip_defaults["shadow"],
            entrance_animation=AnimationType.FADE_IN if is_fullscreen else AnimationType.SCALE_IN,
        )

    # Board
    board_data = template.get("board")
    if board_data is None:
        board = BoardLayout(
            visible=False,
            fullscreen=False,
            position_rect=PositionRect(x_percent=0, y_percent=0, width_percent=0, height_percent=0, z_index=0, anchor="hidden"),
        )
    else:
        x, y, w, h, z, anchor = board_data
        is_fullscreen = template.get("board_fullscreen", False)
        board = BoardLayout(
            visible=True,
            fullscreen=is_fullscreen,
            position_rect=PositionRect(x_percent=x, y_percent=y, width_percent=w, height_percent=h, z_index=z, anchor=anchor),
            background=BoardBackground.TRANSPARENT if is_fullscreen else BoardBackground.DARK_GRADIENT,
            border_radius=0 if is_fullscreen else 12,
            shadow="none" if is_fullscreen else "medium",
            board_opacity=1.0 if is_fullscreen else 0.95,
        )

    return instructor, board


def compute_dynamic_board_rect(
    asset_count: int,
    asset_types: list[str],
    base_rect: PositionRect,
    is_overlay: bool = False,
) -> PositionRect:
    """Dynamically size the board overlay based on asset content.

    Only applies when the board is an overlay on the instructor (not fullscreen).
    When board is fullscreen, the base_rect (100×100) is kept.
    """
    if not is_overlay:
        return base_rect

    if asset_count == 0:
        # Text/keywords only — compact panel
        return PositionRect(
            x_percent=55, y_percent=10,
            width_percent=42, height_percent=35,
            z_index=base_rect.z_index, anchor="right_panel_compact",
        )
    elif asset_count == 1:
        if "formula" in asset_types or "chart" in asset_types:
            return PositionRect(
                x_percent=45, y_percent=8,
                width_percent=52, height_percent=50,
                z_index=base_rect.z_index, anchor="right_panel_medium",
            )
        else:
            return PositionRect(
                x_percent=35, y_percent=5,
                width_percent=62, height_percent=75,
                z_index=base_rect.z_index, anchor="right_panel_large",
            )
    elif asset_count == 2:
        return PositionRect(
            x_percent=25, y_percent=5,
            width_percent=72, height_percent=80,
            z_index=base_rect.z_index, anchor="right_panel_wide",
        )
    else:
        # 3+ assets — nearly fullscreen grid
        return PositionRect(
            x_percent=10, y_percent=5,
            width_percent=85, height_percent=90,
            z_index=base_rect.z_index, anchor="grid_panel",
        )


def compute_asset_positions(
    assets_count: int,
    board_rect: PositionRect,
) -> list[PositionRect]:
    """Compute positions for assets within the board area.

    Layouts:
        1 asset  → centered in board
        2 assets → side by side
        3 assets → 1 top center + 2 bottom
        4+ assets → 2×2 grid
    """
    if assets_count == 0 or not board_rect.width_percent:
        return []

    bx = board_rect.x_percent
    by = board_rect.y_percent
    bw = board_rect.width_percent
    bh = board_rect.height_percent

    # Margins within the board (as % of board area)
    margin = 3.0

    if assets_count == 1:
        return [PositionRect(
            x_percent=bx + margin,
            y_percent=by + margin,
            width_percent=bw - (2 * margin),
            height_percent=bh * 0.65,
            z_index=5,
            anchor="board_center",
        )]

    elif assets_count == 2:
        half_w = (bw - (3 * margin)) / 2
        return [
            PositionRect(
                x_percent=bx + margin,
                y_percent=by + margin,
                width_percent=half_w,
                height_percent=bh * 0.60,
                z_index=5,
                anchor="board_left",
            ),
            PositionRect(
                x_percent=bx + (2 * margin) + half_w,
                y_percent=by + margin,
                width_percent=half_w,
                height_percent=bh * 0.60,
                z_index=5,
                anchor="board_right",
            ),
        ]

    elif assets_count == 3:
        half_w = (bw - (3 * margin)) / 2
        half_h = (bh * 0.7 - (2 * margin)) / 2
        return [
            # Top center
            PositionRect(
                x_percent=bx + bw / 4,
                y_percent=by + margin,
                width_percent=bw / 2,
                height_percent=half_h,
                z_index=5,
                anchor="board_top",
            ),
            # Bottom left
            PositionRect(
                x_percent=bx + margin,
                y_percent=by + margin + half_h + margin,
                width_percent=half_w,
                height_percent=half_h,
                z_index=5,
                anchor="grid_bottom_left",
            ),
            # Bottom right
            PositionRect(
                x_percent=bx + (2 * margin) + half_w,
                y_percent=by + margin + half_h + margin,
                width_percent=half_w,
                height_percent=half_h,
                z_index=5,
                anchor="grid_bottom_right",
            ),
        ]

    else:
        # 2×2 grid for 4+ assets (extras get positions cycled)
        half_w = (bw - (3 * margin)) / 2
        half_h = (bh * 0.7 - (2 * margin)) / 2
        grid_positions = [
            PositionRect(
                x_percent=bx + margin,
                y_percent=by + margin,
                width_percent=half_w,
                height_percent=half_h,
                z_index=5,
                anchor="grid_top_left",
            ),
            PositionRect(
                x_percent=bx + (2 * margin) + half_w,
                y_percent=by + margin,
                width_percent=half_w,
                height_percent=half_h,
                z_index=5,
                anchor="grid_top_right",
            ),
            PositionRect(
                x_percent=bx + margin,
                y_percent=by + margin + half_h + margin,
                width_percent=half_w,
                height_percent=half_h,
                z_index=5,
                anchor="grid_bottom_left",
            ),
            PositionRect(
                x_percent=bx + (2 * margin) + half_w,
                y_percent=by + margin + half_h + margin,
                width_percent=half_w,
                height_percent=half_h,
                z_index=5,
                anchor="grid_bottom_right",
            ),
        ]
        # Repeat grid positions if more than 4 assets
        result = []
        for i in range(assets_count):
            result.append(grid_positions[i % 4])
        return result


def compute_keyword_positions(
    count: int,
    board_rect: PositionRect,
) -> list[PositionRect]:
    """Compute evenly-spaced keyword badge positions across the top of the board."""
    if count == 0 or not board_rect.width_percent:
        return []

    bx = board_rect.x_percent
    bw = board_rect.width_percent
    by = board_rect.y_percent
    badge_h = 4.0  # 4% of viewport height
    margin = 2.0

    # Evenly space badges across the top
    usable_width = bw - (2 * margin)
    badge_w = min(usable_width / count - 1, 15.0)  # cap at 15% width

    positions = []
    for i in range(count):
        x = bx + margin + i * (badge_w + 1)
        positions.append(PositionRect(
            x_percent=round(x, 1),
            y_percent=round(by + margin, 1),
            width_percent=round(badge_w, 1),
            height_percent=badge_h,
            z_index=8,
            anchor="board_top",
        ))

    return positions


def compute_script_text_position(
    board_rect: PositionRect,
    show: bool,
    position: str = "bottom",
) -> PositionRect:
    """Compute the position of the script text area."""
    if not show:
        return PositionRect(
            x_percent=0, y_percent=0, width_percent=0, height_percent=0,
            z_index=0, anchor="hidden",
        )

    bx = board_rect.x_percent
    bw = board_rect.width_percent
    bh = board_rect.height_percent
    margin = 3.0
    text_h = 12.0

    if position == "bottom":
        return PositionRect(
            x_percent=round(bx + margin, 1),
            y_percent=round(100 - text_h - margin, 1),
            width_percent=round(bw - (2 * margin), 1),
            height_percent=round(text_h, 1),
            z_index=12,
            anchor="board_bottom",
        )
    elif position == "top":
        return PositionRect(
            x_percent=round(bx + margin, 1),
            y_percent=round(margin, 1),
            width_percent=round(bw - (2 * margin), 1),
            height_percent=round(text_h, 1),
            z_index=12,
            anchor="board_top",
        )
    elif position == "overlay_center":
        return PositionRect(
            x_percent=round(bx + bw * 0.1, 1),
            y_percent=round(bh * 0.35, 1),
            width_percent=round(bw * 0.8, 1),
            height_percent=round(text_h * 1.5, 1),
            z_index=15,
            anchor="center_overlay",
        )
    elif position == "side_panel":
        return PositionRect(
            x_percent=round(bx + bw + 2, 1),
            y_percent=round(20, 1),
            width_percent=round(min(100 - bx - bw - 4, 25), 1),
            height_percent=round(60, 1),
            z_index=12,
            anchor="side_panel",
        )
    else:
        # Default to bottom
        return PositionRect(
            x_percent=round(bx + margin, 1),
            y_percent=round(100 - text_h - margin, 1),
            width_percent=round(bw - (2 * margin), 1),
            height_percent=round(text_h, 1),
            z_index=12,
            anchor="board_bottom",
        )
