# Multilingual Chat Framework

Kor'tana now supports multilingual conversations with language detection and switching capabilities.

## Overview

The multilingual framework allows Kor'tana to:
- Respond in multiple languages (10+ supported)
- Automatically detect the language of user messages
- Switch languages mid-conversation
- Maintain context across language changes

## Supported Languages

| Code | Language   |
|------|------------|
| `en` | English    |
| `es` | Spanish    |
| `fr` | French     |
| `de` | German     |
| `zh` | Chinese    |
| `ja` | Japanese   |
| `ko` | Korean     |
| `pt` | Portuguese |
| `it` | Italian    |
| `ru` | Russian    |

## API Endpoints

### 1. Get Supported Languages

```http
GET /language/supported
```

**Response:**
```json
{
  "en": "English",
  "es": "Spanish",
  "fr": "French",
  ...
}
```

### 2. Switch Language

```http
POST /language/switch
Content-Type: application/json

{
  "language": "es",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "success": true,
  "language": "es",
  "language_name": "Spanish",
  "message": "Language switched to Spanish (es)"
}
```

### 3. Detect Language

```http
GET /language/detect?text=Bonjour le monde
```

**Response:**
```json
{
  "text": "Bonjour le monde",
  "detected_language": "fr",
  "language_name": "French"
}
```

## Using Multilingual Features

### Core Query Endpoint

Add a `language` parameter to specify the response language:

```http
POST /core/query
Content-Type: application/json

{
  "query": "What is the meaning of life?",
  "language": "es"
}
```

Kor'tana will respond in Spanish.

### OpenAI-Compatible Chat Endpoint

The `/v1/chat/completions` endpoint also supports the `language` parameter:

```http
POST /v1/chat/completions
Content-Type: application/json

{
  "model": "kortana-custom",
  "messages": [
    {"role": "user", "content": "Tell me about AI"}
  ],
  "language": "fr"
}
```

Kor'tana will respond in French.

## Examples

### Python Example

```python
import httpx

# Switch to Spanish
response = httpx.post(
    "http://localhost:8000/language/switch",
    json={"language": "es"}
)
print(response.json())

# Ask a question in Spanish
response = httpx.post(
    "http://localhost:8000/core/query",
    json={
        "query": "¿Qué recuerdas sobre mí?",
        "language": "es"
    }
)
print(response.json()["final_kortana_response"])
```

### JavaScript Example

```javascript
// Switch to French
const switchResponse = await fetch('http://localhost:8000/language/switch', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ language: 'fr' })
});

// Ask a question in French
const queryResponse = await fetch('http://localhost:8000/core/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'Parle-moi de toi',
    language: 'fr'
  })
});
```

### cURL Example

```bash
# Get supported languages
curl http://localhost:8000/language/supported

# Switch to German
curl -X POST http://localhost:8000/language/switch \
  -H "Content-Type: application/json" \
  -d '{"language": "de"}'

# Ask a question in German
curl -X POST http://localhost:8000/core/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Was ist künstliche Intelligenz?",
    "language": "de"
  }'
```

## Implementation Details

### Language Detection

The framework uses a simple heuristic-based language detection system that identifies languages based on character ranges:

- **Chinese**: Unicode range U+4E00 to U+9FFF
- **Japanese**: Hiragana (U+3040-U+309F) and Katakana (U+30A0-U+30FF)
- **Korean**: Hangul (U+AC00-U+D7AF)
- **Russian**: Cyrillic (U+0400-U+04FF)
- **Default**: English for Latin scripts

For production use, consider integrating a more robust language detection library.

### System Prompts

When a language is specified, Kor'tana adds a language-specific instruction to the system prompt:

```
Please respond in [Language]. All responses should be in [Language] language.
```

This ensures the LLM generates responses in the requested language.

### Language Validation

Invalid language codes automatically default to English (`en`) to ensure a graceful fallback.

## Testing

### Unit Tests

Run the language utilities tests:

```bash
pytest tests/test_language_utils.py -v
```

### Integration Tests

Run the API endpoint tests:

```bash
pytest tests/test_language_api.py -v
```

### Manual Testing

Test the API manually:

```bash
# Start the server
python -m uvicorn src.kortana.main:app --reload

# Test in another terminal
curl http://localhost:8000/language/supported
```

## Health Check

The `/health` endpoint now reports multilingual support:

```http
GET /health
```

```json
{
  "status": "healthy",
  "service": "Kor'tana",
  "version": "1.0.0",
  "message": "The Warchief's companion is ready",
  "multilingual_support": true,
  "supported_languages": ["en", "es", "fr", "de", "zh", "ja", "ko", "pt", "it", "ru"]
}
```

## Future Enhancements

Potential improvements for the multilingual framework:

1. **Advanced Language Detection**: Integrate a library like `langdetect` or `fasttext` for more accurate detection
2. **Session Persistence**: Store language preferences in user sessions or profiles
3. **Multilingual Embeddings**: Use multilingual sentence transformers for cross-language memory search
4. **Translation Memory**: Cache translations for common phrases
5. **Language-Specific Prompts**: Customize system prompts per language for better cultural context
6. **Auto-Detection**: Automatically detect language from user input and respond accordingly
7. **Mixed Language Support**: Handle code-switching and mixed-language conversations

## Notes

- Language preferences are request-based and not persisted by default
- Memory search uses the original embeddings (language-agnostic with proper multilingual models)
- LLM quality varies by language - some models perform better in English
- Consider using multilingual models (e.g., GPT-4, Claude) for best results
