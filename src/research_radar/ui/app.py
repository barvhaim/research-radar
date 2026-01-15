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
    Format the analysis dictionary into a readable string.

    Args:
        analysis: Dictionary with questions as keys and answers as values

    Returns:
        Formatted analysis text
    """
    if not analysis:
        return "No analysis available"

    formatted_parts = []
    for question, answer in analysis.items():
        formatted_parts.append(f"**{question}**\n\n{answer}\n")

    return "\n---\n\n".join(formatted_parts)


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

        return status_msg, analysis_text, summary

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

    custom_css = (
        "body { max-width: 1200px; margin: 0 auto; padding: 20px; } "
        "textarea { scrollbar-width: none; } "
        "textarea::-webkit-scrollbar { display: none; }"
    )
    with gr.Blocks(
        title="Research Radar - Paper Analysis",
        theme=theme,
        css=custom_css,
    ) as demo:
        gr.Markdown(
            """
<div style="text-align: center; padding: 60px 20px 50px 20px;
backdrop-filter: blur(10px); border-radius: 16px; margin-bottom: 40px;
border: 1px solid rgba(255, 255, 255, 0.7);">
<h1 style="margin: 0; font-size: 48px; font-weight: 900; color: #1e40af;
letter-spacing: -1.2px; font-family: 'Inter', sans-serif;">Research Radar</h1>
<p style="margin: 16px 0 8px 0; font-size: 20px; color: #3b82f6;
font-weight: 600;">Intelligent Research Analysis Platform</p>
<p style="margin: 0; font-size: 16px; color: #64748b; font-weight: 400;
line-height: 1.5;">Extract insights from papers and videos with AI-powered
filtering and analysis</p>
</div>
            """
        )

        with gr.Row(equal_height=False):
            with gr.Column(scale=3):
                paper_id_input = gr.Textbox(
                    label="Enter content ID",
                    placeholder="Paper ID (e.g. 2510.24081) or YouTube ID (e.g. qYNweeDHiyU)",
                    lines=1,
                )

                keywords_input = gr.Dropdown(
                    choices=available_keywords,
                    label="Select Keywords (optional - leave empty to skip filtering)",
                    value=[],
                    multiselect=True,
                    interactive=True,
                    allow_custom_value=True,
                )

            with gr.Column(scale=0.5):
                gr.Markdown("")  # Spacer for button alignment
                analyze_btn = gr.Button("→", variant="primary", size="lg", min_width=50)

        status_output = gr.Textbox(
            label="Status",
            interactive=False,
            lines=1,
        )

        gr.Markdown("")  # Spacing

        with gr.Row():
            with gr.Column():
                analysis_output = gr.Textbox(
                    label="Analysis (Question-Answer)",
                    interactive=False,
                    lines=12,
                )

            with gr.Column():
                summary_output = gr.Textbox(
                    label="Summary",
                    interactive=False,
                    lines=12,
                )

        gr.Markdown("")  # Spacing

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

        gr.Markdown(
            """
<div style="margin-top: 40px; padding: 20px;
background: rgba(59, 130, 246, 0.05); border-radius: 12px;
border-left: 4px solid #3b82f6;">
<p style="margin: 0; font-size: 14px; color: #FFFFFF; font-weight: 500;">
Processing may take a few moments depending on content size.</p>
</div>
            """
        )

    return demo


def main():
    """Main entry point for the UI application."""
    logger.info("Starting Research Radar UI...")

    demo = create_ui()
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        show_error=True,
    )


if __name__ == "__main__":
    main()
