import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const username = formData.get('username');
    const password = formData.get('password');

    // Validar campos
    if (!username || !password) {
      return NextResponse.json(
        { detail: 'Username y password son obligatorios' },
        { status: 400 }
      );
    }

    // Enviar petición al backend
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        username: username.toString(),
        password: password.toString(),
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || 'Error de autenticación' },
        { status: response.status }
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error('Error en autenticación:', error);
    return NextResponse.json(
      { detail: 'Error interno del servidor' },
      { status: 500 }
    );
  }
} 