# Kor'tana Voice Output Setup

## What You Need

1. **PyNaCl** - Discord voice encryption
2. **FFmpeg** - Audio playback

---

## Installation Steps

### 1. Activate Virtual Environment

```cmd
discord_bot_env\Scripts\activate
```

### 2. Install PyNaCl

```cmd
pip install PyNaCl
```

### 3. Install FFmpeg

**Check if you have it:**
```cmd
ffmpeg -version
```

**If not installed:**
- Download from: https://ffmpeg.org/download.html
- Or use: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
- Extract and add `bin` folder to PATH

### 4. Restart Bot

```cmd
python kortana_discord_full.py
```

---

## How It Works

### Commands:

- **`/join`** - Kor'tana joins your voice channel
- **`/kortana [message]`** - She responds in text AND speaks in voice
- **`/speak [text]`** - She speaks specific text
- **`/leave`** - She leaves voice

### Flow:

1. You type `/kortana Hello!`
2. ChatEngine generates AI response
3. Response shows in text channel
4. TTS converts response to audio
5. Audio plays in voice channel

---

## Limitations

⚠️ **Discord bots cannot HEAR users speaking**
- This was removed from Discord API
- Bots can only SPEAK (output audio)
- Users type commands, bot speaks responses

✅ **What DOES work:**
- Bot speaks AI responses
- High-quality TTS
- Text chat with voice output

---

## Testing

1. Join a Discord voice channel
2. Type `/join` 
3. Bot joins channel
4. Type `/kortana what's your name?`
5. Bot responds in text AND speaks

---

## Troubleshooting

### "PyNaCl library needed"
→ Run `pip install PyNaCl` in venv

### "FFmpeg not found"
→ Install FFmpeg and add to PATH

### "Voice features unavailable"
→ Check that voice_orchestrator is loaded at startup

### No audio plays
→ Check Discord audio settings
→ Make sure bot has permission to speak in channel

---

Ready to test? Run the installation steps above!
