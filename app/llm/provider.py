"""LLM provider — LiteLLM wrapper with Ollama Cloud default and multi-provider support."""

from __future__ import annotations

import os
import time
import json

import litellm

from app.config import Settings
from app.utils.errors import LLMError, ErrorCode
from app.utils.logger import logger


class LLMProvider:
    """Unified LLM interface via LiteLLM. Supports Ollama Cloud, Groq, OpenAI, Anthropic, Cohere."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._configure_provider()

    def _configure_provider(self) -> None:
        """Set up LiteLLM and environment variables for the configured provider."""
        provider = self.settings.llm_provider.lower()

        if provider == "ollama":
            # Ollama Cloud: uses OLLAMA_API_KEY env var
            os.environ["OLLAMA_API_KEY"] = self.settings.ollama_api_key
            self.model_string = f"ollama/{self.settings.llm_model}"
        elif provider == "groq":
            os.environ["GROQ_API_KEY"] = self.settings.llm_api_key
            self.model_string = f"groq/{self.settings.llm_model}"
        elif provider == "openai":
            os.environ["OPENAI_API_KEY"] = self.settings.llm_api_key
            self.model_string = self.settings.llm_model
        elif provider == "anthropic":
            os.environ["ANTHROPIC_API_KEY"] = self.settings.llm_api_key
            self.model_string = f"anthropic/{self.settings.llm_model}"
        elif provider == "cohere":
            os.environ["COHERE_API_KEY"] = self.settings.llm_api_key
            self.model_string = f"cohere/{self.settings.llm_model}"
        else:
            self.model_string = f"{provider}/{self.settings.llm_model}"

        if self.settings.llm_api_base:
            os.environ["OLLAMA_API_BASE"] = self.settings.llm_api_base

        # Suppress LiteLLM verbose logging
        litellm.set_verbose = False

        logger.info("LLM configured: provider=%s, model=%s", provider, self.model_string)

    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
    ) -> tuple[str, int, int]:
        """Make an LLM call with retry logic.

        Returns:
            (response_text, prompt_tokens, completion_tokens)

        Raises:
            LLMError on all retries exhausted.
        """
        temp = temperature if temperature is not None else self.settings.llm_temperature
        last_error = None

        for attempt in range(1, self.settings.llm_max_retries + 1):
            try:
                logger.info("LLM call attempt %d/%d", attempt, self.settings.llm_max_retries)
                start = time.time()

                response = litellm.completion(
                    model=self.model_string,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temp,
                    timeout=self.settings.llm_timeout,
                    response_format={"type": "json_object"},
                )

                elapsed = time.time() - start
                text = response.choices[0].message.content.strip()
                usage = response.usage
                prompt_tokens = usage.prompt_tokens if usage else 0
                completion_tokens = usage.completion_tokens if usage else 0

                logger.info(
                    "LLM response received in %.1fs — tokens: prompt=%d, completion=%d",
                    elapsed, prompt_tokens, completion_tokens,
                )
                return text, prompt_tokens, completion_tokens

            except Exception as exc:
                last_error = exc
                wait = 2 ** (attempt - 1)  # 1s, 2s, 4s
                logger.warning(
                    "LLM call attempt %d failed: %s — retrying in %ds",
                    attempt, str(exc)[:200], wait,
                )
                if attempt < self.settings.llm_max_retries:
                    time.sleep(wait)

        raise LLMError(
            f"All {self.settings.llm_max_retries} LLM attempts failed. Last error: {last_error}",
            code=ErrorCode.LLM_ALL_RETRIES_FAILED,
            details={"last_error": str(last_error)},
        )

    def parse_json_response(self, text: str) -> dict:
        """Parse LLM response as JSON, handling common formatting issues."""
        # Strip markdown fences if present
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # Remove first and last lines (fences)
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise LLMError(
                f"LLM returned invalid JSON: {exc}",
                code=ErrorCode.LLM_INVALID_RESPONSE,
                details={"raw_response": text[:500]},
            ) from exc

    def health_check(self) -> dict:
        """Check if the LLM provider is reachable."""
        try:
            text, _, _ = self.call(
                system_prompt="You are a test assistant.",
                user_prompt='Return exactly: {"status": "ok"}',
                temperature=0,
            )
            return {"reachable": True, "provider": self.settings.llm_provider, "model": self.model_string}
        except Exception as exc:
            return {"reachable": False, "provider": self.settings.llm_provider, "error": str(exc)[:200]}
