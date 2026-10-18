# backend/services/session_memory.py
"""
Sliding-Window In-Memory Conversation Session Manager.
"""

import time
from typing import List, Dict, Optional, Any
from backend.config import settings

class SessionMemoryManager:
    """
    Manages active dialogue histories keyed by session_id.
    NOTE: For distributed production, swap this in-memory dict with Redis or PostgreS.
    """
    _instance: Optional["SessionMemoryManager"] = None

    def __init__(self, max_turns: int = settings.MEMORY_WINDOW_TURNS):
        self.max_turns = max_turns
        self._sessions: Dict[str, List[Dict[str, Any]]] = {}

    @classmethod
    def get_instance(cls) -> "SessionMemoryManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def add_turn(self, session_id: Optional[str], role: str, content: str):
        if not session_id:
            session_id = "default_session"
        if session_id not in self._sessions:
            self._sessions[session_id] = []

        self._sessions[session_id].append({
            "role": role,
            "content": content,
            "timestamp": time.time()
        })

        max_msgs = self.max_turns * 2
        if len(self._sessions[session_id]) > max_msgs:
            self._sessions[session_id] = self._sessions[session_id][-max_msgs:]

    def get_history(self, session_id: Optional[str]) -> List[Dict[str, Any]]:
        if not session_id or session_id not in self._sessions:
            return []
        return self._sessions[session_id]

    def get_formatted_history_text(self, session_id: Optional[str], incoming_history: Optional[List[Any]] = None) -> str:
        combined_turns: List[Dict[str, str]] = []
        if session_id and session_id in self._sessions:
            for item in self._sessions[session_id]:
                combined_turns.append({
                    "role": item.get("role", "user"),
                    "content": item.get("content", "")
                })

        if not combined_turns and incoming_history:
            for h in incoming_history:
                role = getattr(h, 'role', None) or (h.get('role') if isinstance(h, dict) else 'user')
                content = getattr(h, 'content', None) or (h.get('content') if isinstance(h, dict) else str(h))
                combined_turns.append({"role": role, "content": content})

        recent = combined_turns[-(self.max_turns * 2):] if combined_turns else []
        if not recent:
            return ""
        lines = []
        for t in recent:
            speaker = "Student (ศ฿ตญฝาวรเที)" if t["role"] == "user" else "AI Counselor (সஹসப্ব্বি)"
            lines.append(f"{speaker}: {t['content']}")
        return "\n".join(lines)

    def clear_session(self, session_id: str):
        if session_id in self._sessions:
            del self._sessions[session_id]


def get_session_memory() -> SessionMemoryManager:
    return SessionMemoryManager.get_instance()
