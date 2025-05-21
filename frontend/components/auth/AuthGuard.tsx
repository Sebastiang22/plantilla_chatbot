import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';

interface AuthGuardProps {
  children: React.ReactNode;
}

export default function AuthGuard({ children }: AuthGuardProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const checkAuth = async () => {
      try {
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
        router.push('/login');
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, [router]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    );
  }

  return isAuthenticated ? <>{children}</> : null;
} 