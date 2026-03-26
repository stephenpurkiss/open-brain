# Open Brain

Persistent semantic memory for AI tools via MCP.

Your AI forgets everything between sessions. Open Brain doesn't.

## What It Does

Capture thoughts with semantic meaning, search by concept (not keywords), organize by category. Works with Claude Code, Cursor, and any MCP-compatible tool.

## Install

```bash
pip install open-brain
```

## Usage

### As MCP Server (Claude Code)

Add to your `.mcp.json`:

```json
{
  "mcpServers": {
    "open-brain": {
      "command": "open-brain",
      "args": ["serve"]
    }
  }
}
```

### CLI

```bash
open-brain stats          # Show brain overview
open-brain export out.json  # Export all thoughts
open-brain serve          # Start MCP server
```

## Tools

- **capture_thought** -- Save a thought with semantic embedding
- **search_thoughts** -- Search by meaning (vector similarity)
- **browse_recent** -- Browse chronologically
- **stats** -- Overview metrics

## How It Differs from claude-mem

| | claude-mem | Open Brain |
|--|-----------|------------|
| Memory type | Session logs | Semantic thoughts |
| Search | Keyword | Vector similarity |
| Categories | None | 7 customizable domains |
| Storage | Files | SQLite (local) or PostgreSQL (cloud) |
| Updates | Append-only | Searchable, updatable |
| MCP native | No | Yes |

## Storage

By default, thoughts are stored in `~/.open-brain/brain.db` (SQLite). Embeddings are generated locally using the gte-small ONNX model (384 dimensions, ~67MB downloaded on first use).

No data leaves your machine. Self-sovereign knowledge.

## License

MIT
