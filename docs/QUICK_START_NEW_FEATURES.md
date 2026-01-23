# Kor'tana New Features Quick Start

This guide will help you quickly get started with the new features in Kor'tana.

## Prerequisites

- Kor'tana server running
- API accessible at `http://127.0.0.1:8000`

## Quick Examples

### 1. Multilingual Support

**Detect language:**
```bash
curl -X POST "http://127.0.0.1:8000/api/multilingual/detect" \
  -H "Content-Type: application/json" \
  -d '{"text": "Bonjour le monde"}'
```

**Translate text:**
```bash
curl -X POST "http://127.0.0.1:8000/api/multilingual/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world",
    "target_language": "es",
    "source_language": "en"
  }'
```

### 2. Emotional Intelligence

**Analyze sentiment:**
```bash
curl -X POST "http://127.0.0.1:8000/api/emotional-intelligence/sentiment" \
  -H "Content-Type: application/json" \
  -d '{"text": "I love this amazing product!"}'
```

**Detect emotion:**
```bash
curl -X POST "http://127.0.0.1:8000/api/emotional-intelligence/emotion" \
  -H "Content-Type: application/json" \
  -d '{"text": "I am so happy today!"}'
```

### 3. Content Generation

**Summarize text:**
```bash
curl -X POST "http://127.0.0.1:8000/api/content/summarize" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your long text here...",
    "max_length": 100
  }'
```

**Rewrite in different style:**
```bash
curl -X POST "http://127.0.0.1:8000/api/content/rewrite" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your text",
    "style": "formal"
  }'
```

### 4. Plugin System

**List available plugins:**
```bash
curl "http://127.0.0.1:8000/api/plugins/list"
```

**Execute weather plugin:**
```bash
curl -X POST "http://127.0.0.1:8000/api/plugins/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "plugin_name": "WeatherPlugin",
    "parameters": {"location": "New York"}
  }'
```

**Execute stock plugin:**
```bash
curl -X POST "http://127.0.0.1:8000/api/plugins/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "plugin_name": "StockPlugin",
    "parameters": {"symbol": "AAPL"}
  }'
```

### 5. Ethical Transparency

**Log an ethical decision:**
```bash
curl -X POST "http://127.0.0.1:8000/api/ethics/log-decision" \
  -H "Content-Type: application/json" \
  -d '{
    "decision_type": "content_moderation",
    "context": "User message review",
    "decision": "Approved",
    "reasoning": "Content is appropriate",
    "confidence": 0.9
  }'
```

**Get transparency report:**
```bash
curl "http://127.0.0.1:8000/api/ethics/report"
```

### 6. Gaming Features

**Start an interactive story:**
```bash
curl -X POST "http://127.0.0.1:8000/api/gaming/story/start" \
  -H "Content-Type: application/json" \
  -d '{
    "genre": "fantasy",
    "setting": "A mystical forest"
  }'
```

**Roll dice for RPG:**
```bash
curl -X POST "http://127.0.0.1:8000/api/gaming/rpg/roll" \
  -H "Content-Type: application/json" \
  -d '{"dice_notation": "2d6+3"}'
```

**Generate NPC:**
```bash
curl "http://127.0.0.1:8000/api/gaming/rpg/npc?npc_type=merchant"
```

### 7. Marketplace

**Browse modules:**
```bash
curl "http://127.0.0.1:8000/api/marketplace/modules"
```

**Search modules:**
```bash
curl "http://127.0.0.1:8000/api/marketplace/modules/search?query=nlp"
```

**Get module details:**
```bash
curl "http://127.0.0.1:8000/api/marketplace/modules/advanced-nlp"
```

## Python Examples

### Using the Modules Directly

```python
import sys
sys.path.insert(0, 'src')

# Multilingual
from kortana.modules.multilingual import TranslationService, LanguageDetector

translator = TranslationService()
languages = translator.get_supported_languages()
print(f"Supported: {languages}")

detector = LanguageDetector()
lang = detector.detect("Hola mundo")
print(f"Detected: {lang}")

# Emotional Intelligence
from kortana.modules.emotional_intelligence import SentimentAnalyzer, EmotionDetector

sentiment_analyzer = SentimentAnalyzer()
sentiment, confidence = sentiment_analyzer.analyze("This is great!")
print(f"Sentiment: {sentiment} ({confidence:.2f})")

emotion_detector = EmotionDetector()
emotion, confidence = emotion_detector.detect("I am so happy!")
print(f"Emotion: {emotion} ({confidence:.2f})")

# Content Generation
from kortana.modules.content_generation import ContentGenerator

generator = ContentGenerator()
summary = generator.summarize("Long text here..." * 20, max_length=50)
print(f"Summary: {summary}")

# Plugin System
from kortana.modules.plugin_framework import PluginLoader
from kortana.modules.plugin_framework.example_plugins import WeatherPlugin

loader = PluginLoader()
loader.load_plugin(WeatherPlugin())
result = loader.execute_plugin("WeatherPlugin", location="London")
print(f"Weather: {result}")
```

### Using with FastAPI TestClient

```python
from fastapi.testclient import TestClient
from kortana.main import app

client = TestClient(app)

# Test multilingual endpoint
response = client.get("/api/multilingual/languages")
print(response.json())

# Test emotional intelligence
response = client.post(
    "/api/emotional-intelligence/sentiment",
    json={"text": "This is wonderful!"}
)
print(response.json())

# Test content generation
response = client.post(
    "/api/content/summarize",
    json={"text": "Long text...", "max_length": 50}
)
print(response.json())
```

## Interactive API Documentation

For the best experience, use the interactive Swagger UI documentation:

1. Start the Kor'tana server
2. Open your browser to: `http://127.0.0.1:8000/docs`
3. Try out each endpoint interactively

## Next Steps

- Read the full documentation: [NEW_FEATURES.md](NEW_FEATURES.md)
- Create custom plugins for your specific needs
- Integrate with your existing applications
- Provide feedback on ethical decisions to improve the system

## Troubleshooting

**Issue: Module import errors**
- Ensure you're in the correct directory
- Add `src` to your Python path: `sys.path.insert(0, 'src')`

**Issue: API endpoint not found**
- Check that the server is running
- Verify you're using the correct port (default: 8000)
- Ensure all modules are properly installed

**Issue: Plugin execution fails**
- Verify the plugin name is correct (case-sensitive)
- Check that required parameters are provided
- Ensure the plugin is enabled

For more help, see the main documentation or open an issue on GitHub.
