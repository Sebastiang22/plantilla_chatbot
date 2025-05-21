"use client"

import { useState } from "react"
import {
  type ColumnDef,
  type ColumnFiltersState,
  type SortingState,
  type VisibilityState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table"
import { ArrowUpDown, ChevronDown, Filter, Search, Loader2, CheckCircle, Clock, Trash2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { StatusBadge } from "@/components/status-badge"
import { Order, OrderState, OrderCallback, OrderStatusCallback, OrderDeleteCallback } from "@/lib/types"
import { formatDate, formatCOP } from "@/lib/utils/format"

interface OrdersListProps {
  orders: Order[]
  onSelectOrder: OrderCallback
  onStatusUpdate: OrderStatusCallback
  onDeleteOrder: OrderDeleteCallback
  updatingOrderIds?: Set<string>
  setUpdatingOrderIds?: (updater: (prev: Set<string>) => Set<string>) => void
  isLoading?: boolean
  error?: string | null
}

// Función para traducir el estado de la orden
function translateOrderState(state: string): string {
  // Ahora solo pasamos el estado original para que el StatusBadge lo maneje
  return state;
}

/**
 * Lista de órdenes con funcionalidad de filtrado, ordenamiento y paginación
 */
export function OrdersList({ 
  orders, 
  onSelectOrder, 
  onStatusUpdate, 
  onDeleteOrder, 
  updatingOrderIds = new Set(), 
  setUpdatingOrderIds,
  isLoading = false,
  error = null 
}: OrdersListProps) {
  const [sorting, setSorting] = useState<SortingState>([
    { id: "created_at", desc: true }
  ])
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({})
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState<string | null>(null)

  // Función para manejar el cambio en el filtro de estado
  const handleStatusFilterChange = (status: string | null) => {
    setStatusFilter(status)
    
    if (status) {
      // Aplicar filtro por estado
      setColumnFilters(prev => {
        // Eliminar filtro anterior de estado si existe
        const filteredValues = prev.filter(filter => filter.id !== "state")
        // Añadir nuevo filtro
        return [...filteredValues, { id: "state", value: status }]
      })
    } else {
      // Eliminar filtro por estado
      setColumnFilters(prev => prev.filter(filter => filter.id !== "state"))
    }
  }

  const handleStatusUpdate = async (orderId: string, newStatus: string) => {
    // Si se proporciona setUpdatingOrderIds, usarlo, de lo contrario no hacer nada con updatingOrderIds
    setUpdatingOrderIds?.(prev => new Set(prev).add(orderId));
    
    try {
      await onStatusUpdate(orderId, newStatus);
    } finally {
      setUpdatingOrderIds?.(prev => {
        const newSet = new Set(prev);
        newSet.delete(orderId);
        return newSet;
      });
    }
  }

  // En la definición de columnas, modificar la columna "address"
  const columns: ColumnDef<Order>[] = [
    {
      accessorKey: "id",
      header: "# Pedido",
      cell: ({ row }) => {
        // Obtener el índice de la fila en los datos filtrados
        const filteredRows = table.getFilteredRowModel().rows;
        const index = filteredRows.findIndex(r => r.id === row.id);
        // Invertir el orden: la primera fila será la de mayor número
        const displayNumber = filteredRows.length - index;
        return <span className="font-medium">#{displayNumber}</span>;
      },
    },
    {
      accessorKey: "address",
      header: "Dirección",
      cell: ({ row }) => <div className="max-w-[200px] truncate">{row.getValue("address")}</div>,
    },
    {
      accessorKey: "customer_name",
      header: ({ column }) => {
        return (
          <Button variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>
            Cliente
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        )
      },
    },
    {
      accessorKey: "products",
      header: "Productos",
      cell: ({ row }) => {
        const products = row.getValue("products") as { quantity: number }[]
        const totalItems = products.reduce((sum, product) => sum + product.quantity, 0)
        return <div>{totalItems} item(s)</div>
      },
    },
    {
      id: "total_price",
      header: "Total",
      cell: ({ row }) => {
        const products = row.getValue("products") as { price: number, quantity: number }[]
        const totalPrice = products.reduce((sum, product) => sum + (product.price * product.quantity), 0)
        return <div className="font-medium">{formatCOP(totalPrice)}</div>
      },
    },
    {
      accessorKey: "created_at",
      header: ({ column }) => (
        <div className="flex items-center">
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            className="p-0 hover:bg-transparent"
          >
            Fecha
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        </div>
      ),
      cell: ({ row }) => {
        return <div className="font-medium">{formatDate(row.getValue("created_at"))}</div>
      },
      sortingFn: (rowA, rowB, columnId) => {
        const dateA = new Date(rowA.getValue(columnId)).getTime()
        const dateB = new Date(rowB.getValue(columnId)).getTime()
        return dateA < dateB ? -1 : dateA > dateB ? 1 : 0
      },
    },
    {
      accessorKey: "state",
      header: ({ column }) => (
        <div className="flex items-center">
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            className="p-0 hover:bg-transparent"
          >
            Estado
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
          {/* Añadir menú de filtro por estado */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="ml-1 h-8 w-8">
                <Filter className="h-4 w-4" />
                <span className="sr-only">Filtrar por estado</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => handleStatusFilterChange(null)}>
                Todos
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => handleStatusFilterChange(OrderState.PENDING)}>
                Pendiente
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleStatusFilterChange(OrderState.PREPARING)}>
                En Preparación
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleStatusFilterChange(OrderState.DELIVERY)}>
                En Reparto
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleStatusFilterChange(OrderState.COMPLETED)}>
                Completado
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      ),
      cell: ({ row }) => {
        return <StatusBadge status={translateOrderState(row.getValue("state"))} />
      },
    },
    {
      id: "actions",
      cell: ({ row }) => {
        const order = row.original
        const isUpdating = updatingOrderIds.has(order.id);
        
        return (
          <div className="flex items-center justify-end gap-2">
            {/* Acciones de estado */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" disabled={isUpdating}>
                  {isUpdating ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <><Clock className="h-4 w-4" /><span className="sr-only">Estado</span></>
                  )}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem 
                  disabled={order.state === OrderState.PENDING || isUpdating}
                  onClick={() => handleStatusUpdate(order.id, OrderState.PENDING)}
                >
                  <div className="flex items-center">
                    Pendiente
                    {order.state === OrderState.PENDING && <CheckCircle className="ml-2 h-4 w-4 text-green-500" />}
                  </div>
                </DropdownMenuItem>
                <DropdownMenuItem 
                  disabled={order.state === OrderState.PREPARING || isUpdating}
                  onClick={() => handleStatusUpdate(order.id, OrderState.PREPARING)}
                >
                  <div className="flex items-center">
                    En Preparación
                    {order.state === OrderState.PREPARING && <CheckCircle className="ml-2 h-4 w-4 text-green-500" />}
                  </div>
                </DropdownMenuItem>
                <DropdownMenuItem 
                  disabled={order.state === OrderState.DELIVERY || isUpdating}
                  onClick={() => handleStatusUpdate(order.id, OrderState.DELIVERY)}
                >
                  <div className="flex items-center">
                    En Reparto
                    {order.state === OrderState.DELIVERY && <CheckCircle className="ml-2 h-4 w-4 text-green-500" />}
                  </div>
                </DropdownMenuItem>
                <DropdownMenuItem 
                  disabled={order.state === OrderState.COMPLETED || isUpdating}
                  onClick={() => handleStatusUpdate(order.id, OrderState.COMPLETED)}
                >
                  <div className="flex items-center">
                    Completado
                    {order.state === OrderState.COMPLETED && <CheckCircle className="ml-2 h-4 w-4 text-green-500" />}
                  </div>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem 
                  onClick={() => onDeleteOrder(order.id)}
                  disabled={isUpdating}
                  className="text-red-500 focus:text-red-500"
                >
                  <div className="flex items-center">
                    <Trash2 className="mr-2 h-4 w-4" />
                    Eliminar
                  </div>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
            
            {/* Acción de ver detalles */}
            <Button 
              variant="ghost" 
              size="sm" 
              className="h-8 w-8 p-0" 
              onClick={() => {
                // Obtener el índice de la fila en los datos filtrados
                const filteredRows = table.getFilteredRowModel().rows;
                const index = filteredRows.findIndex(r => r.id === row.id);
                // Calcular el índice invertido igual que en la tabla
                const displayNumber = filteredRows.length - index;
                onSelectOrder(order, displayNumber);
              }}
            >
              <span className="sr-only">Ver detalles</span>
              <ChevronDown className="h-4 w-4" />
            </Button>
          </div>
        )
      },
    },
  ]

  // Usar hook de tabla con configuración
  const table = useReactTable({
    data: orders,
    columns,
    state: {
      sorting,
      columnFilters,
      columnVisibility,
      globalFilter: searchTerm,
    },
    enableRowSelection: true,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onColumnVisibilityChange: setColumnVisibility,
    onGlobalFilterChange: setSearchTerm,
    globalFilterFn: "includesString",
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

  // Función para manejar la búsqueda mediante input
  const handleSearch = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value
    setSearchTerm(value)
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-2xl font-bold tracking-tight">Órdenes</h2>
        <div className="flex items-center gap-2">
          <div className="relative w-full sm:w-64">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Buscar órdenes..."
              className="w-full pl-8"
              value={searchTerm}
              onChange={handleSearch}
            />
          </div>
        </div>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  return (
                    <TableHead key={header.id}>
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                    </TableHead>
                  )
                })}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center">
                  <div className="flex flex-col items-center justify-center gap-2">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                    <p className="text-sm text-muted-foreground">Cargando órdenes...</p>
                  </div>
                </TableCell>
              </TableRow>
            ) : error ? (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center">
                  <div className="flex flex-col items-center justify-center gap-2">
                    <p className="text-sm font-medium text-red-500">Error al cargar órdenes</p>
                    <p className="text-xs text-muted-foreground">{error}</p>
                  </div>
                </TableCell>
              </TableRow>
            ) : table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  data-state={row.getIsSelected() && "selected"}
                  className="cursor-pointer"
                  onClick={() => {
                    // Obtener el índice de la fila en los datos filtrados
                    const index = table.getFilteredRowModel().rows.findIndex(r => r.id === row.id);
                    onSelectOrder(row.original, index + 1);
                  }}
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center">
                  No hay órdenes disponibles.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      <div className="flex items-center justify-between gap-2">
        <div className="flex-1 text-sm text-muted-foreground">
          {table.getFilteredRowModel().rows.length} órdenes encontradas.
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            Anterior
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            Siguiente
          </Button>
        </div>
      </div>
    </div>
  )
}