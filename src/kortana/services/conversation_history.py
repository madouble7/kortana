"""
Conversation History Module

Provides conversation management for maintaining chat history and context.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


class ConversationHistory:
    """Manages conversation history and persistence."""
    
    def __init__(self, storage_path: str | Path = "data/conversations"):
        """Initialize conversation history manager.
        
        Args:
            storage_path: Directory to store conversation files
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.conversations: dict[str, dict] = {}
    
    def create_conversation(self, user_id: str = "default") -> str:
        """Create a new conversation.
        
        Args:
            user_id: User identifier
            
        Returns:
            Conversation ID
        """
        conv_id = str(uuid.uuid4())
        self.conversations[conv_id] = {
            "id": conv_id,
            "user_id": user_id,
            "messages": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "metadata": {}
        }
        self._save_conversation(conv_id)
        return conv_id
    
    def add_message(self, conversation_id: str, role: str, content: str, 
                   metadata: dict[str, Any] | None = None) -> None:
        """Add a message to a conversation.
        
        Args:
            conversation_id: Conversation ID
            role: Message role (user/assistant)
            content: Message content
            metadata: Optional metadata about the message
        """
        if conversation_id not in self.conversations:
            self._load_conversation(conversation_id)
        
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.conversations[conversation_id]["messages"].append(message)
        self.conversations[conversation_id]["updated_at"] = datetime.now().isoformat()
        self._save_conversation(conversation_id)
    
    def get_conversation(self, conversation_id: str) -> dict | None:
        """Get a conversation by ID.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Conversation data or None if not found
        """
        if conversation_id not in self.conversations:
            self._load_conversation(conversation_id)
        
        return self.conversations.get(conversation_id)
    
    def get_messages(self, conversation_id: str, limit: int | None = None) -> list[dict]:
        """Get messages from a conversation.
        
        Args:
            conversation_id: Conversation ID
            limit: Optional limit on number of messages (most recent)
            
        Returns:
            List of messages
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return []
        
        messages = conversation["messages"]
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    def list_conversations(self, user_id: str | None = None) -> list[dict]:
        """List all conversations, optionally filtered by user.
        
        Args:
            user_id: Optional user ID filter
            
        Returns:
            List of conversation summaries
        """
        # Load all conversation files
        for conv_file in self.storage_path.glob("*.json"):
            conv_id = conv_file.stem
            if conv_id not in self.conversations:
                self._load_conversation(conv_id)
        
        conversations = list(self.conversations.values())
        
        if user_id:
            conversations = [c for c in conversations if c.get("user_id") == user_id]
        
        # Sort by updated_at descending
        conversations.sort(key=lambda c: c.get("updated_at", ""), reverse=True)
        
        # Return summaries (without full message history)
        return [{
            "id": c["id"],
            "user_id": c.get("user_id"),
            "message_count": len(c.get("messages", [])),
            "created_at": c.get("created_at"),
            "updated_at": c.get("updated_at"),
            "preview": self._get_conversation_preview(c)
        } for c in conversations]
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            True if deleted, False if not found
        """
        conv_path = self.storage_path / f"{conversation_id}.json"
        if conv_path.exists():
            conv_path.unlink()
        
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        
        return False
    
    def _save_conversation(self, conversation_id: str) -> None:
        """Save conversation to disk.
        
        Args:
            conversation_id: Conversation ID
        """
        if conversation_id not in self.conversations:
            return
        
        conv_path = self.storage_path / f"{conversation_id}.json"
        with open(conv_path, 'w', encoding='utf-8') as f:
            json.dump(self.conversations[conversation_id], f, indent=2, ensure_ascii=False)
    
    def _load_conversation(self, conversation_id: str) -> None:
        """Load conversation from disk.
        
        Args:
            conversation_id: Conversation ID
        """
        conv_path = self.storage_path / f"{conversation_id}.json"
        if not conv_path.exists():
            return
        
        try:
            with open(conv_path, 'r', encoding='utf-8') as f:
                self.conversations[conversation_id] = json.load(f)
        except Exception as e:
            print(f"Error loading conversation {conversation_id}: {e}")
    
    def _get_conversation_preview(self, conversation: dict) -> str:
        """Get a preview of the conversation.
        
        Args:
            conversation: Conversation data
            
        Returns:
            Preview text
        """
        messages = conversation.get("messages", [])
        if not messages:
            return "No messages"
        
        # Get first user message as preview
        for msg in messages:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                return content[:100] + "..." if len(content) > 100 else content
        
        return "New conversation"


# Global instance
conversation_history = ConversationHistory()
