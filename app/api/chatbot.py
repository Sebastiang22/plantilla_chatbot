"""Endpoints de la API del chatbot para manejar interacciones de chat.

Este módulo proporciona endpoints para interacciones de chat, incluyendo chat regular,
chat en streaming, gestión del historial de mensajes y limpieza del historial.
"""

import json
import uuid
from typing import List
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from core.config import settings
from core.langgraph.graph import LangGraphAgent
from core.limiter import limiter
from core.logging import logger
from schemas.chat import ChatRequest, ChatResponse, Message, StreamResponse, MessageResponse, ThreadResponse
from services.database import database_service

router = APIRouter()
agent = LangGraphAgent()

@router.post("/chat", response_model=MessageResponse)
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["chat"][0])
async def chat(
    request: Request,
    chat_request: ChatRequest,
    phone: str,
):
    """Procesa una solicitud de chat usando LangGraph.

    Args:
        request: Objeto de solicitud FastAPI para limitación de tasa
        chat_request: Solicitud de chat que contiene mensajes
        phone: Número de celular del usuario

    Returns:
        MessageResponse: Respuesta con solo el contenido del mensaje

    Raises:
        HTTPException: Si hay un error al procesar la solicitud
    """
    thread = None
    try:
        # Obtener o crear usuario usando el método del servicio
        user = await database_service.get_or_create_user(phone)
        
        # Obtener o crear thread usando el método del servicio
        thread = await database_service.get_or_create_thread(user.id)
            
        logger.info(
            "chat_request_received",
            thread_id=thread.id,
            user_id=user.id,
            message_count=len(chat_request.messages),
        )

        # Procesar la solicitud a través de LangGraph
        result = await agent.get_response(
            messages=chat_request.messages,
            session_id=thread.id,
            initial_state={"phone": phone}
        )

        logger.info("chat_request_processed", thread_id=thread.id)

        # Extraer solo el contenido del último mensaje del asistente
        if result and len(result) > 0:
            last_message = result[-1]
            if last_message.role == "assistant":
                return MessageResponse(content=last_message.content)
            else:
                return MessageResponse(content="No se pudo generar una respuesta")
        else:
            return MessageResponse(content="No se pudo generar una respuesta")

    except Exception as e:
        error_thread_id = thread.id if thread else "unknown"
        logger.error("chat_request_failed", thread_id=error_thread_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-thread")
async def create_thread(phone: str):
    """Crea un nuevo thread para el usuario especificado por su número de teléfono.

    Args:
        phone: Número de celular del usuario

    Returns:
        dict: Diccionario con el thread_id creado

    Raises:
        HTTPException: Si hay un error al crear el thread
    """
    try:
        # Obtener o crear usuario usando el método del servicio
        user = await database_service.get_or_create_user(phone)
        # Crear un nuevo thread_id único
        thread_id = str(uuid.uuid4())
        # Crear un nuevo thread para el usuario
        thread = await database_service.create_thread(thread_id, user.id)
        return {"thread_id": thread.id}
    except Exception as e:
        logger.error("create_thread_failed", phone=phone, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

