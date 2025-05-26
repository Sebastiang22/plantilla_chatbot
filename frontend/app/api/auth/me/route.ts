import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    // Obtener el token del header Authorization
    const authHeader = request.headers.get('Authorization');
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return NextResponse.json(
        { detail: 'Token de autenticación no proporcionado' },
        { status: 401 }
      );
    }
    
    
    const token = authHeader.split(' ')[1];
    
    // Verificar el token con el backend
    const response = await fetch(`https://juanchito-plaza.blueriver-8537145c.westus2.azurecontainerapps.io/api/v1/auth/me`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!response.ok) {
      return NextResponse.json(
        { detail: 'Token inválido o sesión expirada' },
        { status: response.status }
      );
    }
    
    const data = await response.json();
    return NextResponse.json(data);
    
  } catch (error) {
    console.error('Error al verificar token:', error);
    return NextResponse.json(
      { detail: 'Error interno del servidor' },
      { status: 500 }
    );
  }
} 