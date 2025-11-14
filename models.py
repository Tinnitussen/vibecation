"""
Pydantic models for the Vibecation holiday planning application.
Based on the JSON structure from sample03.json.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class ActivityType(str, Enum):
    """Enumeration of activity types."""
    ATTRACTION = "attraction"
    TRAVEL = "travel"
    FOOD = "food"
    ENTERTAINMENT = "entertainment"
    ACCOMMODATION = "accommodation"


class Activity(BaseModel):
    """
    Model representing a single activity in a holiday itinerary.
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

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "activity_id": "activity_001a1",
                "activity_name": "Sagrada Familia tour",
                "activity_type": "attraction",
                "activity_description": "Guided tour of Gaudí's masterpiece, the iconic Sagrada Familia basilica.",
                "from_date_time": "2025-04-12T10:00:00Z",
                "start_location": "Sagrada Familia",
                "start_lat": 41.4036,
                "start_lon": 2.1744,
                "to_date_time": "2025-04-12T11:30:00Z",
                "end_location": "Sagrada Familia",
                "end_lat": 41.4036,
                "end_lon": 2.1744,
                "activities": []
            }
        }


class Holiday(BaseModel):
    """
    Model representing a complete holiday itinerary.
    """
    holiday_name: str = Field(..., description="Name of the holiday")
    holiday_id: str = Field(..., description="Unique identifier for the holiday")
    activities: List[Activity] = Field(..., description="List of activities in the holiday")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "holiday_name": "Spain Week",
                "holiday_id": "holiday_001",
                "activities": []
            }
        }


class HolidayList(BaseModel):
    """
    Root model representing a list of holidays.
    This matches the JSON array structure.
    """
    holidays: List[Holiday] = Field(..., description="List of holidays")

    @classmethod
    def from_json_array(cls, json_data: List[dict]) -> 'HolidayList':
        """
        Create a HolidayList from a JSON array structure.
        
        Args:
            json_data: List of holiday dictionaries
            
        Returns:
            HolidayList instance
        """
        holidays = [Holiday(**holiday_data) for holiday_data in json_data]
        return cls(holidays=holidays)

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "holidays": [
                    {
                        "holiday_name": "Spain Week",
                        "holiday_id": "holiday_001",
                        "activities": []
                    }
                ]
            }
        }


# Enable forward references for recursive Activity model
Activity.model_rebuild()