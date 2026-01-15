"""FastAPI server for Research Radar workflow."""

import logging
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from mcp_server.workflow_adapter import run_workflow_for_paper

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
    analysis: Optional[dict] = Field(default=None, description="Detailed analysis with Q&A")
    status: str = Field(default="success", description="Status of the analysis")


@app.get("/")
async def root():
    """Serve the React UI."""
    frontend_path = Path(__file__).parent.parent.parent.parent / "frontend" / "dist" / "index.html"
    if frontend_path.exists():
        return FileResponse(frontend_path)
    return {"message": "Research Radar API", "version": "0.1.0", "endpoints": {"analyze": "/api/analyze", "health": "/api/health"}}


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
        result = run_workflow_for_paper(
            paper_id=request.paper_id.strip(),
            required_keywords=request.keywords if request.keywords else None,
        )

        return AnalysisResponse(
            paper_id=result.get("paper_id", request.paper_id),
            summary=result.get("summary", "No summary available"),
            analysis=result.get("analysis") or {},
            status="success",
        )

    except Exception as e:
        logger.error("Error analyzing content %s: %s", request.paper_id, e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze content: {str(e)}",
        ) from e


# Mount static files for React UI
frontend_dist = Path(__file__).parent.parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")
    logger.info("Frontend assets mounted from %s", frontend_dist)
else:
    logger.warning("Frontend dist directory not found at %s. UI will not be available.", frontend_dist)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "research_radar.api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
