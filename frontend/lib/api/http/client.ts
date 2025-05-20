/**
 * Cliente HTTP para comunicación con el backend
 */
import { backendConfig, buildApiUrl } from '../../config';

// Tipos de error de la API
interface ApiError {
  statusCode: number;
  message: string;
  details?: any;
}

/**
 * Opciones para la petición
 */
interface FetchOptions extends RequestInit {
  timeout?: number;
}

/**
 * Cliente HTTP mejorado con manejo de errores y timeout
 */
async function fetchWithTimeout(
  url: string,
  options: FetchOptions = {}
): Promise<Response> {
  const { timeout = backendConfig.timeouts.default, ...fetchOptions } = options;
  
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  
  try {
    const response = await fetch(url, {
      ...fetchOptions,
      signal: controller.signal,
    });
    
    if (!response.ok) {
      let errorData: ApiError;
      try {
        errorData = await response.json();
      } catch (e) {
        errorData = {
          statusCode: response.status,
          message: response.statusText || 'Error de servidor desconocido'
        };
      }
      
      throw new Error(errorData.message || `Error ${response.status}: ${response.statusText}`);
    }
    
    return response;
  } finally {
    clearTimeout(timeoutId);
  }
}

// Función para generar un hash simple de los datos
function generateDataHash(data: any): string {
  // Convertir los datos a JSON y luego a una cadena hash simple
  // Esto no es un hash criptográfico completo, pero sirve para comparaciones básicas
  const jsonStr = JSON.stringify(data);
  let hash = 0;
  for (let i = 0; i < jsonStr.length; i++) {
    const char = jsonStr.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convertir a un entero de 32 bits
  }
  return hash.toString();
}

/**
 * API client con métodos para diferentes operaciones
 */
export const apiClient = {
  // Almacenar el hash de los datos más recientes
  _lastDataHash: '',

  /**
   * Obtiene las órdenes del día actual utilizando el endpoint by-date
   */
  async getOrders() {
    // Obtenemos la fecha actual en formato ISO
    const today = new Date().toISOString().split('T')[0];
    
    // Construimos la URL con los parámetros
    const params = new URLSearchParams();
    params.append('start_date', today);
    params.append('end_date', today);
    
    const endpoint = backendConfig.endpoints.orders.byDate;
    const url = buildApiUrl(`${endpoint}?${params.toString()}`);
    
    const response = await fetchWithTimeout(url);
    const data = await response.json();
    
    // Calcular y almacenar el hash de los datos
    this._lastDataHash = generateDataHash(data);
    
    return data;
  },

  /**
   * Verifica si hay cambios en los datos sin descargarlos completamente
   * @returns {Promise<boolean>} true si hay cambios, false si no hay cambios
   */
  async checkForChanges(): Promise<boolean> {
    try {
      // Si no tenemos un hash previo, definitivamente necesitamos cargar los datos
      if (!this._lastDataHash) {
        return true;
      }
      
      // Obtener datos actuales
      const today = new Date().toISOString().split('T')[0];
      const params = new URLSearchParams();
      params.append('start_date', today);
      params.append('end_date', today);
      
      const endpoint = backendConfig.endpoints.orders.byDate;
      const url = buildApiUrl(`${endpoint}?${params.toString()}`);
      
      const response = await fetchWithTimeout(url);
      const data = await response.json();
      
      // Generar hash de los nuevos datos
      const newHash = generateDataHash(data);
      
      // Comparar con el hash anterior
      return newHash !== this._lastDataHash;
    } catch (error) {
      console.error("Error al verificar cambios:", error);
      // En caso de error, preferimos recargar por seguridad
      return true;
    }
  },
  
  /**
   * Actualiza el estado de una orden
   */
  async updateOrderStatus(orderId: string, newStatus: string) {
    const response = await fetchWithTimeout(buildApiUrl(backendConfig.endpoints.orders.updateState), {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        order_id: orderId,
        state: newStatus
      }),
    });
    
    return response.json();
  },
  
  /**
   * Elimina una orden
   */
  async deleteOrder(orderId: string) {
    const response = await fetchWithTimeout(buildApiUrl(backendConfig.endpoints.orders.delete(orderId)), {
      method: 'DELETE',
    });
    
    return response.json();
  },
  
  /**
   * Verifica el estado del servidor
   */
  async checkServerStatus() {
    try {
      const response = await fetchWithTimeout(
        buildApiUrl(backendConfig.endpoints.orders.wsStatus), 
        { timeout: backendConfig.timeouts.serverStatus }
      );
      return response.ok;
    } catch (error) {
      console.error('Error al verificar estado del servidor:', error);
      return false;
    }
  }
};