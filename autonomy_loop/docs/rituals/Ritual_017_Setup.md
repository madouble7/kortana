# Ritual_017: Gemini Multimodal Foundation - Setup Guide

This guide details how to set up your environment and backend to utilize Kor'tana's new Gemini multimodal capabilities with AWS Secrets Manager.

## 🎯 Objectives

*   Securely configure your Google API Key via AWS Secrets Manager.
*   Run the FastAPI backend with multimodal features enabled.
*   Test the newly integrated Gemini API endpoints.

## 🔐 Step 1: Configure Google API Key in AWS Secrets Manager

**Important:** Your Google API key should be stored in AWS Secrets Manager, and the backend will retrieve it using its ARN.

1.  **Create a Secret in AWS Secrets Manager:**
    *   Go to the AWS Secrets Manager console.
    *   Click "Store a new secret".
    *   Choose "Other type of secret".
    *   For "Secret value", enter your Google API Key directly (e.g., `AIzaSy...`). **Do NOT store it as key/value pairs unless specifically required by your secrets_loader configuration.**
    *   For "Secret name", use a consistent naming convention, e.g., `kortana/prod/GOOGLE_API_KEY` or `kortana/dev/GOOGLE_API_KEY`.
    *   **Crucially, note down the ARN (Amazon Resource Name) of this secret.** It will look like `arn:aws:secretsmanager:YOUR_AWS_REGION:YOUR_AWS_ACCOUNT_ID:secret:kortana/prod/GOOGLE_API_KEY-XXXXXX`.

2.  **Ensure IAM Permissions:**
    *   Your backend's ECS Task Role (or local IAM user if running directly on EC2/ECS) must have `secretsmanager:GetSecretValue` permission for the specific secret ARN.
    *   If using KMS for encryption, ensure `kms:Decrypt` permissions are also granted to the KMS key used by the secret.

## ⚙️ Step 2: Configure Environment Variables

Update your `.env` file within the `services/local-api-v2` directory to point to your AWS Secrets Manager ARN.

```bash
# services/local-api-v2/.env
# ... existing llm, asr, server, rag, logging vars ...

# Google API Key sourced from AWS Secrets Manager ARN
# REPLACE WITH YOUR ACTUAL AWS SECRETS MANAGER ARN
GOOGLE_API_KEY_SECRET_ARN="arn:aws:secretsmanager:YOUR_AWS_REGION:YOUR_AWS_ACCOUNT_ID:secret:kortana/prod/GOOGLE_API_KEY-EXAMPLE_SUFFIX"

# Optional: If you want to use a logical name and let secrets_loader resolve
# GOOGLE_API_KEY="GOOGLE_API_KEY" # This will try 'kortana/dev/GOOGLE_API_KEY', etc.

# Configuration for secrets_loader (important for local development if not using ARN)
# ENV_PREFIX=kortana/dev             # If your secrets are named kortana/dev/MY_KEY
# SECRETS_BLOB=secrets.blob.json    # Optional: for a local JSON fallback file
# SECRETS_TTL_SECONDS=120           # Cache TTL for secrets
```

## 🚀 Step 3: Start the Backend Server

Navigate to the backend directory and start the FastAPI application.

```bash
cd c:\kortana\services\local-api-v2
# (Optional: activate your Python virtual environment if not using Docker)
# . .venv/bin/activate
uvicorn app.main:app --reload
```

## ✅ Step 4: Verify Backend Health and Functionality

Use `curl` commands to test the new endpoints.

### 1. Test Multimodal Health Check

```bash
curl http://localhost:8000/api/gemini/health
```
**Expected Output:** `{"status":"ok", "gemini_client_ready":true, "model_id":"gemini-2.5-flash"}` (or your configured default model). If `gemini_client_ready` is `false`, check your API key configuration and backend logs.

### 2. Test Chat Endpoint

```bash
curl -X POST http://localhost:8000/api/gemini/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-2.5-flash",
    "messages": [
      {"role": "user", "content": "Hello Kor'\''tana! How are you today?"}
    ],
    "use_thinking_mode": false
  }'
```

### 3. Test Audio Transcription (replaces faster-whisper)

```bash
# Create a dummy audio file for testing
echo "This is a test audio for transcription." | ffmpeg -f s16le -ar 16000 -ac 1 -i - test_audio.wav

curl -X POST http://localhost:8000/api/gemini/transcribe \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_audio.wav;type=audio/wav"
```

### 4. Test Search Grounding

```bash
curl -X POST http://localhost:8000/api/gemini/search-grounding \
  -H "Content-Type: application/json" \
  -d '{"query": "Who won the most bronze medals during the Paris Olympics in 2024?"}'
```

### 5. Test Maps Grounding (optional: include lat/lon for better results)

```bash
curl -X POST http://localhost:8000/api/gemini/maps-grounding \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the best coffee shops near me?", "latitude": 34.0522, "longitude": -118.2437}'
```

### 6. Test Text-to-Speech

```bash
curl -X POST http://localhost:8000/api/gemini/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is Kor'\''tana speaking!"}' \
  -o tts_output.mp3 # Save the audio output
```
Then play `tts_output.mp3` to verify.

### 7. Test Image Analysis

```bash
# Create a dummy base64 image (replace with your actual base64 image data)
DUMMY_BASE64_IMAGE="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

curl -X POST http://localhost:8000/api/gemini/analyze-image \
  -H "Content-Type: application/json" \
  -d '{
    "image": {
      "base64": "'"$DUMMY_BASE64_IMAGE"'",
      "mimeType": "image/png"
    },
    "prompt": "Describe this image."
  }'
```

### 8. Test Image Generation (using gemini-2.5-flash-image)

```bash
curl -X POST http://localhost:8000/api/gemini/generate-image \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A robot holding a red skateboard."
  }' \
  -o generated_image.json # This will save a JSON with base64 image data
```
You will need to extract the `image_base64` from the JSON and decode it to view the image.

### 9. Test Cache Refresh (Admin Function)

```bash
# You need an admin token for this. Assuming you have configured authentication.
# For local testing without full auth, you might temporarily remove 'require_admin' from the endpoint.
# With auth, you'd include an Authorization: Bearer <ADMIN_JWT_TOKEN> header.
curl -X POST http://localhost:8000/secrets/refresh
```

## 🌐 Step 5: Frontend Integration Status

*   **ChatInterface**: Now uses `/api/gemini/chat` and `/api/gemini/chat-text-stream` (unified endpoints). Audio transcription in chat now uses Gemini via `/api/gemini/transcribe`.
*   **ImageAnalyzer**: Uses `/api/gemini/analyze-image`.
*   **VideoAnalyzer**: Uses `/api/gemini/analyze-video`.
*   **SearchGrounding**: Uses `/api/gemini/search-grounding`.
*   **MapsGrounding**: Uses `/api/gemini/maps-grounding`.
*   **TextToSpeech**: Uses `/api/gemini/tts`.
*   **ImageGenerator**: Uses `/api/gemini/generate-image`.
*   **VideoGenerator**: Uses `/api/gemini/generate-video` and `/api/gemini/ops/video/{operation_name}`.
*   **ImageEditor**: Uses `/api/gemini/edit-image`.
*   **LiveConversation**: The backend endpoint `/api/gemini/ws/live-conversation` is a placeholder. Full Live API integration usually requires a direct client-to-Gemini connection or a sophisticated backend relay, and is pending in this backend implementation.

## 🦅 FOR KOR'TANA!

**Ritual_017 Status:** ✅ **AWS SECRETS MANAGER INTEGRATION COMPLETE**

The foundation is now securely laid. Proceed with confidence.
