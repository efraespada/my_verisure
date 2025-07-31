#!/usr/bin/env python3
"""
Script de prueba para la validación de dispositivo y obtención de teléfonos OTP.
Este script prueba la primera fase del 2FA.
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


async def test_device_validation(user_id: str, password: str) -> None:
    """Prueba la validación de dispositivo y obtención de teléfonos OTP."""
    logger.info("🧪 Iniciando prueba de validación de dispositivo...")
    logger.info(f"👤 User ID: {user_id}")
    logger.info(f"🔑 Password: {'*' * len(password)}")
    
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
                
                # Show phone selection
                print("\n" + "="*50)
                print("📱 TELÉFONOS DISPONIBLES PARA OTP")
                print("="*50)
                for phone in phones:
                    print(f"ID {phone.get('id')}: {phone.get('phone')}")
                
                print("\nSelecciona un teléfono para enviar el OTP:")
                try:
                    phone_id = int(input("ID del teléfono: ").strip())
                    
                    if client.select_phone(phone_id):
                        logger.info("✅ Teléfono seleccionado correctamente")
                        
                        # Send OTP
                        otp_hash = client._otp_data.get("otp_hash")
                        if otp_hash:
                            logger.info("📤 Enviando OTP...")
                            otp_sent = await client._send_otp(phone_id, otp_hash)
                            
                            if otp_sent:
                                logger.info("✅ OTP enviado correctamente")
                                logger.info("📱 Revisa tu teléfono para el SMS")
                            else:
                                logger.error("❌ Error enviando OTP")
                        else:
                            logger.error("❌ No hay hash OTP disponible")
                    else:
                        logger.error(f"❌ Teléfono ID {phone_id} no encontrado")
                        
                except ValueError:
                    logger.error("❌ ID de teléfono inválido")
                except KeyboardInterrupt:
                    logger.info("⏹️  Selección cancelada por el usuario")
                except Exception as e:
                    logger.error(f"❌ Error durante selección: {e}")
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
    print("🚀 My Verisure Device Validation Test")
    print("=" * 40)
    
    # Verificar argumentos
    if len(sys.argv) != 3:
        print("Uso: python test_device_validation.py <user_id> <password>")
        print("Ejemplo: python test_device_validation.py 16633776S mi_password")
        print("\nNota: El user_id debe ser tu DNI/NIE (sin guiones)")
        print("Este script probará la validación de dispositivo y mostrará los teléfonos disponibles")
        sys.exit(1)
    
    user_id = sys.argv[1]
    password = sys.argv[2]
    
    print(f"👤 User ID: {user_id}")
    print(f"🔑 Password: {'*' * len(password)}")
    print()
    
    # Ejecutar prueba
    try:
        asyncio.run(test_device_validation(user_id, password))
    except KeyboardInterrupt:
        print("\n⏹️  Prueba interrumpida por el usuario")
    except Exception as e:
        logger.error(f"❌ Error ejecutando prueba: {e}")


if __name__ == "__main__":
    main() 