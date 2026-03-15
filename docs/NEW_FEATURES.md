# Kor'tana New Features Documentation

This document describes the new features added to Kor'tana in this update.

## Table of Contents

1. [Multilingual Support](#1-multilingual-support)
2. [Emotional Intelligence (EQ)](#2-emotional-intelligence-eq)
3. [Adaptive Content Generation](#3-adaptive-content-generation)
4. [Dynamic API Integration (Plugins)](#4-dynamic-api-integration-plugins)
5. [Ethical Transparency Dashboard](#5-ethical-transparency-dashboard)
6. [Gaming Expansion](#6-gaming-expansion)
7. [Community-Driven Marketplace](#7-community-driven-marketplace)

---

## 1. Multilingual Support

Real-time translation and multilingual memory adaptation for seamless interaction in multiple languages.

### Features

- **Translation Service**: Translate text between supported languages
- **Language Detection**: Automatically detect input language
- **Supported Languages**: English, Spanish, French, German, Japanese, Chinese, Korean, Arabic, Russian, Portuguese

### API Endpoints

#### Get Supported Languages
```http
GET /api/multilingual/languages
```

Response:
```json
{
  "languages": ["en", "es", "fr", "de", "ja", "zh", "ko", "ar", "ru", "pt"]
}
```

#### Translate Text
```http
POST /api/multilingual/translate
```

Request:
```json
{
  "text": "Hello, how are you?",
  "target_language": "es",
  "source_language": "auto"
}
```

Response:
```json
{
  "original": "Hello, how are you?",
  "translated": "[es] Hello, how are you?",
  "source_language": "auto",
  "target_language": "es"
}
```

#### Detect Language
```http
POST /api/multilingual/detect
```

Request:
```json
{
  "text": "Bonjour tout le monde"
}
```

Response:
```json
{
  "language": "fr",
  "confidence": 0.85,
  "text": "Bonjour tout le monde"
}
```

---

## 2. Emotional Intelligence (EQ)

Sentiment analysis and emotion detection to adapt Kor'tana's responses based on detected mood or emotion.

### Features

- **Sentiment Analysis**: Detect positive, negative, or neutral sentiment
- **Emotion Detection**: Identify specific emotions (joy, sadness, anger, fear, surprise)
- **Confidence Scoring**: Get confidence levels for all detections
- **Multi-emotion Analysis**: Detect multiple emotions in text

### API Endpoints

#### Analyze Sentiment
```http
POST /api/emotional-intelligence/sentiment
```

Request:
```json
{
  "text": "This is wonderful and amazing!"
}
```

Response:
```json
{
  "text": "This is wonderful and amazing!",
  "sentiment": "positive",
  "confidence": 0.75,
  "score": 0.75
}
```

#### Detect Emotion
```http
POST /api/emotional-intelligence/emotion
```

Request:
```json
{
  "text": "I am so happy and excited!"
}
```

Response:
```json
{
  "text": "I am so happy and excited!",
  "primary_emotion": "joy",
  "confidence": 0.80,
  "all_emotions": {
    "joy": 1.0
  }
}
```

#### Full Emotional Analysis
```http
POST /api/emotional-intelligence/analyze
```

Combines sentiment and emotion analysis in a single call.

---

## 3. Adaptive Content Generation

Enable Kor'tana to summarize, elaborate, or rewrite text across different industries and needs.

### Features

- **Text Summarization**: Condense text to specified length
- **Text Elaboration**: Expand text to target length
- **Style Rewriting**: Rewrite in different styles (formal, casual, technical, creative, professional)
- **Industry Adaptation**: Adapt content for specific industries

### API Endpoints

#### Summarize Text
```http
POST /api/content/summarize
```

Request:
```json
{
  "text": "Long text to summarize...",
  "max_length": 100
}
```

#### Elaborate Text
```http
POST /api/content/elaborate
```

Request:
```json
{
  "text": "Short text to expand",
  "target_length": 200
}
```

#### Rewrite Text
```http
POST /api/content/rewrite
```

Request:
```json
{
  "text": "Original text",
  "style": "formal"
}
```

Styles: `formal`, `casual`, `technical`, `creative`, `professional`

#### Adapt for Industry
```http
POST /api/content/adapt-industry
```

Request:
```json
{
  "text": "Generic text",
  "industry": "healthcare"
}
```

---

## 4. Dynamic API Integration (Plugins)

Plugin-based framework for fetching and interacting with external data sources dynamically.

### Features

- **Plugin System**: Extensible plugin architecture
- **Built-in Plugins**: Weather, Stock Market, Task Management
- **Plugin Management**: Enable/disable plugins
- **Custom Plugins**: Easy to create new plugins

### API Endpoints

#### List Plugins
```http
GET /api/plugins/list
```

Response:
```json
{
  "plugins": [
    {
      "name": "WeatherPlugin",
      "version": "1.0.0",
      "description": "Fetches current weather information",
      "parameters": ["location"],
      "enabled": true
    }
  ],
  "count": 3
}
```

#### Get Plugin Info
```http
GET /api/plugins/{plugin_name}
```

#### Execute Plugin
```http
POST /api/plugins/execute
```

Request:
```json
{
  "plugin_name": "WeatherPlugin",
  "parameters": {
    "location": "New York"
  }
}
```

Response:
```json
{
  "plugin": "WeatherPlugin",
  "result": {
    "location": "New York",
    "temperature": "22°C",
    "condition": "Partly Cloudy",
    "humidity": "65%"
  }
}
```

#### Enable/Disable Plugin
```http
POST /api/plugins/{plugin_name}/enable
POST /api/plugins/{plugin_name}/disable
```

### Creating Custom Plugins

```python
from kortana.modules.plugin_framework import BasePlugin

class MyPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.name = "MyPlugin"
    
    def execute(self, **kwargs):
        # Plugin logic here
        return {"result": "success"}
    
    def get_info(self):
        return {
            "name": self.name,
            "version": "1.0.0",
            "description": "My custom plugin",
            "parameters": ["param1", "param2"]
        }
```

---

## 5. Ethical Transparency Dashboard

Real-time, user-accessible dashboard showing how ethical decisions are made with user feedback capability.

### Features

- **Decision Logging**: Log all ethical decisions with reasoning
- **Transparency Reports**: Generate comprehensive reports
- **User Feedback**: Collect feedback on ethical decisions
- **Decision Types**: Content moderation, privacy protection, bias mitigation, transparency, fairness

### API Endpoints

#### Log Ethical Decision
```http
POST /api/ethics/log-decision
```

Request:
```json
{
  "decision_type": "content_moderation",
  "context": "User message review",
  "decision": "Approved",
  "reasoning": "Content is appropriate and respectful",
  "confidence": 0.9
}
```

#### Get All Decisions
```http
GET /api/ethics/decisions
```

#### Get Recent Decisions
```http
GET /api/ethics/decisions/recent?limit=10
```

#### Get Specific Decision
```http
GET /api/ethics/decisions/{decision_id}
```

#### Submit Feedback
```http
POST /api/ethics/feedback
```

Request:
```json
{
  "decision_id": "1234567890.123",
  "feedback": "This was a good decision"
}
```

#### Get Transparency Report
```http
GET /api/ethics/report
```

Response:
```json
{
  "total_decisions": 42,
  "decisions_by_type": {
    "content_moderation": 15,
    "privacy_protection": 10,
    "bias_mitigation": 8,
    "transparency": 5,
    "fairness": 4
  },
  "average_confidence": 0.85,
  "feedback_received": 12,
  "feedback_rate": 0.29
}
```

#### Get Decision Breakdown
```http
GET /api/ethics/breakdown
```

---

## 6. Gaming Expansion

AI assistant for interactive storytelling, tabletop RPGs, and multiplayer environments.

### Features

- **Interactive Storytelling**: Create and continue stories in various genres
- **RPG Assistant**: Campaign management, character tracking, dice rolling
- **NPC Generation**: Auto-generate non-player characters
- **Multiplayer Support**: Handle multiple players and sessions

### API Endpoints

#### Start Story
```http
POST /api/gaming/story/start
```

Request:
```json
{
  "genre": "fantasy",
  "setting": "A magical forest filled with ancient secrets"
}
```

#### Continue Story
```http
POST /api/gaming/story/continue
```

Request:
```json
{
  "player_action": "explore the mysterious cave"
}
```

#### Add Character to Story
```http
POST /api/gaming/story/character
```

#### Get Story Summary
```http
GET /api/gaming/story/summary
```

#### Create RPG Campaign
```http
POST /api/gaming/rpg/campaign
```

Request:
```json
{
  "name": "Quest for the Dragon's Hoard",
  "system": "D&D 5e"
}
```

#### Add Player
```http
POST /api/gaming/rpg/player
```

Request:
```json
{
  "player_name": "John",
  "character_name": "Aragorn",
  "character_class": "Ranger"
}
```

#### Roll Dice
```http
POST /api/gaming/rpg/roll
```

Request:
```json
{
  "dice_notation": "2d6+3"
}
```

Response:
```json
{
  "notation": "2d6+3",
  "rolls": [4, 5],
  "modifier": 3,
  "total": 12
}
```

#### Generate NPC
```http
GET /api/gaming/rpg/npc?npc_type=merchant
```

---

## 7. Community-Driven Marketplace

Module marketplace where developers can contribute and integrate their own plugins or enhancements.

### Features

- **Module Discovery**: Browse and search available modules
- **Module Submission**: Submit new modules to marketplace
- **Installation Management**: Install/uninstall modules
- **Rating System**: Rate and review modules
- **Category Organization**: Modules organized by category

### API Endpoints

#### Browse Modules
```http
GET /api/marketplace/modules?category=nlp
```

Response:
```json
{
  "modules": [
    {
      "name": "advanced-nlp",
      "version": "1.0.0",
      "author": "community-user-1",
      "description": "Advanced natural language processing capabilities",
      "category": "nlp",
      "downloads": 125,
      "rating": 4.5,
      "ratings_count": 23,
      "created_at": "2026-01-15T10:30:00",
      "updated_at": "2026-01-15T10:30:00"
    }
  ],
  "count": 1
}
```

#### Search Modules
```http
GET /api/marketplace/modules/search?query=nlp
```

#### Get Module Details
```http
GET /api/marketplace/modules/{module_name}
```

#### Submit Module
```http
POST /api/marketplace/modules/submit
```

Request:
```json
{
  "name": "my-awesome-module",
  "version": "1.0.0",
  "author": "developer-name",
  "description": "My awesome module description",
  "category": "utilities"
}
```

#### Install Module
```http
POST /api/marketplace/modules/{module_name}/install
```

#### Uninstall Module
```http
POST /api/marketplace/modules/{module_name}/uninstall
```

#### Rate Module
```http
POST /api/marketplace/modules/rate
```

Request:
```json
{
  "name": "advanced-nlp",
  "rating": 4.5
}
```

---

## Testing

All modules have been tested and verified. To run the test suite:

```bash
python test_new_routers.py
```

## Integration

All new modules are automatically integrated into the main Kor'tana FastAPI application. Simply start the server:

```bash
python -m uvicorn src.kortana.main:app --reload
```

Visit `http://127.0.0.1:8000/docs` to access the interactive API documentation.

## Architecture

Each module follows a clean architecture pattern:

```
src/kortana/modules/{module_name}/
├── __init__.py          # Module exports
├── {service}.py         # Core service logic
├── router.py            # FastAPI router with endpoints
└── {models}.py          # Data models (if needed)
```

## Future Enhancements

- Integration with real translation APIs (Google Translate, DeepL)
- Advanced emotion detection using ML models
- LLM-based content generation for better quality
- OAuth for plugin authentication
- Persistent storage for ethical decisions
- Multiplayer game state synchronization
- Marketplace payment integration
