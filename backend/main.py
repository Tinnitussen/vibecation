"""
FastAPI backend for Vibecation travel planner application.
"""
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from pydantic import field_validator
from typing import List, Optional, Dict
from datetime import datetime
import bcrypt
import json
import hashlib
from motor.motor_asyncio import AsyncIOMotorClient
import os
import secrets
import string
from contextlib import asynccontextmanager
from brainstormchat import brainstorm_chat, create_final_plan

# Database connection
client: Optional[AsyncIOMotorClient] = None
db = None

# WebSocket connection manager for chat
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, trip_id: str):
        await websocket.accept()
        if trip_id not in self.active_connections:
            self.active_connections[trip_id] = []
        self.active_connections[trip_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, trip_id: str):
        if trip_id in self.active_connections:
            self.active_connections[trip_id] = [
                conn for conn in self.active_connections[trip_id] if conn != websocket
            ]
            if not self.active_connections[trip_id]:
                del self.active_connections[trip_id]
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)
    
    async def broadcast(self, message: dict, trip_id: str, exclude_websocket: Optional[WebSocket] = None):
        if trip_id in self.active_connections:
            for connection in self.active_connections[trip_id]:
                if connection != exclude_websocket:
                    try:
                        await connection.send_json(message)
                    except:
                        # Connection closed, remove it
                        self.active_connections[trip_id] = [
                            conn for conn in self.active_connections[trip_id] if conn != connection
                        ]

manager = ConnectionManager()

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
# Allow origins from environment variable or default to localhost
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://frontend:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
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

# Chat Models
class ChatMessage(BaseModel):
    messageID: Optional[str] = None
    tripID: str
    userID: str
    userName: Optional[str] = None
    content: str
    createdAt: Optional[datetime] = None

class ChatMessageResponse(BaseModel):
    messageID: str
    tripID: str
    userID: str
    userName: Optional[str] = None
    content: str
    createdAt: datetime

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

