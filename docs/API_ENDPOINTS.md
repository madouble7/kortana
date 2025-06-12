# Kor'tana API Documentation for LobeChat Integration

This document outlines the API endpoints provided by Kor'tana's backend for integration with the LobeChat frontend.

## Base URL

All API endpoints are relative to the base URL:

```
http://localhost:8000
```

## Authentication

Authentication is required for all API endpoints except for health checks. Authentication is performed using an API key provided in the `Authorization` header:

```
Authorization: Bearer YOUR_API_KEY
```

The API key should be configured in the `.env` file as `KORTANA_API_KEY`.

## Error Handling

All endpoints return standard HTTP status codes:

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Invalid or missing API key
- `403 Forbidden`: Valid API key but insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error responses follow this format:

```json
{
  "error": {
    "code": "error_code",
    "message": "Human-readable error message",
    "details": { /* Optional additional error details */ }
  }
}
```

## API Endpoints

### Health Check

#### GET /health

Check if the Kor'tana API is operational.

**Response**:

```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

### Core Query Endpoint

#### POST /core/query

This is the main endpoint for interacting with Kor'tana's core logic, including memory search and LLM-powered responses.

**Request**:

```json
{
  "query": "What do you remember about our first conversation?"
}
```

**Response**:

```json
{
  "original_query": "What do you remember about our first conversation?",
  "context_from_memory": [
    "Our first conversation was on June 8, 2025. You introduced yourself as Matt and we discussed your project goals.",
    "During our first meeting, you mentioned your interest in AI companions and your vision for Kor'tana."
  ],
  "ethical_evaluation": {
    "is_potentially_arrogant": false,
    "flags": [],
    "reasoning": []
  },
  "final_response": "I remember our first conversation on June 8, 2025. You introduced yourself as Matt and we talked about your vision for the Kor'tana project. You were particularly interested in creating an AI companion with ethical discernment and a strong memory system. You also mentioned wanting Kor'tana to evolve and learn over time. Is there something specific from that conversation you'd like to explore further?"
}
```

### Memory Management

#### POST /memories/

Create a new memory in Kor'tana's memory system.

**Request**:

```json
{
  "memory_type": "INTERACTION",
  "title": "Discussion about autonomy",
  "content": "Matt expressed his view that true autonomy requires both decision-making ability and self-directed action.",
  "metadata": {
    "source": "conversation",
    "importance": 0.8,
    "tags": ["autonomy", "philosophy"]
  },
  "sentiments": [
    {
      "emotion": "curiosity",
      "intensity": 7
    }
  ]
}
```

**Response**:

```json
{
  "id": 42,
  "memory_type": "interaction",
  "title": "Discussion about autonomy",
  "content": "Matt expressed his view that true autonomy requires both decision-making ability and self-directed action.",
  "metadata": {
    "source": "conversation",
    "importance": 0.8,
    "tags": ["autonomy", "philosophy"]
  },
  "sentiments": [
    {
      "id": 17,
      "emotion": "curiosity",
      "intensity": 7,
      "created_at": "2025-06-12T14:30:00Z"
    }
  ],
  "created_at": "2025-06-12T14:30:00Z",
  "updated_at": "2025-06-12T14:30:00Z",
  "accessed_at": "2025-06-12T14:30:00Z"
}
```

#### GET /memories/{memory_id}

Retrieve a specific memory by its ID.

**Response**: Same format as the POST response above.

#### GET /memories/

Retrieve a paginated list of memories.

**Query parameters**:
- `skip`: Number of items to skip (default: 0)
- `limit`: Maximum number of items to return (default: 20)

**Response**:

```json
[
  {
    "id": 42,
    "memory_type": "interaction",
    "title": "Discussion about autonomy",
    "content": "Matt expressed his view that true autonomy requires both decision-making ability and self-directed action.",
    "metadata": {
      "source": "conversation",
      "importance": 0.8,
      "tags": ["autonomy", "philosophy"]
    },
    "sentiments": [...],
    "created_at": "2025-06-12T14:30:00Z",
    "updated_at": "2025-06-12T14:30:00Z",
    "accessed_at": "2025-06-12T14:30:00Z"
  },
  {...}
]
```

#### PUT /memories/{memory_id}

Update an existing memory.

**Request**:

```json
{
  "title": "Updated title",
  "content": "Updated content",
  "metadata": {
    "importance": 0.9
  }
}
```

**Response**: Updated memory object in the same format as GET.

#### DELETE /memories/{memory_id}

Delete a memory by its ID.

**Response**: Deleted memory object.

### Chat Integration

#### POST /chat

Send a chat message and receive a response. This endpoint is specifically designed for LobeChat integration.

**Request**:

```json
{
  "message": "What do you remember about our project goals?",
  "conversation_id": "conv_12345", // Optional, for continuity
  "user": "Matt", // Optional, defaults to KORTANA_USER_NAME in .env
  "include_memory": true // Optional, whether to include memory context
}
```

**Response**:

```json
{
  "response": "Based on our conversations, I remember that our project goals include building a highly autonomous AI agent with strong ethical foundations, creating a memory system that allows for contextual responses, and developing a system that can learn and evolve over time. We've been focusing on completing the core infrastructure in phases, with Phase 3 currently emphasizing complexity reduction, test coverage, and performance optimization. Is there a specific aspect of our project goals you'd like to explore further?",
  "conversation_id": "conv_12345",
  "memories_accessed": [
    {
      "id": 24,
      "title": "Project goals discussion",
      "relevance_score": 0.92
    }
  ],
  "metadata": {
    "processing_time_ms": 320,
    "tokens_used": 246
  }
}
```

## LobeChat Integration Guide

### Step 1: Configure API Connection

In your LobeChat configuration:

1. Set the "API Endpoint" to `http://localhost:8000/chat`
2. Configure the "Authorization" header with your Kor'tana API key
3. Use the POST method

### Step 2: Message Format Mapping

Map LobeChat's message format to Kor'tana's expected format:

```javascript
// Example transformation function
function transformLobeMessageToKortana(lobeMessage) {
  return {
    message: lobeMessage.content,
    conversation_id: lobeMessage.conversationId,
    user: lobeMessage.sender === 'user' ? 'Matt' : 'Kor\'tana',
    include_memory: true
  };
}
```

### Step 3: Response Handling

Map Kor'tana's response back to LobeChat's expected format:

```javascript
// Example response handler
function handleKortanaResponse(kortanaResponse) {
  return {
    content: kortanaResponse.response,
    conversationId: kortanaResponse.conversation_id,
    // Add any additional LobeChat-specific fields
  };
}
```

## Rate Limiting

The API enforces rate limiting of 60 requests per minute per API key. Exceeding this limit will result in a `429 Too Many Requests` response.

## Conclusion

This API documentation provides all necessary details for integrating Kor'tana with LobeChat. For any issues or additional requirements, please update the blueprint or contact the development team.
