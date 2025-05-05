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
from core.langgraph.tools import get_menu_tool, duckduckgo_search_tool, tools
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
)


class OrchestratorState(TypedDict):
    """
    Estado compartido en el grafo, contiene los mensajes, la intención detectada y el historial de agentes.
    """
    messages: List[Any]
    intent: Optional[str]
    agent_history: List[str]


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
            "conversation_agent": [get_menu_tool,duckduckgo_search_tool],
            "order_data_agent": [],
            "update_order_agent": [],
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
        """Process tool calls from the last message.

        Args:
            state: The current agent state containing messages and tool calls.

        Returns:
            Dict with updated messages containing tool responses.
        """
        outputs = []
        for tool_call in state.messages[-1].tool_calls:
            print(f"\033[94m[tool] {tool_call['name']}\033[0m")
            tool_result = await self.tools_by_name[tool_call["name"]].ainvoke(tool_call["args"])
            outputs.append(
                ToolMessage(
                    content=tool_result,
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
        return {"messages": outputs}

    def _router(self, state: GraphState) -> Literal["end", "tool_node"]:
        """Determine if the agent should continue or end based on the last message.

        Args:
            state: The current agent state containing messages.

        Returns:
            Literal["end", "tool_node"]: "end" if there are no tool calls, "tool_node" otherwise.
        """
        messages = state.messages
        last_message = messages[-1]
        # If there is no function call, then we finish
        if not last_message.tool_calls:
            return "end"
        # Otherwise if there is, we continue
        else:
            return "tool_node"

    async def _orchestrator(self, state: GraphState) -> GraphState:
        """
        Nodo orquestador que detecta la intención del mensaje del usuario usando el LLM y redirige al agente adecuado.
        """
        print("\033[92m[orchestrator]\033[0m")
        # Tomar el último mensaje del usuario
        messages = state.messages
        last_message = messages[-1]
        # Preparar el prompt para el LLM
        messages = prepare_messages(state.messages, self.llm, SYSTEM_PROMPT_ORCHESTRATOR)

        # Invocar el modelo para obtener la intención
        response = await self.llm.ainvoke(dump_messages(messages))
        print(f"\033[96m[orchestrator response]: {response}\033[0m")    
        intent = response.content.strip()
        print(f"\033[96m[orchestrator intent detected]: {intent}\033[0m")
        if intent == "order_data_agent":
            state.node_history.append("order_data_agent")
        else:
            state.node_history.append("conversation_agent")
        return state

    async def conversation_agent(self, state: GraphState) -> GraphState:
        """
        Agente especializado en conversación general.
        """
        print("\033[92m[conversation_agent]\033[0m")
        print(f"\033[92m{state.node_history}\033[0m")

        messages = prepare_messages(state.messages, self.llm, SYSTEM_PROMPT_CONVERSATION)
        llm_with_tools = self.llm.bind_tools(self.agent_tools["conversation_agent"])
        ai_message = await llm_with_tools.ainvoke(dump_messages(messages))
        state.messages.append(ai_message)
        state.node_history.append("conversation_agent")

        return state

    async def order_data_agent(self, state: GraphState) -> dict:
        """
        Agente especializado en obtención de datos de pedido.
        """
        print("\033[92m[order_data_agent]\033[0m")
        messages = prepare_messages(state.messages, self.llm, SYSTEM_PROMPT_ORDER_DATA)
        llm_with_tools = self.llm.bind_tools(self.agent_tools["order_data_agent"])
        generated_state = {"messages": [await llm_with_tools.ainvoke(dump_messages(messages))]}
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
        print("\033[92m[update_order_agent]\033[0m")
        messages = prepare_messages(state.messages, self.llm, SYSTEM_PROMPT_UPDATE_ORDER)
        llm_with_tools = self.llm.bind_tools(self.agent_tools["update_order_agent"])
        generated_state = {"messages": [await llm_with_tools.ainvoke(dump_messages(messages))]}
        logger.info(
            "llm_response_generated",
            session_id=state.session_id,
            model=settings.LLM_MODEL,
            environment=settings.ENVIRONMENT.value,
        )
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

    async def create_graph(self) -> Optional[CompiledStateGraph]:
        """Create and configure the LangGraph workflow con orquestador y agentes especializados."""
        if self._graph is None:
            try:
                graph_builder = StateGraph(GraphState)
                graph_builder.add_node("orchestrator", self._orchestrator)
                graph_builder.add_node("conversation_agent", self.conversation_agent)
                graph_builder.add_node("order_data_agent", self.order_data_agent)
                graph_builder.add_node("update_order_agent", self.update_order_agent)
                graph_builder.add_node("pqrs_agent", self.pqrs_agent)
                graph_builder.add_node("tool_call", self._tool_call)

                # Nodo de entrada
                graph_builder.set_entry_point("orchestrator")

                # Transición del orquestador al agente adecuado
                graph_builder.add_conditional_edges(
                    "orchestrator",
                    self.route_by_intent,
                    {
                        "conversation_agent": "conversation_agent",
                        "order_data_agent": "order_data_agent",
                        "update_order_agent": "update_order_agent",
                        "pqrs_agent": "pqrs_agent",
                    }
                )

                # Solo conversation_agent puede terminar o llamar tools (para pruebas)
                graph_builder.add_conditional_edges(
                    "conversation_agent",
                    self._router,
                    {"tool_node": "tool_call", "end": END},
                )
                graph_builder.add_edge("tool_call", "conversation_agent")

                graph_builder.set_finish_point("conversation_agent")

                # Get connection pool (may be None in production if DB unavailable)
                connection_pool = await self._get_connection_pool()
                if connection_pool:
                    checkpointer = AsyncPostgresSaver(connection_pool)
                    await checkpointer.setup()
                else:
                    checkpointer = None
                    if settings.ENVIRONMENT != Environment.PRODUCTION:
                        raise Exception("Connection pool initialization failed")

                self._graph = graph_builder.compile(
                    checkpointer=checkpointer, name=f"{settings.PROJECT_NAME} Agent ({settings.ENVIRONMENT.value})"
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
        user_id: Optional[str] = None,
    ) -> list[dict]:
        """Get a response from the LLM.

        Args:
            messages (list[Message]): The messages to send to the LLM.
            session_id (str): The session ID for Langfuse tracking.
            user_id (Optional[str]): The user ID for Langfuse tracking.

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
                    user_id=user_id,
                    session_id=session_id,
                )
            ],
        }
        try:
            response = await self._graph.ainvoke(
                {
                    "messages": dump_messages(messages),
                    "session_id": session_id,
                    "last_node": "conversation_agent",  # Valor por defecto para evitar error de validación
                },
                config
            )
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
