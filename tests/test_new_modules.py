"""
Tests for new Kor'tana modules
"""

import pytest


# Multilingual Module Tests
def test_translation_service():
    from kortana.modules.multilingual import TranslationService

    service = TranslationService()
    assert service.is_supported("en")
    assert service.is_supported("es")
    assert not service.is_supported("xyz")

    # Test translation
    result = service.translate("Hello", "en", "es")
    assert result is not None


def test_language_detector():
    from kortana.modules.multilingual import LanguageDetector

    detector = LanguageDetector()

    # Test English detection
    lang = detector.detect("Hello world")
    assert lang == "en"

    # Test Spanish detection
    lang = detector.detect("Hola señor")
    assert lang == "es"

    # Test with confidence
    lang, confidence = detector.detect_with_confidence("Hello")
    assert lang == "en"
    assert 0 <= confidence <= 1


# Emotional Intelligence Module Tests
def test_sentiment_analyzer():
    from kortana.modules.emotional_intelligence import SentimentAnalyzer
    from kortana.modules.emotional_intelligence.sentiment_analyzer import Sentiment

    analyzer = SentimentAnalyzer()

    # Test positive sentiment
    sentiment, confidence = analyzer.analyze("This is wonderful and amazing!")
    assert sentiment == Sentiment.POSITIVE
    assert confidence > 0.5

    # Test negative sentiment
    sentiment, confidence = analyzer.analyze("This is terrible and awful")
    assert sentiment == Sentiment.NEGATIVE
    assert confidence > 0.5

    # Test sentiment score
    score = analyzer.get_sentiment_score("This is great")
    assert score > 0


def test_emotion_detector():
    from kortana.modules.emotional_intelligence import EmotionDetector
    from kortana.modules.emotional_intelligence.emotion_detector import Emotion

    detector = EmotionDetector()

    # Test joy detection
    emotion, confidence = detector.detect("I am so happy and excited!")
    assert emotion == Emotion.JOY

    # Test all emotions
    emotions = detector.detect_all("I am happy")
    assert isinstance(emotions, dict)


# Content Generation Module Tests
def test_content_generator():
    from kortana.modules.content_generation import ContentGenerator
    from kortana.modules.content_generation.content_generator import ContentStyle

    generator = ContentGenerator()

    # Test summarization
    text = "This is a long text. " * 20
    summary = generator.summarize(text, max_length=50)
    assert len(summary) <= 60  # Allow some margin

    # Test elaboration
    short_text = "Hello"
    elaborated = generator.elaborate(short_text, target_length=200)
    assert len(elaborated) > len(short_text)

    # Test rewriting
    rewritten = generator.rewrite("Test text", ContentStyle.FORMAL)
    assert "formal" in rewritten.lower()

    # Test industry adaptation
    adapted = generator.adjust_for_industry("Test", "healthcare")
    assert "healthcare" in adapted.lower()


# Plugin Framework Module Tests
def test_plugin_base():
    from kortana.modules.plugin_framework import BasePlugin, PluginRegistry

    class TestPlugin(BasePlugin):
        def execute(self, **kwargs):
            return {"result": "test"}

        def get_info(self):
            return {"name": self.name, "version": self.version}

    plugin = TestPlugin()
    assert plugin.is_enabled()

    plugin.disable()
    assert not plugin.is_enabled()

    # Test registry
    registry = PluginRegistry()
    registry.register(plugin)
    assert "TestPlugin" in registry.list_plugins()


def test_example_plugins():
    from kortana.modules.plugin_framework.example_plugins import (
        WeatherPlugin,
        StockPlugin,
        TaskManagementPlugin,
    )

    # Test WeatherPlugin
    weather = WeatherPlugin()
    result = weather.execute(location="New York")
    assert "location" in result
    assert result["location"] == "New York"

    # Test StockPlugin
    stock = StockPlugin()
    result = stock.execute(symbol="AAPL")
    assert "symbol" in result
    assert result["symbol"] == "AAPL"

    # Test TaskManagementPlugin
    task_mgr = TaskManagementPlugin()
    result = task_mgr.execute(action="add", task="Test task")
    assert result["action"] == "add"


# Ethical Transparency Module Tests
def test_ethical_decision_logger():
    from kortana.modules.ethical_transparency import EthicalDecisionLogger
    from kortana.modules.ethical_transparency.decision_logger import (
        EthicalDecisionType,
    )

    logger = EthicalDecisionLogger()

    # Log a decision
    decision_id = logger.log_decision(
        EthicalDecisionType.CONTENT_MODERATION,
        "User message",
        "Approved",
        "Content is appropriate",
        0.9,
    )
    assert decision_id is not None

    # Get decision
    decision = logger.get_decision(decision_id)
    assert decision is not None
    assert decision.decision_type == EthicalDecisionType.CONTENT_MODERATION

    # Add feedback
    success = logger.add_feedback(decision_id, "Good decision")
    assert success


def test_transparency_service():
    from kortana.modules.ethical_transparency import (
        EthicalDecisionLogger,
        TransparencyService,
    )
    from kortana.modules.ethical_transparency.decision_logger import (
        EthicalDecisionType,
    )

    logger = EthicalDecisionLogger()
    service = TransparencyService(logger)

    # Log some decisions
    logger.log_decision(
        EthicalDecisionType.BIAS_MITIGATION, "Context", "Decision", "Reasoning"
    )

    # Generate report
    report = service.generate_report()
    assert "total_decisions" in report
    assert report["total_decisions"] > 0


# Gaming Module Tests
def test_storytelling_engine():
    from kortana.modules.gaming import StorytellingEngine
    from kortana.modules.gaming.storytelling_engine import StoryGenre

    engine = StorytellingEngine()

    # Start a story
    story = engine.start_story(StoryGenre.FANTASY, "A magical forest")
    assert story["genre"] == StoryGenre.FANTASY
    assert story["setting"] == "A magical forest"

    # Continue story
    result = engine.continue_story("explore the forest")
    assert "previous_action" in result

    # Add character
    character = engine.add_character("Hero", "A brave warrior")
    assert character["name"] == "Hero"


def test_rpg_assistant():
    from kortana.modules.gaming import RPGAssistant

    assistant = RPGAssistant()

    # Create campaign
    campaign = assistant.create_campaign("Test Campaign", "D&D 5e")
    assert campaign["name"] == "Test Campaign"

    # Add player
    player = assistant.add_player("John", "Aragorn", "Ranger")
    assert player["character_name"] == "Aragorn"

    # Roll dice
    result = assistant.roll_dice("2d6")
    assert "rolls" in result
    assert len(result["rolls"]) == 2

    # Generate NPC
    npc = assistant.generate_npc("merchant")
    assert "name" in npc


# Marketplace Module Tests
def test_module_registry():
    from kortana.modules.marketplace.module_registry import ModuleRegistry

    registry = ModuleRegistry()

    # Register module
    module = registry.register_module(
        "test-module", "1.0.0", "test-author", "Test description", "test"
    )
    assert module.name == "test-module"

    # Get module
    retrieved = registry.get_module("test-module")
    assert retrieved is not None
    assert retrieved.name == "test-module"

    # Install module
    success = registry.install_module("test-module")
    assert success
    assert registry.is_installed("test-module")

    # Rate module
    success = registry.rate_module("test-module", 4.5)
    assert success


def test_marketplace_service():
    from kortana.modules.marketplace import MarketplaceService

    service = MarketplaceService()

    # Browse modules
    result = service.browse_modules()
    assert "modules" in result
    assert result["count"] >= 0

    # Search modules
    result = service.search_modules("nlp")
    assert "results" in result