@app.get("/trips/{tripID}/overview")
async def get_trip_overview(tripID: str):
    """Get trip overview with decisions (top activities, locations, cuisines)."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    # Get trip info
    trip = await db.trips.find_one({"tripID": tripID})
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Get all votes for this trip
    votes_collection = db.votes
    all_votes = await votes_collection.find({
        "tripID": tripID
    }).to_list(length=10000)
    
    # Aggregate activity votes
    activity_votes = {}
    for vote in all_votes:
        if vote.get("voteType") == "activity":
            activity_id = vote.get("optionID")
            if activity_id not in activity_votes:
                activity_votes[activity_id] = {"upvotes": 0, "downvotes": 0}
            if vote.get("vote", True):
                activity_votes[activity_id]["upvotes"] += 1
            else:
                activity_votes[activity_id]["downvotes"] += 1
    
    # Aggregate location votes
    location_votes = {}
    for vote in all_votes:
        if vote.get("voteType") == "location":
            location_id = vote.get("optionID")
            if location_id not in location_votes:
                location_votes[location_id] = {"upvotes": 0, "downvotes": 0}
            if vote.get("vote", True):
                location_votes[location_id]["upvotes"] += 1
            else:
                location_votes[location_id]["downvotes"] += 1
    
    # Aggregate cuisine votes
    cuisine_votes = {}
    for vote in all_votes:
        if vote.get("voteType") == "food_cuisine":
            cuisine_name = vote.get("optionID") or vote.get("voteValue")
            if cuisine_name:
                if cuisine_name not in cuisine_votes:
                    cuisine_votes[cuisine_name] = {"votes": 0}
                if vote.get("vote", True):
                    cuisine_votes[cuisine_name]["votes"] += 1
    
    # Get all submitted suggestions for this trip
    suggestions = await db.trip_suggestions.find({
        "tripID": tripID,
        "status": "submitted"
    }).to_list(length=100)
    
    # Extract all activities from suggestions
    all_activities_dict = {}
    for suggestion in suggestions:
        days = suggestion.get("days", [])
        for day in days:
            activities_list = day.get("activities", [])
            for activity in activities_list:
                activity_id = activity.get("activity_id")
                if not activity_id:
                    activity_key = f"{activity.get('activity_name', '')}_{activity.get('type', '')}_{activity.get('location', '')}"
                    activity_id = hashlib.md5(activity_key.encode()).hexdigest()[:12]
                    activity_id = f"act_{activity_id}"
                
                if activity_id not in all_activities_dict:
                    all_activities_dict[activity_id] = {
                        "activity_id": activity_id,
                        "activity_name": activity.get("activity_name", "Unnamed Activity"),
                        "type": activity.get("type", "sightseeing"),
                        "description": activity.get("description", activity.get("activity_description", "")),
                        "vigor": activity.get("vigor", "medium"),
                        "location": activity.get("location", activity.get("start_location", "")),
                    }
    
    # Enrich with vote data
    activities = []
    for activity_id, activity in all_activities_dict.items():
        counts = activity_votes.get(activity_id, {"upvotes": 0, "downvotes": 0})
        net_score = counts["upvotes"] - counts["downvotes"]
        
        activity_with_votes = {
            **activity,
            "upvotes": counts["upvotes"],
            "downvotes": counts["downvotes"],
            "net_score": net_score
        }
        activities.append(activity_with_votes)
    
    # Fallback to mock data if no suggestions
    if not activities:
        for mock_activity in MOCK_ACTIVITIES:
            activity_id = mock_activity.get("activity_id")
            counts = activity_votes.get(activity_id, {"upvotes": 0, "downvotes": 0})
            net_score = counts["upvotes"] - counts["downvotes"]
            
            activity = {
                **mock_activity,
                "upvotes": counts["upvotes"],
                "downvotes": counts["downvotes"],
                "net_score": net_score
            }
            activities.append(activity)
    
    # Extract all unique locations from suggestions
    all_locations_dict = {}
    for suggestion in suggestions:
        days = suggestion.get("days", [])
        for day in days:
            day_location = day.get("location")
            if day_location:
                location_id = f"loc_{hashlib.md5(day_location.encode()).hexdigest()[:12]}"
                if location_id not in all_locations_dict:
                    all_locations_dict[location_id] = {
                        "location_id": location_id,
                        "name": day_location,
                        "description": day.get("description", ""),
                        "lat": None,
                        "lon": None
                    }
            
            activities_list = day.get("activities", [])
            for activity in activities_list:
                location_name = activity.get("location") or activity.get("start_location")
                if location_name:
                    location_id = f"loc_{hashlib.md5(location_name.encode()).hexdigest()[:12]}"
                    if location_id not in all_locations_dict:
                        all_locations_dict[location_id] = {
                            "location_id": location_id,
                            "name": location_name,
                            "description": "",
                            "lat": activity.get("start_lat"),
                            "lon": activity.get("start_lon")
                        }
    
    # Enrich with vote data
    locations = []
    for location_id, location in all_locations_dict.items():
        counts = location_votes.get(location_id, {"upvotes": 0, "downvotes": 0})
        net_score = counts["upvotes"] - counts["downvotes"]
        
        location_with_votes = {
            **location,
            "upvotes": counts["upvotes"],
            "downvotes": counts["downvotes"],
            "net_score": net_score
        }
        locations.append(location_with_votes)
    
    # Fallback to mock data if no suggestions
    if not locations:
        for mock_location in MOCK_LOCATIONS:
            location_id = mock_location.get("location_id")
            counts = location_votes.get(location_id, {"upvotes": 0, "downvotes": 0})
            net_score = counts["upvotes"] - counts["downvotes"]
            
            location = {
                **mock_location,
                "upvotes": counts["upvotes"],
                "downvotes": counts["downvotes"],
                "net_score": net_score
            }
            locations.append(location)
    
    # Get cuisines from mock data and enrich with votes
    cuisines = []
    for mock_cuisine in MOCK_CUISINES:
        cuisine_name = mock_cuisine.get("name")
        votes = cuisine_votes.get(cuisine_name, {"votes": 0})["votes"]
        
        cuisine = {
            **mock_cuisine,
            "votes": votes
        }
        cuisines.append(cuisine)
    
    # Calculate top items (sorted by net score, descending)
    top_activities = sorted(
        [a for a in activities if a["net_score"] > 0],
        key=lambda x: x["net_score"],
        reverse=True
    )[:10]  # Top 10
    
    top_locations = sorted(
        [l for l in locations if l["net_score"] > 0],
        key=lambda x: x["net_score"],
        reverse=True
    )[:10]  # Top 10
    
    top_cuisines = sorted(
        [c for c in cuisines if c["votes"] > 0],
        key=lambda x: x["votes"],
        reverse=True
    )[:10]  # Top 10
    
    # Calculate total votes
    total_votes = len(all_votes)
    
    return {
        "trip": {
            "title": trip.get("title", ""),
            "description": trip.get("description"),
            "members": trip.get("members", []),
            "status": trip.get("status", "planning")
        },
        "decisions": {
            "top_activities": top_activities,
            "top_locations": top_locations,
            "top_cuisines": top_cuisines,
            "total_votes": total_votes
        }
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
    """Get trip details itinerary generated from voting results."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    # Check if trip exists
    trip = await db.trips.find_one({"tripID": tripID})
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Try to get trip details from database (cached result)
    trip_details = await db.trip_details.find_one({"tripID": tripID})
    
    if trip_details and "days" in trip_details:
        # Remove MongoDB _id field
        trip_details.pop("_id", None)
        return TripDetailsItinerary(**trip_details)
    
    # Generate trip details from voting results
    # Get all submitted suggestions
    suggestions = await db.trip_suggestions.find({
        "tripID": tripID,
        "status": "submitted"
    }).to_list(length=100)
    
    if not suggestions:
        # No suggestions yet - return empty itinerary
        return TripDetailsItinerary(
            tripID=tripID,
            days=[],
            trip_summary="No suggestions have been submitted yet. Complete the brainstorming phase first."
        )
    
    # Get all votes for this trip
    votes_collection = db.votes
    all_votes = await votes_collection.find({
        "tripID": tripID
    }).to_list(length=10000)
    
    # Aggregate activity votes
    activity_votes = {}
    for vote in all_votes:
        if vote.get("voteType") == "activity":
            activity_id = vote.get("optionID")
            if activity_id not in activity_votes:
                activity_votes[activity_id] = {"upvotes": 0, "downvotes": 0}
            if vote.get("vote", True):
                activity_votes[activity_id]["upvotes"] += 1
            else:
                activity_votes[activity_id]["downvotes"] += 1
    
    # Aggregate location votes
    location_votes = {}
    for vote in all_votes:
        if vote.get("voteType") == "location":
            location_id = vote.get("optionID")
            if location_id not in location_votes:
                location_votes[location_id] = {"upvotes": 0, "downvotes": 0}
            if vote.get("vote", True):
                location_votes[location_id]["upvotes"] += 1
            else:
                location_votes[location_id]["downvotes"] += 1
    
    # Aggregate cuisine votes
    cuisine_votes = {}
    for vote in all_votes:
        if vote.get("voteType") == "food_cuisine":
            cuisine_name = vote.get("optionID") or vote.get("voteValue")
            if cuisine_name:
                if cuisine_name not in cuisine_votes:
                    cuisine_votes[cuisine_name] = {"votes": 0}
                if vote.get("vote", True):
                    cuisine_votes[cuisine_name]["votes"] += 1
    
    # Extract all activities from suggestions
    all_activities_dict = {}
    for suggestion in suggestions:
        days = suggestion.get("days", [])
        for day in days:
            activities_list = day.get("activities", [])
            for activity in activities_list:
                activity_id = activity.get("activity_id")
                if not activity_id:
                    activity_key = f"{activity.get('activity_name', '')}_{activity.get('type', '')}_{activity.get('location', '')}"
                    activity_id = hashlib.md5(activity_key.encode()).hexdigest()[:12]
                    activity_id = f"act_{activity_id}"
                
                if activity_id not in all_activities_dict:
                    all_activities_dict[activity_id] = {
                        "activity_id": activity_id,
                        "activity_name": activity.get("activity_name", "Unnamed Activity"),
                        "type": activity.get("type", "sightseeing"),
                        "description": activity.get("description", activity.get("activity_description", "")),
                        "vigor": activity.get("vigor", "medium"),
                        "location": activity.get("location", activity.get("start_location", "")),
                        "start_lat": activity.get("start_lat"),
                        "start_lon": activity.get("start_lon"),
                    }
    
    # Enrich activities with vote data
    activities = []
    for activity_id, activity in all_activities_dict.items():
        counts = activity_votes.get(activity_id, {"upvotes": 0, "downvotes": 0})
        net_score = counts["upvotes"] - counts["downvotes"]
        
        activity_with_votes = {
            **activity,
            "upvotes": counts["upvotes"],
            "downvotes": counts["downvotes"],
            "net_score": net_score
        }
        activities.append(activity_with_votes)
    
    # Extract all unique locations from suggestions
    all_locations_dict = {}
    for suggestion in suggestions:
        days = suggestion.get("days", [])
        for day in days:
            day_location = day.get("location")
            if day_location:
                location_id = f"loc_{hashlib.md5(day_location.encode()).hexdigest()[:12]}"
                if location_id not in all_locations_dict:
                    all_locations_dict[location_id] = {
                        "location_id": location_id,
                        "name": day_location,
                        "description": day.get("description", ""),
                        "lat": None,
                        "lon": None
                    }
            
            activities_list = day.get("activities", [])
            for activity in activities_list:
                location_name = activity.get("location") or activity.get("start_location")
                if location_name:
                    location_id = f"loc_{hashlib.md5(location_name.encode()).hexdigest()[:12]}"
                    if location_id not in all_locations_dict:
                        all_locations_dict[location_id] = {
                            "location_id": location_id,
                            "name": location_name,
                            "description": "",
                            "lat": activity.get("start_lat"),
                            "lon": activity.get("start_lon")
                        }
    
    # Enrich locations with vote data
    locations = []
    for location_id, location in all_locations_dict.items():
        counts = location_votes.get(location_id, {"upvotes": 0, "downvotes": 0})
        net_score = counts["upvotes"] - counts["downvotes"]
        
        location_with_votes = {
            **location,
            "upvotes": counts["upvotes"],
            "downvotes": counts["downvotes"],
            "net_score": net_score
        }
        locations.append(location_with_votes)
    
    # Get cuisines from votes
    cuisines = []
    for cuisine_name, vote_data in cuisine_votes.items():
        cuisines.append({
            "name": cuisine_name,
            "votes": vote_data["votes"]
        })
    
    # Prepare poll results for create_final_plan
    poll_results = {
        "activities": activities,
        "locations": locations,
        "cuisines": cuisines
    }
    
    # Convert suggestions to the format expected by create_final_plan
    old_plans = []
    for suggestion in suggestions:
        days = suggestion.get("days", [])
        if days:
            old_plans.append(days)
    
    # Generate final plan using create_final_plan
    try:
        final_plan = create_final_plan(old_plans, poll_results)
        
        # Prepare response
        result = {
            "tripID": tripID,
            "days": final_plan.get("days", []),
            "trip_summary": final_plan.get("trip_summary", "Trip itinerary generated from voting results.")
        }
        
        # Save to database for caching
        await db.trip_details.update_one(
            {"tripID": tripID},
            {"$set": result},
            upsert=True
        )
        
        return TripDetailsItinerary(**result)
    except Exception as e:
        # If generation fails, return empty itinerary with error message
        print(f"Error generating trip details: {e}")
        return TripDetailsItinerary(
            tripID=tripID,
            days=[],
            trip_summary=f"Unable to generate trip details. Error: {str(e)}"
        )

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
    Extracts activities from submitted brainstorm suggestions.
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
    
    # Get all submitted suggestions for this trip
    suggestions = await db.trip_suggestions.find({
        "tripID": tripID,
        "status": "submitted"
    }).to_list(length=100)
    
    # Extract all activities from suggestions
    all_activities = {}
    
    for suggestion in suggestions:
        days = suggestion.get("days", [])
        for day in days:
            activities = day.get("activities", [])
            for activity in activities:
                # Use activity_id if available, otherwise create a hash-based ID
                activity_id = activity.get("activity_id")
                if not activity_id:
                    # Create a unique ID based on activity content
                    activity_key = f"{activity.get('activity_name', '')}_{activity.get('type', '')}_{activity.get('location', '')}"
                    activity_id = hashlib.md5(activity_key.encode()).hexdigest()[:12]
                    activity_id = f"act_{activity_id}"
                
                # Only add if we haven't seen this activity_id before
                if activity_id not in all_activities:
                    # Normalize activity data to match expected format
                    normalized_activity = {
                        "activity_id": activity_id,
                        "activity_name": activity.get("activity_name", "Unnamed Activity"),
                        "type": activity.get("type", "sightseeing"),
                        "description": activity.get("description", activity.get("activity_description", "")),
                        "vigor": activity.get("vigor", "medium"),
                        "location": activity.get("location", activity.get("start_location", "")),
                        "from_date_time": activity.get("from_date_time"),
                        "to_date_time": activity.get("to_date_time"),
                        "start_location": activity.get("start_location", activity.get("location", "")),
                        "start_lat": activity.get("start_lat"),
                        "start_lon": activity.get("start_lon"),
                        "end_location": activity.get("end_location", activity.get("location", "")),
                        "end_lat": activity.get("end_lat"),
                        "end_lon": activity.get("end_lon"),
                    }
                    all_activities[activity_id] = normalized_activity
    
    # Convert to list and enrich with vote data
    activities = []
    for activity_id, activity in all_activities.items():
        counts = vote_counts.get(activity_id, {"upvotes": 0, "downvotes": 0})
        
        activity_with_votes = {
            **activity,
            "upvotes": counts["upvotes"],
            "downvotes": counts["downvotes"],
            "user_vote": user_votes.get(activity_id, None)
        }
        activities.append(activity_with_votes)
    
    # If no activities from suggestions, fall back to mock data
    if not activities:
        for mock_activity in MOCK_ACTIVITIES:
            activity_id = mock_activity["activity_id"]
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
async def get_location_poll(tripID: str = Query(...), userID: str = Query(None)):
    """
    Get location poll with real vote counts from database.
    Extracts locations from submitted brainstorm suggestions.
    If userID is provided, also includes the user's vote for each location.
    """
    if db is None:
        # Fallback to mock data if database not connected
        return {"locations": MOCK_LOCATIONS}
    
    votes_collection = db.votes
    
    # Get all votes for locations in this trip
    location_votes = await votes_collection.find({
        "tripID": tripID,
        "voteType": "location"
    }).to_list(length=1000)
    
    # Aggregate votes by locationID
    vote_counts = {}
    user_votes = {}
    
    for vote in location_votes:
        location_id = vote["optionID"]
        
        # Count upvotes and downvotes
        if location_id not in vote_counts:
            vote_counts[location_id] = {"upvotes": 0, "downvotes": 0}
        
        if vote["vote"]:
            vote_counts[location_id]["upvotes"] += 1
        else:
            vote_counts[location_id]["downvotes"] += 1
        
        # Track user's vote if userID provided
        if userID and vote["userID"] == userID:
            user_votes[location_id] = vote["vote"]
    
    # Get all submitted suggestions for this trip
    suggestions = await db.trip_suggestions.find({
        "tripID": tripID,
        "status": "submitted"
    }).to_list(length=100)
    
    # Extract all unique locations from suggestions
    all_locations = {}
    
    for suggestion in suggestions:
        days = suggestion.get("days", [])
        for day in days:
            # Get day location
            day_location = day.get("location")
            if day_location:
                location_id = f"loc_{hashlib.md5(day_location.encode()).hexdigest()[:12]}"
                if location_id not in all_locations:
                    all_locations[location_id] = {
                        "location_id": location_id,
                        "name": day_location,
                        "type": "city",  # Default type
                        "lat": None,
                        "lon": None
                    }
            
            # Get locations from activities
            activities = day.get("activities", [])
            for activity in activities:
                location_name = activity.get("location") or activity.get("start_location")
                if location_name:
                    location_id = f"loc_{hashlib.md5(location_name.encode()).hexdigest()[:12]}"
                    if location_id not in all_locations:
                        all_locations[location_id] = {
                            "location_id": location_id,
                            "name": location_name,
                            "type": "city",  # Default type
                            "lat": activity.get("start_lat"),
                            "lon": activity.get("start_lon")
                        }
    
    # Convert to list and enrich with vote data
    locations = []
    for location_id, location in all_locations.items():
        counts = vote_counts.get(location_id, {"upvotes": 0, "downvotes": 0})
        
        location_with_votes = {
            **location,
            "upvotes": counts["upvotes"],
            "downvotes": counts["downvotes"],
            "user_vote": user_votes.get(location_id, None)
        }
        locations.append(location_with_votes)
    
    # If no locations from suggestions, fall back to mock data
    if not locations:
        for mock_location in MOCK_LOCATIONS:
            location_id = mock_location["location_id"]
            counts = vote_counts.get(location_id, {"upvotes": 0, "downvotes": 0})
            location = {
                **mock_location,
                "upvotes": counts["upvotes"],
                "downvotes": counts["downvotes"],
                "user_vote": user_votes.get(location_id, None)
            }
            locations.append(location)
    
    return {"locations": locations}

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

