"""Unit tests for domain models."""

import pytest

from ...api.models.domain.auth import Auth, AuthResult


class TestAuth:
    """Test Auth domain model."""

    def test_auth_creation(self):
        """Test Auth creation with valid data."""
        auth = Auth(username="test_user", password="test_pass")
        
        assert auth.username == "test_user"
        assert auth.password == "test_pass"

    def test_auth_validation_missing_username(self):
        """Test Auth validation with missing username."""
        with pytest.raises(ValueError, match="Username is required"):
            Auth(username="", password="test_pass")

    def test_auth_validation_missing_password(self):
        """Test Auth validation with missing password."""
        with pytest.raises(ValueError, match="Password is required"):
            Auth(username="test_user", password="")

    def test_auth_validation_none_username(self):
        """Test Auth validation with None username."""
        with pytest.raises(ValueError, match="Username is required"):
            Auth(username=None, password="test_pass")

    def test_auth_validation_none_password(self):
        """Test Auth validation with None password."""
        with pytest.raises(ValueError, match="Password is required"):
            Auth(username="test_user", password=None)


class TestAuthResult:
    """Test AuthResult domain model."""

    def test_auth_result_creation(self):
        """Test AuthResult creation."""
        result = AuthResult(
            success=True,
            message="Login successful",
            hash="test_hash",
            refresh_token="test_refresh",
            lang="es",
            legals=True,
            change_password=False,
            need_device_authorization=True,
        )

        assert result.success is True
        assert result.message == "Login successful"
        assert result.hash == "test_hash"
        assert result.refresh_token == "test_refresh"
        assert result.lang == "es"
        assert result.legals is True
        assert result.change_password is False
        assert result.need_device_authorization is True

    def test_auth_result_from_dto(self):
        """Test AuthResult from DTO."""
        from ...api.models.dto.auth_dto import AuthDTO
        
        dto = AuthDTO(
            res="OK",
            msg="Login successful",
            hash="test_hash",
            refresh_token="test_refresh",
            lang="es",
            legals=True,
            change_password=False,
            need_device_authorization=True,
        )

        result = AuthResult.from_dto(dto)

        assert result.success is True
        assert result.message == "Login successful"
        assert result.hash == "test_hash"
        assert result.refresh_token == "test_refresh"
        assert result.lang == "es"
        assert result.legals is True
        assert result.change_password is False
        assert result.need_device_authorization is True

    def test_auth_result_to_dto(self):
        """Test AuthResult to DTO."""
        result = AuthResult(
            success=True,
            message="Login successful",
            hash="test_hash",
            refresh_token="test_refresh",
            lang="es",
            legals=True,
            change_password=False,
            need_device_authorization=True,
        )

        dto = result.to_dto()

        assert dto.res == "OK"
        assert dto.msg == "Login successful"
        assert dto.hash == "test_hash"
        assert dto.refresh_token == "test_refresh"
        assert dto.lang == "es"
        assert dto.legals is True
        assert dto.change_password is False
        assert dto.need_device_authorization is True

    def test_auth_result_failure(self):
        """Test AuthResult for failure case."""
        result = AuthResult(
            success=False,
            message="Login failed",
        )

        assert result.success is False
        assert result.message == "Login failed"
        assert result.hash is None
        assert result.refresh_token is None
        assert result.lang is None
        assert result.legals is None
        assert result.change_password is None
        assert result.need_device_authorization is None

    def test_auth_result_from_dto_failure(self):
        """Test AuthResult from DTO for failure case."""
        from ...api.models.dto.auth_dto import AuthDTO
        
        dto = AuthDTO(
            res="ERROR",
            msg="Login failed",
        )

        result = AuthResult.from_dto(dto)

        assert result.success is False
        assert result.message == "Login failed"
        assert result.hash is None
        assert result.refresh_token is None
        assert result.lang is None
        assert result.legals is None
        assert result.change_password is None
        assert result.need_device_authorization is None
