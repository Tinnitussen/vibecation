"""
API routes for AI-powered trip planning.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime, timedelta
import json
import os
from backend.models import Trip, Activity, ActivityType
from pydantic import BaseModel, Field
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# Initialize OpenAI client (will be None if no API key)
openai_client = None
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    openai_client = OpenAI(api_key=api_key)


class TripPreferences(BaseModel):
    """Model for trip planning preferences."""
    destination: Optional[str] = Field(None, description="Destination or region")
    start_date: Optional[str] = Field(None, description="Trip start date (YYYY-MM-DD)")
    duration_days: Optional[int] = Field(None, description="Number of days for the trip")
    interests: Optional[str] = Field(None, description="Interests and preferences (e.g., 'food, museums, beaches')")
    budget: Optional[str] = Field(None, description="Budget level: budget-friendly, mid, or higher")
    activity_level: Optional[str] = Field(None, description="Activity level: active or relaxing")
    climate: Optional[str] = Field(None, description="Climate preference: hot or cold")
    query: Optional[str] = Field(None, description="Free-form trip description")


def generate_trip_with_llm(preferences: TripPreferences) -> Trip:
    """
    Generate a trip itinerary using LLM based on user preferences.
    Returns a Trip object with structured activities.
    """
    # Build the prompt
    prompt_parts = []
    
    if preferences.query:
        prompt_parts.append(f"User request: {preferences.query}")
    else:
        prompt_parts.append("Create a detailed trip itinerary based on the following preferences:")
        if preferences.destination:
            prompt_parts.append(f"- Destination: {preferences.destination}")
        if preferences.start_date:
            prompt_parts.append(f"- Start date: {preferences.start_date}")
        if preferences.duration_days:
            prompt_parts.append(f"- Duration: {preferences.duration_days} days")
        if preferences.interests:
            prompt_parts.append(f"- Interests: {preferences.interests}")
        if preferences.budget:
            prompt_parts.append(f"- Budget: {preferences.budget}")
        if preferences.activity_level:
            prompt_parts.append(f"- Activity level: {preferences.activity_level}")
        if preferences.climate:
            prompt_parts.append(f"- Climate preference: {preferences.climate}")
    
    prompt = "\n".join(prompt_parts)
    
    # Get the Pydantic schema for Trip
    trip_schema = Trip.model_json_schema()
    
    system_prompt = f"""You are a travel planning assistant. Generate a detailed trip itinerary in JSON format that matches this exact schema:

{json.dumps(trip_schema, indent=2)}

Requirements:
1. Return a single Trip object directly (not wrapped in another object) with trip_name, trip_id, and activities array
2. Each activity must have: activity_id, activity_name, activity_type (one of: attraction, travel, food, entertainment, accommodation), activity_description, from_date_time, to_date_time, start_location, end_location, start_lat, start_lon, end_lat, end_lon
3. Activities can be nested (activities field can contain sub-activities)
4. Use realistic coordinates (latitude/longitude) for locations
5. Use ISO 8601 format for dates (YYYY-MM-DDTHH:MM:SSZ)
6. Create a logical day-by-day itinerary
7. Include travel activities between locations when needed
8. Make the trip_name descriptive and appealing
9. Generate unique activity_id values (e.g., "activity_001", "activity_002")

IMPORTANT: Return the Trip object directly as the root JSON object. The JSON should start with {{"trip_name": ...}} not {{"trip": ...}} or {{"trips": [...]}}.

Return ONLY valid JSON matching the Trip schema. Do not include any markdown formatting or explanations."""

    if openai_client:
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Using cheaper model for MVP
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            
            response_text = response.choices[0].message.content
            trip_data = json.loads(response_text)
            
            # Handle case where LLM returns Trip wrapped in an object
            if 'trip_name' in trip_data and 'trip_id' in trip_data:
                # Direct Trip object
                trip = Trip(**trip_data)
            elif 'trips' in trip_data and len(trip_data['trips']) > 0:
                # Wrapped in trips array
                trip = Trip(**trip_data['trips'][0])
            else:
                # Try to extract trip from any nested structure
                trip = Trip(**trip_data)
            
            return trip
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"LLM generation failed: {str(e)}")
    else:
        # Fallback: Generate a sample trip if no API key
        return generate_sample_trip(preferences)


def generate_sample_trip(preferences: TripPreferences) -> Trip:
    """Generate a sample trip when LLM is not available."""
    destination = preferences.destination or "Barcelona"
    duration = preferences.duration_days or 3
    start_date_str = preferences.start_date or datetime.now().strftime("%Y-%m-%d")
    
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    except:
        start_date = datetime.now()
    
    # Sample coordinates for Barcelona
    barcelona_lat, barcelona_lon = 41.4036, 2.1744
    
    activities = []
    activity_counter = 1
    
    for day in range(duration):
        day_date = start_date + timedelta(days=day)
        
        # Morning activity
        morning_time = day_date.replace(hour=10, minute=0, second=0)
        activities.append(Activity(
            activity_id=f"activity_{day+1}_morning",
            activity_name=f"{destination} Day {day+1} - Morning Exploration",
            activity_type=ActivityType.ATTRACTION,
            activity_description=f"Explore {destination} on day {day+1}",
            from_date_time=morning_time,
            start_location=destination,
            start_lat=barcelona_lat,
            start_lon=barcelona_lon,
            to_date_time=morning_time + timedelta(hours=2),
            end_location=destination,
            end_lat=barcelona_lat,
            end_lon=barcelona_lon,
            activities=[]
        ))
        
        # Afternoon activity
        afternoon_time = day_date.replace(hour=14, minute=0, second=0)
        activities.append(Activity(
            activity_id=f"activity_{day+1}_afternoon",
            activity_name=f"{destination} Day {day+1} - Afternoon Activity",
            activity_type=ActivityType.ENTERTAINMENT,
            activity_description=f"Afternoon activity in {destination}",
            from_date_time=afternoon_time,
            start_location=destination,
            start_lat=barcelona_lat,
            start_lon=barcelona_lon,
            to_date_time=afternoon_time + timedelta(hours=3),
            end_location=destination,
            end_lat=barcelona_lat,
            end_lon=barcelona_lon,
            activities=[]
        ))
    
    trip_name = f"{destination} Adventure" if preferences.destination else "Sample Trip"
    
    return Trip(
        trip_name=trip_name,
        trip_id=f"trip_{int(datetime.now().timestamp())}",
        activities=activities
    )


@router.post("/generate", response_model=Trip)
async def generate_trip(preferences: TripPreferences):
    """
    Generate a trip itinerary based on user preferences.
    Uses LLM to create a structured Trip with activities.
    """
    try:
        trip = generate_trip_with_llm(preferences)
        return trip
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate trip: {str(e)}")

