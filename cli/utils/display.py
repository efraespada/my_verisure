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
    print(f"{prefix}🏠 Instalación: {installation.alias}")
    print(f"   🆔 Número: {installation.numinst}")
    print(f"   🏠 Tipo: {installation.type}")
    print(f"   👤 Propietario: {installation.name} {installation.surname}")
    print(f"   📍 Dirección: {installation.address}")
    print(f"   🏙️  Ciudad: {installation.city} ({installation.postcode})")
    print(f"   📞 Teléfono: {installation.phone}")
    print(f"   📧 Email: {installation.email}")
    print(f"   🎭 Rol: {installation.role}")
    print()


def print_alarm_status(status) -> None:
    """Imprime el estado de la alarma."""
    print_header("ESTADO DE LA ALARMA")
    print(f"🛡️  Estado: {status.status or 'N/A'}")
    print(f"📋 Mensaje: {status.message}")
    print(f"🏠 Instalación: {status.numinst or 'N/A'}")
    print(f"🔧 Respuesta Protom: {status.protom_response or 'N/A'}")
    if status.protom_response_date:
        print(f"⏰ Fecha Respuesta: {status.protom_response_date}")
    if status.forced_armed is not None:
        print(f"🔒 Forzado: {'Sí' if status.forced_armed else 'No'}")
    print()


def print_services_info(services_data) -> None:
    """Imprime información de servicios de una instalación."""
    if not services_data.success:
        print_error(f"Error obteniendo servicios: {services_data.message}")
        return

    services = services_data.services
    print_success(f"Se encontraron {len(services)} servicios")

    # Mostrar información básica de la instalación
    installation_info = services_data.installation_data or {}
    print(f"   📊 Estado: {installation_info.get('status', 'N/A')}")
    print(f"   🛡️  Panel: {installation_info.get('panel', 'N/A')}")
    print(f"   📱 SIM: {installation_info.get('sim', 'N/A')}")
    print(f"   🎭 Rol: {installation_info.get('role', 'N/A')}")
    print(f"   🔧 IBS: {installation_info.get('instIbs', 'N/A')}")
    print()

    # Mostrar servicios activos
    active_services = [s for s in services if s.active]
    print(f"   ✅ Servicios activos ({len(active_services)}):")
    for service in active_services:
        service_id = service.id_service
        service_request = service.request or "N/A"
        service_visible = "👁️" if service.visible else "🙈"
        service_premium = "⭐" if service.is_premium else ""
        service_bde = "💰" if service.bde else ""
        print(
            f"      {service_visible} {service_id}: {service_request} {service_premium}{service_bde}"
        )

    # Mostrar servicios inactivos (solo si hay pocos)
    inactive_services = [s for s in services if not s.active]
    if inactive_services and len(inactive_services) <= 5:
        print(f"   ❌ Servicios inactivos ({len(inactive_services)}):")
        for service in inactive_services:
            service_id = service.id_service
            service_request = service.request or "N/A"
            print(f"      ❌ {service_id}: {service_request}")

    # Capacidades
    capabilities = services_data.capabilities
    if capabilities:
        print(
            f"   🔐 Capacidades: {capabilities[:30] + '...' if capabilities else 'None'}"
        )


def print_separator() -> None:
    """Imprime un separador."""
    print("\n" + "-" * 60)
    print()
