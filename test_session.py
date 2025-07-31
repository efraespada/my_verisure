#!/usr/bin/env python3
"""
Script de prueba para el login de My Verisure con manejo de sesiones.
Este script te permite probar la autenticación y el manejo de cookies/sesiones.
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
    logger.error(f"No se pudo importar el módulo api: {e}")
    logger.error("Asegúrate de estar en el directorio correcto del proyecto")
    sys.exit(1)


async def test_session_management(user_id: str, password: str) -> None:
    """Prueba el login y manejo de sesiones con la API de My Verisure."""
    logger.info("🧪 Iniciando prueba de sesión...")
    logger.info(f"👤 User ID: {user_id}")
    logger.info(f"🔑 Password: {'*' * len(password)}")
    
    # Session file path
    session_file = f"sessions/my_verisure_{user_id}.json"
    
    client = MyVerisureClient(user=user_id, password=password)
    
    try:
        # Conectar
        logger.info("📡 Conectando a la API...")
        await client.connect()
        logger.info("✅ Conexión establecida")
        
        # Try to load existing session first
        logger.info("📂 Intentando cargar sesión existente...")
        if client.load_session(session_file):
            logger.info("✅ Sesión cargada desde archivo")
            
            if client.is_session_valid():
                logger.info("✅ Sesión válida, no necesitamos hacer login")
                logger.info(f"📊 Datos de sesión: {client._session_data}")
            else:
                logger.info("❌ Sesión expirada, necesitamos hacer login")
                await perform_login(client, password)
        else:
            logger.info("📂 No hay sesión existente, haciendo login...")
            await perform_login(client, password)
        
        # Save session
        logger.info("💾 Guardando sesión...")
        client.save_session(session_file)
        logger.info("✅ Sesión guardada")
        
        # Test session loading
        logger.info("🔄 Probando recarga de sesión...")
        new_client = MyVerisureClient(user=user_id, password=password)
        if new_client.load_session(session_file):
            logger.info("✅ Sesión recargada correctamente")
            logger.info(f"📊 Datos de sesión recargada: {new_client._session_data}")
        else:
            logger.error("❌ Error al recargar sesión")
            
    except MyVerisureAuthenticationError as e:
        logger.error(f"❌ Error de autenticación: {e}")
        logger.info("💡 Verifica tu User ID (DNI/NIE) y contraseña")
        
    except MyVerisureConnectionError as e:
        logger.error(f"❌ Error de conexión: {e}")
        logger.info("💡 Verifica tu conexión a internet y la URL de la API")
        
    except MyVerisureError as e:
        logger.error(f"❌ Error de My Verisure: {e}")
        
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        
    finally:
        # Desconectar
        logger.info("🔌 Desconectando...")
        await client.disconnect()
        logger.info("✅ Desconexión completada")


async def perform_login(client: MyVerisureClient, password: str) -> None:
    """Realizar el proceso de login."""
    logger.info("🔐 Intentando login...")
    success = await client.login()
    
    if success:
        logger.info("✅ Login exitoso!")
        logger.info(f"🎫 Token: {client._hash}")
        logger.info(f"📊 Datos de sesión: {client._session_data}")
        
        # Check for device authorization
        if client._session_data.get("needDeviceAuthorization"):
            logger.warning("⚠️  Se requiere autorización de dispositivo")
            logger.info("💡 Esto puede requerir pasos adicionales en la aplicación móvil")
    else:
        logger.error("❌ Login falló")


def main():
    """Función principal."""
    print("🚀 My Verisure Session Test")
    print("=" * 40)
    
    # Verificar argumentos
    if len(sys.argv) != 3:
        print("Uso: python test_session.py <user_id> <password>")
        print("Ejemplo: python test_session.py 12345678D mi_password")
        print("\nNota: El user_id debe ser tu DNI/NIE (sin guiones)")
        sys.exit(1)
    
    user_id = sys.argv[1]
    password = sys.argv[2]
    
    print(f"👤 User ID: {user_id}")
    print(f"🔑 Password: {'*' * len(password)}")
    print()
    
    # Ejecutar prueba
    try:
        asyncio.run(test_session_management(user_id, password))
    except KeyboardInterrupt:
        print("\n⏹️  Prueba interrumpida por el usuario")
    except Exception as e:
        logger.error(f"❌ Error ejecutando prueba: {e}")


if __name__ == "__main__":
    main() 