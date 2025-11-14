import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Suggestions from './pages/Suggestions'
import { AuthProvider, useAuth } from './context/AuthContext'

function ProtectedRoute({ children }) {
  const { userID } = useAuth()
  return userID ? children : <Navigate to="/login" replace />
}

function AppRoutes() {
  const { userID } = useAuth()
  
  return (
    <Routes>
      <Route path="/login" element={userID ? <Navigate to="/dashboard" replace /> : <Login />} />
      <Route path="/register" element={userID ? <Navigate to="/dashboard" replace /> : <Register />} />
      <Route 
        path="/dashboard" 
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/trips/:tripID/suggestions" 
        element={
          <ProtectedRoute>
            <Suggestions />
          </ProtectedRoute>
        } 
      />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <AppRoutes />
      </Router>
    </AuthProvider>
  )
}

export default App

