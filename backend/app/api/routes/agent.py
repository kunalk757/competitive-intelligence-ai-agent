from fastapi import APIRouter, HTTPException, status
from app.agent.state import AgentRunRequest, AgentRunResponse
from app.agent.agent import default_agent

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
        response = await default_agent.run(request)
        if not response.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=response.error or "Agent reasoning loop failed.",
            )
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent execution error: {str(e)}",
        )
