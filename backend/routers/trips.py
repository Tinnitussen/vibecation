"""
API routes for trip management.
"""

from fastapi import APIRouter, HTTPException
from typing import List
from backend.models import Trip
from backend.database import get_database
from bson import ObjectId

router = APIRouter()


@router.get("/", response_model=List[Trip])
async def get_trips():
    """Get all trips."""
    db = get_database()
    if not db:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    trips_collection = db.trips
    trips = await trips_collection.find().to_list(length=100)
    
    # Convert ObjectId to string and remove _id field
    for trip in trips:
        trip["trip_id"] = str(trip.pop("_id", trip.get("trip_id")))
    
    return trips


@router.get("/{trip_id}", response_model=Trip)
async def get_trip(trip_id: str):
    """Get a specific trip by ID."""
    db = get_database()
    if not db:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    trips_collection = db.trips
    
    # Try to find by trip_id first, then by _id
    trip = await trips_collection.find_one({"trip_id": trip_id})
    if not trip:
        try:
            trip = await trips_collection.find_one({"_id": ObjectId(trip_id)})
        except:
            pass
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    trip["trip_id"] = str(trip.pop("_id", trip.get("trip_id")))
    return trip


@router.post("/", response_model=Trip, status_code=201)
async def create_trip(trip: Trip):
    """Create a new trip."""
    db = get_database()
    if not db:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    trips_collection = db.trips
    
    # Check if trip_id already exists
    existing = await trips_collection.find_one({"trip_id": trip.trip_id})
    if existing:
        raise HTTPException(status_code=400, detail="Trip with this ID already exists")
    
    trip_dict = trip.model_dump()
    result = await trips_collection.insert_one(trip_dict)
    
    # Return the created trip
    created_trip = await trips_collection.find_one({"_id": result.inserted_id})
    created_trip["trip_id"] = str(created_trip.pop("_id", created_trip.get("trip_id")))
    return created_trip


@router.put("/{trip_id}", response_model=Trip)
async def update_trip(trip_id: str, trip: Trip):
    """Update an existing trip."""
    db = get_database()
    if not db:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    trips_collection = db.trips
    
    # Try to find by trip_id first, then by _id
    existing = await trips_collection.find_one({"trip_id": trip_id})
    if not existing:
        try:
            existing = await trips_collection.find_one({"_id": ObjectId(trip_id)})
        except:
            pass
    
    if not existing:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    trip_dict = trip.model_dump()
    trip_dict["_id"] = existing["_id"]
    
    await trips_collection.replace_one({"_id": existing["_id"]}, trip_dict)
    
    updated_trip = await trips_collection.find_one({"_id": existing["_id"]})
    updated_trip["trip_id"] = str(updated_trip.pop("_id", updated_trip.get("trip_id")))
    return updated_trip


@router.delete("/{trip_id}", status_code=204)
async def delete_trip(trip_id: str):
    """Delete a trip."""
    db = get_database()
    if not db:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    trips_collection = db.trips
    
    # Try to find by trip_id first, then by _id
    existing = await trips_collection.find_one({"trip_id": trip_id})
    if not existing:
        try:
            existing = await trips_collection.find_one({"_id": ObjectId(trip_id)})
        except:
            pass
    
    if not existing:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    await trips_collection.delete_one({"_id": existing["_id"]})
    return None

