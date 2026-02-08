# 🎤 Kor'tana Voice & Chat Interfaces

Two ways to talk to Kor'tana interactively:

## **Option 1: Text Chat (Recommended for Quick Start)**

```bash
cd c:\KOR-TANA\kortana
python kor_tana_chat.py
```

**Available Commands:**

- `status` - Show current status
- `dashboard` - Full system overview
- `tasks` - Show recent tasks
- `metrics` - Performance metrics
- `health` - System health check
- `start` - Start autonomous monitoring
- `stop` - Pause monitoring
- `check` - Force immediate check
- `approve [task-id]` - Approve a task
- `retry [task-id]` - Retry a failed task
- `help` - Show all commands
- `save` - Save conversation
- `exit` - Exit chat

**Example Session:**

```
💬 You: status
🤖 Kor'tana: Current Status:
  • Monitoring: 🟢 Active
  • Total Tasks: 12
  • Completed: 8
  • Failed: 1
  • Last Check: 2026-01-28 19:00:00

💬 You: start
🤖 Kor'tana: ✅ Autonomous monitoring activated. I'm now working on tasks.

💬 You: tasks
🤖 Kor'tana: Recent Tasks (5):
  1. Process GitHub Issues
     Status: completed
     ID: task-123
  ...
```

---

## **Option 2: Voice Chat (Real-Time Audio)**

```bash
cd c:\KOR-TANA\kortana
python kor_tana_voice_chat.py
```

**Features:**

- Real-time voice recognition (Google Speech Recognition)
- Text-to-speech responses
- Natural language commands
- Conversation logging
- Microphone-based input

**Voice Commands:**

- "What's your status?" → Current status
- "Show me the dashboard" → Full overview
- "What are you working on?" → Task list
- "Start monitoring" → Activate autonomous mode
- "Stop monitoring" → Pause monitoring
- "Force a check" → Immediate scan
- "What are my metrics?" → Performance data
- "Are you okay?" → System health
- "Help" → Available commands
- "Exit" or "Goodbye" → End session

**Example Voice Session:**

```
🎤 Listening... (speak now)
👤 You: What's your status
🤖 Kor'tana: I'm actively monitoring and executing tasks. I have 12 tasks in my queue.

🎤 Listening... (speak now)
👤 You: Start monitoring
🤖 Kor'tana: Autonomous monitoring activated. I'm now actively working on tasks.

🎤 Listening... (speak now)
👤 You: Show me my dashboard
🤖 Kor'tana: Here's my status: Total tasks: 12. Completed: 8. Failed: 1. Human interventions needed: 2.
```

---

## **Setup Requirements**

Both interfaces require the Kor'tana server to be running:

```bash
# In a separate terminal, ensure server is running:
cd backend
python -m uvicorn src.kortana.main:app --port 8000
```

### **For Voice Chat Only:**

Additional Python packages (auto-installed on first run):

- `speech_recognition` - Speech-to-text (uses Google's API)
- `pyttsx3` - Text-to-speech (offline, no API key needed)

### **System Requirements:**

- **Microphone** (for voice chat)
- **Speaker/Headphones** (for voice responses)
- **Internet connection** (for speech recognition)

---

## **Features Comparison**

| Feature | Text Chat | Voice Chat |
|---------|-----------|-----------|
| Speed | ⚡ Instant | 🎤 ~2-3 sec |
| Setup | ✅ No extra setup | ⚠️ Needs microphone |
| Commands | 📝 Type naturally | 🎤 Speak naturally |
| History | ✅ Saves to JSON | ✅ Saves to JSON |
| Remote Use | ✅ SSH/remote | ❌ Needs audio devices |
| Batch Commands | ✅ Easy scripting | ❌ Manual input |

---

## **Sample Workflows**

### **Workflow 1: Monitor Autonomous Development**

```
💬 You: start
🤖 Kor'tana: Autonomous monitoring activated.

💬 You: dashboard
🤖 Kor'tana: [Shows full overview]

💬 You: check
🤖 Kor'tana: Running immediate check...

💬 You: tasks
🤖 Kor'tana: [Shows recent tasks]

💬 You: save
🤖 Kor'tana: Conversation saved!
```

### **Workflow 2: Approve Pending Tasks**

```
💬 You: status
🤖 Kor'tana: [Shows status with 2 tasks pending human approval]

💬 You: tasks
🤖 Kor'tana: [Shows task list including pending ones]

💬 You: approve task-123
🤖 Kor'tana: Task task-123 approved. Proceeding!

💬 You: approve task-124
🤖 Kor'tana: Task task-124 approved. Proceeding!
```

### **Workflow 3: Monitor System Health**

```
💬 You: health
🤖 Kor'tana: System Health: OK
  ✅ Database
  ✅ Queue
  ✅ API

💬 You: metrics
🤖 Kor'tana: Performance Metrics:
  • Tasks per Hour: 15
  • Success Rate: 95%
  • Memory Usage: 256MB
```

---

## **Troubleshooting**

### **Text Chat Issues**

- **"Cannot connect to Kor'tana"** → Server not running on port 8000
- **No responses** → Check that server is responding to requests
- **Commands not recognized** → Type 'help' to see exact command format

### **Voice Chat Issues**

- **"Listening..." hangs** → Microphone not detected or not working
- **"I didn't catch that"** → Try speaking louder or closer to microphone
- **No audio response** → Check speaker/headphone volume, ensure pyttsx3 works
- **Speech recognition errors** → Check internet connection (uses Google API)
- **Audio input device not found** → Ensure microphone is connected and selected

---

## **Advanced Usage**

### **Run Multiple Instances**

```bash
# Terminal 1: Voice chat
python kor_tana_voice_chat.py

# Terminal 2: Text chat (in another window)
python kor_tana_chat.py

# Both can communicate with the same Kor'tana instance!
```

### **Script Integration**

Both interfaces log conversations to JSON files:

- `kor_tana_chat_log.json` - Text chat history
- `voice_chat_log.json` - Voice chat history

Use these logs for audit trails, debugging, or analysis.

---

## **Quick Start**

1. **Ensure Kor'tana server is running** (in one terminal)
2. **Choose your interface:**
   - Text: `python kor_tana_chat.py`
   - Voice: `python kor_tana_voice_chat.py`
3. **Issue commands** and watch Kor'tana respond
4. **Type 'help'** for full command list
5. **Type 'exit'** to end session

---

**Ready to chat? Start with text chat - it's faster!** 🚀
