"""Configuration loader for TAK AI Agent"""

import os
from pathlib import Path
from typing import Any, Optional
import yaml
from dotenv import load_dotenv


class AgentConfig:
    """Loads and provides access to agent configuration from YAML file"""

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        load_dotenv()

        with open(self.config_path, "r") as f:
            self._config = yaml.safe_load(f)

        self._validate_config()

    def _validate_config(self) -> None:
        """Validate required configuration fields"""
        required_sections = ["agent", "tak_server"]
        for section in required_sections:
            if section not in self._config:
                raise ValueError(f"Missing required configuration section: {section}")

        required_agent_fields = ["callsign", "uid"]
        for field in required_agent_fields:
            if field not in self._config["agent"]:
                raise ValueError(f"Missing required agent field: {field}")

        required_server_fields = ["host", "port", "cert_file", "key_file", "ca_file"]
        for field in required_server_fields:
            if field not in self._config["tak_server"]:
                raise ValueError(f"Missing required tak_server field: {field}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation (e.g., 'agent.callsign')"""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    @property
    def callsign(self) -> str:
        return self._config["agent"]["callsign"]

    @property
    def uid(self) -> str:
        return self._config["agent"]["uid"]

    @property
    def team(self) -> str:
        return self._config["agent"].get("team", "Cyan")

    @property
    def role(self) -> str:
        return self._config["agent"].get("role", "Team Member")

    @property
    def position(self) -> dict:
        return self._config["agent"].get("position", {"lat": 0.0, "lon": 0.0})

    @property
    def tak_server_host(self) -> str:
        return self._config["tak_server"]["host"]

    @property
    def tak_server_port(self) -> int:
        return self._config["tak_server"]["port"]

    @property
    def cert_file(self) -> str:
        return self._config["tak_server"]["cert_file"]

    @property
    def key_file(self) -> str:
        return self._config["tak_server"]["key_file"]

    @property
    def ca_file(self) -> str:
        return self._config["tak_server"]["ca_file"]

    @property
    def trigger_words(self) -> list:
        return self._config.get("chat", {}).get("trigger_words", [])

    @property
    def llm_provider(self) -> str:
        return self._config.get("llm", {}).get("provider", "groq")

    @property
    def llm_model(self) -> str:
        return self._config.get("llm", {}).get("model", "llama-3.3-70b-versatile")

    @property
    def llm_temperature(self) -> float:
        return self._config.get("llm", {}).get("temperature", 0.3)

    @property
    def llm_max_tokens(self) -> int:
        return self._config.get("llm", {}).get("max_tokens", 500)

    @property
    def system_prompt(self) -> str:
        """Load system prompt from template or custom instructions"""
        personality = self._config.get("personality", {})
        template_name = personality.get("template", "default")
        custom = personality.get("custom_instructions", "")

        template_path = Path(__file__).parent.parent.parent / "templates" / "system_prompts" / f"{template_name}.txt"
        template_content = ""
        if template_path.exists():
            with open(template_path, "r") as f:
                template_content = f.read()

        if custom:
            return f"{template_content}\n\n{custom}".strip()
        return template_content if template_content else self._default_system_prompt()

    def _default_system_prompt(self) -> str:
        return f"""You are {self.callsign}, an AI agent operating on a TAK (Team Awareness Kit) network.

Your role: {self.role}
Team: {self.team}

You provide tactical support to team members via chat. Keep responses concise and professional.
When providing coordinates, use decimal degrees format.
When planning routes, provide clear waypoint descriptions with coordinates."""

    @property
    def stale_minutes(self) -> int:
        return self._config["agent"].get("stale_minutes", 10)

    @property
    def position_report_interval(self) -> int:
        return self._config["agent"].get("position_report_interval", 60)

    def get_api_key(self, key_name: str) -> Optional[str]:
        """Get API key from environment variable"""
        return os.environ.get(key_name)

    @property
    def groq_api_key(self) -> Optional[str]:
        return self.get_api_key("GROQ_API_KEY")

    @property
    def anthropic_api_key(self) -> Optional[str]:
        return self.get_api_key("ANTHROPIC_API_KEY")

    @property
    def log_level(self) -> str:
        return self._config.get("logging", {}).get("level", "INFO")

    @property
    def log_file(self) -> Optional[str]:
        return self._config.get("logging", {}).get("file")
