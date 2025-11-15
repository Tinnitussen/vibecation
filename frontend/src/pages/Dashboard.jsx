import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import ConfirmDialog from '../components/ConfirmDialog'
import apiClient from '../api/client'
import './Dashboard.css'

function Dashboard() {
  const { userID, logout } = useAuth()
  const toast = useToast()
  const [user, setUser] = useState(null)
  const [trips, setTrips] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showJoinModal, setShowJoinModal] = useState(false)
  const [showConfirmDialog, setShowConfirmDialog] = useState(false)
  const [tripToDelete, setTripToDelete] = useState(null)
  const [newTrip, setNewTrip] = useState({ title: '', description: '' })
  const [joinCode, setJoinCode] = useState('')
  const [creating, setCreating] = useState(false)
  const [joining, setJoining] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    if (userID) {
      loadUserData()
      loadTrips()
    }
  }, [userID])

  const loadUserData = async () => {
    try {
      const response = await apiClient.get(`/users/${userID}`)
      setUser(response.data)
    } catch (err) {
      console.error('Failed to load user data:', err)
    }
  }

  const loadTrips = async () => {
    try {
      const response = await apiClient.get('/dashboard', {
        params: { userID }
      })
      const tripIDs = response.data.yourTrips
      
      // Fetch details for each trip
      const tripPromises = tripIDs.map(async (tripID) => {
        try {
          const tripInfo = await apiClient.get('/tripinfo', {
            params: { tripID }
          })
          return { tripID, ...tripInfo.data }
        } catch (err) {
          console.error(`Failed to load trip ${tripID}:`, err)
          return null
        }
      })
      
      const tripDetails = await Promise.all(tripPromises)
      setTrips(tripDetails.filter(t => t !== null))
    } catch (err) {
      console.error('Failed to load trips:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateTrip = async (e) => {
    e.preventDefault()
    setCreating(true)
    
    try {
      const response = await apiClient.post(`/createtrip?userID=${userID}`, {
        title: newTrip.title,
        description: newTrip.description || undefined,
        members: []
      })
      
      setShowCreateModal(false)
      setNewTrip({ title: '', description: '' })
      toast.success('Trip created successfully!')
      loadTrips()
      navigate(`/trips/${response.data.tripID}/overview`)
    } catch (err) {
      console.error('Failed to create trip:', err)
      toast.error('Failed to create trip. Please try again.')
    } finally {
      setCreating(false)
    }
  }

  const handleJoinTrip = async (e) => {
    e.preventDefault()
    setJoining(true)
    
    try {
      const response = await apiClient.post('/trips/join', null, {
        params: {
          inviteCode: joinCode.toUpperCase().trim(),
          userID: userID
        }
      })
      
      if (response.data.alreadyMember) {
        toast.warning('You are already a member of this trip!')
      } else {
        toast.success(`Successfully joined "${response.data.title}"!`)
        setShowJoinModal(false)
        setJoinCode('')
        loadTrips()
        navigate(`/trips/${response.data.tripID}/overview`)
      }
    } catch (err) {
      console.error('Failed to join trip:', err)
      if (err.response?.status === 404) {
        toast.error('Invalid invite code. Please check and try again.')
      } else {
        toast.error('Failed to join trip. Please try again.')
      }
    } finally {
      setJoining(false)
    }
  }

  const handleDeleteTrip = (tripID) => {
    setTripToDelete(tripID)
    setShowConfirmDialog(true)
  }

  const confirmDeleteTrip = async () => {
    if (!tripToDelete) return
    
    try {
      await apiClient.delete(`/trips/${tripToDelete}`)
      toast.success('Trip deleted successfully')
      loadTrips()
    } catch (err) {
      console.error('Failed to delete trip:', err)
      toast.error('Failed to delete trip. Please try again.')
    } finally {
      setShowConfirmDialog(false)
      setTripToDelete(null)
    }
  }

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="spinner"></div>
      </div>
    )
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-content">
          <div className="header-left">
            <button 
              className="btn-home"
              onClick={() => navigate('/dashboard')}
              title="Home"
            >
              🏠
            </button>
            <h1 className="logo">Vibecation</h1>
          </div>
          <div className="user-menu">
            <span className="user-name">{user?.name || 'User'}</span>
            <button onClick={logout} className="btn-logout">Logout</button>
          </div>
        </div>
      </header>

      <main className="dashboard-main">
        <div className="dashboard-content">
          <div className="dashboard-title-section">
            <h2>My Trips</h2>
            <div className="dashboard-actions">
              <button 
                className="btn-join-trip"
                onClick={() => setShowJoinModal(true)}
              >
                🔗 Join Trip
              </button>
              <button 
                className="btn-create-trip"
                onClick={() => setShowCreateModal(true)}
              >
                + Create New Trip
              </button>
            </div>
          </div>

          {trips.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">✈️</div>
              <h3>No trips yet</h3>
              <p>Start planning your first adventure!</p>
              <button 
                className="btn-primary"
                onClick={() => setShowCreateModal(true)}
              >
                Create your first trip
              </button>
            </div>
          ) : (
            <div className="trip-grid">
              {trips.map((trip) => (
                <div key={trip.tripID} className="trip-card">
                  <div className="trip-card-header">
                    <h3 className="trip-title">{trip.title}</h3>
                    <button
                      className="btn-delete"
                      onClick={() => handleDeleteTrip(trip.tripID)}
                      title="Delete trip"
                    >
                      🗑️
                    </button>
                  </div>
                  {trip.description && (
                    <p className="trip-description">{trip.description}</p>
                  )}
                  <div className="trip-meta">
                    <span className="member-count">
                      👥 {trip.members?.length || 0} member{trip.members?.length !== 1 ? 's' : ''}
                    </span>
                  </div>
                  <div className="trip-actions">
                    <button
                      className="btn-view"
                      onClick={() => navigate(`/trips/${trip.tripID}/overview`)}
                    >
                      View
                    </button>
                    <button
                      className="btn-brainstorm"
                      onClick={() => navigate(`/trips/${trip.tripID}/brainstorm`)}
                    >
                      Brainstorm
                    </button>
                    <button
                      className="btn-suggestions"
                      onClick={() => navigate(`/trips/${trip.tripID}/suggestions`)}
                    >
                      Suggestions
                    </button>
                    <button
                      className="btn-details"
                      onClick={() => navigate(`/trips/${trip.tripID}/details`)}
                    >
                      Details
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Create New Trip</h2>
            <form onSubmit={handleCreateTrip}>
              <div className="form-group">
                <label htmlFor="trip-title">Trip Title *</label>
                <input
                  id="trip-title"
                  type="text"
                  value={newTrip.title}
                  onChange={(e) => setNewTrip({ ...newTrip, title: e.target.value })}
                  required
                  placeholder="e.g., Summer in Spain"
                />
              </div>
              <div className="form-group">
                <label htmlFor="trip-description">Description</label>
                <textarea
                  id="trip-description"
                  value={newTrip.description}
                  onChange={(e) => setNewTrip({ ...newTrip, description: e.target.value })}
                  placeholder="Optional description"
                  rows="3"
                />
              </div>
              <div className="modal-actions">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowCreateModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={creating}>
                  {creating ? 'Creating...' : 'Create Trip'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showJoinModal && (
        <div className="modal-overlay" onClick={() => setShowJoinModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Join Trip with Invite Code</h2>
            <form onSubmit={handleJoinTrip}>
              <div className="form-group">
                <label htmlFor="join-code">Invite Code *</label>
                <input
                  id="join-code"
                  type="text"
                  value={joinCode}
                  onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
                  placeholder="Enter 8-character code"
                  maxLength={8}
                  required
                  style={{ 
                    textTransform: 'uppercase',
                    fontFamily: 'monospace',
                    fontSize: '1.2em',
                    letterSpacing: '0.1em',
                    textAlign: 'center'
                  }}
                />
                <small>Enter the invite code shared by the trip owner</small>
              </div>
              <div className="modal-actions">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => {
                    setShowJoinModal(false)
                    setJoinCode('')
                  }}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={joining}>
                  {joining ? 'Joining...' : 'Join Trip'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <button
        className="fab"
        onClick={() => setShowCreateModal(true)}
        title="Create new trip"
      >
        +
      </button>

      {showConfirmDialog && (
        <ConfirmDialog
          title="Delete Trip"
          message="Are you sure you want to delete this trip? This action cannot be undone."
          onConfirm={confirmDeleteTrip}
          onCancel={() => {
            setShowConfirmDialog(false)
            setTripToDelete(null)
          }}
        />
      )}
    </div>
  )
}

export default Dashboard

