"""Gradio web UI for Research Radar paper analysis."""

import logging
import gradio as gr
from dotenv import load_dotenv
from mcp_server.workflow_adapter import run_workflow_for_paper

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def format_analysis(analysis: dict) -> str:
    """
    Format the analysis dictionary into a readable markdown string.

    Args:
        analysis: Dictionary with questions as keys and answers as values

    Returns:
        Formatted analysis text with clear visual separation
    """
    if not analysis:
        return "*No analysis available*"

    formatted_parts = []
    for i, (question, answer) in enumerate(analysis.items(), 1):
        formatted_parts.append(f"#### {i}. {question}\n\n{answer}")

    return "\n\n---\n\n".join(formatted_parts)


def format_summary(summary: str) -> str:
    """
    Format the summary for better readability by adding paragraph breaks.

    Args:
        summary: Raw summary text

    Returns:
        Formatted summary with better paragraph structure
    """
    if not summary:
        return "*No summary available*"

    # Split long text into paragraphs at sentence boundaries for readability
    # Add line breaks after sentences that end a thought
    sentences = summary.replace(". ", ".\n\n").replace("; ", ";\n\n")
    return sentences


def analyze_paper(paper_id: str, selected_keywords: list) -> tuple[str, str, str]:
    """
    Analyze a paper and return the results.

    Args:
        paper_id: Hugging Face paper ID (e.g., "2510.24081") / YT video ID
        selected_keywords: List of selected keywords for filtering

    Returns:
        Tuple of (status_message, analysis_text, summary_text)
    """
    if not paper_id or not paper_id.strip():
        return "Error", "Please enter a valid ID", ""

    try:
        logger.info(
            "Starting analysis for: %s with keywords: %s", paper_id, selected_keywords
        )

        # Call workflow adapter directly with selected keywords
        result = run_workflow_for_paper(
            paper_id.strip(), required_keywords=selected_keywords
        )

        paper_id_result = result.get("paper_id", paper_id)

        # Get both analysis and summary from the result
        analysis = result.get("analysis", {})
        summary = result.get("summary", "No summary available")

        # Format the analysis if available
        analysis_text = (
            format_analysis(analysis) if analysis else "No analysis available"
        )

        status_msg = f"Analysis completed successfully for: {paper_id_result}"

        # Format summary for readability
        formatted_summary = format_summary(summary)

        return status_msg, analysis_text, formatted_summary

    except Exception as e:
        logger.error("Error analyzing %s: %s", paper_id, e, exc_info=True)
        return "Error occurred", "", f"Failed to analyze: {e}"


def create_ui():
    """Create and configure the Gradio interface."""

    # Professional theme with modern blue color scheme
    theme = gr.themes.Glass(
        primary_hue="blue",
        secondary_hue="slate",
        font=[gr.themes.GoogleFont("Inter"), "sans-serif"],
    )

    # Available keywords for filtering (35 most relevant)
    available_keywords = [
        # Core Concepts
        "Large Language Models (LLMs)",
        "Transformers",
        "Attention Mechanisms",
        "Neural Networks",
        # Training Methods
        "Fine-tuning",
        "Reinforcement Learning",
        "Direct Preference Optimization (DPO)",
        "Supervised Learning",
        "Transfer Learning",
        # Reasoning & Prompting
        "Chain-of-Thought",
        "Reasoning",
        "Prompting",
        "In-Context Learning",
        "Few-Shot Learning",
        # Retrieval & Knowledge
        "RAG (Retrieval-Augmented Generation)",
        "Knowledge Retrieval",
        "Semantic Search",
        # Instructions & Evaluation
        "Instruction Following",
        "Benchmarks",
        "Evaluation",
        "Human Feedback",
        # Memory & Context
        "Long Context",
        "Memory",
        "Context Window",
        # Information Theory
        "Entropy",
        "KL-divergence",
        "Uncertainty",
        # Tasks & Applications
        "Code Generation",
        "Question Answering",
        "Summarization",
        "Translation",
        # Multimodal
        "Multimodal",
        "Vision-Language",
        # Safety & Alignment
        "Alignment",
        "Safety",
    ]

    custom_css = """
        .content-box {
            background: rgba(30, 41, 59, 0.5);
            border: 1px solid rgba(100, 116, 139, 0.3);
            border-radius: 12px;
            padding: 20px;
            margin: 8px 0;
            line-height: 1.7;
        }
        .content-box p { margin-bottom: 12px; }
        .section-title {
            color: #60a5fa;
            border-bottom: 2px solid #3b82f6;
            padding-bottom: 8px;
            margin-bottom: 16px;
        }
    """

    with gr.Blocks(
        title="Research Radar - Paper Analysis",
    ) as demo:
        # Header
        gr.Markdown("# Research Radar")
        gr.Markdown(
            "*Extract insights from papers and videos with AI-powered analysis*"
        )

        # Input Section
        with gr.Group():
            with gr.Row():
                paper_id_input = gr.Textbox(
                    label="Content URL or ID",
                    placeholder="ArXiv ID (2510.24081) or YouTube URL (https://youtube.com/watch?v=...)",
                    lines=1,
                    scale=4,
                )
                analyze_btn = gr.Button(
                    "Analyze",
                    variant="primary",
                    size="lg",
                    scale=1,
                )

            keywords_input = gr.Dropdown(
                choices=available_keywords,
                label="Filter by Keywords (optional - leave empty to analyze all content)",
                value=[],
                multiselect=True,
                interactive=True,
                allow_custom_value=True,
            )

        # Status
        status_output = gr.Textbox(
            label="Status",
            interactive=False,
            lines=1,
        )

        # Summary Section (first - most important)
        gr.Markdown("## Summary", elem_classes=["section-title"])
        summary_output = gr.Markdown(
            value="*Summary will appear here after analysis...*",
            elem_classes=["content-box"],
        )

        # Analysis Section (detailed Q&A below)
        gr.Markdown("## Detailed Analysis", elem_classes=["section-title"])
        analysis_output = gr.Markdown(
            value="*Detailed analysis will appear here...*",
            elem_classes=["content-box"],
        )

        # Footer note
        gr.Markdown(
            "---\n*Processing may take a few moments depending on content size.*",
        )

        # Connect the button click to the analysis function
        analyze_btn.click(
            fn=analyze_paper,
            inputs=[paper_id_input, keywords_input],
            outputs=[status_output, analysis_output, summary_output],
        )

        # Allow Enter key to trigger analysis
        paper_id_input.submit(
            fn=analyze_paper,
            inputs=[paper_id_input, keywords_input],
            outputs=[status_output, analysis_output, summary_output],
        )

    return demo, theme, custom_css


def main():
    """Main entry point for the UI application."""
    logger.info("Starting Research Radar UI...")

    demo, theme, custom_css = create_ui()
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        show_error=True,
        theme=theme,
        css=custom_css,
    )


if __name__ == "__main__":
    main()
