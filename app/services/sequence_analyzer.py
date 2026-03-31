"""Sequence analyzer — detects consecutive asset paragraphs and generates continuity hints."""

from __future__ import annotations

from app.schemas.enums import SequencePosition
from app.schemas.inputs import NormalizedParagraph
from app.schemas.internals import ContinuityHint
from app.schemas.outputs import PositionRect
from app.utils.logger import logger

# Minimum consecutive paragraphs with assets to form a "sequence"
_MIN_SEQUENCE_LENGTH = 2


def analyze_sequences(paragraphs: list[NormalizedParagraph]) -> list[ContinuityHint]:
    """Scan all paragraphs and produce a ContinuityHint for each.

    A "sequence" is a run of consecutive paragraphs that all have visual assets.
    Within a sequence, the instructor gets pinned in a consistent position.
    """
    n = len(paragraphs)
    if n == 0:
        return []

    # Step 1: mark which paragraphs have assets
    has_assets = [len(p.assets) > 0 for p in paragraphs]

    # Step 2: find consecutive runs of asset-bearing paragraphs
    sequences: list[tuple[int, int]] = []  # (start_idx, end_idx) inclusive
    i = 0
    while i < n:
        if has_assets[i]:
            j = i
            while j < n and has_assets[j]:
                j += 1
            run_length = j - i
            if run_length >= _MIN_SEQUENCE_LENGTH:
                sequences.append((i, j - 1))
            i = j
        else:
            i += 1

    # Step 3: build a lookup: paragraph_index → (sequence_idx, position_in_seq)
    seq_lookup: dict[int, tuple[int, SequencePosition, int]] = {}
    for seq_idx, (start, end) in enumerate(sequences):
        seq_len = end - start + 1
        for k in range(start, end + 1):
            if k == start:
                pos = SequencePosition.START
            elif k == end:
                pos = SequencePosition.END
            else:
                pos = SequencePosition.MIDDLE
            seq_lookup[k] = (seq_idx, pos, seq_len)

    # Step 4: determine pin position based on dominant asset types in each sequence
    seq_pin_positions: dict[int, PositionRect] = {}
    for seq_idx, (start, end) in enumerate(sequences):
        seq_pin_positions[seq_idx] = _compute_pin_position(paragraphs[start:end + 1])

    # Step 5: generate hints
    hints: list[ContinuityHint] = []
    for idx in range(n):
        if idx in seq_lookup:
            seq_idx, position, seq_len = seq_lookup[idx]
            start_para_id = paragraphs[sequences[seq_idx][0]].id
            pin_rect = seq_pin_positions[seq_idx]

            hints.append(ContinuityHint(
                is_in_sequence=True,
                sequence_position=position,
                sequence_length=seq_len,
                sequence_start_paragraph_id=start_para_id,
                pin_instructor=True,
                pin_position=pin_rect,
                pin_size="small",
                pin_style="pip",
            ))
        else:
            hints.append(ContinuityHint(is_in_sequence=False))

    _log_sequences(paragraphs, sequences)
    return hints


def _compute_pin_position(sequence_paragraphs: list[NormalizedParagraph]) -> PositionRect:
    """Determine the best instructor pin position for a sequence.

    Based on the dominant asset types:
    - Diagrams, formulas, images → bottom_right (small PiP, out of the way)
    - Charts, infographics → right side (medium, for data discussion)
    """
    asset_types: set[str] = set()
    for p in sequence_paragraphs:
        for a in p.assets:
            asset_types.add(a.type.lower())

    if asset_types & {"chart", "infographic"}:
        # Charts need instructor visible for explanation
        return PositionRect(
            x_percent=72.0, y_percent=60.0,
            width_percent=25.0, height_percent=35.0,
            z_index=10, anchor="right",
        )
    else:
        # Default: small PiP in bottom-right corner
        return PositionRect(
            x_percent=72.0, y_percent=72.0,
            width_percent=25.0, height_percent=25.0,
            z_index=10, anchor="bottom_right",
        )


def _log_sequences(
    paragraphs: list[NormalizedParagraph],
    sequences: list[tuple[int, int]],
) -> None:
    """Log detected sequences for debugging."""
    if not sequences:
        logger.info("No asset sequences detected (all paragraphs are standalone)")
        return

    for seq_idx, (start, end) in enumerate(sequences):
        para_ids = [paragraphs[i].id for i in range(start, end + 1)]
        logger.info(
            "Sequence %d: paragraphs %d-%d (%d paragraphs) IDs=%s",
            seq_idx + 1, start, end, end - start + 1, para_ids,
        )
