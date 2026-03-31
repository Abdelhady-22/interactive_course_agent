"""Enumerations — single source of truth for all valid values."""

from enum import Enum


class LayoutMode(str, Enum):
    """The 14 supported screen layout modes."""

    INSTRUCTOR_ONLY = "instructor_only"
    BOARD_ONLY = "board_only"
    BOARD_DOMINANT = "board_dominant"
    INSTRUCTOR_DOMINANT = "instructor_dominant"
    SPLIT_50_50 = "split_50_50"
    SPLIT_60_40 = "split_60_40"
    INSTRUCTOR_PIP = "instructor_pip"
    PICTURE_IN_PICTURE_LARGE = "picture_in_picture_large"
    INSTRUCTOR_BEHIND_BOARD = "instructor_behind_board"
    OVERLAY_FLOATING = "overlay_floating"
    BOARD_WITH_SIDE_STRIP = "board_with_side_strip"
    MULTI_ASSET_GRID = "multi_asset_grid"
    FULLSCREEN_ASSET = "fullscreen_asset"
    STACKED_VERTICAL = "stacked_vertical"


class TransitionType(str, Enum):
    """Transition effects between layouts."""

    FADE = "fade"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"
    CUT = "cut"
    DISSOLVE = "dissolve"
    NONE = "none"


class AssetType(str, Enum):
    """Types of visual assets."""

    IMAGE = "image"
    FORMULA = "formula"
    DIAGRAM = "diagram"
    CHART = "chart"
    INFOGRAPHIC = "infographic"


class KeywordType(str, Enum):
    """Keyword classification types."""

    MAIN = "main"
    KEY_TERMS = "Key Terms"
    CALLOUTS = "Callouts"


class DecisionSource(str, Enum):
    """Who made the layout decision."""

    RULE = "rule"
    LLM = "llm"
    FALLBACK = "fallback"


class SequencePosition(str, Enum):
    """Position of a paragraph within a consecutive asset sequence."""

    STANDALONE = "standalone"
    START = "start"
    MIDDLE = "middle"
    END = "end"
