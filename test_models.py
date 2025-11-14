"""
Test script to demonstrate loading and validating the sample JSON data
using the Pydantic models.
"""

import json
from pathlib import Path
from backend.models import TripList, Trip, Activity, ActivityType


def load_sample_data():
    """Load and validate sample data using Pydantic models."""
    
    # Load the sample JSON file
    sample_file = Path("sample-data/sample03.json")
    
    if not sample_file.exists():
        print(f"Sample file not found: {sample_file}")
        return None
    
    with open(sample_file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    # Create TripList from JSON data
    try:
        trip_list = TripList.from_json_array(json_data)
        print("✅ Successfully loaded and validated sample data!")
        return trip_list
    except Exception as e:
        print(f"❌ Error validating data: {e}")
        return None


def demonstrate_model_usage():
    """Demonstrate various model operations."""
    
    print("🏖️  Vibecation Pydantic Models Demo\n")
    
    # Load sample data
    trip_list = load_sample_data()
    if not trip_list:
        return
    
    # Display basic info
    print(f"📊 Loaded {len(trip_list.trips)} trip(s)")
    
    for trip in trip_list.trips:
        print(f"\n🎯 Trip: {trip.trip_name} (ID: {trip.trip_id})")
        print(f"   📅 Total activities: {len(trip.activities)}")
        
        for activity in trip.activities:
            print(f"   🎬 {activity.activity_name}")
            print(f"      📍 {activity.start_location} → {activity.end_location}")
            print(f"      🏷️  Type: {activity.activity_type.value}")
            print(f"      ⏰ {activity.from_date_time} → {activity.to_date_time}")
            
            if activity.activities:
                print(f"      🔗 Sub-activities: {len(activity.activities)}")
                for sub_activity in activity.activities:
                    print(f"         • {sub_activity.activity_name}")
    
    # Demonstrate JSON serialization
    print(f"\n📤 JSON Export Preview:")
    json_output = trip_list.model_dump_json(indent=2)
    print(json_output[:300] + "..." if len(json_output) > 300 else json_output)
    
    # Show model schema
    print(f"\n📋 Activity Model Schema:")
    schema = Activity.model_json_schema()
    print(f"   Properties: {len(schema.get('properties', {}))}")
    print(f"   Required fields: {schema.get('required', [])}")


if __name__ == "__main__":
    demonstrate_model_usage()