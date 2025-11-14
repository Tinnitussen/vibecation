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
from motor.motor_asyncio import AsyncIOMotorClient
import os
import secrets
import string
from contextlib import asynccontextmanager

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
    trip = await db.trips.find_one({"tripID": tripID})
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    return TripInfoResponse(
        title=trip.get("title", ""),
        members=trip.get("members", []),
        description=trip.get("description")
    )

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

MOCK_VIGOR_PREFERENCES = [
    {
        "activity_id": "act_001",
        "activity_name": "Sagrada Familia tour",
        "preferences": {
            "low": 1,
            "medium": 3,
            "high": 1
        },
        "user_preference": None
    },
    {
        "activity_id": "act_002",
        "activity_name": "Park Güell visit",
        "preferences": {
            "low": 4,
            "medium": 1,
            "high": 0
        },
        "user_preference": None
    },
    {
        "activity_id": "act_003",
        "activity_name": "Beach day",
        "preferences": {
            "low": 5,
            "medium": 0,
            "high": 0
        },
        "user_preference": None
    },
    {
        "activity_id": "act_004",
        "activity_name": "Tapas tour",
        "preferences": {
            "low": 3,
            "medium": 2,
            "high": 0
        },
        "user_preference": None
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
    """Get all trip suggestions (mock data)."""
    # Return mock suggestions regardless of tripID
    return {
        "suggestions": [s["days"] for s in MOCK_SUGGESTIONS],
        "participants": [s["userID"] for s in MOCK_SUGGESTIONS]
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

@app.get("/polls/get/activity_vigor")
async def get_activity_vigor_poll(tripID: str = Query(...)):
    """Get activity vigor poll (mock data)."""
    # Return mock vigor preferences regardless of tripID
    return {"vigor_preferences": MOCK_VIGOR_PREFERENCES}

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
    
    # Count votes per cuisine
    vote_counts = {}
    user_selected = set()
    
    for vote in cuisine_votes:
        cuisine_name = vote.get("voteValue")  # For cuisine, voteValue stores the cuisine name
        
        if cuisine_name:
            if cuisine_name not in vote_counts:
                vote_counts[cuisine_name] = 0
            vote_counts[cuisine_name] += 1
            
            # Track user's selections if userID provided
            if userID and vote["userID"] == userID:
                user_selected.add(cuisine_name)
    
    # Start with mock cuisines and enrich with real vote data
    cuisines = []
    for mock_cuisine in MOCK_CUISINES:
        cuisine_name = mock_cuisine["name"]
        
        cuisine = {
            **mock_cuisine,
            "votes": vote_counts.get(cuisine_name, 0),
            "selected": cuisine_name in user_selected
        }
        cuisines.append(cuisine)
    
    return {"cuisines": cuisines}


@app.post("/polls/vote/food_cuisine")
async def vote_food_cuisine(vote_data: dict):
    """
    Submit cuisine votes. Replaces all previous cuisine votes for this user.
    """
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    tripID = vote_data.get("tripID")
    userID = vote_data.get("userID")
    selectedCuisines = vote_data.get("selectedCuisines", [])
    
    if not all([tripID, userID]):
        raise HTTPException(status_code=400, detail="Missing required fields: tripID, userID")
    
    votes_collection = db.votes
    
    # Remove all existing cuisine votes for this user in this trip
    await votes_collection.delete_many({
        "tripID": tripID,
        "userID": userID,
        "voteType": "food_cuisine"
    })
    
    # Insert new votes for selected cuisines
    if selectedCuisines:
        vote_docs = []
        for cuisine_name in selectedCuisines:
            vote_doc = {
                "tripID": tripID,
                "userID": userID,
                "optionID": cuisine_name,  # Using cuisine name as optionID
                "voteType": "food_cuisine",
                "vote": True,  # All cuisine selections are positive votes
                "voteValue": cuisine_name,  # Store cuisine name in voteValue
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            }
            vote_docs.append(vote_doc)
        
        if vote_docs:
            await votes_collection.insert_many(vote_docs)
    
    return {
        "message": "Cuisine votes submitted successfully",
        "selectedCuisines": selectedCuisines
    }

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

