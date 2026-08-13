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
    if not getattr(services_data, "success", True):
        print_error(
            f"Error obteniendo servicios: "
            f"{getattr(services_data, 'message', 'Unknown error')}"
        )
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
        print_error(
            f"Error obteniendo servicios: "
            f"{getattr(services_data, 'message', 'No se encontraron servicios')}"
        )
        return

    services = getattr(installation, "services", None) or []
    if not services:
        print_error("No se encontraron servicios para esta instalación")
        return

    print_success(f"Se encontraron {len(services)} servicios")

    # Mostrar información básica de la instalación
    installation_info = installation
    print(f"   📊 Estado: {installation_info.status}")
    print(f"   🛡️  Panel: {installation_info.panel}")
    print(f"   📱 SIM: {installation_info.sim}")
    print(f"   🎭 Rol: {installation_info.role}")
    print(f"   🔧 IBS: {installation_info.instIbs}")
    print()

    # Mostrar servicios activos
    # Los servicios pueden ser diccionarios o objetos Service
    def get_service_active(service):
        if isinstance(service, dict):
            return service.get('active', False)
        return service.active
    
    def get_service_id(service):
        if isinstance(service, dict):
            return service.get('idService', service.get('id_service', 'N/A'))
        return service.id_service
    
    def get_service_request(service):
        if isinstance(service, dict):
            return service.get('request', 'N/A')
        return service.request or "N/A"
    
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
        service_id = get_service_id(service)
        service_request = get_service_request(service)
        service_visible = "👁️" if get_service_visible(service) else "🙈"
        service_premium = "⭐" if get_service_premium(service) else ""
        service_bde = "💰" if get_service_bde(service) else ""
        print(
            f"      {service_visible} {service_id}: {service_request} {service_premium}{service_bde}"
        )

    # Mostrar servicios inactivos (solo si hay pocos)
    inactive_services = [s for s in services if not get_service_active(s)]
    if inactive_services and len(inactive_services) <= 5:
        print(f"   ❌ Servicios inactivos ({len(inactive_services)}):")
        for service in inactive_services:
            service_id = get_service_id(service)
            service_request = get_service_request(service)
            print(f"      ❌ {service_id}: {service_request}")

    # Capacidades
    capabilities = getattr(installation_info, "capabilities", None)
    if capabilities:
        print(
            f"   🔐 Capacidades: {capabilities[:30] + '...' if capabilities else 'None'}"
        )


def print_separator() -> None:
    """Imprime un separador."""
    print("\n" + "-" * 60)
    print()
