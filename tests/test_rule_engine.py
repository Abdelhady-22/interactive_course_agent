"""Tests for the rule engine."""

from app.schemas.inputs import NormalizedAsset, NormalizedKeyword, NormalizedParagraph
from app.schemas.enums import LayoutMode
from app.services.rule_engine import evaluate_rules


def _make_paragraph(text: str, keywords: list[str] = None, assets: list[dict] = None) -> NormalizedParagraph:
    """Helper to create a test paragraph."""
    kws = [NormalizedKeyword(word=kw, type="main") for kw in (keywords or [])]
    asset_list = [
        NormalizedAsset(id=f"a{i}", type=a.get("type", "image"), name=a.get("name", ""), description="")
        for i, a in enumerate(assets or [])
    ]
    return NormalizedParagraph(
        id="test", index=0, start_ms=0, end_ms=10000,
        text=text, keywords=kws, assets=asset_list,
    )


class TestGreetingRule:
    def test_greeting_detected(self):
        p = _make_paragraph("Welcome back! In this video, our objective is to explain...")
        result = evaluate_rules(p)
        assert result.matched
        assert result.layout_mode == LayoutMode.INSTRUCTOR_ONLY
        assert result.confidence >= 0.90

    def test_greeting_with_assets(self):
        p = _make_paragraph("Welcome to the course!", assets=[{"type": "image", "name": "plant"}])
        result = evaluate_rules(p)
        assert result.matched
        assert result.layout_mode == LayoutMode.INSTRUCTOR_DOMINANT
        assert result.confidence < 0.85  # Low enough for LLM review


class TestSummaryRule:
    def test_summary_detected(self):
        p = _make_paragraph("Let's recap what we've learned today. In summary, the key takeaways are...")
        result = evaluate_rules(p)
        assert result.matched
        assert result.layout_mode == LayoutMode.INSTRUCTOR_ONLY
        assert result.confidence >= 0.90


class TestMultiAssetRule:
    def test_three_assets_triggers_grid(self):
        p = _make_paragraph("Compare these three images", assets=[
            {"type": "image", "name": "a"}, {"type": "image", "name": "b"}, {"type": "diagram", "name": "c"},
        ])
        result = evaluate_rules(p)
        assert result.matched
        assert result.layout_mode == LayoutMode.MULTI_ASSET_GRID


class TestFormulaRule:
    def test_formula_asset_detected(self):
        p = _make_paragraph("Look at this equation", assets=[{"type": "formula", "name": "eq"}])
        result = evaluate_rules(p)
        assert result.matched
        assert result.layout_mode == LayoutMode.BOARD_DOMINANT

    def test_formula_keyword_detected(self):
        p = _make_paragraph("The chemical equation shows Zn + 2HCl → ZnCl₂", assets=[{"type": "image", "name": "x"}])
        result = evaluate_rules(p)
        assert result.matched
        assert result.layout_mode == LayoutMode.BOARD_DOMINANT


class TestSingleVisualRule:
    def test_single_image(self):
        p = _make_paragraph("This diagram shows the process", assets=[{"type": "diagram", "name": "flow"}])
        result = evaluate_rules(p)
        assert result.matched
        assert result.layout_mode in (LayoutMode.BOARD_DOMINANT, LayoutMode.FULLSCREEN_ASSET)

    def test_fullscreen_for_detailed_image(self):
        p = _make_paragraph("A close-up photograph of the zinc surface under microscope",
                            assets=[{"type": "image", "name": "zinc"}])
        result = evaluate_rules(p)
        assert result.matched
        assert result.layout_mode == LayoutMode.FULLSCREEN_ASSET


class TestChartRule:
    def test_chart_detected(self):
        p = _make_paragraph("The chart shows reaction rate data", assets=[{"type": "chart", "name": "rate"}])
        result = evaluate_rules(p)
        assert result.matched
        assert result.layout_mode == LayoutMode.SPLIT_50_50

    def test_multiple_charts(self):
        p = _make_paragraph("Comparing chart data", assets=[
            {"type": "chart", "name": "a"}, {"type": "image", "name": "b"},
        ])
        result = evaluate_rules(p)
        assert result.matched
        assert result.layout_mode == LayoutMode.SPLIT_60_40


class TestNoRuleMatch:
    def test_ambiguous_paragraph(self):
        p = _make_paragraph("The Industrial Revolution changed chemical manufacturing forever.")
        result = evaluate_rules(p)
        assert not result.matched
