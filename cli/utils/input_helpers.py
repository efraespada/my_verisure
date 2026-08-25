"""Input helpers for the CLI."""

import getpass
import logging
from typing import Optional, List, Dict

from custom_components.my_verisure.core.application.otp_code_policy import (
    is_valid_otp_code,
)

logger = logging.getLogger(__name__)


def get_user_credentials() -> tuple[str, str]:
    """Solicita las credenciales del usuario."""
    from .display import print_header, print_error

    print_header("MY VERISURE - AUTENTICACIÓN INTERACTIVA")

    print("👤 Ingresa tus credenciales de My Verisure:")
    print()

    # Solicitar User ID (DNI/NIE)
    while True:
        user_id = input("📋 User ID (DNI/NIE): ").strip()
        if user_id:
            break
        print_error("El User ID es obligatorio")

    # Solicitar contraseña
    while True:
        password = getpass.getpass("🔑 Contraseña: ").strip()
        if password:
            break
        print_error("La contraseña es obligatoria")

    return user_id, password


def select_phone(phones: List[Dict]) -> Optional[int]:
    """Permite al usuario seleccionar un teléfono."""
    from .display import print_header, print_error, print_success

    print_header("SELECCIÓN DE TELÉFONO")

    print("📱 Teléfonos disponibles para recibir el código OTP:")
    print()

    for i, _phone in enumerate(phones):
        print(f"  {i+1}. ID [REDACTED]: [REDACTED]")

    print()

    while True:
        try:
            choice = input(
                "Selecciona el número de teléfono (1, 2, ...): "
            ).strip()
            choice_num = int(choice)

            if 1 <= choice_num <= len(phones):
                selected_phone = phones[choice_num - 1]
                phone_id = selected_phone.get("id")

                print_success("Teléfono seleccionado: [REDACTED]")
                return phone_id
            else:
                print_error(
                    f"Por favor selecciona un número entre 1 y {len(phones)}"
                )

        except ValueError:
            print_error("Por favor ingresa un número válido")
        except KeyboardInterrupt:
            print("\n⏹️  Selección cancelada")
            return None


def get_otp_code() -> Optional[str]:
    """Solicita el código OTP al usuario."""
    from .display import print_header, print_error, print_success

    print_header("VERIFICACIÓN OTP")

    print("📱 Revisa tu teléfono para el código OTP que acabas de recibir.")
    print("💡 El código suele ser de 6 dígitos.")
    print()

    while True:
        try:
            otp_code = input("🔢 Código OTP: ").strip()
            if otp_code:
                if is_valid_otp_code(otp_code):
                    print_success("Código OTP ingresado: [REDACTED]")
                    return otp_code
                print_error("El código OTP debe contener exactamente seis dígitos ASCII")
            else:
                print_error("El código OTP es obligatorio")

        except KeyboardInterrupt:
            print("\n⏹️  Entrada cancelada")
            return None


def select_installation(installations: List) -> Optional[str]:
    """Permite al usuario seleccionar una instalación."""
    from .display import (
        print_header,
        print_error,
        print_success,
        print_installation_info,
    )

    if not installations:
        print_error("No hay instalaciones disponibles")
        return None

    if len(installations) == 1:
        installation = installations[0]
        print_success("Usando única instalación disponible")
        return installation.numinst

    print_header("SELECCIÓN DE INSTALACIÓN")

    print("🏠 Instalaciones disponibles:")
    print()

    for i, installation in enumerate(installations):
        print_installation_info(installation, i + 1)

    while True:
        try:
            choice = input(
                f"Selecciona el número de instalación (1-{len(installations)}): "
            ).strip()
            choice_num = int(choice)

            if 1 <= choice_num <= len(installations):
                selected_installation = installations[choice_num - 1]
                print_success("Instalación seleccionada")
                return selected_installation.numinst
            else:
                print_error(
                    f"Por favor selecciona un número entre 1 y {len(installations)}"
                )

        except ValueError:
            print_error("Por favor ingresa un número válido")
        except KeyboardInterrupt:
            print("\n⏹️  Selección cancelada")
            return None


def confirm_action(action: str) -> bool:
    """Solicita confirmación para una acción."""
    from .display import print_warning, print_error

    print_warning(f"¿Estás seguro de que quieres {action}?")

    while True:
        try:
            response = input("Responde 'sí' o 'no' (s/n): ").strip().lower()
            if response in ["sí", "si", "s", "yes", "y"]:
                return True
            elif response in ["no", "n"]:
                return False
            else:
                print_error("Por favor responde 'sí' o 'no'")
        except KeyboardInterrupt:
            print("\n⏹️  Acción cancelada")
            return False
