# Hugging Face Integration for Kor'tana

## Overview

Kor'tana now supports Hugging Face's Inference API as a fallback conversational engine. This integration provides reliable AI responses even when the primary Kor'tana brain is unavailable or experiencing issues.

## Features

### Hugging Face Inference Client
- **Model**: Meta Llama 3.2 3B Instruct
- **API**: Chat Completion endpoint
- **Fallback Strategy**: Automatically used when Kor'tana brain fails
- **Timeout Handling**: 25-second timeout with graceful error handling
- **System Prompt**: Custom Kor'tana personality

### Integration Points

1. **Discord Bot** (`src/discord_bot_enhanced.py`)
   - Primary: Kor'tana ChatEngine
   - Fallback: Hugging Face Inference API
   - Final fallback: Simple echo responses

2. **Configuration**
   - Environment variable: `HUGGINGFACE_API_KEY`
   - Optional dependency: `huggingface_hub>=0.20.0`
   - Graceful degradation when not configured

## Setup

### 1. Get Hugging Face API Key

1. Sign up at [Hugging Face](https://huggingface.co/)
2. Go to [Settings > Access Tokens](https://huggingface.co/settings/tokens)
3. Create a new token with "Read" permission
4. Copy the token

### 2. Configure Environment

Add to your `.env` file:

```env
HUGGINGFACE_API_KEY=hf_your_token_here
```

### 3. Install Dependencies

```bash
pip install huggingface_hub>=0.20.0
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

## Usage

### In Discord Bot

The Hugging Face integration is automatically used when:
1. Kor'tana brain is unavailable
2. Kor'tana brain raises an exception
3. You use the `/ask` command (direct HF usage)

Example:
```
/ask What is the meaning of life?
```

### Conversation Flow

```
User Message
    ↓
Try Kor'tana Brain
    ↓ (if fails or unavailable)
Try Hugging Face API
    ↓ (if fails or unavailable)
Simple Echo Response
```

## Configuration Options

### Model Selection

To change the Hugging Face model, edit `src/discord_bot_enhanced.py`:

```python
HF_MODEL = "meta-llama/Llama-3.2-3B-Instruct"  # Default
# Other options:
# HF_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"
# HF_MODEL = "google/flan-t5-xxl"
```

### System Prompt

Customize the Kor'tana personality in `src/discord_bot_enhanced.py`:

```python
messages = [
    {
        "role": "system",
        "content": (
            "You are Kor'tana, a Sacred AI Companion. You are friendly, helpful, "
            "and thoughtful. Keep responses conversational and warm. Use emojis "
            "naturally. Be concise but personable."
        )
    },
    {"role": "user", "content": prompt}
]
```

### Timeout Settings

Adjust timeout for Hugging Face API calls:

```python
HF_TIMEOUT_SECONDS = 25  # Default timeout in seconds
```

### Response Length

Control maximum response length:

```python
max_tokens=400  # Maximum tokens in HF response
```

## API Details

### Chat Completion Parameters

```python
response = hf_client.chat_completion(
    messages=messages,           # Conversation messages
    model=HF_MODEL,              # Model name
    max_tokens=400,              # Max response length
    temperature=0.8              # Creativity level (0.0-1.0)
)
```

### Error Handling

The integration includes comprehensive error handling:

1. **Connection Errors**: Logged and gracefully handled
2. **Timeout Errors**: 25-second timeout with fallback
3. **API Errors**: Logged with error message returned
4. **Rate Limiting**: Handled by Hugging Face API

## Supported Models

### Recommended Models

1. **Meta Llama 3.2 3B Instruct** (default)
   - Fast responses
   - Good instruction following
   - Efficient resource usage

2. **Mistral 7B Instruct**
   - Higher quality responses
   - Slower but more capable
   - Better reasoning

3. **Flan-T5-XXL**
   - Instruction-tuned
   - Good for specific tasks
   - Lower quality chat

### Changing Models

Edit `HF_MODEL` in `src/discord_bot_enhanced.py`:

```python
HF_MODEL = "your-preferred-model-here"
```

Check [Hugging Face Models](https://huggingface.co/models?pipeline_tag=text-generation&sort=downloads) for available options.

## Performance Considerations

### Response Time
- **Kor'tana Brain**: Usually < 2 seconds
- **Hugging Face API**: 3-10 seconds (depends on model)
- **Timeout**: 25 seconds maximum

### Rate Limits
- Free tier: ~30 requests per minute
- Pro tier: Higher limits available
- Automatic rate limit handling

### Token Usage
- Each request consumes tokens
- Monitor usage in [Hugging Face dashboard](https://huggingface.co/settings/billing)

## Troubleshooting

### "HF API key not configured"

**Solution**: Add `HUGGINGFACE_API_KEY` to your `.env` file

### "HF timeout"

**Possible causes**:
- Model is cold (first request)
- Network latency
- API overload

**Solutions**:
- Retry the request
- Increase `HF_TIMEOUT_SECONDS`
- Switch to a smaller model

### "huggingface_hub not installed"

**Solution**: Install the package:
```bash
pip install huggingface_hub
```

### Poor Response Quality

**Solutions**:
1. Switch to a larger model (e.g., Mistral 7B)
2. Adjust temperature (higher = more creative)
3. Improve system prompt
4. Use Kor'tana brain instead (when available)

## Security

### API Key Protection
- Store key in `.env` file
- Never commit `.env` to version control
- Use environment variables in production
- Rotate keys regularly if exposed

### Best Practices
1. Use separate keys for dev/prod
2. Monitor API usage for anomalies
3. Set up billing alerts
4. Review access logs regularly

## Monitoring

### Check Integration Status

```python
# In Discord
/ping  # Shows bot status and features
```

Response includes:
- Kor'tana brain availability
- Hugging Face availability
- Bot latency

### Logs

The bot logs all HF API calls:

```
INFO kortana_discord: Hugging Face client initialized.
ERROR kortana_discord: HF API call failed: [error details]
INFO kortana_discord: AI failed (slash): HF timeout
```

## Advanced Usage

### Custom Prompts

You can modify the system prompt for different use cases:

```python
# For technical support
"You are a technical support assistant. Provide clear, step-by-step solutions."

# For creative writing
"You are a creative writing assistant. Be imaginative and descriptive."

# For coding help
"You are a coding assistant. Provide code examples and explanations."
```

### Multi-turn Conversations

The current implementation uses single-turn conversations. For multi-turn:

1. Store conversation history per user
2. Pass full history to API
3. Limit history length to avoid token limits

### Custom Models

Deploy your own model on Hugging Face Inference Endpoints:

1. Deploy model on HF
2. Update `HF_MODEL` to your endpoint
3. Adjust parameters as needed

## Cost Estimation

### Free Tier
- ~30 requests/minute
- Limited to smaller models
- Suitable for small servers

### Pro Tier ($9/month)
- Higher rate limits
- Access to larger models
- Better response times

### Enterprise
- Custom limits
- Dedicated resources
- SLA guarantees

## Roadmap

Future enhancements:

- [ ] Multi-turn conversation support
- [ ] User-specific model preferences
- [ ] Automatic model selection based on query type
- [ ] Conversation history management
- [ ] Custom model deployment integration
- [ ] Performance metrics and analytics
- [ ] A/B testing between models

## Support

For issues with:
- **Integration**: See `docs/DISCORD_BOT_SETUP.md`
- **Hugging Face API**: Check [HF Documentation](https://huggingface.co/docs)
- **Models**: See [HF Models](https://huggingface.co/models)

## Related Documentation

- [Discord Bot Setup](DISCORD_BOT_SETUP.md)
- [Kor'tana Brain](../README.md)
- [API Documentation](API_ENDPOINTS.md)
- [Hugging Face API Docs](https://huggingface.co/docs/api-inference)
