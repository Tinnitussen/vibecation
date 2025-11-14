import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import apiClient from '../api/client'
import './Suggestions.css'

function Suggestions() {
  const { tripID } = useParams()
  const { userID } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('activities')
  const [loading, setLoading] = useState(true)
  const [suggestions, setSuggestions] = useState([])
  const [participants, setParticipants] = useState([])
  const [activities, setActivities] = useState([])
  const [locations, setLocations] = useState([])
  const [cuisines, setCuisines] = useState([])
  const [tripInfo, setTripInfo] = useState(null)
  const [brainstormStatus, setBrainstormStatus] = useState(null)

  useEffect(() => {
    loadData()
  }, [tripID])

  const loadData = async () => {
    setLoading(true)
    try {
      // Load trip info
      const tripResponse = await apiClient.get('/tripinfo', {
        params: { tripID }
      })
      setTripInfo(tripResponse.data)

      // Check brainstorm completion status
      let completionStatus = { allCompleted: true } // Default to allow access for backward compatibility
      try {
        const completionResponse = await apiClient.get('/check_brainstorm_completion', {
          params: { tripID }
        })
        completionStatus = completionResponse.data
        setBrainstormStatus(completionStatus)
      } catch (err) {
        console.error('Failed to check brainstorm completion:', err)
        // If endpoint doesn't exist or fails, allow access (backward compatibility)
        setBrainstormStatus(completionStatus)
      }

      // Only load suggestions if all members have finished brainstorming
      if (completionStatus.allCompleted) {
        // Load suggestions
        const suggestionsResponse = await apiClient.get('/get_all_trip_suggestions', {
          params: { tripID }
        })
        setSuggestions(suggestionsResponse.data.suggestions)
        setParticipants(suggestionsResponse.data.participants)

        // Load user info for participants
        const userPromises = suggestionsResponse.data.participants.map(userID =>
          apiClient.get(`/users/${userID}`).catch(() => ({ data: { name: 'Unknown User', userID } }))
        )
        const users = await Promise.all(userPromises)
        setParticipants(users.map(u => u.data))

        // Load polls
        await Promise.all([
          loadActivityPoll(),
          loadLocationPoll(),
          loadCuisinePoll()
        ])
      }
    } catch (err) {
      console.error('Failed to load data:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadActivityPoll = async () => {
    try {
      const response = await apiClient.get('/polls/get/activity', {
        params: { tripID, userID }
      })
      setActivities(response.data.activities)
    } catch (err) {
      console.error('Failed to load activity poll:', err)
    }
  }

  const loadLocationPoll = async () => {
    try {
      const response = await apiClient.get('/polls/get/location', {
        params: { tripID }
      })
      setLocations(response.data.locations)
    } catch (err) {
      console.error('Failed to load location poll:', err)
    }
  }

  const loadCuisinePoll = async () => {
    try {
      const response = await apiClient.get('/polls/get/food_cuisines', {
        params: { tripID, userID }
      })
      setCuisines(response.data.cuisines)
    } catch (err) {
      console.error('Failed to load cuisine poll:', err)
    }
  }

  const handleCuisineVote = async (cuisineName, vote) => {
    try {
      const response = await apiClient.post('/polls/vote/food_cuisine', {
        tripID,
        cuisineName,
        userID,
        vote
      })
      
      const { action, vote: returnedVote } = response.data
      const previousCuisine = cuisines.find(c => c.name === cuisineName)
      const previousVote = previousCuisine?.user_vote
      
      // Update local state based on action
      setCuisines(cuisines.map(cuisine => {
        if (cuisine.name === cuisineName) {
          let newUpvotes = cuisine.upvotes || 0
          let newDownvotes = cuisine.downvotes || 0
          
          if (action === 'removed') {
            // Vote was removed - decrement the previous vote count
            if (previousVote === true) {
              newUpvotes = Math.max(0, newUpvotes - 1)
            } else if (previousVote === false) {
              newDownvotes = Math.max(0, newDownvotes - 1)
            }
            return {
              ...cuisine,
              upvotes: newUpvotes,
              downvotes: newDownvotes,
              user_vote: null
            }
          } else if (action === 'updated') {
            // Vote was changed - decrement old vote, increment new vote
            if (previousVote === true) {
              newUpvotes = Math.max(0, newUpvotes - 1)
            } else if (previousVote === false) {
              newDownvotes = Math.max(0, newDownvotes - 1)
            }
            if (returnedVote === true) {
              newUpvotes += 1
            } else if (returnedVote === false) {
              newDownvotes += 1
            }
            return {
              ...cuisine,
              upvotes: newUpvotes,
              downvotes: newDownvotes,
              user_vote: returnedVote
            }
          } else if (action === 'created') {
            // New vote - increment the appropriate count
            if (returnedVote === true) {
              newUpvotes += 1
            } else if (returnedVote === false) {
              newDownvotes += 1
            }
            return {
              ...cuisine,
              upvotes: newUpvotes,
              downvotes: newDownvotes,
              user_vote: returnedVote
            }
          }
        }
        return cuisine
      }))
    } catch (err) {
      console.error('Failed to vote:', err)
      toast.error('Failed to vote. Please try again.')
    }
  }

  const handleActivityVote = async (activityID, vote) => {
    try {
      await apiClient.post('/polls/vote/activity', {
        tripID,
        activityID,
        userID,
        vote
      })
      
      // Reload activities to get accurate vote counts from database
      // This ensures we always have the correct data
      await loadActivityPoll()
    } catch (err) {
      console.error('Failed to vote:', err)
      toast.error('Failed to vote. Please try again.')
    }
  }

  const handleLocationVote = async (locationID, vote) => {
    try {
      const response = await apiClient.post('/polls/vote/location', {
        tripID,
        locationID,
        userID,
        vote
      })
      
      const { action, vote: returnedVote } = response.data
      const previousLocation = locations.find(loc => loc.location_id === locationID)
      const previousVote = previousLocation?.user_vote
      
      // Update local state based on action
      setLocations(locations.map(loc => {
        if (loc.location_id === locationID) {
          let newUpvotes = loc.upvotes || 0
          let newDownvotes = loc.downvotes || 0
          
          if (action === 'removed') {
            // Vote was removed - decrement the previous vote count
            if (previousVote === true) {
              newUpvotes = Math.max(0, newUpvotes - 1)
            } else if (previousVote === false) {
              newDownvotes = Math.max(0, newDownvotes - 1)
            }
            return {
              ...loc,
              upvotes: newUpvotes,
              downvotes: newDownvotes,
              user_vote: null
            }
          } else if (action === 'updated') {
            // Vote was changed - decrement old vote, increment new vote
            if (previousVote === true) {
              newUpvotes = Math.max(0, newUpvotes - 1)
            } else if (previousVote === false) {
              newDownvotes = Math.max(0, newDownvotes - 1)
            }
            if (returnedVote === true) {
              newUpvotes += 1
            } else if (returnedVote === false) {
              newDownvotes += 1
            }
            return {
              ...loc,
              upvotes: newUpvotes,
              downvotes: newDownvotes,
              user_vote: returnedVote
            }
          } else if (action === 'created') {
            // New vote - increment the appropriate count
            if (returnedVote === true) {
              newUpvotes += 1
            } else if (returnedVote === false) {
              newDownvotes += 1
            }
            return {
              ...loc,
              upvotes: newUpvotes,
              downvotes: newDownvotes,
              user_vote: returnedVote
            }
          }
        }
        return loc
      }))
    } catch (err) {
      console.error('Failed to vote:', err)
      toast.error('Failed to vote. Please try again.')
    }
  }

  const getActivityTypeColor = (type) => {
    const colors = {
      sightseeing: '#9C27B0',
      relaxing: '#4CAF50',
      food: '#FF9800',
      entertainment: '#673AB7',
      watersport: '#00BCD4',
      adventure: '#FF5722'
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

  const calculatePollProgress = () => {
    const totalPolls = 3
    let completed = 0
    if (activities.length > 0) completed++
    if (locations.length > 0) completed++
    if (cuisines.length > 0) completed++
    return { completed, total: totalPolls, percentage: (completed / totalPolls) * 100 }
  }

  if (loading) {
    return (
      <div className="suggestions-loading">
        <div className="spinner"></div>
      </div>
    )
  }

  // Check if all members have finished brainstorming
  if (brainstormStatus && !brainstormStatus.allCompleted) {
    const remaining = brainstormStatus.totalMembers - brainstormStatus.completedMembers
    return (
      <div className="suggestions-page">
        <header className="suggestions-header">
          <div className="header-content">
            <div className="header-left">
              <button 
                className="btn-home"
                onClick={() => navigate('/dashboard')}
                title="Home"
              >
                🏠
              </button>
              <h1>{tripInfo?.title || 'Trip Suggestions'}</h1>
            </div>
            <div className="header-actions">
              <button
                className="btn-secondary"
                onClick={() => navigate(`/trips/${tripID}/brainstorm`)}
              >
                ← Back to Brainstorm
              </button>
            </div>
          </div>
        </header>

        <main className="suggestions-main">
          <div className="brainstorm-waiting">
            <div className="waiting-icon">⏳</div>
            <h2>Waiting for All Members to Finish Brainstorming</h2>
            <p className="waiting-message">
              {brainstormStatus.completedMembers} of {brainstormStatus.totalMembers} members have submitted their suggestions.
            </p>
            <p className="waiting-detail">
              {remaining} member{remaining !== 1 ? 's' : ''} still need{remaining === 1 ? 's' : ''} to complete brainstorming.
            </p>
            <p className="waiting-instruction">
              Once all members have submitted their suggestions, you'll be able to view and vote on them here.
            </p>
            <button
              className="btn-primary"
              onClick={() => navigate(`/trips/${tripID}/brainstorm`)}
            >
              Go to Brainstorm
            </button>
          </div>
        </main>
      </div>
    )
  }

  const progress = calculatePollProgress()

  return (
    <div className="suggestions-page">
      <header className="suggestions-header">
        <div className="header-content">
          <div className="header-left">
            <button 
              className="btn-home"
              onClick={() => navigate('/dashboard')}
              title="Home"
            >
              🏠
            </button>
            <h1>{tripInfo?.title || 'Trip Suggestions'}</h1>
            <p className="participant-count">
              {participants.length} participant{participants.length !== 1 ? 's' : ''}
            </p>
          </div>
          <div className="header-actions">
            <button
              className="btn-secondary"
              onClick={() => navigate(`/trips/${tripID}/brainstorm`)}
            >
              ← Back to Brainstorm
            </button>
            {progress.completed === progress.total && (
              <button
                className="btn-primary"
                onClick={() => navigate(`/trips/${tripID}/overview`)}
              >
                View Final Plan
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="suggestions-main">
        {/* Suggestions Overview */}
        <section className="suggestions-overview">
          <h2>All Suggestions</h2>
          <div className="suggestions-grid">
            {suggestions.map((suggestion, idx) => {
              const participant = participants[idx] || { name: 'Unknown User', userID: 'unknown' }
              const totalDays = suggestion.length
              const totalActivities = suggestion.reduce((sum, day) => sum + (day.activities?.length || 0), 0)
              const uniqueLocations = new Set(suggestion.map(day => day.location)).size

              return (
                <ParticipantSuggestionCard
                  key={idx}
                  participant={participant}
                  suggestion={suggestion}
                  totalDays={totalDays}
                  totalActivities={totalActivities}
                  uniqueLocations={uniqueLocations}
                  getVigorColor={getVigorColor}
                />
              )
            })}
          </div>
        </section>

        {/* Polling Section */}
        <section className="polling-section">
          <div className="poll-progress">
            <h2>Polling Progress</h2>
            <div className="progress-bar-container">
              <div
                className="progress-bar"
                style={{ width: `${progress.percentage}%` }}
              ></div>
            </div>
            <p className="progress-text">
              {progress.completed} of {progress.total} polls completed
            </p>
            {progress.completed === progress.total && (
              <p className="progress-complete">✓ All polls complete!</p>
            )}
          </div>

          <div className="poll-tabs">
            <button
              className={`tab ${activeTab === 'activities' ? 'active' : ''}`}
              onClick={() => setActiveTab('activities')}
            >
              Activities
            </button>
            <button
              className={`tab ${activeTab === 'locations' ? 'active' : ''}`}
              onClick={() => setActiveTab('locations')}
            >
              Locations
            </button>
            <button
              className={`tab ${activeTab === 'cuisines' ? 'active' : ''}`}
              onClick={() => setActiveTab('cuisines')}
            >
              Food Cuisines
            </button>
          </div>

          <div className="poll-content">
            {activeTab === 'activities' && (
              <ActivityPoll
                activities={activities}
                onVote={handleActivityVote}
                getActivityTypeColor={getActivityTypeColor}
                getVigorColor={getVigorColor}
              />
            )}
            {activeTab === 'locations' && (
              <LocationPoll
                locations={locations}
                onVote={handleLocationVote}
              />
            )}
            {activeTab === 'cuisines' && (
              <FoodCuisinePoll
                cuisines={cuisines}
                onVote={handleCuisineVote}
              />
            )}
          </div>
        </section>
      </main>
    </div>
  )
}

function ParticipantSuggestionCard({ participant, suggestion, totalDays, totalActivities, uniqueLocations, getVigorColor }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="participant-suggestion-card">
      <div className="card-header" onClick={() => setExpanded(!expanded)}>
        <div className="participant-info">
          <div className="participant-avatar">
            {participant.name.charAt(0).toUpperCase()}
          </div>
          <div>
            <h3>{participant.name}</h3>
            <p className="participant-id">@{participant.userID}</p>
          </div>
        </div>
        <div className="suggestion-stats">
          <span>{totalDays} days</span>
          <span>{totalActivities} activities</span>
          <span>{uniqueLocations} locations</span>
        </div>
        <button className="expand-btn">{expanded ? '▼' : '▶'}</button>
      </div>
      {expanded && (
        <div className="card-content">
          {suggestion.map((day, idx) => (
            <div key={idx} className="day-preview">
              <h4>Day {day.id} - {day.date}</h4>
              <p className="day-location">📍 {day.location}</p>
              {day.activities && day.activities.length > 0 && (
                <ul className="activities-preview">
                  {day.activities.slice(0, 3).map((activity, actIdx) => (
                    <li key={actIdx}>
                      <span className="activity-name">{activity.activity_name}</span>
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
                    </li>
                  ))}
                  {day.activities.length > 3 && (
                    <li className="more-activities">+{day.activities.length - 3} more</li>
                  )}
                </ul>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// Unified poll component for activities, locations, and cuisines
function UnifiedPoll({ items, onVote, getItemId, getItemName, getItemHeader, getItemDescription, getItemExtra }) {
  return (
    <div className="poll-list">
      {items.map((item) => {
        const itemId = getItemId(item)
        const itemName = getItemName(item)
        const header = getItemHeader(item)
        const description = getItemDescription(item)
        const extra = getItemExtra(item)
        
        return (
          <div key={itemId} className="poll-item">
            <div className="poll-item-header">
              {header}
            </div>
            {description && <p className="poll-item-description">{description}</p>}
            {extra && <p className="poll-item-location">{extra}</p>}
            <div className="poll-item-actions">
              <button
                className={`vote-btn upvote ${item.user_vote === true ? 'active' : ''}`}
                onClick={() => onVote(itemId, true)}
              >
                ↑ {item.upvotes || 0}
              </button>
              <button
                className={`vote-btn downvote ${item.user_vote === false ? 'active' : ''}`}
                onClick={() => onVote(itemId, false)}
              >
                ↓ {item.downvotes || 0}
              </button>
            </div>
          </div>
        )
      })}
    </div>
  )
}

function ActivityPoll({ activities, onVote, getActivityTypeColor, getVigorColor }) {
  return (
    <UnifiedPoll
      items={activities}
      onVote={onVote}
      getItemId={(item) => item.activity_id}
      getItemName={(item) => item.activity_name}
      getItemHeader={(item) => (
        <>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
            <span
              className="activity-type-badge"
              style={{ backgroundColor: getActivityTypeColor(item.type) }}
            >
              {item.type}
            </span>
            {item.vigor && (
              <span 
                className="vigor-badge"
                style={{ 
                  backgroundColor: getVigorColor(item.vigor),
                  color: '#FFFFFF'
                }}
              >
                {item.vigor}
              </span>
            )}
          </div>
          <h3>{item.activity_name}</h3>
        </>
      )}
      getItemDescription={(item) => item.description}
      getItemExtra={(item) => `📍 ${item.location}`}
    />
  )
}

function LocationPoll({ locations, onVote }) {
  return (
    <UnifiedPoll
      items={locations}
      onVote={onVote}
      getItemId={(item) => item.location_id}
      getItemName={(item) => item.name}
      getItemHeader={(item) => (
        <>
          <h3>{item.name}</h3>
          <span className="location-type">{item.type}</span>
        </>
      )}
      getItemDescription={() => null}
      getItemExtra={(item) => `📍 ${item.lat.toFixed(4)}, ${item.lon.toFixed(4)}`}
    />
  )
}

function FoodCuisinePoll({ cuisines, onVote }) {
  return (
    <UnifiedPoll
      items={cuisines}
      onVote={onVote}
      getItemId={(item) => item.name}
      getItemName={(item) => item.name}
      getItemHeader={(item) => <h3>{item.name}</h3>}
      getItemDescription={() => null}
      getItemExtra={() => null}
    />
  )
}

export default Suggestions

