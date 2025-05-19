"use client";

import { useState, useCallback } from "react";
import { OrdersList } from "./orders/order-list";
import { OrderModal } from "./orders/order-modal";
import { ConfirmDialog } from "@/components/confirm-dialog";
import { Statistics } from "./stats/statistics";
import { useOrders } from "@/app/providers";
import { useToast } from "@/components/ui/use-toast";
import { MoonIcon, SunIcon, MenuIcon } from "lucide-react";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Order, OrderState } from "@/lib/types";
import { MenuImageModal } from "@/components/menu-image-modal";
import { useOrdersDateFilter } from "@/hooks/useOrdersDateFilter";
import { DateFilter } from "./orders/date-filter";
import { StatusBadge } from "@/components/status-badge";
import Image from "next/image";

// Componente Emoji accesible
const Emoji = ({ 
  symbol, 
  label, 
  className 
}: { 
  symbol: string; 
  label?: string; 
  className?: string 
}) => (
  <span
    className={`emoji ${className || ""}`}
    role="img"
    aria-label={label || ""}
    aria-hidden={label ? "false" : "true"}
  >
    {symbol}
  </span>
);

// Función para traducir estado de orden para mostrar en mensajes
function getDisplayNameForOrderState(state: string): string {
  const lowerState = state.toLowerCase();
  
  if (lowerState === OrderState.PENDING) return "Pendiente";
  if (lowerState === OrderState.PREPARING) return "En preparación";
  if (lowerState === OrderState.DELIVERY) return "En reparto";
  if (lowerState === OrderState.COMPLETED) return "Completado";
  
  // Estados especiales que pueden venir del backend
  if (lowerState === "preparando") return "En reparto"; // Mostrar "preparando" como "En reparto"
  
  // Estado no reconocido, devolver con primera letra en mayúscula
  return state.charAt(0).toUpperCase() + state.slice(1);
}

/**
 * Componente principal del Dashboard
 */
