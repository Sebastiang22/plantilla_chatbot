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
    """
    prompt = load_prompt("system_update_order.md")
    return prompt.format(
        last_order_info="No hay información de órdenes previas.",
        current_date_and_time=""
    )


# Cargar todos los prompts
SYSTEM_PROMPT_CONVERSATION = load_prompt("system_conversation.md")
SYSTEM_PROMPT_ORDER_DATA = load_prompt("system_order_data.md")
SYSTEM_PROMPT_UPDATE_ORDER = load_update_order_prompt()
SYSTEM_PROMPT_PQRS = load_prompt("system_pqrs.md")
SYSTEM_PROMPT_ORCHESTRATOR = load_orchestrator_prompt()