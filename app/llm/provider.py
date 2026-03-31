"""LLM provider — native Ollama for GLM-5 Cloud, LiteLLM for other providers."""

from __future__ import annotations

import os
import time
import json

from app.config import Settings
from app.utils.errors import LLMError, ErrorCode
from app.utils.logger import logger


class LLMProvider:
    """Unified LLM interface. Uses native ollama library for Ollama Cloud, LiteLLM for others."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.provider = settings.llm_provider.lower()
        self._configure_provider()

    def _configure_provider(self) -> None:
        """Set up the LLM provider."""
        if self.provider == "ollama":
            # Native ollama library — connects to Ollama Cloud via API key
            import ollama
            self._ollama_client = ollama.Client(
                host=self.settings.llm_api_base or "https://api.ollama.com",
            )
            # Set API key in environment for ollama library
            if self.settings.ollama_api_key:
                os.environ["OLLAMA_API_KEY"] = self.settings.ollama_api_key

            logger.info("LLM configured: native ollama, model=%s", self.settings.llm_model)
        else:
            # LiteLLM for Groq, OpenAI, Anthropic, Cohere, etc.
            import litellm
            litellm.set_verbose = False

            if self.provider == "groq":
                os.environ["GROQ_API_KEY"] = self.settings.llm_api_key
                self.model_string = f"groq/{self.settings.llm_model}"
            elif self.provider == "openai":
                os.environ["OPENAI_API_KEY"] = self.settings.llm_api_key
                self.model_string = self.settings.llm_model
            elif self.provider == "anthropic":
                os.environ["ANTHROPIC_API_KEY"] = self.settings.llm_api_key
                self.model_string = f"anthropic/{self.settings.llm_model}"
            elif self.provider == "cohere":
                os.environ["COHERE_API_KEY"] = self.settings.llm_api_key
                self.model_string = f"cohere/{self.settings.llm_model}"
            else:
                self.model_string = f"{self.provider}/{self.settings.llm_model}"

            logger.info("LLM configured: litellm, provider=%s, model=%s", self.provider, self.model_string)

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
        if self.provider == "ollama":
            return self._call_ollama(system_prompt, user_prompt, temperature)
        else:
            return self._call_litellm(system_prompt, user_prompt, temperature)

    def _call_ollama(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
    ) -> tuple[str, int, int]:
        """Call Ollama Cloud using the native ollama library."""
        from ollama import chat, ChatResponse

        temp = temperature if temperature is not None else self.settings.llm_temperature
        last_error = None

        for attempt in range(1, self.settings.llm_max_retries + 1):
            try:
                logger.info("Ollama call attempt %d/%d (model=%s)",
                            attempt, self.settings.llm_max_retries, self.settings.llm_model)
                start = time.time()

                response: ChatResponse = chat(
                    model=self.settings.llm_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    options={"temperature": temp},
                    format="json",
                )

                elapsed = time.time() - start
                text = response.message.content.strip()

                # Extract token usage if available
                prompt_tokens = 0
                completion_tokens = 0
                if hasattr(response, "prompt_eval_count") and response.prompt_eval_count:
                    prompt_tokens = response.prompt_eval_count
                if hasattr(response, "eval_count") and response.eval_count:
                    completion_tokens = response.eval_count

                logger.info(
                    "Ollama response received in %.1fs — tokens: prompt=%d, completion=%d",
                    elapsed, prompt_tokens, completion_tokens,
                )
                return text, prompt_tokens, completion_tokens

            except Exception as exc:
                last_error = exc
                wait = 2 ** (attempt - 1)
                logger.warning(
                    "Ollama call attempt %d failed: %s — retrying in %ds",
                    attempt, str(exc)[:200], wait,
                )
                if attempt < self.settings.llm_max_retries:
                    time.sleep(wait)

        raise LLMError(
            f"All {self.settings.llm_max_retries} Ollama attempts failed. Last error: {last_error}",
            code=ErrorCode.LLM_ALL_RETRIES_FAILED,
            details={"last_error": str(last_error)},
        )

    def _call_litellm(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
    ) -> tuple[str, int, int]:
        """Call LLM using LiteLLM (Groq, OpenAI, Anthropic, etc.)."""
        import litellm

        temp = temperature if temperature is not None else self.settings.llm_temperature
        last_error = None

        for attempt in range(1, self.settings.llm_max_retries + 1):
            try:
                logger.info("LiteLLM call attempt %d/%d", attempt, self.settings.llm_max_retries)
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
                    "LiteLLM response received in %.1fs — tokens: prompt=%d, completion=%d",
                    elapsed, prompt_tokens, completion_tokens,
                )
                return text, prompt_tokens, completion_tokens

            except Exception as exc:
                last_error = exc
                wait = 2 ** (attempt - 1)
                logger.warning(
                    "LiteLLM call attempt %d failed: %s — retrying in %ds",
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
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
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
            return {"reachable": True, "provider": self.settings.llm_provider, "model": self.settings.llm_model}
        except Exception as exc:
            return {"reachable": False, "provider": self.settings.llm_provider, "error": str(exc)[:200]}
