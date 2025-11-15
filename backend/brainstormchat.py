
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


def infer_vigor_from_type(activity_type: str) -> str:
    """Infer vigor level from activity type."""
    vigor_map = {
        "attraction": "medium",
        "travel": "low",
        "food": "low",
        "entertainment": "medium",
        "accommodation": "low"
    }
    return vigor_map.get(activity_type.lower(), "medium")


def transform_activity_to_frontend_format(activity: dict) -> dict:
    """Transform an activity from OpenAI format to frontend format."""
    # Handle datetime objects - convert to ISO string if needed
    from_dt = activity.get("from_date_time", "")
    to_dt = activity.get("to_date_time", "")
    
    if isinstance(from_dt, datetime):
        from_dt = from_dt.isoformat()
    if isinstance(to_dt, datetime):
        to_dt = to_dt.isoformat()
    
    return {
        "id": activity.get("activity_id", ""),
        "activity_id": activity.get("activity_id", ""),
        "activity_name": activity.get("activity_name", ""),
        "type": activity.get("activity_type", "").lower() if activity.get("activity_type") else "",
        "description": activity.get("activity_description", ""),
        "from_date_time": from_dt,
        "to_date_time": to_dt,
        "location": activity.get("start_location", ""),
        "vigor": infer_vigor_from_type(activity.get("activity_type", "")),
        "start_lat": activity.get("start_lat", 0.0),
        "start_lon": activity.get("start_lon", 0.0),
        "end_lat": activity.get("end_lat", 0.0),
        "end_lon": activity.get("end_lon", 0.0)
    }


def flatten_activities(activities: list) -> list:
    """Flatten nested activities into a single list."""
    flattened = []
    for activity in activities:
        # Add the main activity
        flattened.append(activity)
        # Add nested activities if they exist
        nested = activity.get("activities", [])
        if nested:
            flattened.extend(flatten_activities(nested))
    return flattened


def transform_trip_to_days(trip_data: dict) -> list:
    """
    Transform Trip object (with flat activities list) into days format expected by frontend.
    
    Args:
        trip_data: Dictionary containing trip data from OpenAI (trip_name, trip_id, activities, trip_summary)
    
    Returns:
        List of day objects, each containing activities grouped by date
    """
    activities = trip_data.get("activities", [])
    if not activities:
        return []
    
    # Flatten nested activities
    flattened_activities = flatten_activities(activities)
    
    # Group activities by date
    days_dict = {}
    
    for activity in flattened_activities:
        # Extract date from from_date_time
        from_dt = activity.get("from_date_time", "")
        
        # Handle different datetime formats
        if isinstance(from_dt, datetime):
            date_str = from_dt.strftime("%Y-%m-%d")
        elif isinstance(from_dt, str):
            # Parse date from ISO format string (e.g., "2024-09-01T14:00:00+03:00" or "2024-09-01 14:00:00+03:00")
            try:
                if 'T' in from_dt:
                    date_str = from_dt.split('T')[0]
                elif ' ' in from_dt:
                    date_str = from_dt.split(' ')[0]
                else:
                    date_str = from_dt[:10] if len(from_dt) >= 10 else ""
            except:
                date_str = from_dt[:10] if len(from_dt) >= 10 else ""
        else:
            date_str = ""
        
        if not date_str:
            continue
        
        # Get location from first activity of the day, or use start_location
        location = activity.get("start_location", "")
        
        # Initialize day if not exists
        if date_str not in days_dict:
            days_dict[date_str] = {
                "date": date_str,
                "location": location,
                "activities": []
            }
        
        # Transform and add activity
        transformed_activity = transform_activity_to_frontend_format(activity)
        days_dict[date_str]["activities"].append(transformed_activity)
    
    # Convert to list and add day IDs
    days_list = []
    for idx, (date_str, day_data) in enumerate(sorted(days_dict.items()), 1):
        days_list.append({
            "id": idx,
            "date": day_data["date"],
            "location": day_data["location"],
            "description": f"Day {idx} in {day_data['location']}",
            "activities": day_data["activities"]
        })
    
    return days_list


