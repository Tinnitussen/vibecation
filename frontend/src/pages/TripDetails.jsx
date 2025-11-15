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
  const [saving, setSaving] = useState(false)
  const [trip, setTrip] = useState(null)
  const [details, setDetails] = useState(null)
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
  const [expandedSections, setExpandedSections] = useState({
    accommodation: true,
    transportation: true,
    documents: true,
    budget: true,
    additional: true
  })

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
      setHasUnsavedChanges(false)
    } catch (err) {
      console.error('Failed to load trip details:', err)
      toast.error('Failed to load trip details')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!details) return
    
    try {
      setSaving(true)
      await apiClient.put(`/trips/${tripID}/details`, details)
      setHasUnsavedChanges(false)
      toast.success('Trip details saved successfully!')
    } catch (err) {
      console.error('Failed to save trip details:', err)
      toast.error('Failed to save trip details')
    } finally {
      setSaving(false)
    }
  }

  const updateDetails = (path, value) => {
    setDetails(prev => {
      const newDetails = JSON.parse(JSON.stringify(prev))
      const keys = path.split('.')
      let current = newDetails
      for (let i = 0; i < keys.length - 1; i++) {
        if (!current[keys[i]]) {
          current[keys[i]] = {}
        }
        current = current[keys[i]]
      }
      current[keys[keys.length - 1]] = value
      setHasUnsavedChanges(true)
      return newDetails
    })
  }

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }))
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
          <div className="save-status">
            {hasUnsavedChanges && <span className="unsaved-indicator">● Unsaved changes</span>}
            {saving && <span className="saving-indicator">Saving...</span>}
            {!hasUnsavedChanges && !saving && <span className="saved-indicator">✓ Saved</span>}
          </div>
        </div>
      </header>

      <main className="details-main">
        <div className="details-navigation">
          <button 
            className={expandedSections.accommodation ? 'active' : ''}
            onClick={() => toggleSection('accommodation')}
          >
            🏨 Accommodation
          </button>
          <button 
            className={expandedSections.transportation ? 'active' : ''}
            onClick={() => toggleSection('transportation')}
          >
            ✈️ Transportation
          </button>
          <button 
            className={expandedSections.documents ? 'active' : ''}
            onClick={() => toggleSection('documents')}
          >
            📄 Travel Documents
          </button>
          <button 
            className={expandedSections.budget ? 'active' : ''}
            onClick={() => toggleSection('budget')}
          >
            💰 Budget
          </button>
          <button 
            className={expandedSections.additional ? 'active' : ''}
            onClick={() => toggleSection('additional')}
          >
            📋 Additional Details
          </button>
        </div>

        <div className="details-content">
          {/* Accommodation Section */}
          {expandedSections.accommodation && (
            <AccommodationSection 
              accommodations={details.accommodations || []}
              onUpdate={(accommodations) => updateDetails('accommodations', accommodations)}
            />
          )}

          {/* Transportation Section */}
          {expandedSections.transportation && (
            <TransportationSection 
              transportation={details.transportation}
              onUpdate={(transportation) => updateDetails('transportation', transportation)}
            />
          )}

          {/* Travel Documents Section */}
          {expandedSections.documents && (
            <TravelDocumentsSection 
              documents={details.documents}
              onUpdate={(documents) => updateDetails('documents', documents)}
            />
          )}

          {/* Budget Section */}
          {expandedSections.budget && (
            <BudgetSection 
              budget={details.budget}
              onUpdate={(budget) => updateDetails('budget', budget)}
            />
          )}

          {/* Additional Details Section */}
          {expandedSections.additional && (
            <AdditionalDetailsSection 
              additional={details.additional}
              onUpdate={(additional) => updateDetails('additional', additional)}
            />
          )}
        </div>
      </main>

      <div className="save-button-container">
        <button 
          className="save-button"
          onClick={handleSave}
          disabled={!hasUnsavedChanges || saving}
        >
          {saving ? 'Saving...' : 'Save All Changes'}
        </button>
      </div>
    </div>
  )
}

