import { Badge } from "@/components/ui/badge"
import { OrderState } from "@/lib/types"

interface StatusBadgeProps {
  status: string
}

/**
 * Componente que muestra un badge con el estado del pedido
 */
export function StatusBadge({ status }: StatusBadgeProps) {
  const normalizedStatus = normalizeStatus(status);
  
  // Usar los mismos colores que en el modal
  switch (normalizedStatus) {
    case OrderState.PENDING:
      return (
        <Badge className="bg-yellow-500 text-white border-transparent">
          Pendiente
        </Badge>
      )
    case OrderState.PREPARING:
      return (
        <Badge className="bg-blue-500 text-white border-transparent">
          En preparación
        </Badge>
      )
    case OrderState.DELIVERY:
      return (
        <Badge className="bg-purple-500 text-white border-transparent">
          En reparto
        </Badge>
      )
    case OrderState.COMPLETED:
      return (
        <Badge className="bg-green-500 text-white border-transparent">
          Completado
        </Badge>
      )
    default:
      return (
        <Badge variant="outline" className="bg-gray-500 text-white">
          {status}
        </Badge>
      )
  }
}

/**
 * Normaliza el estado a uno de los valores de OrderState
 */
function normalizeStatus(status: string): string {
  const lowerStatus = status.toLowerCase();
  
  // Mapeo de estados en inglés a español
  if (lowerStatus === "pending") return OrderState.PENDING;
  if (lowerStatus === "preparing") return OrderState.PREPARING;
  if (lowerStatus === "delivery") return OrderState.DELIVERY;
  if (lowerStatus === "completed") return OrderState.COMPLETED;
  
  // Mapeo de estados en español a las constantes OrderState
  if (lowerStatus === "pendiente") return OrderState.PENDING;
  if (lowerStatus === "en preparación") return OrderState.PREPARING;
  if (lowerStatus === "en preparacion") return OrderState.PREPARING;
  if (lowerStatus === "en reparto") return OrderState.DELIVERY;
  if (lowerStatus === "completado") return OrderState.COMPLETED;
  
  // Si ya es una constante OrderState, devolverla
  if (Object.values(OrderState).includes(lowerStatus as OrderState)) {
    return lowerStatus;
  }
  
  return status;
} 