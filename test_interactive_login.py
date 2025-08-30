#!/usr/bin/env python3
"""
Script interactivo para el flujo completo de autenticación de My Verisure.
Guía al usuario paso a paso por el proceso de login, selección de teléfono y verificación OTP.
Usa la nueva arquitectura con casos de uso y repositorios.
"""

import asyncio
import logging
import sys
import os
import json
import getpass
from typing import Optional

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Añadir el directorio actual al path para importar el módulo
sys.path.append('./custom_components/my_verisure')

try:
    from dependency_injection.providers import setup_dependencies, get_auth_use_case, get_installation_use_case, clear_dependencies
    from api.exceptions import (
        MyVerisureAuthenticationError,
        MyVerisureConnectionError,
        MyVerisureError,
        MyVerisureOTPError,
    )
except ImportError as e:
    logger.error(f"No se pudo importar los módulos: {e}")
    logger.error("Asegúrate de estar en el directorio correcto del proyecto")
    sys.exit(1)


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


def get_user_credentials() -> tuple[str, str]:
    """Solicita las credenciales del usuario."""
    print_header("MY VERISURE - AUTENTICACIÓN INTERACTIVA")
    
    print("👤 Ingresa tus credenciales de My Verisure:")
    print()
    
    # Solicitar User ID (DNI/NIE)
    while True:
        user_id = input("📋 User ID (DNI/NIE): ").strip()
        if user_id:
            break
        print_error("El User ID es obligatorio")
    
    # Solicitar contraseña
    while True:
        password = getpass.getpass("🔑 Contraseña: ").strip()
        if password:
            break
        print_error("La contraseña es obligatoria")
    
    return user_id, password


def select_phone(phones: list[dict]) -> Optional[int]:
    """Permite al usuario seleccionar un teléfono."""
    print_header("SELECCIÓN DE TELÉFONO")
    
    print("📱 Teléfonos disponibles para recibir el código OTP:")
    print()
    
    for i, phone in enumerate(phones):
        phone_id = phone.get("id", i)
        phone_number = phone.get("phone", "Desconocido")
        print(f"  {i+1}. ID {phone_id}: {phone_number}")
    
    print()
    
    while True:
        try:
            choice = input("Selecciona el número de teléfono (1, 2, ...): ").strip()
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(phones):
                selected_phone = phones[choice_num - 1]
                phone_id = selected_phone.get("id")
                phone_number = selected_phone.get("phone")
                
                print_success(f"Teléfono seleccionado: ID {phone_id} - {phone_number}")
                return phone_id
            else:
                print_error(f"Por favor selecciona un número entre 1 y {len(phones)}")
                
        except ValueError:
            print_error("Por favor ingresa un número válido")
        except KeyboardInterrupt:
            print("\n⏹️  Selección cancelada")
            return None


def get_otp_code() -> Optional[str]:
    """Solicita el código OTP al usuario."""
    print_header("VERIFICACIÓN OTP")
    
    print("📱 Revisa tu teléfono para el código OTP que acabas de recibir.")
    print("💡 El código suele ser de 6 dígitos.")
    print()
    
    while True:
        try:
            otp_code = input("🔢 Código OTP: ").strip()
            if otp_code:
                # Validar que sea numérico
                if otp_code.isdigit():
                    print_success(f"Código OTP ingresado: {otp_code}")
                    return otp_code
                else:
                    print_error("El código OTP debe contener solo números")
            else:
                print_error("El código OTP es obligatorio")
                
        except KeyboardInterrupt:
            print("\n⏹️  Entrada cancelada")
            return None


