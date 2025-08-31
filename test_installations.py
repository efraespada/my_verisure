#!/usr/bin/env python3
"""
Script para probar la recuperación de instalaciones de My Verisure.
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


async def test_installations(user_id: str, password: str) -> None:
    """Prueba la recuperación de instalaciones."""
    logger.info("🧪 Iniciando prueba de recuperación de instalaciones...")
    logger.info(f"👤 User ID: {user_id}")
    logger.info(f"🔑 Password: {'*' * len(password)}")
    
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
            
            # Obtener instalaciones
            logger.info("🏠 Obteniendo instalaciones...")
            installations = await client.get_installations()
            
            if installations:
                logger.info(f"✅ Se encontraron {len(installations)} instalación(es)")
                print("\n" + "="*60)
                print("🏠 INSTALACIONES ENCONTRADAS")
                print("="*60)
                
                for i, installation in enumerate(installations):
                    print(f"\n🏠 Instalación {i+1}:")
                    print(f"   📍 Alias: {installation.get('alias', 'N/A')}")
                    print(f"   🆔 Número: {installation.get('numinst', 'N/A')}")
                    print(f"   🏠 Tipo: {installation.get('type', 'N/A')}")
                    print(f"   👤 Propietario: {installation.get('name', 'N/A')} {installation.get('surname', 'N/A')}")
                    print(f"   📍 Dirección: {installation.get('address', 'N/A')}")
                    print(f"   🏙️  Ciudad: {installation.get('city', 'N/A')} ({installation.get('postcode', 'N/A')})")
                    print(f"   📞 Teléfono: {installation.get('phone', 'N/A')}")
                    print(f"   📧 Email: {installation.get('email', 'N/A')}")
                    print(f"   🎭 Rol: {installation.get('role', 'N/A')}")
                    print(f"   💰 Deuda: {'Sí' if installation.get('due') else 'No'}")
                    print(f"   🛡️  Panel: {installation.get('panel', 'N/A')}")
                
                # Obtener servicios de todas las instalaciones
                print("\n" + "="*60)
                print("🔧 SERVICIOS DE TODAS LAS INSTALACIONES")
                print("="*60)
                
                for i, installation_info in enumerate(installations):
                    installation_id = installation_info.get("numinst")
                    installation_alias = installation_info.get("alias", "N/A")
                    
                    if installation_id:
                        print(f"\n🏠 Procesando instalación {i+1}/{len(installations)}: {installation_alias}")
                        print(f"🆔 Número: {installation_id}")
                        
                        try:
                            services_data = await client.get_installation_services(installation_id)
                            
                            installation = services_data.get("installation", {})
                            services = services_data.get("services", [])
                            
                            logger.info(f"✅ Se encontraron {len(services)} servicios para instalación {installation_id}")
                            
                            # Información básica de la instalación
                            print(f"   📊 Estado: {installation.get('status', 'N/A')}")
                            print(f"   🛡️  Panel: {installation.get('panel', 'N/A')}")
                            print(f"   📱 SIM: {installation.get('sim', 'N/A')}")
                            print(f"   🎭 Rol: {installation.get('role', 'N/A')}")
                            print(f"   🔧 IBS: {installation.get('instIbs', 'N/A')}")
                            
                            # Servicios activos
                            active_services = [s for s in services if s.get("active")]
                            print(f"   ✅ Servicios activos ({len(active_services)}):")
                            for service in active_services:
                                service_id = service.get("idService", "N/A")
                                service_request = service.get("request", "N/A")
                                service_visible = "👁️" if service.get("visible") else "🙈"
                                service_premium = "⭐" if service.get("isPremium") else ""
                                service_bde = "💰" if service.get("bde") else ""
                                print(f"      {service_visible} {service_id}: {service_request} {service_premium}{service_bde}")
                            
                            # Capacidades
                            capabilities = services_data.get("capabilities")
                            if capabilities:
                                print(f"   🔐 Capacidades: {capabilities[:30] + '...' if capabilities else 'None'}")
                            
                        except Exception as e:
                            logger.error(f"❌ Error obteniendo servicios para instalación {installation_id}: {e}")
                            print(f"   ❌ Error: {e}")
                        
                        # Separador entre instalaciones
                        if i < len(installations) - 1:
                            print("\n" + "-" * 60)
                
                print("\n" + "="*60)
                print("✅ RESUMEN FINAL")
                print("="*60)
                print(f"🏠 Total de instalaciones procesadas: {len(installations)}")
                print("🔧 Todas las instalaciones han sido procesadas correctamente")
            else:
                logger.info("ℹ️  No se encontraron instalaciones")
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
    print("🚀 My Verisure Installations Test")
    print("=" * 35)
    
    # Verificar argumentos
    if len(sys.argv) != 3:
        print("Uso: python test_installations.py <user_id> <password>")
        print("Ejemplo: python test_installations.py 12345678A mi_password")
        print("\nNota: El user_id debe ser tu DNI/NIE (sin guiones)")
        print("Este script realizará el login completo y obtendrá las instalaciones")
        sys.exit(1)
    
    user_id = sys.argv[1]
    password = sys.argv[2]
    
    print(f"👤 User ID: {user_id}")
    print(f"🔑 Password: {'*' * len(password)}")
    print()
    
    # Ejecutar prueba
    try:
        asyncio.run(test_installations(user_id, password))
    except KeyboardInterrupt:
        print("\n⏹️  Prueba interrumpida por el usuario")
    except Exception as e:
        logger.error(f"❌ Error ejecutando prueba: {e}")


if __name__ == "__main__":
    main() 