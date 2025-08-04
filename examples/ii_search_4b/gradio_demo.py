"""Gradio Demo for II-SEARCH-CIR Research Assistant.

This module provides a web interface for the AI-powered research assistant that can
conduct multi-turn conversations, execute Python code, and generate research reports.
"""

import argparse
import gradio as gr
import logging
import sys
from typing import List, Tuple

from transformers import AutoTokenizer
from vllm import LLM

try:
    from search_assistant import predict_query, SearchAssistantConfig
    from configs import (
        DEFAULT_MODEL_PATH,
        DEFAULT_TEMPERATURE,
        DEFAULT_TOP_P,
        MAX_OUTPUT_TOKENS,
    )
except ImportError as e:
    logging.error(f"Failed to import required modules: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class GradioSearchAssistant:
    """Gradio interface for the Search Assistant."""

    def __init__(self, config: SearchAssistantConfig):
        """Initialize the Gradio assistant with configuration.

        Args:
            config: Configuration object for the search assistant.
        """
        self.config = config
        self.model = None
        self.tokenizer = None
        self.load_model()

    def load_model(self):
        """Load the model and tokenizer."""
        try:
            logger.info(f"Loading model from: {self.config.model_path}")
            self.model = LLM(
                model=self.config.model_path,
                tensor_parallel_size=self.config.tensor_parallel_size,
                rope_scaling=self.config.rope_scaling,
                max_model_len=self.config.max_model_len,
                trust_remote_code=self.config.trust_remote_code,
            )
            self.tokenizer = AutoTokenizer.from_pretrained(self.config.model_path)
            logger.info("Model and tokenizer loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def process_query(
        self,
        query: str,
        temperature: float,
        top_p: float,
        max_turns: int,
        generate_summary: bool,
        history: List[Tuple[str, str]],
    ) -> Tuple[List[Tuple[str, str]], str, str]:
        """Process a research query and return results.

        Args:
            query: The research question to investigate.
            temperature: Sampling temperature for model generation.
            top_p: Top-p sampling parameter.
            max_turns: Maximum number of conversation turns.
            generate_summary: Whether to generate a summary report.
            history: Previous conversation history.

        Returns:
            Tuple containing:
                - Updated conversation history
                - Research trace/log
                - Summary report (if generated)
        """
        if not query.strip():
            return history, "Please enter a valid query.", ""

        try:
            # Process the query
            result = predict_query(
                query=query,
                model=self.model,
                tokenizer=self.tokenizer,
                sampling_param={
                    "temperature": temperature,
                    "top_p": top_p,
                },
                max_tokens=self.config.max_tokens,
                max_turn=max_turns,
                generate_summary_report=generate_summary,
            )

            # Extract results
            trace = result.get("trace", "")
            summary = result.get("summary", "") if generate_summary else ""
            total_tokens = result.get("total_tokens", 0)

            # Update history
            history = history + [
                (query, f"Research completed. Total tokens used: {total_tokens}")
            ]

            # Format trace for display
            trace_display = (
                f"### Research Process\n\n{trace}\n\n### Total Tokens: {total_tokens}"
            )

            return history, trace_display, summary

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            error_msg = f"An error occurred: {str(e)}"
            history = history + [(query, error_msg)]
            return history, error_msg, ""

    def clear_conversation(self):
        """Clear the conversation history."""
        return [], "", ""


def create_interface(assistant: GradioSearchAssistant) -> gr.Blocks:
    """Create the Gradio interface.

    Args:
        assistant: The GradioSearchAssistant instance.

    Returns:
        gr.Blocks: The Gradio interface.
    """
    with gr.Blocks(title="II-SEARCH-CIR Research Assistant") as demo:
        gr.Markdown(
            """
            # II-SEARCH-CIR: AI-Powered Research Assistant
            
            This assistant can help you with complex research queries by:
            - Conducting multi-turn conversations
            - Executing Python code for analysis
            - Performing web searches
            - Generating comprehensive research reports
            
            ### Example Queries:
            - What are the treatment options for relapsing polychondritis?
            - How can the total, direct, and indirect effects be computed in mediation analysis?
            - Explain the latest developments in quantum computing
            """
        )

        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    label="Conversation", height=400, show_label=True, elem_id="chatbot"
                )

                query_input = gr.Textbox(
                    label="Enter your research query",
                    placeholder="Type your question here...",
                    lines=2,
                )

                with gr.Row():
                    submit_btn = gr.Button("Submit", variant="primary")
                    clear_btn = gr.Button("Clear")

            with gr.Column(scale=1):
                gr.Markdown("### Configuration")

                temperature = gr.Slider(
                    minimum=0.0,
                    maximum=2.0,
                    value=assistant.config.temperature,
                    step=0.1,
                    label="Temperature",
                    info="Higher values make output more random",
                )

                top_p = gr.Slider(
                    minimum=0.0,
                    maximum=1.0,
                    value=assistant.config.top_p,
                    step=0.05,
                    label="Top-p",
                    info="Nucleus sampling parameter",
                )

                max_turns = gr.Slider(
                    minimum=1,
                    maximum=50,
                    value=assistant.config.max_turns,
                    step=1,
                    label="Max Turns",
                    info="Maximum conversation turns",
                )

                generate_summary = gr.Checkbox(
                    value=assistant.config.generate_summary,
                    label="Generate Summary Report",
                    info="Create a comprehensive summary at the end",
                )

                gr.Markdown("### Example Queries")
                gr.Examples(
                    examples=[
                        "Who is the current president of US?",
                        "What are the potential complications associated with relapsing polychondritis?",
                        "How can I perform sentiment analysis on social media data using Python?",
                        "Explain the mechanism of action of mRNA vaccines",
                        "What are the best practices for implementing microservices architecture?",
                    ],
                    inputs=query_input,
                )

        with gr.Row():
            with gr.Column():
                research_trace = gr.Textbox(
                    label="Research Trace",
                    lines=20,
                    max_lines=30,
                    show_label=True,
                    interactive=False,
                )

        with gr.Row():
            with gr.Column():
                summary_output = gr.Textbox(
                    label="Summary Report",
                    lines=10,
                    max_lines=20,
                    show_label=True,
                    interactive=False,
                    visible=True,
                )

        # Event handlers
        def process_and_update(query, temp, top_p, turns, gen_summary, history):
            history, trace, summary = assistant.process_query(
                query, temp, top_p, turns, gen_summary, history
            )
            return history, "", trace, summary

        submit_btn.click(
            fn=process_and_update,
            inputs=[
                query_input,
                temperature,
                top_p,
                max_turns,
                generate_summary,
                chatbot,
            ],
            outputs=[chatbot, query_input, research_trace, summary_output],
        )

        query_input.submit(
            fn=process_and_update,
            inputs=[
                query_input,
                temperature,
                top_p,
                max_turns,
                generate_summary,
                chatbot,
            ],
            outputs=[chatbot, query_input, research_trace, summary_output],
        )

        clear_btn.click(
            fn=assistant.clear_conversation,
            inputs=[],
            outputs=[chatbot, research_trace, summary_output],
        )

        # Update summary visibility based on checkbox
        def toggle_summary_visibility(gen_summary):
            return gr.update(visible=gen_summary)

        generate_summary.change(
            fn=toggle_summary_visibility,
            inputs=[generate_summary],
            outputs=[summary_output],
        )

    return demo


