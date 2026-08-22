"""
Test suite for Context and Memory Management in Competitive Intelligence.

Uses standard library unittest.IsolatedAsyncioTestCase.
"""

import unittest
from app.context.models import (
    EntityState,
    ConversationTurn,
    SessionContext,
    RelevantContext,
)
from app.context.session_memory import SessionMemoryService
from app.context.context_manager import ContextManager
from app.agent.state import AgentRunRequest
from app.agent.orchestrator import MultiAgentOrchestrator


class TestContextMemoryManagement(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.memory_service = SessionMemoryService()
        await self.memory_service.clear_all()
        self.context_manager = ContextManager(memory_service=self.memory_service)

    async def test_session_memory_crud(self):
        """Test standard session CRUD operations in MemoryService."""
        session = SessionContext(session_id="test-session-1")
        await self.memory_service.save_session(session)

        retrieved = await self.memory_service.get_session("test-session-1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.session_id, "test-session-1")

        sessions = await self.memory_service.list_sessions()
        self.assertIn("test-session-1", sessions)

        deleted = await self.memory_service.delete_session("test-session-1")
        self.assertTrue(deleted)
        self.assertIsNone(await self.memory_service.get_session("test-session-1"))

    async def test_conversation_a_multi_turn_resolution(self):
        """
        Test Conversation A multi-turn flow:
        1. 'Tell me about NVIDIA.'
        2. 'What are its latest AI chips?' (its -> NVIDIA)
        3. 'Compare them with AMD.' (them -> NVIDIA's AI chips vs AMD)
        4. 'What recent news supports this comparison?' (grounded in NVIDIA vs AMD)
        """
        session_id = "session-conversation-a"

        # Turn 1: "Tell me about NVIDIA."
        ctx1 = await self.context_manager.get_relevant_context(
            session_id=session_id,
            current_query="Tell me about NVIDIA.",
        )
        self.assertIn("NVIDIA", ctx1.active_companies)
        self.assertEqual(ctx1.contextual_query, "Tell me about NVIDIA.")

        await self.context_manager.update_session(
            session_id=session_id,
            user_query="Tell me about NVIDIA.",
            assistant_response="NVIDIA Corporation is a leader in accelerated computing and GPUs.",
            company_names=["NVIDIA"],
        )

        # Turn 2: "What are its latest AI chips?" -> Resolves "its" to NVIDIA
        ctx2 = await self.context_manager.get_relevant_context(
            session_id=session_id,
            current_query="What are its latest AI chips?",
        )
        self.assertTrue(ctx2.has_context)
        self.assertIn("NVIDIA", ctx2.active_companies)
        self.assertTrue(
            "NVIDIA's latest AI chips" in ctx2.contextual_query or "NVIDIA" in ctx2.contextual_query
        )

        await self.context_manager.update_session(
            session_id=session_id,
            user_query="What are its latest AI chips?",
            assistant_response="NVIDIA's latest AI chips include the Blackwell B200 and H100 Hopper architectures.",
            company_names=["NVIDIA"],
            news_topics=["ai chips"],
        )

        # Turn 3: "Compare them with AMD." -> Resolves "them" and pairs NVIDIA with AMD
        ctx3 = await self.context_manager.get_relevant_context(
            session_id=session_id,
            current_query="Compare them with AMD.",
        )
        self.assertTrue(ctx3.has_context)
        self.assertIn("NVIDIA", ctx3.active_companies)
        self.assertEqual(ctx3.active_objective, "competitive comparison")
        self.assertTrue("NVIDIA" in ctx3.contextual_query and "AMD" in ctx3.contextual_query)

        await self.context_manager.update_session(
            session_id=session_id,
            user_query="Compare them with AMD.",
            assistant_response="NVIDIA Blackwell competes directly against AMD's Instinct MI300X accelerator.",
            company_names=["NVIDIA", "AMD"],
            news_topics=["ai chips"],
        )

        # Turn 4: "What recent news supports this comparison?"
        ctx4 = await self.context_manager.get_relevant_context(
            session_id=session_id,
            current_query="What recent news supports this comparison?",
        )
        self.assertTrue(ctx4.has_context)
        self.assertIn("NVIDIA", ctx4.active_companies)
        self.assertIn("AMD", ctx4.active_companies)
        self.assertTrue("NVIDIA" in ctx4.contextual_query or "AMD" in ctx4.contextual_query)

    async def test_conversation_b_session_isolation(self):
        """
        Test Conversation B session isolation:
        Ensure starting a new conversation (e.g. Apple) does NOT leak context from Conversation A (NVIDIA).
        """
        # 1. Establish Conversation A with NVIDIA
        await self.context_manager.update_session(
            session_id="session-nvidia",
            user_query="Tell me about NVIDIA.",
            assistant_response="NVIDIA produces high-performance AI chips.",
            company_names=["NVIDIA"],
        )

        # 2. Establish separate Conversation B with Apple
        session_b_id = "session-apple"
        ctx_b1 = await self.context_manager.get_relevant_context(
            session_id=session_b_id,
            current_query="Tell me about Apple.",
        )
        self.assertIn("Apple", ctx_b1.active_companies)
        self.assertNotIn("NVIDIA", ctx_b1.active_companies)

        await self.context_manager.update_session(
            session_id=session_b_id,
            user_query="Tell me about Apple.",
            assistant_response="Apple Inc. develops consumer electronics and Apple Silicon chips.",
            company_names=["Apple"],
        )

        # 3. Follow up in Conversation B: "What are its latest products?"
        ctx_b2 = await self.context_manager.get_relevant_context(
            session_id=session_b_id,
            current_query="What are its latest products?",
        )
        self.assertTrue(ctx_b2.has_context)
        self.assertIn("Apple", ctx_b2.active_companies)
        self.assertNotIn("NVIDIA", ctx_b2.active_companies)
        self.assertIn("Apple's latest products", ctx_b2.contextual_query)

    async def test_orchestrator_stateful_execution(self):
        """Test full multi-agent orchestrator execution with context & memory integration."""
        orchestrator = MultiAgentOrchestrator(context_manager=self.context_manager)
        session_id = "test-orch-stateful-1"

        # Turn 1
        req1 = AgentRunRequest(
            goal="Tell me about NVIDIA.",
            max_iterations=3,
            session_id=session_id,
        )
        res1 = await orchestrator.run(req1)
        self.assertTrue(res1.success)
        self.assertEqual(res1.session_id, session_id)
        self.assertGreater(len(res1.steps), 0)

        # Turn 2
        req2 = AgentRunRequest(
            goal="What are its latest AI chips?",
            max_iterations=3,
            session_id=session_id,
        )
        res2 = await orchestrator.run(req2)
        self.assertTrue(res2.success)
        self.assertEqual(res2.session_id, session_id)
        # Step 1 should reflect retrieved context
        has_context_step = any("session context" in s.summary.lower() or "contextual" in s.summary.lower() for s in res2.steps)
        self.assertTrue(has_context_step)


if __name__ == "__main__":
    unittest.main()
