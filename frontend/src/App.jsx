import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Overview from './pages/Overview'
import Suggestions from './pages/Suggestions'
import Brainstorm from './pages/Brainstorm'
import TripDetails from './pages/TripDetails'
import { AuthProvider, useAuth } from './context/AuthContext'
import { ToastProvider } from './context/ToastContext'

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
        path="/trips/:tripID/overview" 
        element={
          <ProtectedRoute>
            <Overview />
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
      <Route 
        path="/trips/:tripID/brainstorm" 
        element={
          <ProtectedRoute>
            <Brainstorm />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/trips/:tripID/details" 
        element={
          <ProtectedRoute>
            <TripDetails />
          </ProtectedRoute>
        } 
      />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <Router>
          <AppRoutes />
        </Router>
      </AuthProvider>
    </ToastProvider>
  )
}

export default App

