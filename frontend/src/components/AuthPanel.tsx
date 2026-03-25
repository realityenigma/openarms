import React, { useState } from 'react'
import { getUserProfile, loginUser, registerUser } from '../api/client'
import { useAuthStore } from '../store/auth'

const AuthPanel: React.FC = () => {
  const { isAuthenticated, user, logout, setAuth } = useAuthStore((state) => ({
    isAuthenticated: state.isAuthenticated,
    user: state.user,
    logout: state.logout,
    setAuth: state.setAuth,
  }))

  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [email, setEmail] = useState('')
  const [fullName, setFullName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const onLogin = async (event: React.FormEvent) => {
    event.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const token = await loginUser({ username, password })
      const profile = await getUserProfile(username)
      setAuth(profile, token.access_token)
      setPassword('')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Login failed'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  const onRegister = async (event: React.FormEvent) => {
    event.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await registerUser({ username, password, email, full_name: fullName || undefined })
      const token = await loginUser({ username, password })
      const profile = await getUserProfile(username)
      setAuth(profile, token.access_token)
      setPassword('')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Registration failed'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  if (isAuthenticated && user) {
    return (
      <section style={{ border: '1px solid #e5e7eb', borderRadius: 8, padding: 12, background: '#fff' }}>
        <p style={{ margin: 0 }}>
          Signed in as <strong>{user.username}</strong>
        </p>
        <button
          type="button"
          onClick={logout}
          style={{ marginTop: 8, padding: '6px 10px', border: '1px solid #d1d5db', borderRadius: 6, background: '#fff' }}
        >
          Logout
        </button>
      </section>
    )
  }

  return (
    <section style={{ border: '1px solid #e5e7eb', borderRadius: 8, padding: 12, background: '#fff' }}>
      <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
        <button
          type="button"
          onClick={() => setMode('login')}
          style={{ padding: '6px 10px', border: '1px solid #d1d5db', borderRadius: 6, background: mode === 'login' ? '#e5e7eb' : '#fff' }}
        >
          Login
        </button>
        <button
          type="button"
          onClick={() => setMode('register')}
          style={{ padding: '6px 10px', border: '1px solid #d1d5db', borderRadius: 6, background: mode === 'register' ? '#e5e7eb' : '#fff' }}
        >
          Register
        </button>
      </div>

      <form onSubmit={mode === 'login' ? onLogin : onRegister} style={{ display: 'grid', gap: 8 }}>
        <input
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          placeholder="Username"
          required
          style={{ padding: '8px 10px', border: '1px solid #d1d5db', borderRadius: 6 }}
        />
        <input
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="Password"
          required
          style={{ padding: '8px 10px', border: '1px solid #d1d5db', borderRadius: 6 }}
        />

        {mode === 'register' ? (
          <>
            <input
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="Email"
              required
              style={{ padding: '8px 10px', border: '1px solid #d1d5db', borderRadius: 6 }}
            />
            <input
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
              placeholder="Full name (optional)"
              style={{ padding: '8px 10px', border: '1px solid #d1d5db', borderRadius: 6 }}
            />
          </>
        ) : null}

        <button
          type="submit"
          disabled={loading}
          style={{ padding: '8px 10px', border: '1px solid #d1d5db', borderRadius: 6, background: '#fff' }}
        >
          {loading ? 'Please wait…' : mode === 'login' ? 'Login' : 'Create account'}
        </button>
      </form>

      {error ? <p style={{ marginBottom: 0, color: '#b91c1c' }}>{error}</p> : null}
    </section>
  )
}

export default AuthPanel
