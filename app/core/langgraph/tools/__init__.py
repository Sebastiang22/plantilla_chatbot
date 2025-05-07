"""LangGraph tools for enhanced language model capabilities.

This package contains custom tools that can be used with LangGraph to extend
the capabilities of language models. Currently includes tools for web search
and other external integrations.
"""

from langchain_core.tools.base import BaseTool

from .duckduckgo_search import duckduckgo_search_tool
from .menu_tool import get_menu as get_menu_tool
from .order_tool import confirm_product

__all__ = ["get_menu_tool", "duckduckgo_search_tool","confirm_product"]
tools: list[BaseTool] = [duckduckgo_search_tool, get_menu_tool, confirm_product]

