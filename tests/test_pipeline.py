"""End-to-end pipeline tests with mocked LLM."""

import json
from unittest.mock import patch, MagicMock

import pytest

from app.config import Settings
from app.services.pipeline import Pipeline
from app.schemas.enums import LayoutMode, DecisionSource
from app.schemas.outputs import TokenUsage


@pytest.fixture
def pipeline_settings():
    """Settings with LLM review disabled for unit tests."""
    return Settings(
        llm_provider="ollama",
        llm_model="glm-5:cloud",
        enable_llm_review=False,
    )


@pytest.fixture
def pipeline_settings_with_review():
    """Settings with LLM review enabled."""
    return Settings(
        llm_provider="ollama",
        llm_model="glm-5:cloud",
        enable_llm_review=True,
        review_confidence_threshold=0.85,
    )


class TestPipelineRulesOnly:
    """Test pipeline with rules only (no LLM calls)."""

    def test_greeting_paragraph_gets_instructor_only(self, pipeline_settings):
        pipeline = Pipeline(pipeline_settings)
        result = pipeline.process_transcript(
            raw_input=[{
                "startTime": 0, "endTime": 15,
                "id": 1,
                "text": "Welcome back! In this video, our objective is to explain cement production.",
                "keywords": [{"word": "cement production", "type": "main"}],
                "wordTimestamps": [],
                "visual": None,
            }],
            review_rules=False,
        )
        assert result.total_paragraphs == 1
        decision = result.decisions[0]
        assert decision.layout.mode == LayoutMode.INSTRUCTOR_ONLY
        assert decision.decided_by == DecisionSource.RULE
        assert decision.confidence >= 0.90

    def test_formula_paragraph_gets_board_dominant(self, pipeline_settings):
        pipeline = Pipeline(pipeline_settings)
        result = pipeline.process_transcript(
            raw_input=[{
                "startTime": 0, "endTime": 30,
                "id": 1,
                "text": "The chemical equation for this reaction is critical to understand.",
                "keywords": [{"word": "chemical equation", "type": "main"}],
                "wordTimestamps": [],
                "visual": {
                    "type": "formula",
                    "src": "",
                    "title": "Reaction Equation",
                    "alt": "Zinc reacts with HCl",
                    "startTime": 0,
                    "assist_image_id": "f-001",
                },
            }],
            review_rules=False,
        )
        decision = result.decisions[0]
        assert decision.layout.mode == LayoutMode.BOARD_DOMINANT

    def test_multiple_paragraphs_get_different_assets(self, pipeline_settings):
        pipeline = Pipeline(pipeline_settings)
        result = pipeline.process_transcript(
            raw_input=[
                {
                    "startTime": 0, "endTime": 20,
                    "id": 1,
                    "text": "Let's examine the chemical equation for this process.",
                    "keywords": [],
                    "wordTimestamps": [],
                    "visual": {"type": "image", "src": "a.jpg", "title": "Image A", "alt": "", "startTime": 0, "assist_image_id": "a1"},
                },
                {
                    "startTime": 20, "endTime": 40,
                    "id": 2,
                    "text": "Now look at this chart data that shows reaction rates.",
                    "keywords": [],
                    "wordTimestamps": [],
                    "visual": {"type": "chart", "src": "b.jpg", "title": "Chart B", "alt": "", "startTime": 20, "assist_image_id": "b2"},
                },
            ],
            review_rules=False,
        )
        assert result.total_paragraphs == 2
        # Each paragraph should have its OWN asset
        d0_ids = [a.id for a in result.decisions[0].assets]
        d1_ids = [a.id for a in result.decisions[1].assets]
        assert d0_ids != d1_ids

    def test_stats_are_computed(self, pipeline_settings):
        pipeline = Pipeline(pipeline_settings)
        result = pipeline.process_transcript(
            raw_input=[{
                "startTime": 0, "endTime": 15,
                "id": 1,
                "text": "Welcome! This is an introductory lesson.",
                "keywords": [],
                "wordTimestamps": [],
                "visual": None,
            }],
            review_rules=False,
        )
        assert result.stats.decided_by_rule >= 1
        assert result.stats.processing_time_ms > 0

    def test_position_rects_are_valid(self, pipeline_settings):
        pipeline = Pipeline(pipeline_settings)
        result = pipeline.process_transcript(
            raw_input=[{
                "startTime": 0, "endTime": 30,
                "id": 1,
                "text": "This diagram shows the production process.",
                "keywords": [{"word": "production", "type": "main"}],
                "wordTimestamps": [],
                "visual": {"type": "diagram", "src": "d.jpg", "title": "Process Diagram", "alt": "", "startTime": 0, "assist_image_id": "d1"},
            }],
            review_rules=False,
        )
        decision = result.decisions[0]
        # Instructor should have a valid position_rect
        pos = decision.layout.instructor.position_rect
        assert 0 <= pos.x_percent <= 100
        assert 0 <= pos.y_percent <= 100
        # Board should have a valid position_rect
        board_pos = decision.layout.board.position_rect
        assert board_pos.width_percent > 0


