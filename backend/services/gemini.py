"""
Gemini AI Service for Kor'tana
Handles interaction with Google's Generative AI models
"""


import google.generativeai as genai
from config import get_settings
from logger import log_error, log_request


class GeminiService:
    """Service for interacting with Gemini models"""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = "gemini-1.5-flash" # Use flash for cost/speed, can be configured

        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
        else:
            self.model = None
            log_error("gemini_service", "Gemini API key not configured")

    async def analyze_text(self, text: str, system_instruction: str | None = None) -> str:
        """Analyze text using Gemini"""
        if not self.model:
            return "Gemini service not configured (missing API key)"

        try:
            log_request("gemini_analyze", f"Analyzing text of length {len(text)}")

            prompt = text
            if system_instruction:
                prompt = f"{system_instruction}\n\n{text}"

            response = await self.model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            log_error("gemini_analyze_error", f"Error calling Gemini: {e}")
            return f"Error during analysis: {str(e)}"

    async def generate_code(self, prompt: str) -> str:
        """Generate code using Gemini"""
        system_prompt = "You are an expert software engineer. Generate only the code requested without markdown formatting markers unless specified."
        return await self.analyze_text(prompt, system_instruction=system_prompt)

# Singleton instance
gemini_service = GeminiService()
