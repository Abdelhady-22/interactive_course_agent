"""Transcript router — endpoints for processing transcripts and paragraphs."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from typing import Any

from app.config import Settings, get_settings
from app.schemas.inputs import ProcessTranscriptRequest, ProcessParagraphRequest
from app.schemas.outputs import PlaybackJSON, DecisionOutput
from app.services.pipeline import Pipeline
from app.services.ingestion import ingest_transcript
from app.schemas.inputs import NormalizedParagraph, NormalizedKeyword, NormalizedAsset
from app.utils.errors import AgentError, agent_http_exception
from app.utils.logger import logger

router = APIRouter(prefix="/api", tags=["transcript"])


@router.post("/process-transcript", response_model=PlaybackJSON)
async def process_transcript(
    request: ProcessTranscriptRequest,
    settings: Settings = Depends(get_settings),
) -> PlaybackJSON:
    """Process an entire transcript and return layout decisions for all paragraphs.

    Accepts both flat-array format (example.json) and structured format (plan/input.json).
    Auto-detects the input format.

    Query behavior:
    - `force_llm_paragraphs`: list of paragraph IDs/indexes to force through LLM
    - `review_rules`: enable LLM review of low-confidence rule decisions (< 0.85)
    """
    try:
        logger.info("Processing transcript — %d forced LLM paragraphs, review_rules=%s",
                     len(request.force_llm_paragraphs), request.review_rules)

        pipeline = Pipeline(settings)
        result = pipeline.process_transcript(
            raw_input=request.transcript,
            force_llm_paragraphs=request.force_llm_paragraphs,
            review_rules=request.review_rules,
        )

        logger.info("Transcript processed: %d decisions, %d by rule, %d by LLM",
                     result.total_paragraphs, result.stats.decided_by_rule, result.stats.decided_by_llm)

        return result

    except AgentError as exc:
        raise agent_http_exception(exc, status_code=422)
    except Exception as exc:
        logger.error("Unexpected error processing transcript: %s", exc)
        raise agent_http_exception(
            AgentError(f"Unexpected error: {exc}"), status_code=500,
        )


@router.post("/process-paragraph", response_model=DecisionOutput)
async def process_paragraph(
    request: ProcessParagraphRequest,
    settings: Settings = Depends(get_settings),
) -> DecisionOutput:
    """Re-process a single paragraph through the pipeline.

    Use this to re-run the AI on a specific paragraph after reviewing results.
    Set `use_llm=true` to force LLM decision regardless of rules.
    """
    try:
        # Build normalized paragraph from the raw input
        p_raw = request.paragraph
        paragraph = NormalizedParagraph(
            id=str(p_raw.get("id", "reprocess")),
            index=0,
            start_ms=int(p_raw.get("start_ms", p_raw.get("startTime", 0) * 1000)),
            end_ms=int(p_raw.get("end_ms", p_raw.get("endTime", 0) * 1000)),
            text=p_raw.get("text", ""),
            keywords=[
                NormalizedKeyword(word=kw if isinstance(kw, str) else kw.get("word", ""),
                                  type="main" if isinstance(kw, str) else kw.get("type", "main"))
                for kw in p_raw.get("keywords", [])
            ],
            assets=[
                NormalizedAsset(id=a.get("id", ""), type=a.get("type", "image"),
                                name=a.get("name", a.get("title", "")),
                                description=a.get("description", a.get("alt", "")),
                                src=a.get("src", ""))
                for a in request.assets
            ],
        )

        pipeline = Pipeline(settings)
        result = pipeline.process_single_paragraph(
            paragraph=paragraph,
            previous_decisions=request.previous_decisions,
            use_llm=request.use_llm,
        )

        return result

    except AgentError as exc:
        raise agent_http_exception(exc, status_code=422)
    except Exception as exc:
        logger.error("Unexpected error processing paragraph: %s", exc)
        raise agent_http_exception(
            AgentError(f"Unexpected error: {exc}"), status_code=500,
        )
