#!/usr/bin/env python3
"""
Script para probar la recuperación de servicios de instalación de My Verisure.
"""

import asyncio
import logging
import sys
import os
from typing import Optional

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Añadir el directorio actual al path para importar el módulo api
sys.path.append('./custom_components/my_verisure')

try:
    from api.client import MyVerisureClient
    from api.exceptions import (
        MyVerisureAuthenticationError,
        MyVerisureConnectionError,
        MyVerisureError,
        MyVerisureOTPError,
    )
except ImportError as e:
    logger.error(f"No se pudo importar el módulo api: {e}")
    logger.error("Asegúrate de estar en el directorio correcto del proyecto")
    sys.exit(1)


async def test_installation_services(user_id: str, password: str, installation_id: str) -> None:
    """Prueba la recuperación de servicios de instalación."""
    logger.info("🧪 Iniciando prueba de servicios de instalación...")
    logger.info(f"👤 User ID: {user_id}")
    logger.info(f"🔑 Password: {'*' * len(password)}")
    logger.info(f"🏠 Installation ID: {installation_id}")
    
    client = MyVerisureClient(user=user_id, password=password)
    
    try:
        # Conectar
        logger.info("📡 Conectando a la API...")
        await client.connect()
        logger.info("✅ Conexión establecida")
        
        # Intentar login completo
        logger.info("🔐 Intentando login completo...")
        login_success = await client.login()
        
        if login_success:
            logger.info("✅ Login exitoso!")
            logger.info(f"🎫 Token: {client._hash[:50] + '...' if client._hash else 'None'}")
            
            # Obtener servicios de instalación
            logger.info(f"🏠 Obteniendo servicios para instalación {installation_id}...")
            services_data = await client.get_installation_services(installation_id)
            
            installation = services_data.get("installation", {})
            services = services_data.get("services", [])
            
            logger.info(f"✅ Se encontraron {len(services)} servicios")
            print("\n" + "="*60)
            print("🏠 SERVICIOS DE INSTALACIÓN")
            print("="*60)
            
            # Información básica de la instalación
            print(f"\n🏠 Instalación: {installation.get('alias', 'N/A')}")
            print(f"🆔 Número: {installation.get('numinst', 'N/A')}")
            print(f"📊 Estado: {installation.get('status', 'N/A')}")
            print(f"🛡️  Panel: {installation.get('panel', 'N/A')}")
            print(f"📱 SIM: {installation.get('sim', 'N/A')}")
            print(f"🎭 Rol: {installation.get('role', 'N/A')}")
            print(f"🔧 IBS: {installation.get('instIbs', 'N/A')}")
            print()
            
            # Servicios activos
            active_services = [s for s in services if s.get("active")]
            print(f"✅ Servicios activos ({len(active_services)}):")
            print("-" * 40)
            
            for service in active_services:
                service_id = service.get("idService", "N/A")
                service_request = service.get("request", "N/A")
                service_visible = "👁️" if service.get("visible") else "🙈"
                service_premium = "⭐" if service.get("isPremium") else ""
                service_bde = "💰" if service.get("bde") else ""
                service_cod_oper = "🔧" if service.get("codOper") else ""
                
                print(f"   {service_visible} {service_id}: {service_request} {service_premium}{service_bde}{service_cod_oper}")
                
                # Mostrar configuración genérica si existe
                generic_config = service.get("genericConfig")
                if generic_config and generic_config.get("attributes"):
                    for attr in generic_config["attributes"]:
                        key = attr.get("key", "N/A")
                        value = attr.get("value", "N/A")
                        print(f"      ⚙️  {key}: {value}")
                
                # Mostrar atributos si existen
                attributes = service.get("attributes", {}).get("attributes", [])
                if attributes:
                    for attr in attributes:
                        name = attr.get("name", "N/A")
                        value = attr.get("value", "N/A")
                        active = "✅" if attr.get("active") else "❌"
                        print(f"      {active} {name}: {value}")
            
            print()
            
            # Servicios inactivos
            inactive_services = [s for s in services if not s.get("active")]
            if inactive_services:
                print(f"❌ Servicios inactivos ({len(inactive_services)}):")
                print("-" * 40)
                for service in inactive_services:
                    service_id = service.get("idService", "N/A")
                    service_request = service.get("request", "N/A")
                    print(f"   ❌ {service_id}: {service_request}")
                print()
            
            # Capacidades
            capabilities = services_data.get("capabilities")
            if capabilities:
                print(f"🔐 Capacidades disponibles (token JWT)")
                print(f"   Token: {capabilities[:50] + '...' if capabilities else 'None'}")
            
        else:
            logger.error("❌ Login falló")
            
    except MyVerisureOTPError as e:
        logger.error(f"❌ Error OTP: {e}")
        logger.info("💡 El flujo OTP se inició correctamente, pero hubo un error")
        
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


def main():
    """Función principal."""
    print("🚀 My Verisure Installation Services Test")
    print("=" * 45)
    
    # Verificar argumentos
    if len(sys.argv) != 4:
        print("Uso: python test_installation_services.py <user_id> <password> <installation_id>")
        print("Ejemplo: python test_installation_services.py 12345678A mi_password 6220569")
        print("\nNota:")
        print("- El user_id debe ser tu DNI/NIE (sin guiones)")
        print("- El installation_id es el número de instalación (ej: 6220569)")
        print("Este script realizará el login completo y obtendrá los servicios de la instalación")
        sys.exit(1)
    
    user_id = sys.argv[1]
    password = sys.argv[2]
    installation_id = sys.argv[3]
    
    print(f"👤 User ID: {user_id}")
    print(f"🔑 Password: {'*' * len(password)}")
    print(f"🏠 Installation ID: {installation_id}")
    print()
    
    # Ejecutar prueba
    try:
        asyncio.run(test_installation_services(user_id, password, installation_id))
    except KeyboardInterrupt:
        print("\n⏹️  Prueba interrumpida por el usuario")
    except Exception as e:
        logger.error(f"❌ Error ejecutando prueba: {e}")


if __name__ == "__main__":
    main() 