@app.post("/polls/finish_voting")
async def finish_voting(finish_data: dict):
    """Mark a user as finished voting for a trip."""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    tripID = finish_data.get("tripID")
    userID = finish_data.get("userID")
    
    if not all([tripID, userID]):
        raise HTTPException(status_code=400, detail="Missing required fields: tripID, userID")
    
    # Use polling_completion collection to track which users have finished
    completion_collection = db.polling_completion
    
    # Check if already marked as complete
    existing = await completion_collection.find_one({
        "tripID": tripID,
        "userID": userID
    })
    
    if existing:
        return {
            "message": "User already marked as finished voting",
            "alreadyCompleted": True
        }
    
    # Mark user as finished
    completion_doc = {
        "tripID": tripID,
        "userID": userID,
        "completedAt": datetime.utcnow()
    }
    
    await completion_collection.insert_one(completion_doc)
    
    return {
        "message": "Voting marked as complete",
        "alreadyCompleted": False
    }

@app.get("/check_polling_completion")
async def check_polling_completion(tripID: str = Query(...)):
    """Check if all trip members have finished voting."""
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
    
    # Get all users who have finished voting
    completion_collection = db.polling_completion
    completed_users = await completion_collection.find({
        "tripID": tripID
    }).to_list(length=100)
    
    completed_user_ids = [c["userID"] for c in completed_users]
    completed_count = len(set(completed_user_ids))
    
    return {
        "allCompleted": completed_count >= len(members),
        "totalMembers": len(members),
        "completedMembers": completed_count,
        "completedUserIDs": list(set(completed_user_ids)),
        "allMemberIDs": members
    }

