import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import apiClient from '../api/client'
import './Suggestions.css'

function Suggestions() {
  const { tripID } = useParams()
  const { userID } = useAuth()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('activities')
  const [loading, setLoading] = useState(true)
  const [suggestions, setSuggestions] = useState([])
  const [participants, setParticipants] = useState([])
  const [activities, setActivities] = useState([])
  const [locations, setLocations] = useState([])
  const [vigorPreferences, setVigorPreferences] = useState([])
  const [cuisines, setCuisines] = useState([])
  const [tripInfo, setTripInfo] = useState(null)

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
        loadVigorPoll(),
        loadCuisinePoll()
      ])
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

  const loadVigorPoll = async () => {
    try {
      const response = await apiClient.get('/polls/get/activity_vigor', {
        params: { tripID }
      })
      setVigorPreferences(response.data.vigor_preferences)
    } catch (err) {
      console.error('Failed to load vigor poll:', err)
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

  const handleCuisineVote = async (selectedCuisines) => {
    try {
      await apiClient.post('/polls/vote/food_cuisine', {
        tripID,
        userID,
        selectedCuisines
      })
      
      // Reload cuisines to get accurate vote counts from database
      await loadCuisinePoll()
      
      alert('Cuisine preferences saved successfully!')
    } catch (err) {
      console.error('Failed to submit cuisine votes:', err)
      alert('Failed to save cuisine preferences. Please try again.')
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
      alert('Failed to vote. Please try again.')
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
      alert('Failed to vote. Please try again.')
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

  const calculatePollProgress = () => {
    const totalPolls = 4
    let completed = 0
    if (activities.length > 0) completed++
    if (locations.length > 0) completed++
    if (vigorPreferences.length > 0) completed++
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
              className={`tab ${activeTab === 'vigor' ? 'active' : ''}`}
              onClick={() => setActiveTab('vigor')}
            >
              Activity Vigor
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
              />
            )}
            {activeTab === 'locations' && (
              <LocationPoll
                locations={locations}
                onVote={handleLocationVote}
              />
            )}
            {activeTab === 'vigor' && (
              <ActivityVigorPoll
                preferences={vigorPreferences}
              />
            )}
            {activeTab === 'cuisines' && (
              <FoodCuisinePoll
                cuisines={cuisines}
                onSubmit={handleCuisineVote}
              />
            )}
          </div>
        </section>
      </main>
    </div>
  )
}

function ParticipantSuggestionCard({ participant, suggestion, totalDays, totalActivities, uniqueLocations }) {
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
                    <li key={actIdx}>{activity.activity_name}</li>
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

function ActivityPoll({ activities, onVote, getActivityTypeColor }) {
  return (
    <div className="poll-list">
      {activities.map((activity) => (
        <div key={activity.activity_id} className="poll-item">
          <div className="poll-item-header">
            <span
              className="activity-type-badge"
              style={{ backgroundColor: getActivityTypeColor(activity.type) }}
            >
              {activity.type}
            </span>
            <h3>{activity.activity_name}</h3>
          </div>
          <p className="poll-item-description">{activity.description}</p>
          <p className="poll-item-location">📍 {activity.location}</p>
          <div className="poll-item-actions">
            <button
              className={`vote-btn upvote ${activity.user_vote === true ? 'active' : ''}`}
              onClick={() => onVote(activity.activity_id, true)}
            >
              ↑ {activity.upvotes}
            </button>
            <button
              className={`vote-btn downvote ${activity.user_vote === false ? 'active' : ''}`}
              onClick={() => onVote(activity.activity_id, false)}
            >
              ↓ {activity.downvotes}
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}

function LocationPoll({ locations, onVote }) {
  return (
    <div className="poll-list">
      {locations.map((location) => (
        <div key={location.location_id} className="poll-item">
          <div className="poll-item-header">
            <h3>{location.name}</h3>
            <span className="location-type">{location.type}</span>
          </div>
          <p className="poll-item-location">
            📍 {location.lat.toFixed(4)}, {location.lon.toFixed(4)}
          </p>
          <div className="poll-item-actions">
            <button
              className={`vote-btn upvote ${location.user_vote === true ? 'active' : ''}`}
              onClick={() => onVote(location.location_id, true)}
            >
              ↑ {location.upvotes}
            </button>
            <button
              className={`vote-btn downvote ${location.user_vote === false ? 'active' : ''}`}
              onClick={() => onVote(location.location_id, false)}
            >
              ↓ {location.downvotes}
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}

function ActivityVigorPoll({ preferences }) {
  return (
    <div className="poll-list">
      {preferences.map((pref) => (
        <div key={pref.activity_id} className="poll-item">
          <h3>{pref.activity_name}</h3>
          <div className="vigor-selector">
            <div className="vigor-options">
              <button className={`vigor-btn low ${pref.user_preference === 'low' ? 'active' : ''}`}>
                Low
              </button>
              <button className={`vigor-btn medium ${pref.user_preference === 'medium' ? 'active' : ''}`}>
                Medium
              </button>
              <button className={`vigor-btn high ${pref.user_preference === 'high' ? 'active' : ''}`}>
                High
              </button>
            </div>
            <div className="vigor-results">
              <div className="vigor-bar">
                <div
                  className="vigor-bar-segment low"
                  style={{ width: `${(pref.preferences.low / 5) * 100}%` }}
                ></div>
                <div
                  className="vigor-bar-segment medium"
                  style={{ width: `${(pref.preferences.medium / 5) * 100}%` }}
                ></div>
                <div
                  className="vigor-bar-segment high"
                  style={{ width: `${(pref.preferences.high / 5) * 100}%` }}
                ></div>
              </div>
              <div className="vigor-stats">
                <span>Low: {pref.preferences.low}</span>
                <span>Medium: {pref.preferences.medium}</span>
                <span>High: {pref.preferences.high}</span>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

function FoodCuisinePoll({ cuisines, onSubmit }) {
  const [selectedCuisines, setSelectedCuisines] = useState([])
  const [submitting, setSubmitting] = useState(false)

  // Initialize selected cuisines from loaded data (user's previous selections)
  useEffect(() => {
    const userSelected = cuisines
      .filter(c => c.selected)
      .map(c => c.name)
    setSelectedCuisines(userSelected)
  }, [cuisines])

  const toggleCuisine = (cuisineName) => {
    setSelectedCuisines(prev =>
      prev.includes(cuisineName)
        ? prev.filter(c => c !== cuisineName)
        : [...prev, cuisineName]
    )
  }

  const handleSubmit = async () => {
    if (!onSubmit) return
    
    setSubmitting(true)
    try {
      await onSubmit(selectedCuisines)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="cuisine-poll-container">
      <div className="poll-list">
        {cuisines.map((cuisine, idx) => (
          <div key={idx} className="poll-item cuisine-item">
            <label className="cuisine-checkbox">
              <input
                type="checkbox"
                checked={selectedCuisines.includes(cuisine.name)}
                onChange={() => toggleCuisine(cuisine.name)}
              />
              <span className="cuisine-name">{cuisine.name}</span>
              <span className="cuisine-votes">{cuisine.votes} votes</span>
            </label>
          </div>
        ))}
      </div>
      <div className="cuisine-submit-section">
        <button
          className="cuisine-submit-btn"
          onClick={handleSubmit}
          disabled={submitting}
        >
          {submitting ? 'Saving...' : 'Submit Cuisine Preferences'}
        </button>
        {selectedCuisines.length > 0 && (
          <p className="cuisine-selection-count">
            {selectedCuisines.length} cuisine{selectedCuisines.length !== 1 ? 's' : ''} selected
          </p>
        )}
      </div>
    </div>
  )
}

export default Suggestions

