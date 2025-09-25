"""Information command for the CLI."""

import logging
from typing import Optional

from .base import BaseCommand
from ..utils.display import (
    print_command_header,
    print_success,
    print_error,
    print_info,
    print_header,
    print_installation_info,
    print_services_info,
    print_separator,
    print_alarm_status,
)

logger = logging.getLogger(__name__)


class InfoCommand(BaseCommand):
    """Information command."""

    async def execute(self, action: str, **kwargs) -> bool:
        """Execute information command."""
        print_command_header("INFO", "Información del sistema")

        if action == "installations":
            return await self._show_installations(**kwargs)
        elif action == "services":
            return await self._show_services(**kwargs)
        elif action == "status":
            return await self._show_status(**kwargs)
        else:
            print_error(f"Acción de información desconocida: {action}")
            return False

    async def _show_installations(self, interactive: bool = True) -> bool:
        """Show all installations."""
        print_header("INSTALACIONES")

        try:
            if not await self.setup():
                return False

            installations = (
                await self.installation_use_case.get_installations()
            )

            if installations:
                print_success(
                    f"Se encontraron {len(installations)} instalación(es)"
                )
                print()

                for i, installation in enumerate(installations):
                    print_installation_info(installation, i + 1)
                    if i < len(installations) - 1:
                        print_separator()
            else:
                print_info("No se encontraron instalaciones")

            return True

        except Exception as e:
            print_error(f"Error obteniendo instalaciones: {e}")
            return False

    async def _show_services(
        self, installation_id: Optional[str] = None, interactive: bool = True
    ) -> bool:
        """Show services for an installation."""
        print_header("SERVICIOS DE INSTALACIÓN")

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
                f"Obteniendo servicios para instalación: {installation_id}"
            )

            services_data = await self.installation_use_case.get_installation_services(
                installation_id
            )

            if services_data.services and len(services_data.services) > 0:
                print_services_info(services_data)
                return True
            else:
                print_error(
                    f"Error obteniendo servicios: {services_data.message}"
                )
                return False

        except Exception as e:
            print_error(f"Error obteniendo servicios: {e}")
            return False

    async def _show_status(
        self, installation_id: Optional[str] = None, interactive: bool = True
    ) -> bool:
        """Show status for an installation."""
        print_header("ESTADO DE INSTALACIÓN")

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
                f"Obteniendo estado para instalación: {installation_id}"
            )

            # Get alarm status
            alarm_status = await self.alarm_use_case.get_alarm_status(
                installation_id
            )
            print_success("Estado de alarma obtenido")
            print_alarm_status(alarm_status)

            return True

        except Exception as e:
            print_error(f"Error obteniendo estado: {e}")
            return False
