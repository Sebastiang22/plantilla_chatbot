"""This file contains the prompts for the agent."""

import os
from pathlib import Path
from datetime import datetime

from core.config import settings


def load_prompt(filename: str) -> str:
    """
    Carga un prompt desde un archivo markdown.
    """
    prompt_path = Path(__file__).parent / filename
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()
    
def load_orchestrator_prompt() -> str:
    """
    Carga el prompt del orquestador con valores por defecto.
    """
    prompt = load_prompt("system_orchestrator.md")
    return prompt.format(
        agent_name="Orchestrator",
        last_order_info="No hay información de órdenes previas.",
        current_date_and_time=""
    )


def load_update_order_prompt() -> str:
    """
    Carga el prompt de actualización de pedidos con valores por defecto.
    
    Importante: Este prompt contiene marcadores de posición {client_name}, {last_order_info}
    y {current_date_and_time} que deben ser reemplazados antes de usar el prompt.
    """
    # Cargar el prompt sin formatear para preservar los marcadores de posición
    prompt = load_prompt("system_update_order.md")
    return prompt  # Retornar el prompt sin formatear


def load_conversation_prompt() -> str:
    """
    Carga el prompt de conversación con valores por defecto.
    
    Importante: Este prompt contiene marcadores de posición {client_name} y {current_date_and_time}
    que deben ser reemplazados antes de usar el prompt.
    """
    # Cargar el prompt sin formatear para preservar los marcadores de posición
    prompt = load_prompt("system_conversation.md")
    return prompt  # Retornar el prompt sin formatear


def load_order_data_prompt() -> str:
    """
    Carga el prompt de datos de pedido con valores por defecto.
    
    Importante: Este prompt contiene marcadores de posición {client_name}, {previous_address} 
    y {current_date_and_time} que deben ser reemplazados antes de usar el prompt.
    """
    # Cargar el prompt sin formatear para preservar los marcadores de posición
    prompt = load_prompt("system_order_data.md")
    return prompt  # Retornar el prompt sin formatear


# Cargar todos los prompts
SYSTEM_PROMPT_CONVERSATION = load_conversation_prompt()
SYSTEM_PROMPT_ORDER_DATA = load_order_data_prompt()
SYSTEM_PROMPT_UPDATE_ORDER = load_update_order_prompt()
SYSTEM_PROMPT_PQRS = load_prompt("system_pqrs.md")
SYSTEM_PROMPT_ORCHESTRATOR = load_orchestrator_prompt()