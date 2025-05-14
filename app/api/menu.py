from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from services.menu_service import MenuService
from services.openai_service import OpenAIService, get_openai_service
from models.menu_image import MenuType


class MenuImageRequest(BaseModel):
    """
    Modelo para la solicitud de actualización del menú
    """
    image_hex: str
    tipo_menu: MenuType = MenuType.EJECUTIVO


router = APIRouter(
    tags=["menu"],
    responses={404: {"description": "Not found"}},
)


@router.post("/extract", response_model=dict)
async def extract_menu_from_image(
    request: MenuImageRequest,
    menu_service: MenuService = Depends(),
    openai_service: OpenAIService = Depends(get_openai_service)
):
    """
    Recibe una imagen del menú en formato hexadecimal, extrae su contenido en formato JSON utilizando el servicio de OpenAI
    y actualiza la base de datos con la nueva imagen del menú.

    Args:
        request (MenuImageRequest): Solicitud con la imagen del menú en formato hexadecimal
        menu_service (MenuService): Servicio para manejar operaciones del menú
        openai_service (OpenAIService): Servicio de OpenAI para procesar la imagen

    Returns:
        dict: Respuesta con el resultado de la operación
    """
    try:
        # Guardar el menú en la base de datos
        success = await menu_service.insert_menu(
            image_hex=request.image_hex,
            tipo_menu=request.tipo_menu
        )
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Error al guardar el menú en la base de datos"
            )
        
        # Procesar la imagen con el servicio de OpenAI
        menu_data = await openai_service.extract_menu_from_image(
            image_hex=request.image_hex,
            prompt="Extrae toda la información del menú de esta imagen en formato JSON. "
                  "Los campos deben ser: 'name' para el nombre del plato, 'description' para la descripción, "
                  "'price' para el precio (como número), y 'category' para la categoría. "
                  "Ejemplo: {'menu': [{'name': 'Plato 1', 'description': 'Descripción 1', 'price': 20000, 'category': 'Menú Ejecutivo'}]}"
        )
        
        
        print("Datos recibidos de OpenAI:", menu_data)
        
        # Validar si el menú extraído está vacío
        if not menu_data.get("menu"):
            # Lanzar una excepción personalizada si la imagen no es un menú válido
            raise HTTPException(
                status_code=400,
                detail="Imagen de menú no válida"
            )
        
        # Procesar y guardar los productos del menú
        success = await menu_service.process_menu_data(menu_data)
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Error al procesar y guardar los productos del menú"
            )
        
        # Obtener el menú actualizado de la base de datos
        updated_menu = await menu_service.get_menu(tipo_menu=request.tipo_menu)
        
        return {
            "message": "Menú actualizado exitosamente",
            "menu_data": menu_data,
            "updated_menu": updated_menu
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar el menú: {str(e)}"
        ) 