@app.post("/polls/finalize")
async def finalize_polls(finalize_data: dict):
    """Finalize polling results and persist to polls collection when all users have finished voting."""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    tripID = finalize_data.get("tripID")
    
    if not tripID:
        raise HTTPException(status_code=400, detail="Missing required field: tripID")
    
    # Check if all users have finished voting
    completion_status = await check_polling_completion(tripID)
    if not completion_status["allCompleted"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Not all users have finished voting. {completion_status['completedMembers']}/{completion_status['totalMembers']} completed"
        )
    
    # Check if polls already finalized
    polls_collection = db.polls
    existing_polls = await polls_collection.find({
        "tripID": tripID,
        "status": "completed"
    }).to_list(length=10)
    
    if existing_polls:
        return {
            "message": "Polls already finalized",
            "alreadyFinalized": True,
            "pollIDs": [p["pollID"] for p in existing_polls]
        }
    
    # Get all votes for this trip
    votes_collection = db.votes
    all_votes = await votes_collection.find({
        "tripID": tripID
    }).to_list(length=10000)
    
    # Aggregate votes by poll type
    poll_types = ["activity", "location", "food_cuisine"]
    created_polls = []
    
    for poll_type in poll_types:
        # Filter votes for this poll type
        type_votes = [v for v in all_votes if v.get("voteType") == poll_type]
        
        if not type_votes:
            continue
        
        # Aggregate votes by optionID
        option_votes = {}
        for vote in type_votes:
            option_id = vote.get("optionID")
            if not option_id:
                continue
            
            if option_id not in option_votes:
                option_votes[option_id] = {
                    "upvotes": 0,
                    "downvotes": 0,
                    "optionID": option_id
                }
            
            if vote.get("vote") is True:
                option_votes[option_id]["upvotes"] += 1
            elif vote.get("vote") is False:
                option_votes[option_id]["downvotes"] += 1
        
        # Create poll options with aggregated data
        options = []
        for option_id, counts in option_votes.items():
            net_score = counts["upvotes"] - counts["downvotes"]
            options.append({
                "optionID": option_id,
                "upvotes": counts["upvotes"],
                "downvotes": counts["downvotes"],
                "netScore": net_score
            })
        
        # Generate pollID
        poll_count = await polls_collection.count_documents({})
        pollID = f"poll_{str(poll_count + 1).zfill(3)}"
        
        # Create poll document
        poll_doc = {
            "pollID": pollID,
            "tripID": tripID,
            "pollType": poll_type,
            "status": "completed",
            "options": options,
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow(),
            "closedAt": datetime.utcnow(),
            "totalVotes": len(type_votes)
        }
        
        await polls_collection.insert_one(poll_doc)
        created_polls.append(pollID)
    
    return {
        "message": "Polls finalized successfully",
        "alreadyFinalized": False,
        "pollIDs": created_polls,
        "pollsCreated": len(created_polls)
    }

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

