"""
Test for text_analysis module.
"""

from src.kortana.utils import text_analysis


def test_identify_important_message_for_context():
    """Test the identify_important_message_for_context function."""
    # Test important messages
    assert text_analysis.identify_important_message_for_context("This is URGENT")
    assert text_analysis.identify_important_message_for_context("Remember this")
    assert text_analysis.identify_important_message_for_context("This is important")

    # Test non-important messages
    assert not text_analysis.identify_important_message_for_context(
        "Just a normal message"
    )
    assert not text_analysis.identify_important_message_for_context("Hello there")


def test_analyze_sentiment():
    """Test the analyze_sentiment function."""
    # Test positive sentiment
    assert text_analysis.analyze_sentiment("I love this") > 0

    # Test negative sentiment
    assert text_analysis.analyze_sentiment("I hate this") < 0

    # Test neutral sentiment
    assert abs(text_analysis.analyze_sentiment("This is a statement")) < 0.5


def test_detect_emphasis_all_caps():
    """Test the detect_emphasis_all_caps function."""
    # Test with all caps
    assert text_analysis.detect_emphasis_all_caps("THIS IS LOUD")

    # Test with some caps
    assert not text_analysis.detect_emphasis_all_caps("This Is Normal")

    # Test with no caps
    assert not text_analysis.detect_emphasis_all_caps("this is quiet")
