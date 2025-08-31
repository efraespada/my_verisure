"""Session manager for the CLI."""

import asyncio
import json
import logging
import os
import sys
from typing import Optional, Tuple

# Add core to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'core'))

from core.dependency_injection.providers import (
    setup_dependencies, 
    get_auth_use_case, 
    get_installation_use_case, 
    clear_dependencies, 
    get_client
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
                with open(self.session_file, 'r') as f:
                    session_data = json.load(f)
                
                self.username = session_data.get('username')
                self.password = session_data.get('password')
                self.current_installation = session_data.get('current_installation')
                
                # Check if we have credentials
                if self.username and self.password:
                    logger.info("Session loaded from file")
                    # We'll verify the session is still valid when needed
                else:
                    logger.info("No valid session found in file")
                    
        except Exception as e:
            logger.warning(f"Could not load session: {e}")
            self._clear_session_file()
    
    def _save_session(self) -> None:
        """Save session to file."""
        try:
            session_data = {
                'username': self.username,
                'password': self.password,
                'current_installation': self.current_installation,
                'timestamp': asyncio.get_event_loop().time()
            }
            
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            logger.info("Session saved to file")
            
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
    
    async def ensure_authenticated(self, interactive: bool = True) -> bool:
        """Ensure the user is authenticated, performing login if necessary."""
        # If we have credentials, try to login with them
        if self.username and self.password:
            try:
                # Setup dependencies with saved credentials
                setup_dependencies(username=self.username, password=self.password)
                
                # Get use cases
                self.auth_use_case = get_auth_use_case()
                self.installation_use_case = get_installation_use_case()
                
                # Try to login with saved credentials
                try:
                    auth_result = await self.auth_use_case.login(username=self.username, password=self.password)
                    
                    if auth_result.success:
                        self.is_authenticated = True
                        logger.info("Login successful with saved credentials")
                        return True
                    else:
                        logger.warning(f"Login failed with saved credentials: {auth_result.message}")
                        # Fall through to interactive login if needed
                        
                except MyVerisureOTPError:
                    logger.info("OTP required for saved credentials")
                    # Fall through to interactive login if needed
                except Exception as e:
                    logger.warning(f"Error logging in with saved credentials: {e}")
                    # Fall through to interactive login if needed
                    
            except Exception as e:
                logger.warning(f"Error setting up dependencies: {e}")
                clear_dependencies()
        
        # If we reach here, we need to authenticate interactively
        if interactive:
            return await self._perform_interactive_login()
        else:
            raise Exception("Authentication required but interactive mode disabled")
    
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
                auth_result = await self.auth_use_case.login(username=user_id, password=password)
                
                if auth_result.success:
                    print_success("Login inicial exitoso")
                    print_info(f"Token de autenticación: {auth_result.hash[:50] + '...' if auth_result.hash else 'None'}")
                    print_success("¡Autenticación completada sin OTP requerido!")
                    self.is_authenticated = True
                    self._save_session()
                    return True
                else:
                    print_error(f"Login falló: {auth_result.message}")
                    return False
                    
            except MyVerisureOTPError:
                # OTP required, continue with flow
                print_info("Se requiere verificación OTP - continuando con el flujo...")
                
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
                print_info(f"Enviando código OTP al teléfono ID {selected_phone_id}...")
                
                # For simplicity, use default values
                record_id = selected_phone_id
                otp_hash = "default_hash"  # In real implementation, this would come from OTP error
                
                otp_sent = await self.auth_use_case.send_otp(record_id, otp_hash)
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
                self._save_session()
                return True
            
        except MyVerisureOTPError as e:
            print_error(f"Error OTP: {e}")
            print_info("El flujo OTP se inició correctamente, pero hubo un error en la verificación")
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
            # Get client and disconnect explicitly
            try:
                client = get_client()
                if client:
                    print_info("Desconectando cliente HTTP...")
                    await client.disconnect()
                    print_success("Cliente HTTP desconectado")
            except Exception as e:
                print_info(f"No se pudo desconectar el cliente: {e}")
        except Exception as e:
            print_info(f"Error obteniendo cliente: {e}")
        
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
        print_success("Sesión cerrada y limpiada")


# Global session manager instance
session_manager = SessionManager()