# Chat Endpoints
@app.websocket("/ws/trips/{tripID}/chat")
async def websocket_chat_endpoint(websocket: WebSocket, tripID: str):
    """WebSocket endpoint for real-time trip chat."""
    await manager.connect(websocket, tripID)
    
    # Verify trip exists
    trip = await db.trips.find_one({"tripID": tripID})
    if not trip:
        await manager.send_personal_message({
            "type": "error",
            "message": "Trip not found"
        }, websocket)
        await websocket.close()
        return
    
    # Store verified userID for this connection
    verified_userID = None
    
    # Helper function to check if user is a member
    def is_trip_member(user_id, trip_doc):
        """Check if user is owner or in members list."""
        trip_owner = trip_doc.get("ownerID")
        trip_members = trip_doc.get("members", [])
        # Include owner in members check
        all_members = list(set([trip_owner] + trip_members)) if trip_owner else trip_members
        return user_id in all_members
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # Validate message data
            message_userID = data.get("userID")
            content = data.get("content", "").strip()
            
            # If this is the first message, verify membership
            if verified_userID is None:
                if not message_userID:
                    await manager.send_personal_message({
                        "type": "error",
                        "message": "Missing userID"
                    }, websocket)
                    continue
                
                # Re-fetch trip to get latest members list (in case user just joined)
                trip = await db.trips.find_one({"tripID": tripID})
                if not trip:
                    await manager.send_personal_message({
                        "type": "error",
                        "message": "Trip not found"
                    }, websocket)
                    continue
                
                # Verify user is a member of the trip
                if not is_trip_member(message_userID, trip):
                    await manager.send_personal_message({
                        "type": "error",
                        "message": "You are not a member of this trip"
                    }, websocket)
                    continue
                
                verified_userID = message_userID
            
            # Use verified userID for subsequent messages
            userID = verified_userID
            
            if not content:
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Message content cannot be empty"
                }, websocket)
                continue
            
            # Get user info for display name
            user = await db.users.find_one({"userID": userID})
            userName = user.get("name", user.get("username", "Unknown")) if user else "Unknown"
            
            # Generate message ID
            messageID = await get_next_id("chat_messages")
            
            # Create message document
            message_doc = {
                "messageID": messageID,
                "tripID": tripID,
                "userID": userID,
                "userName": userName,
                "content": content,
                "createdAt": datetime.utcnow()
            }
            
            # Save to database
            await db.chat_messages.insert_one(message_doc)
            
            # Prepare message for broadcast
            message_response = {
                "type": "message",
                "messageID": messageID,
                "tripID": tripID,
                "userID": userID,
                "userName": userName,
                "content": content,
                "createdAt": message_doc["createdAt"].isoformat()
            }
            
            # Broadcast to all connected clients in this trip (including sender)
            await manager.broadcast(message_response, tripID, exclude_websocket=None)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, tripID)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, tripID)

