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
        self.is_authenticated = False
        self.current_installation = None
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
                    self.is_authenticated = True
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
            
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f)
                
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

    def update_credentials(self, username: str, password: str, hash_token: str, refresh_token: str = None) -> None:
        """Update credentials after successful authentication."""
        self.username = username
        self.password = password
        self.hash_token = hash_token
        self.refresh_token = refresh_token
        self.session_timestamp = time.time()
        self.is_authenticated = True
        
        # Save session
        self._save_session()
        logger.info("Credentials updated and session saved")

    def clear_credentials(self) -> None:
        """Clear all credentials and session data."""
        self.is_authenticated = False
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
        
        return True  # We have credentials, let the use case handle the login

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