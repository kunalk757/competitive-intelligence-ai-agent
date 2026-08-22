from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from app.ai.gemini_service import gemini_service

router = APIRouter(prefix="/ai", tags=["AI"])


class AITestRequest(BaseModel):
    prompt: str = Field(
        ...,
        description="The prompt to test with the Gemini API.",
        examples=["Explain competitive intelligence in one sentence."],
    )

    @field_validator("prompt")
    def validate_prompt(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Prompt cannot be empty or contain only whitespace.")
        return v.strip()


class AITestResponse(BaseModel):
    success: bool
    response: str


@router.post(
    "/test",
    response_model=AITestResponse,
    summary="Test Gemini AI integration",
    description="Send a text prompt to Gemini API and receive an AI generated response.",
)
async def test_gemini_endpoint(request: AITestRequest):
    try:
        result = await gemini_service.generate_text(prompt=request.prompt)
        return AITestResponse(success=True, response=result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while communicating with Gemini API.",
        )