@app.get("/trips/{tripID}/chat/messages")
async def get_chat_messages(tripID: str, userID: str = Query(...), limit: int = Query(50, ge=1, le=200)):
    """Get chat messages for a trip."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    # Verify trip exists and user is a member
    trip = await db.trips.find_one({"tripID": tripID})
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Check if user is owner or in members list
    trip_owner = trip.get("ownerID")
    trip_members = trip.get("members", [])
    # Include owner in members check
    all_members = list(set([trip_owner] + trip_members)) if trip_owner else trip_members
    
    if userID not in all_members:
        raise HTTPException(status_code=403, detail="You are not a member of this trip")
    
    # Get messages from database
    messages = await db.chat_messages.find(
        {"tripID": tripID}
    ).sort("createdAt", -1).limit(limit).to_list(length=limit)
    
    # Convert to response format
    message_list = []
    for msg in reversed(messages):  # Reverse to get chronological order
        message_list.append({
            "messageID": msg.get("messageID"),
            "tripID": msg.get("tripID"),
            "userID": msg.get("userID"),
            "userName": msg.get("userName", "Unknown"),
            "content": msg.get("content"),
            "createdAt": msg.get("createdAt").isoformat() if msg.get("createdAt") else None
        })
    
    return {"messages": message_list}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

