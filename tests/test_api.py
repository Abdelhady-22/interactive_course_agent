"""Tests for the API endpoints."""

from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestRootAndHealth:
    def test_root(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Interactive Course Agent"
        assert "version" in data

    def test_health(self):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "llm" in data


class TestProcessTranscript:
    def test_flat_input_accepted(self, flat_input_sample):
        response = client.post("/api/process-transcript", json={
            "transcript": flat_input_sample,
            "force_llm_paragraphs": [],
            "review_rules": False,
        })
        # Should succeed (rules only, no LLM needed)
        assert response.status_code == 200
        data = response.json()
        assert "decisions" in data
        assert data["total_paragraphs"] == 2

    def test_structured_input_accepted(self, structured_input_sample):
        response = client.post("/api/process-transcript", json={
            "transcript": structured_input_sample,
            "review_rules": False,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["total_paragraphs"] == 1

    def test_decisions_have_position_rects(self, flat_input_sample):
        response = client.post("/api/process-transcript", json={
            "transcript": flat_input_sample,
            "review_rules": False,
        })
        data = response.json()
        decision = data["decisions"][0]

        # Layout positions
        assert "position_rect" in decision["layout"]["instructor"]
        inst_pos = decision["layout"]["instructor"]["position_rect"]
        assert "x_percent" in inst_pos
        assert "y_percent" in inst_pos
        assert "width_percent" in inst_pos
        assert "height_percent" in inst_pos
        assert "z_index" in inst_pos

    def test_each_paragraph_gets_own_asset(self, flat_input_sample):
        response = client.post("/api/process-transcript", json={
            "transcript": flat_input_sample,
            "review_rules": False,
        })
        data = response.json()
        d0_assets = data["decisions"][0]["assets"]
        d1_assets = data["decisions"][1]["assets"]

        # Each paragraph should have its own asset, not the same one
        if d0_assets and d1_assets:
            assert d0_assets[0]["id"] != d1_assets[0]["id"]

    def test_stats_included(self, flat_input_sample):
        response = client.post("/api/process-transcript", json={
            "transcript": flat_input_sample,
            "review_rules": False,
        })
        data = response.json()
        assert "stats" in data
        assert "decided_by_rule" in data["stats"]
        assert "processing_time_ms" in data["stats"]

    def test_invalid_input_returns_error(self):
        response = client.post("/api/process-transcript", json={
            "transcript": "not valid",
        })
        assert response.status_code == 422