class TestPipelineStructuredInput:
    """Test pipeline with structured input format."""

    def test_structured_input_works(self, pipeline_settings):
        pipeline = Pipeline(pipeline_settings)
        result = pipeline.process_transcript(
            raw_input={
                "video_context": {"description": "Chemistry course"},
                "paragraph": {
                    "id": "p_014",
                    "start_ms": 142300,
                    "end_ms": 158700,
                    "text": "The chemical equation shows the reaction.",
                    "keywords": ["chemical equation"],
                },
                "assets": [
                    {"id": "a1", "type": "formula", "name": "reaction", "description": "Zn + HCl"},
                ],
            },
            review_rules=False,
        )
        assert result.total_paragraphs == 1


class TestPipelineForceLLM:
    """Test force_llm_paragraphs parameter."""

    @patch("app.services.pipeline.Pipeline._call_director")
    def test_force_llm_bypasses_rules(self, mock_director, pipeline_settings):
        mock_director.return_value = (
            LayoutMode.SPLIT_50_50, 0.85,
            "LLM decided split layout", [],
            TokenUsage(prompt_tokens=100, completion_tokens=50),
        )

        pipeline = Pipeline(pipeline_settings)
        result = pipeline.process_transcript(
            raw_input=[{
                "startTime": 0, "endTime": 15,
                "id": 1,
                "text": "Welcome! This is an introduction.",
                "keywords": [],
                "wordTimestamps": [],
                "visual": None,
            }],
            force_llm_paragraphs=[1],
            review_rules=False,
        )

        decision = result.decisions[0]
        assert decision.decided_by == DecisionSource.LLM
        mock_director.assert_called_once()


class TestPipelineContinuity:
    """Test sequence detection and instructor pinning."""

    def test_consecutive_assets_form_sequence(self, pipeline_settings):
        pipeline = Pipeline(pipeline_settings)
        result = pipeline.process_transcript(
            raw_input=[
                {
                    "startTime": 0, "endTime": 20, "id": 1,
                    "text": "Look at this photograph showing the process.",
                    "keywords": [], "wordTimestamps": [],
                    "visual": {"type": "image", "src": "a.jpg", "title": "A", "alt": "", "startTime": 0, "assist_image_id": "a1"},
                },
                {
                    "startTime": 20, "endTime": 40, "id": 2,
                    "text": "This diagram shows another step.",
                    "keywords": [], "wordTimestamps": [],
                    "visual": {"type": "diagram", "src": "b.jpg", "title": "B", "alt": "", "startTime": 20, "assist_image_id": "b2"},
                },
                {
                    "startTime": 40, "endTime": 60, "id": 3,
                    "text": "The chart shows rate data here.",
                    "keywords": [], "wordTimestamps": [],
                    "visual": {"type": "chart", "src": "c.jpg", "title": "C", "alt": "", "startTime": 40, "assist_image_id": "c3"},
                },
            ],
            review_rules=False,
        )
        # Paragraphs 0,1,2 all have assets → should be a sequence
        for d in result.decisions:
            assert d.continuity.sequence_length == 3
