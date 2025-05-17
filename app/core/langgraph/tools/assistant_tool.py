import os
import aiohttp
import json
from langchain_core.tools import tool
from services.menu_service import menu_service
from core.config import settings

# Usar la URL de Baileys desde la configuración
# BAILEYS_SERVER_URL = os.getenv("BAILEYS_SERVER_URL", "http://198.244.188.104:3001")

@tool
async def send_menu_images(phone: str) -> dict:
    """
    Obtiene todas las imágenes del menú y las envía al cliente a través de WhatsApp.
    
    Args:
        phone: Número de teléfono del cliente
        
    Returns:
        dict: Resultado de la operación con mensaje de éxito o error
    """
    try:
        # Obtener todas las imágenes del menú
        menu_images = await menu_service.get_menu()
        
        if not menu_images:
            return {
                "message": "No hay imágenes de menú disponibles",
                "error": True
            }
            
        # Enviar cada imagen al cliente
        async with aiohttp.ClientSession() as session:
            for menu_image in menu_images:
                # Verificar que la imagen en hexadecimal no esté vacía
                if not menu_image.image_hex:
                    print(f"Error: La imagen del menú {menu_image.tipo_menu.value} está vacía")
                    continue

                # Preparar los datos para enviar en el formato que espera el endpoint
                payload = {
                    "phone": phone,
                    "imageHex": menu_image.image_hex,
                    "caption": f"Menú {menu_image.tipo_menu.value}"
                }
                
                print(f"\nEnviando imagen del menú {menu_image.tipo_menu.value}...")
                print(f"Payload: {json.dumps(payload, indent=2)}")
                
                # Enviar la imagen
                async with session.post(
                    f"{settings.BAILEYS_SERVER_URL}/api/send-images",
                    json=payload,
                    headers={
                        "Content-Type": "application/json"
                    }
                ) as response:
                    response_text = await response.text()
                    print(f"Respuesta del servidor: {response_text}")
                    print(f"Status code: {response.status}")
                    
                    if not response.ok:
                        return {
                            "message": f"Error al enviar imagen: {response_text}",
                            "error": True
                        }
        
        return {
            "message": "Imágenes del menú enviadas exitosamente",
            "error": False
        }
        
    except Exception as e:
        print(f"Error al enviar imágenes del menú: {str(e)}")
        return {
            "message": f"Error al enviar imágenes del menú: {str(e)}",
            "error": True
        }

@tool
def send_location_tool(phone: str) -> str:
    """
    Envía la ubicación del restaurante al cliente.

    Parámetros:
        phone (str): ID del usuario (número de teléfono) al que se enviará la ubicación.

    Retorna:
        str: Mensaje de confirmación si el envío se realiza con éxito, o mensaje de error en caso contrario.
    """
    import asyncio
    async def _send():
        print(f"\033[92m\nsend_location_tool activada\033[0m")
        try:
            # Definir la ubicación del restaurante
            location_data = {
                "number": phone
            }

            # Hacer la solicitud al endpoint para enviar la ubicación
            async with aiohttp.ClientSession() as session:
                async with session.post(f'{settings.BAILEYS_SERVER_URL}/api/send-location', json=location_data) as response:
                    if response.status == 200:
                        return "Ubicación del restaurante enviada correctamente."
                    else:
                        try:
                            error_msg = (await response.json()).get('error', 'Error desconocido')
                        except Exception:
                            error_msg = await response.text()
                        return f"Error al enviar la ubicación: {error_msg}"
        except Exception as e:
            return f"Error al enviar la ubicación: {str(e)}"
    return asyncio.run(_send()) 