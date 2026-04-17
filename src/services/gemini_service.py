"""Gemini LLM integration service with robust model fallback and remediation metadata."""

import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import google.generativeai as genai

from src.config import Config

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for interacting with Gemini API with retries, model fallback, and caching."""

    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        self.model_name = Config.GEMINI_MODEL
        self.model = None
        self.is_initialized = False
        self._cache: Dict[str, Any] = {}
        self._model_cache: Dict[str, Any] = {}

        fallback_models = os.getenv(
            "GEMINI_FALLBACK_MODELS",
            "gemini-2.5-flash,gemini-1.5-flash,gemini-1.5-pro",
        )
        configured = [m.strip() for m in fallback_models.split(",") if m.strip()]
        self._candidate_models = [self.model_name] + [m for m in configured if m != self.model_name]

        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = self._build_model(self.model_name)
                self.is_initialized = True
                logger.info(f"✅ Gemini configured with primary model: {self.model_name}")
            except Exception as e:
                logger.error(f"❌ Failed to configure Gemini: {e}")
                self.model = None
                self.is_initialized = False
        else:
            logger.warning("⚠️ GEMINI_API_KEY not set. Using fallback remediation guidance.")

    def _build_model(self, model_name: str):
        """Build a generative model instance for a specific model name."""
        return genai.GenerativeModel(
            model_name,
            generation_config={
                "temperature": Config.GEMINI_TEMPERATURE,
                "max_output_tokens": Config.GEMINI_MAX_TOKENS,
            },
        )

    def _get_or_create_model(self, model_name: str):
        """Get cached model instance or create one."""
        if model_name not in self._model_cache:
            self._model_cache[model_name] = self._build_model(model_name)
        return self._model_cache[model_name]

    def _extract_response_text(self, response) -> Optional[str]:
        """Extract text from Gemini API response handling different formats."""
        try:
            if hasattr(response, "text") and response.text:
                return response.text
        except Exception:
            pass

        try:
            if hasattr(response, "candidates") and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                        text_parts = []
                        for part in candidate.content.parts:
                            if hasattr(part, "text") and part.text:
                                text_parts.append(part.text)
                        if text_parts:
                            return "".join(text_parts)
        except Exception:
            pass

        try:
            if hasattr(response, "parts"):
                text_parts = [part.text for part in response.parts if hasattr(part, "text") and part.text]
                if text_parts:
                    return "".join(text_parts)
        except Exception:
            pass

        return None

    def _generate_with_model_candidates(self, prompt: str, max_retries: int = 3) -> Tuple[str, str]:
        """
        Generate text using candidate Gemini models with retry/fallback.

        Returns:
            Tuple of (response_text, model_name_used)
        """
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")

        last_error: Optional[Exception] = None

        for candidate in self._candidate_models:
            model = self._get_or_create_model(candidate)
            for attempt in range(max_retries):
                try:
                    logger.info(
                        f"🤖 Gemini call using model {candidate} "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )
                    response = model.generate_content(prompt)
                    response_text = self._extract_response_text(response)
                    if response_text and len(response_text.strip()) > 20:
                        self.model_name = candidate
                        self.model = model
                        self.is_initialized = True
                        return response_text.strip(), candidate
                    last_error = RuntimeError("Gemini returned empty or too-short content")
                except Exception as e:
                    last_error = e
                    logger.warning(
                        f"Gemini model {candidate} failed on attempt {attempt + 1}: {e}"
                    )
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)

        self.is_initialized = False
        if last_error:
            raise last_error
        raise RuntimeError("Gemini generation failed with unknown error")

    def generate_remediation_response(
        self,
        issue_description: str,
        standard: str,
        max_retries: int = 3,
        require_gemini: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate remediation guidance with provider metadata.

        Args:
            issue_description: Accessibility issue text.
            standard: Standard reference.
            max_retries: Retry attempts per model.
            require_gemini: If True, raise when Gemini cannot generate output.

        Returns:
            Dict with keys: text, provider, model, fallback_used.
        """
        cache_key = f"remediation_v2:{issue_description}:{standard}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        prompt = f"""You are an accessibility expert specializing in PDF document compliance.

