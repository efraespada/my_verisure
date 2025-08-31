"""Authentication command for the CLI."""

import logging

from .base import BaseCommand
from ..utils.display import (
    print_command_header,
    print_success,
    print_error,
    print_info,
    print_warning,
    print_header,
)
from ..utils.session_manager import session_manager

logger = logging.getLogger(__name__)


class AuthCommand(BaseCommand):
    """Authentication command."""

    async def execute(self, action: str, **kwargs) -> bool:
        """Execute authentication command."""
        print_command_header("AUTH", "Gestión de autenticación")

        if action == "login":
            return await self._login(**kwargs)
        elif action == "logout":
            return await self._logout()
        elif action == "status":
            return await self._status()
        else:
            print_error(f"Acción de autenticación desconocida: {action}")
            return False

    async def _login(self, interactive: bool = True) -> bool:
        """Perform login."""
        print_header("INICIO DE SESIÓN")

        try:
            # Setup will handle the login process
            success = await self.setup(interactive)

            if success:
                print_success("Inicio de sesión exitoso")
                return True
            else:
                print_error("Inicio de sesión fallido")
                return False

        except Exception as e:
            print_error(f"Error durante el inicio de sesión: {e}")
            return False

    async def _logout(self) -> bool:
        """Perform logout."""
        print_header("CIERRE DE SESIÓN")

        try:
            await session_manager.logout()
            print_success("Sesión cerrada correctamente")
            return True

        except Exception as e:
            print_error(f"Error durante el cierre de sesión: {e}")
            return False

    async def _status(self) -> bool:
        """Show authentication status."""
        print_header("ESTADO DE AUTENTICACIÓN")

        if session_manager.username:
            print_info(f"👤 Usuario: {session_manager.username}")
        else:
            print_info("👤 Usuario: No configurado")

        # Try to authenticate with saved credentials
        if session_manager.username and not session_manager.is_authenticated:
            print_info(
                "🔄 Intentando autenticación con credenciales guardadas..."
            )
            try:
                success = await session_manager.ensure_authenticated(
                    interactive=False
                )
                if success:
                    print_success("✅ Autenticado automáticamente")
                else:
                    print_warning("⚠️  No se pudo autenticar automáticamente")
            except Exception as e:
                print_warning(f"⚠️  Error en autenticación automática: {e}")

        if session_manager.is_authenticated:
            print_success("✅ Autenticado")
            if session_manager.current_installation:
                print_info(
                    f"🏠 Instalación actual: {session_manager.current_installation}"
                )
            else:
                print_info("🏠 No hay instalación seleccionada")
        else:
            print_warning("⚠️  No autenticado")
            if session_manager.username:
                print_info("Ejecuta 'auth login' para reautenticarte")
            else:
                print_info("Ejecuta 'auth login' para autenticarte")

        return True
