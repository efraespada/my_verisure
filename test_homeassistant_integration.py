#!/usr/bin/env python3
"""
Script de prueba que simula el comportamiento de Home Assistant.
Este script prueba el coordinator y el manejo de sesiones como lo haría HA.
"""

import asyncio
import logging
import sys
import os
from typing import Optional

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Añadir el directorio actual al path para importar el módulo api
sys.path.append('./custom_components/my_verisure')

try:
    from coordinator import MyVerisureDataUpdateCoordinator
    from const import CONF_USER, CONF_PASSWORD, CONF_INSTALLATION_ID
except ImportError as e:
    logger.error(f"No se pudo importar los módulos: {e}")
    logger.error("Asegúrate de estar en el directorio correcto del proyecto")
    sys.exit(1)


class MockConfigEntry:
    """Mock config entry for testing."""
    
    def __init__(self, user: str, password: str, installation_id: str = None):
        self.data = {
            CONF_USER: user,
            CONF_PASSWORD: password,
            CONF_INSTALLATION_ID: installation_id
        }
        self.entry_id = "test_entry_id"


class MockHomeAssistant:
    """Mock Home Assistant instance for testing."""
    
    def __init__(self):
        self.config_path = "test_storage"
        
    def config_path(self, *args):
        """Mock config path."""
        return os.path.join(self.config_path, *args)


async def test_homeassistant_integration(user_id: str, password: str) -> None:
    """Prueba la integración como lo haría Home Assistant."""
    logger.info("🧪 Iniciando prueba de integración Home Assistant...")
    logger.info(f"👤 User ID: {user_id}")
    logger.info(f"🔑 Password: {'*' * len(password)}")
    
    # Create mock objects
    mock_hass = MockHomeAssistant()
    mock_entry = MockConfigEntry(user_id, password)
    
    # Ensure storage directory exists
    os.makedirs(mock_hass.config_path, exist_ok=True)
    
    try:
        # Create coordinator (this simulates what HA does)
        logger.info("🔧 Creando coordinator...")
        coordinator = MyVerisureDataUpdateCoordinator(mock_hass, mock_entry)
        logger.info("✅ Coordinator creado")
        
        # Test login (this simulates HA setup)
        logger.info("🔐 Probando login...")
        login_success = await coordinator.async_login()
        
        if login_success:
            logger.info("✅ Login exitoso en coordinator")
            
            # Test data update (this simulates HA polling)
            logger.info("📊 Probando actualización de datos...")
            try:
                data = await coordinator._async_update_data()
                logger.info("✅ Datos obtenidos: %s", data)
            except Exception as e:
                logger.warning("⚠️  Error obteniendo datos (esperado sin queries implementadas): %s", e)
            
            # Test session persistence
            logger.info("🔄 Probando persistencia de sesión...")
            new_coordinator = MyVerisureDataUpdateCoordinator(mock_hass, mock_entry)
            session_loaded = await new_coordinator.async_login()
            
            if session_loaded:
                logger.info("✅ Sesión persistida correctamente")
            else:
                logger.error("❌ Error al persistir sesión")
        else:
            logger.error("❌ Login falló en coordinator")
            
    except Exception as e:
        logger.error(f"❌ Error en integración: {e}")
        
    finally:
        # Cleanup
        logger.info("🧹 Limpiando...")
        if 'coordinator' in locals():
            await coordinator.async_shutdown()


def main():
    """Función principal."""
    print("🚀 My Verisure Home Assistant Integration Test")
    print("=" * 50)
    
    # Verificar argumentos
    if len(sys.argv) != 3:
        print("Uso: python test_homeassistant_integration.py <user_id> <password>")
        print("Ejemplo: python test_homeassistant_integration.py 16633776S mi_password")
        print("\nNota: El user_id debe ser tu DNI/NIE (sin guiones)")
        sys.exit(1)
    
    user_id = sys.argv[1]
    password = sys.argv[2]
    
    print(f"👤 User ID: {user_id}")
    print(f"🔑 Password: {'*' * len(password)}")
    print()
    
    # Ejecutar prueba
    try:
        asyncio.run(test_homeassistant_integration(user_id, password))
    except KeyboardInterrupt:
        print("\n⏹️  Prueba interrumpida por el usuario")
    except Exception as e:
        logger.error(f"❌ Error ejecutando prueba: {e}")


if __name__ == "__main__":
    main() 