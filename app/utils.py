def prepare_messages(messages: list[Message], llm: ChatOpenAI, system_prompt: str) -> list[BaseMessage]:
    """
    Prepara los mensajes para el LLM, incluyendo el prompt del sistema y limitando a los últimos 10 mensajes.
    
    Args:
        messages (list[Message]): Lista de mensajes de la conversación
        llm (ChatOpenAI): Instancia del modelo de lenguaje
        system_prompt (str): Prompt del sistema a incluir
        
    Returns:
        list[BaseMessage]: Lista de mensajes formateados para el LLM
    """
    # Limitar a los últimos 10 mensajes
    recent_messages = messages[-10:] if len(messages) > 10 else messages
    
    # Convertir mensajes a formato BaseMessage
    base_messages = convert_to_openai_messages(recent_messages)
    
    # Añadir el prompt del sistema al inicio
    return [{"role": "system", "content": system_prompt}] + base_messages 