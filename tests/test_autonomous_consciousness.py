import logging
import os
import unittest

from dotenv import load_dotenv

from kortana.llm_clients.genai_client import GoogleGenAIClient

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables from .env
load_dotenv()


class TestAutonomousConsciousness(unittest.TestCase):
    def setUp(self):
        """Initialize test environment"""
        logger.info("🚀 Initializing Google GenAI test environment")
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            logger.error("❌ GOOGLE_API_KEY environment variable not set")
            self.skipTest("GOOGLE_API_KEY environment variable not set")

        logger.info("🔑 API key found, initializing client...")
        self.genai_client = GoogleGenAIClient(
            api_key=self.api_key, model_name="gemini-1.5-flash"
        )
        logger.info("✅ Client initialization complete")

    def test_basic_generation(self):
        """Test basic generation with GoogleGenAIClient and generation_config"""
        logger.info("\n🧪 Testing Google GenAI Integration")

        system_prompt = "You are a helpful AI assistant."
        messages = [{"role": "user", "content": "What is the capital of France?"}]

        logger.info("📤 Sending test request to Gemini...")
        response = self.genai_client.generate_response(
            system_prompt=system_prompt,
            messages=messages,
            temperature=0.7,
            max_output_tokens=150,
            top_p=0.9,
        )

        logger.info("📥 Validating response structure...")
        self.assertIsNotNone(response)
        self.assertNotIn("error", response)
        self.assertTrue(response["choices"][0]["message"]["content"])
        self.assertIn("choices", response, "Response missing 'choices' field")
        self.assertTrue(len(response["choices"]) > 0, "Response has no choices")
        self.assertIn(
            "message", response["choices"][0], "Response choice missing 'message' field"
        )
        self.assertIn(
            "content",
            response["choices"][0]["message"],
            "Response message missing 'content' field",
        )
        content = response["choices"][0]["message"]["content"]
        self.assertIsNotNone(content, "Response content is None")
        self.assertNotEqual(content.strip(), "", "Response content is empty")

        logger.info("✨ Response received: %s", content)
        logger.info("✅ Google GenAI test completed successfully")


if __name__ == "__main__":
    unittest.main(verbosity=2)