PDF Accessibility Issue:
{issue_description}

Violated Standard: {standard}

Task: Provide specific, actionable remediation steps that a document author can follow to fix this issue.

Requirements:
- Be specific and technical
- Include tool names (e.g., Adobe Acrobat Pro) when relevant
- Focus on practical, implementable steps
- Keep it concise (2-4 sentences)
- Start directly with the action (no preamble like "To fix this...")

Remediation:"""

        try:
            text, model_used = self._generate_with_model_candidates(prompt, max_retries=max_retries)
            response = {
                "text": text,
                "provider": "gemini",
                "model": model_used,
                "fallback_used": False,
            }
            self._cache[cache_key] = response
            return response
        except Exception as e:
            if require_gemini:
                raise RuntimeError(f"Gemini remediation generation failed: {e}") from e

            fallback = {
                "text": self._fallback_remediation(issue_description, standard),
                "provider": "fallback",
                "model": None,
                "fallback_used": True,
                "error": str(e),
            }
            self._cache[cache_key] = fallback
            return fallback

    def generate_remediation(self, issue_description: str, standard: str, max_retries: int = 3) -> str:
        """Backward-compatible remediation method returning only text."""
        response = self.generate_remediation_response(
            issue_description=issue_description,
            standard=standard,
            max_retries=max_retries,
            require_gemini=False,
        )
        return response["text"]

    def enhance_issue_description(self, raw_finding: str, standard: str) -> str:
        """Enhance a technical finding into a clearer user-facing description."""
        if not self.api_key:
            return raw_finding

        cache_key = f"enhance:{raw_finding}:{standard}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if isinstance(cached, str):
                return cached

        prompt = f"""Convert this technical PDF accessibility finding into a clear, user-friendly description:

Finding: {raw_finding}
Standard: {standard}

Provide a single clear sentence that explains what the issue is and why it matters for accessibility.
Do not include the standard reference in the description.

Description:"""
        try:
            text, _ = self._generate_with_model_candidates(prompt, max_retries=2)
            self._cache[cache_key] = text
            return text
        except Exception as e:
            logger.warning(f"Gemini issue enhancement failed, using raw finding: {e}")
            return raw_finding

    def _fallback_remediation(self, issue_description: str, standard: str) -> str:
        """Provide fallback remediation guidance when Gemini is unavailable."""
        fallback_map = {
            "tag tree": (
                "Use Adobe Acrobat Pro or a similar PDF authoring tool to add tags to the document structure. "
                "Enable the Tagged PDF option when creating/exporting the document and verify tag order in the "
                "Accessibility Checker."
            ),
            "language": (
                "Set the document language in PDF metadata. In Adobe Acrobat, open File > Properties > Advanced "
                "and set the Language field (for example en-US)."
            ),
            "alternative text": (
                "Add meaningful alt text to each informative image or figure in the Tags panel so assistive "
                "technologies can announce image purpose."
            ),
            "form field": (
                "Assign a programmatic name/tooltip to every form field and verify keyboard/tab order in form mode."
            ),
            "scanned": (
                "Run OCR to create a searchable text layer, then add tags and verify reading order with an "
                "accessibility checker."
            ),
            "metadata": (
                "Populate required metadata fields like Title, Author, Subject, and language so assistive tools "
                "can correctly identify the document."
            ),
            "structure": (
                "Review heading hierarchy, list semantics, and reading order tags to ensure content structure "
                "matches the intended document flow."
            ),
        }

        description_lower = issue_description.lower()
        for keyword, guidance in fallback_map.items():
            if keyword in description_lower:
                return guidance

        return (
            f"Review this issue against {standard} and apply a standards-based fix using a PDF accessibility tool. "
            "Validate the result with an accessibility checker before publishing."
        )

    def get_status(self) -> Dict[str, Any]:
        """Get current Gemini service status."""
        return {
            "initialized": self.is_initialized,
            "model": self.model_name if self.is_initialized else None,
            "api_key_set": bool(self.api_key),
            "cache_size": len(self._cache),
            "candidate_models": self._candidate_models,
        }
