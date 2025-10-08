"""Session manager for My Verisure integration."""

import json
import logging
import os
import time
from typing import Optional, Dict, Any

# SessionManager is a simple credential storage, no complex dependencies

logger = logging.getLogger(__name__)

# Global singleton instance
_session_manager_instance: Optional['SessionManager'] = None


class SessionManager:
    """Manages authentication session for My Verisure integration."""

    def __init__(self):
        self._is_authenticated = False
        self.current_installation = None
        self.session_file = self._get_session_file_path()
        self.username = None
        self.password = None
        self.hash_token = None
        self.refresh_token = None
        self.session_timestamp = None

        # Try to load existing session
        self._load_session()

    @property
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated."""
        # Check if we have valid credentials and token
        if not self.username or not self.password or not self.hash_token:
            return False
        
        # Check if token is still valid
        return self._is_token_valid()

    def _get_session_file_path(self) -> str:
        """Get the session file path."""
        # Create .my_verisure directory in user's home
        home_dir = os.path.expanduser("~")
        session_dir = os.path.join(home_dir, ".my_verisure")
        os.makedirs(session_dir, exist_ok=True)
        return os.path.join(session_dir, "session.json")

    def _load_session(self) -> None:
        """Load session from file."""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r') as f:
                    session_data = json.load(f)
                
                self.username = session_data.get('username')
                self.password = session_data.get('password')
                self.hash_token = session_data.get('hash_token')
                self.refresh_token = session_data.get('refresh_token')
                self.session_timestamp = session_data.get('session_timestamp')
                self.current_installation = session_data.get('current_installation')
                
                # Check if session is still valid
                if self._is_token_valid():
                    self._is_authenticated = True
                    logger.info("Valid session loaded from file")
                else:
                    logger.info("Session expired, will require re-authentication")
                    
        except Exception as e:
            logger.warning(f"Could not load session: {e}")

    def _save_session(self) -> None:
        """Save session to file."""
        try:
            session_data = {
                'username': self.username,
                'password': self.password,
                'hash_token': self.hash_token,
                'refresh_token': self.refresh_token,
                'session_timestamp': self.session_timestamp,
                'current_installation': self.current_installation,
            }
            
            # Use asyncio to run file operations in thread pool
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, run in thread pool
                loop.run_in_executor(None, self._write_session_file, session_data)
            else:
                # If not in async context, write directly
                self._write_session_file(session_data)
            
            logger.info("Session saved to file")
        except Exception as e:
            logger.error(f"Could not save session: {e}")

    def _write_session_file(self, session_data: dict) -> None:
        """Write session data to file (blocking operation)."""
        with open(self.session_file, 'w') as f:
            json.dump(session_data, f)

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
        current_time = time.time()
        token_age = current_time - self.session_timestamp

        if token_age > 360:  # 6 minutes
            logger.info(f"Token expired (age: {token_age:.1f} seconds)")
            return False

        logger.info(f"Token appears valid (age: {token_age:.1f} seconds)")
        return True

    async def _try_automatic_reauthentication(self) -> bool:
        """Try to reauthenticate automatically using stored credentials."""
        try:
            logger.info("Attempting automatic reauthentication with stored credentials...")
            
            # Import here to avoid circular imports
            from .dependency_injection.providers import (
                setup_dependencies,
                get_auth_use_case,
                clear_dependencies,
            )
            
            # Setup dependencies
            setup_dependencies()
            
            try:
                # Get auth use case and perform login
                auth_use_case = get_auth_use_case()
                
                # Perform login with stored credentials
                auth_result = await auth_use_case.login(self.username, self.password)
                
                if auth_result.success:
                    # Update credentials with new tokens
                    self.update_credentials(
                        self.username,
                        self.password,
                        auth_result.hash,
                        auth_result.refresh_token
                    )
                    logger.info("Automatic reauthentication successful")
                    return True
                else:
                    logger.warning(f"Automatic reauthentication failed: {auth_result.message}")
                    return False
                    
            finally:
                # Clean up dependencies
                clear_dependencies()
                
        except Exception as e:
            logger.warning(f"Automatic reauthentication failed: {e}")
            return False

    def update_credentials(self, username: str, password: str, hash_token: str, refresh_token: str = None) -> None:
        """Update credentials after successful authentication."""
        self.username = username
        self.password = password
        self.hash_token = hash_token
        self.refresh_token = refresh_token
        self.session_timestamp = time.time()
        self._is_authenticated = True
        
        # Save session
        self._save_session()
        logger.info("Credentials updated and session saved")

    def clear_credentials(self) -> None:
        """Clear all credentials and session data."""
        self._is_authenticated = False
        self.current_installation = None
        self.username = None
        self.password = None
        self.hash_token = None
        self.refresh_token = None
        self.session_timestamp = None
        
        # Clear session file
        self._clear_session_file()
        logger.info("Session cleared and cleaned")

    def get_current_hash_token(self) -> Optional[str]:
        """Get current hash token."""
        return self.hash_token

    def get_current_session_data(self) -> Optional[Dict[str, Any]]:
        """Get current session data."""
        if self.hash_token and self.username:
            return {
                'user': self.username,
                'lang': 'ES',
                'legals': True,
                'changePassword': False,
                'needDeviceAuthorization': None,
                'login_time': self.session_timestamp or time.time(),
            }
        return None

    def get_current_cookies(self) -> Optional[Dict[str, str]]:
        """Get current cookies."""
        # For now, return empty dict - cookies are handled by clients
        return {}

    def is_session_valid(self) -> bool:
        """Check if current session is valid."""
        if not self.hash_token or not self.session_timestamp:
            return False
        
        # Check if session is not too old (6 minutes)
        current_time = time.time()
        session_age = current_time - self.session_timestamp
        
        return session_age <= 360  # 6 minutes

    async def ensure_authenticated(self, interactive: bool = True) -> bool:
        """Check if we have valid credentials."""
        # Check if we already have valid credentials
        if self.is_session_valid():
            logger.info("Valid session found, no authentication needed")
            return True
        
        # If we don't have valid credentials, we need to authenticate
        logger.info("No valid session found, authentication required")
        
        # If we don't have credentials, we need to get them
        if not self.username or not self.password:
            if interactive:
                # Get credentials interactively
                self.username, self.password = self._get_user_credentials()
                return True  # We have credentials now, let the use case handle the login
            else:
                logger.error("No credentials available and non-interactive mode")
                return False
        
        # We have credentials but session is expired, try automatic reauthentication
        logger.info("Session expired but credentials available, attempting automatic reauthentication...")
        return await self._try_automatic_reauthentication()

    def _get_user_credentials(self) -> tuple[str, str]:
        """Get user credentials interactively."""
        print("\n============================================================")
        print("🚀 MY VERISURE - AUTENTICACIÓN INTERACTIVA")
        print("============================================================")
        print("👤 Ingresa tus credenciales de My Verisure:")
        print()
        
        try:
            username = input("📋 User ID (DNI/NIE): ").strip()
            password = input("🔐 Contraseña: ").strip()
            return username, password
        except EOFError:
            # For testing purposes, use hardcoded credentials
            print("📋 User ID (DNI/NIE): 16633776S")
            print("🔐 Contraseña: [HIDDEN]")
            return "16633776S", "Papipupepo2@"

    async def logout(self) -> None:
        """Logout and clear session."""
        logger.info("Logging out and clearing session")
        self.clear_credentials()
        self._clear_session_file()
        logger.info("Logout completed")

    async def cleanup(self) -> None:
        """Clean up resources."""
        # This method will be implemented by the CLI's session manager
        # For now, just clear credentials
        self.clear_credentials()


def get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    global _session_manager_instance
    if _session_manager_instance is None:
        _session_manager_instance = SessionManager()
    return _session_manager_instance