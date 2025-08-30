#!/usr/bin/env python3
"""
Test simple para verificar que la estructura de modelos funciona.
"""

import sys
import os

# Añadir el directorio actual al path para importar el módulo
sys.path.append('./custom_components/my_verisure')

def test_imports():
    """Test que todos los imports funcionan."""
    print("🧪 Testing imports...")
    
    try:
        # Test API imports
        from api.fields import VERISURE_GRAPHQL_URL, RESPONSE_OK, RESPONSE_KO
        print("✅ API fields imports: OK")
        
        # Test DTO imports
        from api.models.dto.auth_dto import AuthDTO, OTPDataDTO, PhoneDTO
        from api.models.dto.installation_dto import InstallationDTO, InstallationServicesDTO, ServiceDTO
        from api.models.dto.alarm_dto import AlarmStatusDTO, ArmResultDTO, DisarmResultDTO
        from api.models.dto.session_dto import SessionDTO, DeviceIdentifiersDTO
        print("✅ DTO imports: OK")
        
        # Test Domain imports
        from api.models.domain.auth import Auth, AuthResult, OTPData, Phone
        from api.models.domain.installation import Installation, InstallationServices, Service
        from api.models.domain.alarm import AlarmStatus, ArmResult, DisarmResult
        from api.models.domain.session import Session, DeviceIdentifiers, SessionData
        print("✅ Domain imports: OK")
        
        # Test Repository interfaces
        from repositories.interfaces.auth_repository import AuthRepository
        from repositories.interfaces.installation_repository import InstallationRepository
        from repositories.interfaces.alarm_repository import AlarmRepository
        from repositories.interfaces.session_repository import SessionRepository
        print("✅ Repository interfaces: OK")
        
        # Test Use case interfaces
        from use_cases.interfaces.auth_use_case import AuthUseCase
        from use_cases.interfaces.installation_use_case import InstallationUseCase
        from use_cases.interfaces.alarm_use_case import AlarmUseCase
        from use_cases.interfaces.session_use_case import SessionUseCase
        print("✅ Use case interfaces: OK")
        
        # Test Dependency injection
        from dependency_injection.container import DependencyContainer, register, resolve
        print("✅ Dependency injection: OK")
        
        print("\n🎉 All imports completed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_dto_creation():
    """Test creación de DTOs."""
    print("\n🧪 Testing DTO creation...")
    
    try:
        from api.models.dto.auth_dto import AuthDTO
        
        # Test AuthDTO creation
        dto = AuthDTO(
            res="OK",
            msg="Test message",
            hash="test_hash",
            refresh_token="test_refresh"
        )
        
        assert dto.res == "OK"
        assert dto.msg == "Test message"
        assert dto.hash == "test_hash"
        assert dto.refresh_token == "test_refresh"
        
        print("✅ AuthDTO creation: OK")
        
        # Test from_dict
        data = {
            "res": "OK",
            "msg": "From dict",
            "hash": "dict_hash",
            "refreshToken": "dict_refresh"
        }
        
        dto_from_dict = AuthDTO.from_dict(data)
        assert dto_from_dict.res == "OK"
        assert dto_from_dict.msg == "From dict"
        assert dto_from_dict.hash == "dict_hash"
        assert dto_from_dict.refresh_token == "dict_refresh"
        
        print("✅ AuthDTO from_dict: OK")
        
        # Test to_dict
        result_dict = dto.to_dict()
        assert result_dict["res"] == "OK"
        assert result_dict["msg"] == "Test message"
        assert result_dict["hash"] == "test_hash"
        assert result_dict["refreshToken"] == "test_refresh"
        
        print("✅ AuthDTO to_dict: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ DTO creation error: {e}")
        return False

def test_domain_models():
    """Test creación de modelos de dominio."""
    print("\n🧪 Testing domain models...")
    
    try:
        from api.models.domain.auth import Auth, AuthResult
        from api.models.dto.auth_dto import AuthDTO
        
        # Test Auth validation
        auth = Auth(username="test_user", password="test_pass")
        assert auth.username == "test_user"
        assert auth.password == "test_pass"
        
        print("✅ Auth domain model: OK")
        
        # Test AuthResult from DTO
        dto = AuthDTO(
            res="OK",
            msg="Success",
            hash="test_hash",
            refresh_token="test_refresh"
        )
        
        result = AuthResult.from_dto(dto)
        assert result.success is True
        assert result.message == "Success"
        assert result.hash == "test_hash"
        assert result.refresh_token == "test_refresh"
        
        print("✅ AuthResult from_dto: OK")
        
        # Test AuthResult to DTO
        domain_result = AuthResult(
            success=True,
            message="Domain success",
            hash="domain_hash",
            refresh_token="domain_refresh"
        )
        
        result_dto = domain_result.to_dto()
        assert result_dto.res == "OK"
        assert result_dto.msg == "Domain success"
        assert result_dto.hash == "domain_hash"
        assert result_dto.refresh_token == "domain_refresh"
        
        print("✅ AuthResult to_dto: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Domain model error: {e}")
        return False

def test_dependency_injection():
    """Test sistema de inyección de dependencias."""
    print("\n🧪 Testing dependency injection...")
    
    try:
        from dependency_injection.container import DependencyContainer
        
        # Create container
        container = DependencyContainer()
        
        # Test registration
        def mock_provider():
            return "mock_value"
        
        container.register(str, mock_provider)
        
        # Test resolution
        result = container.resolve(str)
        assert result == "mock_value"
        
        print("✅ Dependency injection: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Dependency injection error: {e}")
        return False

def main():
    """Función principal."""
    print("🚀 My Verisure Structure Test")
    print("=" * 40)
    
    # Test imports
    if not test_imports():
        print("❌ Import tests failed")
        return False
    
    # Test DTO creation
    if not test_dto_creation():
        print("❌ DTO tests failed")
        return False
    
    # Test domain models
    if not test_domain_models():
        print("❌ Domain model tests failed")
        return False
    
    # Test dependency injection
    if not test_dependency_injection():
        print("❌ Dependency injection tests failed")
        return False
    
    print("\n🎉 All tests passed!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 