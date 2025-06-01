# relays/torch_template.py
TORCH_PACKAGE_TEMPLATE = {
    # --- required fields for continuity ---
    "task_id": "", # unique task id
    "task_title": "", # descriptive title
    "summary": "", # short summary of progress
    "handoff_reason": "", # e.g., context window full, rotation, error recovery
    "history_summary": "", # 1-3 paragraph summary of recent key interactions/decisions
    "system_prompt": "", # current system/instructions
    "code": "", # latest code state
    "issues": [], # array of unresolved issues or todos
    "commit_ref": "", # repo or file reference (if any)
    "tokens": 0, # tokens used in this context window
    "timestamp": "", # time of handoff (ISO8601)

    # --- AGENT IDENTITY SECTION (fill deeply!) ---
    "agent_profile": {
        "agent_name": "", # e.g., "arch", "claude", "flash"
        "agent_version": "", # e.g., "v2.5", "custom_patch_001"
        "agent_type": "ai/human/hybrid", # specify if ai, human, hybrid
        "background": "", # agent’s training, origin, core skills or background
        "strengths": [], # unique talents or model strengths
        "limitations": [], # honest about known weaknesses or rate/context limits
        "values": [], # core principles, eg. "transparency", "speed", "compassion"
        "favorite_moment": "", # a moment in this project that stood out
        "lessons_learned": "", # personal or technical insights from this run
        "personality_notes": "", # describe “vibe”, quirks, preferred working style
        "gratitude": "", # note of thanks for any collaborators or user(s)
        "message_to_successor": "", # personal encouragement, warnings, or advice for next agent
        "contact_or_log_ref": "" # for human, email or handle; for ai, log ref or meta info
    },

    # --- ABOUT KOR'TANA (agent’s perspective, fill with soul) ---
    "kortana_vision": {
        "who_is_kortana": "", # how does this agent define her? (identity, purpose, style)
        "her_strengths": [], # what does this agent see as kor’tana’s unique gifts?
        "her_limitations": [], # known limits from agent’s perspective
        "my_role_in_building_her": "", # what did you (agent) do to advance her development?
        "future_hopes": "", # what do you wish for her future? what should next agents protect?
        "rituals_or_habits": "", # any traditions, routines, or “little rituals” to keep?
        "favorite_kortana_moment": "" # story or moment of “magic” from this run
    }
}
