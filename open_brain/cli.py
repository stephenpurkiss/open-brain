"""CLI entry point for Open Brain."""
import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description="Open Brain -- persistent semantic memory for AI tools")
    subparsers = parser.add_subparsers(dest="command")

    serve_parser = subparsers.add_parser("serve", help="Start MCP stdio server")
    serve_parser.add_argument("--db", default=None, help="Path to SQLite database (default: ~/.open-brain/brain.db)")

    stats_parser = subparsers.add_parser("stats", help="Show brain statistics")
    stats_parser.add_argument("--db", default=None, help="Path to SQLite database")

    export_parser = subparsers.add_parser("export", help="Export thoughts to JSON")
    export_parser.add_argument("output", help="Output JSON file path")
    export_parser.add_argument("--db", default=None, help="Path to SQLite database")

    args = parser.parse_args()

    if args.command == "serve":
        from .server import run_server
        run_server(args.db)
    elif args.command == "stats":
        from .db.sqlite_backend import SQLiteBackend
        db = SQLiteBackend(args.db)
        import json
        print(json.dumps(db.stats(), indent=2, default=str))
    elif args.command == "export":
        from .db.sqlite_backend import SQLiteBackend
        import json
        db = SQLiteBackend(args.db)
        rows = db.conn.execute("SELECT id, content, category, scope, source, created_at FROM thoughts ORDER BY created_at").fetchall()
        thoughts = [dict(row) for row in rows]
        with open(args.output, "w") as f:
            json.dump(thoughts, f, indent=2, default=str)
        print(f"Exported {len(thoughts)} thoughts to {args.output}")
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
