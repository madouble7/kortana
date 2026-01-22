# Multimodal API Reference

Complete API reference for Kor'tana's multimodal capabilities.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. In production, you should implement appropriate authentication mechanisms.

## Endpoints

### 1. Get Capabilities

Get information about available multimodal capabilities.

**Endpoint:** `GET /multimodal/capabilities`

**Response:**
```json
{
  "supported_content_types": ["text", "voice", "audio", "image", "video", "simulation", "mixed"],
  "features": {
    "text_processing": true,
    "voice_transcription": true,
    "image_analysis": true,
    "video_processing": true,
    "simulation_generation": true,
    "mixed_content": true
  },
  "endpoints": {
    "text": "/multimodal/text",
    "voice": "/multimodal/voice",
    "image": "/multimodal/image",
    "video": "/multimodal/video",
    "simulation": "/multimodal/simulation",
    "mixed": "/multimodal/mixed",
    "upload": "/multimodal/upload"
  }
}
```

### 2. Process Text Prompt

Process a text-based prompt.

**Endpoint:** `POST /multimodal/text`

**Request Body:**
```json
{
  "text": "string (required)",
  "context": {
    "key": "value"
  }
}
```

**Response:**
```json
{
  "success": true,
  "response_id": "resp_123456",
  "prompt_id": "prompt_789012",
  "content": "Response content here",
  "content_type": "text",
  "processing_info": {
    "model_used": "gpt-4.1-nano",
    "usage": {
      "prompt_tokens": 50,
      "completion_tokens": 100,
      "total_tokens": 150
    }
  },
  "error_message": null
}
```

### 3. Process Voice/Audio Prompt

Process a voice or audio-based prompt.

**Endpoint:** `POST /multimodal/voice`

**Request Body:**
```json
{
  "audio_url": "string (optional - URL to audio file)",
  "transcription": "string (optional - text transcription)",
  "context": {
    "key": "value"
  }
}
```

**Note:** Either `audio_url` or `transcription` must be provided.

**Response:** Same structure as text prompt response.

### 4. Process Image Prompt

Process an image-based prompt.

**Endpoint:** `POST /multimodal/image`

**Request Body:**
```json
{
  "image_url": "string (required - URL to image file)",
  "caption": "string (optional - image caption)",
  "context": {
    "key": "value"
  }
}
```

**Response:** Same structure as text prompt response.

### 5. Process Video Prompt

Process a video-based prompt.

**Endpoint:** `POST /multimodal/video`

**Request Body:**
```json
{
  "video_url": "string (required - URL to video file)",
  "description": "string (optional - video description)",
  "context": {
    "key": "value"
  }
}
```

**Response:** Same structure as text prompt response.

### 6. Process Simulation Prompt

Process a simulation-based prompt.

**Endpoint:** `POST /multimodal/simulation`

**Request Body:**
```json
{
  "scenario": "string (required)",
  "parameters": {
    "param1": "value1",
    "param2": "value2"
  },
  "expected_outcomes": ["outcome1", "outcome2"],
  "duration": "string (optional - e.g., '6 months')",
  "context": {
    "key": "value"
  }
}
```

**Response:** Same structure as text prompt response.

### 7. Process Mixed Prompt

Process a multimodal prompt with multiple content types.

**Endpoint:** `POST /multimodal/mixed`

**Request Body:**
```json
{
  "contents": [
    {
      "type": "text",
      "data": "Text content",
      "encoding": "utf-8",
      "metadata": {}
    },
    {
      "type": "image",
      "data": "https://example.com/image.jpg",
      "encoding": "url",
      "metadata": {}
    }
  ],
  "primary_type": "text",
  "instruction": "string (optional)",
  "context": {
    "key": "value"
  }
}
```

**Content Types:**
- `text`: Text content
- `image`: Image content (URL or base64)
- `audio`: Audio content (URL or base64)
- `video`: Video content (URL or base64)
- `simulation`: Simulation data

**Response:** Same structure as text prompt response.

### 8. Upload Media File

Upload a media file for processing.

**Endpoint:** `POST /multimodal/upload`

**Request:** Multipart form data

**Form Fields:**
- `file`: The media file (required)
- `content_type`: Type of content - "image", "audio", "video" (required)
- `caption`: Optional caption or description (optional)

