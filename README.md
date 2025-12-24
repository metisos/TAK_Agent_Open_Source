# TAK AI Agent Framework

A modular, configurable AI agent framework for TAK (Team Awareness Kit) networks. Agents connect as full team members with proper credentials and can interact via chat, place markers, create routes, and provide tactical support.

## Overview

TAK AI Agent allows you to deploy AI-powered virtual team members on your TAK server. Each agent:

- Connects via TLS with client certificates (same as human users)
- Appears as a team member with callsign, team color, and role
- Responds to chat messages using LLM-powered intent analysis
- Can place tactical markers (friendly, hostile, neutral, unknown)
- Can create routes with connected waypoints
- Can delete markers and routes it created
- Tracks positions of other team members

## Requirements

- Python 3.11+
- Docker and Docker Compose
- TAK Server with client certificate authentication (port 8089)
- Client certificates (.pem/.key) for each agent
- Anthropic API key (Claude) or Groq API key

## Quick Start

### 1. Install

**From PyPI (recommended):**

```bash
pip install tak-ai-agent
```

**From source:**

```bash
git clone https://github.com/metisos/TAK_Agent_Open_Source.git
cd TAK_Agent_Open_Source
pip install -e .
```

### 2. Add Certificates

Place client certificates in the `certs/` directory:

```
certs/
  ca.pem          # CA certificate from TAK server
  AGENT1.pem      # Client certificate
  AGENT1.key      # Client private key
```

Extract from .p12 files if needed:

```bash
openssl pkcs12 -in AGENT1.p12 -out certs/AGENT1.pem -clcerts -nokeys -legacy
openssl pkcs12 -in AGENT1.p12 -out certs/AGENT1.key -nocerts -nodes -legacy
```

### 3. Configure API Keys

```bash
cp .env.example .env
# Edit .env with your API keys
```

Or use the CLI:

```bash
python -m tak_agent.cli
# Select "Configure API keys"
```

### 4. Create an Agent

**Using CLI (interactive):**

```bash
python -m tak_agent.cli
# Select "Create new agent"
# Follow the prompts
```

**Using Python (programmatic):**

```python
from tak_agent import AgentConfig, TakAgent
from tak_agent.llm import ClaudeProvider

config = AgentConfig("agents/myagent.yaml")
llm = ClaudeProvider(api_key="sk-ant-...")
agent = TakAgent(config=config, llm_provider=llm)

await agent.start()
```

**Using YAML directly:**

```yaml
# agents/myagent.yaml
agent:
  callsign: "OVERWATCH"
  uid: "OVERWATCH-001"
  team: "Cyan"
  role: "HQ"
  position:
    lat: 32.7750
    lon: -96.8000

tak_server:
  host: "your-tak-server.com"
  port: 8089
  cert_file: "/app/certs/AGENT1.pem"
  key_file: "/app/certs/AGENT1.key"
  ca_file: "/app/certs/ca.pem"

llm:
  provider: "claude"
  model: "claude-sonnet-4-20250514"
  temperature: 0.3
  max_tokens: 1024

personality:
  template: "tactical"
```

### 5. Run

**With Docker (recommended):**

```bash
docker compose up -d
docker logs -f tak-agent-geoint
```

**Without Docker:**

```bash
python -m tak_agent.run --config agents/myagent.yaml
```

## Configuration Reference

### Agent Configuration (YAML)

| Field | Description | Required |
|-------|-------------|----------|
| `agent.callsign` | Display name in TAK | Yes |
| `agent.uid` | Unique identifier | Yes |
| `agent.team` | Team color (Cyan, Blue, Green, etc.) | No (default: Cyan) |
| `agent.role` | Role (HQ, Team Lead, Team Member, etc.) | No (default: Team Member) |
| `agent.position.lat` | Starting latitude | No (default: 0.0) |
| `agent.position.lon` | Starting longitude | No (default: 0.0) |
| `agent.stale_minutes` | Position stale time | No (default: 10) |
| `agent.position_report_interval` | Seconds between position updates | No (default: 60) |
| `tak_server.host` | TAK server hostname | Yes |
| `tak_server.port` | TAK server port | Yes (usually 8089) |
| `tak_server.cert_file` | Path to client certificate | Yes |
| `tak_server.key_file` | Path to client private key | Yes |
| `tak_server.ca_file` | Path to CA certificate | Yes |
| `llm.provider` | LLM provider (claude, groq) | No (default: claude) |
| `llm.model` | Model name | No |
| `llm.temperature` | Response temperature | No (default: 0.3) |
| `llm.max_tokens` | Max response tokens | No (default: 1024) |
| `personality.template` | System prompt template name | No (default: default) |
| `personality.custom_instructions` | Additional instructions | No |

### Team Colors

- Cyan, Blue, Green, Yellow, Orange, Magenta, Red, White, Maroon, Purple

### Roles

- HQ, Team Lead, Team Member, Medic, RTO, Sniper, Forward Observer

### Personality Templates

| Template | Description |
|----------|-------------|
| `geoint` | Geospatial intelligence support |
| `tactical` | General tactical coordination |
| `recon` | Reconnaissance and surveillance |
| `logistics` | Supply and transport coordination |
| `default` | Basic support agent |

## CLI Reference

```bash
python -m tak_agent.cli
```

### Main Menu

