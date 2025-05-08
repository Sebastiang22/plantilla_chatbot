import base64
import json
from typing import Dict, Any, Optional

from openai import OpenAI

from core.config import settings


class OpenAIService:
    """
    Servicio para interactuar con la API de OpenAI
    """
    def __init__(self):
        """
        Inicializa el cliente de OpenAI con la API key desde la configuración de `core.config`.
        """
        try:
            self.client = OpenAI(api_key=settings.LLM_API_KEY)
            self.model = settings.LLM_MODEL
            print(f"Servicio OpenAI inicializado con modelo: {self.model}")
        except Exception as e:
            print(f"Error al inicializar el servicio OpenAI: {e}")
            raise

    async def extract_menu_from_image(
        self,
        image_hex: Optional[str] = None,
        prompt: str = (
            "Extrae toda la información del menú de esta imagen en formato JSON. "
            "Incluye nombres de platos, descripciones, precios y categorías."
        ),
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        Extrae información estructurada del menú de una imagen usando la API de visión de OpenAI.

        Args:
            image_hex (Optional[str]): Imagen en formato hexadecimal
            prompt (str): Prompt para guiar la extracción de información
            model (Optional[str]): Modelo a utilizar, si no se especifica se usa el modelo por defecto
            max_tokens (int): Número máximo de tokens en la respuesta
            temperature (float): Temperatura para la generación de texto

        Returns:
            Dict[str, Any]: Información extraída del menú en formato JSON

        Raises:
            ValueError: Si no se proporciona una imagen válida
            Exception: Si ocurre un error durante el proceso
        """
        try:
            model_to_use = model or self.model

            if image_hex is not None:
                image_bytes = bytes.fromhex(image_hex)
                b64 = base64.b64encode(image_bytes).decode()
                image_content = {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                }
            else:
                raise ValueError("No se encontró ninguna fuente de imagen válida.")

            messages = [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    image_content
                ]
            }]

            params = {
                "model": model_to_use,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "response_format": {"type": "json_object"}
            }

            resp = self.client.chat.completions.create(**params)
            text = resp.choices[0].message.content

            try:
                menu = json.loads(text)
            except json.JSONDecodeError as e:
                menu = {"error": "No se pudo parsear JSON", "raw": text}

            return menu

        except Exception as e:
            raise


# Para inyección en FastAPI
async def get_openai_service() -> OpenAIService:
    """
    Función para inyección de dependencias en FastAPI.
    
    Returns:
        OpenAIService: Instancia del servicio OpenAI
    """
    return OpenAIService() 