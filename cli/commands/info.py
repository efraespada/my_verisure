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
        elif action == "devices":
            return await self._show_devices(**kwargs)
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

            if services_data.installation.services and len(services_data.installation.services) > 0:
                print_services_info(services_data)
                return True
            else:
                print_error("No se encontraron servicios para esta instalación")
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

    async def _show_devices(self, installation_id: Optional[str] = None, interactive: bool = True) -> bool:
        """Show devices for an installation."""
        print_header("DISPOSITIVOS")

        try:
            if not await self.setup():
                return False

            # Get installation ID
            if not installation_id:
                installations = await self.installation_use_case.get_installations()
                if not installations:
                    print_error("No se encontraron instalaciones")
                    return False
                
                if len(installations) == 1:
                    installation_id = installations[0].numinst
                    print_info(f"Usando instalación: {installations[0].alias or installation_id}")
                else:
                    print_info("Múltiples instalaciones encontradas:")
                    for i, installation in enumerate(installations):
                        print(f"  {i + 1}. {installation.alias or installation.numinst} ({installation.numinst})")
                    
                    if interactive:
                        try:
                            choice = int(input("\nSelecciona una instalación (número): ")) - 1
                            if 0 <= choice < len(installations):
                                installation_id = installations[choice].numinst
                                print_info(f"Seleccionada: {installations[choice].alias or installation_id}")
                            else:
                                print_error("Selección inválida")
                                return False
                        except (ValueError, KeyboardInterrupt):
                            print_error("Operación cancelada")
                            return False
                    else:
                        print_error("Se requiere --installation-id cuando hay múltiples instalaciones")
                        return False

            # Get installation services to get panel info
            services = await self.installation_use_case.get_installation_services(installation_id)
            panel = services.installation.panel or "SDVFAST"
            
            print_info(f"Obteniendo dispositivos para instalación {installation_id} con panel {panel}...")
            
            # Get devices
            devices = await self.get_installation_devices_use_case.get_installation_devices(
                installation_id=installation_id,
                panel=panel,
                force_refresh=True
            )

            if devices.devices:
                print_success(f"Se encontraron {len(devices.devices)} dispositivo(s)")
                print()
                
                # Group devices by type
                devices_by_type = {}
                for device in devices.devices:
                    device_type = device.type
                    if device_type not in devices_by_type:
                        devices_by_type[device_type] = []
                    devices_by_type[device_type].append(device)
                
                # Show devices by type
                for device_type, type_devices in devices_by_type.items():
                    print_header(f"{device_type.upper()} ({len(type_devices)} dispositivos)")
                    
                    for i, device in enumerate(type_devices):
                        print(f"  {i + 1}. {device.display_name}")
                        print(f"     ID: {device.id}")
                        print(f"     Código: {device.code}")
                        print(f"     Subtipo: {device.subtype}")
                        print(f"     Activo: {'Sí' if device.is_active else 'No'}")
                        print(f"     Remoto: {'Sí' if device.remote_use else 'No'}")
                        if device.serial_number:
                            print(f"     Serial: {device.serial_number}")
                        if device.config and device.config.flags:
                            flags = []
                            if device.config.flags.pin_code:
                                flags.append("PIN")
                            if device.config.flags.doorbell_button:
                                flags.append("Timbre")
                            if flags:
                                print(f"     Configuración: {', '.join(flags)}")
                        print()
                    
                    if device_type != list(devices_by_type.keys())[-1]:
                        print_separator()
                
                # Summary
                active_devices = devices.active_devices
                remote_devices = devices.remote_devices
                
                print_info(f"Resumen: {len(devices.devices)} total, {len(active_devices)} activos, {len(remote_devices)} remotos")
                
            else:
                print_info("No se encontraron dispositivos")

            return True

        except Exception as e:
            print_error(f"Error obteniendo dispositivos: {e}")
            return False
