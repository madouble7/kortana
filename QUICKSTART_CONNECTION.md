# Kor'tana ↔ LobeChat Connection Guide

## Current Status
✅ **Kor'tana Backend**: Ready with LobeChat adapter at `/adapters/lobechat/chat`
✅ **Connection Documentation**: Available in `docs/LOBECHAT_CONNECTION.md`
✅ **Test Scripts**: Created for validation

## Step 1: Start Kor'tana Backend

Open Command Prompt and run:
```cmd
cd c:\project-kortana
python src\kortana\main.py
```

Or using uvicorn:
```cmd
cd c:\project-kortana\src
python -m uvicorn kortana.main:app --reload --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Started reloader process
```

**Verify Backend:**
- Open browser to http://localhost:8000/health
- Should see: `{"status":"healthy","service":"Kor'tana","version":"1.0.0"}`

## Step 2: Start LobeChat Frontend

In a NEW Command Prompt window:
```cmd
cd c:\project-kortana\lobechat-frontend
npm run dev
```

**Expected Output:**
```
Local:   http://localhost:3010
Network: http://192.168.x.x:3010
```

## Step 3: Configure LobeChat to Connect to Kor'tana

1. **Open LobeChat**: http://localhost:3010

2. **Access Settings**:
   - Click the gear icon (⚙️) in the sidebar
   - Navigate to "Language Model" settings

3. **Add Custom Provider**:
   - Click "Add Custom Provider" or "+"
   - **Provider Name**: `Kor'tana`
   - **Base URL**: `http://localhost:8000`
   - **API Endpoint**: `/adapters/lobechat/chat`
   - **Method**: POST
   - **API Key**: Leave blank or use "test-key" (current setup doesn't require authentication)

4. **Save Configuration**

## Step 4: Create Kor'tana Chat

1. **New Conversation**:
   - Click "New Chat" in LobeChat
   - Select "Kor'tana" as the model provider
   - Model: Any (Kor'tana handles this internally)

2. **Test Message**:
   - Type: "Hello Kor'tana, are you connected?"
   - Send the message

**Expected Response:**
```
Kor'tana (via LobeChat): Hello Kor'tana, are you connected?
```

## Troubleshooting

### Backend Issues
- **Port 8000 in use**: Try `netstat -an | findstr :8000` to check
- **Import errors**: Run `pip install fastapi uvicorn` in your Python environment
- **Module not found**: Ensure you're in the `c:\project-kortana` directory

### Frontend Issues
- **Port 3010 in use**: LobeChat will auto-assign a different port
- **Connection refused**: Verify Kor'tana backend is running on port 8000
- **CORS errors**: The backend has CORS enabled for all origins

### Connection Issues
- **No response**: Check browser dev tools (F12) for network errors
- **Wrong endpoint**: Ensure the API endpoint is exactly `/adapters/lobechat/chat`
- **Format errors**: The backend expects LobeChat's message format

## Testing with curl

You can test the connection manually:
```cmd
curl -X POST http://localhost:8000/adapters/lobechat/chat ^
  -H "Content-Type: application/json" ^
  -d "{\\"messages\\": [{\\"role\\": \\"user\\", \\"content\\": \\"Hello\\"}]}"
```

## Next Steps

Once connected successfully:
1. The basic adapter will echo messages back
2. Future integration will connect to Kor'tana's full AI pipeline
3. Memory and ethical evaluation will be added to responses

## Current Limitations

- **Simple Echo**: The adapter currently echoes messages (proof of concept)
- **No Authentication**: API key validation is basic
- **No Memory**: Full memory integration pending
- **No AI Processing**: Real LLM integration coming next

The foundation is complete - now we can build upon this connection!
