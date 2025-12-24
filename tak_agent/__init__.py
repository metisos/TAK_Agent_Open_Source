"""
TAK AI Agent Framework

A modular, configurable AI agent framework for TAK networks.
Agents connect as full team members and can interact via chat,
place markers, create routes, and provide tactical support.

Example usage:

    from tak_agent import AgentConfig, TakAgent, create_agent
    from tak_agent.llm import ClaudeProvider

    # Quick creation with defaults
    agent = create_agent(
        config_path="agents/myagent.yaml",
        api_key="sk-ant-..."
    )
    await agent.run()

    # Or manual setup
    config = AgentConfig("agents/myagent.yaml")
    llm = ClaudeProvider(api_key="sk-ant-...")
    agent = TakAgent(config=config, llm_provider=llm)
    await agent.start()
"""

from .core import AgentConfig, TakAgent, TakClient, CotBuilder
from .llm import BaseLLMProvider, ClaudeProvider, GroqProvider

__version__ = "1.0.0"
__all__ = [
    "AgentConfig",
    "TakAgent",
    "TakClient",
    "CotBuilder",
    "BaseLLMProvider",
    "ClaudeProvider",
    "GroqProvider",
    "create_agent",
    "configure_agent",
]


def create_agent(
    config_path: str,
    api_key: str = None,
    provider: str = "claude",
    model: str = None,
) -> TakAgent:
    """
    Create a TakAgent from a configuration file.

    Args:
        config_path: Path to agent YAML configuration file
        api_key: LLM API key (uses env var if not provided)
        provider: LLM provider ("claude" or "groq")
        model: Model name (uses config default if not provided)

    Returns:
        Configured TakAgent instance ready to start

    Example:
        agent = create_agent("agents/geoint.yaml", api_key="sk-ant-...")
        await agent.run()
    """
    import os
    from dotenv import load_dotenv

    load_dotenv()

    config = AgentConfig(config_path)

    # Determine provider
    provider = provider or config.llm_provider

    # Get API key
    if not api_key:
        if provider == "claude":
            api_key = os.environ.get("ANTHROPIC_API_KEY")
        elif provider == "groq":
            api_key = os.environ.get("GROQ_API_KEY")

    if not api_key:
        raise ValueError(f"No API key provided for {provider}")

    # Create LLM provider
    if provider == "claude":
        llm = ClaudeProvider(
            api_key=api_key,
            model=model or config.llm_model,
            temperature=config.llm_temperature,
            max_tokens=config.llm_max_tokens,
        )
    elif provider == "groq":
        llm = GroqProvider(
            api_key=api_key,
            model=model or config.llm_model,
            temperature=config.llm_temperature,
            max_tokens=config.llm_max_tokens,
        )
    else:
        raise ValueError(f"Unknown provider: {provider}")

    return TakAgent(config=config, llm_provider=llm)


def configure_agent(
    name: str,
    callsign: str,
    tak_host: str,
    tak_port: int = 8089,
    cert_name: str = None,
    team: str = "Cyan",
    role: str = "HQ",
    lat: float = 0.0,
    lon: float = 0.0,
    provider: str = "claude",
    model: str = "claude-sonnet-4-20250514",
    template: str = "default",
    custom_instructions: str = "",
    save_path: str = None,
) -> dict:
    """
    Create an agent configuration programmatically.

    Args:
        name: Agent name (used for filename)
        callsign: Display name in TAK
        tak_host: TAK server hostname
        tak_port: TAK server port (default: 8089)
        cert_name: Certificate name (without extension)
        team: Team color
        role: Team role
        lat: Starting latitude
        lon: Starting longitude
        provider: LLM provider ("claude" or "groq")
        model: LLM model name
        template: Personality template name
        custom_instructions: Additional instructions
        save_path: Path to save YAML config (optional)

    Returns:
        Configuration dictionary

    Example:
        config = configure_agent(
            name="recon",
            callsign="RECON-1",
            tak_host="tak.example.com",
            cert_name="GRP5",
            team="Green",
            role="Team Lead",
            template="recon"
        )
    """
    import yaml
    from pathlib import Path

    cert_name = cert_name or name.upper()

    config = {
        "agent": {
            "callsign": callsign,
            "uid": f"{callsign}-{name}",
            "team": team,
            "role": role,
            "position": {
                "lat": lat,
                "lon": lon,
            },
            "stale_minutes": 10,
            "position_report_interval": 60,
        },
        "tak_server": {
            "host": tak_host,
            "port": tak_port,
            "protocol": "ssl",
            "cert_file": f"/app/certs/{cert_name}.pem",
            "key_file": f"/app/certs/{cert_name}.key",
            "ca_file": "/app/certs/ca.pem",
        },
        "chat": {
            "respond_to_all": True,
        },
        "llm": {
            "provider": provider,
            "model": model,
            "temperature": 0.3,
            "max_tokens": 1024,
        },
        "personality": {
            "template": template,
            "custom_instructions": custom_instructions or f"You are {callsign}.",
        },
        "logging": {
            "level": "INFO",
            "file": f"/app/logs/{name}.log",
        },
    }

    if save_path:
        path = Path(save_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(f"# TAK AI Agent Configuration\n")
            f.write(f"# Agent: {callsign}\n\n")
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    return config
