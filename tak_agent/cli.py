#!/usr/bin/env python3
"""TAK AI Agent Configuration CLI"""

import os
import sys
import yaml
from pathlib import Path

# ANSI colors
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    END = '\033[0m'

# TAK team colors
TEAM_COLORS = [
    "Cyan", "Blue", "Green", "Yellow", "Orange",
    "Magenta", "Red", "White", "Maroon", "Purple"
]

# TAK roles
ROLES = [
    "HQ", "Team Lead", "Team Member", "Medic",
    "RTO", "Sniper", "Forward Observer"
]

# LLM providers
LLM_PROVIDERS = {
    "claude": {
        "name": "Claude (Anthropic)",
        "models": [
            "claude-sonnet-4-20250514",
            "claude-3-5-sonnet-20241022",
            "claude-3-haiku-20240307"
        ],
        "env_key": "ANTHROPIC_API_KEY"
    },
    "groq": {
        "name": "Groq",
        "models": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768"
        ],
        "env_key": "GROQ_API_KEY"
    }
}

# Agent templates
TEMPLATES = [
    ("geoint", "GEOINT - Geospatial Intelligence Support"),
    ("tactical", "Tactical - General tactical support"),
    ("recon", "Recon - Reconnaissance and surveillance"),
    ("logistics", "Logistics - Supply and transport coordination"),
    ("default", "Default - Basic agent template"),
]

# Base directory is parent of tak_agent package
BASE_DIR = Path(__file__).parent.parent
AGENTS_DIR = BASE_DIR / "agents"
CERTS_DIR = BASE_DIR / "certs"
TEMPLATES_DIR = BASE_DIR / "templates" / "system_prompts"


def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')


def print_header():
    print(f"""
{Colors.CYAN}{Colors.BOLD}╔══════════════════════════════════════════════════════════════╗
║              TAK AI AGENT CONFIGURATION                       ║
║                    OVERWATCH CLI                               ║
╚══════════════════════════════════════════════════════════════╝{Colors.END}
""")


def print_menu(title, options):
    """Print a menu and get selection"""
    print(f"\n{Colors.BOLD}{title}{Colors.END}")
    print("-" * 40)
    for i, opt in enumerate(options, 1):
        if isinstance(opt, tuple):
            print(f"  {Colors.CYAN}{i}.{Colors.END} {opt[1]}")
        else:
            print(f"  {Colors.CYAN}{i}.{Colors.END} {opt}")
    print(f"  {Colors.YELLOW}0.{Colors.END} Back/Cancel")
    print()

    while True:
        try:
            choice = input(f"{Colors.GREEN}Select option: {Colors.END}").strip()
            if choice == '0' or choice.lower() == 'q':
                return None
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx] if isinstance(options[idx], tuple) else (options[idx], options[idx])
        except (ValueError, IndexError):
            pass
        print(f"{Colors.RED}Invalid selection. Try again.{Colors.END}")


def get_input(prompt, default=None, required=True):
    """Get text input from user"""
    if default:
        prompt = f"{prompt} [{Colors.YELLOW}{default}{Colors.END}]: "
    else:
        prompt = f"{prompt}: "

    while True:
        value = input(f"{Colors.GREEN}{prompt}{Colors.END}").strip()
        if not value and default:
            return default
        if value or not required:
            return value
        print(f"{Colors.RED}This field is required.{Colors.END}")


def get_float_input(prompt, default=None):
    """Get float input from user"""
    while True:
        value = get_input(prompt, str(default) if default else None)
        try:
            return float(value)
        except ValueError:
            print(f"{Colors.RED}Please enter a valid number.{Colors.END}")


def list_available_certs():
    """List available certificates in certs directory"""
    certs = []
    if CERTS_DIR.exists():
        for f in CERTS_DIR.glob("*.pem"):
            # Check if matching key exists
            key_file = f.with_suffix(".key")
            if key_file.exists():
                name = f.stem
                certs.append((name, f"Certificate: {name}"))
    return certs


