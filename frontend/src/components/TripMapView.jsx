import { useEffect, useRef } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Fix for default marker icons in React-Leaflet
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
})

// Component to fit map bounds
function FitBounds({ bounds }) {
  const map = useMap()
  
  useEffect(() => {
    if (bounds && bounds[0] && bounds[1]) {
      try {
        map.fitBounds(bounds, { padding: [50, 50], maxZoom: 12 })
      } catch (e) {
        console.error('Error fitting bounds:', e)
      }
    }
  }, [map, bounds])
  
  return null
}

function TripMapView({ days }) {
  const mapRef = useRef(null)

  // Extract all locations with coordinates from the itinerary
  const locations = []
  const routes = []
  let lastLocation = null

  if (days && days.length > 0) {
    days.forEach((day, dayIndex) => {
      if (day.activities && day.activities.length > 0) {
        day.activities.forEach((activity, actIndex) => {
          if (activity.start_lat && activity.start_lon) {
            const location = {
              id: activity.id || activity.activity_id || `${dayIndex}-${actIndex}`,
              name: activity.activity_name,
              type: activity.type,
              lat: activity.start_lat,
              lon: activity.start_lon,
              day: day.id,
              dayDate: day.date,
              location: activity.location,
              description: activity.description,
              time: activity.from_date_time
            }
            locations.push(location)

            // Create route from previous location (within day or from previous day)
            if (lastLocation) {
              routes.push([
                [lastLocation.lat, lastLocation.lon],
                [activity.start_lat, activity.start_lon]
              ])
            }

            // Update last location to end location if available, otherwise start location
            if (activity.end_lat && activity.end_lon) {
              lastLocation = {
                lat: activity.end_lat,
                lon: activity.end_lon
              }
            } else {
              lastLocation = {
                lat: activity.start_lat,
                lon: activity.start_lon
              }
            }

            // Also add end location marker if different from start
            if (activity.end_lat && activity.end_lon && 
                (activity.end_lat !== activity.start_lat || activity.end_lon !== activity.start_lon)) {
              locations.push({
                id: `${activity.id || activity.activity_id || `${dayIndex}-${actIndex}`}-end`,
                name: `${activity.activity_name} (End)`,
                type: activity.type,
                lat: activity.end_lat,
                lon: activity.end_lon,
                day: day.id,
                dayDate: day.date,
                location: activity.location,
                description: activity.description,
                time: activity.to_date_time
              })
            }
          }
        })
      }
    })
  }

  // Calculate bounds to fit all markers
  const getBounds = () => {
    if (locations.length === 0) {
      return [[37.9, 23.7], [37.9, 23.7]] // Default to Athens area
    }
    
    const lats = locations.map(loc => loc.lat)
    const lons = locations.map(loc => loc.lon)
    
    return [
      [Math.min(...lats), Math.min(...lons)],
      [Math.max(...lats), Math.max(...lons)]
    ]
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

  const createCustomIcon = (type) => {
    const color = getActivityTypeColor(type)
    return L.divIcon({
      className: 'custom-marker',
      html: `<div style="background-color: ${color}; width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>`,
      iconSize: [20, 20],
      iconAnchor: [10, 10]
    })
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

  if (locations.length === 0) {
    return (
      <div className="map-container-empty">
        <p>No location data available for this trip.</p>
      </div>
    )
  }

  const bounds = getBounds()
  const centerLat = (bounds[0][0] + bounds[1][0]) / 2
  const centerLon = (bounds[0][1] + bounds[1][1]) / 2

  return (
    <div className="map-container">
      <MapContainer
        center={[centerLat, centerLon]}
        zoom={8}
        style={{ height: '100%', width: '100%' }}
        ref={mapRef}
      >
        <FitBounds bounds={bounds} />
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {/* Draw routes between activities */}
        {routes.map((route, index) => (
          <Polyline
            key={`route-${index}`}
            positions={route}
            color="#FF00FF"
            weight={3}
            opacity={0.6}
            dashArray="10, 5"
          />
        ))}

        {/* Add markers for each location */}
        {locations.map((location) => (
          <Marker
            key={location.id}
            position={[location.lat, location.lon]}
            icon={createCustomIcon(location.type)}
          >
            <Popup>
              <div className="map-popup">
                <h3>{location.name}</h3>
                <div className="popup-badge" style={{ backgroundColor: getActivityTypeColor(location.type) }}>
                  {location.type}
                </div>
                <p className="popup-day">Day {location.day} - {location.dayDate}</p>
                {location.location && (
                  <p className="popup-location">📍 {location.location}</p>
                )}
                {location.time && (
                  <p className="popup-time">🕐 {formatDateTime(location.time)}</p>
                )}
                {location.description && (
                  <p className="popup-description">{location.description}</p>
                )}
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  )
}

export default TripMapView

