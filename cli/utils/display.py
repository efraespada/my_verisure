"""Display utilities for the CLI."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def print_header(title: str) -> None:
    """Imprime un encabezado formateado."""
    print("\n" + "=" * 60)
    print(f"🚀 {title}")
    print("=" * 60)


def print_success(message: str) -> None:
    """Imprime un mensaje de éxito."""
    print(f"✅ {message}")


def print_error(message: str) -> None:
    """Imprime un mensaje de error."""
    print(f"❌ {message}")


def print_info(message: str) -> None:
    """Imprime un mensaje informativo."""
    print(f"ℹ️  {message}")


def print_warning(message: str) -> None:
    """Imprime un mensaje de advertencia."""
    print(f"⚠️  {message}")


def print_command_header(command: str, description: str) -> None:
    """Imprime el encabezado de un comando."""
    print_header(f"MY VERISURE CLI - {command.upper()}")
    print_info(description)
    print()


def print_installation_info(installation, index: Optional[int] = None) -> None:
    """Imprime información de una instalación."""
    prefix = f"{index}. " if index is not None else ""
    print(f"{prefix}🏠 Instalación: Instalación {index or 1}")
    print("   🆔 Número: [REDACTED]")
    print(f"   🏠 Tipo: {installation.type}")
    print("   👤 Propietario: [REDACTED]")
    print("   📍 Dirección: [REDACTED]")
    print("   🏙️  Ciudad: [REDACTED]")
    print("   📞 Teléfono: [REDACTED]")
    print("   📧 Email: [REDACTED]")
    print(f"   🎭 Rol: {installation.role}")
    print()


def print_alarm_status(status) -> None:
    """Imprime el estado de la alarma."""
    print_header("ESTADO DE LA ALARMA")
    print(f"🛡️  Estado: {status.status or 'N/A'}")
    print("📋 Mensaje: Estado de alarma recibido")
    print("🏠 Instalación: [REDACTED]")
    print("🔧 Respuesta Protom: Respuesta recibida")
    if status.protom_response_date:
        print(f"⏰ Fecha Respuesta: {status.protom_response_date}")
    if status.forced_armed is not None:
        print(f"🔒 Forzado: {'Sí' if status.forced_armed else 'No'}")
    print()


def print_services_info(services_data) -> None:
    """Imprime información de servicios de una instalación."""
    if not getattr(services_data, "success", True):
        print_error("Error obteniendo servicios")
        return

    installation = getattr(services_data, "installation", None)
    if installation is None:
        services = getattr(services_data, "services", None) or []
        raw_installation = getattr(services_data, "installation_data", {}) or {}
        if isinstance(raw_installation, dict):
            from types import SimpleNamespace

            installation = SimpleNamespace(
                services=services,
                capabilities=getattr(services_data, "capabilities", None),
                **raw_installation,
            )

    if installation is None:
        print_error("Error obteniendo servicios")
        return

    services = getattr(installation, "services", None) or []
    if not services:
        print_error("No se encontraron servicios para esta instalación")
        return

    print_success(f"Se encontraron {len(services)} servicios")

    # Mostrar información básica de la instalación
    installation_info = installation
    print(f"   📊 Estado: {installation_info.status}")
    print(f"   🎭 Rol: {installation_info.role}")
    print()

    # Mostrar servicios activos
    # Los servicios pueden ser diccionarios o objetos Service
    def get_service_active(service):
        if isinstance(service, dict):
            return service.get('active', False)
        return service.active
    
    def get_service_visible(service):
        if isinstance(service, dict):
            return service.get('visible', False)
        return service.visible
    
    def get_service_premium(service):
        if isinstance(service, dict):
            return service.get('isPremium', False)
        return service.is_premium
    
    def get_service_bde(service):
        if isinstance(service, dict):
            return service.get('bde', False)
        return service.bde

    active_services = [s for s in services if get_service_active(s)]
    print(f"   ✅ Servicios activos ({len(active_services)}):")
    for service in active_services:
        service_visible = "👁️" if get_service_visible(service) else "🙈"
        service_premium = "⭐" if get_service_premium(service) else ""
        service_bde = "💰" if get_service_bde(service) else ""
        print(f"      {service_visible} Servicio activo {service_premium}{service_bde}")

    inactive_services = [s for s in services if not get_service_active(s)]
    if inactive_services and len(inactive_services) <= 5:
        print(f"   ❌ Servicios inactivos ({len(inactive_services)}):")
        for _service in inactive_services:
            print("      ❌ Servicio inactivo")

    # Capabilities are provider secrets and are intentionally not displayed.


def print_separator() -> None:
    """Imprime un separador."""
    print("\n" + "-" * 60)
    print()
