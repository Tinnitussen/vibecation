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
    
    trip_doc = {
        "tripID": trip_id,
        "title": trip_data.title,
        "description": trip_data.description or "",
        "ownerID": userID,
        "members": members,
        "status": "planning",
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }
    
    await db.trips.insert_one(trip_doc)
    
    return {
        "tripID": trip_id,
        "message": "Trip created successfully"
    }

@app.delete("/trips/{tripID}", status_code=204)
async def delete_trip(tripID: str):
    """Delete a trip."""
    result = await db.trips.delete_one({"tripID": tripID})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    return None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

