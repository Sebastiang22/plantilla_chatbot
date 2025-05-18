import { NextRequest, NextResponse } from "next/server";
import { API_URL } from "@/lib/config";

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const orderId = params.id;
    
    // Conectar con el backend real usando la URL centralizada
    const response = await fetch(`${API_URL}/orders/${orderId}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      return NextResponse.json(
        { error: errorData.detail || "Error al eliminar el pedido" },
        { status: response.status }
      );
    }
    
    return NextResponse.json(
      { message: `Pedido ${orderId} eliminado correctamente` },
      { status: 200 }
    );
  } catch (error) {
    console.error("Error al eliminar pedido:", error);
    return NextResponse.json(
      { error: "Error al procesar la solicitud" },
      { status: 500 }
    );
  }
} 