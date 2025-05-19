"""This file contains the LangGraph Agent/workflow and interactions with the LLM."""

from typing import (
    Any,
    AsyncGenerator,
    Dict,
    Literal,
    Optional,
    TypedDict,
    List,
)

from asgiref.sync import sync_to_async
from langchain_core.messages import (
    BaseMessage,
    ToolMessage,
    convert_to_openai_messages,
)
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langfuse.callback import CallbackHandler
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import (
    END,
    StateGraph,
    START,
)
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import StateSnapshot
from openai import OpenAIError
from psycopg_pool import AsyncConnectionPool


from core.config import (
    Environment,
    settings,
)
from core.langgraph.tools import (get_menu_tool,  
                                  tools, 
                                  confirm_product,
                                  get_last_order,
                                  add_products_to_order,
                                    update_order_product,
                                    send_menu_images,
                                    send_location_tool)
from services.order_service import OrderService
from services.database import database_service

from core.logging import logger
from core.prompts import (
    SYSTEM_PROMPT_CONVERSATION,
    SYSTEM_PROMPT_ORDER_DATA,
    SYSTEM_PROMPT_UPDATE_ORDER,
    SYSTEM_PROMPT_PQRS,
    SYSTEM_PROMPT_ORCHESTRATOR,
)
from schemas import (
    GraphState,
    Message,
)
from utils import (
    dump_messages,
    prepare_messages,
    current_colombian_time,
)

