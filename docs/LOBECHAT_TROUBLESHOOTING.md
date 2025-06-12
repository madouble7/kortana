# LobeChat Integration Troubleshooting Guide

This guide helps you troubleshoot common issues with the LobeChat integration for Kor'tana.

## Common Issues and Solutions

### Connection Errors

#### HTTP 401 Unauthorized

**Symptoms:** LobeChat shows an error message about unauthorized access or failed API requests.

**Possible Causes and Solutions:**

1. **Incorrect API Key**: Verify that the API key in your LobeChat configuration matches the `KORTANA_API_KEY` in the `.env` file.

2. **Authorization Header Format**: Make sure the Authorization header is formatted as `Bearer YOUR_API_KEY`.

3. **Missing API Key**: Check that `KORTANA_API_KEY` is set in the `.env` file or environment variables.

#### HTTP 404 Not Found

**Symptoms:** LobeChat cannot connect to the Kor'tana API endpoint.

**Possible Causes and Solutions:**

1. **API Server Not Running**: Make sure the Kor'tana server is running. Use the provided scripts:
   ```
   ./run_kortana_api.bat
   ```
   or
   ```
   pwsh -File ./run_kortana_api.ps1
   ```

2. **Incorrect URL**: Verify the API endpoint URL is set to `http://localhost:8000/api/lobe/chat`.

3. **Port Conflict**: If another application is using port 8000, you can change it in the run scripts or kill the conflicting process.

### Response Format Issues

#### Response Not Showing in LobeChat Interface

**Symptoms:** The API responds successfully, but no message appears in LobeChat.

**Possible Causes and Solutions:**

1. **Response Format Mismatch**: Verify the response format from Kor'tana matches what LobeChat expects. The response should have these fields:
   ```json
   {
     "id": "response-id",
     "content": "Response content",
     "conversation_id": "conversation-id",
     "created_at": 1654321098765
   }
   ```

2. **Content Processing Error**: Check the browser's developer console for JavaScript errors related to content processing.

### Verification Steps

Use the included test script to verify the API is working correctly:

```bash
# Set your API key if not in environment
export KORTANA_API_KEY="your-api-key"

# Run the test script
python scripts/test_lobe_integration.py
```

This will send test messages to the API and display the responses.

## Advanced Debugging

### Checking API Server Logs

If you're experiencing issues, check the API server logs for error messages or exceptions:

1. Look at the terminal where the API server is running for error messages.

2. Check the `logs/kortana_api.log` file (if configured).

### Testing Direct API Calls

Use curl or Postman to test API calls directly:

```bash
curl -X POST http://localhost:8000/api/lobe/chat \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello, Kor'\''tana!", "conversation_id": "test-conversation"}'
```

### Memory Integration Issues

If responses don't seem to include context from previous conversations:

1. Check that memory services are properly initialized.

2. Verify conversation IDs are consistently used across messages.

3. Check the database connection configuration.

## Getting Help

If you continue to experience issues after following this troubleshooting guide:

1. Provide detailed information about the issue including error messages and steps to reproduce.

2. Include relevant logs from the API server.

3. Note any recent changes to the configuration or code.

By following these troubleshooting steps, most common integration issues can be resolved quickly.
