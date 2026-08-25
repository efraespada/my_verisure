"""Authentication command for the CLI."""

import asyncio
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
from custom_components.my_verisure.core.api.exceptions import MyVerisureOTPError
from custom_components.my_verisure.core.application.otp_code_policy import is_valid_otp_code
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
            if not await self.setup(interactive):
                return False

            session_manager = self.session_manager
            username = session_manager.username
            password = session_manager.password
            if username is None or password is None:
                print_error("Usuario y contraseña son necesarios para iniciar sesión")
                return False
            try:
                # Perform login through the command composition root
                auth_use_case = self.auth_use_case
                auth_result = await auth_use_case.login(username, password)
                
                if auth_result.success:
                    print_success("Inicio de sesión exitoso")
                    return True
                else:
                    print_error("Inicio de sesión fallido")
                    return False
                    
            except MyVerisureOTPError:
                # Handle OTP authentication flow
                print_info("🔐 Autenticación MFA requerida")
                return await self._handle_otp_flow()
            except Exception:
                raise

        except Exception:
            print_error("Error durante el inicio de sesión")
            return False

    async def _logout(self) -> bool:
        """Perform logout."""
        print_header("CIERRE DE SESIÓN")

        try:
            session_manager = self.session_manager
            await session_manager.logout()
            print_success("Sesión cerrada correctamente")
            return True

        except Exception:
            print_error("Error durante el cierre de sesión")
            return False

    async def _status(self) -> bool:
        """Show authentication status."""
        print_header("ESTADO DE AUTENTICACIÓN")

        session_manager = self.session_manager
        
        # Show user information
        if session_manager.username:
            print_info("👤 Usuario: [REDACTED]")
        else:
            print_info("👤 Usuario: No configurado")

        # Try to ensure authentication (this will attempt automatic reauthentication if needed)
        try:
            await session_manager.ensure_authenticated(interactive=False)
        except Exception:
            print_warning("⚠️  Error durante verificación de autenticación")
        # Show authentication status
        if session_manager.is_authenticated:
            print_success("✅ Autenticado")
            if session_manager.current_installation:
                print_info("🏠 Instalación seleccionada: [REDACTED]")
            else:
                print_info("🏠 No hay instalación seleccionada")
        else:
            print_warning("⚠️  No autenticado")
            if session_manager.username:
                print_info("💡 Ejecuta 'auth login' para reautenticarte")
            else:
                print_info("💡 Ejecuta 'auth login' para autenticarte")

        return True

    async def _handle_otp_flow(self) -> bool:
        """Handle OTP authentication flow."""
        print_header("AUTENTICACIÓN MFA")
        
        try:
            try:
                auth_use_case = self.auth_use_case
                
                # Get available phone numbers
                phones = auth_use_case.get_available_phones()
                if not phones:
                    print_error("No hay números de teléfono disponibles para OTP")
                    return False
                
                # Show available phone numbers
                print_info("📱 Números de teléfono disponibles:")
                for i, phone in enumerate(phones):
                    print_info(f"  {i}: [REDACTED]")
                
                # Let user select phone
                try:
                    phone_index = int(await asyncio.to_thread(
                        input,
                        "Selecciona el número de teléfono (0-{}): ".format(len(phones)-1),
                    ))
                    if phone_index < 0 or phone_index >= len(phones):
                        print_error("Índice de teléfono inválido")
                        return False
                    
                    selected_phone = phones[phone_index]
                    if not auth_use_case.select_phone(int(selected_phone.get("id", -1))):
                        print_error("Teléfono OTP no disponible")
                        return False
                    print_info("📞 Teléfono seleccionado: [REDACTED]")
                    
                    # Send OTP
                    print_info("📤 Enviando código OTP...")
                    otp_sent = await auth_use_case.send_otp(selected_phone['record_id'])
                    
                    if otp_sent:
                        print_success("✅ Código OTP enviado")
                        
                        # Get OTP code from user
                        otp_code = (await asyncio.to_thread(
                            input,
                            "🔐 Introduce el código OTP recibido: ",
                        )).strip()
                        
                        if not is_valid_otp_code(otp_code):
                            auth_use_case.invalidate_otp_challenge()
                            print_error("Código OTP inválido")
                            return False
                        
                        # Verify OTP
                        print_info("🔍 Verificando código OTP...")
                        auth_result = await auth_use_case.verify_otp(otp_code)
                        
                        if auth_result.success:
                            print_success("✅ Autenticación MFA exitosa")
                            return True
                        else:
                            print_error("❌ Verificación OTP fallida")
                            return False
                    else:
                        print_error("❌ Error enviando código OTP")
                        return False
                        
                except ValueError:
                    print_error("❌ Por favor introduce un número válido")
                    return False
                except KeyboardInterrupt:
                    print_info("\n⏹️  Proceso cancelado por el usuario")
                    return False
                    
            except Exception:
                print_error("Error durante autenticación MFA")
                return False
            finally:
                self.auth_use_case.invalidate_otp_challenge()
                
        except Exception:
            print_error("Error durante autenticación MFA")
            return False
