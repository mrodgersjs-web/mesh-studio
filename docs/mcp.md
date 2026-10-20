# MCP server

mesh-studio ships an MCP (Model Context Protocol) server so agent clients can
probe your service fleet as tools instead of shelling out to the CLI.

```bash
pip install -e ".[mcp]"
rig-mesh-mcp                    # stdio transport, for local agent clients
rig-mesh-mcp --sse --port 8092  # SSE transport for remote clients
```

## Client configuration (stdio)

From a clone of this repository, install the `mcp` extra in the Python
environment your agent client uses, then register the server. Replace the
example `cwd` with your clone's path.

```json
{
  "mcpServers": {
    "rig-mesh": {
      "command": "python",
      "args": ["-m", "rig_mesh.mcp_server"],
      "cwd": "/path/to/mesh-studio"
    }
  }
}
```

## Tools

| Tool | Description |
| --- | --- |
| `probe_subsystem(name)` | Live health probe for one subsystem |
| `get_status()` | Aggregate probe of all subsystems |
| `list_subsystems()` | Registry listing (no I/O) |
| `run_audit()` | Full audit plus JSON artifact |
| `smoke()` | Deterministic local smoke test |

## Resources

| URI | Description |
| --- | --- |
| `rig://registry` | Full subsystem registry as JSON |
| `rig://audit/latest` | Latest audit artifact |

## Prompts

| Prompt | Description |
| --- | --- |
| `health_check_prompt` | Asks the agent to interpret a status snapshot |

The server wraps the same `CommandRouter` the CLI uses, so tool results and
CLI output are the same JSON.
