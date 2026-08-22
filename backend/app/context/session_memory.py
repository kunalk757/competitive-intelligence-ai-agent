"""
Memory service abstraction and in-memory session store implementation.

Designed for clean decoupling so that Supabase / external storage can be
plugged in seamlessly in the future by implementing MemoryService.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import asyncio
import logging
from app.context.models import SessionContext

logger = logging.getLogger("session_memory")


class MemoryService(ABC):
    """
    Abstract interface for managing conversation session memory.
    
    Future implementations (such as SupabaseMemoryService or RedisMemoryService)
    can implement this interface without modifying agent or orchestrator logic.
    """

    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[SessionContext]:
        """Retrieve a session by its unique ID."""
        pass

    @abstractmethod
    async def save_session(self, session: SessionContext) -> None:
        """Persist or update a session."""
        pass

    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session from memory."""
        pass

    @abstractmethod
    async def list_sessions(self) -> List[str]:
        """List all active session IDs."""
        pass


class SessionMemoryService(MemoryService):
    """
    Thread-safe, in-memory implementation of MemoryService.
    Stores session context objects in local memory with turn retention limits.
    """

    def __init__(self, max_turns_per_session: int = 25):
        self._sessions: Dict[str, SessionContext] = {}
        self._lock = asyncio.Lock()
        self.max_turns_per_session = max_turns_per_session

    async def get_session(self, session_id: str) -> Optional[SessionContext]:
        async with self._lock:
            return self._sessions.get(session_id)

    async def save_session(self, session: SessionContext) -> None:
        async with self._lock:
            # Enforce max turns limit if session grows very large
            if len(session.turns) > self.max_turns_per_session:
                session.turns = session.turns[-self.max_turns_per_session:]
            self._sessions[session.session_id] = session
            logger.debug(f"Saved session '{session.session_id}' with {len(session.turns)} turn(s).")

    async def delete_session(self, session_id: str) -> bool:
        async with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.info(f"Deleted session '{session_id}'.")
                return True
            return False

    async def list_sessions(self) -> List[str]:
        async with self._lock:
            return list(self._sessions.keys())

    async def clear_all(self) -> None:
        """Utility for testing / resets."""
        async with self._lock:
            self._sessions.clear()


# Default singleton instance
default_memory_service = SessionMemoryService()
