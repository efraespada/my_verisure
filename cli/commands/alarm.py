"""Alarm control command for the CLI."""

import sys
import os
import logging
from typing import Optional

from .base import BaseCommand
from ..utils.display import (
    print_command_header,
    print_success,
    print_error,
    print_info,
    print_header,
    print_alarm_status,
)
from ..utils.input_helpers import confirm_action

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "custom_components", "my_verisure"))

from core.api.models.domain.alarm import ArmResult, DisarmResult


logger = logging.getLogger(__name__)


class AlarmCommand(BaseCommand):
    """Alarm control command."""

    async def execute(self, action: str, **kwargs) -> bool:
        """Execute alarm command."""
        print_command_header("ALARM", "Alarm control")

        if action == "status":
            return await self._show_status(**kwargs)
        elif action == "arm":
            return await self._arm(**kwargs)
        elif action == "disarm":
            return await self._disarm(**kwargs)
        else:
            print_error(f"Unknown alarm action: {action}")
            return False

    async def _show_status(
        self, installation_id: Optional[str] = None, interactive: bool = True
    ) -> bool:
        """Show alarm status."""
        print_header("ALARM STATUS")

        try:
            if not await self.setup():
                return False

            # Get installation ID
            selected_installation_id = await self.select_installation_if_needed(
                installation_id
            )
            if not selected_installation_id:
                return False

            print_info(
                f"Getting alarm status for installation: {selected_installation_id}"
            )

            alarm_status = await self.alarm_use_case.get_alarm_status(
                selected_installation_id
            )
            print_alarm_status(alarm_status)

            return True

        except Exception as e:
            print_error(f"Error getting alarm status: {e}")
            return False

    async def _arm(
        self,
        mode: str,
        installation_id: Optional[str] = None,
        confirm: bool = True,
        interactive: bool = True,
    ) -> ArmResult:
        """Arm the alarm."""
        print_header(f"ARM ALARM - MODE {mode.upper()}")

        try:
            if not await self.setup():
                return False

            # Get installation ID
            installation_id = await self.select_installation_if_needed(
                installation_id
            )
            if not installation_id:
                return False

            # Validate mode
            valid_modes = ["away", "home", "night"]
            if mode.lower() not in valid_modes:
                print_error(
                    f"Invalid mode: {mode}. Valid modes: {', '.join(valid_modes)}"
                )
                return False

            # Confirm action if requested
            if confirm:
                if not confirm_action(f"arm the alarm in mode {mode}"):
                    print_info("Action cancelled")
                    return False

            print_info(
                f"Arming alarm in mode {mode} for installation: {installation_id}"
            )

            # Arm the alarm
            if mode.lower() == "away":
                result = await self.alarm_use_case.arm_away(installation_id)
            elif mode.lower() == "home":
                result = await self.alarm_use_case.arm_home(installation_id)
            elif mode.lower() == "night":
                result = await self.alarm_use_case.arm_night(installation_id)
            else:
                print_error(f"Mode not supported: {mode}")
                return ArmResult(success=False, message=f"Mode not supported: {mode}")

            if result.success:
                print_success(f"Alarm armed successfully in mode {mode}")
                return result
            else:
                print_error(f"Error arming the alarm in mode {mode}")
                return ArmResult(success=False, message=f"Error arming the alarm in mode {mode}")

        except Exception as e:
            print_error(f"Error arming the alarm: {e}")
            return ArmResult(success=False, message=f"Error arming the alarm: {e}")

    async def _disarm(
        self, installation_id: Optional[str] = None, confirm: bool = True, interactive: bool = True
    ) -> DisarmResult:
        """Disarm the alarm."""
        print_header("DISARM ALARM")

        try:
            if not await self.setup():
                return DisarmResult(success=False, message="Error setting up the alarm")

            # Get installation ID
            installation_id = await self.select_installation_if_needed(
                installation_id
            )
            if not installation_id:
                return DisarmResult(success=False, message="Error selecting the installation for disarming the alarm")

            # Confirm action if requested and interactive
            if confirm and interactive:
                if not confirm_action("disarm the alarm"):
                    return DisarmResult(success=False, message="Action cancelled")

            print_info(
                f"Disarming alarm for installation: {installation_id}"
            )

            # Disarm the alarm
            result = await self.alarm_use_case.disarm(installation_id)

            if result.success:
                print_success("Alarm disarmed successfully")
                return result
            else:
                print_error("Error disarming the alarm")
                return result

        except Exception as e:
            print_error(f"Error disarming the alarm: {e}")
            return DisarmResult(success=False, message=f"Error disarming the alarm: {e}")