def list_agents():
    """List all configured agents"""
    agents = []
    if AGENTS_DIR.exists():
        for f in AGENTS_DIR.glob("*.yaml"):
            try:
                with open(f) as file:
                    config = yaml.safe_load(file)
                    callsign = config.get("agent", {}).get("callsign", "Unknown")
                    team = config.get("agent", {}).get("team", "Unknown")
                    agents.append({
                        "file": f,
                        "name": f.stem,
                        "callsign": callsign,
                        "team": team
                    })
            except Exception:
                pass
    return agents


def show_agents():
    """Display all configured agents"""
    agents = list_agents()

    print(f"\n{Colors.BOLD}Configured Agents:{Colors.END}")
    print("-" * 60)

    if not agents:
        print(f"  {Colors.YELLOW}No agents configured yet.{Colors.END}")
    else:
        print(f"  {'Name':<15} {'Callsign':<15} {'Team':<15} {'File'}")
        print("-" * 60)
        for agent in agents:
            print(f"  {agent['name']:<15} {agent['callsign']:<15} {agent['team']:<15} {agent['file'].name}")

    print()
    input(f"{Colors.GREEN}Press Enter to continue...{Colors.END}")


def create_agent():
    """Interactive agent creation wizard"""
    clear_screen()
    print_header()
    print(f"{Colors.BOLD}CREATE NEW AGENT{Colors.END}")
    print("=" * 40)

    # Basic info
    print(f"\n{Colors.CYAN}Step 1: Basic Information{Colors.END}")

    agent_name = get_input("Agent name (filename)", required=True).lower().replace(" ", "_")
    callsign = get_input("Callsign (display name)", agent_name.upper())
    uid = get_input("UID", f"{callsign}-{agent_name}")

    # Team selection
    print(f"\n{Colors.CYAN}Step 2: Team Configuration{Colors.END}")
    team_result = print_menu("Select team color:", TEAM_COLORS)
    if team_result is None:
        return
    team = team_result[0]

    role_result = print_menu("Select role:", ROLES)
    if role_result is None:
        return
    role = role_result[0]

    # Position
    print(f"\n{Colors.CYAN}Step 3: Starting Position{Colors.END}")
    print(f"  {Colors.YELLOW}Enter coordinates in decimal degrees{Colors.END}")
    lat = get_float_input("Latitude", 32.7750)
    lon = get_float_input("Longitude", -96.8000)

    # TAK Server
    print(f"\n{Colors.CYAN}Step 4: TAK Server Connection{Colors.END}")
    host = get_input("TAK server hostname", "takadmin.grg-tak.com")
    port = int(get_input("TAK server port", "8089"))

    # Certificate
    print(f"\n{Colors.CYAN}Step 5: Certificate{Colors.END}")
    certs = list_available_certs()
    if not certs:
        print(f"{Colors.RED}No certificates found in {CERTS_DIR}{Colors.END}")
        print(f"Please add .pem and .key files to the certs directory.")
        input(f"{Colors.GREEN}Press Enter to continue...{Colors.END}")
        return

    cert_result = print_menu("Select certificate:", certs)
    if cert_result is None:
        return
    cert_name = cert_result[0]

    # LLM Provider
    print(f"\n{Colors.CYAN}Step 6: LLM Configuration{Colors.END}")
    provider_options = [(k, v["name"]) for k, v in LLM_PROVIDERS.items()]
    provider_result = print_menu("Select LLM provider:", provider_options)
    if provider_result is None:
        return
    provider = provider_result[0]

    provider_info = LLM_PROVIDERS[provider]
    model_options = [(m, m) for m in provider_info["models"]]
    model_result = print_menu("Select model:", model_options)
    if model_result is None:
        return
    model = model_result[0]

    # Template
    print(f"\n{Colors.CYAN}Step 7: Personality Template{Colors.END}")
    template_result = print_menu("Select template:", TEMPLATES)
    if template_result is None:
        return
    template = template_result[0]

    # Custom instructions
    print(f"\n{Colors.CYAN}Step 8: Custom Instructions (optional){Colors.END}")
    custom = get_input("Custom instructions", "", required=False)

    # Build config
    config = {
        "agent": {
            "callsign": callsign,
            "uid": uid,
            "team": team,
            "role": role,
            "position": {
                "lat": lat,
                "lon": lon
            },
            "stale_minutes": 10,
            "position_report_interval": 60
        },
        "tak_server": {
            "host": host,
            "port": port,
            "protocol": "ssl",
            "cert_file": f"/app/certs/{cert_name}.pem",
            "key_file": f"/app/certs/{cert_name}.key",
            "ca_file": "/app/certs/ca.pem"
        },
        "chat": {
            "respond_to_all": True
        },
        "llm": {
            "provider": provider,
            "model": model,
            "temperature": 0.3,
            "max_tokens": 1024
        },
        "personality": {
            "template": template,
            "custom_instructions": custom if custom else f"You are {callsign}, a tactical support agent."
        },
        "logging": {
            "level": "INFO",
            "file": f"/app/logs/{agent_name}.log"
        }
    }

    # Save
    AGENTS_DIR.mkdir(exist_ok=True)
    config_path = AGENTS_DIR / f"{agent_name}.yaml"

    print(f"\n{Colors.CYAN}Configuration Summary:{Colors.END}")
    print("-" * 40)
    print(f"  Callsign: {callsign}")
    print(f"  Team: {team} / {role}")
    print(f"  Position: {lat}, {lon}")
    print(f"  TAK Server: {host}:{port}")
    print(f"  Certificate: {cert_name}")
    print(f"  LLM: {provider} / {model}")
    print(f"  Template: {template}")
    print()

    confirm = get_input(f"Save configuration to {config_path.name}? (y/n)", "y")
    if confirm.lower() == 'y':
        with open(config_path, 'w') as f:
            # Add header comment
            f.write(f"# TAK AI Agent Configuration\n")
            f.write(f"# Agent: {callsign}\n")
            f.write(f"# Created by OVERWATCH CLI\n\n")
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        print(f"\n{Colors.GREEN}Agent configuration saved to {config_path}{Colors.END}")
        print(f"\nTo run this agent:")
        print(f"  {Colors.CYAN}docker compose up -d{Colors.END}")
    else:
        print(f"{Colors.YELLOW}Configuration cancelled.{Colors.END}")

    input(f"\n{Colors.GREEN}Press Enter to continue...{Colors.END}")


