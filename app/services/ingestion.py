"""Ingestion service — parses and normalizes both input formats."""

from __future__ import annotations

import uuid
from typing import Any

from app.schemas.inputs import (
    FlatParagraphInput,
    KeywordInput,
    NormalizedAsset,
    NormalizedKeyword,
    NormalizedParagraph,
    NormalizedTranscript,
    NormalizedWordTimestamp,
    VisualInput,
)
from app.utils.errors import IngestionError
from app.utils.logger import logger


def ingest_transcript(raw_input: list[dict[str, Any]] | dict[str, Any]) -> NormalizedTranscript:
    """Auto-detect input format and normalize into a NormalizedTranscript.

    Supports:
        - Format A (flat array): list of paragraph dicts with embedded visual
        - Format B (structured): dict with video_context, paragraph/paragraphs, assets
    """
    try:
        if isinstance(raw_input, list):
            return _ingest_flat_array(raw_input)
        elif isinstance(raw_input, dict):
            return _ingest_structured(raw_input)
        else:
            raise IngestionError(f"Unsupported input type: {type(raw_input).__name__}")
    except IngestionError:
        raise
    except Exception as exc:
        logger.error("Ingestion failed: %s", exc)
        raise IngestionError(f"Failed to parse input: {exc}") from exc


def _ingest_flat_array(paragraphs_raw: list[dict[str, Any]]) -> NormalizedTranscript:
    """Parse Format A: a flat list of paragraphs with embedded visuals."""
    if not paragraphs_raw:
        raise IngestionError("Empty paragraph list")

    paragraphs: list[NormalizedParagraph] = []

    for idx, p_raw in enumerate(paragraphs_raw):
        try:
            flat = FlatParagraphInput(**p_raw)
        except Exception as exc:
            raise IngestionError(
                f"Invalid paragraph at index {idx}: {exc}",
                details={"index": idx},
            ) from exc

        # Convert seconds → milliseconds
        start_ms = int(flat.startTime * 1000)
        end_ms = int(flat.endTime * 1000)

        # Normalize keywords
        keywords = [
            NormalizedKeyword(word=kw.word, type=kw.type)
            for kw in flat.keywords
        ]

        # Normalize word timestamps
        word_timestamps = _normalize_word_timestamps(flat.wordTimestamps, start_ms)

        # Extract visual as an asset
        assets: list[NormalizedAsset] = []
        if flat.visual is not None:
            asset = _visual_to_asset(flat.visual)
            assets.append(asset)

        paragraphs.append(NormalizedParagraph(
            id=str(flat.id),
            index=idx,
            start_ms=start_ms,
            end_ms=end_ms,
            text=flat.text,
            keywords=keywords,
            word_timestamps=word_timestamps,
            assets=assets,
        ))

    logger.info("Ingested %d paragraphs (flat format)", len(paragraphs))
    return NormalizedTranscript(paragraphs=paragraphs)


def _ingest_structured(data: dict[str, Any]) -> NormalizedTranscript:
    """Parse Format B: structured dict with video_context, paragraphs, assets."""
    video_context = data.get("video_context", {}).get("description", "")

    # Support both single paragraph and multiple paragraphs
    paragraphs_raw = data.get("paragraphs", [])
    if not paragraphs_raw and "paragraph" in data:
        paragraphs_raw = [data["paragraph"]]

    if not paragraphs_raw:
        raise IngestionError("No paragraphs found in structured input")

    # Parse shared assets
    shared_assets = [
        NormalizedAsset(
            id=a.get("id", str(uuid.uuid4())),
            type=a.get("type", "image"),
            name=a.get("name", a.get("title", "")),
            description=a.get("description", a.get("alt", "")),
            content=a.get("content"),
            src=a.get("src", ""),
        )
        for a in data.get("assets", [])
    ]

    paragraphs: list[NormalizedParagraph] = []
    for idx, p_raw in enumerate(paragraphs_raw):
        # Handle both ms and seconds timestamps
        if "start_ms" in p_raw:
            start_ms = int(p_raw["start_ms"])
            end_ms = int(p_raw["end_ms"])
        elif "startTime" in p_raw:
            start_ms = int(p_raw["startTime"] * 1000)
            end_ms = int(p_raw["endTime"] * 1000)
        else:
            start_ms = 0
            end_ms = 0

        # Normalize keywords — can be list of strings or list of dicts
        raw_keywords = p_raw.get("keywords", [])
        keywords: list[NormalizedKeyword] = []
        for kw in raw_keywords:
            if isinstance(kw, str):
                keywords.append(NormalizedKeyword(word=kw, type="main"))
            elif isinstance(kw, dict):
                keywords.append(NormalizedKeyword(word=kw.get("word", ""), type=kw.get("type", "main")))

        paragraphs.append(NormalizedParagraph(
            id=str(p_raw.get("id", str(uuid.uuid4()))),
            index=idx,
            start_ms=start_ms,
            end_ms=end_ms,
            text=p_raw.get("text", ""),
            keywords=keywords,
            word_timestamps=[],
            assets=shared_assets.copy(),
        ))

    logger.info("Ingested %d paragraphs (structured format), %d shared assets", len(paragraphs), len(shared_assets))
    return NormalizedTranscript(paragraphs=paragraphs, video_context=video_context)


def _visual_to_asset(visual: VisualInput) -> NormalizedAsset:
    """Convert a flat-format visual object to a normalized asset."""
    return NormalizedAsset(
        id=visual.assist_image_id or str(uuid.uuid4()),
        type=visual.type,
        name=visual.title,
        description=visual.alt,
        src=visual.src,
    )


def _normalize_word_timestamps(
    raw_timestamps: list,
    paragraph_start_ms: int,
) -> list[NormalizedWordTimestamp]:
    """Normalize word timestamps to unified format with ms."""
    result: list[NormalizedWordTimestamp] = []
    for wt in raw_timestamps:
        if hasattr(wt, "resolved_word"):
            word = wt.resolved_word
            start = wt.start
            end = wt.end
        elif isinstance(wt, dict):
            word = (wt.get("word") or wt.get("text", "")).strip()
            start = wt.get("start", 0)
            end = wt.get("end", 0)
        else:
            continue

        if not word:
            continue

        result.append(NormalizedWordTimestamp(
            word=word,
            start_ms=int(start * 1000),
            end_ms=int(end * 1000),
        ))

    return result
