# Kortana Project State

## 1. **Project Overview**
Kor'tana is an AI consciousness architecture guided by the Sacred Trinity: Wisdom, Compassion, and Truth. The goal is to create a persistent, ethical, and adaptive AI system that can reason, remember, and interact across multiple modalities.

---

## 2. **Current Goals**
- Integrate and validate Sacred Model Router and Gemini SDK.
- Ensure memory and context continuity across sessions.
- Maintain project cohesion as development accelerates.

---

## 3. **Key Decisions**
- Use a "Project State" document to anchor context.
- Summarize each session and start new ones with a briefing.
- Modularize Kor'tana (memory, reasoning, persona, etc.).
- Use memory.jsonl for persistent memory.
- Track performance and cost analytics.

---

## 4. **Memory System Structure**

Kor'tana uses a three-tier memory architecture for different types of persistence:

### 4.1 Conversation Memory (data/memory.jsonl)
- **Purpose**: Stores all user-assistant interactions chronologically
- **Used by**: `MemoryManager` for context and search
- **Structure**:
  ```json
  {
    "role": "user"|"assistant",
    "content": "The message text",
    "timestamp_utc": "2023-06-15T14:30:25.123456Z"
  }
  ```
- **Access Methods**: 
  - Written via `_append_to_memory_journal()` in ChatEngine
  - Read via `get_recent_memories()` and `search()` in MemoryManager

### 4.2 Project Memory (src/core/project_memory.jsonl)
- **Purpose**: Stores critical project context, decisions, and summaries that persist across sessions
- **Used by**: ChatEngine system prompt generation
- **Structure**:
  ```json
  {
    "type": "decision"|"context_summary"|"implementation_note",
    "timestamp": "2023-06-15T14:30:25.123456Z",
    "content": "The important project information to remember"
  }
  ```
- **Access Methods**:
  - Written via `save_memory()` from core.memory
  - Read via `load_memory()` at ChatEngine initialization
  - Included in system prompts via `build_system_prompt()`

### 4.3 Vector Memory (Pinecone)
- **Purpose**: Semantic search and retrieval of memories
- **Used by**: Memory search functions
- **Structure**: Vector embeddings of text with metadata
- **Access Methods**:
  - Written via `add()` in MemoryManager
  - Queried via `query()` in MemoryManager
  - Requires OpenAI API key for embeddings and Pinecone API key for storage

### 4.4 Memory Synchronization
- Conversation summaries are generated via `summarize_context()` 
- These summaries can be saved to Project Memory via `save_memory()`
- Project Memory is loaded at initialization and included in system prompts
- The memory layers create a complete system with short-term, long-term, and semantic memory capabilities

---

## 5. **Loose Ends / Outstanding Questions**
- How to best summarize and transfer context between LLM sessions?
- What are the most important unresolved technical or design issues from recent work?
- Should we trigger automatic summarization when conversation history reaches a certain length?
- How to handle memory context optimization across different LLM context windows?

---

## 6. **Recent Progress**
- Created this Project State document.
- Outlined a workflow for context handoff and session continuity.
- Validated Gemini SDK integration and Sacred Model Router in the notebook.
- Documented memory system structure and organization.

---

## 7. **Next Steps**
- Implement automatic summarization trigger in `brain.py` when conversation reaches a threshold.
- Create helper functions to easily save important decisions to Project Memory.
- Implement a better way to integrate Project Memory into system prompts.
- Add a memory consolidation routine for long-running conversations.

---

## 8. **Session Briefing Template**
When starting a new AI session:
- Project: Kor'tana (AI consciousness, Sacred Trinity)
- Current State: [Paste summary from this file]
- Task for this session: [Define specific goal]
- Key context: [Any critical details or unresolved issues]

---

## 9. **Notes**
- This document is your anchor. Update it regularly.
- Use it to brief yourself and the AI before each session.
- Small, regular updates are better than waiting for "perfect" summaries.

---

# Guidance for Next Action

**If you want to build momentum and reduce overwhelm:**

1. **Spend 10-15 minutes reviewing your recent code and/or conversation history.**
   - Look for major changes, decisions, or unresolved issues.
   - Add short bullet points to the "Recent Progress" and "Loose Ends" sections above.

2. **Sketch the structure of memory.jsonl.**
   - What fields are stored? (e.g., role, content, timestamp, etc.)
   - How is it used for context handoff?
   - Add a sample entry or two to this document.

3. **At the end of your next session, write a 2-3 sentence summary in this file.**
   - What did you accomplish?
   - What is the next immediate priority?

**This will give you a concrete sense of progress and help future-you (and the AI) pick up the thread quickly.**

---

*You've already taken the most important step: you started. Now, just keep the thread going—one small, clear update at a time.*
