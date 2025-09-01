"""Alarm control command for the CLI."""

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

logger = logging.getLogger(__name__)


class AlarmCommand(BaseCommand):
    """Alarm control command."""

    async def execute(self, action: str, **kwargs) -> bool:
        """Execute alarm command."""
        print_command_header("ALARM", "Control de alarmas")

        if action == "status":
            return await self._show_status(**kwargs)
        elif action == "arm":
            return await self._arm(**kwargs)
        elif action == "disarm":
            return await self._disarm(**kwargs)
        else:
            print_error(f"Acción de alarma desconocida: {action}")
            return False

    async def _show_status(
        self, installation_id: Optional[str] = None, interactive: bool = True
    ) -> bool:
        """Show alarm status."""
        print_header("ESTADO DE ALARMA")

        try:
            if not await self.setup():
                return False

            # Get installation ID
            installation_id = await self.select_installation_if_needed(
                installation_id
            )
            if not installation_id:
                return False

            print_info(
                f"Obteniendo estado de alarma para instalación: {installation_id}"
            )

            alarm_status = await self.alarm_use_case.get_alarm_status(
                installation_id
            )
            print_alarm_status(alarm_status)

            return True

        except Exception as e:
            print_error(f"Error obteniendo estado de alarma: {e}")
            return False

    async def _arm(
        self,
        mode: str,
        installation_id: Optional[str] = None,
        confirm: bool = True,
        interactive: bool = True,
    ) -> bool:
        """Arm the alarm."""
        print_header(f"ARMAR ALARMA - MODO {mode.upper()}")

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
                    f"Modo inválido: {mode}. Modos válidos: {', '.join(valid_modes)}"
                )
                return False

            # Confirm action if requested
            if confirm:
                if not confirm_action(f"armar la alarma en modo {mode}"):
                    print_info("Acción cancelada")
                    return False

            print_info(
                f"Armando alarma en modo {mode} para instalación: {installation_id}"
            )

            # Arm the alarm
            if mode.lower() == "away":
                success = await self.alarm_use_case.arm_away(installation_id)
            elif mode.lower() == "home":
                success = await self.alarm_use_case.arm_home(installation_id)
            elif mode.lower() == "night":
                success = await self.alarm_use_case.arm_night(installation_id)
            else:
                print_error(f"Modo no soportado: {mode}")
                return False

            if success:
                print_success(f"Alarma armada correctamente en modo {mode}")
                return True
            else:
                print_error(f"Error armando la alarma en modo {mode}")
                return False

        except Exception as e:
            print_error(f"Error armando la alarma: {e}")
            return False

    async def _disarm(
        self, installation_id: Optional[str] = None, confirm: bool = True, interactive: bool = True
    ) -> bool:
        """Disarm the alarm."""
        print_header("DESARMAR ALARMA")

        try:
            if not await self.setup():
                return False

            # Get installation ID
            installation_id = await self.select_installation_if_needed(
                installation_id
            )
            if not installation_id:
                return False

            # Confirm action if requested
            if confirm:
                if not confirm_action("desarmar la alarma"):
                    print_info("Acción cancelada")
                    return False

            print_info(
                f"Desarmando alarma para instalación: {installation_id}"
            )

            # Disarm the alarm
            success = await self.alarm_use_case.disarm(installation_id)

            if success:
                print_success("Alarma desarmada correctamente")
                return True
            else:
                print_error("Error desarmando la alarma")
                return False

        except Exception as e:
            print_error(f"Error desarmando la alarma: {e}")
            return False
