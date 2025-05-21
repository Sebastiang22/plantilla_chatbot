"use client"

import { useState } from "react"
import { OrderList } from "@/components/order-list"
import OrderDetail from "./OrderDetail"
import SearchBar from "./SearchBar"
import Statistics from "./Statistics"
import { useOrders } from "../providers"
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";

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
  const { orders, setDateFilter, dateFilter } = useOrders();
  const [startDate, setStartDate] = useState<Date | null>(null);
  const [endDate, setEndDate] = useState<Date | null>(null);

  const handleDateChange = (dates: [Date | null, Date | null]) => {
    const [start, end] = dates;
    setStartDate(start);
    setEndDate(end);
    if (start && end) {
      const startStr = start.toISOString().split('T')[0];
      const endStr = end.toISOString().split('T')[0];
      setDateFilter({ start: startStr, end: endStr });
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6">Café Order Management</h1>
      <div className="mb-4">
        <label className="block mb-2 font-semibold">Filtrar por rango de fechas:</label>
        <DatePicker
          selectsRange
          startDate={startDate}
          endDate={endDate}
          onChange={handleDateChange}
          dateFormat="yyyy-MM-dd"
          isClearable={true}
          className="border rounded px-2 py-1"
        />
      </div>
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

