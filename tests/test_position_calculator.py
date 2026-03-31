"""Tests for the position calculator."""

from app.schemas.enums import LayoutMode
from app.schemas.outputs import PositionRect
from app.services.position_calculator import (
    compute_layout_positions,
    compute_asset_positions,
    compute_keyword_positions,
    compute_script_text_position,
)


class TestLayoutPositions:
    def test_instructor_only(self):
        inst, board = compute_layout_positions(LayoutMode.INSTRUCTOR_ONLY)
        assert inst.visible is True
        assert inst.position_rect.width_percent == 100
        assert board.visible is False

    def test_board_dominant(self):
        inst, board = compute_layout_positions(LayoutMode.BOARD_DOMINANT)
        assert inst.visible is True
        assert inst.size == "small"
        assert inst.style == "pip"
        assert inst.position_rect.anchor == "bottom_right"
        assert board.visible is True
        assert board.position_rect.width_percent == 70

    def test_split_50_50(self):
        inst, board = compute_layout_positions(LayoutMode.SPLIT_50_50)
        assert inst.position_rect.width_percent == 50
        assert board.position_rect.width_percent == 50

    def test_fullscreen_asset_hides_instructor(self):
        inst, board = compute_layout_positions(LayoutMode.FULLSCREEN_ASSET)
        assert inst.visible is False
        assert board.visible is True
        assert board.position_rect.width_percent == 100

    def test_all_modes_produce_valid_positions(self):
        for mode in LayoutMode:
            inst, board = compute_layout_positions(mode)
            if inst.visible:
                assert 0 <= inst.position_rect.x_percent <= 100
                assert 0 <= inst.position_rect.y_percent <= 100

    def test_behind_board_opacity(self):
        inst, board = compute_layout_positions(LayoutMode.INSTRUCTOR_BEHIND_BOARD)
        assert inst.opacity == 0.3
        assert inst.style == "semi_transparent"


class TestAssetPositions:
    def _board(self):
        return PositionRect(x_percent=0, y_percent=0, width_percent=70, height_percent=100, z_index=1, anchor="left")

    def test_single_asset(self):
        positions = compute_asset_positions(1, self._board())
        assert len(positions) == 1
        assert positions[0].anchor == "board_center"

    def test_two_assets_side_by_side(self):
        positions = compute_asset_positions(2, self._board())
        assert len(positions) == 2
        assert positions[0].x_percent < positions[1].x_percent

    def test_four_assets_grid(self):
        positions = compute_asset_positions(4, self._board())
        assert len(positions) == 4

    def test_zero_assets(self):
        positions = compute_asset_positions(0, self._board())
        assert positions == []


class TestKeywordPositions:
    def _board(self):
        return PositionRect(x_percent=0, y_percent=0, width_percent=70, height_percent=100, z_index=1, anchor="left")

    def test_keywords_spaced(self):
        positions = compute_keyword_positions(3, self._board())
        assert len(positions) == 3
        # Each keyword should be to the right of the previous
        for i in range(1, len(positions)):
            assert positions[i].x_percent > positions[i - 1].x_percent

    def test_zero_keywords(self):
        positions = compute_keyword_positions(0, self._board())
        assert positions == []


class TestScriptTextPosition:
    def _board(self):
        return PositionRect(x_percent=0, y_percent=0, width_percent=70, height_percent=100, z_index=1, anchor="left")

    def test_visible_text(self):
        pos = compute_script_text_position(self._board(), 0.5)
        assert pos.width_percent > 0
        assert pos.anchor == "board_bottom"

    def test_hidden_text(self):
        pos = compute_script_text_position(self._board(), 0.0)
        assert pos.width_percent == 0
