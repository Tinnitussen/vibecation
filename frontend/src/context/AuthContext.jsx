import { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext()

export function AuthProvider({ children }) {
  const [userID, setUserID] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check for stored userID on mount
    const storedUserID = localStorage.getItem('userID')
    if (storedUserID) {
      setUserID(storedUserID)
    }
    setLoading(false)
  }, [])

  const login = (id) => {
    setUserID(id)
    localStorage.setItem('userID', id)
  }

  const logout = () => {
    setUserID(null)
    localStorage.removeItem('userID')
  }

  return (
    <AuthContext.Provider value={{ userID, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

