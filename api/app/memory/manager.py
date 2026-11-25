"""Conversation Memory and Context Manager.

Tracks multi-turn chat sessions and provides contextual resolution for follow-up questions
(e.g., "now break that down by month" or "show this only for electronics").
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import time


@dataclass
class TurnContext:
    user_query: str
    generated_sql: str
    summary_insight: Optional[str] = None
    entities: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class ConversationMemoryManager:
    """Stores conversation turns per session and constructs contextual follow-up prompts."""

    def __init__(self):
        self._sessions: Dict[str, List[TurnContext]] = {}

    def add_turn(
        self,
        session_id: str,
        user_query: str,
        generated_sql: str,
        insight: Optional[str] = None
    ):
        """Records a completed conversation turn."""
        if session_id not in self._sessions:
            self._sessions[session_id] = []

        turn = TurnContext(
            user_query=user_query,
            generated_sql=generated_sql,
            summary_insight=insight
        )
        self._sessions[session_id].append(turn)

    def get_conversation_history_context(self, session_id: Optional[str]) -> str:
        """Returns previous query context if user is asking a follow-up question."""
        if not session_id or session_id not in self._sessions:
            return ""

        turns = self._sessions[session_id]
        if not turns:
            return ""

        last_turn = turns[-1]
        return f"""
PREVIOUS CONVERSATION CONTEXT (The user is asking a follow-up question to this):
Previous User Question: "{last_turn.user_query}"
Previous Executed SQL:
```sql
{last_turn.generated_sql}
```
INSTRUCTION FOR FOLLOW-UPS:
If the user says "break it down by month", "filter by Gujarat", or references previous data,
modify or extend the previous SQL rather than starting from scratch.
"""


# Global instance
memory_manager = ConversationMemoryManager()
