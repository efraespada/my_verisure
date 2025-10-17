"""JWT utility functions for My Verisure integration."""

import logging
import time
from typing import Optional, Dict, Any

try:
    import jwt
except ImportError:
    jwt = None

_LOGGER = logging.getLogger(__name__)


def is_jwt_expired(token: str, leeway: int = 30) -> bool:
    """
    Check if a JWT token has expired.
    
    Args:
        token: The JWT token to check
        leeway: Number of seconds of leeway for expiration check
        
    Returns:
        True if token is expired or invalid, False if still valid
    """
    if not token:
        _LOGGER.debug("No token provided")
        return True
        
    if jwt is None:
        _LOGGER.warning("PyJWT not available, cannot validate JWT expiration")
        return False
    
    try:
        # Decode the token without verification to get the payload
        # We only need to check the expiration, not verify the signature
        payload = jwt.decode(token, options={"verify_signature": False})
        
        # Check if token has expiration claim
        if "exp" not in payload:
            _LOGGER.debug("Token has no expiration claim")
            return False
            
        # Get current time
        current_time = time.time()
        expiration_time = payload["exp"]
        
        # Check if token is expired (with leeway)
        is_expired = current_time >= (expiration_time - leeway)
        
        if is_expired:
            _LOGGER.debug("JWT token expired (exp: %s, current: %s)", 
                         expiration_time, current_time)
        else:
            _LOGGER.debug("JWT token is still valid (exp: %s, current: %s)", 
                         expiration_time, current_time)
            
        return is_expired
        
    except jwt.InvalidTokenError as e:
        _LOGGER.warning("Invalid JWT token: %s", e)
        return True
    except Exception as e:
        _LOGGER.error("Error checking JWT expiration: %s", e)
        return True


def get_jwt_payload(token: str) -> Optional[Dict[str, Any]]:
    """
    Get the payload of a JWT token without verification.
    
    Args:
        token: The JWT token to decode
        
    Returns:
        The token payload or None if invalid
    """
    if not token or jwt is None:
        return None
        
    try:
        return jwt.decode(token, options={"verify_signature": False})
    except Exception as e:
        _LOGGER.debug("Error decoding JWT payload: %s", e)
        return None
