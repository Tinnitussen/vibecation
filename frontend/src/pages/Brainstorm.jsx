import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import apiClient from '../api/client'
import './Brainstorm.css'

function Brainstorm() {
  const { tripID } = useParams()
  const { userID } = useAuth()
  const navigate = useNavigate()
  const [tripInfo, setTripInfo] = useState(null)
  const [days, setDays] = useState([])
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [tripSuggestionID, setTripSuggestionID] = useState(null)
  const [selectedTypes, setSelectedTypes] = useState([])
  const [brainstormStatus, setBrainstormStatus] = useState(null)
  const messagesEndRef = useRef(null)
  const chatInputRef = useRef(null)

  useEffect(() => {
    loadTripInfo()
    checkBrainstormCompletion()
  }, [tripID])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const loadTripInfo = async () => {
    try {
      const response = await apiClient.get('/tripinfo', {
        params: { tripID }
      })
      setTripInfo(response.data)
      // Generate initial tripSuggestionID
      setTripSuggestionID(`suggestion_${Date.now()}`)
    } catch (err) {
      console.error('Failed to load trip info:', err)
    }
  }

  const checkBrainstormCompletion = async () => {
    try {
      const response = await apiClient.get('/check_brainstorm_completion', {
        params: { tripID }
      })
      setBrainstormStatus(response.data)
    } catch (err) {
      console.error('Failed to check brainstorm completion:', err)
      // Default to allowing access for backward compatibility
      setBrainstormStatus({ allCompleted: true })
    }
  }

  const generateTripSuggestionID = () => {
    return `suggestion_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  const handleSendMessage = async () => {
    if (!inputValue.trim() || loading) return

    const userMessage = inputValue.trim()
    setInputValue('')
    setMessages(prev => [...prev, { type: 'user', content: userMessage }])
    setLoading(true)

    // Add loading message
    setMessages(prev => [...prev, { type: 'loading', content: '' }])

    try {
      // Generate tripSuggestionID if not set
      if (!tripSuggestionID) {
        setTripSuggestionID(generateTripSuggestionID())
      }
      
      // Use unified endpoint - send empty JSON for first message, current days for subsequent
      const oldPlan = messages.length === 0 ? '{}' : JSON.stringify(days)
      
      const response = await apiClient.get('/trip_brinstorm', {
        params: {
          tripID,
          userID,
          query: userMessage,
          old_plan: oldPlan,
          tripSuggestionID: tripSuggestionID || generateTripSuggestionID()
        }
      })

      // Remove loading message and add system response
      setMessages(prev => {
        const filtered = prev.filter(m => m.type !== 'loading')
        return [...filtered, { type: 'system', content: response.data.trip_summary }]
      })

      // Update days
      setDays(response.data.days || [])
    } catch (err) {
      console.error('Failed to get trip plan:', err)
      setMessages(prev => {
        const filtered = prev.filter(m => m.type !== 'loading')
        return [...filtered, { type: 'error', content: 'Failed to generate trip plan. Please try again.' }]
      })
    } finally {
      setLoading(false)
    }
  }

  const handleSubmitSuggestion = async () => {
    if (days.length === 0) {
      alert('No activities to submit. Please generate a trip plan first.')
      return
    }

    try {
      await apiClient.post('/post_trip_suggestion', {
        tripSuggestionID: tripSuggestionID || generateTripSuggestionID(),
        tripID,
        userID,
        days
      })
      // Refresh brainstorm completion status and check if we can navigate
      const statusResponse = await apiClient.get('/check_brainstorm_completion', {
        params: { tripID }
      }).catch(() => ({ data: { allCompleted: true } }))
      
      const status = statusResponse.data
      setBrainstormStatus(status)
      
      if (status.allCompleted) {
        alert('Trip suggestion submitted successfully! All members have finished brainstorming.')
        navigate(`/trips/${tripID}/suggestions`)
      } else {
        const remaining = status.totalMembers - status.completedMembers
        alert(`Your suggestion has been submitted! Waiting for ${remaining} more member${remaining !== 1 ? 's' : ''} to finish brainstorming.`)
      }
    } catch (err) {
      console.error('Failed to submit suggestion:', err)
      alert('Failed to submit suggestion. Please try again.')
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
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
      attraction: '#9C27B0',
      travel: '#2196F3',
      accommodation: '#607D8B'
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

  const filteredDays = days.filter(day => {
    if (selectedTypes.length === 0) return true
    return day.activities?.some(activity => selectedTypes.includes(activity.type))
  })

  const allActivityTypes = [...new Set(
    days.flatMap(day => day.activities?.map(act => act.type) || [])
  )]

  return (
    <div className="brainstorm-page">
      <header className="brainstorm-header">
        <div className="header-content">
          <div className="header-left">
            <button
              className="btn-back"
              onClick={() => navigate('/dashboard')}
            >
              ← Dashboard
            </button>
            <h1>{tripInfo?.title || 'Trip Brainstorm'}</h1>
          </div>
          {brainstormStatus?.allCompleted ? (
            <button
              className="btn-suggestions"
              onClick={() => navigate(`/trips/${tripID}/suggestions`)}
            >
              View Suggestions
            </button>
          ) : (
            <button
              className="btn-suggestions"
              disabled={true}
              title={brainstormStatus ? `Waiting for ${brainstormStatus.totalMembers - brainstormStatus.completedMembers} more member(s) to finish brainstorming` : 'Checking status...'}
              style={{ opacity: 0.6, cursor: 'not-allowed' }}
            >
              View Suggestions ({brainstormStatus ? `${brainstormStatus.completedMembers}/${brainstormStatus.totalMembers}` : '...'})
            </button>
          )}
        </div>
      </header>

      <main className="brainstorm-main">
        {/* Left Side - Activity Cards Panel (60%) */}
        <div className="activity-panel">
          {allActivityTypes.length > 0 && (
            <div className="activity-filter">
              <span className="filter-label">Filter by type:</span>
              <div className="filter-buttons">
                {allActivityTypes.map(type => (
                  <button
                    key={type}
                    className={`filter-btn ${selectedTypes.includes(type) ? 'active' : ''}`}
                    onClick={() => {
                      setSelectedTypes(prev =>
                        prev.includes(type)
                          ? prev.filter(t => t !== type)
                          : [...prev, type]
                      )
                    }}
                    style={{
                      borderColor: getActivityTypeColor(type),
                      backgroundColor: selectedTypes.includes(type) ? getActivityTypeColor(type) : 'transparent',
                      color: selectedTypes.includes(type) ? '#FFFFFF' : getActivityTypeColor(type)
                    }}
                  >
                    {type}
                  </button>
                ))}
                {selectedTypes.length > 0 && (
                  <button
                    className="filter-btn clear"
                    onClick={() => setSelectedTypes([])}
                  >
                    Clear
                  </button>
                )}
              </div>
            </div>
          )}

          <div className="activity-cards-container">
            {filteredDays.length === 0 ? (
              <div className="empty-activities">
                <div className="empty-icon">🗺️</div>
                <p>No activities yet. Start chatting to generate your trip plan!</p>
              </div>
            ) : (
              filteredDays.map((day, dayIdx) => (
                <DayGroup
                  key={dayIdx}
                  day={day}
                  getActivityTypeColor={getActivityTypeColor}
                  getVigorColor={getVigorColor}
                />
              ))
            )}
          </div>
        </div>

        {/* Right Side - Chat Interface (40%) */}
        <div className="chat-panel">
          <div className="chat-messages">
            {messages.length === 0 ? (
              <div className="chat-welcome">
                <div className="welcome-icon">💬</div>
                <h2>Start Planning Your Trip</h2>
                <p>Describe your ideal trip and I'll help you create an amazing itinerary!</p>
                <p className="welcome-example">Example: "I want a 3-day trip to Barcelona with sightseeing and relaxing activities"</p>
              </div>
            ) : (
              messages.map((message, idx) => (
                <ChatMessage key={idx} message={message} />
              ))
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="chat-input-container">
            <div className="chat-input-wrapper">
              <textarea
                ref={chatInputRef}
                className="chat-input"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Describe your ideal trip..."
                rows={3}
                disabled={loading}
              />
              <button
                className="btn-send"
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || loading}
              >
                {loading ? '...' : 'Send'}
              </button>
            </div>
            {days.length > 0 && (
              <button
                className="btn-submit-suggestion"
                onClick={handleSubmitSuggestion}
              >
                Submit Suggestion
              </button>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

function DayGroup({ day, getActivityTypeColor, getVigorColor }) {
  return (
    <div className="day-group">
      <div className="day-header">
        <h3>Day {day.id}</h3>
        <span className="day-date">{day.date}</span>
        <span className="day-location">📍 {day.location}</span>
      </div>
      {day.description && <p className="day-description">{day.description}</p>}
      <div className="activities-list">
        {day.activities?.map((activity, actIdx) => (
          <ActivityCard
            key={actIdx}
            activity={activity}
            getActivityTypeColor={getActivityTypeColor}
            getVigorColor={getVigorColor}
          />
        ))}
      </div>
    </div>
  )
}

function ActivityCard({ activity, getActivityTypeColor, getVigorColor }) {
  const [expanded, setExpanded] = useState(false)

  const formatTime = (dateTime) => {
    if (!dateTime) return ''
    const date = new Date(dateTime)
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div
      className="activity-card"
      style={{ borderLeftColor: getActivityTypeColor(activity.type) }}
    >
      <div className="activity-header" onClick={() => setExpanded(!expanded)}>
        <div className="activity-badges">
          <span
            className="activity-type-badge"
            style={{ backgroundColor: getActivityTypeColor(activity.type) }}
          >
            {activity.type}
          </span>
          <span
            className="vigor-badge"
            style={{ backgroundColor: getVigorColor(activity.vigor) }}
          >
            {activity.vigor}
          </span>
        </div>
        <h4>{activity.activity_name}</h4>
        <button className="expand-btn">{expanded ? '▼' : '▶'}</button>
      </div>
      {expanded && (
        <div className="activity-details">
          <p className="activity-description">{activity.description}</p>
          <div className="activity-info">
            <div className="info-item">
              <span className="info-label">Time:</span>
              <span>{formatTime(activity.from_date_time)} - {formatTime(activity.to_date_time)}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Location:</span>
              <span>📍 {activity.location}</span>
            </div>
            {activity.start_lat && activity.start_lon && (
              <div className="info-item">
                <span className="info-label">Coordinates:</span>
                <span>{activity.start_lat.toFixed(4)}, {activity.start_lon.toFixed(4)}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function ChatMessage({ message }) {
  if (message.type === 'loading') {
    return (
      <div className="message message-loading">
        <div className="typing-indicator">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    )
  }

  if (message.type === 'error') {
    return (
      <div className="message message-error">
        <p>{message.content}</p>
      </div>
    )
  }

  return (
    <div className={`message message-${message.type}`}>
      <p>{message.content}</p>
    </div>
  )
}

export default Brainstorm

