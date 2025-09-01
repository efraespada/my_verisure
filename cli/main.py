#!/usr/bin/env python3
"""My Verisure CLI - Command Line Interface."""

import argparse
import asyncio
import logging
import sys
import os

# Add core to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "core"))

from .commands.auth import AuthCommand
from .commands.info import InfoCommand
from .commands.alarm import AlarmCommand
from .utils.display import print_header, print_error, print_info
from .utils.session_manager import session_manager

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        description="My Verisure CLI - Command Line Interface for My Verisure integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Authentication
  my_verisure auth login
  my_verisure auth logout
  my_verisure auth status

  # Information
  my_verisure info installations
  my_verisure info services --installation-id 12345
  my_verisure info status --installation-id 12345

  # Alarm control
  my_verisure alarm status --installation-id 12345
  my_verisure alarm arm --mode away --installation-id 12345
  my_verisure alarm disarm --installation-id 12345

  # Non-interactive mode (for scripts)
  my_verisure auth login --non-interactive
  my_verisure alarm arm --mode away --no-confirm
        """,
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )

    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Disable interactive prompts (for scripts)",
    )

    # Create subparsers for commands
    subparsers = parser.add_subparsers(
        dest="command", help="Available commands"
    )

    # Auth command
    auth_parser = subparsers.add_parser(
        "auth", help="Authentication management"
    )
    auth_subparsers = auth_parser.add_subparsers(
        dest="action", help="Authentication actions"
    )

    auth_subparsers.add_parser("login", help="Login to My Verisure")
    auth_subparsers.add_parser("logout", help="Logout from My Verisure")
    auth_subparsers.add_parser("status", help="Show authentication status")

    # Info command
    info_parser = subparsers.add_parser("info", help="Information commands")
    info_subparsers = info_parser.add_subparsers(
        dest="action", help="Information actions"
    )

    info_subparsers.add_parser("installations", help="List all installations")

    services_parser = info_subparsers.add_parser(
        "services", help="Show installation services"
    )
    services_parser.add_argument("--installation-id", help="Installation ID")

    status_parser = info_subparsers.add_parser(
        "status", help="Show installation status"
    )
    status_parser.add_argument("--installation-id", help="Installation ID")

    # Alarm command
    alarm_parser = subparsers.add_parser("alarm", help="Alarm control")
    alarm_subparsers = alarm_parser.add_subparsers(
        dest="action", help="Alarm actions"
    )

    status_alarm_parser = alarm_subparsers.add_parser(
        "status", help="Show alarm status"
    )
    status_alarm_parser.add_argument(
        "--installation-id", help="Installation ID"
    )

    arm_parser = alarm_subparsers.add_parser("arm", help="Arm the alarm")
    arm_parser.add_argument(
        "--mode",
        required=True,
        choices=["away", "home", "night"],
        help="Arming mode",
    )
    arm_parser.add_argument("--installation-id", help="Installation ID")
    arm_parser.add_argument(
        "--no-confirm", action="store_true", help="Skip confirmation prompt"
    )

    disarm_parser = alarm_subparsers.add_parser(
        "disarm", help="Disarm the alarm"
    )
    disarm_parser.add_argument("--installation-id", help="Installation ID")
    disarm_parser.add_argument(
        "--no-confirm", action="store_true", help="Skip confirmation prompt"
    )

    return parser


async def main():
    """Main function."""
    parser = create_parser()
    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # Show header
    print_header("MY VERISURE CLI")
    print_info("Command Line Interface for My Verisure integration")
    print()

    try:
        if args.command == "auth":
            command = AuthCommand()
            success = await command.execute(
                args.action, interactive=not args.non_interactive
            )

        elif args.command == "info":
            command = InfoCommand()
            if args.action == "services":
                success = await command.execute(
                    args.action,
                    installation_id=args.installation_id,
                    interactive=not args.non_interactive,
                )
            elif args.action == "status":
                success = await command.execute(
                    args.action,
                    installation_id=args.installation_id,
                    interactive=not args.non_interactive,
                )
            else:
                success = await command.execute(
                    args.action, interactive=not args.non_interactive
                )

        elif args.command == "alarm":
            command = AlarmCommand()
            if args.action == "status":
                success = await command.execute(
                    args.action,
                    installation_id=args.installation_id,
                    interactive=not args.non_interactive,
                )
            elif args.action == "arm":
                success = await command.execute(
                    args.action,
                    mode=args.mode,
                    installation_id=args.installation_id,
                    confirm=not args.no_confirm,
                    interactive=not args.non_interactive,
                )
            elif args.action == "disarm":
                success = await command.execute(
                    args.action,
                    installation_id=args.installation_id,
                    confirm=not args.no_confirm,
                    interactive=not args.non_interactive,
                )
            else:
                success = False

        else:
            parser.print_help()
            return 0

        # Cleanup (skip for auth status since it doesn't initialize dependencies)
        if not (args.command == "auth" and args.action == "status"):
            await session_manager.cleanup()

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n⏹️  Proceso interrumpido por el usuario")
        await session_manager.cleanup()
        return 1

    except Exception as e:
        print_error(f"Error inesperado: {e}")
        await session_manager.cleanup()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