export function DashboardClient() {
  const { theme, setTheme } = useTheme();
  const { toast } = useToast();
  const { 
    orders, 
    stats, 
    isLoading, 
    error, 
    refreshOrders, 
    updateOrderStatus, 
    deleteOrder 
  } = useOrders();

  // Usar el hook de filtrado por fecha a nivel del dashboard
  const {
    dateRange,
    orders: dateFilteredOrders,
    stats: dateFilteredStats,
    isLoading: isLoadingDates,
    error: dateFilterError,
    fetchOrdersByDateRange,
    setQuickDateRange
  } = useOrdersDateFilter();

  // Determinar qué datos mostrar (los filtrados por fecha o los generales)
  const displayOrders = dateFilteredOrders || orders;
  const displayStats = dateFilteredOrders ? dateFilteredStats : stats;
  const combinedLoading = isLoading || isLoadingDates;
  const combinedError = error || dateFilterError;

  const [selectedOrderData, setSelectedOrderData] = useState<{order: Order | null, index: number | null}>({
    order: null,
    index: null
  });
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isConfirmDialogOpen, setIsConfirmDialogOpen] = useState(false);
  const [pendingDeleteOrderId, setPendingDeleteOrderId] = useState<string | null>(null);
  const [updatingOrderIds, setUpdatingOrderIds] = useState<Set<string>>(new Set());
  const [isMenuModalOpen, setIsMenuModalOpen] = useState(false);

  // Manejar la selección de un pedido (versión unificada)
  const handleSelectOrder = useCallback((order: Order, index?: number) => {
    setSelectedOrderData({
      order, 
      index: typeof index === 'number' ? index : null
    });
    setIsModalOpen(true);
  }, []);

  // Manejar la actualización de estado de un pedido
  const handleStatusUpdate = useCallback(async (orderId: string, newStatus: string) => {
    try {
      // Marcar como actualizando
      setUpdatingOrderIds(prev => {
        const newSet = new Set(prev);
        newSet.add(orderId);
        return newSet;
      });

      await updateOrderStatus(orderId, newStatus);

      // Mostrar notificación de éxito usando la función de traducción
      toast({
        title: "Estado actualizado",
        description: `El pedido ha sido marcado como "${getDisplayNameForOrderState(newStatus)}"`,
        variant: "default",
      });
      
      // Si tenemos un filtro de fecha aplicado, actualizar los datos filtrados
      if (dateRange.startDate || dateRange.endDate) {
        fetchOrdersByDateRange(dateRange);
      }
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Error",
        description: err instanceof Error ? err.message : "No se pudo actualizar el estado.",
      });
    } finally {
      // Quitar de la lista de actualizando
      setUpdatingOrderIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(orderId);
        return newSet;
      });
    }
  }, [updateOrderStatus, toast, dateRange, fetchOrdersByDateRange]);

  // Manejar la eliminación de un pedido
  const handleDeleteOrder = useCallback((orderId: string) => {
    setPendingDeleteOrderId(orderId);
    setIsConfirmDialogOpen(true);
  }, []);

  // Confirmar eliminación de pedido
  const confirmDeleteOrder = useCallback(async () => {
    if (!pendingDeleteOrderId) return;

    try {
      await deleteOrder(pendingDeleteOrderId);
      toast({
        title: "Pedido eliminado",
        description: "El pedido ha sido eliminado exitosamente",
        variant: "default",
      });

      // Si el pedido eliminado es el que está seleccionado, cerrar el modal
      if (selectedOrderData.order?.id === pendingDeleteOrderId) {
        setIsModalOpen(false);
        setSelectedOrderData({order: null, index: null});
      }
      
      // Si tenemos un filtro de fecha aplicado, actualizar los datos filtrados
      if (dateRange.startDate || dateRange.endDate) {
        fetchOrdersByDateRange(dateRange);
      }
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Error",
        description: err instanceof Error ? err.message : "No se pudo eliminar el pedido.",
      });
    } finally {
      setIsConfirmDialogOpen(false);
      setPendingDeleteOrderId(null);
    }
  }, [pendingDeleteOrderId, deleteOrder, toast, selectedOrderData, dateRange, fetchOrdersByDateRange]);
  
  // Manejar cambios en el filtro de fecha
  const handleDateChange = useCallback((startDate: string | null, endDate: string | null) => {
    fetchOrdersByDateRange({ startDate, endDate });
  }, [fetchOrdersByDateRange]);

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-10 border-b bg-background">
        <div className="container flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-2">
            {/* Volvemos a usar una ruta relativa directa */}
            <Image 
              src="/juanchito-plaza-logo.png"
              alt="Juanchito Plaza Logo" 
              width={32}
              height={32}
              className="h-8 w-8 object-contain"
              priority
            />
            <h1 className="text-lg font-semibold md:text-xl">Juanchito Plaza Dashboard</h1>
          </div>
          <div className="flex items-center gap-2">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="icon">
                  {theme === "dark" ? <MoonIcon className="h-4 w-4" /> : <SunIcon className="h-4 w-4" />}
                  <span className="sr-only">Cambiar tema</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => setTheme("light")}>
                  Claro
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setTheme("dark")}>
                  Oscuro
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setTheme("system")}>
                  Sistema
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
            <DateFilter onDateChange={handleDateChange} />
            <Button variant="outline" onClick={() => setIsMenuModalOpen(true)}>
              <MenuIcon className="h-4 w-4 mr-2" />
              Cambiar Menú
            </Button>
            <Button variant="default" onClick={() => {
              refreshOrders();
              if (dateRange.startDate || dateRange.endDate) {
                fetchOrdersByDateRange(dateRange);
              }
            }}>
              Actualizar
            </Button>
          </div>
        </div>
      </header>
      <main className="flex-1 overflow-auto p-4">
        <div className="container mx-auto space-y-6">
          {/* Estadísticas - mostrar las filtradas si hay filtro activo */}
          <Statistics stats={displayStats} isLoading={combinedLoading} />

          {/* Lista de Órdenes - no incluir el filtro de fecha aquí, ya está en el header */}
          <OrdersList
            orders={displayOrders}
            onSelectOrder={handleSelectOrder}
            onStatusUpdate={handleStatusUpdate}
            onDeleteOrder={handleDeleteOrder}
            updatingOrderIds={updatingOrderIds}
            setUpdatingOrderIds={setUpdatingOrderIds}
            isLoading={combinedLoading}
            error={combinedError}
          />

          {/* Modal de Orden - Actualizado para usar selectedOrderData */}
          {selectedOrderData.order && (
            <OrderModal
              order={selectedOrderData.order}
              orderIndex={selectedOrderData.index}
              open={isModalOpen}
              onOpenChange={setIsModalOpen}
              onStatusUpdate={handleStatusUpdate}
              onDeleteOrder={handleDeleteOrder}
              isUpdating={updatingOrderIds.has(selectedOrderData.order.id)}
            />
          )}

          {/* Diálogo de Confirmación */}
          <ConfirmDialog
            open={isConfirmDialogOpen}
            onOpenChange={setIsConfirmDialogOpen}
            onConfirm={confirmDeleteOrder}
            title="Eliminar Pedido"
            description="¿Estás seguro que deseas eliminar este pedido? Esta acción no se puede deshacer."
          />

          {/* Modal para cambiar la imagen del menú */}
          <MenuImageModal
            open={isMenuModalOpen}
            onOpenChange={setIsMenuModalOpen}
          />
        </div>
      </main>
    </div>
  );
}