# Multimodal Usage Examples

This document provides practical examples of using Kor'tana's multimodal capabilities.

## Table of Contents
- [Text Prompts](#text-prompts)
- [Voice/Audio Prompts](#voiceaudio-prompts)
- [Image Prompts](#image-prompts)
- [Video Prompts](#video-prompts)
- [Simulation Prompts](#simulation-prompts)
- [Mixed Multimodal Prompts](#mixed-multimodal-prompts)
- [Programmatic Usage](#programmatic-usage)

## Text Prompts

### Basic Text Query

```python
import requests

response = requests.post(
    "http://localhost:8000/multimodal/text",
    json={
        "text": "What are the key trends in AI for 2024?",
        "context": {
            "user": "researcher",
            "domain": "artificial_intelligence"
        }
    }
)

result = response.json()
print(result["content"])
```

### Text with Memory Context

```python
response = requests.post(
    "http://localhost:8000/multimodal/text",
    json={
        "text": "What did we discuss about neural networks last time?",
        "context": {
            "use_memory": True,
            "session_id": "session_123"
        }
    }
)
```

## Voice/Audio Prompts

### Audio URL with Transcription

```python
response = requests.post(
    "http://localhost:8000/multimodal/voice",
    json={
        "audio_url": "https://example.com/audio/meeting_recording.mp3",
        "transcription": "This is the transcribed text from the audio",
        "context": {
            "meeting_id": "meeting_456",
            "participants": ["Alice", "Bob"]
        }
    }
)
```

### Audio URL Only (Auto-transcription)

```python
response = requests.post(
    "http://localhost:8000/multimodal/voice",
    json={
        "audio_url": "https://example.com/audio/voice_note.wav"
    }
)
```

## Image Prompts

### Image Analysis

```python
response = requests.post(
    "http://localhost:8000/multimodal/image",
    json={
        "image_url": "https://example.com/images/chart.png",
        "caption": "Quarterly sales chart showing revenue trends",
        "context": {
            "task": "analyze_trends",
            "quarter": "Q4_2024"
        }
    }
)
```

### Multiple Images Comparison

```python
# Use mixed endpoint for multiple images
response = requests.post(
    "http://localhost:8000/multimodal/mixed",
    json={
        "contents": [
            {
                "type": "image",
                "data": "https://example.com/before.jpg",
                "encoding": "url",
                "metadata": {"label": "before"}
            },
            {
                "type": "image",
                "data": "https://example.com/after.jpg",
                "encoding": "url",
                "metadata": {"label": "after"}
            },
            {
                "type": "text",
                "data": "Compare these two images and describe the differences"
            }
        ],
        "primary_type": "image",
        "instruction": "Provide a detailed comparison"
    }
)
```

## Video Prompts

### Video Analysis

```python
response = requests.post(
    "http://localhost:8000/multimodal/video",
    json={
        "video_url": "https://example.com/videos/presentation.mp4",
        "description": "Company Q4 presentation video",
        "context": {
            "duration": "15 minutes",
            "presenter": "CEO"
        }
    }
)
```

## Simulation Prompts

### Basic Simulation

```python
response = requests.post(
    "http://localhost:8000/multimodal/simulation",
    json={
        "scenario": "What would happen if we increase marketing spend by 50%?",
        "parameters": {
            "current_spend": 100000,
            "increase_percentage": 50,
            "duration": "6 months"
        },
        "expected_outcomes": [
            "increased_lead_generation",
            "improved_brand_awareness"
        ],
        "context": {
            "industry": "tech",
            "company_size": "mid-market"
        }
    }
)
```

### Complex Scenario Analysis

```python
response = requests.post(
    "http://localhost:8000/multimodal/simulation",
    json={
        "scenario": "Simulate the impact of launching a new product line",
        "parameters": {
            "product_category": "premium",
            "target_market": "enterprise",
            "investment": 500000,
            "timeline": "12 months",
            "team_size": 10
        },
        "expected_outcomes": [
            "revenue_projection",
            "market_share_change",
            "customer_acquisition_cost"
        ],
        "duration": "1 year"
    }
)
```

## Mixed Multimodal Prompts

### Text + Image + Audio

```python
response = requests.post(
    "http://localhost:8000/multimodal/mixed",
    json={
        "contents": [
            {
                "type": "text",
                "data": "Here's the presentation slides and audio commentary"
            },
            {
                "type": "image",
                "data": "https://example.com/slide1.jpg",
                "encoding": "url"
            },
            {
                "type": "audio",
                "data": "https://example.com/commentary.mp3",
                "encoding": "url"
            }
        ],
        "primary_type": "mixed",
        "instruction": "Summarize the key points from this presentation"
    }
)
```

### Document with Images

```python
response = requests.post(
    "http://localhost:8000/multimodal/mixed",
    json={
        "contents": [
            {
                "type": "text",
                "data": "# Annual Report 2024\n\nOur company had a great year..."
            },
            {
                "type": "image",
                "data": "https://example.com/chart1.png",
                "encoding": "url",
                "metadata": {"caption": "Revenue Growth"}
            },
            {
                "type": "image",
                "data": "https://example.com/chart2.png",
                "encoding": "url",
                "metadata": {"caption": "Customer Satisfaction"}
            }
        ],
        "primary_type": "text",
        "instruction": "Create an executive summary of this annual report"
    }
)
```

## Programmatic Usage

### Using the Python SDK

```python
from src.kortana.core.multimodal import (
    MultimodalPromptGenerator,
    ContentType,
    SimulationQuery
)

# Initialize generator
generator = MultimodalPromptGenerator()

# Create a text prompt
text_prompt = generator.create_text_prompt(
    "What are the benefits of AI?",
    context={"topic": "artificial_intelligence"}
)

# Create an image prompt
image_prompt = generator.create_image_prompt(
    image_data="https://example.com/chart.png",
    encoding="url",
    caption="Sales data visualization"
)

# Create a simulation prompt
sim_query = SimulationQuery(
    scenario="Market expansion simulation",
    parameters={"budget": 100000, "timeframe": "6 months"}
)
sim_prompt = generator.create_simulation_prompt(sim_query)

# Create a mixed prompt
mixed_prompt = generator.create_mixed_prompt(
    contents=[
        {"type": "text", "data": "Analyze this data"},
        {"type": "image", "data": "https://example.com/data.png", "encoding": "url"}
    ],
    primary_type=ContentType.TEXT
)
```

### Processing Prompts Programmatically

```python
from src.kortana.services.multimodal_service import MultimodalService
from sqlalchemy.orm import Session

# Assume you have a database session
db: Session = get_db_session()

# Create service
service = MultimodalService(db)

# Process a prompt
response = await service.process_prompt(text_prompt)

print(f"Success: {response.success}")
print(f"Content: {response.content}")
print(f"Processing Info: {response.processing_info}")
```

## File Upload Example

### Uploading Media Files

```python
import requests

# Upload an image
with open("local_image.jpg", "rb") as f:
    files = {"file": f}
    data = {
        "content_type": "image",
        "caption": "My local image"
    }
    response = requests.post(
        "http://localhost:8000/multimodal/upload",
        files=files,
        data=data
    )
    
upload_info = response.json()
print(f"File uploaded: {upload_info['filename']}")
```

## Error Handling

### Handling API Errors

```python
try:
    response = requests.post(
        "http://localhost:8000/multimodal/text",
        json={"text": "Hello"},
        timeout=30
    )
    response.raise_for_status()
    result = response.json()
    
    if not result.get("success"):
        print(f"Error: {result.get('error_message')}")
    else:
        print(f"Response: {result['content']}")
        
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
```

## Best Practices

1. **Always provide context** when available - it improves response quality
2. **Use URLs for large media files** instead of base64 to reduce payload size
3. **Include captions/descriptions** for media to provide additional context
4. **Handle errors gracefully** and check the `success` field in responses
5. **Use appropriate content types** - don't force everything through text
6. **Enable memory integration** for conversational continuity
7. **Validate inputs** before sending to avoid unnecessary API calls

## Advanced Examples

### Chaining Multiple Requests

```python
# First, analyze an image
image_response = requests.post(
    "http://localhost:8000/multimodal/image",
    json={"image_url": "https://example.com/chart.png"}
).json()

# Then, use the analysis in a follow-up query
followup_response = requests.post(
    "http://localhost:8000/multimodal/text",
    json={
        "text": f"Based on this analysis: {image_response['content']}, what actions should we take?",
        "context": {"previous_analysis": True}
    }
).json()
```

### Batch Processing

```python
images = [
    "https://example.com/img1.jpg",
    "https://example.com/img2.jpg",
    "https://example.com/img3.jpg"
]

results = []
for img_url in images:
    response = requests.post(
        "http://localhost:8000/multimodal/image",
        json={"image_url": img_url}
    )
    results.append(response.json())

# Aggregate results
for i, result in enumerate(results, 1):
    print(f"Image {i}: {result['content']}")
```