def main():
    """Main entry point for the Gradio demo."""
    parser = argparse.ArgumentParser(
        description="Gradio Demo for II-SEARCH-CIR Search Assistant",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--model-name-or-path",
        type=str,
        default=DEFAULT_MODEL_PATH,
        help="Path to the model directory or HuggingFace model name",
    )

    parser.add_argument(
        "--share", action="store_true", help="Create a public sharing link for the demo"
    )

    parser.add_argument(
        "--server-port", type=int, default=7860, help="Port to run the Gradio server on"
    )

    parser.add_argument(
        "--server-name", type=str, default="127.0.0.1", help="Server name/IP to bind to"
    )

    args = parser.parse_args()

    # Create configuration
    config_args = argparse.Namespace(
        model_name_or_path=args.model_name_or_path,
        temperature=DEFAULT_TEMPERATURE,
        top_p=DEFAULT_TOP_P,
        max_tokens=MAX_OUTPUT_TOKENS,
        max_turns=32,
        interactive=False,
        no_summary=False,
    )

    try:
        config = SearchAssistantConfig(config_args)
        config.validate()

        # Create assistant and interface
        assistant = GradioSearchAssistant(config)
        demo = create_interface(assistant)

        # Launch the demo
        logger.info(f"Launching Gradio demo on {args.server_name}:{args.server_port}")
        demo.launch(
            server_name=args.server_name,
            server_port=args.server_port,
            share=args.share,
            show_error=True,
        )

    except Exception as e:
        logger.error(f"Failed to launch demo: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
