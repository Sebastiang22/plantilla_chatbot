"""This file contains the prompts for the agent."""

import os
from datetime import datetime

from core.config import settings


def load_agent_prompt(filename):
    """Carga el prompt de sistema para un agente específico."""
    with open(os.path.join(os.path.dirname(__file__), filename), "r") as f:
        return f.read().format(
            agent_name=settings.PROJECT_NAME + " Agent",
            current_date_and_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

SYSTEM_PROMPT_CONVERSATION = load_agent_prompt("system_conversation.md")
SYSTEM_PROMPT_ORDER_DATA = load_agent_prompt("system_order_data.md")
SYSTEM_PROMPT_UPDATE_ORDER = load_agent_prompt("system_update_order.md")
SYSTEM_PROMPT_PQRS = load_agent_prompt("system_pqrs.md")

def load_orchestrator_prompt():
    """Carga el prompt de sistema para el orquestador."""
    with open(os.path.join(os.path.dirname(__file__), "system_orchestrator.md"), "r") as f:
        return f.read().format(
            agent_name=settings.PROJECT_NAME + " Orchestrator",
            current_date_and_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

SYSTEM_PROMPT_ORCHESTRATOR = load_orchestrator_prompt()