async def interactive_login() -> None:
    """Flujo interactivo completo de autenticación usando casos de uso."""
    
    try:
        # Paso 1: Obtener credenciales
        user_id, password = get_user_credentials()
        
        # Paso 2: Configurar dependencias
        print_header("CONFIGURACIÓN DE DEPENDENCIAS")
        print_info("Configurando sistema de dependencias...")
        setup_dependencies(username=user_id, password=password)
        print_success("Dependencias configuradas")
        print()
        
        # Paso 3: Obtener casos de uso
        auth_use_case = get_auth_use_case()
        installation_use_case = get_installation_use_case()
        
        # Paso 4: Conectar y hacer login
        print_header("CONEXIÓN Y LOGIN")
        print_info("Iniciando proceso de autenticación...")
        
        try:
            auth_result = await auth_use_case.login(username=user_id, password=password)
            
            if auth_result.success:
                print_success("Login inicial exitoso")
                print_info(f"Token de autenticación: {auth_result.hash[:50] + '...' if auth_result.hash else 'None'}")
                
                # Si llegamos aquí sin excepción, no se requiere OTP
                print_success("¡Autenticación completada sin OTP requerido!")
                
            else:
                print_error(f"Login falló: {auth_result.message}")
                return
                
        except MyVerisureOTPError:
            # Se requiere OTP, continuar con el flujo
            print_info("Se requiere verificación OTP - continuando con el flujo...")
            
            # Paso 5: Mostrar teléfonos disponibles y seleccionar
            phones = auth_use_case.get_available_phones()
            if not phones:
                print_error("No hay teléfonos disponibles para OTP")
                return
            
            selected_phone_id = select_phone(phones)
            if selected_phone_id is None:
                return
            
            # Paso 6: Enviar OTP
            print_header("ENVÍO DE OTP")
            print_info(f"Enviando código OTP al teléfono ID {selected_phone_id}...")
            
            # Para simplificar, usamos valores por defecto
            record_id = selected_phone_id
            otp_hash = "default_hash"  # En una implementación real, esto vendría del error OTP
            
            otp_sent = await auth_use_case.send_otp(record_id, otp_hash)
            if not otp_sent:
                print_error("Error enviando el código OTP")
                return
            
            print_success("Código OTP enviado correctamente")
            print_info("Revisa tu teléfono para el SMS")
            
            # Paso 7: Verificar OTP
            otp_code = get_otp_code()
            if otp_code is None:
                return
            
            print_info("Verificando código OTP...")
            otp_verified = await auth_use_case.verify_otp(otp_code)
            
            if not otp_verified:
                print_error("Error verificando el código OTP")
                return
                
            print_header("¡AUTENTICACIÓN COMPLETADA!")
            print_success("¡Código OTP verificado correctamente!")
            print_success("¡Autenticación completa exitosa!")
            print_info("Ya puedes usar la API de My Verisure")
        
        # Paso 8: Obtener instalaciones (se ejecuta tanto con OTP como sin OTP)
        print_header("RECUPERACIÓN DE INSTALACIONES")
        print_info("Obteniendo información de las instalaciones...")
        
        try:
            installations = await installation_use_case.get_installations()
            
            if installations:
                print_success(f"Se encontraron {len(installations)} instalación(es)")
                print()
                
                for i, installation in enumerate(installations):
                    print(f"🏠 Instalación {i+1}:")
                    print(f"   📍 Alias: {installation.alias}")
                    print(f"   🆔 Número: {installation.numinst}")
                    print(f"   🏠 Tipo: {installation.type}")
                    print(f"   👤 Propietario: {installation.name} {installation.surname}")
                    print(f"   📍 Dirección: {installation.address}")
                    print(f"   🏙️  Ciudad: {installation.city} ({installation.postcode})")
                    print(f"   📞 Teléfono: {installation.phone}")
                    print(f"   📧 Email: {installation.email}")
                    print(f"   🎭 Rol: {installation.role}")
                    print()
            else:
                print_info("No se encontraron instalaciones")
                
        except Exception as e:
            print_error(f"Error obteniendo instalaciones: {e}")
            
        # Paso 9: Obtener servicios de todas las instalaciones
        if installations:
            print_header("SERVICIOS DE TODAS LAS INSTALACIONES")
            print_info(f"Procesando {len(installations)} instalación(es)...")
            print()
            
            for i, installation in enumerate(installations):
                installation_id = installation.numinst
                installation_alias = installation.alias
                
                print(f"🏠 Procesando instalación {i+1}/{len(installations)}: {installation_alias}")
                print(f"🆔 Número: {installation_id}")
                print()
                
                try:
                    services_data = await installation_use_case.get_installation_services(installation_id)
                    
                    # Debug: Check the success value
                    print(f"DEBUG: services_data.success = {services_data.success}")
                    print(f"DEBUG: services_data.message = {services_data.message}")
                    print(f"DEBUG: services_data.services count = {len(services_data.services) if services_data.services else 0}")
                    
                    if services_data.success:
                        services = services_data.services
                        
                        print_success(f"Se encontraron {len(services)} servicios")
                        
                        # Mostrar información básica de la instalación
                        installation_info = services_data.installation_data or {}
                        print(f"   📊 Estado: {installation_info.get('status', 'N/A')}")
                        print(f"   🛡️  Panel: {installation_info.get('panel', 'N/A')}")
                        print(f"   📱 SIM: {installation_info.get('sim', 'N/A')}")
                        print(f"   🎭 Rol: {installation_info.get('role', 'N/A')}")
                        print(f"   🔧 IBS: {installation_info.get('instIbs', 'N/A')}")
                        print()
                        
                        # Mostrar servicios activos
                        active_services = [s for s in services if s.active]
                        print(f"   ✅ Servicios activos ({len(active_services)}):")
                        for service in active_services:
                            service_id = service.id_service
                            service_request = service.request or "N/A"
                            service_visible = "👁️" if service.visible else "🙈"
                            service_premium = "⭐" if service.is_premium else ""
                            service_bde = "💰" if service.bde else ""
                            print(f"      {service_visible} {service_id}: {service_request} {service_premium}{service_bde}")
                        
                        # Mostrar servicios inactivos (solo si hay pocos)
                        inactive_services = [s for s in services if not s.active]
                        if inactive_services and len(inactive_services) <= 5:
                            print(f"   ❌ Servicios inactivos ({len(inactive_services)}):")
                            for service in inactive_services:
                                service_id = service.id_service
                                service_request = service.request or "N/A"
                                print(f"      ❌ {service_id}: {service_request}")
                        
                        # Capacidades
                        capabilities = services_data.capabilities
                        if capabilities:
                            print(f"   🔐 Capacidades: {capabilities[:30] + '...' if capabilities else 'None'}")
                        
                    else:
                        print_error(f"Error obteniendo servicios: {services_data.message}")
                        
                except Exception as e:
                    print_error(f"Error obteniendo servicios para instalación {installation_id}: {e}")
                
                # Separador entre instalaciones
                if i < len(installations) - 1:
                    print("\n" + "-" * 60)
                    print()
            
            print_header("RESUMEN FINAL")
            print_success(f"Procesamiento completado para {len(installations)} instalación(es)")
            print_info("Todas las instalaciones han sido procesadas correctamente")
            
    except MyVerisureOTPError as e:
        print_error(f"Error OTP: {e}")
        print_info("El flujo OTP se inició correctamente, pero hubo un error en la verificación")
        
    except MyVerisureAuthenticationError as e:
        print_error(f"Error de autenticación: {e}")
        print_info("Verifica tu User ID (DNI/NIE) y contraseña")
        
    except MyVerisureConnectionError as e:
        print_error(f"Error de conexión: {e}")
        print_info("Verifica tu conexión a internet y la URL de la API")
        
    except MyVerisureError as e:
        print_error(f"Error de My Verisure: {e}")
        
    except KeyboardInterrupt:
        print("\n⏹️  Proceso interrumpido por el usuario")
        
    except Exception as e:
        print_error(f"Error inesperado: {e}")
        
    finally:
        # Limpiar dependencias
        print_info("Limpiando dependencias...")
        clear_dependencies()
        print_success("Dependencias limpiadas")


def main():
    """Función principal."""
    print("🚀 My Verisure - Autenticación Interactiva (Nueva Arquitectura)")
    print("=" * 60)
    print("Este script te guiará paso a paso por el proceso de autenticación")
    print("de My Verisure usando la nueva arquitectura con casos de uso.")
    print()
    
    # Ejecutar flujo interactivo
    try:
        asyncio.run(interactive_login())
    except KeyboardInterrupt:
        print("\n⏹️  Proceso interrumpido por el usuario")
    except Exception as e:
        print_error(f"Error ejecutando el flujo: {e}")


if __name__ == "__main__":
    main() 