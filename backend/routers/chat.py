

from fastapi import APIRouter, HTTPException

from backend.schemas import ChatResponse, ChatRequest
from backend.agent.agent import run_agent


router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(payload: ChatRequest):
    """
    User ask questions and agent dynamically triggers tools, reads live database records,
    and generates answers based on the data.
    """

    try:
        result = await run_agent(user_question=payload.question)

        return ChatResponse(
            question=result["question"],
            answer=result["answer"],
            chart_path=result.get("chart_path")
        )
    except Exception as e:
        error_msg = str(e)

        # handle llm error
        if "503" in error_msg or "UNAVAILABLE" in error_msg or "high demand" in error_msg.lower():
            llm_err = (
                "**Service Notice:** AI model is currently experiencing high demand on servers. "
                "This is usually temporary — please wait for few minutes and try submitting your question again."
            )

        # handle rate limits
        elif "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
            llm_err = (
                "**Rate Limit:** The AI API quota limit was temporarily reached. "
                "Please pause for a few seconds before asking another question."
            )

        # any other unexpected failure
        else:
            llm_err = (
                f"**Analysis Interrupted:** An unexpected issue occurred while analyzing the data. "
                f"Details: {error_msg}. Please try rephrasing your question."
            )
        
        return ChatResponse(
            question=payload.question,
            answer=llm_err
        )


    