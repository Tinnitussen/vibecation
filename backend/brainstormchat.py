
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import List, Optional
from openai import AzureOpenAI
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class ActivityType(str, Enum):
    """Enumeration of activity types."""
    ATTRACTION = "attraction"
    TRAVEL = "travel"
    FOOD = "food"
    ENTERTAINMENT = "entertainment"
    ACCOMMODATION = "accommodation"


class Activity(BaseModel):
    """
    Model representing a single activity in a trip itinerary.
    Activities can be nested to represent sub-activities.
    """
    activity_id: str = Field(..., description="Unique identifier for the activity")
    activity_name: str = Field(..., description="Name of the activity")
    activity_type: ActivityType = Field(..., description="Type of activity")
    activity_description: str = Field(..., description="Detailed description of the activity")
    from_date_time: datetime = Field(..., description="Start date and time of the activity")
    start_location: str = Field(..., description="Starting location name")
    start_lat: float = Field(..., description="Starting latitude coordinate")
    start_lon: float = Field(..., description="Starting longitude coordinate")
    to_date_time: datetime = Field(..., description="End date and time of the activity")
    end_location: str = Field(..., description="Ending location name")
    end_lat: float = Field(..., description="Ending latitude coordinate")
    end_lon: float = Field(..., description="Ending longitude coordinate")
    activities: List['Activity'] = Field(default_factory=list, description="List of nested sub-activities")


class Trip(BaseModel):
    """
    Model representing a complete trip itinerary.
    """
    trip_name: str = Field(..., description="Name of the trip")
    trip_id: str = Field(..., description="Unique identifier for the trip")
    activities: List[Activity] = Field(..., description="List of activities in the trip")
    trip_summary: str = Field(..., description="A comprehensive description of the trip and activities")


def brainstorm_chat(query: str, old_plan_json: dict):
    """
    Generate or iterate on trip plan using Azure OpenAI.
    
    Args:
        query: User's trip planning query
        old_plan_json: Dictionary containing old plan data (empty dict {} for initial generation)
    
    Returns:
        Dictionary with trip data from OpenAI response
    """
    # Check if this is initial generation or iteration
    is_initial = not old_plan_json or (isinstance(old_plan_json, dict) and not old_plan_json) or (isinstance(old_plan_json, list) and len(old_plan_json) == 0)
    
    if is_initial:
        # Initial trip generation - just use the query
        prompt = query
    else:
        # Iteration on existing plan - serialize old_plan_json with datetime handling
        # Use default=str to handle datetime objects in JSON serialization
        old_trip_json = json.dumps(old_plan_json, default=str)
        prompt = query + "\n\nOld trip\n\n" + old_trip_json

    # Initialize Azure OpenAI client with credentials from environment variables
    client = AzureOpenAI()
    model = 'gpt-4.1'
    autotuning_res = client.responses.parse(
        model=model,
        input=[
            {
                "role": "system",
                "content": "You are a helpful assistant and a expert trip planner",
            },
            {"role": "user", "content": prompt},
        ],
        text_format=Trip,
    )
    # Use mode='json' to properly serialize datetime objects to ISO format strings
    return autotuning_res.output_parsed.model_dump(mode='json')

if __name__ == "__main__":
    query = "I want to go to the Greece for 10 days"
    old_plan_json = {}
    print(json.dumps(brainstorm_chat(query, old_plan_json), indent=4, default=str))