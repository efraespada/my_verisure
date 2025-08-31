#!/usr/bin/env python3
"""
Script de prueba simplificado para el coordinator sin dependencias de Home Assistant.
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
    from api.client import MyVerisureClient
    from api.exceptions import (
        MyVerisureAuthenticationError,
        MyVerisureConnectionError,
        MyVerisureError,
    )
except ImportError as e:
    logger.error(f"No se pudo importar los módulos: {e}")
    logger.error("Asegúrate de estar en el directorio correcto del proyecto")
    sys.exit(1)


class SimpleCoordinator:
    """Simplified coordinator for testing."""
    
    def __init__(self, user: str, password: str, storage_path: str = "test_storage"):
        self.user = user
        self.password = password
        self.storage_path = storage_path
        self.client = MyVerisureClient(user=user, password=password)
        
        # Session file path
        session_file = os.path.join(storage_path, f"my_verisure_{user}.json")
        
        # Try to load existing session
        if self.client.load_session(session_file):
            logger.info("Session loaded from storage")
        else:
            logger.info("No existing session found")

    async def async_login(self) -> bool:
        """Login to My Verisure."""
        try:
            await self.client.connect()
            
            # Check if we have a valid session
            if self.client.is_session_valid():
                logger.info("Using existing valid session")
                return True
            
            # Perform login
            await self.client.login()
            
            # Save session after successful login
            session_file = os.path.join(self.storage_path, f"my_verisure_{self.client.user}.json")
            self.client.save_session(session_file)
            
            return True
        except MyVerisureAuthenticationError as ex:
            logger.error("Authentication failed for My Verisure: %s", ex)
            return False
        except MyVerisureError as ex:
            logger.error("Could not log in to My Verisure: %s", ex)
            return False

    async def async_update_data(self) -> dict:
        """Update data from My Verisure."""
        try:
            # Get all devices for the installation
            devices = await self.client.get_devices("")
            
            # Organize devices by type
            organized_data = {
                "alarm": self._get_alarm_state(devices),
                "cameras": self._filter_devices_by_type(devices, ["CAMERA", "SMARTCAMERA"]),
                "climate": self._filter_devices_by_type(devices, ["CLIMATE", "HUMIDITY", "TEMPERATURE"]),
                "door_window": self._filter_devices_by_type(devices, ["DOOR", "WINDOW", "PIR"]),
                "locks": self._filter_devices_by_type(devices, ["LOCK", "SMARTLOCK"]),
                "smart_plugs": self._filter_devices_by_type(devices, ["SMARTPLUG", "PLUG"]),
                "sensors": self._filter_devices_by_type(devices, ["SENSOR", "MOTION", "SMOKE", "WATER"]),
            }
            
            return organized_data
            
        except MyVerisureError as ex:
            logger.error("Error updating data: %s", ex)
            return {}

    def _get_alarm_state(self, devices: list) -> dict:
        """Extract alarm state from devices."""
        alarm_devices = self._filter_devices_by_type(devices, ["ALARM", "PANEL", "CONTROL"])
        
        if alarm_devices:
            alarm_device = list(alarm_devices.values())[0]
            return {
                "state": alarm_device.get("status", "UNKNOWN"),
                "device": alarm_device,
            }
        
        return {"state": "UNKNOWN", "device": None}

    def _filter_devices_by_type(self, devices: list, device_types: list) -> dict:
        """Filter devices by type and organize by device ID."""
        filtered_devices = {}
        
        for device in devices:
            device_type = device.get("type", "").upper()
            if any(dt in device_type for dt in device_types):
                device_id = device.get("id", device.get("name", "unknown"))
                filtered_devices[device_id] = device
        
        return filtered_devices

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator."""
        if self.client:
            await self.client.disconnect()


async def test_coordinator(user_id: str, password: str) -> None:
    """Prueba el coordinator simplificado."""
    logger.info("🧪 Iniciando prueba de coordinator...")
    logger.info(f"👤 User ID: {user_id}")
    logger.info(f"🔑 Password: {'*' * len(password)}")
    
    # Ensure storage directory exists
    storage_path = "test_storage"
    os.makedirs(storage_path, exist_ok=True)
    
    coordinator = SimpleCoordinator(user_id, password, storage_path)
    
    try:
        # Test login
        logger.info("🔐 Probando login...")
        login_success = await coordinator.async_login()
        
        if login_success:
            logger.info("✅ Login exitoso en coordinator")
            
            # Test data update
            logger.info("📊 Probando actualización de datos...")
            try:
                data = await coordinator.async_update_data()
                logger.info("✅ Datos obtenidos: %s", data)
            except Exception as e:
                logger.warning("⚠️  Error obteniendo datos (esperado sin queries implementadas): %s", e)
            
            # Test session persistence
            logger.info("🔄 Probando persistencia de sesión...")
            new_coordinator = SimpleCoordinator(user_id, password, storage_path)
            session_loaded = await new_coordinator.async_login()
            
            if session_loaded:
                logger.info("✅ Sesión persistida correctamente")
            else:
                logger.error("❌ Error al persistir sesión")
        else:
            logger.error("❌ Login falló en coordinator")
            
    except Exception as e:
        logger.error(f"❌ Error en coordinator: {e}")
        
    finally:
        # Cleanup
        logger.info("🧹 Limpiando...")
        await coordinator.async_shutdown()


def main():
    """Función principal."""
    print("🚀 My Verisure Simple Coordinator Test")
    print("=" * 45)
    
    # Verificar argumentos
    if len(sys.argv) != 3:
        print("Uso: python test_coordinator_simple.py <user_id> <password>")
        print("Ejemplo: python test_coordinator_simple.py 12345678A mi_password")
        print("\nNota: El user_id debe ser tu DNI/NIE (sin guiones)")
        sys.exit(1)
    
    user_id = sys.argv[1]
    password = sys.argv[2]
    
    print(f"👤 User ID: {user_id}")
    print(f"🔑 Password: {'*' * len(password)}")
    print()
    
    # Ejecutar prueba
    try:
        asyncio.run(test_coordinator(user_id, password))
    except KeyboardInterrupt:
        print("\n⏹️  Prueba interrumpida por el usuario")
    except Exception as e:
        logger.error(f"❌ Error ejecutando prueba: {e}")


if __name__ == "__main__":
    main() 