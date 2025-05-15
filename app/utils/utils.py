from datetime import datetime
from pytz import timezone

def current_colombian_time() -> str:
    """
    Retorna la hora actual en formato de Colombia (zona horaria América/Bogotá).
    
    Returns:
        str: Fecha y hora actual en formato 'YYYY-MM-DD HH:MM:SS'
    """
    current_time = datetime.now(timezone('America/Bogota')).strftime('%Y-%m-%d %H:%M:%S')
    return current_time
