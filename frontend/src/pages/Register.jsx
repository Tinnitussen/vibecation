import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import apiClient from '../api/client'
import './Register.css'

function Register() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    name: '',
    password: '',
    confirmPassword: '',
  })
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [errors, setErrors] = useState({})
  const [availability, setAvailability] = useState({ username: null, email: null })
  const [passwordStrength, setPasswordStrength] = useState('weak')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  // Debounced availability check
  useEffect(() => {
    const timer = setTimeout(() => {
      if (formData.username && formData.username.length >= 3) {
        checkAvailability('username', formData.username)
      }
    }, 500)
    return () => clearTimeout(timer)
  }, [formData.username])

  useEffect(() => {
    const timer = setTimeout(() => {
      if (formData.email && formData.email.includes('@')) {
        checkAvailability('email', formData.email)
      }
    }, 500)
    return () => clearTimeout(timer)
  }, [formData.email])

  // Password strength calculation (simplified for demo)
  useEffect(() => {
    const password = formData.password
    if (password.length < 2) {
      setPasswordStrength('weak')
      return
    }
    
    // Very basic strength calculation for demo
    if (password.length >= 6) {
      setPasswordStrength('strong')
    } else if (password.length >= 3) {
      setPasswordStrength('medium')
    } else {
      setPasswordStrength('weak')
    }
  }, [formData.password])

  const checkAvailability = async (field, value) => {
    try {
      const params = { [field]: value }
      const response = await apiClient.get('/users/check-availability', { params })
      setAvailability(prev => ({
        ...prev,
        [field]: response.data.available
      }))
    } catch (err) {
      setAvailability(prev => ({
        ...prev,
        [field]: false
      }))
    }
  }

  const validateForm = () => {
    const newErrors = {}

    if (formData.username.length < 3) {
      newErrors.username = 'Username must be at least 3 characters'
    } else if (!/^[a-zA-Z0-9_]+$/.test(formData.username)) {
      newErrors.username = 'Username can only contain letters, numbers, and underscores'
    } else if (availability.username === false) {
      newErrors.username = 'Username is already taken'
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address'
    } else if (availability.email === false) {
      newErrors.email = 'Email is already registered'
    }

    if (formData.name.length < 2) {
      newErrors.name = 'Name must be at least 2 characters'
    }

    if (formData.password.length < 2) {
      newErrors.password = 'Password must be at least 2 characters'
    }

    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }

    setLoading(true)
    try {
      const response = await apiClient.post('/users', {
        username: formData.username,
        email: formData.email,
        name: formData.name,
        password: formData.password,
      })
      
      login(response.data.userID)
      navigate('/dashboard')
    } catch (err) {
      const errorData = err.response?.data?.detail || {}
      if (typeof errorData === 'string') {
        setErrors({ submit: errorData })
      } else if (errorData.field) {
        setErrors({ [errorData.field]: errorData.error })
      } else {
        setErrors({ submit: 'Registration failed. Please try again.' })
      }
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
    // Clear error for this field
    if (errors[e.target.name]) {
      setErrors({
        ...errors,
        [e.target.name]: ''
      })
    }
  }

  return (
    <div className="register-page">
      <div className="register-card">
        <h1 className="register-title">Create Account</h1>
        <p className="register-subtitle">Sign up to start planning your trips</p>
        
        <form onSubmit={handleSubmit} className="register-form">
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <div className="input-wrapper">
              <input
                id="username"
                name="username"
                type="text"
                value={formData.username}
                onChange={handleChange}
                required
                placeholder="Enter username"
                className={errors.username ? 'error' : ''}
              />
              {formData.username && formData.username.length >= 3 && (
                <span className={`availability-indicator ${availability.username === false ? 'unavailable' : ''}`}>
                  {availability.username === true && '✓'}
                  {availability.username === false && '✗'}
                </span>
              )}
            </div>
            {errors.username && <span className="error-text">{errors.username}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="email">Email</label>
            <div className="input-wrapper">
              <input
                id="email"
                name="email"
                type="email"
                value={formData.email}
                onChange={handleChange}
                required
                placeholder="Enter email"
                className={errors.email ? 'error' : ''}
              />
              {formData.email && formData.email.includes('@') && (
                <span className={`availability-indicator ${availability.email === false ? 'unavailable' : ''}`}>
                  {availability.email === true && '✓'}
                  {availability.email === false && '✗'}
                </span>
              )}
            </div>
            {errors.email && <span className="error-text">{errors.email}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="name">Full Name</label>
            <input
              id="name"
              name="name"
              type="text"
              value={formData.name}
              onChange={handleChange}
              required
              placeholder="Enter your full name"
              className={errors.name ? 'error' : ''}
            />
            {errors.name && <span className="error-text">{errors.name}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <div className="password-input-wrapper">
              <input
                id="password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                value={formData.password}
                onChange={handleChange}
                required
                placeholder="Enter password"
                className={errors.password ? 'error' : ''}
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? '👁️' : '👁️‍🗨️'}
              </button>
            </div>
            {formData.password && (
              <div className="password-strength">
                <div className={`strength-bar ${passwordStrength}`}></div>
                <span className="strength-text">
                  Strength: {passwordStrength.charAt(0).toUpperCase() + passwordStrength.slice(1)}
                </span>
              </div>
            )}
            {errors.password && <span className="error-text">{errors.password}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <div className="password-input-wrapper">
              <input
                id="confirmPassword"
                name="confirmPassword"
                type={showConfirmPassword ? 'text' : 'password'}
                value={formData.confirmPassword}
                onChange={handleChange}
                required
                placeholder="Confirm password"
                className={errors.confirmPassword ? 'error' : ''}
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              >
                {showConfirmPassword ? '👁️' : '👁️‍🗨️'}
              </button>
            </div>
            {errors.confirmPassword && <span className="error-text">{errors.confirmPassword}</span>}
          </div>

          {errors.submit && <div className="error-message">{errors.submit}</div>}

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        <p className="login-link">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </div>
    </div>
  )
}

export default Register