// Accommodation Section Component
function AccommodationSection({ accommodations, onUpdate }) {
  const addAccommodation = () => {
    const newAccommodation = {
      id: `acc_${Date.now()}`,
      name: '',
      type: 'hotel',
      checkIn: '',
      checkOut: '',
      address: '',
      city: '',
      country: '',
      phone: '',
      bookingReference: '',
      confirmationNumber: '',
      notes: ''
    }
    onUpdate([...accommodations, newAccommodation])
  }

  const updateAccommodation = (index, field, value) => {
    const updated = [...accommodations]
    updated[index] = { ...updated[index], [field]: value }
    onUpdate(updated)
  }

  const removeAccommodation = (index) => {
    onUpdate(accommodations.filter((_, i) => i !== index))
  }

  return (
    <section className="details-section">
      <h2>🏨 Accommodation</h2>
      {accommodations.map((acc, index) => (
        <div key={acc.id || index} className="accommodation-card">
          <div className="card-header">
            <h3>Accommodation {index + 1}</h3>
            {accommodations.length > 1 && (
              <button 
                className="btn-remove"
                onClick={() => removeAccommodation(index)}
              >
                Remove
              </button>
            )}
          </div>
          <div className="form-grid">
            <div className="form-group">
              <label>Name *</label>
              <input
                type="text"
                value={acc.name || ''}
                onChange={(e) => updateAccommodation(index, 'name', e.target.value)}
                placeholder="Hotel name"
                required
              />
            </div>
            <div className="form-group">
              <label>Type *</label>
              <select
                value={acc.type || 'hotel'}
                onChange={(e) => updateAccommodation(index, 'type', e.target.value)}
              >
                <option value="hotel">Hotel</option>
                <option value="apartment">Apartment</option>
                <option value="hostel">Hostel</option>
                <option value="resort">Resort</option>
                <option value="villa">Villa</option>
                <option value="Airbnb">Airbnb</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div className="form-group">
              <label>Check-in Date</label>
              <input
                type="date"
                value={acc.checkIn || ''}
                onChange={(e) => updateAccommodation(index, 'checkIn', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Check-out Date</label>
              <input
                type="date"
                value={acc.checkOut || ''}
                onChange={(e) => updateAccommodation(index, 'checkOut', e.target.value)}
                min={acc.checkIn || ''}
              />
            </div>
            <div className="form-group full-width">
              <label>Address</label>
              <input
                type="text"
                value={acc.address || ''}
                onChange={(e) => updateAccommodation(index, 'address', e.target.value)}
                placeholder="Street address"
              />
            </div>
            <div className="form-group">
              <label>City</label>
              <input
                type="text"
                value={acc.city || ''}
                onChange={(e) => updateAccommodation(index, 'city', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Country</label>
              <input
                type="text"
                value={acc.country || ''}
                onChange={(e) => updateAccommodation(index, 'country', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Phone</label>
              <input
                type="tel"
                value={acc.phone || ''}
                onChange={(e) => updateAccommodation(index, 'phone', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Booking Reference</label>
              <input
                type="text"
                value={acc.bookingReference || ''}
                onChange={(e) => updateAccommodation(index, 'bookingReference', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Confirmation Number</label>
              <input
                type="text"
                value={acc.confirmationNumber || ''}
                onChange={(e) => updateAccommodation(index, 'confirmationNumber', e.target.value)}
              />
            </div>
            <div className="form-group full-width">
              <label>Notes</label>
              <textarea
                value={acc.notes || ''}
                onChange={(e) => updateAccommodation(index, 'notes', e.target.value)}
                rows="3"
                placeholder="Additional notes..."
              />
            </div>
          </div>
        </div>
      ))}
      <button className="btn-add" onClick={addAccommodation}>
        + Add Accommodation
      </button>
    </section>
  )
}

// Transportation Section Component
function TransportationSection({ transportation, onUpdate }) {
  const transport = transportation || {
    flights: [],
    rentalCar: { hasRentalCar: false },
    publicTransport: { passes: [], details: '' },
    other: ''
  }

  const updateField = (path, value) => {
    const newTransport = JSON.parse(JSON.stringify(transport))
    const keys = path.split('.')
    let current = newTransport
    for (let i = 0; i < keys.length - 1; i++) {
      if (!current[keys[i]]) {
        current[keys[i]] = {}
      }
      current = current[keys[i]]
    }
    current[keys[keys.length - 1]] = value
    onUpdate(newTransport)
  }

  const addFlight = () => {
    const newFlight = {
      id: `flight_${Date.now()}`,
      type: 'outbound',
      departureAirport: '',
      arrivalAirport: '',
      departureDateTime: '',
      arrivalDateTime: '',
      airline: '',
      flightNumber: '',
      bookingReference: '',
      confirmationNumber: '',
      seatAssignments: '',
      notes: ''
    }
    updateField('flights', [...transport.flights, newFlight])
  }

  const updateFlight = (index, field, value) => {
    const updated = [...transport.flights]
    updated[index] = { ...updated[index], [field]: value }
    updateField('flights', updated)
  }

  const removeFlight = (index) => {
    updateField('flights', transport.flights.filter((_, i) => i !== index))
  }

  return (
    <section className="details-section">
      <h2>✈️ Transportation</h2>
      
      {/* Flights */}
      <div className="subsection">
        <h3>Flights</h3>
        {transport.flights.map((flight, index) => (
          <div key={flight.id || index} className="flight-card">
            <div className="card-header">
              <h4>Flight {index + 1} - {flight.type || 'outbound'}</h4>
              <button className="btn-remove" onClick={() => removeFlight(index)}>
                Remove
              </button>
            </div>
            <div className="form-grid">
              <div className="form-group">
                <label>Type</label>
                <select
                  value={flight.type || 'outbound'}
                  onChange={(e) => updateFlight(index, 'type', e.target.value)}
                >
                  <option value="outbound">Outbound</option>
                  <option value="return">Return</option>
                  <option value="connecting">Connecting</option>
                </select>
              </div>
              <div className="form-group">
                <label>Departure Airport</label>
                <input
                  type="text"
                  value={flight.departureAirport || ''}
                  onChange={(e) => updateFlight(index, 'departureAirport', e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>Arrival Airport</label>
                <input
                  type="text"
                  value={flight.arrivalAirport || ''}
                  onChange={(e) => updateFlight(index, 'arrivalAirport', e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>Departure Date & Time</label>
                <input
                  type="datetime-local"
                  value={flight.departureDateTime ? flight.departureDateTime.slice(0, 16) : ''}
                  onChange={(e) => updateFlight(index, 'departureDateTime', e.target.value + ':00Z')}
                />
              </div>
              <div className="form-group">
                <label>Arrival Date & Time</label>
                <input
                  type="datetime-local"
                  value={flight.arrivalDateTime ? flight.arrivalDateTime.slice(0, 16) : ''}
                  onChange={(e) => updateFlight(index, 'arrivalDateTime', e.target.value + ':00Z')}
                />
              </div>
              <div className="form-group">
                <label>Airline</label>
                <input
                  type="text"
                  value={flight.airline || ''}
                  onChange={(e) => updateFlight(index, 'airline', e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>Flight Number</label>
                <input
                  type="text"
                  value={flight.flightNumber || ''}
                  onChange={(e) => updateFlight(index, 'flightNumber', e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>Booking Reference</label>
                <input
                  type="text"
                  value={flight.bookingReference || ''}
                  onChange={(e) => updateFlight(index, 'bookingReference', e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>Confirmation Number</label>
                <input
                  type="text"
                  value={flight.confirmationNumber || ''}
                  onChange={(e) => updateFlight(index, 'confirmationNumber', e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>Seat Assignments</label>
                <input
                  type="text"
                  value={flight.seatAssignments || ''}
                  onChange={(e) => updateFlight(index, 'seatAssignments', e.target.value)}
                />
              </div>
              <div className="form-group full-width">
                <label>Notes</label>
                <textarea
                  value={flight.notes || ''}
                  onChange={(e) => updateFlight(index, 'notes', e.target.value)}
                  rows="2"
                />
              </div>
            </div>
          </div>
        ))}
        <button className="btn-add" onClick={addFlight}>
          + Add Flight
        </button>
      </div>

      {/* Rental Car */}
      <div className="subsection">
        <h3>Rental Car</h3>
        <div className="form-group">
          <label>
            <input
              type="checkbox"
              checked={transport.rentalCar?.hasRentalCar || false}
              onChange={(e) => updateField('rentalCar.hasRentalCar', e.target.checked)}
            />
            Has Rental Car
          </label>
        </div>
        {transport.rentalCar?.hasRentalCar && (
          <div className="form-grid">
            <div className="form-group">
              <label>Company</label>
              <input
                type="text"
                value={transport.rentalCar.company || ''}
                onChange={(e) => updateField('rentalCar.company', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Pickup Location</label>
              <input
                type="text"
                value={transport.rentalCar.pickupLocation || ''}
                onChange={(e) => updateField('rentalCar.pickupLocation', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Pickup Date & Time</label>
              <input
                type="datetime-local"
                value={transport.rentalCar.pickupDateTime ? transport.rentalCar.pickupDateTime.slice(0, 16) : ''}
                onChange={(e) => updateField('rentalCar.pickupDateTime', e.target.value + ':00Z')}
              />
            </div>
            <div className="form-group">
              <label>Drop-off Location</label>
              <input
                type="text"
                value={transport.rentalCar.dropoffLocation || ''}
                onChange={(e) => updateField('rentalCar.dropoffLocation', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Drop-off Date & Time</label>
              <input
                type="datetime-local"
                value={transport.rentalCar.dropoffDateTime ? transport.rentalCar.dropoffDateTime.slice(0, 16) : ''}
                onChange={(e) => updateField('rentalCar.dropoffDateTime', e.target.value + ':00Z')}
              />
            </div>
            <div className="form-group">
              <label>Car Type</label>
              <select
                value={transport.rentalCar.carType || 'economy'}
                onChange={(e) => updateField('rentalCar.carType', e.target.value)}
              >
                <option value="economy">Economy</option>
                <option value="compact">Compact</option>
                <option value="midsize">Midsize</option>
                <option value="SUV">SUV</option>
                <option value="luxury">Luxury</option>
              </select>
            </div>
            <div className="form-group">
              <label>Booking Reference</label>
              <input
                type="text"
                value={transport.rentalCar.bookingReference || ''}
                onChange={(e) => updateField('rentalCar.bookingReference', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Confirmation Number</label>
              <input
                type="text"
                value={transport.rentalCar.confirmationNumber || ''}
                onChange={(e) => updateField('rentalCar.confirmationNumber', e.target.value)}
              />
            </div>
          </div>
        )}
      </div>

      {/* Public Transport */}
      <div className="subsection">
        <h3>Public Transport</h3>
        <div className="form-group">
          <label>Passes</label>
          <div className="checkbox-group">
            {['metro', 'bus', 'train', 'ferry'].map(passType => (
              <label key={passType}>
                <input
                  type="checkbox"
                  checked={(transport.publicTransport?.passes || []).includes(passType)}
                  onChange={(e) => {
                    const passes = transport.publicTransport?.passes || []
                    const newPasses = e.target.checked
                      ? [...passes, passType]
                      : passes.filter(p => p !== passType)
                    updateField('publicTransport.passes', newPasses)
                  }}
                />
                {passType.charAt(0).toUpperCase() + passType.slice(1)}
              </label>
            ))}
          </div>
        </div>
        <div className="form-group">
          <label>Details</label>
          <textarea
            value={transport.publicTransport?.details || ''}
            onChange={(e) => updateField('publicTransport.details', e.target.value)}
            rows="3"
          />
        </div>
      </div>

      {/* Other Transportation */}
      <div className="subsection">
        <h3>Other Transportation</h3>
        <div className="form-group">
          <textarea
            value={transport.other || ''}
            onChange={(e) => updateField('other', e.target.value)}
            rows="3"
            placeholder="Other transportation notes..."
          />
        </div>
      </div>
    </section>
  )
}

// Travel Documents Section Component
function TravelDocumentsSection({ documents, onUpdate }) {
  const docs = documents || {
    passport: { required: false },
    visa: { required: false },
    travelInsurance: { hasInsurance: false },
    emergencyContacts: []
  }

  const updateField = (path, value) => {
    const newDocs = JSON.parse(JSON.stringify(docs))
    const keys = path.split('.')
    let current = newDocs
    for (let i = 0; i < keys.length - 1; i++) {
      if (!current[keys[i]]) {
        current[keys[i]] = {}
      }
      current = current[keys[i]]
    }
    current[keys[keys.length - 1]] = value
    onUpdate(newDocs)
  }

  const addEmergencyContact = () => {
    const contacts = docs.emergencyContacts || []
    const newContact = {
      id: `contact_${Date.now()}`,
      name: '',
      relationship: '',
      phone: '',
      email: '',
      notes: ''
    }
    updateField('emergencyContacts', [...contacts, newContact])
  }

  const updateEmergencyContact = (index, field, value) => {
    const contacts = [...(docs.emergencyContacts || [])]
    contacts[index] = { ...contacts[index], [field]: value }
    updateField('emergencyContacts', contacts)
  }

  const removeEmergencyContact = (index) => {
    const contacts = docs.emergencyContacts || []
    updateField('emergencyContacts', contacts.filter((_, i) => i !== index))
  }

  return (
    <section className="details-section">
      <h2>📄 Travel Documents</h2>
      
      {/* Passport */}
      <div className="subsection">
        <h3>Passport Requirements</h3>
        <div className="form-group">
          <label>
            <input
              type="checkbox"
              checked={docs.passport?.required || false}
              onChange={(e) => updateField('passport.required', e.target.checked)}
            />
            Valid passport required
          </label>
        </div>
        {docs.passport?.required && (
          <div className="form-grid">
            <div className="form-group">
              <label>Expiration Date</label>
              <input
                type="date"
                value={docs.passport.expirationDate || ''}
                onChange={(e) => updateField('passport.expirationDate', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Minimum Validity (months)</label>
              <input
                type="number"
                value={docs.passport.minimumValidityMonths || ''}
                onChange={(e) => updateField('passport.minimumValidityMonths', parseInt(e.target.value) || 0)}
              />
            </div>
            <div className="form-group full-width">
              <label>Notes</label>
              <textarea
                value={docs.passport.notes || ''}
                onChange={(e) => updateField('passport.notes', e.target.value)}
                rows="2"
              />
            </div>
          </div>
        )}
      </div>

      {/* Visa */}
      <div className="subsection">
        <h3>Visa Requirements</h3>
        <div className="form-group">
          <label>
            <input
              type="checkbox"
              checked={docs.visa?.required || false}
              onChange={(e) => updateField('visa.required', e.target.checked)}
            />
            Visa required
          </label>
        </div>
        {docs.visa?.required && (
          <div className="form-grid">
            <div className="form-group">
              <label>Visa Type</label>
              <select
                value={docs.visa.type || 'tourist'}
                onChange={(e) => updateField('visa.type', e.target.value)}
              >
                <option value="tourist">Tourist</option>
                <option value="business">Business</option>
                <option value="transit">Transit</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div className="form-group">
              <label>Application Date</label>
              <input
                type="date"
                value={docs.visa.applicationDate || ''}
                onChange={(e) => updateField('visa.applicationDate', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Approval Date</label>
              <input
                type="date"
                value={docs.visa.approvalDate || ''}
                onChange={(e) => updateField('visa.approvalDate', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Visa Number</label>
              <input
                type="text"
                value={docs.visa.visaNumber || ''}
                onChange={(e) => updateField('visa.visaNumber', e.target.value)}
              />
            </div>
            <div className="form-group full-width">
              <label>Notes</label>
              <textarea
                value={docs.visa.notes || ''}
                onChange={(e) => updateField('visa.notes', e.target.value)}
                rows="2"
              />
            </div>
          </div>
        )}
      </div>

      {/* Travel Insurance */}
      <div className="subsection">
        <h3>Travel Insurance</h3>
        <div className="form-group">
          <label>
            <input
              type="checkbox"
              checked={docs.travelInsurance?.hasInsurance || false}
              onChange={(e) => updateField('travelInsurance.hasInsurance', e.target.checked)}
            />
            Has travel insurance
          </label>
        </div>
        {docs.travelInsurance?.hasInsurance && (
          <div className="form-grid">
            <div className="form-group">
              <label>Provider</label>
              <input
                type="text"
                value={docs.travelInsurance.provider || ''}
                onChange={(e) => updateField('travelInsurance.provider', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Policy Number</label>
              <input
                type="text"
                value={docs.travelInsurance.policyNumber || ''}
                onChange={(e) => updateField('travelInsurance.policyNumber', e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Coverage Amount</label>
              <input
                type="number"
                value={docs.travelInsurance.coverageAmount || ''}
                onChange={(e) => updateField('travelInsurance.coverageAmount', parseFloat(e.target.value) || 0)}
              />
            </div>
            <div className="form-group">
              <label>Currency</label>
              <input
                type="text"
                value={docs.travelInsurance.currency || ''}
                onChange={(e) => updateField('travelInsurance.currency', e.target.value)}
                placeholder="USD"
              />
            </div>
            <div className="form-group">
              <label>Emergency Contact</label>
              <input
                type="tel"
                value={docs.travelInsurance.emergencyContact || ''}
                onChange={(e) => updateField('travelInsurance.emergencyContact', e.target.value)}
              />
            </div>
            <div className="form-group full-width">
              <label>Notes</label>
              <textarea
                value={docs.travelInsurance.notes || ''}
                onChange={(e) => updateField('travelInsurance.notes', e.target.value)}
                rows="2"
              />
            </div>
          </div>
        )}
      </div>

      {/* Emergency Contacts */}
      <div className="subsection">
        <h3>Emergency Contacts</h3>
        {(docs.emergencyContacts || []).map((contact, index) => (
          <div key={contact.id || index} className="contact-card">
            <div className="card-header">
              <h4>Contact {index + 1}</h4>
              <button className="btn-remove" onClick={() => removeEmergencyContact(index)}>
                Remove
              </button>
            </div>
            <div className="form-grid">
              <div className="form-group">
                <label>Name *</label>
                <input
                  type="text"
                  value={contact.name || ''}
                  onChange={(e) => updateEmergencyContact(index, 'name', e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label>Relationship</label>
                <input
                  type="text"
                  value={contact.relationship || ''}
                  onChange={(e) => updateEmergencyContact(index, 'relationship', e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>Phone *</label>
                <input
                  type="tel"
                  value={contact.phone || ''}
                  onChange={(e) => updateEmergencyContact(index, 'phone', e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={contact.email || ''}
                  onChange={(e) => updateEmergencyContact(index, 'email', e.target.value)}
                />
              </div>
              <div className="form-group full-width">
                <label>Notes</label>
                <textarea
                  value={contact.notes || ''}
                  onChange={(e) => updateEmergencyContact(index, 'notes', e.target.value)}
                  rows="2"
                />
              </div>
            </div>
          </div>
        ))}
        <button className="btn-add" onClick={addEmergencyContact}>
          + Add Emergency Contact
        </button>
      </div>
    </section>
  )
}

// Budget Section Component
function BudgetSection({ budget, onUpdate }) {
  const budgetData = budget || {
    total: 0,
    currency: 'USD',
    breakdown: {
      accommodation: 0,
      food: 0,
      activities: 0,
      transportation: 0,
      shopping: 0,
      miscellaneous: 0
    },
    expenses: []
  }

  const updateField = (path, value) => {
    const newBudget = JSON.parse(JSON.stringify(budgetData))
    const keys = path.split('.')
    let current = newBudget
    for (let i = 0; i < keys.length - 1; i++) {
      if (!current[keys[i]]) {
        current[keys[i]] = {}
      }
      current = current[keys[i]]
    }
    current[keys[keys.length - 1]] = value
    onUpdate(newBudget)
  }

  const addExpense = () => {
    const expenses = budgetData.expenses || []
    const newExpense = {
      id: `exp_${Date.now()}`,
      date: new Date().toISOString().split('T')[0],
      category: 'food',
      description: '',
      amount: 0
    }
    updateField('expenses', [...expenses, newExpense])
  }

  const updateExpense = (index, field, value) => {
    const expenses = [...(budgetData.expenses || [])]
    expenses[index] = { ...expenses[index], [field]: value }
    updateField('expenses', expenses)
  }

  const removeExpense = (index) => {
    const expenses = budgetData.expenses || []
    updateField('expenses', expenses.filter((_, i) => i !== index))
  }

  const totalAllocated = Object.values(budgetData.breakdown || {}).reduce((sum, val) => sum + (val || 0), 0)
  const totalExpenses = (budgetData.expenses || []).reduce((sum, exp) => sum + (exp.amount || 0), 0)
  const remaining = (budgetData.total || 0) - totalAllocated

  return (
    <section className="details-section">
      <h2>💰 Budget</h2>
      
      {/* Total Budget */}
      <div className="subsection">
        <h3>Total Budget</h3>
        <div className="form-grid">
          <div className="form-group">
            <label>Total Amount</label>
            <input
              type="number"
              value={budgetData.total || ''}
              onChange={(e) => updateField('total', parseFloat(e.target.value) || 0)}
              step="0.01"
            />
          </div>
          <div className="form-group">
            <label>Currency</label>
            <input
              type="text"
              value={budgetData.currency || 'USD'}
              onChange={(e) => updateField('currency', e.target.value)}
              placeholder="USD"
            />
          </div>
          <div className="form-group">
            <label>Total Allocated</label>
            <input
              type="text"
              value={`${budgetData.currency || 'USD'} ${totalAllocated.toFixed(2)}`}
              readOnly
              className="readonly"
            />
          </div>
          <div className="form-group">
            <label>Remaining</label>
            <input
              type="text"
              value={`${budgetData.currency || 'USD'} ${remaining.toFixed(2)}`}
              readOnly
              className={remaining < 0 ? 'readonly negative' : 'readonly'}
            />
          </div>
        </div>
      </div>

      {/* Budget Breakdown */}
      <div className="subsection">
        <h3>Budget Breakdown</h3>
        <div className="form-grid">
          <div className="form-group">
            <label>Accommodation</label>
            <input
              type="number"
              value={budgetData.breakdown?.accommodation || ''}
              onChange={(e) => updateField('breakdown.accommodation', parseFloat(e.target.value) || 0)}
              step="0.01"
            />
          </div>
          <div className="form-group">
            <label>Food & Dining</label>
            <input
              type="number"
              value={budgetData.breakdown?.food || ''}
              onChange={(e) => updateField('breakdown.food', parseFloat(e.target.value) || 0)}
              step="0.01"
            />
          </div>
          <div className="form-group">
            <label>Activities & Entertainment</label>
            <input
              type="number"
              value={budgetData.breakdown?.activities || ''}
              onChange={(e) => updateField('breakdown.activities', parseFloat(e.target.value) || 0)}
              step="0.01"
            />
          </div>
          <div className="form-group">
            <label>Transportation</label>
            <input
              type="number"
              value={budgetData.breakdown?.transportation || ''}
              onChange={(e) => updateField('breakdown.transportation', parseFloat(e.target.value) || 0)}
              step="0.01"
            />
          </div>
          <div className="form-group">
            <label>Shopping</label>
            <input
              type="number"
              value={budgetData.breakdown?.shopping || ''}
              onChange={(e) => updateField('breakdown.shopping', parseFloat(e.target.value) || 0)}
              step="0.01"
            />
          </div>
          <div className="form-group">
            <label>Miscellaneous</label>
            <input
              type="number"
              value={budgetData.breakdown?.miscellaneous || ''}
              onChange={(e) => updateField('breakdown.miscellaneous', parseFloat(e.target.value) || 0)}
              step="0.01"
            />
          </div>
        </div>
      </div>

      {/* Expenses */}
      <div className="subsection">
        <h3>Expense Tracker</h3>
        <div className="expenses-table">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Category</th>
                <th>Description</th>
                <th>Amount</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {(budgetData.expenses || []).map((expense, index) => (
                <tr key={expense.id || index}>
                  <td>
                    <input
                      type="date"
                      value={expense.date || ''}
                      onChange={(e) => updateExpense(index, 'date', e.target.value)}
                    />
                  </td>
                  <td>
                    <select
                      value={expense.category || 'food'}
                      onChange={(e) => updateExpense(index, 'category', e.target.value)}
                    >
                      <option value="accommodation">Accommodation</option>
                      <option value="food">Food</option>
                      <option value="activities">Activities</option>
                      <option value="transportation">Transportation</option>
                      <option value="shopping">Shopping</option>
                      <option value="miscellaneous">Miscellaneous</option>
                    </select>
                  </td>
                  <td>
                    <input
                      type="text"
                      value={expense.description || ''}
                      onChange={(e) => updateExpense(index, 'description', e.target.value)}
                    />
                  </td>
                  <td>
                    <input
                      type="number"
                      value={expense.amount || ''}
                      onChange={(e) => updateExpense(index, 'amount', parseFloat(e.target.value) || 0)}
                      step="0.01"
                    />
                  </td>
                  <td>
                    <button className="btn-remove-small" onClick={() => removeExpense(index)}>
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <td colSpan="3"><strong>Total Expenses</strong></td>
                <td><strong>{budgetData.currency || 'USD'} {totalExpenses.toFixed(2)}</strong></td>
                <td></td>
              </tr>
            </tfoot>
          </table>
        </div>
        <button className="btn-add" onClick={addExpense}>
          + Add Expense
        </button>
      </div>
    </section>
  )
}

// Additional Details Section Component
function AdditionalDetailsSection({ additional, onUpdate }) {
  const additionalData = additional || {
    packingList: [],
    importantNotes: [],
    weather: null,
    timeZone: null
  }

  const updateField = (path, value) => {
    const newAdditional = JSON.parse(JSON.stringify(additionalData))
    const keys = path.split('.')
    let current = newAdditional
    for (let i = 0; i < keys.length - 1; i++) {
      if (!current[keys[i]]) {
        current[keys[i]] = {}
      }
      current = current[keys[i]]
    }
    current[keys[keys.length - 1]] = value
    onUpdate(newAdditional)
  }

  const addPackingItem = () => {
    const items = additionalData.packingList || []
    const newItem = {
      id: `item_${Date.now()}`,
      item: '',
      packed: false
    }
    updateField('packingList', [...items, newItem])
  }

  const updatePackingItem = (index, field, value) => {
    const items = [...(additionalData.packingList || [])]
    items[index] = { ...items[index], [field]: value }
    updateField('packingList', items)
  }

  const removePackingItem = (index) => {
    const items = additionalData.packingList || []
    updateField('packingList', items.filter((_, i) => i !== index))
  }

  const addImportantNote = () => {
    const notes = additionalData.importantNotes || []
    const newNote = {
      id: `note_${Date.now()}`,
      content: '',
      createdAt: new Date().toISOString()
    }
    updateField('importantNotes', [...notes, newNote])
  }

  const updateImportantNote = (index, field, value) => {
    const notes = [...(additionalData.importantNotes || [])]
    notes[index] = { ...notes[index], [field]: value }
    updateField('importantNotes', notes)
  }

  const removeImportantNote = (index) => {
    const notes = additionalData.importantNotes || []
    updateField('importantNotes', notes.filter((_, i) => i !== index))
  }

  return (
    <section className="details-section">
      <h2>📋 Additional Details</h2>
      
      {/* Packing List */}
      <div className="subsection">
        <h3>Packing List</h3>
        <div className="packing-list">
          {(additionalData.packingList || []).map((item, index) => (
            <div key={item.id || index} className="packing-item">
              <input
                type="checkbox"
                checked={item.packed || false}
                onChange={(e) => updatePackingItem(index, 'packed', e.target.checked)}
              />
              <input
                type="text"
                value={item.item || ''}
                onChange={(e) => updatePackingItem(index, 'item', e.target.value)}
                placeholder="Item name"
                className="packing-item-input"
              />
              <button className="btn-remove-small" onClick={() => removePackingItem(index)}>
                Remove
              </button>
            </div>
          ))}
        </div>
        <button className="btn-add" onClick={addPackingItem}>
          + Add Item
        </button>
      </div>

      {/* Important Notes */}
      <div className="subsection">
        <h3>Important Notes</h3>
        {(additionalData.importantNotes || []).map((note, index) => (
          <div key={note.id || index} className="note-card">
            <div className="card-header">
              <span className="note-date">
                {note.createdAt ? new Date(note.createdAt).toLocaleDateString() : 'New note'}
              </span>
              <button className="btn-remove" onClick={() => removeImportantNote(index)}>
                Remove
              </button>
            </div>
            <textarea
              value={note.content || ''}
              onChange={(e) => updateImportantNote(index, 'content', e.target.value)}
              rows="3"
              placeholder="Enter important note..."
            />
          </div>
        ))}
        <button className="btn-add" onClick={addImportantNote}>
          + Add Note
        </button>
      </div>

      {/* Weather Info (Read-only) */}
      {additionalData.weather && (
        <div className="subsection">
          <h3>Weather Information</h3>
          {additionalData.weather.current && (
            <div className="weather-info">
              <p><strong>Current:</strong> {additionalData.weather.current.temperature}°C, {additionalData.weather.current.condition}</p>
            </div>
          )}
          {additionalData.weather.forecast && additionalData.weather.forecast.length > 0 && (
            <div className="weather-forecast">
              <h4>Forecast</h4>
              {additionalData.weather.forecast.map((forecast, index) => (
                <div key={index} className="forecast-item">
                  <span>{forecast.date}</span>
                  <span>{forecast.high}°C / {forecast.low}°C</span>
                  <span>{forecast.condition}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Time Zone Info (Read-only) */}
      {additionalData.timeZone && (
        <div className="subsection">
          <h3>Time Zone Information</h3>
          <div className="timezone-info">
            <p><strong>Destination:</strong> {additionalData.timeZone.destination}</p>
            <p><strong>Offset:</strong> {additionalData.timeZone.offset}</p>
            <p><strong>Difference from Home:</strong> {additionalData.timeZone.differenceFromHome}</p>
          </div>
        </div>
      )}
    </section>
  )
}

export default TripDetails

