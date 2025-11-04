'use client'

import { useAuth } from '@/lib/hooks/useAuth'

export default function Home() {
  const { user, isLoading, isAuthenticated } = useAuth()
  
  return (
    <div className="p-8">
      <h1>Auth Status</h1>
      <pre>{JSON.stringify({ user, isLoading, isAuthenticated }, null, 2)}</pre>
    </div>
  )
}