def edit_agent():
    """Edit an existing agent"""
    agents = list_agents()
    if not agents:
        print(f"\n{Colors.YELLOW}No agents to edit.{Colors.END}")
        input(f"{Colors.GREEN}Press Enter to continue...{Colors.END}")
        return

    options = [(a["name"], f"{a['callsign']} ({a['team']})") for a in agents]
    result = print_menu("Select agent to edit:", options)
    if result is None:
        return

    agent_name = result[0]
    config_path = AGENTS_DIR / f"{agent_name}.yaml"

    # Open in editor or show simple edit options
    print(f"\n{Colors.CYAN}Editing {agent_name}{Colors.END}")
    print(f"Config file: {config_path}")
    print()
    print("Options:")
    print(f"  1. Open in nano")
    print(f"  2. Open in vim")
    print(f"  3. Show current config")
    print(f"  0. Cancel")

    choice = input(f"\n{Colors.GREEN}Select: {Colors.END}").strip()

    if choice == '1':
        os.system(f"nano {config_path}")
    elif choice == '2':
        os.system(f"vim {config_path}")
    elif choice == '3':
        print()
        with open(config_path) as f:
            print(f.read())
        input(f"\n{Colors.GREEN}Press Enter to continue...{Colors.END}")


def delete_agent():
    """Delete an agent configuration"""
    agents = list_agents()
    if not agents:
        print(f"\n{Colors.YELLOW}No agents to delete.{Colors.END}")
        input(f"{Colors.GREEN}Press Enter to continue...{Colors.END}")
        return

    options = [(a["name"], f"{a['callsign']} ({a['team']})") for a in agents]
    result = print_menu("Select agent to delete:", options)
    if result is None:
        return

    agent_name = result[0]
    config_path = AGENTS_DIR / f"{agent_name}.yaml"

    confirm = get_input(f"{Colors.RED}Delete {agent_name}? This cannot be undone. (yes/no){Colors.END}", "no")
    if confirm.lower() == 'yes':
        config_path.unlink()
        print(f"{Colors.GREEN}Agent {agent_name} deleted.{Colors.END}")
    else:
        print(f"{Colors.YELLOW}Deletion cancelled.{Colors.END}")

    input(f"\n{Colors.GREEN}Press Enter to continue...{Colors.END}")


