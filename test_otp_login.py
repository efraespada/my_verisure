#!/usr/bin/env python3
"""
Script de prueba para el login de My Verisure con OTP.
Este script prueba el flujo completo de autenticación de dos factores.
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
sys.path.append('.')

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


async def test_otp_login(user_id: str, password: str) -> None:
    """Prueba el login con OTP de My Verisure."""
    logger.info("🧪 Iniciando prueba de login con OTP...")
    logger.info(f"👤 User ID: {user_id}")
    logger.info(f"🔑 Password: {'*' * len(password)}")
    
    client = MyVerisureClient(user=user_id, password=password)
    
    try:
        # Conectar
        logger.info("📡 Conectando a la API...")
        await client.connect()
        logger.info("✅ Conexión establecida")
        
        # Intentar login (esto debería iniciar el flujo OTP)
        logger.info("🔐 Intentando login...")
        login_success = await client.login()
        
        if login_success:
            logger.info("✅ Login exitoso!")
            logger.info(f"🎫 Token: {client._token}")
            logger.info(f"📊 Datos de sesión: {client._session_data}")
            
            # Check if we have OTP data
            if client._otp_data:
                logger.info("📱 Datos OTP disponibles:")
                logger.info(f"  Hash: {client._otp_data.get('otp_hash')}")
                logger.info(f"  Teléfonos: {client._otp_data.get('phones')}")
                
                # Ask user for OTP code
                print("\n" + "="*50)
                print("📱 VERIFICACIÓN OTP REQUERIDA")
                print("="*50)
                print("Se ha enviado un SMS a tu teléfono.")
                print("Por favor, introduce el código que recibiste:")
                
                try:
                    otp_code = input("Código OTP: ").strip()
                    if otp_code:
                        logger.info("🔍 Verificando código OTP...")
                        otp_verified = await client.verify_otp(otp_code)
                        
                        if otp_verified:
                            logger.info("✅ Código OTP verificado correctamente")
                            logger.info("🎉 Autenticación completa exitosa!")
                        else:
                            logger.error("❌ Verificación OTP falló")
                    else:
                        logger.warning("⚠️  No se introdujo código OTP")
                except KeyboardInterrupt:
                    logger.info("⏹️  Verificación OTP cancelada por el usuario")
                except Exception as e:
                    logger.error(f"❌ Error durante verificación OTP: {e}")
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
    print("🚀 My Verisure OTP Login Test")
    print("=" * 35)
    
    # Verificar argumentos
    if len(sys.argv) != 3:
        print("Uso: python test_otp_login.py <user_id> <password>")
        print("Ejemplo: python test_otp_login.py 16633776S mi_password")
        print("\nNota: El user_id debe ser tu DNI/NIE (sin guiones)")
        print("Este script probará el flujo completo de autenticación con OTP")
        sys.exit(1)
    
    user_id = sys.argv[1]
    password = sys.argv[2]
    
    print(f"👤 User ID: {user_id}")
    print(f"🔑 Password: {'*' * len(password)}")
    print()
    
    # Ejecutar prueba
    try:
        asyncio.run(test_otp_login(user_id, password))
    except KeyboardInterrupt:
        print("\n⏹️  Prueba interrumpida por el usuario")
    except Exception as e:
        logger.error(f"❌ Error ejecutando prueba: {e}")


if __name__ == "__main__":
    main() 