**Response:**
```json
{
  "success": true,
  "filename": "uploaded_file.jpg",
  "content_type": "image",
  "size": 102400,
  "caption": "Optional caption",
  "message": "File uploaded successfully"
}
```

## Response Structure

All processing endpoints return a response with the following structure:

```typescript
{
  success: boolean;          // Whether the request was successful
  response_id: string;       // Unique response identifier
  prompt_id: string;         // Identifier of the original prompt
  content: string;           // Response content (text)
  content_type: string;      // Type of response content
  processing_info: {         // Information about processing
    model_used?: string;     // Model that generated the response
    usage?: {                // Token usage statistics
      prompt_tokens: number;
      completion_tokens: number;
      total_tokens: number;
    };
    primary_content_type?: string;  // Primary content type of input
  };
  error_message: string | null;  // Error message if failed
}
```

## Error Responses

### 400 Bad Request

Invalid request parameters.

```json
{
  "detail": "Error message describing what's wrong"
}
```

### 422 Unprocessable Entity

Request body doesn't match the expected schema.

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error

Server error during processing.

```json
{
  "detail": "Error message"
}
```

## Content Type Details

### Text Content

**Format:**
```json
{
  "type": "text",
  "data": "The actual text content"
}
```

### Image Content

**URL Format:**
```json
{
  "type": "image",
  "data": "https://example.com/image.jpg",
  "encoding": "url"
}
```

**Base64 Format:**
```json
{
  "type": "image",
  "data": "base64EncodedImageData...",
  "encoding": "base64"
}
```

**Supported Formats:** JPG, JPEG, PNG, GIF, WebP, BMP

### Audio Content

**URL Format:**
```json
{
  "type": "audio",
  "data": "https://example.com/audio.mp3",
  "encoding": "url"
}
```

**Base64 Format:**
```json
{
  "type": "audio",
  "data": "base64EncodedAudioData...",
  "encoding": "base64"
}
```

**Supported Formats:** MP3, WAV, OGG, M4A, FLAC, AAC

### Video Content

**URL Format:**
```json
{
  "type": "video",
  "data": "https://example.com/video.mp4",
  "encoding": "url"
}
```

**Supported Formats:** MP4, WebM, AVI, MOV, MKV

### Simulation Content

**Format:**
```json
{
  "type": "simulation",
  "data": {
    "scenario": "Description of scenario",
    "parameters": {
      "param1": "value1"
    },
    "expected_outcomes": ["outcome1"],
    "context": "Additional context",
    "duration": "Time frame"
  }
}
```

## Rate Limiting

Currently, there are no rate limits. In production, implement appropriate rate limiting based on your infrastructure.

## Best Practices

1. **Use URLs for large files**: Prefer URLs over base64 for files > 1MB
2. **Provide context**: Include relevant context to improve response quality
3. **Handle errors**: Always check the `success` field in responses
4. **Validate inputs**: Validate data before sending to avoid errors
5. **Use appropriate timeouts**: Some operations (e.g., video processing) may take longer

## Code Examples

### cURL

```bash
# Text prompt
curl -X POST http://localhost:8000/multimodal/text \
  -H "Content-Type: application/json" \
  -d '{"text": "What is AI?"}'

# Image prompt
curl -X POST http://localhost:8000/multimodal/image \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/image.jpg", "caption": "A chart"}'

# Upload file
curl -X POST http://localhost:8000/multimodal/upload \
  -F "file=@image.jpg" \
  -F "content_type=image" \
  -F "caption=My image"
```

### Python

```python
import requests

# Text prompt
response = requests.post(
    "http://localhost:8000/multimodal/text",
    json={"text": "What is AI?"}
)
result = response.json()
```

### JavaScript

```javascript
// Text prompt
fetch('http://localhost:8000/multimodal/text', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ text: 'What is AI?' })
})
.then(res => res.json())
.then(data => console.log(data));
```

## Versioning

Current API version: v1

The API follows semantic versioning. Breaking changes will result in a new major version.

## Support

For issues or questions:
- Check the [Usage Examples](MULTIMODAL_USAGE_EXAMPLES.md)
- Review the [Integration Guide](MULTIMODAL_INTEGRATION_GUIDE.md)
- Create an issue in the repository
