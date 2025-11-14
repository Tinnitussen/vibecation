import { useState, useEffect } from 'react'
import axios from 'axios'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function App() {
  const [trips, setTrips] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchTrips()
  }, [])

  const fetchTrips = async () => {
    try {
      setLoading(true)
      const response = await axios.get(`${API_URL}/api/trips/`)
      setTrips(response.data)
      setError(null)
    } catch (err) {
      setError('Failed to fetch trips. Make sure the backend is running.')
      console.error('Error fetching trips:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>🏖️ Vibecation</h1>
        <p>Your Vacation Planner</p>
      </header>

      <main className="app-main">
        {loading && <div className="loading">Loading trips...</div>}
        
        {error && (
          <div className="error">
            {error}
          </div>
        )}

        {!loading && !error && (
          <div className="trips-container">
            {trips.length === 0 ? (
              <div className="empty-state">
                <p>No trips found. Create your first vacation plan!</p>
              </div>
            ) : (
              <div className="trips-grid">
                {trips.map((trip) => (
                  <div key={trip.trip_id} className="trip-card">
                    <h2>{trip.trip_name}</h2>
                    <p className="trip-id">ID: {trip.trip_id}</p>
                    <p className="trip-activities">
                      {trip.activities?.length || 0} activities
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="api-info">
          <p>API Status: <a href={`${API_URL}/health`} target="_blank" rel="noopener noreferrer">Check Health</a></p>
          <p>API Docs: <a href={`${API_URL}/docs`} target="_blank" rel="noopener noreferrer">Swagger UI</a></p>
        </div>
      </main>
    </div>
  )
}

export default App

