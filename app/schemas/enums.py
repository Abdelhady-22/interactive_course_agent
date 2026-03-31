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


# ── V2 Enhancement Enums ──


class PipShape(str, Enum):
    """Instructor PiP overlay shape."""

    CIRCLE = "circle"
    ROUNDED_RECT = "rounded_rect"
    SQUARE = "square"
    HEXAGON = "hexagon"


class PipBorder(str, Enum):
    """PiP border style."""

    NONE = "none"
    THIN_WHITE = "thin_white"
    GLOW_BLUE = "glow_blue"
    GLOW_GOLD = "glow_gold"
    GRADIENT = "gradient"


class AnimationType(str, Enum):
    """Entrance/exit animation types for assets and keywords."""

    NONE = "none"
    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    SLIDE_UP = "slide_up"
    SLIDE_DOWN = "slide_down"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"
    SCALE_IN = "scale_in"
    SCALE_OUT = "scale_out"
    ZOOM_IN = "zoom_in"
    POP_IN = "pop_in"
    BOUNCE_IN = "bounce_in"


class ScriptPosition(str, Enum):
    """Where to display the script text."""

    BOTTOM = "bottom"
    TOP = "top"
    OVERLAY_CENTER = "overlay_center"
    SIDE_PANEL = "side_panel"
    HIDDEN = "hidden"


class ScriptStyle(str, Enum):
    """How to display the script text."""

    SUBTITLE = "subtitle"
    CAPTION = "caption"
    TELEPROMPTER = "teleprompter"
    KARAOKE = "karaoke"
    FULL_TEXT = "full_text"


class BoardBackground(str, Enum):
    """Board area background style."""

    TRANSPARENT = "transparent"
    SOLID_DARK = "solid_dark"
    SOLID_LIGHT = "solid_light"
    DARK_GRADIENT = "dark_gradient"
    GLASSMORPHISM = "glassmorphism"
    THEMED = "themed"


class InstructorEnergy(str, Enum):
    """Instructor behavior energy level."""

    CALM = "calm"
    NEUTRAL = "neutral"
    ENTHUSIASTIC = "enthusiastic"
    SERIOUS = "serious"
    EXCITED = "excited"


class InstructorGesture(str, Enum):
    """Suggested instructor gesture."""

    NONE = "none"
    POINTING_AT_BOARD = "pointing_at_board"
    HANDS_OPEN = "hands_open"
    COUNTING = "counting"
    EMPHASIZING = "emphasizing"
    WRITING = "writing"


class FocusTarget(str, Enum):
    """Where the learner should focus."""

    INSTRUCTOR = "instructor"
    BOARD = "board"
    ASSET = "asset"
    KEYWORD = "keyword"
    SPLIT = "split"