def brainstorm_chat(query: str, old_plan_json: dict):
    """
    Generate or iterate on trip plan using Azure OpenAI.
    
    Args:
        query: User's trip planning query
        old_plan_json: Dictionary containing old plan data (empty dict {} for initial generation)
    
    Returns:
        Dictionary with 'days' (list of day objects) and 'trip_summary' (string)
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
    trip_data = autotuning_res.output_parsed.model_dump(mode='json')
    
    # Transform trip data to days format
    days = transform_trip_to_days(trip_data)
    
    return {
        "days": days,
        "trip_summary": trip_data.get("trip_summary", "")
    }

def create_final_plan(old_plans: List[List[dict]], poll_results: dict):
    """
    Create a final trip plan by merging multiple trip suggestions and incorporating poll results.
    
    Args:
        old_plans: List of trip plan arrays (each plan is an array of VibecationDay objects)
        poll_results: Dictionary containing poll results with keys:
            - activities: List of Activity objects with vote counts
            - locations: List of Location objects with vote counts
            - cuisines: List of cuisine strings or objects
    
    Returns:
        Dictionary with 'days' (list of day objects) and 'trip_summary' (string)
    """
    # Build prompt that includes all plans and poll results
    prompt_parts = []
    
    # Add information about multiple plans
    prompt_parts.append("I have multiple trip suggestions from different users. Please create a final unified trip plan that:")
    prompt_parts.append("1. Merges the best elements from all suggestions")
    prompt_parts.append("2. Incorporates the poll results (activities, locations, and cuisines that received the most votes)")
    prompt_parts.append("3. Creates a cohesive, well-structured itinerary")
    prompt_parts.append("\n")
    
    # Add all the plans
    prompt_parts.append("Here are the trip suggestions:")
    for idx, plan in enumerate(old_plans, 1):
        prompt_parts.append(f"\n--- Suggestion {idx} ---")
        plan_json = json.dumps(plan, default=str)
        prompt_parts.append(plan_json)
    
    # Add poll results
    prompt_parts.append("\n\n--- Poll Results ---")
    
    # Add activities with vote counts
    if poll_results.get("activities"):
        prompt_parts.append("\nPopular Activities (based on votes):")
        for activity in poll_results["activities"]:
            upvotes = activity.get("upvotes", 0)
            downvotes = activity.get("downvotes", 0)
            net_score = upvotes - downvotes
            activity_name = activity.get("activity_name", activity.get("name", ""))
            activity_type = activity.get("type", "")
            activity_desc = activity.get("description", "")
            prompt_parts.append(f"- {activity_name} ({activity_type}): {activity_desc} [Votes: +{upvotes}/-{downvotes} (net: {net_score})]")
    
    # Add locations with vote counts
    if poll_results.get("locations"):
        prompt_parts.append("\nPopular Locations (based on votes):")
        for location in poll_results["locations"]:
            upvotes = location.get("upvotes", 0)
            downvotes = location.get("downvotes", 0)
            net_score = upvotes - downvotes
            location_name = location.get("name", "")
            location_type = location.get("type", "")
            prompt_parts.append(f"- {location_name} ({location_type}) [Votes: +{upvotes}/-{downvotes} (net: {net_score})]")
    
    # Add cuisines
    if poll_results.get("cuisines"):
        prompt_parts.append("\nPreferred Cuisines (based on votes):")
        for cuisine in poll_results["cuisines"]:
            if isinstance(cuisine, dict):
                cuisine_name = cuisine.get("name", "")
                votes = cuisine.get("votes", cuisine.get("upvotes", 0))
                prompt_parts.append(f"- {cuisine_name} [Votes: {votes}]")
            else:
                prompt_parts.append(f"- {cuisine}")
    
    prompt_parts.append("\n\nPlease create a final unified trip plan that incorporates the most popular elements from the polls while maintaining a logical flow and structure.")
    
    # Combine all prompt parts
    prompt = "\n".join(prompt_parts)
    
    # Initialize Azure OpenAI client
    client = AzureOpenAI()
    model = 'gpt-4.1'
    
    try:
        autotuning_res = client.responses.parse(
            model=model,
            input=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant and an expert trip planner. Your task is to merge multiple trip suggestions into one cohesive final plan, prioritizing activities, locations, and cuisines that received the most votes in polls.",
                },
                {"role": "user", "content": prompt},
            ],
            text_format=Trip,
        )
        # Use mode='json' to properly serialize datetime objects to ISO format strings
        trip_data = autotuning_res.output_parsed.model_dump(mode='json')
        
        # Transform trip data to days format
        days = transform_trip_to_days(trip_data)
        
        return {
            "days": days,
            "trip_summary": trip_data.get("trip_summary", "")
        }
    except Exception as e:
        # Fallback: return first plan if available, or empty result
        print(f"Error creating final plan: {e}")
        if old_plans and len(old_plans) > 0:
            # Return the first plan as fallback
            return {
                "days": old_plans[0] if old_plans[0] else [],
                "trip_summary": "Final plan created by merging multiple suggestions and incorporating poll results."
            }
        return {
            "days": [],
            "trip_summary": "Unable to generate final plan."
        }


if __name__ == "__main__":
    query = "I want to go to the Greece for 10 days"
    old_plan_json = {}
    print(json.dumps(brainstorm_chat(query, old_plan_json), indent=4, default=str))