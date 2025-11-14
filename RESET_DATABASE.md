# How to Reset MongoDB Database State

## Quick Reset Methods

### Method 1: Drop All Collections (Recommended)

This will remove all data but keep the database structure:

```bash
docker exec vibecation-mongodb mongosh vibecation --eval "
  db.trips.drop();
  db.votes.drop();
  db.users.drop();
  db.polls.drop();
  db.trip_suggestions.drop();
  db.locations.drop();
  db.trip_details.drop();
  db.chat_messages.drop();
  db.audit_logs.drop();
  db.id_counters.drop();
  print('All collections dropped');
"
```

Then reinitialize:
```bash
docker exec -i vibecation-mongodb mongosh vibecation < init-mongo.js
```

### Method 2: Drop Entire Database

This completely removes the database and recreates it:

```bash
# Drop the entire database
docker exec vibecation-mongodb mongosh --eval "db.getSiblingDB('vibecation').dropDatabase()"

# Reinitialize
docker exec -i vibecation-mongodb mongosh vibecation < init-mongo.js
```

### Method 3: Using the Reset Script

```bash
# Make script executable (Linux/Mac)
chmod +x reset-database.sh

# Run the script
./reset-database.sh
```

Or on Windows (Git Bash):
```bash
bash reset-database.sh
```

### Method 4: Reset Specific Collections

If you only want to reset certain collections:

```bash
# Reset only votes
docker exec vibecation-mongodb mongosh vibecation --eval "db.votes.drop()"

# Reset only trips
docker exec vibecation-mongodb mongosh vibecation --eval "db.trips.drop()"

# Reset votes and trips
docker exec vibecation-mongodb mongosh vibecation --eval "
  db.votes.drop();
  db.trips.drop();
"
```

## Complete Reset (Drop Database + Reinitialize)

```bash
# 1. Stop containers (optional, but safer)
docker-compose stop mongodb

# 2. Remove the MongoDB volume (WARNING: This deletes all data permanently)
docker volume rm vibecation_mongodb_data

# 3. Start MongoDB again (will recreate volume and run init script)
docker-compose up -d mongodb

# 4. Wait for initialization
docker-compose logs -f mongodb
```

## Verify Reset

After resetting, verify the database is empty:

```bash
# Check collection counts
docker exec vibecation-mongodb mongosh vibecation --eval "
  print('Trips: ' + db.trips.countDocuments());
  print('Votes: ' + db.votes.countDocuments());
  print('Users: ' + db.users.countDocuments());
  print('Polls: ' + db.polls.countDocuments());
"

# List all collections
docker exec vibecation-mongodb mongosh vibecation --eval "show collections"
```

## Quick One-Liner Reset

```bash
docker exec vibecation-mongodb mongosh vibecation --eval "db.dropDatabase()" && docker exec -i vibecation-mongodb mongosh vibecation < init-mongo.js
```

## Notes

- **Dropping collections** removes data but keeps indexes (they'll be recreated on first insert)
- **Dropping database** removes everything including indexes
- **Removing volume** is the most thorough reset but requires container restart
- The `init-mongo.js` script will recreate collections and indexes