1. **Create new agent** - Interactive wizard to create agent configuration
2. **List agents** - Show all configured agents
3. **Edit agent** - Modify existing agent configuration
4. **Delete agent** - Remove agent configuration
5. **Configure API keys** - Set LLM provider API keys
6. **Start/Stop agents** - Docker compose controls

## Programmatic API

### Basic Usage

```python
import asyncio
from tak_agent import AgentConfig, TakAgent
from tak_agent.llm import ClaudeProvider

async def main():
    # Load configuration
    config = AgentConfig("agents/myagent.yaml")

    # Initialize LLM
    llm = ClaudeProvider(
        api_key="your-api-key",
        model="claude-sonnet-4-20250514"
    )

    # Create and run agent
    agent = TakAgent(config=config, llm_provider=llm)
    await agent.run()

asyncio.run(main())
```

### Sending Map Objects

```python
# Place a marker
await agent.send_marker(
    name="HQ Alpha",
    lat=32.7800,
    lon=-96.7950,
    marker_type="friendly",  # friendly, hostile, neutral, unknown
    remarks="Command post"
)

# Create a route
await agent.send_route(
    route_name="MSR Tampa",
    waypoints=[
        {"name": "SP", "lat": 32.78, "lon": -96.80},
        {"name": "CP1", "lat": 32.79, "lon": -96.79},
        {"name": "OBJ", "lat": 32.80, "lon": -96.78},
    ]
)

# Delete all items created by this agent
await agent.delete_all_created()
```

### Custom LLM Provider

```python
from tak_agent.llm import BaseLLMProvider

class MyProvider(BaseLLMProvider):
    async def generate(self, system_prompt, user_message, context=None):
        # Your implementation
        return "Response text"
```

## Certificate Setup

Agents authenticate to TAK server using client certificates, the same way human users do. This ensures agents are full team members with proper permissions.

### From TAK Server Admin

1. Generate a user/certificate in TAK Server admin interface
2. Download the .p12 file
3. Extract PEM files:

```bash
# Extract certificate
openssl pkcs12 -in USER.p12 -out USER.pem -clcerts -nokeys -legacy -passin pass:atakatak

# Extract private key
openssl pkcs12 -in USER.p12 -out USER.key -nocerts -nodes -legacy -passin pass:atakatak

# Get CA certificate from truststore
openssl pkcs12 -in truststore-root.p12 -out ca.pem -cacerts -nokeys -legacy -passin pass:atakatak
```

### File Permissions

```bash
chmod 600 certs/*.key
chmod 644 certs/*.pem
```

## Docker Deployment

### docker-compose.yml

```yaml
version: '3.8'

services:
  agent1:
    build: .
    container_name: tak-agent-1
    restart: always
    env_file:
      - .env
    volumes:
      - ./agents/agent1.yaml:/app/config.yaml:ro
      - ./certs:/app/certs:ro
      - ./templates:/app/templates:ro
      - ./logs:/app/logs
    networks:
      - tak-network

networks:
  tak-network:
    external: true
    name: your-tak-network
```

### Multiple Agents

Create multiple service entries in docker-compose.yml, each with its own config:

```yaml
services:
  geoint:
    build: .
    container_name: tak-agent-geoint
    volumes:
      - ./agents/geoint.yaml:/app/config.yaml:ro
      # ...

  recon:
    build: .
    container_name: tak-agent-recon
    volumes:
      - ./agents/recon.yaml:/app/config.yaml:ro
      # ...
```

## Architecture

```
tak-ai-agent/
├── tak_agent/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── agent.py        # Main agent class
│   │   ├── config.py       # Configuration loader
│   │   ├── cot_builder.py  # CoT XML message builder
│   │   └── tak_client.py   # TAK server connection
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── base_provider.py
│   │   ├── claude_provider.py
│   │   └── groq_provider.py
│   ├── cli.py              # Interactive CLI
│   └── run.py              # Entry point
├── agents/                  # Agent configurations
├── certs/                   # Certificates
├── templates/
│   └── system_prompts/      # Personality templates
├── docker-compose.yml
├── Dockerfile
├── setup.py
└── requirements.txt
```

## TAK Map Actions

The agent can create map objects when requested via chat. The LLM includes special markers in its response that are parsed and sent to TAK:

### Markers

```
[MARKER: name, latitude, longitude, type, remarks]
```

Types: `friendly`, `hostile`, `neutral`, `unknown`

### Routes

```
[ROUTE: route_name | wp1_name,lat,lon | wp2_name,lat,lon | ...]
```

### Delete All

```
[DELETE_ALL]
```

## Troubleshooting

### Agent not connecting

1. Check certificate paths in config
2. Verify TAK server hostname and port
3. Check certificate permissions (key should be 600)
4. Ensure CA certificate matches TAK server

### Agent not responding to chat

1. Check LLM API key in .env
2. Verify LLM provider and model in config
3. Check logs: `docker logs tak-agent-name`

### Markers not appearing

1. Verify coordinates are valid (lat: -90 to 90, lon: -180 to 180)
2. Check TAK client is receiving data
3. Review agent logs for parsing errors

## Support

For support, questions, or feature requests, contact:

Christian Johnson - cjohnson@metisos.com

## License

MIT License

## Contributing

Contributions welcome. Please submit pull requests with tests.
