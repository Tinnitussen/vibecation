"""
FastAPI backend for Vibecation travel planner application.
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from pydantic import field_validator
from typing import List, Optional
from datetime import datetime
import bcrypt
import json
from motor.motor_asyncio import AsyncIOMotorClient
import os
import secrets
import string
from contextlib import asynccontextmanager
from brainstormchat import brainstorm_chat, create_final_plan

# Database connection
client: Optional[AsyncIOMotorClient] = None
db = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for database connection."""
    global client, db
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://mongodb:27017")
    client = AsyncIOMotorClient(mongodb_url)
    db = client.vibecation
    yield
    if client:
        client.close()

app = FastAPI(
    title="Vibecation API",
    description="API for planning and managing travel itineraries",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v

class UserResponse(BaseModel):
    userID: str
    username: str
    email: str
    name: str

class LoginResponse(BaseModel):
    userID: str

class TripCreate(BaseModel):
    title: str
    members: List[str] = []
    description: Optional[str] = None
    tripID: Optional[str] = None

class TripResponse(BaseModel):
    tripID: str
    title: str
    description: Optional[str] = None
    members: List[str]
    ownerID: str
    createdAt: datetime
    updatedAt: datetime

class TripInfoResponse(BaseModel):
    title: str
    members: List[str]
    description: Optional[str] = None

class DashboardResponse(BaseModel):
    yourTrips: List[str]

class CreateFinalPlanRequest(BaseModel):
    tripID: str
    userID: str
    old_plans: List[List[dict]]
    poll_results: dict

# Trip Details Models
class Accommodation(BaseModel):
    id: Optional[str] = None
    name: str
    type: str  # hotel, apartment, hostel, resort, villa, Airbnb, other
    checkIn: Optional[str] = None  # date string
    checkOut: Optional[str] = None  # date string
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    bookingReference: Optional[str] = None
    confirmationNumber: Optional[str] = None
    notes: Optional[str] = None

class Flight(BaseModel):
    id: Optional[str] = None
    type: str  # outbound, return, connecting
    departureAirport: Optional[str] = None
    arrivalAirport: Optional[str] = None
    departureDateTime: Optional[str] = None  # datetime string
    arrivalDateTime: Optional[str] = None  # datetime string
    airline: Optional[str] = None
    flightNumber: Optional[str] = None
    bookingReference: Optional[str] = None
    confirmationNumber: Optional[str] = None
    seatAssignments: Optional[str] = None
    notes: Optional[str] = None

class RentalCar(BaseModel):
    hasRentalCar: bool = False
    company: Optional[str] = None
    pickupLocation: Optional[str] = None
    pickupDateTime: Optional[str] = None  # datetime string
    dropoffLocation: Optional[str] = None
    dropoffDateTime: Optional[str] = None  # datetime string
    carType: Optional[str] = None  # economy, compact, midsize, SUV, luxury
    bookingReference: Optional[str] = None
    confirmationNumber: Optional[str] = None

class PublicTransport(BaseModel):
    passes: List[str] = []  # metro, bus, train, ferry
    details: Optional[str] = None

class Transportation(BaseModel):
    flights: List[Flight] = []
    rentalCar: Optional[RentalCar] = None
    publicTransport: Optional[PublicTransport] = None
    other: Optional[str] = None

class PassportInfo(BaseModel):
    required: bool = False
    expirationDate: Optional[str] = None  # date string
    minimumValidityMonths: Optional[int] = None
    notes: Optional[str] = None

class VisaInfo(BaseModel):
    required: bool = False
    type: Optional[str] = None  # tourist, business, transit, other
    applicationDate: Optional[str] = None  # date string
    approvalDate: Optional[str] = None  # date string
    visaNumber: Optional[str] = None
    notes: Optional[str] = None

class TravelInsurance(BaseModel):
    hasInsurance: bool = False
    provider: Optional[str] = None
    policyNumber: Optional[str] = None
    coverageAmount: Optional[float] = None
    currency: Optional[str] = None
    emergencyContact: Optional[str] = None
    notes: Optional[str] = None

class EmergencyContact(BaseModel):
    id: Optional[str] = None
    name: str
    relationship: Optional[str] = None
    phone: str
    email: Optional[str] = None
    notes: Optional[str] = None

class TravelDocuments(BaseModel):
    passport: Optional[PassportInfo] = None
    visa: Optional[VisaInfo] = None
    travelInsurance: Optional[TravelInsurance] = None
    emergencyContacts: List[EmergencyContact] = []

class BudgetBreakdown(BaseModel):
    accommodation: Optional[float] = None
    food: Optional[float] = None
    activities: Optional[float] = None
    transportation: Optional[float] = None
    shopping: Optional[float] = None
    miscellaneous: Optional[float] = None

class Expense(BaseModel):
    id: Optional[str] = None
    date: str  # date string
    category: str  # accommodation, food, activities, transportation, shopping, miscellaneous
    description: Optional[str] = None
    amount: float

class Budget(BaseModel):
    total: Optional[float] = None
    currency: Optional[str] = None
    breakdown: Optional[BudgetBreakdown] = None
    expenses: List[Expense] = []

class PackingItem(BaseModel):
    id: Optional[str] = None
    item: str
    packed: bool = False

class ImportantNote(BaseModel):
    id: Optional[str] = None
    content: str
    createdAt: Optional[str] = None  # datetime string

class CurrentWeather(BaseModel):
    temperature: Optional[float] = None
    condition: Optional[str] = None
    humidity: Optional[float] = None

class WeatherForecast(BaseModel):
    date: str  # date string
    high: Optional[float] = None
    low: Optional[float] = None
    condition: Optional[str] = None

class WeatherInfo(BaseModel):
    current: Optional[CurrentWeather] = None
    forecast: List[WeatherForecast] = []

class TimeZoneInfo(BaseModel):
    destination: Optional[str] = None
    offset: Optional[str] = None
    differenceFromHome: Optional[str] = None

class AdditionalDetails(BaseModel):
    packingList: List[PackingItem] = []
    importantNotes: List[ImportantNote] = []
    weather: Optional[WeatherInfo] = None
    timeZone: Optional[TimeZoneInfo] = None

class TripDetails(BaseModel):
    tripID: str
    accommodations: List[Accommodation] = []
    transportation: Optional[Transportation] = None
    documents: Optional[TravelDocuments] = None
    budget: Optional[Budget] = None
    additional: Optional[AdditionalDetails] = None
    updatedAt: Optional[str] = None  # datetime string

# Trip Details Itinerary Model (for itinerary-based details)
class ActivityDetail(BaseModel):
    id: Optional[str] = None
    activity_id: Optional[str] = None
    activity_name: str
    type: str
    description: str
    from_date_time: Optional[str] = None
    to_date_time: Optional[str] = None
    location: Optional[str] = None
    vigor: Optional[str] = None
    start_lat: Optional[float] = None
    start_lon: Optional[float] = None
    end_lat: Optional[float] = None
    end_lon: Optional[float] = None

class DayDetail(BaseModel):
    id: int
    date: str
    location: str
    description: str
    activities: List[ActivityDetail] = []

class TripDetailsItinerary(BaseModel):
    tripID: Optional[str] = None
    days: List[DayDetail] = []
    trip_summary: Optional[str] = None

# Helper functions
async def get_next_id(collection_name: str) -> str:
    """Generate next sequential ID for a collection."""
    counter_collection = db.id_counters
    result = await counter_collection.find_one_and_update(
        {"_id": collection_name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    seq = result.get("seq", 1)
    prefix = collection_name.replace("users", "user").replace("trips", "trip")
    return f"{prefix}_{str(seq).zfill(3)}"

async def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

async def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

async def generate_invite_code() -> str:
    """Generate a unique invite code (8 characters, alphanumeric uppercase)."""
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(secrets.choice(alphabet) for _ in range(8))
        # Check if code already exists
        existing = await db.trips.find_one({"inviteCode": code})
        if not existing:
            return code

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Vibecation API", "version": "1.0.0"}

@app.get("/login", response_model=LoginResponse)
async def login(
    username: str = Query(...),
    password: str = Query(...)
):
    """User login endpoint."""
    user = await db.users.find_one({"username": username, "isActive": True})
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not await verify_password(password, user.get("passwordHash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Update last login
    await db.users.update_one(
        {"userID": user["userID"]},
        {"$set": {"lastLoginAt": datetime.utcnow()}}
    )
    
    return LoginResponse(userID=user["userID"])

@app.post("/users", response_model=UserResponse, status_code=201)
async def create_user(user_data: UserCreate):
    """Create a new user account."""
    # Check if username or email already exists
    existing_user = await db.users.find_one({
        "$or": [
            {"username": user_data.username},
            {"email": user_data.email}
        ]
    })
    
    if existing_user:
        if existing_user.get("username") == user_data.username:
            raise HTTPException(
                status_code=409,
                detail={"error": "Username already exists", "field": "username"}
            )
        if existing_user.get("email") == user_data.email:
            raise HTTPException(
                status_code=409,
                detail={"error": "Email already registered", "field": "email"}
            )
    
    # Generate user ID
    user_id = await get_next_id("users")
    
    # Hash password
    password_hash = await hash_password(user_data.password)
    
    # Create user document
    user_doc = {
        "userID": user_id,
        "username": user_data.username,
        "email": user_data.email,
        "name": user_data.name,
        "passwordHash": password_hash,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow(),
        "isActive": True
    }
    
    await db.users.insert_one(user_doc)
    
    return UserResponse(
        userID=user_id,
        username=user_data.username,
        email=user_data.email,
        name=user_data.name
    )

@app.get("/users/check-availability")
async def check_availability(
    username: Optional[str] = Query(None),
    email: Optional[str] = Query(None)
):
    """Check username or email availability."""
    if not username and not email:
        raise HTTPException(status_code=400, detail="Must provide either username or email")
    
    query = {}
    field = None
    if username:
        query["username"] = username
        field = "username"
    if email:
        query["email"] = email
        field = "email"
    
    existing_user = await db.users.find_one(query)
    
    return {
        "available": existing_user is None,
        "field": field
    }

@app.get("/users/{userID}", response_model=UserResponse)
async def get_user(userID: str):
    """Get user profile information."""
    user = await db.users.find_one({"userID": userID, "isActive": True})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        userID=user["userID"],
        username=user["username"],
        email=user["email"],
        name=user["name"]
    )

@app.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(userID: str = Query(...)):
    """Get user dashboard with all trips."""
    # Find trips where user is owner or member
    trips = await db.trips.find({
        "$or": [
            {"ownerID": userID},
            {"members": userID}
        ]
    }).to_list(length=None)
    
    trip_ids = [trip["tripID"] for trip in trips]
    
    return DashboardResponse(yourTrips=trip_ids)

@app.get("/tripinfo", response_model=TripInfoResponse)
async def get_trip_info(tripID: str = Query(...)):
    """Get trip information."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    trip = await db.trips.find_one({"tripID": tripID})
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    return TripInfoResponse(
        title=trip.get("title", ""),
        members=trip.get("members", []),
        description=trip.get("description")
    )

@app.get("/check_brainstorm_completion")
async def check_brainstorm_completion(tripID: str = Query(...)):
    """Check if all trip members have finished brainstorming (submitted suggestions)."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    # Get trip info to get all members
    trip = await db.trips.find_one({"tripID": tripID})
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    members = trip.get("members", [])
    if not members:
        return {
            "allCompleted": False,
            "totalMembers": 0,
            "completedMembers": 0,
            "completedUserIDs": []
        }
    
    # Get all submitted suggestions for this trip
    submitted_suggestions = await db.trip_suggestions.find({
        "tripID": tripID,
        "status": "submitted"
    }).to_list(length=100)
    
    completed_user_ids = [s["userID"] for s in submitted_suggestions]
    completed_count = len(set(completed_user_ids))  # Use set to avoid duplicates
    
    return {
        "allCompleted": completed_count >= len(members),
        "totalMembers": len(members),
        "completedMembers": completed_count,
        "completedUserIDs": list(set(completed_user_ids)),
        "allMemberIDs": members
    }

@app.post("/createtrip", response_model=dict, status_code=201)
async def create_trip(trip_data: TripCreate, userID: str = Query(...)):
    """Create a new trip."""
    # Generate trip ID if not provided
    trip_id = trip_data.tripID or await get_next_id("trips")
    
    # Ensure creator is in members list
    members = list(set([userID] + trip_data.members))
    
    # Generate unique invite code
    invite_code = await generate_invite_code()
    
    trip_doc = {
        "tripID": trip_id,
        "title": trip_data.title,
        "description": trip_data.description or "",
        "ownerID": userID,
        "members": members,
        "inviteCode": invite_code,
        "status": "planning",
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }
    
    await db.trips.insert_one(trip_doc)
    
    return {
        "tripID": trip_id,
        "inviteCode": invite_code,
        "message": "Trip created successfully"
    }

@app.get("/trips/{tripID}", response_model=TripResponse)
async def get_trip(tripID: str):
    """Get trip details."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    trip = await db.trips.find_one({"tripID": tripID})
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    return TripResponse(
        tripID=trip["tripID"],
        title=trip.get("title", ""),
        description=trip.get("description"),
        members=trip.get("members", []),
        ownerID=trip.get("ownerID", ""),
        createdAt=trip.get("createdAt", datetime.utcnow()),
        updatedAt=trip.get("updatedAt", datetime.utcnow())
    )

@app.delete("/trips/{tripID}", status_code=204)
async def delete_trip(tripID: str):
    """Delete a trip."""
    result = await db.trips.delete_one({"tripID": tripID})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    return None

@app.get("/trips/{tripID}/invite-code")
async def get_invite_code(tripID: str, userID: str = Query(...)):
    """Get invite code for a trip. Only owner can access."""
    trip = await db.trips.find_one({"tripID": tripID})
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Only owner can get the invite code
    if trip.get("ownerID") != userID:
        raise HTTPException(status_code=403, detail="Only trip owner can access invite code")
    
    invite_code = trip.get("inviteCode")
    if not invite_code:
        # Generate one if it doesn't exist (for backward compatibility)
        invite_code = await generate_invite_code()
        await db.trips.update_one(
            {"tripID": tripID},
            {"$set": {"inviteCode": invite_code, "updatedAt": datetime.utcnow()}}
        )
    
    return {
        "tripID": tripID,
        "inviteCode": invite_code
    }

@app.post("/trips/join")
async def join_trip_by_invite_code(invite_code: str = Query(..., alias="inviteCode"), userID: str = Query(...)):
    """Join a trip using an invite code."""
    if not invite_code:
        raise HTTPException(status_code=400, detail="Invite code is required")
    
    # Find trip by invite code
    trip = await db.trips.find_one({"inviteCode": invite_code.upper()})
    
    if not trip:
        raise HTTPException(status_code=404, detail="Invalid invite code")
    
    # Check if user is already a member
    if userID in trip.get("members", []):
        return {
            "tripID": trip["tripID"],
            "message": "You are already a member of this trip",
            "alreadyMember": True
        }
    
    # Add user to members list
    members = trip.get("members", [])
    if userID not in members:
        members.append(userID)
        await db.trips.update_one(
            {"tripID": trip["tripID"]},
            {
                "$set": {
                    "members": members,
                    "updatedAt": datetime.utcnow()
                }
            }
        )
    
    return {
        "tripID": trip["tripID"],
        "title": trip.get("title", ""),
        "message": "Successfully joined trip",
        "alreadyMember": False
    }

# Mock data for trip details
MOCK_TRIP_DETAILS = {
    "days": [
        {
            "id": 1,
            "date": "2024-07-01",
            "location": "Athens International Airport",
            "description": "Day 1 in Athens International Airport",
            "activities": [
                {
                    "id": "day1-athens-arrival",
                    "activity_id": "day1-athens-arrival",
                    "activity_name": "Arrive in Athens & Explore the Acropolis",
                    "type": "attraction",
                    "description": "Arrive at Athens International Airport in the morning, transfer to your hotel, and set out to explore the Acropolis. Visit the Parthenon and the Acropolis Museum. Enjoy a traditional Greek dinner in Plaka in the evening.",
                    "from_date_time": "2024-07-01T09:00:00+03:00",
                    "to_date_time": "2024-07-01T18:00:00+03:00",
                    "location": "Athens International Airport",
                    "vigor": "medium",
                    "start_lat": 37.9364,
                    "start_lon": 23.9445,
                    "end_lat": 37.9715,
                    "end_lon": 23.7267
                }
            ]
        },
        {
            "id": 2,
            "date": "2024-07-02",
            "location": "Hotel in Athens",
            "description": "Day 2 in Hotel in Athens",
            "activities": [
                {
                    "id": "day2-athens-walk",
                    "activity_id": "day2-athens-walk",
                    "activity_name": "Athens City Walk & Plaka Neighborhood",
                    "type": "attraction",
                    "description": "Discover Athens highlights: Ancient Agora, Temple of Olympian Zeus, changing of the guard at Syntagma Square. Evening stroll in Plaka, dinner at a taverna.",
                    "from_date_time": "2024-07-02T09:00:00+03:00",
                    "to_date_time": "2024-07-02T20:00:00+03:00",
                    "location": "Hotel in Athens",
                    "vigor": "medium",
                    "start_lat": 37.985,
                    "start_lon": 23.733,
                    "end_lat": 37.9737,
                    "end_lon": 23.7306
                }
            ]
        },
        {
            "id": 3,
            "date": "2024-07-03",
            "location": "Athens",
            "description": "Day 3 in Athens",
            "activities": [
                {
                    "id": "day3-delphi-trip",
                    "activity_id": "day3-delphi-trip",
                    "activity_name": "Day Trip to Delphi",
                    "type": "travel",
                    "description": "Take a guided day trip to the ancient site of Delphi. Tour the Temple of Apollo, Theater, and Archaeological Museum. Return to Athens in the evening.",
                    "from_date_time": "2024-07-03T07:00:00+03:00",
                    "to_date_time": "2024-07-03T19:00:00+03:00",
                    "location": "Athens",
                    "vigor": "low",
                    "start_lat": 37.9838,
                    "start_lon": 23.7275,
                    "end_lat": 38.4839,
                    "end_lon": 22.501
                }
            ]
        },
        {
            "id": 4,
            "date": "2024-07-04",
            "location": "Piraeus Port",
            "description": "Day 4 in Piraeus Port",
            "activities": [
                {
                    "id": "day4-ferry-mykonos",
                    "activity_id": "day4-ferry-mykonos",
                    "activity_name": "Ferry to Mykonos & Beach Afternoon",
                    "type": "travel",
                    "description": "Take the morning ferry from Piraeus to Mykonos. Check in to your hotel and spend the afternoon relaxing on one of Mykonos's beautiful beaches.",
                    "from_date_time": "2024-07-04T08:00:00+03:00",
                    "to_date_time": "2024-07-04T15:00:00+03:00",
                    "location": "Piraeus Port",
                    "vigor": "low",
                    "start_lat": 37.9429,
                    "start_lon": 23.6466,
                    "end_lat": 37.4467,
                    "end_lon": 25.3289
                }
            ]
        },
        {
            "id": 5,
            "date": "2024-07-05",
            "location": "Mykonos Town",
            "description": "Day 5 in Mykonos Town",
            "activities": [
                {
                    "id": "day5-mykonos-discovery",
                    "activity_id": "day5-mykonos-discovery",
                    "activity_name": "Explore Mykonos Town & Beaches",
                    "type": "attraction",
                    "description": "Wander through Mykonos Town, see the iconic windmills and Little Venice, then relax at Super Paradise Beach. Enjoy Mykonos nightlife.",
                    "from_date_time": "2024-07-05T09:00:00+03:00",
                    "to_date_time": "2024-07-05T20:00:00+03:00",
                    "location": "Mykonos Town",
                    "vigor": "medium",
                    "start_lat": 37.4467,
                    "start_lon": 25.3289,
                    "end_lat": 37.4283,
                    "end_lon": 25.3603
                }
            ]
        },
        {
            "id": 6,
            "date": "2024-07-06",
            "location": "Mykonos Old Port",
            "description": "Day 6 in Mykonos Old Port",
            "activities": [
                {
                    "id": "day6-delos-excursion",
                    "activity_id": "day6-delos-excursion",
                    "activity_name": "Day Excursion to Delos",
                    "type": "attraction",
                    "description": "Join a boat tour from Mykonos Old Port to Delos Island. Guided tour of the UNESCO World Heritage Site, return to Mykonos for the afternoon.",
                    "from_date_time": "2024-07-06T09:30:00+03:00",
                    "to_date_time": "2024-07-06T14:00:00+03:00",
                    "location": "Mykonos Old Port",
                    "vigor": "medium",
                    "start_lat": 37.451,
                    "start_lon": 25.3276,
                    "end_lat": 37.399,
                    "end_lon": 25.2678
                }
            ]
        },
        {
            "id": 7,
            "date": "2024-07-07",
            "location": "Mykonos Port",
            "description": "Day 7 in Mykonos Port",
            "activities": [
                {
                    "id": "day7-ferry-santorini",
                    "activity_id": "day7-ferry-santorini",
                    "activity_name": "Ferry to Santorini & Oia Sunset",
                    "type": "travel",
                    "description": "Morning ferry to Santorini, check in to your cliffside hotel. Evening visit to beautiful Oia for the iconic sunset.",
                    "from_date_time": "2024-07-07T08:00:00+03:00",
                    "to_date_time": "2024-07-07T17:00:00+03:00",
                    "location": "Mykonos Port",
                    "vigor": "low",
                    "start_lat": 37.454,
                    "start_lon": 25.345,
                    "end_lat": 36.4617,
                    "end_lon": 25.3754
                }
            ]
        },
        {
            "id": 8,
            "date": "2024-07-08",
            "location": "Fira, Santorini",
            "description": "Day 8 in Fira, Santorini",
            "activities": [
                {
                    "id": "day8-santorini-explore",
                    "activity_id": "day8-santorini-explore",
                    "activity_name": "Santorini Highlights: Akrotiri, Beaches & Winery",
                    "type": "attraction",
                    "description": "Tour the Akrotiri Archaeological Site, visit Red Beach and Perissa's black sands, with a wine tasting at a local winery.",
                    "from_date_time": "2024-07-08T09:00:00+03:00",
                    "to_date_time": "2024-07-08T20:00:00+03:00",
                    "location": "Fira, Santorini",
                    "vigor": "medium",
                    "start_lat": 36.4167,
                    "start_lon": 25.4333,
                    "end_lat": 36.4146,
                    "end_lon": 25.4556
                }
            ]
        },
        {
            "id": 9,
            "date": "2024-07-09",
            "location": "Santorini Old Port",
            "description": "Day 9 in Santorini Old Port",
            "activities": [
                {
                    "id": "day9-catamaran-santorini",
                    "activity_id": "day9-catamaran-santorini",
                    "activity_name": "Santorini Catamaran Cruise",
                    "type": "entertainment",
                    "description": "Full-day catamaran cruise with stops for swimming, snorkeling, and a seafood lunch on board. Enjoy views of the caldera.",
                    "from_date_time": "2024-07-09T10:00:00+03:00",
                    "to_date_time": "2024-07-09T18:30:00+03:00",
                    "location": "Santorini Old Port",
                    "vigor": "medium",
                    "start_lat": 36.419,
                    "start_lon": 25.428,
                    "end_lat": 36.419,
                    "end_lon": 25.428
                }
            ]
        },
        {
            "id": 10,
            "date": "2024-07-10",
            "location": "Santorini Airport/Port",
            "description": "Day 10 in Santorini Airport/Port",
            "activities": [
                {
                    "id": "day10-athens-return-departure",
                    "activity_id": "day10-athens-return-departure",
                    "activity_name": "Return to Athens & Departure",
                    "type": "travel",
                    "description": "Morning flight or ferry back to Athens. If time permits, enjoy some last-minute shopping in the Monastiraki area before your departure.",
                    "from_date_time": "2024-07-10T07:00:00+03:00",
                    "to_date_time": "2024-07-10T17:00:00+03:00",
                    "location": "Santorini Airport/Port",
                    "vigor": "low",
                    "start_lat": 36.4035,
                    "start_lon": 25.4793,
                    "end_lat": 37.9364,
                    "end_lon": 23.9445
                }
            ]
        }
    ],
    "trip_summary": "This 10-day Greece itinerary offers a perfect blend of ancient history, vibrant island life, and relaxing beaches. Begin your journey in Athens, exploring iconic sites like the Acropolis before venturing on a day trip to the mystical ruins of Delphi. Continue your adventure by ferry to Mykonos with its picturesque town, lively beaches, and a day trip to the archaeological wonder of Delos. Next, experience the awe-inspiring beauty of Santorini—from volcanic beaches and archaeological treasures to the legendary sunset in Oia. Cap off your journey with a catamaran cruise and a relaxed return to Athens for your departure. Perfect for first-time visitors who want to experience the classics and the charms of the islands."
}

@app.get("/trips/{tripID}/details", response_model=TripDetailsItinerary)
async def get_trip_details(tripID: str):
    """Get trip details itinerary."""
    if db is None:
        # Return mock data if database not connected
        mock_data = MOCK_TRIP_DETAILS.copy()
        mock_data["tripID"] = tripID
        return TripDetailsItinerary(**mock_data)
    
    # Check if trip exists
    trip = await db.trips.find_one({"tripID": tripID})
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Try to get trip details from database
    trip_details = await db.trip_details.find_one({"tripID": tripID})
    
    if trip_details:
        # Remove MongoDB _id field
        trip_details.pop("_id", None)
        # Check if it's the new format (with days) or old format
        if "days" in trip_details:
            return TripDetailsItinerary(**trip_details)
        else:
            # Old format - return mock data for now
            mock_data = MOCK_TRIP_DETAILS.copy()
            mock_data["tripID"] = tripID
            return TripDetailsItinerary(**mock_data)
    else:
        # Return mock data if no details exist
        mock_data = MOCK_TRIP_DETAILS.copy()
        mock_data["tripID"] = tripID
        return TripDetailsItinerary(**mock_data)

@app.put("/trips/{tripID}/details", response_model=dict)
async def update_trip_details(tripID: str, details: TripDetailsItinerary):
    """Update trip details itinerary."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    # Check if trip exists
    trip = await db.trips.find_one({"tripID": tripID})
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Ensure tripID matches
    details.tripID = tripID
    
    # Convert to dict
    details_dict = details.model_dump()
    
    # Upsert trip details
    await db.trip_details.update_one(
        {"tripID": tripID},
        {"$set": details_dict},
        upsert=True
    )
    
    return {
        "message": "Trip details updated successfully",
        "tripDetails": details_dict
    }

# Mock data for suggestions and polls
MOCK_SUGGESTIONS = [
    {
        "userID": "user_001",
        "days": [
            {
                "id": 1,
                "date": "2025-04-12",
                "location": "Barcelona",
                "description": "Day 1 in Barcelona",
                "activities": [
                    {
                        "id": 1,
                        "activity_id": "act_001",
                        "activity_name": "Sagrada Familia tour",
                        "type": "sightseeing",
                        "description": "Guided tour of Gaudí's masterpiece",
                        "vigor": "medium",
                        "from_date_time": "2025-04-12T10:00:00Z",
                        "to_date_time": "2025-04-12T11:30:00Z",
                        "location": "Sagrada Familia"
                    },
                    {
                        "id": 2,
                        "activity_id": "act_002",
                        "activity_name": "Park Güell visit",
                        "type": "sightseeing",
                        "description": "Visit Gaudí's whimsical park",
                        "vigor": "low",
                        "from_date_time": "2025-04-12T14:00:00Z",
                        "to_date_time": "2025-04-12T16:00:00Z",
                        "location": "Park Güell"
                    }
                ]
            },
            {
                "id": 2,
                "date": "2025-04-13",
                "location": "Barcelona",
                "description": "Day 2 in Barcelona",
                "activities": [
                    {
                        "id": 3,
                        "activity_id": "act_003",
                        "activity_name": "Beach day",
                        "type": "relaxing",
                        "description": "Relax at Barceloneta Beach",
                        "vigor": "low",
                        "from_date_time": "2025-04-13T10:00:00Z",
                        "to_date_time": "2025-04-13T16:00:00Z",
                        "location": "Barceloneta Beach"
                    }
                ]
            }
        ]
    },
    {
        "userID": "user_002",
        "days": [
            {
                "id": 1,
                "date": "2025-04-12",
                "location": "Barcelona",
                "description": "Day 1 in Barcelona",
                "activities": [
                    {
                        "id": 1,
                        "activity_id": "act_001",
                        "activity_name": "Sagrada Familia tour",
                        "type": "sightseeing",
                        "description": "Guided tour of Gaudí's masterpiece",
                        "vigor": "medium",
                        "from_date_time": "2025-04-12T10:00:00Z",
                        "to_date_time": "2025-04-12T11:30:00Z",
                        "location": "Sagrada Familia"
                    },
                    {
                        "id": 4,
                        "activity_id": "act_004",
                        "activity_name": "Tapas tour",
                        "type": "food",
                        "description": "Explore local tapas bars",
                        "vigor": "low",
                        "from_date_time": "2025-04-12T19:00:00Z",
                        "to_date_time": "2025-04-12T21:00:00Z",
                        "location": "Gothic Quarter"
                    }
                ]
            }
        ]
    }
]

MOCK_ACTIVITIES = [
    {
        "activity_id": "act_001",
        "activity_name": "Sagrada Familia tour",
        "type": "sightseeing",
        "description": "Guided tour of Gaudí's masterpiece, the iconic Sagrada Familia basilica",
        "vigor": "medium",
        "location": "Sagrada Familia",
        "upvotes": 5,
        "downvotes": 1,
        "user_vote": None
    },
    {
        "activity_id": "act_002",
        "activity_name": "Park Güell visit",
        "type": "sightseeing",
        "description": "Visit Gaudí's whimsical Park Güell with colorful mosaics",
        "vigor": "low",
        "location": "Park Güell",
        "upvotes": 4,
        "downvotes": 0,
        "user_vote": None
    },
    {
        "activity_id": "act_003",
        "activity_name": "Beach day",
        "type": "relaxing",
        "description": "Relax at Barceloneta Beach",
        "vigor": "low",
        "location": "Barceloneta Beach",
        "upvotes": 3,
        "downvotes": 2,
        "user_vote": None
    },
    {
        "activity_id": "act_004",
        "activity_name": "Tapas tour",
        "type": "food",
        "description": "Explore local tapas bars in the Gothic Quarter",
        "vigor": "low",
        "location": "Gothic Quarter",
        "upvotes": 6,
        "downvotes": 0,
        "user_vote": None
    },
    {
        "activity_id": "act_005",
        "activity_name": "Flamenco show",
        "type": "entertainment",
        "description": "Experience traditional Spanish flamenco performance",
        "vigor": "medium",
        "location": "Flamenco Theater",
        "upvotes": 4,
        "downvotes": 1,
        "user_vote": None
    }
]

MOCK_LOCATIONS = [
    {
        "location_id": "loc_001",
        "name": "Barcelona",
        "type": "city",
        "lat": 41.4036,
        "lon": 2.1744,
        "upvotes": 5,
        "downvotes": 0,
        "user_vote": None
    },
    {
        "location_id": "loc_002",
        "name": "Madrid",
        "type": "city",
        "lat": 40.4168,
        "lon": -3.7038,
        "upvotes": 3,
        "downvotes": 1,
        "user_vote": None
    },
    {
        "location_id": "loc_003",
        "name": "Valencia",
        "type": "city",
        "lat": 39.4699,
        "lon": -0.3763,
        "upvotes": 2,
        "downvotes": 2,
        "user_vote": None
    },
    {
        "location_id": "loc_004",
        "name": "Seville",
        "type": "city",
        "lat": 37.3891,
        "lon": -5.9845,
        "upvotes": 1,
        "downvotes": 3,
        "user_vote": None
    }
]

MOCK_CUISINES = [
    {"name": "Spanish", "votes": 0, "selected": False},
    {"name": "Tapas", "votes": 0, "selected": False},
    {"name": "Mediterranean", "votes": 0, "selected": False},
    {"name": "Seafood", "votes": 0, "selected": False},
    {"name": "Catalan", "votes": 0, "selected": False},
    {"name": "Italian", "votes": 0, "selected": False},
    {"name": "French", "votes": 0, "selected": False}
]

@app.get("/get_all_trip_suggestions")
async def get_all_trip_suggestions(tripID: str = Query(...)):
    """Get all trip suggestions from database."""
    if db is None:
        # Fallback to mock data if database not connected
        return {
            "suggestions": [s["days"] for s in MOCK_SUGGESTIONS],
            "participants": [s["userID"] for s in MOCK_SUGGESTIONS]
        }
    
    # Get all submitted suggestions for this trip
    suggestions = await db.trip_suggestions.find({
        "tripID": tripID,
        "status": "submitted"
    }).sort("submittedAt", -1).to_list(length=100)
    
    return {
        "suggestions": [s["days"] for s in suggestions],
        "participants": [s["userID"] for s in suggestions]
    }

@app.get("/polls/get/activity")
async def get_activity_poll(tripID: str = Query(...), userID: str = Query(None)):
    """
    Get activity poll with real vote counts from database.
    If userID is provided, also includes the user's vote for each activity.
    """
    if db is None:
        # Fallback to mock data if database not connected
        return {"activities": MOCK_ACTIVITIES}
    
    votes_collection = db.votes
    
    # Get all votes for activities in this trip
    activity_votes = await votes_collection.find({
        "tripID": tripID,
        "voteType": "activity"
    }).to_list(length=1000)
    
    # Aggregate votes by activityID
    vote_counts = {}
    user_votes = {}
    
    for vote in activity_votes:
        activity_id = vote["optionID"]
        
        # Count upvotes and downvotes
        if activity_id not in vote_counts:
            vote_counts[activity_id] = {"upvotes": 0, "downvotes": 0}
        
        if vote["vote"]:
            vote_counts[activity_id]["upvotes"] += 1
        else:
            vote_counts[activity_id]["downvotes"] += 1
        
        # Track user's vote if userID provided
        if userID and vote["userID"] == userID:
            user_votes[activity_id] = vote["vote"]
    
    # Start with mock activities and enrich with real vote data
    activities = []
    for mock_activity in MOCK_ACTIVITIES:
        activity_id = mock_activity["activity_id"]
        
        # Get real vote counts from database
        counts = vote_counts.get(activity_id, {"upvotes": 0, "downvotes": 0})
        
        activity = {
            **mock_activity,
            "upvotes": counts["upvotes"],
            "downvotes": counts["downvotes"],
            "user_vote": user_votes.get(activity_id, None)
        }
        activities.append(activity)
    
    return {"activities": activities}

@app.get("/polls/get/location")
async def get_location_poll(tripID: str = Query(...)):
    """Get location poll (mock data)."""
    # Return mock locations regardless of tripID
    return {"locations": MOCK_LOCATIONS}

@app.get("/polls/get/food_cuisines")
async def get_food_cuisines_poll(tripID: str = Query(...), userID: str = Query(None)):
    """
    Get food cuisine poll with real vote counts from database.
    If userID is provided, also includes the user's selected cuisines.
    """
    if db is None:
        # Fallback to mock data if database not connected
        return {"cuisines": MOCK_CUISINES}
    
    votes_collection = db.votes
    
    # Get all cuisine votes for this trip
    cuisine_votes = await votes_collection.find({
        "tripID": tripID,
        "voteType": "food_cuisine"
    }).to_list(length=1000)
    
    # Count votes per cuisine (upvotes and downvotes)
    vote_counts = {}
    user_votes = {}
    
    for vote in cuisine_votes:
        cuisine_name = vote.get("optionID") or vote.get("voteValue")  # optionID stores the cuisine name
        
        if cuisine_name:
            # Count upvotes and downvotes
            if cuisine_name not in vote_counts:
                vote_counts[cuisine_name] = {"upvotes": 0, "downvotes": 0}
            
            if vote.get("vote", True):  # True means upvote (selected)
                vote_counts[cuisine_name]["upvotes"] += 1
            else:
                vote_counts[cuisine_name]["downvotes"] += 1
            
            # Track user's vote if userID provided
            if userID and vote["userID"] == userID:
                user_votes[cuisine_name] = vote.get("vote", True)
    
    # Start with mock cuisines and enrich with real vote data
    cuisines = []
    for mock_cuisine in MOCK_CUISINES:
        cuisine_name = mock_cuisine["name"]
        
        counts = vote_counts.get(cuisine_name, {"upvotes": 0, "downvotes": 0})
        
        cuisine = {
            **mock_cuisine,
            "upvotes": counts["upvotes"],
            "downvotes": counts["downvotes"],
            "user_vote": user_votes.get(cuisine_name, None)
        }
        cuisines.append(cuisine)
    
    return {"cuisines": cuisines}


@app.post("/polls/vote/food_cuisine")
async def vote_food_cuisine(vote_data: dict):
    """
    Vote on a cuisine. Works like activity/location votes - upvote selects, downvote deselects.
    Ensures one vote per user per cuisine. If user already voted, updates the vote. If same vote is clicked, removes it.
    """
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    tripID = vote_data.get("tripID")
    cuisineName = vote_data.get("cuisineName")  # Changed from selectedCuisines array
    userID = vote_data.get("userID")
    vote = vote_data.get("vote")  # True for upvote (select), False for downvote (deselect)
    
    if not all([tripID, cuisineName, userID, vote is not None]):
        raise HTTPException(status_code=400, detail="Missing required fields: tripID, cuisineName, userID, vote")
    
    votes_collection = db.votes
    optionID = cuisineName
    voteType = "food_cuisine"
    
    # Check if user already voted on this cuisine
    vote_query = {
        "tripID": tripID,
        "userID": userID,
        "optionID": optionID,
        "voteType": voteType
    }
    
    existing_vote = await votes_collection.find_one(vote_query)
    
    if existing_vote:
        # User already voted - check if it's the same vote
        if existing_vote["vote"] == vote:
            # Same vote clicked - remove the vote (toggle off)
            await votes_collection.delete_one({"_id": existing_vote["_id"]})
            return {
                "message": "Vote removed",
                "vote": None,
                "action": "removed"
            }
        else:
            # Different vote - update the existing vote
            await votes_collection.update_one(
                {"_id": existing_vote["_id"]},
                {
                    "$set": {
                        "vote": vote,
                        "updatedAt": datetime.utcnow()
                    }
                }
            )
            return {
                "message": "Vote updated successfully",
                "vote": vote,
                "action": "updated"
            }
    else:
        # New vote - create it (works for both upvote and downvote, same as activities/locations)
        vote_doc = {
            "tripID": tripID,
            "userID": userID,
            "optionID": optionID,
            "voteType": voteType,
            "vote": vote,
            "voteValue": cuisineName,  # Store cuisine name in voteValue
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
        
        try:
            await votes_collection.insert_one(vote_doc)
            return {
                "message": "Vote recorded successfully",
                "vote": vote,
                "action": "created"
            }
        except Exception as e:
            # Handle duplicate key error
            if "duplicate" in str(e).lower() or "E11000" in str(e):
                existing = await votes_collection.find_one(vote_query)
                if existing:
                    await votes_collection.update_one(
                        {"_id": existing["_id"]},
                        {
                            "$set": {
                                "vote": vote,
                                "updatedAt": datetime.utcnow()
                            }
                        }
                    )
                    return {
                        "message": "Vote updated successfully",
                        "vote": vote,
                        "action": "updated"
                    }
            raise HTTPException(status_code=500, detail=f"Failed to record vote: {str(e)}")

@app.post("/polls/vote/activity")
async def vote_activity(vote_data: dict):
    """
    Vote on an activity. Ensures one vote per user per activity.
    If user already voted, updates the vote. If same vote is clicked, removes it.
    """
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    tripID = vote_data.get("tripID")
    activityID = vote_data.get("activityID")
    userID = vote_data.get("userID")
    vote = vote_data.get("vote")
    
    if not all([tripID, activityID, userID, vote is not None]):
        raise HTTPException(status_code=400, detail="Missing required fields: tripID, activityID, userID, vote")
    
    votes_collection = db.votes
    optionID = activityID
    voteType = "activity"
    
    # Check if user already voted on this activity
    vote_query = {
        "tripID": tripID,
        "userID": userID,
        "optionID": optionID,
        "voteType": voteType
    }
    
    existing_vote = await votes_collection.find_one(vote_query)
    
    if existing_vote:
        # User already voted - check if it's the same vote
        if existing_vote["vote"] == vote:
            # Same vote clicked - remove the vote (toggle off)
            await votes_collection.delete_one({"_id": existing_vote["_id"]})
            return {
                "message": "Vote removed",
                "vote": None,
                "action": "removed"
            }
        else:
            # Different vote - update the existing vote
            await votes_collection.update_one(
                {"_id": existing_vote["_id"]},
                {
                    "$set": {
                        "vote": vote,
                        "updatedAt": datetime.utcnow()
                    }
                }
            )
            return {
                "message": "Vote updated successfully",
                "vote": vote,
                "action": "updated"
            }
    else:
        # New vote - create it
        vote_doc = {
            "tripID": tripID,
            "userID": userID,
            "optionID": optionID,
            "voteType": voteType,
            "vote": vote,
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
        
        try:
            await votes_collection.insert_one(vote_doc)
            return {
                "message": "Vote recorded successfully",
                "vote": vote,
                "action": "created"
            }
        except Exception as e:
            # Handle duplicate key error (shouldn't happen, but just in case)
            if "duplicate" in str(e).lower() or "E11000" in str(e):
                # Vote was created between check and insert - try to update instead
                existing = await votes_collection.find_one(vote_query)
                if existing:
                    await votes_collection.update_one(
                        {"_id": existing["_id"]},
                        {
                            "$set": {
                                "vote": vote,
                                "updatedAt": datetime.utcnow()
                            }
                        }
                    )
                    return {
                        "message": "Vote updated successfully",
                        "vote": vote,
                        "action": "updated"
                    }
            raise HTTPException(status_code=500, detail=f"Failed to record vote: {str(e)}")


@app.post("/polls/vote/location")
async def vote_location(vote_data: dict):
    """
    Vote on a location. Ensures one vote per user per location.
    If user already voted, updates the vote. If same vote is clicked, removes it.
    """
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    tripID = vote_data.get("tripID")
    locationID = vote_data.get("locationID")
    userID = vote_data.get("userID")
    vote = vote_data.get("vote")
    
    if not all([tripID, locationID, userID, vote is not None]):
        raise HTTPException(status_code=400, detail="Missing required fields: tripID, locationID, userID, vote")
    
    votes_collection = db.votes
    optionID = locationID
    voteType = "location"
    
    # Check if user already voted on this location
    vote_query = {
        "tripID": tripID,
        "userID": userID,
        "optionID": optionID,
        "voteType": voteType
    }
    
    existing_vote = await votes_collection.find_one(vote_query)
    
    if existing_vote:
        # User already voted - check if it's the same vote
        if existing_vote["vote"] == vote:
            # Same vote clicked - remove the vote (toggle off)
            await votes_collection.delete_one({"_id": existing_vote["_id"]})
            return {
                "message": "Vote removed",
                "vote": None,
                "action": "removed"
            }
        else:
            # Different vote - update the existing vote
            await votes_collection.update_one(
                {"_id": existing_vote["_id"]},
                {
                    "$set": {
                        "vote": vote,
                        "updatedAt": datetime.utcnow()
                    }
                }
            )
            return {
                "message": "Vote updated successfully",
                "vote": vote,
                "action": "updated"
            }
    else:
        # New vote - create it
        vote_doc = {
            "tripID": tripID,
            "userID": userID,
            "optionID": optionID,
            "voteType": voteType,
            "vote": vote,
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
        
        try:
            await votes_collection.insert_one(vote_doc)
            return {
                "message": "Vote recorded successfully",
                "vote": vote,
                "action": "created"
            }
        except Exception as e:
            # Handle duplicate key error
            if "duplicate" in str(e).lower() or "E11000" in str(e):
                existing = await votes_collection.find_one(vote_query)
                if existing:
                    await votes_collection.update_one(
                        {"_id": existing["_id"]},
                        {
                            "$set": {
                                "vote": vote,
                                "updatedAt": datetime.utcnow()
                            }
                        }
                    )
                    return {
                        "message": "Vote updated successfully",
                        "vote": vote,
                        "action": "updated"
                    }
            raise HTTPException(status_code=500, detail=f"Failed to record vote: {str(e)}")

# Mock data for brainstorm
MOCK_DAYS = [
    {
        "id": 1,
        "date": "2025-04-12",
        "location": "Barcelona",
        "description": "Day 1 in Barcelona",
        "activities": [
            {
                "id": 1,
                "activity_id": "act_001",
                "activity_name": "Sagrada Familia tour",
                "type": "sightseeing",
                "description": "Guided tour of Gaudí's masterpiece, the iconic Sagrada Familia basilica with its stunning architecture and intricate details.",
                "vigor": "medium",
                "from_date_time": "2025-04-12T10:00:00Z",
                "to_date_time": "2025-04-12T11:30:00Z",
                "location": "Sagrada Familia",
                "start_lat": 41.4036,
                "start_lon": 2.1744,
                "end_lat": 41.4036,
                "end_lon": 2.1744
            },
            {
                "id": 2,
                "activity_id": "act_002",
                "activity_name": "Park Güell visit",
                "type": "sightseeing",
                "description": "Visit Gaudí's whimsical Park Güell with its colorful mosaics, unique architecture, and panoramic views of Barcelona.",
                "vigor": "low",
                "from_date_time": "2025-04-12T14:00:00Z",
                "to_date_time": "2025-04-12T16:00:00Z",
                "location": "Park Güell",
                "start_lat": 41.4145,
                "start_lon": 2.1527,
                "end_lat": 41.4145,
                "end_lon": 2.1527
            }
        ]
    },
    {
        "id": 2,
        "date": "2025-04-13",
        "location": "Barcelona",
        "description": "Day 2 in Barcelona",
        "activities": [
            {
                "id": 3,
                "activity_id": "act_003",
                "activity_name": "Beach day at Barceloneta",
                "type": "relaxing",
                "description": "Relax at Barceloneta Beach, enjoy the Mediterranean sun and sea.",
                "vigor": "low",
                "from_date_time": "2025-04-13T10:00:00Z",
                "to_date_time": "2025-04-13T16:00:00Z",
                "location": "Barceloneta Beach",
                "start_lat": 41.3798,
                "start_lon": 2.1900,
                "end_lat": 41.3798,
                "end_lon": 2.1900
            }
        ]
    }
]

MOCK_TRIP_SUMMARY = "I've created a wonderful 2-day trip to Barcelona! Day 1 includes a guided tour of the iconic Sagrada Familia basilica, one of Gaudí's masterpieces, followed by a visit to Park Güell with its colorful mosaics and panoramic city views. Day 2 is a relaxing beach day at Barceloneta Beach where you can enjoy the Mediterranean sun and sea. This itinerary balances cultural exploration with relaxation, perfect for experiencing Barcelona's unique architecture and beautiful coastline."

@app.get("/trip_brinstorm")
async def trip_brinstorm(
    tripID: str = Query(...),
    userID: str = Query(...),
    query: str = Query(...),
    old_plan: str = Query(...),
    tripSuggestionID: str = Query(...)
):
    """
    Generate or iterate on trip plan.
    If old_plan is empty JSON ({}) or empty, generates initial plan.
    Otherwise, iterates on existing plan.
    """
    # Parse old_plan parameter
    try:
        old_plan_json = json.loads(old_plan)
    except (json.JSONDecodeError, TypeError):
        old_plan_json = {}
    
    # Call the brainstorm_chat function
    try:
        result = brainstorm_chat(query, old_plan_json)
        # Ensure datetime objects are serialized properly
        # FastAPI will handle this, but we can also use json.dumps/loads to ensure proper format
        return result
    except Exception as e:
        # Fallback to mock data if OpenAI call fails
        print(f"Error calling brainstorm_chat: {e}")
        return {
            "days": MOCK_DAYS,
            "trip_summary": MOCK_TRIP_SUMMARY
        }


@app.post("/create_final_plan")
async def create_final_plan_endpoint(request: CreateFinalPlanRequest):
    """
    Create final plan from multiple suggestions and poll results.
    Merges multiple trip suggestions and incorporates poll results to create a unified final itinerary.
    """
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    # Verify trip exists
    trip = await db.trips.find_one({"tripID": request.tripID})
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Verify user is a member of the trip
    if request.userID not in trip.get("members", []) and request.userID != trip.get("ownerID"):
        raise HTTPException(status_code=403, detail="User is not a member of this trip")
    
    # Validate that old_plans is not empty
    if not request.old_plans or len(request.old_plans) == 0:
        raise HTTPException(status_code=400, detail="At least one trip plan is required")
    
    try:
        # Call the create_final_plan function
        result = create_final_plan(request.old_plans, request.poll_results)
        return result
    except Exception as e:
        print(f"Error in create_final_plan_endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create final plan: {str(e)}")

@app.post("/post_trip_suggestion")
async def post_trip_suggestion(suggestion_data: dict):
    """Post a trip suggestion and save to database."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    tripSuggestionID = suggestion_data.get("tripSuggestionID")
    tripID = suggestion_data.get("tripID")
    userID = suggestion_data.get("userID")
    days = suggestion_data.get("days", [])
    
    if not all([tripSuggestionID, tripID, userID]):
        raise HTTPException(status_code=400, detail="Missing required fields: tripSuggestionID, tripID, userID")
    
    # Check if suggestion already exists
    existing = await db.trip_suggestions.find_one({
        "tripSuggestionID": tripSuggestionID
    })
    
    suggestion_doc = {
        "tripSuggestionID": tripSuggestionID,
        "tripID": tripID,
        "userID": userID,
        "days": days,
        "status": "submitted",
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow(),
        "submittedAt": datetime.utcnow()
    }
    
    if existing:
        # Update existing suggestion
        await db.trip_suggestions.update_one(
            {"tripSuggestionID": tripSuggestionID},
            {
                "$set": {
                    "days": days,
                    "status": "submitted",
                    "updatedAt": datetime.utcnow(),
                    "submittedAt": datetime.utcnow()
                }
            }
        )
    else:
        # Insert new suggestion
        await db.trip_suggestions.insert_one(suggestion_doc)
    
    return {
        "message": "Trip suggestion posted successfully",
        "tripSuggestionID": tripSuggestionID
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

