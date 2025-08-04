"""II-SEARCH-CIR: II-SEARCH CODE INTEGRATED REASONING.
This module implements an AI-powered research assistant that can conduct multi-turn
conversations, execute Python code, and generate comprehensive research reports.

Example queries:
- What are the treatment options for relapsing polychondritis?
- How can the total, direct, and indirect effects be computed in mediation analysis?
- Why did the discrepancy between proportion mediated and proportion of variance explained arise in the course example?
"""

import argparse
from datetime import datetime
import logging
import os
import sys
from typing import Dict, Optional, Any, Union

from transformers import AutoTokenizer
from vllm import LLM, SamplingParams

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

try:
    from configs import SYSTEM_PROMPT, HINT_PROMPT, SUMMARY_REPORT, TOOL
    from configs import (
        DEFAULT_MODEL_PATH,
        DEFAULT_TEMPERATURE,
        DEFAULT_TOP_P,
    )
except ImportError as e:
    logger.error(f"Failed to import configuration: {e}")
    sys.exit(1)

try:
    from core.code_executor import PythonCodeTool
except ImportError as e:
    logger.error(f"Failed to import PythonCodeTool: {e}")
    sys.exit(1)


class SearchAssistantConfig:
    """Configuration class for the Search Assistant."""

    def __init__(self, args: argparse.Namespace):
        """Initialize configuration from command line arguments.

        Args:
            args: Parsed command line arguments.
        """
        self.model_path: str = args.model_name_or_path
        self.temperature: float = args.temperature
        self.top_p: float = args.top_p
        self.max_tokens: int = args.max_tokens
        self.max_turns: int = args.max_turns
        self.interactive: bool = args.interactive
        self.generate_summary: bool = not args.no_summary
        self.query: Optional[str] = getattr(args, "query", None)

        # Model configuration
        self.tensor_parallel_size: int = 1
        self.rope_scaling: Dict[str, Union[str, float, int]] = {
            "rope_type": "yarn",
            "factor": 4.0,
            "original_max_position_embeddings": 32768,
        }
        self.max_model_len: int = 128_000
        self.trust_remote_code: bool = True

    def validate(self) -> None:
        """Validate configuration parameters.

        Raises:
            ValueError: If any configuration parameter is invalid.
        """
        if self.temperature < 0.0 or self.temperature > 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")

        if self.top_p < 0.0 or self.top_p > 1.0:
            raise ValueError("Top-p must be between 0.0 and 1.0")

        if self.max_tokens <= 0:
            raise ValueError("Max tokens must be positive")

        if self.max_turns <= 0:
            raise ValueError("Max turns must be positive")

        if not os.path.exists(self.model_path) and not self.model_path.startswith(
            ("hf://", "https://")
        ):
            # Only warn, don't fail, as it might be a HuggingFace model name
            logger.warning(f"Model path may not exist: {self.model_path}")


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the command-line argument parser.

    Returns:
        argparse.ArgumentParser: Configured argument parser.
    """
    parser = argparse.ArgumentParser(
        description="II-SEARCH-CIR: II-SEARCH CODE INTEGRATED REASONING.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--model-name-or-path",
        type=str,
        default=DEFAULT_MODEL_PATH,
        help="Path to the model directory or HuggingFace model name",
    )

    parser.add_argument(
        "--temperature",
        type=float,
        default=DEFAULT_TEMPERATURE,
        help="Temperature for sampling (higher = more random)",
    )

    parser.add_argument(
        "--top_p",
        type=float,
        default=DEFAULT_TOP_P,
        help="Top-p (nucleus) sampling parameter",
    )

    parser.add_argument(
        "--max-tokens",
        type=int,
        default=128000,
        help="Maximum number of tokens to generate",
    )

    parser.add_argument(
        "--max-turns", type=int, default=32, help="Maximum number of conversation turns"
    )

    parser.add_argument(
        "--no-summary", action="store_true", help="Disable summary report generation"
    )

    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Enable interactive mode for multiple queries",
    )

    parser.add_argument(
        "--query", type=str, help="Specific query to process (overrides default query)"
    )

    return parser


def predict_query(
    query: str,
    model: LLM,
    tokenizer: AutoTokenizer,
    sampling_param: Optional[Dict[str, float]] = None,
    max_tokens: int = 128000,
    max_turn: int = 32,
    generate_summary_report: bool = True,
) -> Dict[str, Any]:
    """Execute a research query using the AI model with multi-turn conversation support.

    This function conducts an interactive research session where the AI can:
    - Analyze the user's query
    - Execute Python code for data analysis and web searches
    - Generate comprehensive research reports

    Args:
        query: The research question or query to investigate.
        model: The loaded VLLM language model instance.
        tokenizer: The tokenizer corresponding to the model.
        sampling_param: Dictionary containing sampling parameters (temperature, top_p).
        max_tokens: Maximum number of tokens the model can generate.
        max_turn: Maximum number of conversation turns allowed.
        generate_summary_report: Whether to generate a final summary report.

    Returns:
        Dict containing:
            - 'trace': Complete conversation trace
            - 'messages': List of conversation messages
            - 'total_tokens': Total number of tokens used

    Raises:
        ValueError: If query is empty or model/tokenizer are invalid.
        RuntimeError: If model generation fails.
    """
    if not query.strip():
        raise ValueError("Query cannot be empty")

    if sampling_param is None:
        sampling_param = {"temperature": DEFAULT_TEMPERATURE, "top_p": DEFAULT_TOP_P}

    current_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT.format(tools=TOOL, current_date=current_date),
            "content_type": "text",
        },
        {"role": "user", "content": query, "content_type": "text"},
    ]

    logger.info(f"Starting research query: {query[:100]}...")
    trace = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )

    # Add hint prompt for better reasoning
    trace = trace + "<think>\n" + HINT_PROMPT
    trace_with_mask_obs = trace

    for turn in range(max_turn):
        logger.info(f"Processing at: {turn}/{max_turn}")
        params = SamplingParams(
            temperature=sampling_param.get("temperature", 0.6),
            top_p=sampling_param.get("top_p", 0.9),
            stop=["<end_code>"],
            max_tokens=max_tokens,
        )
        # print(trace)
        response_turn = model.generate(
            trace,
            sampling_params=params,
        )[0]
        # print(response_turn)

        output = response_turn.outputs[0].text
        print("-------------")
        print(output)
        print("-------------")
        messages.append({"role": "assistant", "content": output})
        stop_reason = response_turn.outputs[0].stop_reason

        if stop_reason == "<end_code>":
            # execute python code here
            tool_exe = PythonCodeTool()
            obs, has_error, code_to_execute = tool_exe.conduct_action(output, {})

            if has_error is True or obs is None:
                if obs is not None:
                    logger.info(
                        f"Error log return from code {obs} and code is: \n{code_to_execute}"
                    )
                else:
                    logger.info(f"Error code: {code_to_execute}")
                obs = "Code execute with unknown exception\nPlease review your code and keep in mind that you must use visit_webpage with exactly url return from web_search!!!"
            # Trim output to maximum 3000 tokens
            # print(code_to_execute, obs)
            obs_tokens = tokenizer(obs, add_special_tokens=False)["input_ids"][:3000]
            obs = "```output\n" + tokenizer.decode(obs_tokens) + "\n```"
            trace = trace + output + "<end_code>\n" + obs
            print("-------------")
            print(obs)
            print("-------------")
            trace_with_mask_obs = (
                trace_with_mask_obs
                + output
                + "<end_code>\n"
                + "```output\nOUTPUT_CODE\n```"
            )
            messages.append(
                {"role": "assistant", "content": obs, "content_type": "observation"}
            )
        else:
            # stop by lengths or finish trace
            trace = trace + output
            trace_with_mask_obs = trace_with_mask_obs + output
            break

    if generate_summary_report:
        messages_report = [
            {
                "role": "system",
                "content": SUMMARY_REPORT,
            },
            {
                "role": "user",
                "content": f"""Here is the research process and findings:

                ### Research Process
                {trace}

                ### Original Question
                {query}

                Based on the research above, please provide a clear and comprehensive report.
                """,
            },
        ]

        params = SamplingParams(
            temperature=sampling_param.get("temperature", 0.6),
            top_p=sampling_param.get("top_p", 0.9),
            max_tokens=128000,
        )
        trace_summary = tokenizer.apply_chat_template(
            messages_report, tokenize=False, add_generation_prompt=True
        )
        response_summary = model.generate(
            trace_summary,
            sampling_params=params,
        )[0]

        messages.append(
            {
                "role": "assistant",
                "content": response_summary.outputs[0].text,
                "content_type": "summary",
            }
        )

        trace = (
            trace
            + "\n\nSUMMARY\n\n"
            + response_summary.outputs[0].text.split("</think>")[-1]
        )

    return {
        "trace": trace,
        "messages": messages,
        "total_tokens": len(tokenizer(trace, add_special_tokens=False)["input_ids"]),
        "summary": response_summary.outputs[0].text.split("</think>")[-1],
    }


def main() -> None:
    """Main entry point for the search assistant application."""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Create and validate configuration
    try:
        config = SearchAssistantConfig(args)
        config.validate()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Invalid configuration: {e}")
        sys.exit(1)

    try:
        # Load model and tokenizer
        logger.info(f"Loading model from: {config.model_path}")
        model = LLM(
            model=config.model_path,
            tensor_parallel_size=config.tensor_parallel_size,
            rope_scaling=config.rope_scaling,
            max_model_len=config.max_model_len,
            trust_remote_code=config.trust_remote_code,
        )
        tokenizer = AutoTokenizer.from_pretrained(config.model_path)
        logger.info("Model and tokenizer loaded successfully")

    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        sys.exit(1)

    # Determine query processing mode
    if config.interactive:
        while True:
            try:
                query = input(
                    "\nEnter your research query (or 'quit' to exit): "
                ).strip()
                if query.lower() in ["quit", "exit", "q"]:
                    break
                if not query:
                    print("Please enter a valid query.")
                    continue

                result = predict_query(
                    query,
                    model,
                    tokenizer,
                    sampling_param={
                        "temperature": config.temperature,
                        "top_p": config.top_p,
                    },
                    max_tokens=config.max_tokens,
                    max_turn=config.max_turns,
                    generate_summary_report=config.generate_summary,
                )

                print(f"\nTotal tokens used: {result['total_tokens']}")
                print("\n" + "=" * 80)
                print("Research Results:")
                print("=" * 80)
                print(result["trace"])

            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                logger.error(f"Error processing query: {e}")
                print(f"An error occurred: {e}")
    else:
        # Single query mode
        query = (
            config.query
            or "What are the potential complications associated with relapsing polychondritis?"
        )

        try:
            result = predict_query(
                query,
                model,
                tokenizer,
                sampling_param={
                    "temperature": config.temperature,
                    "top_p": config.top_p,
                },
                max_tokens=config.max_tokens,
                max_turn=config.max_turns,
                generate_summary_report=config.generate_summary,
            )

            print(f"Query: {query}")
            print(f"Total tokens used: {result['total_tokens']}")
            print("\n" + "=" * 80)
            print("Research Results:")
            print("=" * 80)
            print(result["trace"])

        except Exception as e:
            logger.error(f"Failed to process query: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
