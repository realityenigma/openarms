import React from 'react'
import { Link, NavLink } from 'react-router-dom'
import { useAuthStore } from '../store/auth'

const TopNav: React.FC = () => {
  const { isAuthenticated, user, logout } = useAuthStore((state) => ({
    isAuthenticated: state.isAuthenticated,
    user: state.user,
    logout: state.logout,
  }))

  return (
    <header className="oa-topbar">
      <div className="oa-topbar-inner">
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <Link to="/" className="oa-brand">
            OpenArms
          </Link>
          <NavLink to="/" className="oa-nav-link">
            Home
          </NavLink>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {isAuthenticated ? (
            <>
              <Link to="/new-model" className="oa-pill-btn oa-pill-btn-primary">
                + New model
              </Link>
              <Link to="/new-dataset" className="oa-pill-btn">
                + New dataset
              </Link>
              <span style={{ color: '#374151', fontSize: 14 }}>@{user?.username}</span>
              <button
                type="button"
                onClick={logout}
                className="oa-pill-btn"
              >
                Logout
              </button>
            </>
          ) : (
            <Link to="/" style={{ color: '#2563eb', textDecoration: 'none', fontSize: 14, fontWeight: 500 }}>
              Sign in from Home
            </Link>
          )}
        </div>
      </div>
    </header>
  )
}

export default TopNav
