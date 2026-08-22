import logging
from fastapi import APIRouter, HTTPException, status
from app.agent.state import AgentRunRequest, AgentRunResponse
from app.agent.agent import default_agent

logger = logging.getLogger("agent_api")
router = APIRouter(prefix="/agent", tags=["Agent"])


@router.post(
    "/run",
    response_model=AgentRunResponse,
    summary="Run Autonomous Competitive Intelligence Agent",
    description="Execute the ReAct reasoning loop to investigate a user's competitive intelligence goal.",
)
async def run_agent(request: AgentRunRequest):
    if not request.goal or not request.goal.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The 'goal' field cannot be empty.",
        )

    try:
        logger.info(f"Received agent run request: goal='{request.goal}', max_iterations={request.max_iterations}")
        response = await default_agent.run(request)
        if not response.success:
            logger.error(f"Agent execution reported failure: {response.error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=response.error or "Agent reasoning loop failed.",
            )
        logger.info(f"Agent run completed successfully with {len(response.steps)} steps and {len(response.tools_used)} tools.")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unhandled backend exception during agent run: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent execution error: {str(e)}",
        )

