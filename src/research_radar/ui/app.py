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
            f"Starting analysis for: {paper_id} with keywords: {selected_keywords}"
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
        analysis_text = format_analysis(analysis) if analysis else "No analysis available"

        status_msg = f"Analysis completed successfully for: {paper_id_result}"

        return status_msg, analysis_text, summary

    except Exception as e:
        logger.error(f"Error analyzing {paper_id}: {e}", exc_info=True)
        return "Error occurred", "", f"Failed to analyze: {str(e)}"


def create_ui():
    """Create and configure the Gradio interface."""

    # Professional theme with modern blue color scheme
    theme = gr.themes.Soft(
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

    with gr.Blocks(title="Research Radar - Paper Analysis", theme=theme) as demo:
        gr.Markdown(
            """
            <div style="text-align: center; padding: 40px 20px; background: linear-gradient(135deg, #f0f4ff 0%, #ffffff 100%); border-radius: 12px; margin-bottom: 30px;">
                <h1 style="margin: 0; font-size: 36px; font-weight: 700; color: #1e40af; letter-spacing: -0.5px;">Research Radar</h1>
                <p style="margin: 8px 0 0 0; font-size: 16px; color: #64748b; font-weight: 500;">AI-Powered Research Analysis Platform</p>
                <p style="margin: 12px 0 0 0; font-size: 14px; color: #94a3b8;">Analyze research papers and videos with intelligent content filtering</p>
            </div>
            """
        )

        with gr.Row():
            with gr.Column(scale=2):
                paper_id_input = gr.Textbox(
                    label="Enter content ID",
                    placeholder="Enter a Hugging Face paper ID (e.g. 2510.24081) or a YouTube video ID (e.g. qYNweeDHiyU)",
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

            with gr.Column(scale=1):
                analyze_btn = gr.Button("Analyze Content", variant="primary", size="lg")

        status_output = gr.Textbox(
            label="Status",
            interactive=False,
            lines=1,
        )

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
            ---
            **Note:** Analysis may take a few moments depending on the content size and complexity.
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
