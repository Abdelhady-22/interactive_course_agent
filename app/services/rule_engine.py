"""Rule engine — 6 deterministic rules evaluated in priority order."""

from __future__ import annotations

import re
from functools import lru_cache

from app.schemas.enums import LayoutMode
from app.schemas.inputs import NormalizedParagraph
from app.schemas.internals import RuleResult
from app.utils.logger import logger

# ── Keyword lists for pattern matching ──

_GREETING_KEYWORDS = {
    "welcome", "hello", "introduction", "intro", "greeting",
    "welcome back", "good morning", "good afternoon", "good evening",
    "in this video", "in this course", "in this lesson", "our objective",
}

_SUMMARY_KEYWORDS = {
    "summary", "recap", "conclusion", "takeaway", "key takeaways",
    "let's recap", "to summarize", "in conclusion", "wrapping up",
    "what we learned", "to sum up", "in summary", "final thoughts",
}

_FORMULA_KEYWORDS = {
    "formula", "equation", "chemical equation", "balanced equation",
    "mathematical", "expression", "derivation", "calculation",
}

_DETAIL_IMAGE_KEYWORDS = {
    "close-up", "photograph", "detailed", "microscope", "zoom",
    "high-resolution", "detailed view", "macro", "magnified",
}

_CHART_KEYWORDS = {
    "chart", "graph", "data", "plot", "statistics", "trend",
    "rate", "percentage", "comparison", "table", "histogram",
}


def evaluate_rules(paragraph: NormalizedParagraph) -> RuleResult:
    """Evaluate all 6 rules in priority order. Returns first match or no-match."""
    rules = [
        _rule_greeting,
        _rule_summary,
        _rule_multi_asset,
        _rule_formula,
        _rule_single_visual,
        _rule_chart,
    ]

    for rule_fn in rules:
        result = rule_fn(paragraph)
        if result.matched:
            logger.info(
                "Rule '%s' matched paragraph '%s' → %s (confidence=%.2f)",
                result.rule_name, paragraph.id, result.layout_mode, result.confidence,
            )
            return result

    logger.info("No rule matched paragraph '%s' — will use LLM", paragraph.id)
    return RuleResult(matched=False)


def _text_contains_any(text: str, keywords: set[str]) -> bool:
    """Check if text contains any of the keywords using word-boundary matching."""
    text_lower = text.lower()
    for kw in keywords:
        # Use word boundary for single words, substring for multi-word phrases
        if " " in kw:
            if kw in text_lower:
                return True
        else:
            pattern = r'\b' + re.escape(kw) + r'\b'
            if re.search(pattern, text_lower):
                return True
    return False


def _paragraph_keywords_contain(paragraph: NormalizedParagraph, keywords: set[str]) -> bool:
    """Check if paragraph's keyword list contains any matching keywords."""
    return any(kw.word.lower() in keywords for kw in paragraph.keywords)


def _has_assets(paragraph: NormalizedParagraph) -> bool:
    return len(paragraph.assets) > 0


def _asset_types(paragraph: NormalizedParagraph) -> set[str]:
    return {a.type.lower() for a in paragraph.assets}


# ── Rule 1: Greeting / Introduction ──

def _rule_greeting(p: NormalizedParagraph) -> RuleResult:
    """Greeting/intro with no assets → instructor_only."""
    if not _text_contains_any(p.text, _GREETING_KEYWORDS):
        return RuleResult(matched=False)

    # If there are assets, this might not be a pure greeting
    if _has_assets(p):
        return RuleResult(
            matched=True,
            rule_name="greeting_with_assets",
            layout_mode=LayoutMode.INSTRUCTOR_DOMINANT,
            confidence=0.78,
            reason="Greeting/intro detected but paragraph has assets — instructor dominant with small overlay.",
            suggested_assets=[a.id for a in p.assets[:1]],
        )

    return RuleResult(
        matched=True,
        rule_name="greeting",
        layout_mode=LayoutMode.INSTRUCTOR_ONLY,
        confidence=0.95,
        reason="Greeting/introduction detected. Instructor fills the screen to build personal connection.",
    )


# ── Rule 2: Summary / Recap ──

