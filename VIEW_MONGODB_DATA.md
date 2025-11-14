# How to View MongoDB Data in Docker

## Method 1: Using MongoDB Shell (mongosh) - Interactive

### Connect to MongoDB shell:
```bash
docker exec -it vibecation-mongodb mongosh vibecation
```

### Useful commands once inside mongosh:

```javascript
// Show all databases
show dbs

// Use the vibecation database
use vibecation

// Show all collections
show collections

// View all trips
db.trips.find().pretty()

// View all votes
db.votes.find().pretty()

// View all users
db.users.find().pretty()

// Count documents in a collection
db.trips.countDocuments()

// Find a specific trip
db.trips.findOne({ trip_id: "trip_001" })

// View votes for a specific user
db.votes.find({ userID: "user123" }).pretty()

// View all activities in trips
db.trips.aggregate([
  { $unwind: "$activities" },
  { $project: { activity_name: "$activities.activity_name", activity_type: "$activities.activity_type" } }
])
```

### Exit mongosh:
```bash
exit
```

---

## Method 2: Using MongoDB Shell - One-liner Commands

### View all trips:
```bash
docker exec vibecation-mongodb mongosh vibecation --eval "db.trips.find().pretty()"
```

### View all votes:
```bash
docker exec vibecation-mongodb mongosh vibecation --eval "db.votes.find().pretty()"
```

### Count documents:
```bash
docker exec vibecation-mongodb mongosh vibecation --eval "db.trips.countDocuments()"
```

### List all collections:
```bash
docker exec vibecation-mongodb mongosh vibecation --eval "show collections"
```

### View specific collection:
```bash
docker exec vibecation-mongodb mongosh vibecation --eval "db.users.find().pretty()"
```

---

## Method 3: Using MongoDB Compass (GUI Tool)

1. **Download MongoDB Compass**: https://www.mongodb.com/try/download/compass

2. **Connect using:**
   - Connection String: `mongodb://localhost:27017`
   - Or: `mongodb://127.0.0.1:27017`
   - Database: `vibecation`

3. **No authentication needed** (as per your docker-compose.yml)

4. **Browse collections visually** with a GUI interface

---

## Method 4: Export Data to JSON

### Export all trips:
```bash
docker exec vibecation-mongodb mongodump --db=vibecation --collection=trips --out=/tmp/backup
docker cp vibecation-mongodb:/tmp/backup/vibecation/trips.bson ./trips.bson
```

### Or export as JSON:
```bash
docker exec vibecation-mongodb mongosh vibecation --quiet --eval "JSON.stringify(db.trips.find().toArray())" > trips.json
```

---

## Method 5: Using Python Script

Create a script to view data:

```python
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def view_data():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.vibecation
    
    # View trips
    trips = await db.trips.find().to_list(length=100)
    print(f"Found {len(trips)} trips")
    for trip in trips:
        print(f"Trip: {trip.get('trip_name')} (ID: {trip.get('trip_id')})")
    
    # View votes
    votes = await db.votes.find().to_list(length=100)
    print(f"\nFound {len(votes)} votes")
    for vote in votes:
        print(f"Vote: {vote.get('userID')} -> {vote.get('optionID')} ({vote.get('vote')})")

asyncio.run(view_data())
```

---

## Quick Reference Commands

```bash
# Connect to MongoDB shell
docker exec -it vibecation-mongodb mongosh vibecation

# View all collections
docker exec vibecation-mongodb mongosh vibecation --eval "show collections"

# View all trips
docker exec vibecation-mongodb mongosh vibecation --eval "db.trips.find().pretty()"

# View all votes
docker exec vibecation-mongodb mongosh vibecation --eval "db.votes.find().pretty()"

# View all users
docker exec vibecation-mongodb mongosh vibecation --eval "db.users.find().pretty()"

# Count documents
docker exec vibecation-mongodb mongosh vibecation --eval "db.trips.countDocuments()"
```

---

## Troubleshooting

If the container is not running:
```bash
docker-compose up -d mongodb
```

If you get connection errors:
```bash
# Check if container is healthy
docker ps --filter "name=vibecation-mongodb"

# Check MongoDB logs
docker logs vibecation-mongodb
```

