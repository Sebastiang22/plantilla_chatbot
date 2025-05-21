'use client';

import LoginForm from '@/components/auth/LoginForm';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { DashboardHeader } from '@/components/features/dashboard';
import { useTheme } from 'next-themes';

export default function LoginPage() {
  const [checking, setChecking] = useState(true);
  const router = useRouter();
  const { theme, setTheme } = useTheme();

  useEffect(() => {
    // Verificar si ya hay una sesión activa
    const token = localStorage.getItem('token');
    const tokenExpiry = localStorage.getItem('tokenExpiry');
    
    if (token && tokenExpiry) {
      // Verificar si el token no ha expirado
      const expiry = new Date(tokenExpiry);
      if (expiry > new Date()) {
        // Token válido, redirigir a la página principal
        router.push('/');
        return;
      } else {
        // Limpiar token expirado
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        localStorage.removeItem('tokenExpiry');
      }
    }
    
    setChecking(false);
  }, [router]);

  if (checking) {
    return null; // O un componente de carga
  }

  return (
    <>
      <DashboardHeader
        showThemeToggle={true}
        showMenuButton={false}
        showFilterButton={false}
        showUpdateButton={false}
        setTheme={setTheme}
        theme={theme}
      />
      <div className="flex items-center justify-center min-h-screen bg-gray-100 p-4">
        <LoginForm />
      </div>
    </>
  );
}