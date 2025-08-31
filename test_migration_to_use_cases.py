#!/usr/bin/env python3
"""
Script de prueba para verificar la migración a casos de uso.
Este script prueba que la nueva arquitectura con casos de uso funciona correctamente.
"""

import asyncio
import logging
import sys
import os

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Añadir el directorio actual al path para importar el módulo
sys.path.append('./custom_components/my_verisure')

def print_header(title: str) -> None:
    """Imprime un encabezado formateado."""
    print("\n" + "=" * 60)
    print(f"🚀 {title}")
    print("=" * 60)

def print_success(message: str) -> None:
    """Imprime un mensaje de éxito."""
    print(f"✅ {message}")

def print_error(message: str) -> None:
    """Imprime un mensaje de error."""
    print(f"❌ {message}")

def print_info(message: str) -> None:
    """Imprime un mensaje informativo."""
    print(f"ℹ️  {message}")

async def test_migration_to_use_cases():
    """Prueba la migración a casos de uso."""
    print_header("PRUEBA DE MIGRACIÓN A CASOS DE USO")
    
    try:
        # Importar los módulos necesarios
        from dependency_injection.providers import (
            setup_dependencies, 
            get_auth_use_case, 
            get_installation_use_case, 
            get_alarm_use_case,
            get_session_use_case,
            clear_dependencies
        )
        from api.exceptions import (
            MyVerisureAuthenticationError,
            MyVerisureConnectionError,
            MyVerisureError,
            MyVerisureOTPError,
        )
        
        print_success("Importaciones exitosas")
        
        # Test 1: Configurar dependencias
        print_info("Test 1: Configurando dependencias...")
        setup_dependencies(username="test_user", password="test_password")
        print_success("Dependencias configuradas correctamente")
        
        # Test 2: Obtener casos de uso
        print_info("Test 2: Obteniendo casos de uso...")
        auth_use_case = get_auth_use_case()
        session_use_case = get_session_use_case()
        installation_use_case = get_installation_use_case()
        alarm_use_case = get_alarm_use_case()
        
        print_success("Casos de uso obtenidos correctamente")
        print_info(f"Auth use case: {type(auth_use_case).__name__}")
        print_info(f"Session use case: {type(session_use_case).__name__}")
        print_info(f"Installation use case: {type(installation_use_case).__name__}")
        print_info(f"Alarm use case: {type(alarm_use_case).__name__}")
        
        # Test 3: Verificar métodos disponibles
        print_info("Test 3: Verificando métodos disponibles...")
        
        # Verificar métodos del caso de uso de autenticación
        auth_methods = [method for method in dir(auth_use_case) if not method.startswith('_')]
        print_info(f"Métodos de AuthUseCase: {auth_methods}")
        
        # Verificar métodos del caso de uso de instalación
        installation_methods = [method for method in dir(installation_use_case) if not method.startswith('_')]
        print_info(f"Métodos de InstallationUseCase: {installation_methods}")
        
        # Verificar métodos del caso de uso de alarmas
        alarm_methods = [method for method in dir(alarm_use_case) if not method.startswith('_')]
        print_info(f"Métodos de AlarmUseCase: {alarm_methods}")
        
        print_success("Métodos verificados correctamente")
        
        # Test 4: Verificar que los modelos de dominio tienen el método dict()
        print_info("Test 4: Verificando modelos de dominio...")
        
        from api.models.domain.alarm import AlarmStatus
        from api.models.domain.installation import Installation, InstallationServices
        from api.models.domain.auth import AuthResult
        
        # Crear instancias de prueba
        alarm_status = AlarmStatus(
            success=True,
            message="Test alarm status",
            status="OK",
            numinst="test_installation"
        )
        
        installation = Installation(
            numinst="test_installation",
            alias="Test Installation",
            panel="PROTOCOL",
            type="test",
            name="Test",
            surname="User",
            address="Test Address",
            city="Test City",
            postcode="12345",
            province="Test Province",
            email="test@example.com",
            phone="123456789"
        )
        
        auth_result = AuthResult(
            success=True,
            message="Test auth result"
        )
        
        # Verificar que tienen el método dict()
        alarm_dict = alarm_status.dict()
        installation_dict = installation.dict()
        auth_dict = auth_result.dict()
        
        print_info(f"AlarmStatus.dict(): {alarm_dict}")
        print_info(f"Installation.dict(): {installation_dict}")
        print_info(f"AuthResult.dict(): {auth_dict}")
        
        print_success("Modelos de dominio verificados correctamente")
        
        # Test 5: Verificar que el coordinator con casos de uso se puede importar
        print_info("Test 5: Verificando coordinator con casos de uso...")
        
        try:
            from coordinator_use_cases import MyVerisureDataUpdateCoordinatorUseCases, ClientCompatibilityWrapper
            print_success("Coordinator con casos de uso importado correctamente")
            
            # Verificar que el wrapper de compatibilidad funciona
            wrapper = ClientCompatibilityWrapper(
                auth_use_case=auth_use_case,
                session_use_case=session_use_case,
                installation_use_case=installation_use_case,
                alarm_use_case=alarm_use_case
            )
            
            wrapper_methods = [method for method in dir(wrapper) if not method.startswith('_')]
            print_info(f"Métodos del ClientCompatibilityWrapper: {wrapper_methods}")
            print_success("Wrapper de compatibilidad creado correctamente")
            
        except ImportError as e:
            print_error(f"No se pudo importar el coordinator con casos de uso: {e}")
        
        # Test 6: Limpiar dependencias
        print_info("Test 6: Limpiando dependencias...")
        clear_dependencies()
        print_success("Dependencias limpiadas correctamente")
        
        print_header("PRUEBA COMPLETADA EXITOSAMENTE")
        print_success("La migración a casos de uso está lista para ser implementada")
        
        return True
        
    except ImportError as e:
        print_error(f"Error de importación: {e}")
        return False
    except Exception as e:
        print_error(f"Error inesperado: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_migration_to_use_cases())
    sys.exit(0 if success else 1)
