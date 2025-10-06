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
from core.session_manager import get_session_manager
from core.api.exceptions import MyVerisureOTPError
from core.dependency_injection.providers import (
    setup_dependencies,
    get_auth_use_case,
    clear_dependencies,
)
            
            
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
            # Get session manager
            session_manager = get_session_manager()
            
            # Ensure we have credentials
            if not await session_manager.ensure_authenticated(interactive):
                print_error("No se pudieron obtener las credenciales")
                return False
            
            # Setup dependencies
            setup_dependencies()
            
            try:
                # Get auth use case and perform login
                auth_use_case = get_auth_use_case()
                auth_result = await auth_use_case.login(
                    session_manager.username, 
                    session_manager.password
                )
                
                if auth_result.success:
                    # Update session manager with new credentials
                    session_manager.update_credentials(
                        session_manager.username,
                        session_manager.password,
                        auth_result.hash,
                        auth_result.refresh_token
                    )
                    print_success("Inicio de sesión exitoso")
                    return True
                else:
                    print_error(f"Inicio de sesión fallido: {auth_result.message}")
                    return False
                    
            except MyVerisureOTPError:
                # Handle OTP authentication flow
                print_info("🔐 Autenticación MFA requerida")
                return await self._handle_otp_flow()
            except Exception:
                # Clean up dependencies on other errors
                clear_dependencies()
                raise

        except Exception as e:
            print_error(f"Error durante el inicio de sesión: {e}")
            return False

    async def _logout(self) -> bool:
        """Perform logout."""
        print_header("CIERRE DE SESIÓN")

        try:
            session_manager = get_session_manager()
            await session_manager.logout()
            print_success("Sesión cerrada correctamente")
            return True

        except Exception as e:
            print_error(f"Error durante el cierre de sesión: {e}")
            return False

    async def _status(self) -> bool:
        """Show authentication status."""
        print_header("ESTADO DE AUTENTICACIÓN")

        session_manager = get_session_manager()
        
        # Show user information
        if session_manager.username:
            print_info(f"👤 Usuario: {session_manager.username}")
        else:
            print_info("👤 Usuario: No configurado")

        # Show authentication status
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
                print_info("💡 Ejecuta 'auth login' para reautenticarte")
            else:
                print_info("💡 Ejecuta 'auth login' para autenticarte")

        return True

    async def _handle_otp_flow(self) -> bool:
        """Handle OTP authentication flow."""
        print_header("AUTENTICACIÓN MFA")
        
        try:
            try:
                # Get auth use case to access the client
                auth_use_case = get_auth_use_case()
                
                # Get available phone numbers
                phones = auth_use_case.get_available_phones()
                if not phones:
                    print_error("No hay números de teléfono disponibles para OTP")
                    return False
                
                # Show available phone numbers
                print_info("📱 Números de teléfono disponibles:")
                for i, phone in enumerate(phones):
                    print_info(f"  {i}: {phone['phone']}")
                
                # Let user select phone
                try:
                    phone_index = int(input("Selecciona el número de teléfono (0-{}): ".format(len(phones)-1)))
                    if phone_index < 0 or phone_index >= len(phones):
                        print_error("Índice de teléfono inválido")
                        return False
                    
                    selected_phone = phones[phone_index]
                    print_info(f"📞 Teléfono seleccionado: {selected_phone['phone']}")
                    
                    # Send OTP
                    print_info("📤 Enviando código OTP...")
                    otp_sent = await auth_use_case.send_otp(selected_phone['record_id'], selected_phone['otp_hash'])
                    
                    if otp_sent:
                        print_success("✅ Código OTP enviado")
                        
                        # Get OTP code from user
                        otp_code = input("🔐 Introduce el código OTP recibido: ").strip()
                        
                        if not otp_code:
                            print_error("Código OTP requerido")
                            return False
                        
                        # Verify OTP
                        print_info("🔍 Verificando código OTP...")
                        auth_result = await auth_use_case.verify_otp(otp_code)
                        
                        if auth_result.success:
                            # Update session manager with new credentials
                            session_manager = get_session_manager()
                            session_manager.update_credentials(
                                session_manager.username,
                                session_manager.password,
                                auth_result.hash,
                                auth_result.refresh_token
                            )
                            print_success("✅ Autenticación MFA exitosa")
                            return True
                        else:
                            print_error(f"❌ Verificación OTP fallida: {auth_result.message}")
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
                    
            except Exception as e:
                print_error(f"Error durante autenticación MFA: {e}")
                clear_dependencies()
                return False
            finally:
                # Only clear dependencies if there was an error
                pass
                
        except Exception as e:
            print_error(f"Error durante autenticación MFA: {e}")
            clear_dependencies()
            return False
