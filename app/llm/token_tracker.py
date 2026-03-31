"""Token tracker — aggregates token usage across the entire pipeline run."""

from __future__ import annotations

from app.schemas.internals import SessionTokenUsage
from app.schemas.outputs import TokenUsage


class TokenTracker:
    """Tracks token usage per call and aggregates for the session."""

    def __init__(self):
        self.session = SessionTokenUsage()

    def record(self, prompt_tokens: int, completion_tokens: int, is_review: bool = False) -> TokenUsage:
        """Record token usage for a single call."""
        self.session.add(prompt_tokens, completion_tokens, is_review)
        return TokenUsage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)

    def get_session_totals(self) -> TokenUsage:
        """Get aggregated totals for the entire session."""
        return TokenUsage(
            prompt_tokens=self.session.total_prompt_tokens,
            completion_tokens=self.session.total_completion_tokens,
        )

    def reset(self) -> None:
        """Reset the tracker for a new session."""
        self.session = SessionTokenUsage()
