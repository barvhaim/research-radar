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


def analyze_paper(paper_id: str) -> tuple[str, str]:
    """
    Analyze a paper and return the results.

    Args:
        paper_id: Hugging Face paper ID (e.g., "2510.24081")

    Returns:
        Tuple of (status_message, summary_text)
    """
    if not paper_id or not paper_id.strip():
        return "Error", "Please enter a valid paper ID"

    try:
        logger.info(f"Starting analysis for paper: {paper_id}")

        # Call workflow adapter directly
        result = run_workflow_for_paper(paper_id.strip())

        paper_id_result = result.get("paper_id", paper_id)

        # Check for analysis first (preferred), then fall back to summary
        analysis = result.get("analysis", {})
        if analysis:
            # Format the analysis dict if available
            summary = format_analysis(analysis)
        else:
            # Fall back to summary if no analysis
            summary = result.get("summary", "No analysis available")

        status_msg = f"Analysis completed successfully for paper: {paper_id_result}"

        return status_msg, summary

    except Exception as e:
        logger.error(f"Error analyzing paper {paper_id}: {e}", exc_info=True)
        return "Error occurred", f"Failed to analyze paper: {str(e)}"


def create_ui():
    """Create and configure the Gradio interface."""

    with gr.Blocks(title="Research Radar - Paper Analysis") as demo:
        gr.Markdown(
            """
            # Research Radar - Paper Analysis

            Analyze research papers using AI-powered workflow.
            Enter a Hugging Face paper ID to get started.

            **Example Paper ID:** `2510.24081`
            """
        )

        with gr.Row():
            with gr.Column(scale=2):
                paper_id_input = gr.Textbox(
                    label="Paper ID",
                    placeholder="Enter Hugging Face paper ID (e.g., 2510.24081)",
                    lines=1,
                )
            with gr.Column(scale=1):
                analyze_btn = gr.Button(
                    "Analyze Paper",
                    variant="primary",
                    size="lg"
                )

        status_output = gr.Textbox(
            label="Status",
            interactive=False,
            lines=1,
        )

        summary_output = gr.Textbox(
            label="Paper Summary",
            interactive=False,
            lines=15,
        )

        # Connect the button click to the analysis function
        analyze_btn.click(
            fn=analyze_paper,
            inputs=[paper_id_input],
            outputs=[status_output, summary_output],
        )

        # Allow Enter key to trigger analysis
        paper_id_input.submit(
            fn=analyze_paper,
            inputs=[paper_id_input],
            outputs=[status_output, summary_output],
        )

        gr.Markdown(
            """
            ---
            **Note:** Analysis may take a few moments depending on the paper size and complexity.
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
        theme=gr.themes.Soft(),
        show_api=False, 
    )


if __name__ == "__main__":
    main()
