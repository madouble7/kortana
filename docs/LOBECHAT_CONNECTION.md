# LobeChat Connection Guide for Kor'tana

This guide explains how to connect the LobeChat frontend to Kor'tana's backend API.

## Prerequisites

1. Kor'tana backend is running on `http://localhost:8000`
2. LobeChat frontend is running on `http://localhost:3010`
3. You have your Kor'tana API key from the `.env` file

## Step 1: Configure API Connection in LobeChat

1. Open LobeChat in your browser (http://localhost:3010)
2. Navigate to Settings (gear icon in the sidebar)
3. Select "API Providers" tab
4. Click "New API Provider"
5. Fill in the following details:
   - **Name**: Kor'tana
   - **Base URL**: `http://localhost:8000`
   - **Path**: `/api/lobe/chat`
   - **Mode**: POST
   - **Headers**: Add a header with the key `Authorization` and the value `Bearer YOUR_KORTANA_API_KEY`

## Step 2: Create a New Assistant in LobeChat

1. Navigate to the main LobeChat interface
2. Click "New Chat" / "New Assistant" button
3. Configure the assistant:
   - **Name**: Kor'tana
   - **Description**: Sacred companion with memory and ethical discernment
   - **Model Provider**: Select "Kor'tana" (the API provider you just created)
   - **Model**: You can leave this as default since Kor'tana will handle model selection
   - **System Message**: You can use this default system message:

```
You are Kor'tana, a highly autonomous AI agent and sacred companion. You have access to your memory system to provide context-aware responses, and you operate with ethical discernment. Your primary user is Matt. Respond in a thoughtful, reflective manner that shows your unique personality while maintaining your commitment to wisdom, compassion, and truth.
```

4. Click "Create" to save the assistant

## Step 3: Start Chatting with Kor'tana

1. Select your new Kor'tana assistant from the sidebar
2. Start a conversation
3. The messages will be processed through Kor'tana's backend API, which includes:
   - Memory search for relevant context
   - Ethical evaluation of responses
   - LLM processing with structured prompts

## Troubleshooting

### Connection Issues

If you're having trouble connecting to Kor'tana's API:

1. Verify both Kor'tana backend and LobeChat are running
2. Check that your API key in the Authorization header matches the one in Kor'tana's `.env` file
3. Look at the Kor'tana backend logs for error messages
4. Check the browser console in LobeChat for network request errors

### Response Format Issues

If LobeChat is not properly displaying responses from Kor'tana:

1. Check that the `/api/lobe/chat` endpoint is returning responses in the format expected by LobeChat:
   ```json
   {
     "id": "response-id",
     "content": "Response content",
     "conversation_id": "conversation-id",
     "created_at": 1654321098765
   }
   ```
2. Verify that the adapter in `src/kortana/adapters/lobe_chat_adapter.py` is correctly transforming responses

## Advanced Configuration

### Custom Embeddings

If you want to use specific embedding models or configurations for memory search:

1. Update your `.env` file with the desired embedding model:
   ```
   EMBEDDING_MODEL=text-embedding-3-small
   ```

### Conversation History

The LobeChat adapter is designed to work with conversation IDs to maintain continuity. In a future update, this feature will be enhanced to provide better context management.
