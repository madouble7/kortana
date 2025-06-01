import unittest
from src.utils.text_analysis import (count_tokens, summarize_text,
                                   extract_keywords, analyze_sentiment)

class TestTextAnalysisUtils(unittest.TestCase):

    def test_count_tokens(self):
        """Test token counting."""
        text = "This is a test sentence."
        token_count = count_tokens(text)
        self.assertIsInstance(token_count, int)
        self.assertGreater(token_count, 0)

    def test_count_tokens_empty_string(self):
        """Test token counting with an empty string."""
        text = ""
        token_count = count_tokens(text)
        self.assertEqual(token_count, 0)

    def test_summarize_text_basic(self):
        """Test basic text summarization."""
        text = "This is a longer piece of text that needs summarization. It contains several sentences that convey the main ideas. The summary should capture the most important points concisely."
        summary = summarize_text(text, max_tokens=50)
        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary), 0)

    def test_summarize_text_empty_string(self):
        """Test summarization with an empty string."""
        text = ""
        summary = summarize_text(text, max_tokens=10)
        self.assertEqual(summary, "")

    def test_extract_keywords_basic(self):
        """Test basic keyword extraction."""
        text = "Keyword extraction is a technique used in natural language processing to identify important terms."
        keywords = extract_keywords(text)
        self.assertIsInstance(keywords, list)
        self.assertEqual(keywords, [])

    def test_extract_keywords_empty_string(self):
        """Test keyword extraction with an empty string."""
        text = ""
        keywords = extract_keywords(text)
        self.assertEqual(keywords, [])

    def test_analyze_sentiment_basic(self):
        """Test basic sentiment analysis."""
        text = "This is a great day!"
        sentiment = analyze_sentiment(text)
        self.assertIsInstance(sentiment, dict)
        self.assertIn('polarity', sentiment)
        self.assertIn('subjectivity', sentiment)

    def test_analyze_sentiment_empty_string(self):
        """Test sentiment analysis with an empty string."""
        text = ""
        sentiment = analyze_sentiment(text)
        self.assertIsNotNone(sentiment)

if __name__ == '__main__':
    unittest.main()
