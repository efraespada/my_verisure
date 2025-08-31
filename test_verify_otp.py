#!/usr/bin/env python3
"""
Script para probar la verificación del código OTP.
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
        MyVerisureOTPError,
    )
except ImportError as e:
    logger.error(f"No se pudo importar el módulo api: {e}")
    logger.error("Asegúrate de estar en el directorio correcto del proyecto")
    sys.exit(1)


async def test_verify_otp(user_id: str, password: str, otp_code: str) -> None:
    """Prueba la verificación del código OTP."""
    logger.info("🧪 Iniciando prueba de verificación de OTP...")
    logger.info(f"👤 User ID: {user_id}")
    logger.info(f"🔑 Password: {'*' * len(password)}")
    logger.info(f"📱 OTP Code: {otp_code}")
    
    client = MyVerisureClient(user=user_id, password=password)
    
    try:
        # Conectar
        logger.info("📡 Conectando a la API...")
        await client.connect()
        logger.info("✅ Conexión establecida")
        
        # Intentar login (esto debería iniciar el flujo de validación de dispositivo)
        logger.info("🔐 Intentando login...")
        login_success = await client.login()
        
        if login_success:
            logger.info("✅ Login exitoso!")
            logger.info(f"🎫 Token: {client._hash}")
            logger.info(f"📊 Datos de sesión: {client._session_data}")
            
            # Check if we have OTP data
            if client._otp_data:
                logger.info("📱 Datos OTP disponibles:")
                logger.info(f"  Hash: {client._otp_data.get('otp_hash')}")
                
                # Get available phones
                phones = client.get_available_phones()
                logger.info(f"📞 Teléfonos disponibles: {len(phones)}")
                
                for phone in phones:
                    logger.info(f"  ID {phone.get('id')}: {phone.get('phone')}")
                
                # Select phone ID 1 specifically
                phone_id_1 = next((p for p in phones if p.get("id") == 1), None)
                if phone_id_1:
                    logger.info(f"📞 Seleccionando teléfono ID 1: {phone_id_1.get('phone')}")
                    
                    if client.select_phone(1):
                        logger.info("✅ Teléfono ID 1 seleccionado correctamente")
                        
                        # Send OTP to phone ID 1
                        otp_hash = client._otp_data.get("otp_hash")
                        if otp_hash:
                            logger.info("📤 Enviando OTP al teléfono ID 1...")
                            logger.info(f"🔑 Hash OTP: {otp_hash}")
                            
                            otp_sent = await client._send_otp(1, otp_hash)
                            
                            if otp_sent:
                                logger.info("✅ OTP enviado correctamente al teléfono ID 1")
                                logger.info("📱 Revisa tu teléfono (ID 1) para el SMS")
                                logger.info("💡 El SMS debería llegar en unos segundos")
                                
                                # Now verify the OTP code
                                logger.info("🔐 Verificando código OTP...")
                                logger.info(f"📱 Código OTP: {otp_code}")
                                
                                otp_verified = await client.verify_otp(otp_code)
                                
                                if otp_verified:
                                    logger.info("✅ OTP verificado correctamente!")
                                    logger.info(f"🎫 Token de autenticación: {client._hash[:50] + '...' if client._hash else 'None'}")
                                    logger.info("🚀 ¡Autenticación completa exitosa!")
                                else:
                                    logger.error("❌ Error verificando OTP")
                            else:
                                logger.error("❌ Error enviando OTP al teléfono ID 1")
                        else:
                            logger.error("❌ No hay hash OTP disponible")
                    else:
                        logger.error("❌ Error al seleccionar teléfono ID 1")
                else:
                    logger.error("❌ Teléfono ID 1 no encontrado en la lista")
                    logger.info("📞 Teléfonos disponibles:")
                    for phone in phones:
                        logger.info(f"  ID {phone.get('id')}: {phone.get('phone')}")
            else:
                logger.info("✅ Login completado sin OTP requerido")
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
    print("🚀 My Verisure OTP Verification Test")
    print("=" * 35)
    
    # Verificar argumentos
    if len(sys.argv) != 4:
        print("Uso: python test_verify_otp.py <user_id> <password> <otp_code>")
        print("Ejemplo: python test_verify_otp.py 12345678A mi_password 123456")
        print("\nNota:")
        print("- El user_id debe ser tu DNI/NIE (sin guiones)")
        print("- El otp_code es el código de 6 dígitos que recibiste por SMS")
        print("Este script enviará el OTP al teléfono ID 1 y luego verificará el código")
        sys.exit(1)
    
    user_id = sys.argv[1]
    password = sys.argv[2]
    otp_code = sys.argv[3]
    
    print(f"👤 User ID: {user_id}")
    print(f"🔑 Password: {'*' * len(password)}")
    print(f"📱 OTP Code: {otp_code}")
    print("📞 Teléfono objetivo: ID 1")
    print()
    
    # Ejecutar prueba
    try:
        asyncio.run(test_verify_otp(user_id, password, otp_code))
    except KeyboardInterrupt:
        print("\n⏹️  Prueba interrumpida por el usuario")
    except Exception as e:
        logger.error(f"❌ Error ejecutando prueba: {e}")


if __name__ == "__main__":
    main() 