def _rule_summary(p: NormalizedParagraph) -> RuleResult:
    """Summary/recap → instructor_only."""
    if not _text_contains_any(p.text, _SUMMARY_KEYWORDS):
        return RuleResult(matched=False)

    if _has_assets(p):
        return RuleResult(
            matched=True,
            rule_name="summary_with_assets",
            layout_mode=LayoutMode.INSTRUCTOR_DOMINANT,
            confidence=0.80,
            reason="Summary detected with assets — instructor dominant, assets as small reference.",
            suggested_assets=[a.id for a in p.assets[:1]],
        )

    return RuleResult(
        matched=True,
        rule_name="summary",
        layout_mode=LayoutMode.INSTRUCTOR_ONLY,
        confidence=0.95,
        reason="Summary/recap detected. Instructor wraps up — full screen, no distractions.",
    )


# ── Rule 3: Multiple Assets (≥3) ──

def _rule_multi_asset(p: NormalizedParagraph) -> RuleResult:
    """3+ assets → multi_asset_grid."""
    if len(p.assets) < 3:
        return RuleResult(matched=False)

    return RuleResult(
        matched=True,
        rule_name="multi_asset",
        layout_mode=LayoutMode.MULTI_ASSET_GRID,
        confidence=0.88,
        reason=f"Multiple assets ({len(p.assets)}) detected — grid layout for comparison.",
        suggested_assets=[a.id for a in p.assets],
    )


# ── Rule 4: Formula Detected ──

def _rule_formula(p: NormalizedParagraph) -> RuleResult:
    """Formula asset or formula keywords → board_dominant."""
    types = _asset_types(p)
    has_formula_asset = "formula" in types
    has_formula_keywords = (
        _text_contains_any(p.text, _FORMULA_KEYWORDS)
        or _paragraph_keywords_contain(p, _FORMULA_KEYWORDS)
    )

    # Also detect formulas by content patterns (e.g., → symbols, subscripts)
    has_formula_pattern = bool(re.search(r"[→=+]\s*\w+", p.text))

    if not (has_formula_asset or has_formula_keywords or has_formula_pattern):
        return RuleResult(matched=False)

    formula_assets = [a.id for a in p.assets if a.type.lower() == "formula"]
    all_assets = [a.id for a in p.assets]

    return RuleResult(
        matched=True,
        rule_name="formula",
        layout_mode=LayoutMode.BOARD_DOMINANT,
        confidence=0.90,
        reason="Formula content detected — board takes 70% to display formula prominently.",
        suggested_assets=formula_assets or all_assets,
    )


# ── Rule 5: Single Image / Diagram ──

def _rule_single_visual(p: NormalizedParagraph) -> RuleResult:
    """Single image or diagram → board_dominant or fullscreen_asset."""
    if len(p.assets) != 1:
        return RuleResult(matched=False)

    asset = p.assets[0]
    atype = asset.type.lower()

    if atype not in ("image", "diagram", "infographic"):
        return RuleResult(matched=False)

    # Check if the image deserves fullscreen (high-detail keywords)
    is_detail = _text_contains_any(p.text, _DETAIL_IMAGE_KEYWORDS)

    if is_detail:
        return RuleResult(
            matched=True,
            rule_name="single_visual_fullscreen",
            layout_mode=LayoutMode.FULLSCREEN_ASSET,
            confidence=0.83,
            reason=f"Detailed {atype} — fullscreen for maximum visual impact.",
            suggested_assets=[asset.id],
        )

    return RuleResult(
        matched=True,
        rule_name="single_visual",
        layout_mode=LayoutMode.BOARD_DOMINANT,
        confidence=0.85,
        reason=f"Single {atype} asset — board dominant with instructor as PiP.",
        suggested_assets=[asset.id],
    )


# ── Rule 6: Chart / Graph ──

def _rule_chart(p: NormalizedParagraph) -> RuleResult:
    """Chart/graph content → split layouts."""
    types = _asset_types(p)
    has_chart_asset = "chart" in types
    has_chart_keywords = _text_contains_any(p.text, _CHART_KEYWORDS)

    if not (has_chart_asset or has_chart_keywords):
        return RuleResult(matched=False)

    chart_assets = [a.id for a in p.assets if a.type.lower() == "chart"]
    all_assets = [a.id for a in p.assets]

    # Multiple charts → 60/40, single chart → 50/50
    if len(p.assets) >= 2:
        return RuleResult(
            matched=True,
            rule_name="chart_multiple",
            layout_mode=LayoutMode.SPLIT_60_40,
            confidence=0.85,
            reason="Multiple data visuals — 60/40 split gives charts more room.",
            suggested_assets=chart_assets or all_assets,
        )

    return RuleResult(
        matched=True,
        rule_name="chart_single",
        layout_mode=LayoutMode.SPLIT_50_50,
        confidence=0.85,
        reason="Chart/graph detected — equal split for balanced data analysis.",
        suggested_assets=chart_assets or all_assets,
    )
