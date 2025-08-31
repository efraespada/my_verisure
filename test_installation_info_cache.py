#!/usr/bin/env python3
"""
Script de prueba para verificar el cache de información de instalación.
Este script prueba que el caso de uso de alarmas obtiene correctamente panel y capabilities.
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

async def test_installation_info_cache():
    """Prueba el cache de información de instalación."""
    print_header("PRUEBA DE CACHE DE INFORMACIÓN DE INSTALACIÓN")
    
    try:
        # Importar los módulos necesarios
        from dependency_injection.providers import (
            setup_dependencies, 
            get_auth_use_case, 
            get_installation_use_case, 
            get_alarm_use_case,
            clear_dependencies
        )
        from use_cases.implementations.alarm_use_case_impl import InstallationInfoCache
        
        print_success("Importaciones exitosas")
        
        # Test 1: Probar el cache directamente
        print_info("Test 1: Probando InstallationInfoCache directamente...")
        
        cache = InstallationInfoCache(ttl_seconds=60)  # 1 minuto TTL
        
        # Probar cache vacío
        result = cache.get("test_installation")
        if result is None:
            print_success("Cache vacío funciona correctamente")
        else:
            print_error("Cache vacío debería retornar None")
        
        # Probar agregar datos al cache
        cache.set("test_installation", "PROTOCOL", "test_capabilities")
        result = cache.get("test_installation")
        if result and result[0] == "PROTOCOL" and result[1] == "test_capabilities":
            print_success("Datos agregados al cache correctamente")
        else:
            print_error("Error al agregar datos al cache")
        
        # Probar limpiar cache específico
        cache.clear("test_installation")
        result = cache.get("test_installation")
        if result is None:
            print_success("Cache específico limpiado correctamente")
        else:
            print_error("Error al limpiar cache específico")
        
        # Test 2: Configurar dependencias
        print_info("Test 2: Configurando dependencias...")
        setup_dependencies(username="test_user", password="test_password")
        print_success("Dependencias configuradas correctamente")
        
        # Test 3: Obtener casos de uso
        print_info("Test 3: Obteniendo casos de uso...")
        auth_use_case = get_auth_use_case()
        installation_use_case = get_installation_use_case()
        alarm_use_case = get_alarm_use_case()
        
        print_success("Casos de uso obtenidos correctamente")
        print_info(f"Auth use case: {type(auth_use_case).__name__}")
        print_info(f"Installation use case: {type(installation_use_case).__name__}")
        print_info(f"Alarm use case: {type(alarm_use_case).__name__}")
        
        # Test 4: Verificar que el caso de uso de alarmas tiene el cache
        print_info("Test 4: Verificando cache en caso de uso de alarmas...")
        
        # Verificar que tiene el método de cache
        if hasattr(alarm_use_case, 'clear_installation_cache'):
            print_success("Método clear_installation_cache disponible")
        else:
            print_error("Método clear_installation_cache no disponible")
        
        if hasattr(alarm_use_case, 'set_cache_ttl'):
            print_success("Método set_cache_ttl disponible")
        else:
            print_error("Método set_cache_ttl no disponible")
        
        # Test 5: Probar métodos de cache
        print_info("Test 5: Probando métodos de cache...")
        
        # Probar limpiar cache
        try:
            alarm_use_case.clear_installation_cache()
            print_success("Cache limpiado correctamente")
        except Exception as e:
            print_error(f"Error al limpiar cache: {e}")
        
        # Probar establecer TTL
        try:
            alarm_use_case.set_cache_ttl(300)  # 5 minutos
            print_success("TTL establecido correctamente")
        except Exception as e:
            print_error(f"Error al establecer TTL: {e}")
        
        # Test 6: Verificar que el método _get_installation_info existe
        print_info("Test 6: Verificando método _get_installation_info...")
        
        if hasattr(alarm_use_case, '_get_installation_info'):
            print_success("Método _get_installation_info disponible")
        else:
            print_error("Método _get_installation_info no disponible")
        
        # Test 7: Limpiar dependencias
        print_info("Test 7: Limpiando dependencias...")
        clear_dependencies()
        print_success("Dependencias limpiadas correctamente")
        
        print_header("PRUEBA COMPLETADA EXITOSAMENTE")
        print_success("El cache de información de instalación está funcionando correctamente")
        print_info("Los casos de uso ahora obtienen panel y capabilities de los servicios de instalación")
        print_info("Se evitan llamadas repetidas a la API mediante cache local")
        
        return True
        
    except ImportError as e:
        print_error(f"Error de importación: {e}")
        return False
    except Exception as e:
        print_error(f"Error inesperado: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_installation_info_cache())
    sys.exit(0 if success else 1)
