"""FastAPI server for Research Radar workflow."""

import logging
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

# --- IMPORTS FOR CHAT & WORKFLOW ---
from mcp_server.workflow_adapter import run_workflow_for_paper
from research_radar.workflow.nodes import rag_processor
from research_radar.llm.client import get_chat_llm_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Research Radar API",
    description="API for analyzing research papers and YouTube videos",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalysisRequest(BaseModel):
    """Request model for paper/video analysis."""

    paper_id: str = Field(
        ...,
        description="ArXiv paper ID (e.g., '2510.24081') or YouTube video URL/ID",
        min_length=1,
    )
    keywords: Optional[List[str]] = Field(
        default=None,
        description="Optional list of keywords to filter content. If empty, analyzes all content.",
    )


class AnalysisResponse(BaseModel):
    """Response model for paper/video analysis."""

    paper_id: str = Field(..., description="The analyzed paper/video ID")
    summary: str = Field(..., description="Summary of the content")
    analysis: Optional[dict] = Field(
        default=None, description="Detailed analysis with Q&A"
    )
    status: str = Field(default="success", description="Status of the analysis")
    hash_id: Optional[str] = Field(
        default=None, description="Hash ID of the paper for RAG queries"
    )


class ChatRequest(BaseModel):
    """Request model for chatting with a paper."""

    query: str = Field(..., description="Question to ask about the paper")
    hash_id: str = Field(
        ..., description="Hash ID of the paper (from analysis response)"
    )


class ChatResponse(BaseModel):
    """Response model for chat."""

    answer: str = Field(..., description="Answer to the question")
    sources: List[str] = Field(default_factory=list, description="Source chunks used")


@app.get("/")
async def root():
    """Serve the React UI."""
    frontend_path = (
        Path(__file__).parent.parent.parent.parent / "frontend" / "dist" / "index.html"
    )
    if frontend_path.exists():
        return FileResponse(frontend_path)
    return {
        "message": "Research Radar API",
        "version": "0.1.0",
        "endpoints": {"analyze": "/api/analyze", "health": "/api/health"},
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "research-radar"}


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_content(request: AnalysisRequest):
    """
    Analyze a research paper or YouTube video.

    Args:
        request: Analysis request with paper_id and optional keywords

    Returns:
        Analysis results including summary and detailed Q&A

    Raises:
        HTTPException: If analysis fails
    """
    try:
        logger.info(
            "Analyzing content: %s with keywords: %s",
            request.paper_id,
            request.keywords,
        )

        # Run the workflow
        # Pass empty list [] to skip relevance check, None for default keywords
        result = run_workflow_for_paper(
            paper_id=request.paper_id.strip(),
            required_keywords=(
                request.keywords if request.keywords is not None else None
            ),
        )

        return AnalysisResponse(
            paper_id=result.get("paper_id", request.paper_id),
            summary=result.get("summary", "No summary available"),
            analysis=result.get("analysis") or {},
            status="success",
            hash_id=result.get("paper_hash_id"),
        )

    except Exception as e:
        logger.error(
            "Error analyzing content %s: %s", request.paper_id, e, exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze content: {str(e)}",
        ) from e


@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_paper(request: ChatRequest):
    """
    Chat with a specific paper using RAG.

    Args:
        request: Chat request with query and hash_id

    Returns:
        Answer to the question based on paper content

    Raises:
        HTTPException: If chat fails
    """
    try:
        logger.info("Chat Query: '%s' for Hash: %s", request.query, request.hash_id)

        # 1. Retrieve relevant chunks from the SHARED rag_processor
        docs = rag_processor.search(
            query=request.query, article_hash=request.hash_id, k=4
        )

        if not docs:
            return ChatResponse(
                answer="I couldn't find any relevant information in this paper to answer your question.",
                sources=[],
            )

        # 2. Build Context String
        context_text = "\n\n".join([d.page_content for d in docs])

        # 3. Initialize LLM
        llm = get_chat_llm_client()

        # 4. Create Prompt
        prompt = ChatPromptTemplate.from_template(
            """You are a helpful research assistant. Answer the question based ONLY on the following context from a research paper.
If the answer is not in the context, say "I cannot find that information in the paper."

Context:
{context}

Question:
{question}

Answer:"""
        )

        # 5. Generate Answer
        chain = prompt | llm
        response = chain.invoke({"context": context_text, "question": request.query})

        # Handle different LLM return types (String vs AIMessage)
        answer_text = (
            response.content if hasattr(response, "content") else str(response)
        )

        return ChatResponse(
            answer=answer_text,
            sources=[d.metadata.get("source", "unknown") for d in docs],
        )

    except Exception as e:
        logger.error("Chat failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat request: {str(e)}",
        ) from e


# Mount static files for React UI
frontend_dist = Path(__file__).parent.parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount(
        "/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets"
    )
    logger.info("Frontend assets mounted from %s", frontend_dist)
else:
    logger.warning(
        "Frontend dist directory not found at %s. UI will not be available.",
        frontend_dist,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "research_radar.api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
