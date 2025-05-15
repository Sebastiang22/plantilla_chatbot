/**
 * Configuración centralizada de la aplicación
 */

// Configuración del backend
export const backendConfig = {
  // URL base del API, tomada de variables de entorno o valor por defecto
  baseUrl: process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000',
  
  // Endpoints del API
  endpoints: {
    orders: {
      today: '/api/v1/orders/today',
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

// Función helper para construir URLs completas
export const buildApiUrl = (endpoint: string): string => {
  return `${backendConfig.baseUrl}${endpoint}`;
}; 