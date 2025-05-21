'use client';

import GlobalAuthGuard from './GlobalAuthGuard';

interface AuthWrapperProps {
  children: React.ReactNode;
}

// Este componente simplemente envuelve el GlobalAuthGuard para permitir
// que el layout.tsx permanezca como un componente de servidor
export default function AuthWrapper({ children }: AuthWrapperProps) {
  return <GlobalAuthGuard>{children}</GlobalAuthGuard>;
} 