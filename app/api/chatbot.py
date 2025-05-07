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
from schemas.chat import ChatRequest, ChatResponse, Message, StreamResponse, MessageResponse
from services.database import database_service

router = APIRouter()
agent = LangGraphAgent()

async def get_or_create_user(phone: str) -> "User":
    """Obtiene un usuario por su número de teléfono o lo crea si no existe.
    
    Args:
        phone: Número de teléfono del usuario
        
    Returns:
        User: Usuario encontrado o creado
        
    Raises:
        HTTPException: Si hay un error al buscar o crear el usuario
    """
    try:
        user = await database_service.get_user_by_phone(phone)
        if not user:
            logger.info("user_not_found_creating_new", phone=phone)
            user = await database_service.create_user(name="Usuario", phone=phone)
            logger.info("user_created_successfully", user_id=user.id, phone=phone)
        else:
            logger.info("user_found", user_id=user.id, phone=phone)
        return user
    except Exception as e:
        logger.error("user_operation_failed", phone=phone, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al procesar usuario: {str(e)}")

async def get_or_create_thread(user_id: int) -> "Thread":
    """Obtiene el último thread del usuario o crea uno nuevo.
    
    Args:
        user_id: ID del usuario
        
    Returns:
        Thread: Thread encontrado o creado
        
    Raises:
        HTTPException: Si hay un error al buscar o crear el thread
    """
    try:
        thread = await database_service.get_latest_thread(user_id)
        if not thread:
            thread_id = str(uuid.uuid4())
            thread = await database_service.create_thread(thread_id, user_id)
            logger.info("new_thread_created", thread_id=thread.id, user_id=user_id)
        else:
            logger.info("existing_thread_found", thread_id=thread.id, user_id=user_id)
        return thread
    except Exception as e:
        logger.error("thread_operation_failed", user_id=user_id, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al procesar thread: {str(e)}")

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
        # Obtener o crear usuario
        user = await get_or_create_user(phone)
        
        # Obtener o crear thread
        thread = await get_or_create_thread(user.id)
            
        logger.info(
            "chat_request_received",
            thread_id=thread.id,
            user_id=user.id,
            message_count=len(chat_request.messages),
        )

        # Procesar la solicitud a través de LangGraph
        result = await agent.get_response(chat_request.messages, thread.id)

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

@router.post("/chat/stream")
@limiter.limit(settings.RATE_LIMIT_ENDPOINTS["chat_stream"][0])
async def chat_stream(
    request: Request,
    chat_request: ChatRequest,
    phone: str,
):
    """Procesa una solicitud de chat usando LangGraph con respuesta en streaming.
    
    Args:
        request: Objeto de solicitud FastAPI para limitación de tasa
        chat_request: Solicitud de chat que contiene mensajes
        phone: Número de celular del usuario
        
    Returns:
        StreamingResponse: Respuesta en streaming del chat
        
    Raises:
        HTTPException: Si hay un error al procesar la solicitud
    """
    thread = None
    try:
        # Obtener o crear usuario
        user = await get_or_create_user(phone)
        
        # Obtener o crear thread
        thread = await get_or_create_thread(user.id)
            
        logger.info(
            "stream_chat_request_received",
            thread_id=thread.id,
            user_id=user.id,
            message_count=len(chat_request.messages),
        )

        async def event_generator():
            """Genera eventos de streaming.
            
            Yields:
                str: Eventos del servidor en formato JSON
                
            Raises:
                Exception: Si hay un error durante el streaming
            """
            try:
                full_response = ""
                async for chunk in agent.get_stream_response(
                    chat_request.messages, thread.id
                ):
                    full_response += chunk
                    response = StreamResponse(content=chunk, done=False)
                    yield f"data: {json.dumps(response.model_dump())}\n\n"

                # Enviar mensaje final indicando completitud
                final_response = StreamResponse(content="", done=True)
                yield f"data: {json.dumps(final_response.model_dump())}\n\n"

            except Exception as e:
                logger.error(
                    "stream_chat_request_failed",
                    thread_id=thread.id,
                    error=str(e),
                    exc_info=True,
                )
                error_response = StreamResponse(content=str(e), done=True)
                yield f"data: {json.dumps(error_response.model_dump())}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except Exception as e:
        error_thread_id = thread.id if thread else "unknown"
        logger.error(
            "stream_chat_request_failed",
            thread_id=error_thread_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))


