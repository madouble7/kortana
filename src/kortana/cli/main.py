#!/usr/bin/env python3
"""
Kortana Main CLI Entry Point
Sacred Circuit Development Platform
"""

import argparse
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from kortana.config import get_config, load_config
from kortana.core.autonomous_development_engine import AutonomousDevelopmentEngine
from kortana.core.brain import Brain


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser"""
    parser = argparse.ArgumentParser(
        prog="kortana",
        description="Project Kor'tana - Autonomous AI Agent Development Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  kortana start                    # Start the autonomous development engine
  kortana server                   # Start the API server
  kortana agents list             # List all agents
  kortana memory status           # Check memory status
  kortana config validate        # Validate configuration

For more help on a specific command, use:
  kortana <command> --help
        """,
    )

    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")

    parser.add_argument(
        "--config", type=str, help="Configuration file to use (default: auto-detect)"
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Start command
    start_parser = subparsers.add_parser(
        "start", help="Start the autonomous development engine"
    )
    start_parser.add_argument(
        "--analyze-critical-issues",
        action="store_true",
        help="Analyze critical issues on startup",
    )
    start_parser.add_argument(
        "--background", action="store_true", help="Run in background mode"
    )

    # Server command
    server_parser = subparsers.add_parser("server", help="Start the API server")
    server_parser.add_argument("--host", default="localhost", help="Host to bind to")
    server_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    server_parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload"
    )

    # Status command
    status_parser = subparsers.add_parser("status", help="Show system status")
    status_parser.add_argument(
        "--detailed", action="store_true", help="Show detailed status"
    )

    # Interactive command
    interactive_parser = subparsers.add_parser(
        "interactive", help="Start interactive mode"
    )
    interactive_parser.add_argument("--model", help="Model to use for interaction")

    return parser


def cmd_start(args) -> int:
    """Handle the start command"""
    try:
        config = load_config(args.config)

        if args.verbose:
            print("Starting Autonomous Development Engine...")
            print(f"Environment: {config.app.environment}")
            print(f"Debug mode: {config.app.debug}")

        # Initialize the development engine
        engine = AutonomousDevelopmentEngine(config=config)

        if args.analyze_critical_issues:
            print("Analyzing critical issues...")
            engine.analyze_critical_issues()

        if args.background:
            print("Starting in background mode...")
            engine.start_background()
        else:
            print("Starting autonomous development engine...")
            engine.start()

        return 0
    except Exception as e:
        print(f"Error starting engine: {e}", file=sys.stderr)
        return 1


def cmd_server(args) -> int:
    """Handle the server command"""
    try:
        config = load_config(args.config)

        print(f"Starting API server on {args.host}:{args.port}")

        # Import here to avoid circular imports
        from kortana.api.server import create_app, run_server

        app = create_app(config)
        run_server(app, host=args.host, port=args.port, reload=args.reload)

        return 0
    except Exception as e:
        print(f"Error starting server: {e}", file=sys.stderr)
        return 1


def cmd_status(args) -> int:
    """Handle the status command"""
    try:
        config = get_config()

        print("=== Project Kor'tana Status ===")
        print("Version: 1.0.0")
        print(f"Environment: {config.app.environment}")
        print(f"Debug mode: {config.app.debug}")

        if args.detailed:
            print("\nConfiguration:")
            print(f"  - API Host: {config.api.host}:{config.api.port}")
            print(f"  - Default Model: {config.models.default_provider}")
            print(f"  - Memory Max Entries: {config.memory.max_entries}")
            print(f"  - Max Concurrent Agents: {config.agents.max_concurrent}")

        # Check system health
        brain = Brain(config=config)
        health = brain.check_health()

        print(f"\nSystem Health: {'✓ Healthy' if health else '✗ Issues detected'}")

        return 0
    except Exception as e:
        print(f"Error checking status: {e}", file=sys.stderr)
        return 1


def cmd_interactive(args) -> int:
    """Handle the interactive command"""
    try:
        config = load_config(args.config)

        print("=== Project Kor'tana Interactive Mode ===")
        print("Type 'help' for commands, 'exit' to quit")

        brain = Brain(config=config)

        while True:
            try:
                user_input = input("\nkor'tana> ").strip()

                if user_input.lower() in ["exit", "quit"]:
                    print("Goodbye!")
                    break
                elif user_input.lower() == "help":
                    print("""
Available commands:
  status      - Show system status
  agents      - List active agents
  memory      - Show memory statistics
  think <msg> - Ask the brain to think about something
  exit        - Exit interactive mode
                    """)
                elif user_input.lower() == "status":
                    health = brain.check_health()
                    print(
                        f"System Health: {'✓ Healthy' if health else '✗ Issues detected'}"
                    )
                elif user_input.lower() == "agents":
                    # List active agents from the brain
                    try:
                        # Get agent information from the brain's components
                        agents = []
                        if hasattr(brain, 'planner') and brain.planner:
                            agents.append(('Planning Agent', 'Active', 'Generates plans for goals'))
                        if hasattr(brain, 'executor') and brain.executor:
                            agents.append(('Execution Agent', 'Active', 'Executes plan steps'))
                        if hasattr(brain, 'memory_manager') and brain.memory_manager:
                            agents.append(('Memory Agent', 'Active', 'Manages memory storage and retrieval'))
                        
                        if agents:
                            print("\nActive Agents:")
                            print("-" * 60)
                            for name, status, description in agents:
                                print(f"  {name:20s} [{status}] - {description}")
                            print("-" * 60)
                            print(f"Total: {len(agents)} agent(s)")
                        else:
                            print("No agents currently active")
                    except Exception as e:
                        print(f"Error listing agents: {e}")
                        
                elif user_input.lower() == "memory":
                    # Show memory statistics
                    try:
                        print("\nMemory Statistics:")
                        print("-" * 60)
                        
                        if hasattr(brain, 'memory_manager') and brain.memory_manager:
                            # Try to get memory stats
                            try:
                                # Count memories if possible
                                memory_count = 0
                                if hasattr(brain.memory_manager, 'memories'):
                                    memory_count = len(brain.memory_manager.memories)
                                elif hasattr(brain.memory_manager, 'get_all_memories'):
                                    memories = brain.memory_manager.get_all_memories()
                                    memory_count = len(memories) if memories else 0
                                
                                print(f"  Total Memories: {memory_count}")
                                print(f"  Status: Active")
                                
                                # Show memory manager type
                                mem_type = type(brain.memory_manager).__name__
                                print(f"  Manager Type: {mem_type}")
                            except Exception as e:
                                print(f"  Status: Active (unable to retrieve detailed stats)")
                                print(f"  Error: {e}")
                        else:
                            print("  Memory Manager: Not initialized")
                        
                        print("-" * 60)
                    except Exception as e:
                        print(f"Error getting memory statistics: {e}")
                elif user_input.startswith("think "):
                    thought = user_input[6:]
                    response = brain.think(thought)
                    print(f"Brain: {response}")
                else:
                    print(f"Unknown command: {user_input}")

            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
            except EOFError:
                print("\nGoodbye!")
                break

        return 0
    except Exception as e:
        print(f"Error in interactive mode: {e}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args(argv)

    # Set up logging based on verbosity
    if args.verbose or args.debug:
        import logging

        level = logging.DEBUG if args.debug else logging.INFO
        logging.basicConfig(
            level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    # Handle commands
    if args.command == "start":
        return cmd_start(args)
    elif args.command == "server":
        return cmd_server(args)
    elif args.command == "status":
        return cmd_status(args)
    elif args.command == "interactive":
        return cmd_interactive(args)
    else:
        # No command specified, show help
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
