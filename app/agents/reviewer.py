"""Review agent — reviews low-confidence rule decisions and optionally overrides them."""

from __future__ import annotations

from app.agents.prompts import REVIEW_SYSTEM_PROMPT, build_review_prompt
from app.llm.provider import LLMProvider
from app.schemas.inputs import NormalizedParagraph
from app.schemas.internals import ReviewResult, RuleResult, LLMResponse
from app.utils.errors import LLMError
from app.utils.logger import logger


class LayoutReviewer:
    """Reviews rule-engine decisions and optionally overrides them."""

    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def review(
        self,
        paragraph: NormalizedParagraph,
        rule_result: RuleResult,
        previous_decisions: list[dict],
    ) -> tuple[ReviewResult, int, int]:
        """Ask the LLM to review a rule engine decision.

        Returns:
            (ReviewResult, prompt_tokens, completion_tokens)
        """
        keywords = [kw.word for kw in paragraph.keywords]
        assets = [
            {"type": a.type, "name": a.name, "description": a.description}
            for a in paragraph.assets
        ]
        rule_dict = {
            "layout_mode": rule_result.layout_mode.value if rule_result.layout_mode else "unknown",
            "confidence": rule_result.confidence,
            "reason": rule_result.reason,
            "rule_name": rule_result.rule_name,
        }

        user_prompt = build_review_prompt(
            paragraph_text=paragraph.text,
            keywords=keywords,
            assets=assets,
            rule_decision=rule_dict,
            previous_decisions=previous_decisions,
        )

        logger.info(
            "Calling LLM Reviewer for paragraph '%s' (rule=%s, conf=%.2f)",
            paragraph.id, rule_result.rule_name, rule_result.confidence,
        )

        try:
            raw_text, prompt_tokens, completion_tokens = self.llm.call(
                system_prompt=REVIEW_SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )

            parsed = self.llm.parse_json_response(raw_text)
            result = _parse_review_response(parsed)

            logger.info(
                "Reviewer result: approved=%s for paragraph '%s'%s",
                result.approved, paragraph.id,
                "" if result.approved else f" — override to {result.override.layout_mode}" if result.override else "",
            )

            return result, prompt_tokens, completion_tokens

        except LLMError:
            # If review fails, just approve the rule decision
            logger.warning("Review LLM call failed for paragraph '%s', keeping rule decision", paragraph.id)
            return ReviewResult(approved=True, review_note="Review skipped due to LLM error"), 0, 0


def _parse_review_response(data: dict) -> ReviewResult:
    """Parse the review agent's JSON response."""
    from app.agents.director import _parse_llm_response

    approved = data.get("approved", True)
    review_note = data.get("review_note", "")

    override = None
    if not approved and "override" in data:
        override = _parse_llm_response(data["override"])

    return ReviewResult(
        approved=approved,
        override=override,
        review_note=review_note,
    )
