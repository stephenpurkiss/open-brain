"""MCP stdio server for Open Brain."""
import json
import sys

from .db.sqlite_backend import SQLiteBackend
from .embeddings import generate_embedding

TOOLS = {
    "capture_thought": {
        "description": "Save a thought to Open Brain. Generates a semantic embedding for similarity search. Use this to capture decisions, learnings, process rules, corrections, and insights that compound across sessions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "The thought content to save"},
                "category": {"type": "string", "enum": ["process", "legal", "strategic", "evidence", "decision", "identity", "general"], "default": "general"},
                "source": {"type": "string", "description": "Where this thought came from"},
            },
            "required": ["content"]
        }
    },
    "search_thoughts": {
        "description": "Search by meaning. Uses semantic similarity so conceptual queries work. Returns thoughts ranked by relevance.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query -- describe the concept"},
                "limit": {"type": "integer", "default": 10},
                "category": {"type": "string", "description": "Filter by category"},
            },
            "required": ["query"]
        }
    },
    "browse_recent": {
        "description": "Browse recent thoughts chronologically.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "hours": {"type": "integer", "default": 24},
                "category": {"type": "string"},
                "limit": {"type": "integer", "default": 20},
            }
        }
    },
    "stats": {
        "description": "Get overview: total thoughts, embedded count, categories, date range.",
        "inputSchema": {"type": "object", "properties": {}}
    }
}


def run_server(db_path=None):
    """Run MCP stdio server."""
    db = SQLiteBackend(db_path)

    def handle_request(request):
        method = request.get("method")
        params = request.get("params", {})
        req_id = request.get("id")

        if method == "initialize":
            return {"jsonrpc": "2.0", "id": req_id, "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "open-brain", "version": "0.1.0"}
            }}

        elif method == "notifications/initialized":
            return None

        elif method == "tools/list":
            tools_list = [{"name": n, "description": s["description"], "inputSchema": s["inputSchema"]} for n, s in TOOLS.items()]
            return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools_list}}

        elif method == "tools/call":
            tool_name = params.get("name")
            args = params.get("arguments", {})
            try:
                if tool_name == "capture_thought":
                    embedding = generate_embedding(args["content"])
                    result = db.capture(
                        content=args["content"],
                        category=args.get("category", "general"),
                        source=args.get("source"),
                        embedding=embedding,
                    )
                elif tool_name == "search_thoughts":
                    query_embedding = generate_embedding(args["query"])
                    result = db.search(query_embedding, args.get("limit", 10), args.get("category"))
                elif tool_name == "browse_recent":
                    result = db.browse_recent(args.get("hours", 24), args.get("category"), args.get("limit", 20))
                elif tool_name == "stats":
                    result = db.stats()
                else:
                    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}}

                return {"jsonrpc": "2.0", "id": req_id, "result": {
                    "content": [{"type": "text", "text": json.dumps(result, indent=2, default=str)}]
                }}
            except Exception as e:
                return {"jsonrpc": "2.0", "id": req_id, "result": {
                    "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                    "isError": True
                }}

        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown method: {method}"}}

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_request(request)
            if response:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
        except json.JSONDecodeError:
            pass
