"use client"

import { useState } from "react"
import { OrderList } from "@/components/order-list"
import OrderDetail from "./OrderDetail"
import SearchBar from "./SearchBar"
import Statistics from "./Statistics"
import { useOrders } from "../providers"

interface Product {
  name: string;
  quantity: number;
  price: number;
}

interface Order {
  id: string;
  address: string;
  customer_name: string;
  products: Product[];
  created_at: string;
  updated_at: string;
  state: string;
}

export default function OrderDashboard() {
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null)
  const [searchTerm, setSearchTerm] = useState("")
  const { orders } = useOrders();

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6">Café Order Management</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2">
          <SearchBar onSearch={setSearchTerm} />
          <OrderList orders={orders} searchTerm={searchTerm} onSelectOrder={setSelectedOrder} />
        </div>
        <div>
          <Statistics />
          {selectedOrder && <OrderDetail order={selectedOrder} />}
        </div>
      </div>
    </div>
  )
}

