# Multimodal AI Capabilities for Kor'tana

## Overview

Kor'tana now supports advanced multimodal AI prompt generation capabilities, enabling the system to create, process, and respond to prompts that include:

- **Text**: Traditional text-based queries and responses
- **Voice/Audio**: Speech input with transcription support
- **Images**: Visual content analysis using GPT-4 Vision
- **Video**: Video content processing and analysis
- **Simulation**: Scenario-based queries for predictive analysis

## Features

### 1. Modular Architecture

The multimodal system is designed with modularity in mind:

- **Core Models**: Defined in `src/kortana/core/multimodal/models.py`
- **Processors**: Content-specific processors in `src/kortana/core/multimodal/processors.py`
- **Prompt Generator**: Unified interface in `src/kortana/core/multimodal/prompt_generator.py`
- **LLM Integration**: Enhanced clients in `src/kortana/llm_clients/`
- **API Layer**: RESTful endpoints in `src/kortana/api/routers/multimodal_router.py`

### 2. Content Type Support

#### Text
Standard text processing with context awareness and memory integration.

#### Voice/Audio
- Supports both audio URLs and base64-encoded audio data
- Optional transcription input
- Integration with OpenAI Whisper for speech-to-text

#### Images
- URL-based image input
- Base64-encoded image data support
- GPT-4 Vision integration for image understanding
- Optional captions for additional context

#### Video
- URL-based video input
- Optional descriptions
- Frame-by-frame analysis capabilities

#### Simulation
- Scenario-based queries
- Parameterized simulations
- Expected outcomes tracking
- Duration and context support

### 3. Memory Integration

All multimodal interactions can be:
- Stored in Kor'tana's memory system
- Enhanced with relevant historical context
- Searched and retrieved for future reference

### 4. Flexible API

Multiple endpoints for different use cases:
- `/multimodal/text` - Text-based prompts
- `/multimodal/voice` - Voice/audio input
- `/multimodal/image` - Image analysis
- `/multimodal/video` - Video processing
- `/multimodal/simulation` - Scenario simulations
- `/multimodal/mixed` - Combined content types
- `/multimodal/upload` - Media file uploads
- `/multimodal/capabilities` - Feature discovery

## Architecture

### Data Flow

```
User Input → API Endpoint → MultimodalService → Processor → LLM Client → Response
                ↓                                                ↓
            Database ←—————————— Memory Integration ←——————————┘
```

### Components

1. **Models** (`models.py`)
   - `ContentType`: Enum of supported content types
   - `MultimodalContent`: Individual content pieces
   - `MultimodalPrompt`: Complete multimodal prompt
   - `MultimodalResponse`: Response structure
   - `SimulationQuery`: Simulation-specific queries

2. **Processors** (`processors.py`)
   - `TextProcessor`: Handles text content
   - `VoiceProcessor`: Processes audio data
   - `ImageProcessor`: Handles image content
   - `VideoProcessor`: Processes video data
   - `SimulationProcessor`: Handles simulation queries
   - `MultimodalProcessor`: Orchestrates all processors

3. **Prompt Generator** (`prompt_generator.py`)
   - Creates prompts from various content types
   - Validates prompt structure
   - Enhances with context and memory
   - Converts to LLM-compatible format

4. **LLM Clients**
   - `BaseLLMClient`: Extended with multimodal capabilities
   - `MultimodalOpenAIClient`: GPT-4 Vision and Whisper support
   - Factory methods for client creation

5. **API Layer** (`multimodal_router.py`)
   - RESTful endpoints for all content types
   - Request/response validation
   - Error handling
   - File upload support

6. **Service Layer** (`multimodal_service.py`)
   - Orchestrates prompt processing
   - Manages LLM client selection
   - Integrates with memory system
   - Handles response generation

## Usage Examples

See [MULTIMODAL_USAGE_EXAMPLES.md](MULTIMODAL_USAGE_EXAMPLES.md) for detailed code examples.

## API Reference

See [MULTIMODAL_API_REFERENCE.md](MULTIMODAL_API_REFERENCE.md) for complete API documentation.

## Integration Guide

See [MULTIMODAL_INTEGRATION_GUIDE.md](MULTIMODAL_INTEGRATION_GUIDE.md) for step-by-step integration instructions.

## Testing

Comprehensive test suite includes:
- Unit tests for models (`tests/test_multimodal_models.py`)
- Unit tests for processors (`tests/test_multimodal_processors.py`)
- Unit tests for prompt generator (`tests/test_multimodal_prompt_generator.py`)
- Integration tests for API (`tests/test_multimodal_api.py`)

Run tests with:
```bash
pytest tests/test_multimodal_*.py
```

## Performance Considerations

- **Image Processing**: GPT-4 Vision calls are more expensive than text-only
- **Audio Processing**: Transcription adds latency but improves accuracy
- **Video Processing**: May require frame extraction for detailed analysis
- **Memory Usage**: Large media files should be referenced by URL when possible

## Security Considerations

- All uploaded files should be validated for type and size
- Base64 data should be limited in size to prevent DoS
- URLs should be validated before accessing
- Sensitive content should not be stored in logs

## Future Enhancements

Potential future additions:
- Real-time video streaming support
- Advanced simulation engines
- Multi-language transcription
- Custom vision models
- Batch processing capabilities

## Support

For questions or issues:
1. Check the documentation in `docs/`
2. Review test examples in `tests/`
3. Consult the API reference
4. Create an issue in the repository
