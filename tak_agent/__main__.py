#!/usr/bin/env python3
"""
TAK AI Agent - Main entry point

Run with:
    python -m tak_agent --config agents/myagent.yaml
    python -m tak_agent --help
"""

from .run import cli

if __name__ == "__main__":
    cli()
