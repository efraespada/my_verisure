"""Base command class for the CLI."""

import sys
import os
import logging
from abc import ABC, abstractmethod
from typing import Optional

# Add core to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "core"))

from core.dependency_injection.providers import (
    get_auth_use_case,
    get_alarm_use_case,
    get_installation_use_case,
    get_session_use_case,
)

from ..utils.session_manager import session_manager
from ..utils.display import print_error, print_info

logger = logging.getLogger(__name__)


class BaseCommand(ABC):
    """Base class for all CLI commands."""

    def __init__(self):
        self.auth_use_case = None
        self.alarm_use_case = None
        self.installation_use_case = None
        self.session_use_case = None

    async def setup(self, interactive: bool = True) -> bool:
        """Setup the command by ensuring authentication and getting use cases."""
        try:
            # Ensure authentication
            if not await session_manager.ensure_authenticated(interactive):
                return False

            # Get use cases
            self.auth_use_case = get_auth_use_case()
            self.alarm_use_case = get_alarm_use_case()
            self.installation_use_case = get_installation_use_case()
            self.session_use_case = get_session_use_case()

            return True

        except Exception as e:
            print_error(f"Error setting up command: {e}")
            return False

    @abstractmethod
    async def execute(self, *args, **kwargs):
        """Execute the command. Must be implemented by subclasses."""
        pass

    async def cleanup(self):
        """Clean up resources."""
        await session_manager.cleanup()

    def get_installation_id(
        self, installation_id: Optional[str] = None
    ) -> Optional[str]:
        """Get installation ID, either from parameter or current session."""
        if installation_id:
            return installation_id

        if session_manager.current_installation:
            return session_manager.current_installation

        return None

    async def select_installation_if_needed(
        self, installation_id: Optional[str] = None
    ) -> Optional[str]:
        """Select installation if not provided and multiple are available."""
        from ..utils.input_helpers import select_installation

        if installation_id:
            return installation_id

        if session_manager.current_installation:
            return session_manager.current_installation

        # Get all installations and let user select
        try:
            installations = await session_manager.get_installations()
            if not installations:
                print_error("No hay instalaciones disponibles")
                return None

            if len(installations) == 1:
                installation = installations[0]
                print_info(
                    f"Usando única instalación disponible: {installation.alias}"
                )
                session_manager.current_installation = installation.numinst
                return installation.numinst

            # Multiple installations, let user select
            selected_id = select_installation(installations)
            if selected_id:
                session_manager.current_installation = selected_id
                return selected_id

            return None

        except Exception as e:
            print_error(f"Error obteniendo instalaciones: {e}")
            return None
