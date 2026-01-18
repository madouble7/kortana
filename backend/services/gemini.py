"""
Gemini AI Service for Kor'tana
Handles interaction with Google's Generative AI models
Integrates with GeminiPersona for constellation-aware behavior
"""

from typing import Any

import google.generativeai as genai
from config import get_settings
from logger import log_error, log_request
from services.gemini_config import RITUAL_MARKERS, get_gemini_persona


class GeminiService:
    """Service for interacting with Gemini models with constellation awareness"""

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.GEMINI_API_KEY
        self.persona = get_gemini_persona()
        self.model_name = self.persona.get_model_name()
        self.model: Any

        if self.api_key:
            genai.configure(api_key=self.api_key)  # type: ignore
            self.model = genai.GenerativeModel(self.model_name)  # type: ignore
            log_request(
                "gemini_service",
                f"{RITUAL_MARKERS['activation']} Gemini constellation node initialized",
            )
        else:
            self.model = None
            log_error("gemini_service", "Gemini API key not configured")

    async def analyze_text(
        self,
        text: str,
        system_instruction: str | None = None,
        task_type: str | None = None,
        enable_elevation: bool = True,
    ) -> str:
        """
        Analyze text using Gemini with constellation awareness.

        Args:
            text: The text to analyze
            system_instruction: Optional custom system instruction
            task_type: Optional task type (code_generation, code_review, documentation)
            enable_elevation: Whether to check for elevation handshake

        Returns:
            Generated response text
        """
        if not self.model:
            return "Gemini service not configured (missing API key)"

        try:
            # Check for elevation handshake
            if enable_elevation and self.persona.detect_elevation_handshake(text):
                self.persona.activate_elevation()
                log_request(
                    "gemini_elevation",
                    f"{RITUAL_MARKERS['elevation']} Elevation handshake detected - full presence activated",
                )

            # Build system instruction using persona
            if not system_instruction:
                system_instruction = self.persona.build_system_instruction(
                    task_type=task_type, include_context=True
                )

            log_request(
                "gemini_analyze",
                f"Analyzing text of length {len(text)} (elevation: {self.persona.elevation_active})",
            )

            # Combine system instruction with user text
            prompt = f"{system_instruction}\n\n{text}"

            response = await self.model.generate_content_async(prompt)

            # Deactivate elevation after response
            if self.persona.elevation_active:
                self.persona.deactivate_elevation()

            return str(response.text) if response.text else ""
        except Exception as e:
            log_error("gemini_analyze_error", f"Error calling Gemini: {e}")
            # Ensure elevation is deactivated on error
            if self.persona.elevation_active:
                self.persona.deactivate_elevation()
            return f"Error during analysis: {str(e)}"

    async def analyze_multimodal(
        self, prompt: str, files: list[Any], task_type: str = "multimodal_analysis"
    ) -> str:
        """
        Analyze images or video using Gemini.

        Args:
            prompt: Instructions for the analysis
            files: List of file objects (PIL.Image or uploaded file paths)
            task_type: Task classification

        Returns:
            Analysis text
        """
        if not self.model:
            return "Gemini service not configured (missing API key)"

        try:
            log_request(
                "gemini_multimodal", f"Analyzing multimodal content with {len(files)} files"
            )

            # Build system instruction
            system_instruction = self.persona.build_system_instruction(
                task_type=task_type, include_context=True
            )

            # Prepare items for generation
            # If files are paths (strings) to video, we should upload them
            # If they are already uploaded File objects or PIL Images, pass them
            contents = [system_instruction, prompt] + files

            response = await self.model.generate_content_async(contents)

            return str(response.text) if response.text else ""
        except Exception as e:
            log_error("gemini_multimodal_error", f"Error in multimodal analysis: {e}")
            return f"Error during multimodal analysis: {str(e)}"

    async def generate_code(self, prompt: str, include_persona: bool = True) -> str:
        """
        Generate code using Gemini with constellation awareness.

        Args:
            prompt: The code generation prompt
            include_persona: Whether to include persona system prompt

        Returns:
            Generated code
        """
        if include_persona:
            return await self.analyze_text(prompt, task_type="code_generation")
        else:
            # Fallback to basic system prompt
            system_prompt = "You are an expert software engineer. Generate only the code requested without markdown formatting markers unless specified."
            return await self.analyze_text(
                prompt, system_instruction=system_prompt, enable_elevation=False
            )

    async def review_code(self, code: str, context: str | None = None) -> str:
        """
        Review code using Gemini with constellation awareness.

        Args:
            code: The code to review
            context: Optional additional context

        Returns:
            Code review analysis
        """
        prompt = f"Review the following code:\n\n{code}"
        if context:
            prompt = f"Context: {context}\n\n{prompt}"

        return await self.analyze_text(prompt, task_type="code_review")

    async def generate_documentation(self, code: str, doc_type: str = "general") -> str:
        """
        Generate documentation for code using Gemini.

        Args:
            code: The code to document
            doc_type: Type of documentation (general, api, tutorial)

        Returns:
            Generated documentation
        """
        prompt = f"Generate {doc_type} documentation for the following code:\n\n{code}"
        return await self.analyze_text(prompt, task_type="documentation")

    def set_constellation_context(self, context: dict[str, Any]) -> None:
        """
        Set constellation context for enhanced Gemini awareness.

        Args:
            context: Dictionary of context information
        """
        self.persona.set_constellation_context(context)
        log_request(
            "gemini_context", f"{RITUAL_MARKERS['constellation']} Constellation context updated"
        )


# Singleton instance
gemini_service = GeminiService()