def check_api_keys():
    """Check and configure API keys"""
    env_file = BASE_DIR / ".env"

    print(f"\n{Colors.BOLD}API Key Configuration{Colors.END}")
    print("-" * 40)

    # Load existing
    existing = {}
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if '=' in line:
                    key, val = line.strip().split('=', 1)
                    existing[key] = val

    # Check each provider
    for provider_id, info in LLM_PROVIDERS.items():
        key_name = info["env_key"]
        current = existing.get(key_name, "")
        status = f"{Colors.GREEN}Set{Colors.END}" if current else f"{Colors.RED}Not set{Colors.END}"
        print(f"  {info['name']}: {status}")

    print()
    choice = get_input("Update API keys? (y/n)", "n")
    if choice.lower() != 'y':
        return

    # Update keys
    for provider_id, info in LLM_PROVIDERS.items():
        key_name = info["env_key"]
        current = existing.get(key_name, "")
        masked = current[:10] + "..." if len(current) > 10 else current
        new_val = get_input(f"{info['name']} API key", masked, required=False)
        if new_val and new_val != masked:
            existing[key_name] = new_val

    # Save
    with open(env_file, 'w') as f:
        for key, val in existing.items():
            f.write(f"{key}={val}\n")

    print(f"\n{Colors.GREEN}API keys saved to {env_file}{Colors.END}")
    input(f"{Colors.GREEN}Press Enter to continue...{Colors.END}")


def run_agents():
    """Start/stop agents with docker compose"""
    print(f"\n{Colors.BOLD}Agent Control{Colors.END}")
    print("-" * 40)

    options = [
        ("start", "Start all agents"),
        ("stop", "Stop all agents"),
        ("restart", "Restart all agents"),
        ("logs", "View logs"),
        ("status", "Check status"),
    ]

    result = print_menu("Select action:", options)
    if result is None:
        return

    action = result[0]

    if action == "start":
        os.system("docker compose up -d")
    elif action == "stop":
        os.system("docker compose down")
    elif action == "restart":
        os.system("docker compose down && docker compose up -d")
    elif action == "logs":
        os.system("docker compose logs -f --tail=50")
    elif action == "status":
        os.system("docker compose ps")

    input(f"\n{Colors.GREEN}Press Enter to continue...{Colors.END}")


def main_menu():
    """Main menu loop"""
    while True:
        clear_screen()
        print_header()

        options = [
            ("create", "Create new agent"),
            ("list", "List agents"),
            ("edit", "Edit agent"),
            ("delete", "Delete agent"),
            ("keys", "Configure API keys"),
            ("run", "Start/Stop agents"),
        ]

        result = print_menu("Main Menu", options)

        if result is None:
            print(f"\n{Colors.CYAN}Goodbye!{Colors.END}\n")
            sys.exit(0)

        action = result[0]

        if action == "create":
            create_agent()
        elif action == "list":
            show_agents()
        elif action == "edit":
            edit_agent()
        elif action == "delete":
            delete_agent()
        elif action == "keys":
            check_api_keys()
        elif action == "run":
            run_agents()


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.CYAN}Goodbye!{Colors.END}\n")
        sys.exit(0)
