"""Session manager for the CLI."""

import asyncio
import json
import logging
import os
import sys

# Add core to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "core"))

from core.dependency_injection.providers import (
    setup_dependencies,
    get_auth_use_case,
    get_installation_use_case,
    get_auth_client,
    get_session_client,
    get_installation_client,
    get_alarm_client,
    clear_dependencies,
)
from core.api.exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
    MyVerisureError,
    MyVerisureOTPError,
)

from .display import print_header, print_success, print_error, print_info
from .input_helpers import get_user_credentials, select_phone, get_otp_code

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages authentication session for the CLI."""

    def __init__(self):
        self.is_authenticated = False
        self.current_installation = None
        self.auth_use_case = None
        self.installation_use_case = None
        self.session_file = self._get_session_file_path()
        self.username = None
        self.password = None
        self.hash_token = None
        self.refresh_token = None
        self.session_timestamp = None

        # Try to load existing session
        self._load_session()

    def _get_session_file_path(self) -> str:
        """Get the session file path."""
        # Create .my_verisure directory in user's home
        home_dir = os.path.expanduser("~")
        session_dir = os.path.join(home_dir, ".my_verisure")

        # Create directory if it doesn't exist
        if not os.path.exists(session_dir):
            os.makedirs(session_dir, mode=0o700)  # Secure permissions

        return os.path.join(session_dir, "session.json")

    def _load_session(self) -> None:
        """Load session from file."""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, "r") as f:
                    session_data = json.load(f)

                self.username = session_data.get("username")
                self.password = session_data.get("password")
                self.is_authenticated = session_data.get(
                    "is_authenticated", False
                )
                self.current_installation = session_data.get(
                    "current_installation"
                )
                self.hash_token = session_data.get("hash_token")
                self.refresh_token = session_data.get("refresh_token")
                self.session_timestamp = session_data.get("session_timestamp")

                # Check if we have credentials and tokens
                if self.username and self.password and self.hash_token:
                    logger.info("Session loaded from file with tokens")
                    # We'll verify the session is still valid when needed
                elif self.username and self.password:
                    logger.info("Session loaded from file (credentials only)")
                else:
                    logger.info("No valid session found in file")

        except Exception as e:
            logger.warning(f"Could not load session: {e}")
            self._clear_session_file()

    def _save_session(self) -> None:
        """Save session to file."""
        try:
            import time
            session_data = {
                "username": self.username,
                "password": self.password,
                "is_authenticated": self.is_authenticated,
                "current_installation": self.current_installation,
                "hash_token": self.hash_token,
                "refresh_token": self.refresh_token,
                "session_timestamp": self.session_timestamp,
                "timestamp": time.time(),
            }

            with open(self.session_file, "w") as f:
                json.dump(session_data, f, indent=2)

            logger.info("Session saved to file with tokens")

        except Exception as e:
            logger.error(f"Could not save session: {e}")

    def _clear_session_file(self) -> None:
        """Clear session file."""
        try:
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
                logger.info("Session file cleared")
        except Exception as e:
            logger.warning(f"Could not clear session file: {e}")

    def _is_token_valid(self) -> bool:
        """Check if the stored hash token is still valid."""
        if not self.hash_token:
            logger.debug("No hash token available")
            return False

        if not self.session_timestamp:
            logger.debug("No session timestamp available")
            return False

        # Check if token is not too old (6 minutes = 360 seconds)
        import time
        current_time = time.time()
        token_age = current_time - self.session_timestamp

        if token_age > 360:  # 6 minutes
            logger.info(f"Token expired (age: {token_age:.1f} seconds)")
            return False

        logger.info(f"Token appears valid (age: {token_age:.1f} seconds)")
        return True

    def _update_session_tokens(self, auth_result) -> None:
        """Update session tokens from auth result."""
        if auth_result and hasattr(auth_result, 'hash'):
            self.hash_token = auth_result.hash
            self.refresh_token = getattr(auth_result, 'refresh_token', None)
            import time
            self.session_timestamp = time.time()
            logger.info("Session tokens updated")
        else:
            logger.warning("No valid auth result to update tokens")

    async def ensure_authenticated(self, interactive: bool = True) -> bool:
        """Ensure the user is authenticated, performing login if necessary."""
        
        # First, check if we have a valid token
        if self._is_token_valid():
            logger.info("Valid token found, attempting to use existing session")
            try:
                # Setup dependencies with saved credentials and existing tokens
                session_data = {
                    "user": self.username,
                    "lang": "ES",
                    "legals": True,
                    "changePassword": False,
                    "needDeviceAuthorization": None,
                    "login_time": self.session_timestamp,
                }
                setup_dependencies(
                    username=self.username, 
                    password=self.password,
                    hash_token=self.hash_token,
                    session_data=session_data
                )

                # Get use cases
                self.auth_use_case = get_auth_use_case()
                self.installation_use_case = get_installation_use_case()

                # Try to use existing token (we'll test it by making a simple API call)
                try:
                    # Test the token by trying to get installations
                    installations = await self.installation_use_case.get_installations()
                    if installations:
                        self.is_authenticated = True
                        logger.info("Existing token is valid, session restored")
                        return True
                    else:
                        logger.warning("Token validation failed - no installations returned")
                        # Fall through to login
                except Exception as e:
                    logger.warning(f"Token validation failed: {e}")
                    # Fall through to login

            except Exception as e:
                logger.warning(f"Error setting up dependencies for token validation: {e}")
                clear_dependencies()

        # If we have credentials but no valid token, try to login
        if self.username and self.password:
            try:
                # Setup dependencies with saved credentials
                setup_dependencies(
                    username=self.username, password=self.password
                )

                # Get use cases
                self.auth_use_case = get_auth_use_case()
                self.installation_use_case = get_installation_use_case()

                # Try to login with saved credentials
                try:
                    auth_result = await self.auth_use_case.login(
                        username=self.username, password=self.password
                    )

                    if auth_result.success:
                        self.is_authenticated = True
                        self._update_session_tokens(auth_result)
                        self._save_session()
                        logger.info("Login successful with saved credentials")
                        return True
                    else:
                        logger.warning(
                            f"Login failed with saved credentials: {auth_result.message}"
                        )
                        # Fall through to interactive login if needed

                except MyVerisureOTPError:
                    logger.info("OTP required for saved credentials")
                    # Fall through to interactive login if needed
                except Exception as e:
                    logger.warning(
                        f"Error logging in with saved credentials: {e}"
                    )
                    # Fall through to interactive login if needed

            except Exception as e:
                logger.warning(f"Error setting up dependencies: {e}")
                clear_dependencies()

        # If we reach here, we need to authenticate interactively
        if interactive:
            return await self._perform_interactive_login()
        else:
            raise Exception(
                "Authentication required but interactive mode disabled"
            )

    async def _perform_interactive_login(self) -> bool:
        """Perform interactive login with OTP support."""
        try:
            # Step 1: Get credentials
            user_id, password = get_user_credentials()

            # Store credentials
            self.username = user_id
            self.password = password

            # Step 2: Setup dependencies
            print_header("CONFIGURACIÓN DE DEPENDENCIAS")
            print_info("Configurando sistema de dependencias...")
            setup_dependencies(username=user_id, password=password)
            print_success("Dependencias configuradas")
            print()

            # Step 3: Get use cases
            self.auth_use_case = get_auth_use_case()
            self.installation_use_case = get_installation_use_case()

            # Step 4: Connect and login
            print_header("CONEXIÓN Y LOGIN")
            print_info("Iniciando proceso de autenticación...")

            try:
                auth_result = await self.auth_use_case.login(
                    username=user_id, password=password
                )

                if auth_result.success:
                    print_success("Login inicial exitoso")
                    print_info(
                        f"Token de autenticación: {auth_result.hash[:50] + '...' if auth_result.hash else 'None'}"
                    )
                    print_success(
                        "¡Autenticación completada sin OTP requerido!"
                    )
                    self.is_authenticated = True
                    self._update_session_tokens(auth_result)
                    self._save_session()
                    return True
                else:
                    print_error(f"Login falló: {auth_result.message}")
                    return False

            except MyVerisureOTPError:
                # OTP required, continue with flow
                print_info(
                    "Se requiere verificación OTP - continuando con el flujo..."
                )

                # Step 5: Show available phones and select
                phones = self.auth_use_case.get_available_phones()
                if not phones:
                    print_error("No hay teléfonos disponibles para OTP")
                    return False

                selected_phone_id = select_phone(phones)
                if selected_phone_id is None:
                    return False

                # Step 6: Send OTP
                print_header("ENVÍO DE OTP")
                print_info(
                    f"Enviando código OTP al teléfono ID {selected_phone_id}..."
                )

                # For simplicity, use default values
                record_id = selected_phone_id
                otp_hash = "default_hash"  # In real implementation, this would come from OTP error

                otp_sent = await self.auth_use_case.send_otp(
                    record_id, otp_hash
                )
                if not otp_sent:
                    print_error("Error enviando el código OTP")
                    return False

                print_success("Código OTP enviado correctamente")
                print_info("Revisa tu teléfono para el SMS")

                # Step 7: Verify OTP
                otp_code = get_otp_code()
                if otp_code is None:
                    return False

                print_info("Verificando código OTP...")
                otp_verified = await self.auth_use_case.verify_otp(otp_code)

                if not otp_verified:
                    print_error("Error verificando el código OTP")
                    return False

                print_header("¡AUTENTICACIÓN COMPLETADA!")
                print_success("¡Código OTP verificado correctamente!")
                print_success("¡Autenticación completa exitosa!")
                print_info("Ya puedes usar la API de My Verisure")

                self.is_authenticated = True
                # Get the final auth result after OTP verification
                try:
                    # Try to get the auth result from the use case
                    if hasattr(self.auth_use_case, '_auth_result'):
                        self._update_session_tokens(self.auth_use_case._auth_result)
                    self._save_session()
                except Exception as e:
                    logger.warning(f"Could not update session tokens: {e}")
                return True

        except MyVerisureOTPError as e:
            print_error(f"Error OTP: {e}")
            print_info(
                "El flujo OTP se inició correctamente, pero hubo un error en la verificación"
            )
            return False

        except MyVerisureAuthenticationError as e:
            print_error(f"Error de autenticación: {e}")
            print_info("Verifica tu User ID (DNI/NIE) y contraseña")
            return False

        except MyVerisureConnectionError as e:
            print_error(f"Error de conexión: {e}")
            print_info("Verifica tu conexión a internet y la URL de la API")
            return False

        except MyVerisureError as e:
            print_error(f"Error de My Verisure: {e}")
            return False

        except KeyboardInterrupt:
            print("\n⏹️  Proceso interrumpido por el usuario")
            return False

        except Exception as e:
            print_error(f"Error inesperado: {e}")
            return False

    async def get_installations(self):
        """Get all installations."""
        if not self.is_authenticated:
            raise Exception("Not authenticated")

        return await self.installation_use_case.get_installations()

    async def cleanup(self):
        """Clean up resources."""
        try:
            # Disconnect all specific clients
            try:
                auth_client = get_auth_client()
                if auth_client:
                    print_info("Desconectando cliente de autenticación...")
                    await auth_client.disconnect()
                    print_success("Cliente de autenticación desconectado")
            except Exception as e:
                print_info(f"No se pudo desconectar el cliente de autenticación: {e}")

            try:
                session_client = get_session_client()
                if session_client:
                    print_info("Desconectando cliente de sesión...")
                    await session_client.disconnect()
                    print_success("Cliente de sesión desconectado")
            except Exception as e:
                print_info(f"No se pudo desconectar el cliente de sesión: {e}")

            try:
                installation_client = get_installation_client()
                if installation_client:
                    print_info("Desconectando cliente de instalación...")
                    await installation_client.disconnect()
                    print_success("Cliente de instalación desconectado")
            except Exception as e:
                print_info(f"No se pudo desconectar el cliente de instalación: {e}")

            try:
                alarm_client = get_alarm_client()
                if alarm_client:
                    print_info("Desconectando cliente de alarma...")
                    await alarm_client.disconnect()
                    print_success("Cliente de alarma desconectado")
            except Exception as e:
                print_info(f"No se pudo desconectar el cliente de alarma: {e}")

        except Exception as e:
            print_info(f"Error obteniendo clientes: {e}")

        # Clear dependencies
        print_info("Limpiando dependencias...")
        clear_dependencies()
        print_success("Dependencias limpiadas")

        # Note: We don't clear the session file here to maintain persistence
        # Only clear it when explicitly logging out

    async def logout(self):
        """Logout and clear session."""
        await self.cleanup()
        self._clear_session_file()
        self.is_authenticated = False
        self.current_installation = None
        self.auth_use_case = None
        self.installation_use_case = None
        self.username = None
        self.password = None
        self.hash_token = None
        self.refresh_token = None
        self.session_timestamp = None
        print_success("Sesión cerrada y limpiada")


# Global session manager instance
session_manager = SessionManager()