class LangGraphAgent:
    """Manages the LangGraph Agent/workflow and interactions with the LLM.

    This class handles the creation and management of the LangGraph workflow,
    including LLM interactions, database connections, and response processing.
    """

    def __init__(self):
        """Initialize the LangGraph Agent with necessary components."""
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=settings.DEFAULT_LLM_TEMPERATURE,
            api_key=settings.LLM_API_KEY,
            max_tokens=settings.MAX_TOKENS,
            **self._get_model_kwargs(),
        )
        self.tools_by_name = {tool.name: tool for tool in tools}
        self._connection_pool: Optional[AsyncConnectionPool] = None
        self._graph: Optional[CompiledStateGraph] = None
        self.agent_tools = {
            "conversation_agent": [get_menu_tool, get_last_order, send_menu_images, send_location_tool],
            "order_data_agent": [confirm_product, get_menu_tool],
            "update_order_agent": [add_products_to_order,get_menu_tool,update_order_product],
            "pqrs_agent": [],
        }

        logger.info("llm_initialized", model=settings.LLM_MODEL, environment=settings.ENVIRONMENT.value)

    def _get_model_kwargs(self) -> Dict[str, Any]:
        """Get environment-specific model kwargs.
        
        Returns:
            Dict[str, Any]: Additional model arguments based on environment
        """
        model_kwargs = {}

        # Development - we can use lower speeds for cost savings
        if settings.ENVIRONMENT == Environment.DEVELOPMENT:
            model_kwargs["top_p"] = 0.8

        # Production - use higher quality settings
        elif settings.ENVIRONMENT == Environment.PRODUCTION:
            model_kwargs["top_p"] = 0.95
            model_kwargs["presence_penalty"] = 0.1
            model_kwargs["frequency_penalty"] = 0.1

        return model_kwargs

    async def _get_connection_pool(self) -> AsyncConnectionPool:
        """Get a PostgreSQL connection pool using environment-specific settings.

        Returns:
            AsyncConnectionPool: A connection pool for PostgreSQL database.
        """
        if self._connection_pool is None:
            try:
                # Configure pool size based on environment
                max_size = settings.POSTGRES_POOL_SIZE

                self._connection_pool = AsyncConnectionPool(
                    settings.POSTGRES_URL,
                    open=False,
                    max_size=max_size,
                    kwargs={
                        "autocommit": True,
                        "connect_timeout": 5,
                        "prepare_threshold": None,
                    },
                )
                await self._connection_pool.open()
                logger.info("connection_pool_created", max_size=max_size, environment=settings.ENVIRONMENT.value)
            except Exception as e:
                logger.error("connection_pool_creation_failed", error=str(e), environment=settings.ENVIRONMENT.value)
                # In production, we might want to degrade gracefully
                if settings.ENVIRONMENT == Environment.PRODUCTION:
                    logger.warning("continuing_without_connection_pool", environment=settings.ENVIRONMENT.value)
                    return None
                raise e
        return self._connection_pool

    async def _chat(self, state: GraphState) -> dict:
        """Process the chat state and generate a response.

        Args:
            state (GraphState): The current state of the conversation.

        Returns:
            dict: Updated state with new messages.
        """

        llm_calls_num = 0

        # Configure retry attempts based on environment
        max_retries = settings.MAX_LLM_CALL_RETRIES

        for attempt in range(max_retries):
            try:
                import pdb
                pdb.set_trace()
                generated_state = {"messages": [await self.llm.ainvoke(dump_messages(   ))]}
                logger.info(
                    "llm_response_generated",
                    session_id=state.session_id,
                    llm_calls_num=llm_calls_num + 1,
                    model=settings.LLM_MODEL,
                    environment=settings.ENVIRONMENT.value,
                )
                return generated_state
            except OpenAIError as e:
                logger.error(
                    "llm_call_failed",
                    llm_calls_num=llm_calls_num,
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    error=str(e),
                    environment=settings.ENVIRONMENT.value,
                )
                llm_calls_num += 1

                # In production, we might want to fall back to a more reliable model
                if settings.ENVIRONMENT == Environment.PRODUCTION and attempt == max_retries - 2:
                    fallback_model = "gpt-4o"
                    logger.warning(
                        "using_fallback_model", model=fallback_model, environment=settings.ENVIRONMENT.value
                    )
                    self.llm.model_name = fallback_model

                continue

        raise Exception(f"Failed to get a response from the LLM after {max_retries} attempts")

    # Define our tool node
    async def _tool_call(self, state: GraphState) -> GraphState:
        """
        Procesa las llamadas a herramientas desde el último mensaje.
        """
        print("\033[94m[_tool_call] Procesando llamada a herramienta\033[0m")
    
        outputs = []
        for tool_call in state.messages[-1].tool_calls:
            print(f"\033[94m[tool] Ejecutando: {tool_call['name']} con args: {tool_call['args']}\033[0m")
            
            # Add state to the tool arguments if the tool is confirm_product
            if tool_call["name"] == "confirm_product":
                # Get phone from the state dictionary
                phone = state.phone
                if not phone:
                    raise ValueError("Phone number is required for confirm_product tool")
                tool_call["args"]["state"] = {"phone": phone}
            
            # Verificar los argumentos requeridos para add_products_to_order
            if tool_call["name"] == "add_products_to_order":
                # Asegurarse de que el phone esté disponible
                if state.phone and not tool_call["args"].get("phone"):
                    tool_call["args"]["phone"] = state.phone
                
                # Verificar que exista el parámetro products
                if not tool_call["args"].get("products"):
                    print("\033[93mError: Falta el parámetro 'products' en add_products_to_order\033[0m")
                    # En lugar de lanzar un error, proporcionar una respuesta de error
                    outputs.append(
                        ToolMessage(
                            content=str({
                                "message": "Error: Falta el parámetro 'products' requerido para añadir productos a la orden",
                                "error": True
                            }),
                            name=tool_call["name"],
                            tool_call_id=tool_call["id"],
                        )
                    )
                    continue
            
            # Verificar los argumentos requeridos para update_order_product
            if tool_call["name"] == "update_order_product":
                # Asegurarse de que el phone esté disponible
                if state.phone and not tool_call["args"].get("phone"):
                    tool_call["args"]["phone"] = state.phone
                
                # Verificar que existan los parámetros requeridos
                missing_params = []
                if not tool_call["args"].get("product_name"):
                    missing_params.append("product_name")
                if not tool_call["args"].get("new_data"):
                    missing_params.append("new_data")
                
                if missing_params:
                    params_str = ", ".join(missing_params)
                    print(f"\033[93mError: Faltan los parámetros '{params_str}' en update_order_product\033[0m")
                    # En lugar de lanzar un error, proporcionar una respuesta de error
                    outputs.append(
                        ToolMessage(
                            content=str({
                                "message": f"Error: Faltan parámetros requeridos ({params_str}) para modificar el producto",
                                "error": True
                            }),
                            name=tool_call["name"],
                            tool_call_id=tool_call["id"],
                        )
                    )
                    continue
            
            try:
                tool_result = await self.tools_by_name[tool_call["name"]].ainvoke(tool_call["args"])
                outputs.append(
                    ToolMessage(
                        content=str(tool_result),
                        name=tool_call["name"],
                        tool_call_id=tool_call["id"],
                    )
                )
            except Exception as e:
                print(f"\033[93mError al ejecutar la herramienta {tool_call['name']}: {str(e)}\033[0m")
                outputs.append(
                    ToolMessage(
                        content=str({
                            "message": f"Error al ejecutar la herramienta: {str(e)}",
                            "error": True
                        }),
                        name=tool_call["name"],
                        tool_call_id=tool_call["id"],
                    )
                )
        
        print("\033[94m[_tool_call] Respuesta de la herramienta generada\033[0m")
        return {"messages": outputs}

    def _router(self, state: GraphState) -> Literal["end", "tool_node"]:
        """
        Determina si el agente debe continuar o finalizar según el último mensaje.
        """
        messages = state.messages
        last_message = messages[-1]
        if not last_message.tool_calls:
            return "end"
        else:
            return "tool_node"

    async def _orchestrator(self, state: GraphState) -> GraphState:
        """
        Nodo orquestador que detecta la intención del mensaje del usuario usando el LLM y redirige al agente adecuado.
        Verifica si el cliente tiene una orden pendiente antes de permitir nuevos pedidos.
        """
        print("\033[92m[orchestrator] Entrando al orquestador\033[0m")
        #print(f"\033[92mHistorial de nodos: {state.node_history}\033[0m")

        # Obtener la última orden del cliente si hay un número de teléfono
        last_order_info = "No hay información de órdenes previas."
        if state.phone:
            try:
                order_service = OrderService()
                last_order = await order_service.get_last_order(state.phone)
                #print(f"\033[96m[last_order]: {last_order}\033[0m")
                if last_order:
                    product_info = [
                        f"{product['name']} - Cantidad: {product['quantity']} - Precio: ${product['unit_price']} - Subtotal: ${product['subtotal']}"
                        for product in last_order['products']
                    ]
                    
                    last_order_info = f"""
                    Estado de la última orden: {last_order['status']}
                    Fecha: {last_order['created_at']}
                    Dirección: {last_order.get('address', 'No disponible')}
                    
                    Productos:
                    {chr(10).join(f"- {item}" for item in product_info)}
                    
                    Total: ${last_order['total_amount']}
                    """
            except Exception as e:
                print(f"\033[93mError al obtener la última orden: {str(e)}\033[0m")

        # Verificar el último nodo visitado
        if state.node_history:
            last_node = state.node_history[-1]
            if last_node == "order_data_agent":
                # Si ya se usó la tool confirm_product, usar el modelo para detectar la intención
                if len(state.messages) >= 4:
                    last_message = state.messages[-4]
                    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                        for tool_call in last_message.tool_calls:
                            if tool_call["name"] == "confirm_product":
                                print("\033[93mPedido creado, detectando intención del usuario\033[0m")
                                # Preparar el prompt para el LLM
                                current_time = current_colombian_time()
                                formatted_prompt = SYSTEM_PROMPT_ORCHESTRATOR.format(
                                    agent_name="Orchestrator",
                                    last_order_info=last_order_info,
                                    current_date_and_time=current_time
                                )
                                
                                # Limitar mensajes a los últimos 10
                                recent_messages = state.messages[-10:] if len(state.messages) > 10 else state.messages
                                messages = prepare_messages(recent_messages, self.llm, formatted_prompt)

                                # Invocar el modelo para obtener la intención
                                response = await self.llm.ainvoke(dump_messages(messages))
                                
                                try:
                                    # Obtener el contenido de la respuesta
                                    content = response.content.strip()
                                    
                                    # Intentar extraer el nodo de diferentes formatos posibles
                                    intent = None
                                    
                                    # Si es un JSON string, intentar parsearlo
                                    if content.startswith('{') or content.startswith('```json'):
                                        import json
                                        # Limpiar el string de markdown si es necesario
                                        json_str = content.replace('```json', '').replace('```', '').strip()
                                        try:
                                            parsed = json.loads(json_str)
                                            # Intentar obtener el nodo de diferentes claves posibles
                                            intent = parsed.get('node') or parsed.get('intention') or parsed.get('response')
                                        except json.JSONDecodeError:
                                            pass
                                    
                                    # Si no se pudo obtener el nodo del JSON, intentar extraerlo directamente
                                    if not intent:
                                        # Buscar uno de los nodos válidos en el texto
                                        valid_nodes = ["order_data_agent", "conversation_agent", "update_order_agent", "pqrs_agent", "send_menu"]
                                        for node in valid_nodes:
                                            if node in content:
                                                intent = node
                                                break
                                    
                                    # Si la intención es order_data_agent o update_order_agent, redirigir a update_order_agent
                                    if intent in ["order_data_agent", "update_order_agent"]:
                                        # Verificar si el pedido está en estado pending
                                        try:
                                            order_service = OrderService()
                                            last_order = await order_service.get_last_order(state.phone)
                                            
                                            if last_order and last_order['status'] == "pending":
                                                print("\033[93mUsuario quiere añadir más productos, redirigiendo a update_order_agent\033[0m")
                                                state.node_history.append("update_order_agent")
                                                return state
                                            else:
                                                current_status = last_order['status'] if last_order and 'status' in last_order else "no disponible"
                                                print(f"\033[93mEl pedido no está en estado 'pending', está en estado '{current_status}'. No se puede modificar. Redirigiendo a conversation_agent\033[0m")
                                                
                                                # Añadir un mensaje al sistema para informar al usuario
                                                state.messages.append({
                                                    "role": "system",
                                                    "content": f"El pedido ya no se puede modificar porque está en estado {current_status}. Informa al cliente sobre el estado actual sin ofrecer automáticamente ayuda para crear un nuevo pedido. Deja que el cliente decida si quiere hacer un nuevo pedido y te lo solicite explícitamente."
                                                })
                                                
                                                state.node_history.append("conversation_agent")
                                                return state
                                        except Exception as e:
                                            print(f"\033[93mError al verificar el estado del pedido: {str(e)}\033[0m")
                                            state.node_history.append("conversation_agent")
                                            return state
                                    else:
                                        print("\033[93mRedirigiendo a conversation_agent\033[0m")
                                        state.node_history.append("conversation_agent")
                                        return state
                                        
                                except Exception as e:
                                    print(f"\033[93mError al procesar la respuesta: {str(e)}\033[0m")
                                state.node_history.append("conversation_agent")
                                return state
                print("\033[93mRedirigiendo a order_data_agent por ser el último nodo visitado\033[0m")
                
                # Añadir detección de intención para ver si quiere el menú
                current_time = current_colombian_time()
                formatted_prompt = SYSTEM_PROMPT_ORCHESTRATOR.format(
                    agent_name="Orchestrator",
                    last_order_info=last_order_info,
                    current_date_and_time=current_time
                )
                
                # Limitar mensajes a los últimos 10
                recent_messages = state.messages[-10:] if len(state.messages) > 10 else state.messages
                messages = prepare_messages(recent_messages, self.llm, formatted_prompt)

                # Invocar el modelo para obtener la intención
                response = await self.llm.ainvoke(dump_messages(messages))
                print(f"\033[96m[orchestrator response]: {response}\033[0m")    
                
                try:
                    # Obtener el contenido de la respuesta
                    content = response.content.strip()
                    
                    # Intentar extraer el nodo de diferentes formatos posibles
                    intent = None
                    
                    # Si es un JSON string, intentar parsearlo
                    if content.startswith('{') or content.startswith('```json'):
                        import json
                        # Limpiar el string de markdown si es necesario
                        json_str = content.replace('```json', '').replace('```', '').strip()
                        try:
                            parsed = json.loads(json_str)
                            # Intentar obtener el nodo de diferentes claves posibles
                            intent = parsed.get('node') or parsed.get('intention') or parsed.get('response')
                        except json.JSONDecodeError:
                            pass
                    
                    # Si no se pudo obtener el nodo del JSON, intentar extraerlo directamente
                    if not intent:
                        # Buscar uno de los nodos válidos en el texto
                        valid_nodes = ["order_data_agent", "conversation_agent", "update_order_agent", "pqrs_agent", "send_menu"]
                        for node in valid_nodes:
                            if node in content:
                                intent = node
                                break
                    
                    # Si la intención es ver el menú, redirigir a conversation_agent
                    if intent == "send_menu":
                        print("\033[93mUsuario quiere ver el menú, redirigiendo a conversation_agent\033[0m")
                        state.node_history.append("conversation_agent")
                        return state
                except Exception as e:
                    print(f"\033[93mError al procesar la respuesta: {str(e)}\033[0m")
                
                # Si no se detectó intención de menú, seguir con order_data_agent
                state.node_history.append("order_data_agent")
                return state
            elif last_node == "update_order_agent":
                # Verificar si hay suficientes mensajes para revisar
                if len(state.messages) >= 4:
                    # Obtener el cuarto mensaje desde el final
                    fourth_last_message = state.messages[-4]
                    # Verificar si es un AIMessage y tiene tool_calls
                    if hasattr(fourth_last_message, 'tool_calls') and fourth_last_message.tool_calls:
                        for tool_call in fourth_last_message.tool_calls:
                            if tool_call["name"] == "add_products_to_order":
                                print("\033[93mProductos añadidos a la orden, detectando intención del usuario\033[0m")
                                # Preparar el prompt para el LLM
                                current_time = current_colombian_time()
                                formatted_prompt = SYSTEM_PROMPT_ORCHESTRATOR.format(
                                    agent_name="Orchestrator",
                                    last_order_info=last_order_info,
                                    current_date_and_time=current_time
                                )
                                
                                # Limitar mensajes a los últimos 10
                                recent_messages = state.messages[-10:] if len(state.messages) > 10 else state.messages
                                messages = prepare_messages(recent_messages, self.llm, formatted_prompt)

                                # Invocar el modelo para obtener la intención
                                response = await self.llm.ainvoke(dump_messages(messages))
                                print(f"\033[96m[orchestrator response]: {response}\033[0m")    
                                
                                try:
                                    # Obtener el contenido de la respuesta
                                    content = response.content.strip()
                                    
                                    # Intentar extraer el nodo de diferentes formatos posibles
                                    intent = None
                                    
                                    # Si es un JSON string, intentar parsearlo
                                    if content.startswith('{') or content.startswith('```json'):
                                        import json
                                        # Limpiar el string de markdown si es necesario
                                        json_str = content.replace('```json', '').replace('```', '').strip()
                                        try:
                                            parsed = json.loads(json_str)
                                            # Intentar obtener el nodo de diferentes claves posibles
                                            intent = parsed.get('node') or parsed.get('intention') or parsed.get('response')
                                        except json.JSONDecodeError:
                                            pass
                                    
                                    # Si no se pudo obtener el nodo del JSON, intentar extraerlo directamente
                                    if not intent:
                                        # Buscar uno de los nodos válidos en el texto
                                        valid_nodes = ["order_data_agent", "conversation_agent", "update_order_agent", "pqrs_agent", "send_menu"]
                                        for node in valid_nodes:
                                            if node in content:
                                                intent = node
                                                break
                                    
                                    # Si la intención es order_data_agent o update_order_agent, redirigir a update_order_agent
                                    if intent in ["order_data_agent", "update_order_agent"]:
                                        # Verificar si el pedido está en estado pending
                                        try:
                                            order_service = OrderService()
                                            last_order = await order_service.get_last_order(state.phone)
                                            
                                            if last_order and last_order['status'] == "pending":
                                                print("\033[93mUsuario quiere añadir más productos, redirigiendo a update_order_agent\033[0m")
                                                state.node_history.append("update_order_agent")
                                                return state
                                            else:
                                                current_status = last_order['status'] if last_order and 'status' in last_order else "no disponible"
                                                print(f"\033[93mEl pedido no está en estado 'pending', está en estado '{current_status}'. No se puede modificar. Redirigiendo a conversation_agent\033[0m")
                                                
                                                # Añadir un mensaje al sistema para informar al usuario
                                                state.messages.append({
                                                    "role": "system",
                                                    "content": f"El pedido ya no se puede modificar porque está en estado {current_status}. Informa al cliente sobre el estado actual sin ofrecer automáticamente ayuda para crear un nuevo pedido. Deja que el cliente decida si quiere hacer un nuevo pedido y te lo solicite explícitamente."
                                                })
                                                
                                                state.node_history.append("conversation_agent")
                                                return state
                                        except Exception as e:
                                            print(f"\033[93mError al verificar el estado del pedido: {str(e)}\033[0m")
                                            state.node_history.append("conversation_agent")
                                            return state
                                    else:
                                        print("\033[93mRedirigiendo a conversation_agent\033[0m")
                                        state.node_history.append("conversation_agent")
                                        return state
                                        
                                except Exception as e:
                                    print(f"\033[93mError al procesar la respuesta: {str(e)}\033[0m")
                                state.node_history.append("conversation_agent")
                                return state
                print("\033[93mRedirigiendo a update_order_agent por ser el último nodo visitado\033[0m")
                
                # Añadir detección de intención para ver si quiere el menú
                current_time = current_colombian_time()
                formatted_prompt = SYSTEM_PROMPT_ORCHESTRATOR.format(
                    agent_name="Orchestrator",
                    last_order_info=last_order_info,
                    current_date_and_time=current_time
                )
                
                # Limitar mensajes a los últimos 10
                recent_messages = state.messages[-10:] if len(state.messages) > 10 else state.messages
                messages = prepare_messages(recent_messages, self.llm, formatted_prompt)

                # Invocar el modelo para obtener la intención
                response = await self.llm.ainvoke(dump_messages(messages))
                #print(f"\033[96m[orchestrator response]: {response}\033[0m")    
                
                try:
                    # Obtener el contenido de la respuesta
                    content = response.content.strip()
                    
                    # Intentar extraer el nodo de diferentes formatos posibles
                    intent = None
                    
                    # Si es un JSON string, intentar parsearlo
                    if content.startswith('{') or content.startswith('```json'):
                        import json
                        # Limpiar el string de markdown si es necesario
                        json_str = content.replace('```json', '').replace('```', '').strip()
                        try:
                            parsed = json.loads(json_str)
                            # Intentar obtener el nodo de diferentes claves posibles
                            intent = parsed.get('node') or parsed.get('intention') or parsed.get('response')
                        except json.JSONDecodeError:
                            pass
                    
                    # Si no se pudo obtener el nodo del JSON, intentar extraerlo directamente
                    if not intent:
                        # Buscar uno de los nodos válidos en el texto
                        valid_nodes = ["order_data_agent", "conversation_agent", "update_order_agent", "pqrs_agent", "send_menu"]
                        for node in valid_nodes:
                            if node in content:
                                intent = node
                                break
                    
                    # Si la intención es ver el menú, redirigir a conversation_agent
                    if intent == "send_menu":
                        print("\033[93mUsuario quiere ver el menú, redirigiendo a conversation_agent\033[0m")
                        state.node_history.append("conversation_agent")
                        return state
                except Exception as e:
                    print(f"\033[93mError al procesar la respuesta: {str(e)}\033[0m")
                
                # Si no se detectó intención de menú, seguir con update_order_agent
                # Verificar si el pedido está en estado pending antes de redirigir
                try:
                    order_service = OrderService()
                    last_order = await order_service.get_last_order(state.phone)
                    
                    if last_order and last_order['status'] == "pending":
                        state.node_history.append("update_order_agent")
                        return state
                    else:
                        current_status = last_order['status'] if last_order and 'status' in last_order else "no disponible"
                        print(f"\033[93mEl pedido no está en estado 'pending', está en estado '{current_status}'. No se puede modificar. Redirigiendo a conversation_agent\033[0m")
                        
                        # Añadir un mensaje al sistema para informar al usuario
                        state.messages.append({
                            "role": "system",
                            "content": f"El pedido ya no se puede modificar porque está en estado {current_status}. Informa al cliente sobre el estado actual sin ofrecer automáticamente ayuda para crear un nuevo pedido. Deja que el cliente decida si quiere hacer un nuevo pedido y te lo solicite explícitamente."
                        })
                        
                        intent = "conversation_agent"
                except Exception as e:
                    print(f"\033[93mError al verificar el estado del pedido: {str(e)}\033[0m")
                    state.node_history.append("conversation_agent")
                    return state

        # Preparar el prompt para el LLM con la información de la orden
        current_time = current_colombian_time()
        formatted_prompt = SYSTEM_PROMPT_ORCHESTRATOR.format(
            agent_name="Orchestrator",
            last_order_info=last_order_info,
            current_date_and_time=current_time
        )
        
        # Limitar mensajes a los últimos 10
        recent_messages = state.messages[-10:] if len(state.messages) > 10 else state.messages
        messages = prepare_messages(recent_messages, self.llm, formatted_prompt)

        # Invocar el modelo para obtener la intención
        response = await self.llm.ainvoke(dump_messages(messages))
        #print(f"\033[96m[orchestrator response]: {response}\033[0m")    
        
        try:
            # Obtener el contenido de la respuesta
            content = response.content.strip()
            
            # Intentar extraer el nodo de diferentes formatos posibles
            intent = None
            
            # Si es un JSON string, intentar parsearlo
            if content.startswith('{') or content.startswith('```json'):
                import json
                # Limpiar el string de markdown si es necesario
                json_str = content.replace('```json', '').replace('```', '').strip()
                try:
                    parsed = json.loads(json_str)
                    # Intentar obtener el nodo de diferentes claves posibles
                    intent = parsed.get('node') or parsed.get('intention') or parsed.get('response')
                except json.JSONDecodeError:
                    pass
            
            # Si no se pudo obtener el nodo del JSON, intentar extraerlo directamente
            if not intent:
                # Buscar uno de los nodos válidos en el texto
                valid_nodes = ["order_data_agent", "conversation_agent", "update_order_agent", "pqrs_agent", "send_menu"]
                for node in valid_nodes:
                    if node in content:
                        intent = node
                        break
            
            # Si no se encontró un nodo válido, usar conversation_agent como fallback
            if not intent or intent not in valid_nodes:
                print("\033[93mNodo no válido detectado, usando conversation_agent como fallback\033[0m")
                intent = "conversation_agent"
                
        except Exception as e:
            print(f"\033[93mError al procesar la respuesta: {str(e)}\033[0m")
            intent = "conversation_agent"

        print(f"\033[96m[orchestrator intent detected]: {intent}\033[0m")

        # Verificar si hay una orden pendiente antes de permitir nuevos pedidos
        if intent == "order_data_agent" and state.phone:
            last_order = await order_service.get_last_order(state.phone)
            if last_order and last_order['status'] == "pending":
                print("\033[93mCliente tiene una orden pendiente, redirigiendo a update_order_agent\033[0m")
                intent = "update_order_agent"
        
        # Verificar si la intención es update_order_agent y si el pedido está en estado pending
        if intent == "update_order_agent" and state.phone:
            try:
                order_service = OrderService()
                last_order = await order_service.get_last_order(state.phone)
                
                # Solo permitir update_order_agent si el pedido está en estado pending
                if not last_order or last_order['status'] != "pending":
                    current_status = last_order['status'] if last_order and 'status' in last_order else "no disponible"
                    print(f"\033[93mEl pedido no está en estado 'pending', está en estado '{current_status}'. No se puede modificar. Redirigiendo a conversation_agent\033[0m")
                    
                    # Añadir un mensaje al sistema para informar al usuario
                    state.messages.append({
                        "role": "system",
                        "content": f"El pedido ya no se puede modificar porque está en estado {current_status}. Informa al cliente sobre el estado actual sin ofrecer automáticamente ayuda para crear un nuevo pedido. Deja que el cliente decida si quiere hacer un nuevo pedido y te lo solicite explícitamente."
                    })
                    
                    state.node_history.append("conversation_agent")
                    intent = "conversation_agent"
            except Exception as e:
                print(f"\033[93mError al verificar el estado del pedido: {str(e)}\033[0m")
                # En caso de error, es más seguro redirigir a conversation_agent
                intent = "conversation_agent"
        
        # Si la intención es ver el menú, redirigir a conversation_agent
        if intent == "send_menu":
            print("\033[93mUsuario quiere ver el menú, redirigiendo a conversation_agent\033[0m")
            
            # Guardar información especial para que conversation_agent sepa que debe mostrar el menú
            state.messages.append({
                "role": "system",
                "content": "El usuario ha solicitado ver el menú. Por favor, envíale el menú utilizando las herramientas disponibles."
            })
            
            intent = "conversation_agent"

        state.node_history.append(intent)
        return state

    async def conversation_agent(self, state: GraphState) -> GraphState:
        """
        Agente especializado en conversación general.
        """
        print("\033[92m[conversation_agent] Entrando al agente de conversación\033[0m")
        #print(f"\033[92mHistorial de nodos: {state.node_history}\033[0m")

        # Obtener el nombre del cliente y la dirección del último pedido si están disponibles
        client_name = None
        if state.phone:
            try:
                user_details = await database_service.get_user_details_with_latest_order(state.phone)
                print(f"\033[96m[User details from database]: {user_details}\033[0m")
                if user_details and user_details["name"]:
                    client_name = user_details["name"]
                    print(f"\033[96m[Nombre del cliente detectado]: {client_name}\033[0m")
            except Exception as e:
                print(f"\033[93mError al obtener detalles del usuario: {str(e)}\033[0m")

        # Formatear el prompt con el nombre del cliente y la fecha actual
        current_time = current_colombian_time()
        formatted_prompt = SYSTEM_PROMPT_CONVERSATION.format(
            client_name=client_name or "Cliente",
            current_date_and_time=current_time
        )
        
        # Mostrar las primeras 200 caracteres del prompt formateado para depuración
        prompt_preview = formatted_prompt[:200] + "..." if len(formatted_prompt) > 200 else formatted_prompt
        #print(f"\033[95m[Prompt formateado preview]: {prompt_preview}\033[0m")
        
        # Verificar explícitamente si el nombre del cliente está en el prompt
        if client_name and client_name in formatted_prompt:
            print(f"\033[92m[✓] Nombre '{client_name}' incluido en el prompt\033[0m")
        else:
            print(f"\033[91m[✗] Nombre del cliente NO encontrado en el prompt formateado\033[0m")

        # Limitar mensajes a los últimos 10
        recent_messages = state.messages[-10:] if len(state.messages) > 10 else state.messages
        messages = prepare_messages(recent_messages, self.llm, formatted_prompt)
        
        # Mostrar los primeros mensajes para depuración
        if messages:
            first_message = messages[0]
            print(f"\033[95m[Primer mensaje enviado al LLM]: Tipo: {type(first_message)}, Contenido: {str(first_message)[:200]}...\033[0m")
        
        llm_with_tools = self.llm.bind_tools(self.agent_tools["conversation_agent"])
        ai_message = await llm_with_tools.ainvoke(dump_messages(messages))
        if hasattr(ai_message, 'tool_calls') and ai_message.tool_calls:
            for tool_call in ai_message.tool_calls:
                if tool_call["name"] == "get_last_order":
                    print(f"\033[32m Tool Call: {tool_call['name']} \033[0m")
                    arguments = tool_call["args"]
                    arguments["phone"] = state.phone
                elif tool_call["name"] == "send_menu_images":
                    print(f"\033[32m Tool Call: {tool_call['name']} \033[0m")
                    arguments = tool_call["args"]
                    arguments["phone"] = state.phone

        state.messages.append(ai_message)
        state.node_history.append("conversation_agent")

        return state

    async def order_data_agent(self, state: GraphState) -> dict:
        """
        Agente especializado en obtención de datos de pedido.
        """
        print("\033[92m[order_data_agent] Entrando al agente de datos de pedido\033[0m")
        #print(f"\033[92mHistorial de nodos: {state.node_history}\033[0m")
        
        # Obtener el nombre del cliente y la dirección del último pedido si están disponibles
        client_name = None
        previous_address = None
        if state.phone:
            try:
                user_details = await database_service.get_user_details_with_latest_order(state.phone)
                # Imprimir la estructura completa para depuración
                print(f"\033[96m[User details from database (COMPLETO)]: {user_details}\033[0m")
                
                if user_details and user_details["name"]:
                    client_name = user_details["name"]
                    print(f"\033[96m[Nombre del cliente detectado]: {client_name}\033[0m")
                
                # Verificar todas las posibles ubicaciones de la dirección
                if user_details:
                    # Intento 1: Dirección en el nivel principal
                    if "address" in user_details and user_details["address"]:
                        previous_address = user_details["address"]
                        print(f"\033[96m[Dirección encontrada en nivel principal]: {previous_address}\033[0m")
                    
                    # Intento 2: Dirección dentro de "order"
                    elif "order" in user_details and user_details["order"] and "address" in user_details["order"]:
                        previous_address = user_details["order"]["address"]
                        print(f"\033[96m[Dirección encontrada en 'order']: {previous_address}\033[0m")
                    
                    # Intento 3: Dirección dentro de "has_order"
                    elif "has_order" in user_details and user_details["has_order"] and "order" in user_details:
                        if "address" in user_details["order"]:
                            previous_address = user_details["order"]["address"]
                            print(f"\033[96m[Dirección encontrada en 'order' con has_order=True]: {previous_address}\033[0m")
                    
                    # Si no se encuentra la dirección
                    if not previous_address:
                        print("\033[93m[ADVERTENCIA] No se pudo encontrar la dirección en los detalles del usuario\033[0m")
                else:
                    print("\033[93m[ADVERTENCIA] No se encontraron detalles del usuario\033[0m")
                    
            except Exception as e:
                print(f"\033[93mError al obtener detalles del usuario: {str(e)}\033[0m")
        
        # Formatear el prompt con los datos del cliente y la fecha actual
        current_time = current_colombian_time()
        formatted_prompt = SYSTEM_PROMPT_ORDER_DATA.format(
            client_name=client_name or "Cliente",
            previous_address=previous_address or "No disponible",
            current_date_and_time=current_time
        )
        
        # Mostrar las primeras 200 caracteres del prompt formateado para depuración
        prompt_preview = formatted_prompt[:200] + "..." if len(formatted_prompt) > 200 else formatted_prompt
        print(f"\033[95m[Prompt formateado preview]: {prompt_preview}\033[0m")
        
        # Limitar mensajes a los últimos 10
        recent_messages = state.messages[-10:] if len(state.messages) > 10 else state.messages
        messages = prepare_messages(recent_messages, self.llm, formatted_prompt)
        llm_with_tools = self.llm.bind_tools(self.agent_tools["order_data_agent"])
        response_msg = await llm_with_tools.ainvoke(dump_messages(messages))
        
        # Verificar y procesar llamadas a herramientas
        if hasattr(response_msg, 'tool_calls') and response_msg.tool_calls:
            for tool_call in response_msg.tool_calls:
                if tool_call["name"] == "confirm_product":
                    print(f"\033[32m Tool Call: {tool_call['name']} \033[0m")
                    arguments = tool_call["args"]
                    
                    # Si no se proporcionó un nombre pero tenemos uno en la base de datos, usarlo
                    if client_name and (not arguments.get("name") or arguments.get("name") == "Cliente"):
                        arguments["name"] = client_name
                        print(f"\033[32m Añadido nombre {client_name} a confirm_product\033[0m")
                    
                    # Si no se proporcionó una dirección pero tenemos una anterior, usarla
                    if previous_address and (not arguments.get("address") or arguments.get("address") == "No disponible"):
                        arguments["address"] = previous_address
                        print(f"\033[32m Añadido dirección anterior {previous_address} a confirm_product\033[0m")
                    
                    # Asegurar que se incluye el teléfono
                    arguments["phone"] = state.phone
        
        generated_state = {"messages": [response_msg]}
        logger.info(
            "llm_response_generated",
            session_id=state.session_id,
            model=settings.LLM_MODEL,
            environment=settings.ENVIRONMENT.value,
        )
        state.node_history.append("order_data_agent")

        return generated_state

    async def update_order_agent(self, state: GraphState) -> dict:
        """
        Agente especializado en actualización de pedidos.
        """
        print("\033[92m[update_order_agent] Entrando al agente de actualización de pedidos\033[0m")
        print(f"\033[92mHistorial de nodos: {state.node_history}\033[0m")
        
        # Obtener el nombre del cliente
        client_name = None
        if state.phone:
            try:
                user_details = await database_service.get_user_details_with_latest_order(state.phone)
                print(f"\033[96m[User details from database]: {user_details}\033[0m")
                if user_details and user_details["name"]:
                    client_name = user_details["name"]
                    print(f"\033[96m[Nombre del cliente detectado]: {client_name}\033[0m")
            except Exception as e:
                print(f"\033[93mError al obtener detalles del usuario: {str(e)}\033[0m")
        
        # Obtener la última orden del cliente
        last_order_info = "No hay información de órdenes previas."
        if state.phone:
            try:
                order_service = OrderService()
                last_order = await order_service.get_last_order(state.phone)
                #print(f"\033[96m[last_order]: {last_order}\033[0m")
                if last_order:
                    product_info = [
                        f"{product['name']} - Cantidad: {product['quantity']} - Precio: ${product['unit_price']} - Subtotal: ${product['subtotal']}"
                        for product in last_order['products']
                    ]
                    
                    last_order_info = f"""
                    Estado de la última orden: {last_order['status']}
                    Fecha: {last_order['created_at']}
                    Dirección: {last_order.get('address', 'No disponible')}
                    
                    Productos:
                    {chr(10).join(f"- {item}" for item in product_info)}
                    
                    Total: ${last_order['total_amount']}
                    """
                    print(f"\033[96m[last_order_info]: {last_order_info}\033[0m")
            except Exception as e:
                print(f"\033[93mError al obtener la última orden: {str(e)}\033[0m")

        # Preparar el prompt con la información de la orden
        current_time = current_colombian_time()
        formatted_prompt = SYSTEM_PROMPT_UPDATE_ORDER.format(
            client_name=client_name or "Cliente",
            last_order_info=last_order_info,
            current_date_and_time=current_time
        )
        
        # Mostrar las primeras 200 caracteres del prompt formateado para depuración
        prompt_preview = formatted_prompt[:200] + "..." if len(formatted_prompt) > 200 else formatted_prompt
        #print(f"\033[95m[Prompt formateado preview]: {prompt_preview}\033[0m")
        
        # Limitar mensajes a los últimos 10
        recent_messages = state.messages[-10:] if len(state.messages) > 10 else state.messages
        messages = prepare_messages(recent_messages, self.llm, formatted_prompt)
        llm_with_tools = self.llm.bind_tools(self.agent_tools["update_order_agent"])
        response_msg = await llm_with_tools.ainvoke(dump_messages(messages))
        
        # Verificar y procesar llamadas a herramientas
        if hasattr(response_msg, 'tool_calls') and response_msg.tool_calls:
            for tool_call in response_msg.tool_calls:
                print(f"\033[32m Tool Call: {tool_call['name']} \033[0m")
                if tool_call["name"] == "add_products_to_order":
                    # Asegurarse de que el phone esté disponible y reemplazarlo siempre
                    if state.phone:
                        tool_call["args"]["phone"] = state.phone
                        print(f"\033[32m Añadido phone {state.phone} a add_products_to_order\033[0m")
                    else:
                        print("\033[93mError: No hay número de teléfono disponible para add_products_to_order\033[0m")
                    
                    # Verificar que exista el parámetro products
                    if not tool_call["args"].get("products"):
                        print("\033[93mError: Falta el parámetro 'products' en add_products_to_order\033[0m")
                        # Establecer un array vacío como valor por defecto para evitar errores
                        tool_call["args"]["products"] = []
                        
                elif tool_call["name"] == "update_order_product":
                    # Asegurarse de que el phone esté disponible
                    if state.phone:
                        tool_call["args"]["phone"] = state.phone
                        print(f"\033[32m Añadido phone {state.phone} a update_order_product\033[0m")
                    
                    # Verificar que existan los parámetros requeridos
                    if not tool_call["args"].get("product_name"):
                        print("\033[93mError: Falta el parámetro 'product_name' en update_order_product\033[0m")
                    if not tool_call["args"].get("new_data"):
                        print("\033[93mError: Falta el parámetro 'new_data' en update_order_product\033[0m")
                        # Establecer un diccionario vacío como valor por defecto para evitar errores
                        tool_call["args"]["new_data"] = {}
        
        generated_state = {"messages": [response_msg]}
        logger.info(
            "llm_response_generated",
            session_id=state.session_id,
            model=settings.LLM_MODEL,
            environment=settings.ENVIRONMENT.value,
        )
        state.node_history.append("update_order_agent")
        
        return generated_state

    async def pqrs_agent(self, state: GraphState) -> dict:
        """
        Agente especializado en gestión de PQRS.
        """
        print("\033[92m[pqrs_agent]\033[0m")
        messages = prepare_messages(state.messages, self.llm, SYSTEM_PROMPT_PQRS)
        llm_with_tools = self.llm.bind_tools(self.agent_tools["pqrs_agent"])
        generated_state = {"messages": [await llm_with_tools.ainvoke(dump_messages(messages))]}
        logger.info(
            "llm_response_generated",
            session_id=state.session_id,
            model=settings.LLM_MODEL,
            environment=settings.ENVIRONMENT.value,
        )
        return generated_state

    def route_by_intent(self, state: GraphState) -> str:
        """
        Determina el siguiente agente especializado según la intención detectada por el orquestador.
        """
        return state.node_history[-1] if state.node_history else "conversation_agent"

    async def _conversation_tool_call(self, state: GraphState) -> GraphState:
        """Process tool calls from the conversation agent."""
        return await self._tool_call(state)

    async def _order_data_tool_call(self, state: GraphState) -> GraphState:
        """Process tool calls from the order data agent."""
        return await self._tool_call(state)

    async def _update_order_tool_call(self, state: GraphState) -> GraphState:
        """Process tool calls from the update order agent."""
        return await self._tool_call(state)

    async def create_graph(self) -> Optional[CompiledStateGraph]:
        """Create and configure the LangGraph workflow con orquestador y agentes especializados."""
        if self._graph is None:
            try:
                builder = StateGraph(GraphState)
                # Nodos principales
                builder.add_node("orchestrator", self._orchestrator)
                builder.add_node("conversation_agent", self.conversation_agent)
                builder.add_node("order_data_agent", self.order_data_agent)
                builder.add_node("update_order_agent", self.update_order_agent)
                builder.add_node("pqrs_agent", self.pqrs_agent)

                # Nodos de herramienta específicos
                builder.add_node("conversation_tool_call", self._conversation_tool_call)
                builder.add_node("order_data_tool_call", self._order_data_tool_call)
                builder.add_node("update_order_tool_call", self._update_order_tool_call)

                # Nodo de entrada
                builder.set_entry_point("orchestrator")

                # Enrutamiento del orquestador
                builder.add_conditional_edges(
                    "orchestrator",
                    self.route_by_intent,
                    {
                        "conversation_agent": "conversation_agent",
                        "order_data_agent": "order_data_agent",
                        "update_order_agent": "update_order_agent",
                        "pqrs_agent": "pqrs_agent",
                    },
                )

                # conversation_agent <-> conversation_tool_call
                builder.add_conditional_edges(
                    "conversation_agent",
                    self._router,
                    {"tool_node": "conversation_tool_call", "end": END},
                )
                builder.add_edge("conversation_tool_call", "conversation_agent")

                # order_data_agent <-> order_data_tool_call
                builder.add_conditional_edges(
                    "order_data_agent",
                    self._router,
                    {"tool_node": "order_data_tool_call", "end": END},
                )
                builder.add_edge("order_data_tool_call", "order_data_agent")

                # update_order_agent <-> update_order_tool_call
                builder.add_conditional_edges(
                    "update_order_agent",
                    self._router,
                    {"tool_node": "update_order_tool_call", "end": END},
                )
                builder.add_edge("update_order_tool_call", "update_order_agent")

                # Configurar puntos de finalización para cada agente
                builder.set_finish_point("conversation_agent")
                builder.set_finish_point("order_data_agent")
                builder.set_finish_point("update_order_agent")

                # Get connection pool (may be None in production if DB unavailable)
                connection_pool = await self._get_connection_pool()
                if connection_pool:
                    checkpointer = AsyncPostgresSaver(connection_pool)
                    # Inicializar las tablas del checkpointer
                    await checkpointer.setup()
                else:
                    checkpointer = None
                    if settings.ENVIRONMENT != Environment.PRODUCTION:
                        raise Exception("Connection pool initialization failed")


                self._graph = builder.compile(
                    checkpointer=checkpointer,
                    name=f"{settings.PROJECT_NAME} Agent ({settings.ENVIRONMENT.value})",
                )

                logger.info(
                    "graph_created",
                    graph_name=f"{settings.PROJECT_NAME} Agent",
                    environment=settings.ENVIRONMENT.value,
                    has_checkpointer=checkpointer is not None,
                )
            except Exception as e:
                logger.error("graph_creation_failed", error=str(e), environment=settings.ENVIRONMENT.value)
                if settings.ENVIRONMENT == Environment.PRODUCTION:
                    logger.warning("continuing_without_graph")
                    return None
                raise e

        return self._graph

    async def get_response(
        self,
        messages: list[Message],
        session_id: str,
        initial_state: Optional[dict] = None,
    ) -> list[dict]:
        """Get a response from the LLM.

        Args:
            messages (list[Message]): The messages to send to the LLM.
            session_id (str): The session ID for Langfuse tracking.
            initial_state (Optional[dict]): Initial state to be passed to the graph.

        Returns:
            list[dict]: The response from the LLM.
        """
        if self._graph is None:
            self._graph = await self.create_graph()
        config = {
            "configurable": {"thread_id": session_id},
            "callbacks": [
                CallbackHandler(
                    environment=settings.ENVIRONMENT.value,
                    debug=False,
                    session_id=session_id,
                )
            ],
        }
        try:
            # Prepare initial state
            state = {
                "messages": dump_messages(messages),
                "session_id": session_id,
                "last_node": "conversation_agent",  # Valor por defecto para evitar error de validación
            }
            # Add any additional state from initial_state
            if initial_state:
                state.update(initial_state)

            response = await self._graph.ainvoke(state, config)
            return self.__process_messages(response["messages"])
        except Exception as e:
            logger.error(f"Error getting response: {str(e)}")
            raise e

    async def get_stream_response(
        self, messages: list[Message], session_id: str, user_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Get a stream response from the LLM.

        Args:
            messages (list[Message]): The messages to send to the LLM.
            session_id (str): The session ID for the conversation.
            user_id (Optional[str]): The user ID for the conversation.

        Yields:
            str: Tokens of the LLM response.
        """
        config = {
            "configurable": {"thread_id": session_id},
            "callbacks": [
                CallbackHandler(
                    environment=settings.ENVIRONMENT.value, debug=False, user_id=user_id, session_id=session_id
                )
            ],
        }
        if self._graph is None:
            self._graph = await self.create_graph()

        try:
            async for token, _ in self._graph.astream(
                {"messages": dump_messages(messages), "session_id": session_id}, config, stream_mode="messages"
            ):
                try:
                    yield token.content
                except Exception as token_error:
                    logger.error("Error processing token", error=str(token_error), session_id=session_id)
                    # Continue with next token even if current one fails
                    continue
        except Exception as stream_error:
            logger.error("Error in stream processing", error=str(stream_error), session_id=session_id)
            raise stream_error

    async def get_chat_history(self, session_id: str) -> list[Message]:
        """Get the chat history for a given thread ID.

        Args:
            session_id (str): The session ID for the conversation.

        Returns:
            list[Message]: The chat history.
        """
        if self._graph is None:
            self._graph = await self.create_graph()

        state: StateSnapshot = await sync_to_async(self._graph.get_state)(
            config={"configurable": {"thread_id": session_id}}
        )
        return self.__process_messages(state.values["messages"]) if state.values else []

    def __process_messages(self, messages: list[BaseMessage]) -> list[Message]:
        openai_style_messages = convert_to_openai_messages(messages)
        # keep just assistant and user messages
        return [
            Message(**message)
            for message in openai_style_messages
            if message["role"] in ["assistant", "user"] and message["content"]
        ]

    async def clear_chat_history(self, session_id: str) -> None:
        """Clear all chat history for a given thread ID.

        Args:
            session_id: The ID of the session to clear history for.

        Raises:
            Exception: If there's an error clearing the chat history.
        """
        try:
            # Make sure the pool is initialized in the current event loop
            conn_pool = await self._get_connection_pool()

            # Use a new connection for this specific operation
            async with conn_pool.connection() as conn:
                for table in settings.CHECKPOINT_TABLES:
                    try:
                        await conn.execute(f"DELETE FROM {table} WHERE thread_id = %s", (session_id,))
                        logger.info(f"Cleared {table} for session {session_id}")
                    except Exception as e:
                        logger.error(f"Error clearing {table}", error=str(e))
                        raise

        except Exception as e:
            logger.error("Failed to clear chat history", error=str(e))
            raise
