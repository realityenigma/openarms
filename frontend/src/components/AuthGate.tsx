import React from 'react'
import { useAuthStore } from '../store/auth'

type AuthGateProps = {
  children: React.ReactNode
}

const AuthGate: React.FC<AuthGateProps> = ({ children }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)

  if (!isAuthenticated) {
    return <p style={{ margin: 0, color: '#4b5563' }}>Login required to upload files.</p>
  }

  return <>{children}</>
}

export default AuthGate
