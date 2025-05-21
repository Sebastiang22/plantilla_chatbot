import { useState, useCallback, useEffect } from 'react';
import { Order } from '@/lib/types';
import { buildApiUrl, backendConfig } from '@/lib/config';
import { utcToZonedTime, format as formatTz } from 'date-fns-tz';

type DateRange = {
  startDate: string | null;
  endDate: string | null;
};

export function useOrdersDateFilter() {
  // Obtener la fecha actual en la zona horaria de Colombia
  const timeZone = 'America/Bogota';
  const now = new Date();
  const colombiaDate = utcToZonedTime(now, timeZone);
  const today = formatTz(colombiaDate, 'yyyy-MM-dd', { timeZone });
  
  // Estado para el rango de fechas actual (predeterminado: fecha actual)
  const [dateRange, setDateRange] = useState<DateRange>({
    startDate: today,
    endDate: today
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
      const now = new Date();
      const colombiaDate = utcToZonedTime(now, timeZone);
      const today = formatTz(colombiaDate, 'yyyy-MM-dd', { timeZone });
      const newRange = { startDate: today, endDate: today };
      setDateRange(newRange);
      fetchOrdersByDateRange(newRange);
    } else if (days > 0) {
      // Últimos X días
      const end = utcToZonedTime(new Date(), timeZone);
      const start = utcToZonedTime(new Date(), timeZone);
      start.setDate(start.getDate() - days);
      const newRange = {
        startDate: formatTz(start, 'yyyy-MM-dd', { timeZone }),
        endDate: formatTz(end, 'yyyy-MM-dd', { timeZone })
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

  // Cargar datos al inicializar
  useEffect(() => {
    // Cargar los datos del día actual al inicializar
    fetchOrdersByDateRange();
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