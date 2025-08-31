#!/usr/bin/env python3
"""
Test simple para verificar que los casos de uso funcionan.
"""

import sys
import os

# Añadir el directorio actual al path para importar el módulo
sys.path.append('./custom_components/my_verisure')

def test_use_case_imports():
    """Test que todos los imports de casos de uso funcionan."""
    print("🧪 Testing use case imports...")
    
    try:
        # Test Use case interfaces
        from use_cases.interfaces.auth_use_case import AuthUseCase
        from use_cases.interfaces.session_use_case import SessionUseCase
        from use_cases.interfaces.installation_use_case import InstallationUseCase
        from use_cases.interfaces.alarm_use_case import AlarmUseCase
        print("✅ Use case interfaces: OK")
        
        # Test Use case implementations
        from use_cases.implementations.auth_use_case_impl import AuthUseCaseImpl
        from use_cases.implementations.session_use_case_impl import SessionUseCaseImpl
        from use_cases.implementations.installation_use_case_impl import InstallationUseCaseImpl
        from use_cases.implementations.alarm_use_case_impl import AlarmUseCaseImpl
        print("✅ Use case implementations: OK")
        
        print("\n🎉 All use case imports completed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_use_case_creation():
    """Test creación de casos de uso."""
    print("\n🧪 Testing use case creation...")
    
    try:
        from use_cases.implementations.auth_use_case_impl import AuthUseCaseImpl
        from use_cases.implementations.session_use_case_impl import SessionUseCaseImpl
        from use_cases.implementations.installation_use_case_impl import InstallationUseCaseImpl
        from use_cases.implementations.alarm_use_case_impl import AlarmUseCaseImpl
        
        # Create mock repositories
        mock_auth_repo = type('MockAuthRepo', (), {})()
        mock_session_repo = type('MockSessionRepo', (), {})()
        mock_installation_repo = type('MockInstallationRepo', (), {})()
        mock_alarm_repo = type('MockAlarmRepo', (), {})()
        
        # Test AuthUseCaseImpl creation
        auth_use_case = AuthUseCaseImpl(mock_auth_repo)
        assert auth_use_case.auth_repository == mock_auth_repo
        print("✅ AuthUseCaseImpl creation: OK")
        
        # Test SessionUseCaseImpl creation
        session_use_case = SessionUseCaseImpl(mock_session_repo)
        assert session_use_case.session_repository == mock_session_repo
        print("✅ SessionUseCaseImpl creation: OK")
        
        # Test InstallationUseCaseImpl creation
        installation_use_case = InstallationUseCaseImpl(mock_installation_repo)
        assert installation_use_case.installation_repository == mock_installation_repo
        print("✅ InstallationUseCaseImpl creation: OK")
        
        # Test AlarmUseCaseImpl creation
        alarm_use_case = AlarmUseCaseImpl(mock_alarm_repo, mock_installation_repo)
        assert alarm_use_case.alarm_repository == mock_alarm_repo
        assert alarm_use_case.installation_repository == mock_installation_repo
        print("✅ AlarmUseCaseImpl creation: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Use case creation error: {e}")
        return False

def test_use_case_inheritance():
    """Test que los casos de uso heredan correctamente de las interfaces."""
    print("\n🧪 Testing use case inheritance...")
    
    try:
        from use_cases.interfaces.auth_use_case import AuthUseCase
        from use_cases.interfaces.session_use_case import SessionUseCase
        from use_cases.interfaces.installation_use_case import InstallationUseCase
        from use_cases.interfaces.alarm_use_case import AlarmUseCase
        
        from use_cases.implementations.auth_use_case_impl import AuthUseCaseImpl
        from use_cases.implementations.session_use_case_impl import SessionUseCaseImpl
        from use_cases.implementations.installation_use_case_impl import InstallationUseCaseImpl
        from use_cases.implementations.alarm_use_case_impl import AlarmUseCaseImpl
        
        # Test inheritance
        assert issubclass(AuthUseCaseImpl, AuthUseCase)
        assert issubclass(SessionUseCaseImpl, SessionUseCase)
        assert issubclass(InstallationUseCaseImpl, InstallationUseCase)
        assert issubclass(AlarmUseCaseImpl, AlarmUseCase)
        
        print("✅ Use case inheritance: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Use case inheritance error: {e}")
        return False

def main():
    """Función principal."""
    print("🚀 My Verisure Use Case Test")
    print("=" * 40)
    
    # Test imports
    if not test_use_case_imports():
        print("❌ Use case import tests failed")
        return False
    
    # Test creation
    if not test_use_case_creation():
        print("❌ Use case creation tests failed")
        return False
    
    # Test inheritance
    if not test_use_case_inheritance():
        print("❌ Use case inheritance tests failed")
        return False
    
    print("\n🎉 All use case tests passed!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 