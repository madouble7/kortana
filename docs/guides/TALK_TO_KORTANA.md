# 🎯 **Talk to Kor'tana - Complete Guide**

You now have **3 ways** to communicate with Kor'tana. Pick one and start chatting!

---

## **🚀 QUICKSTART - Choose Your Method**

### **Option 1: Simple Text Chat (Recommended - No Setup Needed!)**

```bash
cd c:\KOR-TANA\kortana
python kor_tana_simple_chat.py
```

✅ **Best for:** Quick testing, learning, immediate interaction
⏱️ **Setup time:** None - runs instantly
🔧 **Requirements:** Just Python

**Example:**

```
💬 You: status
🤖 Kor'tana: Current Status:
  • Monitoring: 🟢 Active
  • Total Tasks: 13
  • Completed: 11
  • Failed: 3
  • Last Check: 2026-01-28T13:58:13

💬 You: start
🤖 Kor'tana: ✅ Autonomous monitoring activated. I'm now working on tasks.

💬 You: exit
🤖 Kor'tana: 👋 Goodbye! See you next time.
```

---

### **Option 2: Full-Featured Chat (When Server is Running)**

Requires the Kor'tana server running on port 8000.

**Start server in Terminal 1:**

```bash
cd c:\KOR-TANA\kortana\backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

**Start chat in Terminal 2:**

```bash
cd c:\KOR-TANA\kortana
python kor_tana_chat.py
```

✅ **Best for:** Real API interaction, automation testing
⏱️ **Setup time:** ~30 seconds (start server)
🔧 **Requirements:** Server running, requests library

---

### **Option 3: Voice Chat (Advanced - Audio Required)**

Requires microphone and speakers.

**Start server in Terminal 1:**

```bash
cd c:\KOR-TANA\kortana\backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

**Start voice chat in Terminal 2:**

```bash
cd c:\KOR-TANA\kortana
python kor_tana_voice_chat.py
```

✅ **Best for:** Hands-free operation, natural interaction
⏱️ **Setup time:** ~30 seconds + package install
🔧 **Requirements:** Server, microphone, speakers, speech_recognition, pyttsx3

**Example:**

```
🎤 Listening... (speak now)
👤 You: What's your status
🤖 Kor'tana: I'm actively monitoring and executing tasks. I have 13 tasks in my queue.

🎤 Listening... (speak now)
👤 You: Start monitoring
🤖 Kor'tana: Autonomous monitoring activated. I'm now actively working on tasks.
```

---

## **📋 All Available Commands**

### **Status & Information**

```
status       - Current system status
dashboard    - Full overview with all metrics
tasks        - List of recent tasks
metrics      - Performance statistics
health       - System health check
```

### **Control Commands**

```
start        - Activate autonomous monitoring
stop         - Pause monitoring
check        - Force immediate system check
```

### **Task Management**

```
approve [id] - Approve a pending task (provide task ID)
retry [id]   - Retry a failed task (provide task ID)
```

### **Utility Commands**

```
help         - Show all commands
save         - Save conversation to JSON file
clear        - Clear conversation history
exit / quit  - End chat session
```

---

## **🎬 Live Examples**

### **Example 1: Monitor System**

```
💬 You: status
🤖 Kor'tana: Current Status:
  • Monitoring: 🟢 Active
  • Total Tasks: 8
  • Completed: 6
  • Failed: 1
  • Last Check: 2026-01-28T14:00:00

💬 You: dashboard
🤖 Kor'tana: Dashboard Overview:
  • Status: 🟢 Active
  • Total Tasks: 8
  • Completed: 6
  • Failed: 1
  • Pending: 1
  • Human Interventions: 0
  • Uptime: 48 hours

💬 You: check
🤖 Kor'tana: ⚡ Running immediate check for new tasks...
```

### **Example 2: Control Monitoring**

