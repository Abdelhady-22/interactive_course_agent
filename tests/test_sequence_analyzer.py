"""Tests for the sequence analyzer."""

from app.schemas.inputs import NormalizedAsset, NormalizedParagraph
from app.schemas.enums import SequencePosition
from app.services.sequence_analyzer import analyze_sequences


def _make_paragraphs(has_assets_list: list[bool]) -> list[NormalizedParagraph]:
    """Create test paragraphs with or without assets."""
    paragraphs = []
    for i, has in enumerate(has_assets_list):
        assets = [NormalizedAsset(id=f"a{i}", type="image", name=f"img{i}", description="")]if has else []
        paragraphs.append(NormalizedParagraph(
            id=f"p{i}", index=i,
            start_ms=i * 30000, end_ms=(i + 1) * 30000,
            text=f"Paragraph {i}", assets=assets,
        ))
    return paragraphs


class TestSequenceDetection:
    def test_no_sequences(self):
        paragraphs = _make_paragraphs([True, False, True, False])
        hints = analyze_sequences(paragraphs)
        assert all(not h.is_in_sequence for h in hints)

    def test_basic_sequence(self):
        paragraphs = _make_paragraphs([True, True, True, False])
        hints = analyze_sequences(paragraphs)
        assert hints[0].is_in_sequence
        assert hints[0].sequence_position == SequencePosition.START
        assert hints[1].sequence_position == SequencePosition.MIDDLE
        assert hints[2].sequence_position == SequencePosition.END
        assert not hints[3].is_in_sequence

    def test_sequence_length(self):
        paragraphs = _make_paragraphs([False, True, True, True, True, False])
        hints = analyze_sequences(paragraphs)
        assert hints[1].sequence_length == 4
        assert hints[4].sequence_length == 4

    def test_pinning(self):
        paragraphs = _make_paragraphs([True, True, True])
        hints = analyze_sequences(paragraphs)
        assert all(h.pin_instructor for h in hints)
        assert hints[0].sequence_start_paragraph_id == "p0"
        assert hints[2].sequence_start_paragraph_id == "p0"

    def test_all_standalone(self):
        paragraphs = _make_paragraphs([False, False, False])
        hints = analyze_sequences(paragraphs)
        assert len(hints) == 3
        assert all(not h.is_in_sequence for h in hints)

    def test_empty_input(self):
        hints = analyze_sequences([])
        assert hints == []

    def test_two_separate_sequences(self):
        paragraphs = _make_paragraphs([True, True, False, True, True, True])
        hints = analyze_sequences(paragraphs)
        assert hints[0].sequence_length == 2
        assert hints[3].sequence_length == 3
        assert not hints[2].is_in_sequence
