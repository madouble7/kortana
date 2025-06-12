import unittest

from src.utils import text_encoding


class TestTextEncodingUtils(unittest.TestCase):
    def test_base64_encode_decode(self):
        """Test base64 encoding and decoding."""
        original_text = "Hello, Kortana!"
        encoded_text = text_encoding.encode_text_to_base64(original_text)
        decoded_text = text_encoding.decode_base64_to_text(encoded_text)
        self.assertEqual(original_text, decoded_text)
        self.assertIsInstance(encoded_text, str)
        self.assertIsInstance(decoded_text, str)

    def test_base64_decode_invalid_input(self):
        """Test base64 decoding with invalid input."""
        invalid_encoded_text = "Invalid#Base64"
        with self.assertRaises(
            ValueError
        ):  # Assuming decode_base64_to_text raises ValueError or similar for invalid input
            text_encoding.decode_base64_to_text(invalid_encoded_text)

    # Tests for functionality not present in src/utils/text_encoding.py (commented out)
    # def test_url_encode_decode(self):
    #     """Test URL encoding and decoding."""\n    #     original_text = "https://example.com/query?name=test user&id=123"
    #     encoded_text = text_encoding.url_encode(original_text)
    #     decoded_text = text_encoding.url_decode(encoded_text)
    #     self.assertEqual(original_text, decoded_text)
    #     self.assertIsInstance(encoded_text, str)
    #     self.assertIsInstance(decoded_text, str)

    # def test_url_decode_invalid_input(self):
    #     """Test URL decoding with invalid input."""
    #     # URL decode is generally more lenient, testing a case that might cause unexpected behavior
    #     invalid_encoded_text = "invalid%"
    #     # The expected behavior for invalid % sequences might vary; testing if it doesn't raise an unexpected error or handles gracefully
    #     decoded_text = text_encoding.url_decode(invalid_encoded_text)
    #     self.assertEqual(decoded_text, "invalid%") # Expecting the invalid sequence to be left as is

    # def test_html_encode_decode(self):
    #     """Test HTML encoding and decoding."""
    #     original_text = "<p>Hello & World!</p>"
    #     encoded_text = text_encoding.html_encode(original_text)
    #     decoded_text = text_encoding.html_decode(encoded_text)
    #     self.assertEqual(original_text, decoded_text)
    #     self.assertIsInstance(encoded_text, str)
    #     self.assertIsInstance(decoded_text, str)
    #     self.assertEqual(encoded_text, "&lt;p&gt;Hello &amp; World!&lt;/p&gt;") # Specific check for common entities

    # def test_json_encode_decode(self):
    #     """Test JSON encoding and decoding."""
    #     original_data = {"name": "Kortana", "version": 1.0, "enabled": True}
    #     encoded_text = text_encoding.json_encode(original_data)
    #     decoded_data = text_encoding.json_decode(encoded_text)
    #     self.assertEqual(original_data, decoded_data)
    #     self.assertIsInstance(encoded_text, str)
    #     # json_decode should return appropriate Python types, not necessarily a string

    # def test_json_decode_invalid_input(self):
    #     """Test JSON decoding with invalid input."""
    #     invalid_encoded_text = "{\"name\": \"Kortana\", \"version\": 1.0, \"enabled\": True"
    #     with self.assertRaises(ValueError):
    #         text_encoding.json_decode(invalid_encoded_text)


if __name__ == "__main__":
    unittest.main()
