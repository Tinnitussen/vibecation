import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import apiClient from '../api/client'
import './TripDetails.css'

function TripDetails() {
  const { tripID } = useParams()
  const { userID } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [trip, setTrip] = useState(null)
  const [details, setDetails] = useState(null)

  useEffect(() => {
    loadTripData()
    loadDetails()
  }, [tripID])

  const loadTripData = async () => {
    try {
      const response = await apiClient.get(`/trips/${tripID}`)
      setTrip(response.data)
    } catch (err) {
      console.error('Failed to load trip:', err)
      toast.error('Failed to load trip information')
    }
  }

  const loadDetails = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get(`/trips/${tripID}/details`)
      setDetails(response.data)
    } catch (err) {
      console.error('Failed to load trip details:', err)
      toast.error('Failed to load trip details')
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
      attraction: '#667eea',
      travel: '#f093fb',
      accommodation: '#757575'
    }
    return colors[type] || '#757575'
  }

  const getVigorColor = (vigor) => {
    const colors = {
      low: '#81C784',
      medium: '#FFB74D',
      high: '#E57373'
    }
    return colors[vigor] || '#757575'
  }

  const formatDateTime = (dateTimeStr) => {
    if (!dateTimeStr) return ''
    try {
      const date = new Date(dateTimeStr)
      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch (e) {
      return dateTimeStr
    }
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return ''
    try {
      const date = new Date(dateStr)
      return date.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    } catch (e) {
      return dateStr
    }
  }

  if (loading) {
    return (
      <div className="trip-details-page">
        <div className="details-loading">
          <div className="spinner"></div>
          <p>Loading trip details...</p>
        </div>
      </div>
    )
  }

  if (!details) {
    return (
      <div className="trip-details-page">
        <div className="details-error">
          <p>Failed to load trip details</p>
          <button onClick={() => navigate('/dashboard')} className="back-btn">
            Back to Dashboard
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="trip-details-page">
      <header className="details-header">
        <div className="header-top">
          <button 
            className="btn-home"
            onClick={() => navigate('/dashboard')}
            title="Home"
          >
            🏠 Home
          </button>
          <button 
            className="back-button"
            onClick={() => navigate(`/trips/${tripID}/overview`)}
          >
            ← Back to Overview
          </button>
        </div>
        <div className="header-content">
          <h1>{trip?.title || 'Trip Details'}</h1>
          <div className="breadcrumb">
            Dashboard &gt; Trip Overview &gt; Details
          </div>
        </div>
      </header>

      <main className="details-main">
        {details.trip_summary && (
          <div className="trip-summary-section">
            <h2>Trip Summary</h2>
            <p className="trip-summary-text">{details.trip_summary}</p>
          </div>
        )}

        <div className="itinerary-timeline">
          <h2>Itinerary</h2>
          {details.days && details.days.length > 0 ? (
            <div className="days-container">
              {details.days.map((day, dayIndex) => (
                <div key={day.id || dayIndex} className="day-card">
                  <div className="day-header">
                    <div className="day-number">Day {day.id}</div>
                    <div className="day-date">{formatDate(day.date)}</div>
                    <div className="day-location">📍 {day.location}</div>
                  </div>
                  {day.description && (
                    <p className="day-description">{day.description}</p>
                  )}
                  
                  {day.activities && day.activities.length > 0 && (
                    <div className="activities-list">
                      {day.activities.map((activity, actIndex) => (
                        <div key={activity.id || activity.activity_id || actIndex} className="activity-card">
                          <div className="activity-header">
                            <div className="activity-type-badge" style={{
                              backgroundColor: getActivityTypeColor(activity.type)
                            }}>
                              {activity.type}
                            </div>
                            {activity.vigor && (
                              <span 
                                className="vigor-badge"
                                style={{ 
                                  backgroundColor: getVigorColor(activity.vigor),
                                  color: '#FFFFFF'
                                }}
                              >
                                {activity.vigor}
                              </span>
                            )}
                          </div>
                          <h3 className="activity-name">{activity.activity_name}</h3>
                          <p className="activity-description">{activity.description}</p>
                          
                          <div className="activity-details">
                            {activity.from_date_time && activity.to_date_time && (
                              <div className="activity-time">
                                <span className="time-icon">🕐</span>
                                <span>
                                  {formatDateTime(activity.from_date_time)} - {formatDateTime(activity.to_date_time)}
                                </span>
                              </div>
                            )}
                            {activity.location && (
                              <div className="activity-location">
                                <span className="location-icon">📍</span>
                                <span>{activity.location}</span>
                              </div>
                            )}
                            {(activity.start_lat && activity.start_lon) && (
                              <div className="activity-coordinates">
                                <span className="coord-icon">🗺️</span>
                                <span>
                                  {activity.start_lat.toFixed(4)}, {activity.start_lon.toFixed(4)}
                                </span>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-itinerary">
              <p>No itinerary available for this trip.</p>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

export default TripDetails
