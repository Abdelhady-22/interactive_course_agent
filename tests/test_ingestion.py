"""Tests for the ingestion service."""

from app.services.ingestion import ingest_transcript


class TestFlatIngestion:
    """Tests for flat-array input format."""

    def test_ingest_flat_array(self, flat_input_sample):
        result = ingest_transcript(flat_input_sample)
        assert len(result.paragraphs) == 2

    def test_paragraph_timestamps_converted(self, flat_input_sample):
        result = ingest_transcript(flat_input_sample)
        p = result.paragraphs[0]
        assert p.start_ms == 0
        assert p.end_ms == 28520  # 28.52 * 1000

    def test_visual_extracted_as_asset(self, flat_input_sample):
        result = ingest_transcript(flat_input_sample)
        p = result.paragraphs[0]
        assert len(p.assets) == 1
        assert p.assets[0].name == "Industrial Cement Plant"
        assert p.assets[0].type == "image"

    def test_each_paragraph_gets_own_asset(self, flat_input_sample):
        result = ingest_transcript(flat_input_sample)
        assert result.paragraphs[0].assets[0].id != result.paragraphs[1].assets[0].id
        assert result.paragraphs[0].assets[0].name == "Industrial Cement Plant"
        assert result.paragraphs[1].assets[0].name == "Magnetite Rock Sample"

    def test_keywords_normalized(self, flat_input_sample):
        result = ingest_transcript(flat_input_sample)
        p = result.paragraphs[0]
        assert len(p.keywords) == 2
        assert p.keywords[0].word == "Cement production"
        assert p.keywords[0].type == "main"

    def test_word_timestamps_normalized(self, flat_input_sample):
        result = ingest_transcript(flat_input_sample)
        p = result.paragraphs[0]
        assert len(p.word_timestamps) == 2
        assert p.word_timestamps[0].word == "Welcome"
        assert p.word_timestamps[0].start_ms == 0
        assert p.word_timestamps[0].end_ms == 500


class TestStructuredIngestion:
    """Tests for structured input format."""

    def test_ingest_structured(self, structured_input_sample):
        result = ingest_transcript(structured_input_sample)
        assert len(result.paragraphs) == 1

    def test_structured_paragraph_has_assets(self, structured_input_sample):
        result = ingest_transcript(structured_input_sample)
        p = result.paragraphs[0]
        assert len(p.assets) == 1
        assert p.assets[0].type == "formula"
        assert p.assets[0].name == "reaction equation"

    def test_structured_keywords_are_strings(self, structured_input_sample):
        result = ingest_transcript(structured_input_sample)
        p = result.paragraphs[0]
        assert len(p.keywords) == 3
        assert p.keywords[0].word == "hydrochloric acid"

    def test_video_context_captured(self, structured_input_sample):
        result = ingest_transcript(structured_input_sample)
        assert "chemistry" in result.video_context.lower()


class TestAutoDetection:
    """Tests for format auto-detection."""

    def test_list_detected_as_flat(self, flat_input_sample):
        result = ingest_transcript(flat_input_sample)
        assert len(result.paragraphs) > 0

    def test_dict_detected_as_structured(self, structured_input_sample):
        result = ingest_transcript(structured_input_sample)
        assert len(result.paragraphs) > 0
