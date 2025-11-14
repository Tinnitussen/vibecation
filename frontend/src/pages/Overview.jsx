import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import apiClient from '../api/client'
import './Overview.css'

function Overview() {
  const { tripID } = useParams()
  const { userID } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [overviewData, setOverviewData] = useState(null)
  const [error, setError] = useState(null)
  const [inviteCode, setInviteCode] = useState(null)
  const [loadingInviteCode, setLoadingInviteCode] = useState(false)

  useEffect(() => {
    loadOverviewData()
    loadInviteCode()
  }, [tripID, userID])

  const loadInviteCode = async () => {
    try {
      setLoadingInviteCode(true)
      const response = await apiClient.get(`/trips/${tripID}/invite-code`, {
        params: { userID }
      })
      setInviteCode(response.data.inviteCode)
    } catch (err) {
      // User is not owner or endpoint doesn't exist - silently fail
      setInviteCode(null)
    } finally {
      setLoadingInviteCode(false)
    }
  }

  const loadOverviewData = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get(`/trips/${tripID}/overview`)
      setOverviewData(response.data)
      setError(null)
    } catch (err) {
      setError('Failed to load trip overview')
      console.error('Error loading overview:', err)
    } finally {
      setLoading(false)
    }
  }

  const getActivityTypeColor = (type) => {
    const colors = {
      sightseeing: '#9C27B0',
      relaxing: '#4CAF50',
      food: '#FF9800',
      entertainment: '#673AB7',
      watersport: '#00BCD4',
      adventure: '#FF5722',
      attraction: '#667eea',
      travel: '#f093fb'
    }
    return colors[type] || '#757575'
  }

  if (loading) {
    return (
      <div className="overview-page">
        <div className="overview-loading">
          <div className="spinner"></div>
          <p>Loading trip overview...</p>
        </div>
      </div>
    )
  }

  if (error || !overviewData) {
    return (
      <div className="overview-page">
        <div className="overview-error">
          <p>{error || 'Trip overview not found'}</p>
          <button onClick={() => navigate('/dashboard')} className="back-btn">
            Back to Dashboard
          </button>
        </div>
      </div>
    )
  }

  const { trip, decisions } = overviewData

  return (
    <div className="overview-page">
      <header className="overview-header">
        <div className="header-top-actions">
          <button 
            className="btn-home"
            onClick={() => navigate('/dashboard')}
            title="Home"
          >
            🏠 Home
          </button>
          <button className="back-button" onClick={() => navigate('/dashboard')}>
            ← Back
          </button>
        </div>
        <div className="header-content">
          <h1>{trip.title}</h1>
          {trip.description && <p className="trip-description">{trip.description}</p>}
          <div className="trip-meta">
            <span className="meta-item">👥 {trip.members?.length || 0} members</span>
            <span className="meta-item">📊 {decisions.total_votes} total votes</span>
            <span className="meta-item">Status: {trip.status}</span>
          </div>
          {inviteCode && (
            <div className="invite-code-section">
              <div className="invite-code-label">Invite Code:</div>
              <div className="invite-code-container">
                <code className="invite-code-display">{inviteCode}</code>
                <button
                  className="btn-copy-invite"
                  onClick={() => {
                    navigator.clipboard.writeText(inviteCode)
                    toast.success('Invite code copied to clipboard!')
                  }}
                  title="Copy invite code"
                >
                  📋 Copy
                </button>
              </div>
              <small>Share this code with others to let them join your trip</small>
            </div>
          )}
        </div>
      </header>

      <main className="overview-main">
        <div className="overview-stats">
          <div className="stat-card">
            <div className="stat-icon">🎯</div>
            <div className="stat-value">{decisions.top_activities.length}</div>
            <div className="stat-label">Top Activities</div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">📍</div>
            <div className="stat-value">{decisions.top_locations.length}</div>
            <div className="stat-label">Top Locations</div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">🍽️</div>
            <div className="stat-value">{decisions.top_cuisines.length}</div>
            <div className="stat-label">Top Cuisines</div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">✅</div>
            <div className="stat-value">{decisions.total_votes}</div>
            <div className="stat-label">Total Votes</div>
          </div>
        </div>

        <section className="decisions-section">
          <h2>Final Decisions</h2>
          <p className="section-subtitle">Based on group voting and preferences</p>

          {decisions.top_activities.length > 0 && (
            <div className="decision-card">
              <div className="decision-header">
                <h3>🎯 Top Activities</h3>
                <span className="decision-count">{decisions.top_activities.length} activities</span>
              </div>
              <div className="activities-grid">
                {decisions.top_activities.map((activity, idx) => (
                  <div key={activity.activity_id || idx} className="activity-card">
                    <div className="activity-type-badge" style={{
                      backgroundColor: getActivityTypeColor(activity.type)
                    }}>
                      {activity.type}
                    </div>
                    <h4>{activity.activity_name}</h4>
                    <p className="activity-description">{activity.description}</p>
                    <div className="activity-votes">
                      <span className="vote-badge upvote">↑ {activity.upvotes}</span>
                      <span className="vote-badge downvote">↓ {activity.downvotes}</span>
                      <span className="net-score">Net: {activity.net_score}</span>
                    </div>
                    {activity.location && (
                      <p className="activity-location">📍 {activity.location}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {decisions.top_locations.length > 0 && (
            <div className="decision-card">
              <div className="decision-header">
                <h3>📍 Top Locations</h3>
                <span className="decision-count">{decisions.top_locations.length} locations</span>
              </div>
              <div className="locations-grid">
                {decisions.top_locations.map((location, idx) => (
                  <div key={location.location_id || idx} className="location-card">
                    <h4>{location.name}</h4>
                    <p className="location-description">{location.description}</p>
                    <div className="location-votes">
                      <span className="vote-badge upvote">↑ {location.upvotes}</span>
                      <span className="vote-badge downvote">↓ {location.downvotes}</span>
                      <span className="net-score">Net: {location.net_score}</span>
                    </div>
                    {location.lat && location.lon && (
                      <p className="location-coords">
                        📍 {location.lat.toFixed(4)}, {location.lon.toFixed(4)}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {decisions.top_cuisines.length > 0 && (
            <div className="decision-card">
              <div className="decision-header">
                <h3>🍽️ Top Cuisines</h3>
                <span className="decision-count">{decisions.top_cuisines.length} cuisines</span>
              </div>
              <div className="cuisines-grid">
                {decisions.top_cuisines.map((cuisine, idx) => (
                  <div key={cuisine.name || idx} className="cuisine-card">
                    <h4>{cuisine.name}</h4>
                    <div className="cuisine-votes">
                      <span className="vote-count">{cuisine.votes} votes</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {decisions.top_activities.length === 0 && 
           decisions.top_locations.length === 0 && 
           decisions.top_cuisines.length === 0 && (
            <div className="empty-decisions">
              <div className="empty-icon">🗳️</div>
              <h3>No decisions yet</h3>
              <p>Start voting on suggestions to see final decisions here!</p>
              <button 
                className="primary-btn"
                onClick={() => navigate(`/trips/${tripID}/suggestions`)}
              >
                Go to Suggestions
              </button>
            </div>
          )}
        </section>

        <div className="overview-actions">
          <button 
            className="action-btn secondary"
            onClick={() => navigate(`/trips/${tripID}/suggestions`)}
          >
            View Suggestions
          </button>
          <button 
            className="action-btn primary"
            onClick={() => navigate('/dashboard')}
          >
            Back to Dashboard
          </button>
        </div>
      </main>
    </div>
  )
}

export default Overview

