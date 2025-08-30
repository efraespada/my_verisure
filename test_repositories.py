#!/usr/bin/env python3
"""
Test simple para verificar que los repositorios funcionan.
"""

import sys
import os

# Añadir el directorio actual al path para importar el módulo
sys.path.append('./custom_components/my_verisure')

def test_repository_imports():
    """Test que todos los imports de repositorios funcionan."""
    print("🧪 Testing repository imports...")
    
    try:
        # Test Repository interfaces
        from repositories.interfaces.auth_repository import AuthRepository
        from repositories.interfaces.session_repository import SessionRepository
        from repositories.interfaces.installation_repository import InstallationRepository
        from repositories.interfaces.alarm_repository import AlarmRepository
        print("✅ Repository interfaces: OK")
        
        # Test Repository implementations
        from repositories.implementations.auth_repository_impl import AuthRepositoryImpl
        from repositories.implementations.session_repository_impl import SessionRepositoryImpl
        from repositories.implementations.installation_repository_impl import InstallationRepositoryImpl
        from repositories.implementations.alarm_repository_impl import AlarmRepositoryImpl
        print("✅ Repository implementations: OK")
        
        print("\n🎉 All repository imports completed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_repository_creation():
    """Test creación de repositorios."""
    print("\n🧪 Testing repository creation...")
    
    try:
        from repositories.implementations.auth_repository_impl import AuthRepositoryImpl
        from repositories.implementations.session_repository_impl import SessionRepositoryImpl
        from repositories.implementations.installation_repository_impl import InstallationRepositoryImpl
        from repositories.implementations.alarm_repository_impl import AlarmRepositoryImpl
        
        # Create mock client
        mock_client = type('MockClient', (), {})()
        
        # Test AuthRepositoryImpl creation
        auth_repo = AuthRepositoryImpl(mock_client)
        assert auth_repo.client == mock_client
        print("✅ AuthRepositoryImpl creation: OK")
        
        # Test SessionRepositoryImpl creation
        session_repo = SessionRepositoryImpl(mock_client)
        assert session_repo.client == mock_client
        print("✅ SessionRepositoryImpl creation: OK")
        
        # Test InstallationRepositoryImpl creation
        installation_repo = InstallationRepositoryImpl(mock_client)
        assert installation_repo.client == mock_client
        print("✅ InstallationRepositoryImpl creation: OK")
        
        # Test AlarmRepositoryImpl creation
        alarm_repo = AlarmRepositoryImpl(mock_client)
        assert alarm_repo.client == mock_client
        print("✅ AlarmRepositoryImpl creation: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Repository creation error: {e}")
        return False

def test_repository_inheritance():
    """Test que los repositorios heredan correctamente de las interfaces."""
    print("\n🧪 Testing repository inheritance...")
    
    try:
        from repositories.interfaces.auth_repository import AuthRepository
        from repositories.interfaces.session_repository import SessionRepository
        from repositories.interfaces.installation_repository import InstallationRepository
        from repositories.interfaces.alarm_repository import AlarmRepository
        
        from repositories.implementations.auth_repository_impl import AuthRepositoryImpl
        from repositories.implementations.session_repository_impl import SessionRepositoryImpl
        from repositories.implementations.installation_repository_impl import InstallationRepositoryImpl
        from repositories.implementations.alarm_repository_impl import AlarmRepositoryImpl
        
        # Test inheritance
        assert issubclass(AuthRepositoryImpl, AuthRepository)
        assert issubclass(SessionRepositoryImpl, SessionRepository)
        assert issubclass(InstallationRepositoryImpl, InstallationRepository)
        assert issubclass(AlarmRepositoryImpl, AlarmRepository)
        
        print("✅ Repository inheritance: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Repository inheritance error: {e}")
        return False

def main():
    """Función principal."""
    print("🚀 My Verisure Repository Test")
    print("=" * 40)
    
    # Test imports
    if not test_repository_imports():
        print("❌ Repository import tests failed")
        return False
    
    # Test creation
    if not test_repository_creation():
        print("❌ Repository creation tests failed")
        return False
    
    # Test inheritance
    if not test_repository_inheritance():
        print("❌ Repository inheritance tests failed")
        return False
    
    print("\n🎉 All repository tests passed!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 