```
💬 You: stop
🤖 Kor'tana: ⏹️  Monitoring paused. I'm standing by.

💬 You: status
🤖 Kor'tana: Current Status:
  • Monitoring: 🔴 Paused
  • ...

💬 You: start
🤖 Kor'tana: ✅ Autonomous monitoring activated. I'm now working on tasks.
```

### **Example 3: Task Management**

```
💬 You: tasks
🤖 Kor'tana: Recent Tasks (5):

  1. Process GitHub Issues
     Status: completed
     ID: task-001

  2. Fix failing tests
     Status: in_progress
     ID: task-002

  3. Create documentation
     Status: pending
     ID: task-003

  4. Review pull requests
     Status: completed
     ID: task-004

  5. Optimize database queries
     Status: failed
     ID: task-005

💬 You: approve task-003
🤖 Kor'tana: ✅ Task task-003 approved. Proceeding with execution.

💬 You: retry task-005
🤖 Kor'tana: 🔄 Task task-005 is being retried.
```

---

## **❓ FAQ & Troubleshooting**

### **"How do I save the conversation?"**

Type `save` in any chat interface. Conversations are automatically saved to:

- Text chat: `kor_tana_chat_log.json`
- Voice chat: `voice_chat_log.json`
- Simple chat: `kor_tana_chat_log.json`

### **"Voice chat doesn't work"**

1. Ensure microphone is connected and working
2. Check speaker/headphone volume
3. Verify internet connection (speech recognition requires it)
4. Try the text chat instead (always works)

### **"Server is not starting"**

1. Make sure you're in the `backend` directory
2. Check that port 8000 is not in use
3. Verify Python 3.11+ is installed
4. Run `pip install -r requirements.txt` first

### **"Can I use both chat and voice at the same time?"**

Yes! They both connect to the same Kor'tana instance. Open them in separate terminals.

### **"I just want to test without the server"**

Use `kor_tana_simple_chat.py` - it works locally without any server!

---

## **🔧 Advanced Usage**

### **Scripting with Chat**

You can pipe commands to the chat interfaces:

```bash
# Linux/Mac
echo -e "status\ndashboard\nexit" | python kor_tana_chat.py

# Windows - Create command file and use:
# (Or just run the simple chat which doesn't need piping)
```

### **Monitor Multiple Systems**

Run chat in multiple terminals to monitor simultaneously:

```bash
# Terminal 1
python kor_tana_simple_chat.py

# Terminal 2
python kor_tana_voice_chat.py  (if server running)

# Terminal 3
python kor_tana_chat.py        (if server running)
```

### **Batch Approve Tasks**

```
💬 You: tasks
🤖 Kor'tana: [Shows pending tasks]

💬 You: approve task-123
💬 You: approve task-124
💬 You: approve task-125
```

---

## **🎯 Recommended Workflow**

1. **Start here:** `python kor_tana_simple_chat.py`
2. **Explore commands:** Try `help`, `status`, `dashboard`
3. **When ready:** Start the server and try the full chat
4. **Advanced:** Set up voice chat for hands-free operation

---

## **📊 Comparison Table**

| Feature | Simple Chat | Full Chat | Voice Chat |
|---------|-------------|-----------|-----------|
| **Setup Required** | ❌ None | ⚠️ Server | ⚠️ Server + Audio |
| **Speed** | ⚡ Instant | ⚡ Fast | 🎤 ~2s/response |
| **Commands** | ✅ All | ✅ All | ✅ All |
| **Real API** | ❌ Mocked | ✅ Real | ✅ Real |
| **Conversation Log** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Audio Output** | ❌ No | ❌ No | ✅ Yes |
| **Audio Input** | ❌ No | ❌ No | ✅ Yes |
| **Remote Use** | ✅ SSH OK | ✅ SSH OK | ❌ Needs Audio |

---

## **🚀 Start Now!**

**Simplest option (try this first):**

```bash
cd c:\KOR-TANA\kortana
python kor_tana_simple_chat.py
```

Then type `status` and press Enter!

---

**You're ready to talk to Kor'tana. Choose your interface above and start chatting!** 🤖💬
