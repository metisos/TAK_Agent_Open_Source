#!/usr/bin/env python3
"""TAK AI Agent entry point"""

import argparse
import asyncio
import logging
import signal
import sys
from pathlib import Path

from tak_agent.core import AgentConfig, TakAgent
from tak_agent.llm import GroqProvider, ClaudeProvider


def setup_logging(level: str, log_file: str = None) -> None:
    """Configure logging"""
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    handlers = [logging.StreamHandler(sys.stdout)]

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        datefmt=date_format,
        handlers=handlers,
    )


async def main(config_path: str) -> None:
    """Main entry point"""
    # Load configuration
    config = AgentConfig(config_path)

    # Setup logging
    setup_logging(config.log_level, config.log_file)

    logger = logging.getLogger(__name__)
    logger.info(f"Loading agent configuration from: {config_path}")

    # Initialize LLM provider
    llm = None
    if config.llm_provider == "claude":
        api_key = config.anthropic_api_key
        if api_key:
            llm = ClaudeProvider(
                api_key=api_key,
                model=config.llm_model,
                temperature=config.llm_temperature,
                max_tokens=config.llm_max_tokens,
            )
            logger.info(f"Initialized Claude LLM with model: {config.llm_model}")
        else:
            logger.warning("ANTHROPIC_API_KEY not set, LLM features disabled")
    elif config.llm_provider == "groq":
        api_key = config.groq_api_key
        if api_key:
            llm = GroqProvider(
                api_key=api_key,
                model=config.llm_model,
                temperature=config.llm_temperature,
                max_tokens=config.llm_max_tokens,
            )
            logger.info(f"Initialized Groq LLM with model: {config.llm_model}")
        else:
            logger.warning("GROQ_API_KEY not set, LLM features disabled")
    else:
        logger.warning(f"Unknown LLM provider: {config.llm_provider}, LLM features disabled")

    # Create agent
    agent = TakAgent(config=config, llm_provider=llm)

    # Handle shutdown signals
    loop = asyncio.get_event_loop()
    shutdown_event = asyncio.Event()

    def handle_signal():
        logger.info("Shutdown signal received")
        shutdown_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_signal)

    # Run agent
    try:
        await agent.start()

        # Wait for shutdown signal
        await shutdown_event.wait()

    except Exception as e:
        logger.error(f"Agent error: {e}")
        raise
    finally:
        await agent.stop()


def cli():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="TAK AI Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config",
        "-c",
        required=True,
        help="Path to agent configuration YAML file",
    )

    args = parser.parse_args()

    try:
        asyncio.run(main(args.config))
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    cli()
