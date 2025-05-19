/**
 * Configuración centralizada de la aplicación
 */

// Configuración del backend
export const backendConfig = {
  // URL base del API, tomada de variables de entorno o valor por defecto
  baseUrl: process.env.NEXT_PUBLIC_BACKEND_URL || 'https://juanchito-plaza.blueriver-8537145c.westus2.azurecontainerapps.io',
  
  // Endpoints del API
  endpoints: {
    orders: {
      // Utilizamos el endpoint byDate con parámetros para obtener órdenes del día actual
      byDate: '/api/v1/orders/by-date',
      updateState: '/api/v1/orders/update_state',
      delete: (orderId: string) => `/api/v1/orders/${orderId}`,
      wsStatus: '/api/v1/orders/ws-status'
    },
    menu: {
      list: '/api/v1/menu',
      create: '/api/v1/menu',
      update: (id: string) => `/api/v1/menu/${id}`,
      delete: (id: string) => `/api/v1/menu/${id}`,
      extract: '/api/v1/menu/extract'
    },
    chatbot: {
      chat: '/api/v1/chatbot/chat',
      stream: '/api/v1/chatbot/chat/stream',
      threadNew: '/api/v1/chatbot/thread/new'
    }
  },
  
  // Configuración de timeouts
  timeouts: {
    default: 8000,
    serverStatus: 3000
  }
} as const;

// Exportar la URL del backend como constante para uso general
export const API_URL = backendConfig.baseUrl;

/**
 * Construye una URL para el API utilizando la URL base configurada
 */
export function buildApiUrl(path: string): string {
  return `${backendConfig.baseUrl}${path}`;
} 