'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { Loader2 } from 'lucide-react';

interface GlobalAuthGuardProps {
  children: React.ReactNode;
}

// Rutas que no requieren autenticación
const PUBLIC_ROUTES = ['/login'];

export default function GlobalAuthGuard({ children }: GlobalAuthGuardProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  // Verificar si la ruta actual es pública
  const isPublicRoute = PUBLIC_ROUTES.includes(pathname);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        // Si es una ruta pública, no verificamos autenticación
        if (isPublicRoute) {
          setIsLoading(false);
          return;
        }

        // Verificar si existe un token en localStorage
        const token = localStorage.getItem('token');
        const tokenExpiry = localStorage.getItem('tokenExpiry');
        
        if (!token || !tokenExpiry) {
          router.push('/login');
          return;
        }
        
        // Verificar si el token ha expirado
        const expiry = new Date(tokenExpiry);
        if (expiry < new Date()) {
          // Token expirado, eliminar y redirigir a login
          localStorage.removeItem('token');
          localStorage.removeItem('username');
          localStorage.removeItem('tokenExpiry');
          router.push('/login');
          return;
        }

        // Verificar si el token es válido con una llamada al backend
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/me`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (response.ok) {
          setIsAuthenticated(true);
        } else {
          // Token inválido, redirigir a login
          localStorage.removeItem('token');
          localStorage.removeItem('username');
          localStorage.removeItem('tokenExpiry');
          router.push('/login');
        }
      } catch (error) {
        console.error('Error de autenticación:', error);
        if (!isPublicRoute) {
          router.push('/login');
        }
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, [router, pathname, isPublicRoute]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    );
  }

  // Si es una ruta pública o el usuario está autenticado, mostrar los hijos
  return (isPublicRoute || isAuthenticated) ? <>{children}</> : null;
} 