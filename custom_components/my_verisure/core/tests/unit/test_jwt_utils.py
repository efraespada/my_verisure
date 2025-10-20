"""Unit tests for JWT utilities."""

import time
from unittest.mock import patch, Mock
import pytest

from ...utils.jwt_utils import is_jwt_expired, get_jwt_payload


class TestJWTUtils:
    """Test JWT utility functions."""

    def test_is_jwt_expired_no_token(self):
        """Test JWT expiration check with no token."""
        result = is_jwt_expired("")
        assert result is True
        
        result = is_jwt_expired(None)
        assert result is True

    def test_is_jwt_expired_no_jwt_library(self):
        """Test JWT expiration check when PyJWT is not available."""
        with patch('...utils.jwt_utils.jwt', None):
            result = is_jwt_expired("some_token")
            assert result is False

    def test_is_jwt_expired_valid_token(self):
        """Test JWT expiration check with valid token."""
        # Create a token that expires in 1 hour
        future_time = int(time.time()) + 3600
        
        with patch('...utils.jwt_utils.jwt') as mock_jwt:
            mock_jwt.decode.return_value = {"exp": future_time}
            
            result = is_jwt_expired("valid_token")
            assert result is False
            mock_jwt.decode.assert_called_once_with("valid_token", options={"verify_signature": False})

    def test_is_jwt_expired_expired_token(self):
        """Test JWT expiration check with expired token."""
        # Create a token that expired 1 hour ago
        past_time = int(time.time()) - 3600
        
        with patch('...utils.jwt_utils.jwt') as mock_jwt:
            mock_jwt.decode.return_value = {"exp": past_time}
            
            result = is_jwt_expired("expired_token")
            assert result is True

    def test_is_jwt_expired_with_leeway(self):
        """Test JWT expiration check with leeway."""
        # Create a token that expires in 20 seconds (less than default 30s leeway)
        future_time = int(time.time()) + 20
        
        with patch('...utils.jwt_utils.jwt') as mock_jwt:
            mock_jwt.decode.return_value = {"exp": future_time}
            
            result = is_jwt_expired("token_with_leeway", leeway=30)
            assert result is True

    def test_is_jwt_expired_no_exp_claim(self):
        """Test JWT expiration check with token that has no exp claim."""
        with patch('...utils.jwt_utils.jwt') as mock_jwt:
            mock_jwt.decode.return_value = {"sub": "user123"}
            
            result = is_jwt_expired("token_no_exp")
            assert result is False

    def test_is_jwt_expired_invalid_token(self):
        """Test JWT expiration check with invalid token."""
        with patch('...utils.jwt_utils.jwt') as mock_jwt:
            mock_jwt.InvalidTokenError = Exception
            mock_jwt.decode.side_effect = Exception("Invalid token")
            
            result = is_jwt_expired("invalid_token")
            assert result is True

    def test_is_jwt_expired_decode_error(self):
        """Test JWT expiration check with decode error."""
        with patch('...utils.jwt_utils.jwt') as mock_jwt:
            mock_jwt.decode.side_effect = Exception("Decode error")
            
            result = is_jwt_expired("error_token")
            assert result is True

    def test_get_jwt_payload_no_token(self):
        """Test getting JWT payload with no token."""
        result = get_jwt_payload("")
        assert result is None
        
        result = get_jwt_payload(None)
        assert result is None

    def test_get_jwt_payload_no_jwt_library(self):
        """Test getting JWT payload when PyJWT is not available."""
        with patch('...utils.jwt_utils.jwt', None):
            result = get_jwt_payload("some_token")
            assert result is None

    def test_get_jwt_payload_success(self):
        """Test getting JWT payload successfully."""
        expected_payload = {"sub": "user123", "exp": 1234567890, "iat": 1234567890}
        
        with patch('...utils.jwt_utils.jwt') as mock_jwt:
            mock_jwt.decode.return_value = expected_payload
            
            result = get_jwt_payload("valid_token")
            assert result == expected_payload
            mock_jwt.decode.assert_called_once_with("valid_token", options={"verify_signature": False})

    def test_get_jwt_payload_decode_error(self):
        """Test getting JWT payload with decode error."""
        with patch('...utils.jwt_utils.jwt') as mock_jwt:
            mock_jwt.decode.side_effect = Exception("Decode error")
            
            result = get_jwt_payload("error_token")
            assert result is None

    def test_is_jwt_expired_with_mock_time(self):
        """Test JWT expiration check with mocked time."""
        # Mock time to a fixed value
        fixed_time = 1000000000  # Some fixed timestamp
        
        with patch('time.time', return_value=fixed_time):
            with patch('...utils.jwt_utils.jwt') as mock_jwt:
                # Token expires 1 hour after fixed time
                mock_jwt.decode.return_value = {"exp": fixed_time + 3600}
                
                result = is_jwt_expired("token")
                assert result is False
                
                # Token expired 1 hour before fixed time
                mock_jwt.decode.return_value = {"exp": fixed_time - 3600}
                
                result = is_jwt_expired("expired_token")
                assert result is True

    def test_is_jwt_expired_edge_case_exact_expiration(self):
        """Test JWT expiration check at exact expiration time."""
        current_time = int(time.time())
        
        with patch('...utils.jwt_utils.jwt') as mock_jwt:
            # Token expires exactly now
            mock_jwt.decode.return_value = {"exp": current_time}
            
            result = is_jwt_expired("token", leeway=0)
            assert result is True
            
            # Token expires exactly now with leeway
            result = is_jwt_expired("token", leeway=30)
            assert result is True

    def test_get_jwt_payload_with_complex_payload(self):
        """Test getting JWT payload with complex data."""
        complex_payload = {
            "sub": "user123",
            "exp": 1234567890,
            "iat": 1234567890,
            "roles": ["admin", "user"],
            "metadata": {
                "device_id": "device123",
                "ip_address": "192.168.1.1"
            }
        }
        
        with patch('...utils.jwt_utils.jwt') as mock_jwt:
            mock_jwt.decode.return_value = complex_payload
            
            result = get_jwt_payload("complex_token")
            assert result == complex_payload
            assert result["roles"] == ["admin", "user"]
            assert result["metadata"]["device_id"] == "device123"
