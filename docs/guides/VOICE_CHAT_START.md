# 🎤 VOICE CHAT - MICROPHONE SETUP GUIDE

## ⚡ **RUN THIS NOW**

```powershell
cd c:\KOR-TANA\kortana
python voice_chat_simple.py
```

**That's all you need to type!** The script does everything else.

---

## ✨ **What Happens**

1. Script starts and checks your microphone
2. You see: "🎤 Initializing voice chat..."
3. You see: "✅ Voice chat ready!"
4. Kor'tana says (audio): "Voice chat activated. I'm ready to listen."
5. You see: "🎤 Listening... (speak now)"
6. **You speak clearly into your microphone**
7. Kor'tana responds with audio
8. Repeat, or say "Exit"

---

## 🎯 **Speak These Commands**

```
"What's your status?"       → Current state
"Show dashboard"            → Full overview
"What are you working on?"  → Task list
"Show metrics"              → Performance
"Start monitoring"          → Begin work
"Stop monitoring"           → Pause work
"Check now"                 → Immediate scan
"Help"                      → Command list
"Exit"                      → Quit
```

---

## 🔧 **Setup Requirements** (One-Time)

Your system needs these packages installed (auto-installs first run):

```
✅ speech_recognition    (listens to your voice)
✅ pyttsx3              (speaks responses)
✅ Python 3.6+          (already have)
```

First run might take 30 seconds for setup. Subsequent runs are instant.

---

## 🎤 **Microphone Checklist**

- [ ] Microphone is plugged in or built-in
- [ ] Microphone shows in Windows Settings → Sound → Input
- [ ] Microphone is not muted
- [ ] Volume slider is not at 0%
- [ ] Internet connection is working (needed for speech recognition)

---

## 💻 **Start Command**

```powershell
cd c:\KOR-TANA\kortana
python voice_chat_simple.py
```

Copy-paste this and press Enter.

---

## ❓ **Having Issues?**

### **Script won't start**

```powershell
python -m pip install speech_recognition pyttsx3 -q
python voice_chat_simple.py
```

### **Microphone not detected**

- Check Windows Settings → Sound
- Select your microphone in "Input"
- Test the microphone there first

### **Can't hear Kor'tana**

- Check speaker/headphone volume
- Windows Settings → Sound → Volume up

### **Speech not recognized**

- Speak louder and clearer
- Reduce background noise
- Get closer to microphone
- Check internet connection

---

## 🎬 **First Run Example**

```
🎤 Initializing voice chat...
✅ Voice chat ready! Speak clearly into your microphone.

======================================================================
🎤 KOR'TANA VOICE CHAT
======================================================================

Speak your commands naturally:
  • 'What's your status?'
  • 'Show me the dashboard'
  • 'Start monitoring'
  • 'What are you working on?'
  • 'Exit' to quit

======================================================================

[Audio plays] 🤖: "Voice chat activated. I'm ready to listen. What would you like to know?"

🎤 Listening... (speak now)
👤 You: "What's your status?"
🔍 Recognizing...

[Audio plays] 🤖: "I'm currently monitoring and executing development tasks. Status looks good. I have several tasks in my queue."

🎤 Listening... (speak now)
👤 You: "Exit"
[Audio plays] 🤖: "Goodbye! See you next time."

✅ Conversation saved to voice_chat_log.json
```

---

## ✅ **You're Ready!**

```powershell
python voice_chat_simple.py
```

Run it. Speak. Enjoy voice chat with Kor'tana. 🎤🤖
