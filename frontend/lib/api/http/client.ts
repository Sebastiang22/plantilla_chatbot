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

/**
 * API client con métodos para diferentes operaciones
 */
export const apiClient = {
  /**
   * Obtiene las órdenes del día
   */
  async getOrders() {
    const response = await fetchWithTimeout(buildApiUrl(backendConfig.endpoints.orders.today));
    return response.json();
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