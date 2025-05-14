import { useState, useCallback } from 'react';
import { Order } from '@/lib/types';
import { buildApiUrl, backendConfig } from '@/lib/config';

type DateRange = {
  startDate: string | null;
  endDate: string | null;
};

export function useOrdersDateFilter() {
  // Estado para el rango de fechas actual (predeterminado: últimos 30 días)
  const [dateRange, setDateRange] = useState<DateRange>({
    startDate: null, // Si es null, backend usará últimos 30 días
    endDate: null    // Si es null, backend usará fecha actual
  });
  
  // Estado para controlar si estamos cargando datos
  const [isLoading, setIsLoading] = useState<boolean>(false);
  
  // Estado para almacenar las órdenes
  const [orders, setOrders] = useState<Order[] | null>(null);
  
  // Estado para errores
  const [error, setError] = useState<string | null>(null);
  
  // Estado para estadísticas
  const [stats, setStats] = useState({
    total_orders: 0,
    pending_orders: 0,
    complete_orders: 0,
    total_sales: 0
  });

  // Función para cargar órdenes con el filtro de fechas
  const fetchOrdersByDateRange = useCallback(async (range?: DateRange) => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Usar el rango proporcionado o el estado actual
      const currentRange = range || dateRange;
      
      // Construir URL con parámetros de consulta usando la configuración centralizada
      let endpoint = backendConfig.endpoints.orders.byDate;
      const params = new URLSearchParams();
      
      if (currentRange.startDate) {
        params.append('start_date', currentRange.startDate);
      }
      
      if (currentRange.endDate) {
        params.append('end_date', currentRange.endDate);
      }
      
      // Añadir parámetros a la URL si existen
      const queryString = params.toString();
      const url = buildApiUrl(endpoint + (queryString ? `?${queryString}` : ''));
      
      console.log('Fetching orders with URL:', url);
      
      const response = await fetch(url);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || `Error: ${response.status}`);
      }
      
      const data = await response.json();
      setOrders(data.orders);
      setStats(data.stats);
      
      // Si se proporcionó un nuevo rango, actualizar el estado
      if (range) {
        setDateRange(range);
      }
      
    } catch (err) {
      console.error('Error al obtener órdenes por fecha:', err);
      setError(err instanceof Error ? err.message : 'Error desconocido');
      setOrders(null);
    } finally {
      setIsLoading(false);
    }
  }, [dateRange]);

  // Función para establecer predefinidos rápidos
  const setQuickDateRange = useCallback((days: number) => {
    if (days === 0) {
      // Hoy
      const today = new Date().toISOString().split('T')[0];
      const newRange = { startDate: today, endDate: today };
      setDateRange(newRange);
      fetchOrdersByDateRange(newRange);
    } else if (days > 0) {
      // Últimos X días
      const end = new Date();
      const start = new Date();
      start.setDate(start.getDate() - days);
      
      const newRange = {
        startDate: start.toISOString().split('T')[0],
        endDate: end.toISOString().split('T')[0]
      };
      
      setDateRange(newRange);
      fetchOrdersByDateRange(newRange);
    } else {
      // Todas (null para usar valores predeterminados del backend)
      const newRange = { startDate: null, endDate: null };
      setDateRange(newRange);
      fetchOrdersByDateRange(newRange);
    }
  }, [fetchOrdersByDateRange]);

  return {
    dateRange,
    orders,
    stats,
    isLoading,
    error,
    fetchOrdersByDateRange,
    setQuickDateRange
  };
} 