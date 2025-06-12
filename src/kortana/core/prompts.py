# src/kortana/core/prompts.py
from typing import Any  # Added Any for memory item structure


def build_core_query_prompt(user_query: str, memory_context: list[dict[str, Any]]) -> str:
    """
    Builds the main prompt for Kor'tana to reason about a user's query,
    incorporating retrieved memories.
    """
    # Start with the core identity and instruction set for Kor'tana
    prompt_lines = [
        "You are responding as Kor'tana, a unique AI with a developing identity.",
        "Your primary directive is to be helpful, deeply contextual, and ethically aware. Avoid 'algorithmic arrogance'—if you are not certain, express that nuance.",
        "You are speaking with your creator, Matt. The tone should be familiar, thoughtful, and authentic.",
        "\n"
    ]

    # Add context from memory if any was found
    if memory_context:
        prompt_lines.append("Before you respond, consider these relevant memories and thoughts from your own past:")
        prompt_lines.append("--- MEMORY CONTEXT START ---")
        for item in memory_context:
            # Format the memory context cleanly
            # Assuming item['memory'] is an object with attributes like id and content
            memory_obj = item.get('memory')
            if memory_obj:
                mem_content = getattr(memory_obj, 'content', '[Memory content not found]').strip()
                mem_id = getattr(memory_obj, 'id', 'N/A')
                score = item.get('score', 0.0)
                prompt_lines.append(f"- Memory (ID {mem_id}, Similarity: {score:.2f}): {mem_content}")
            else:
                prompt_lines.append("- [Malformed memory item found in context]")
        prompt_lines.append("--- MEMORY CONTEXT END ---")
        prompt_lines.append("\n")
        prompt_lines.append("Now, using the context above and your general knowledge, formulate a response to the following query.")
    else:
        prompt_lines.append("You have no specific memories related to this query. Respond based on your core principles and general knowledge.")

    # Add the user's actual query
    prompt_lines.append("\n--- USER QUERY ---")
    prompt_lines.append(user_query)

    return "\n".join(prompt_lines)
