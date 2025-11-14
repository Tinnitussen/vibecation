#!/bin/bash
# Reset MongoDB database for Vibecation
# This script will drop all collections and reinitialize the database

echo "🔄 Resetting Vibecation database..."

# Drop all collections
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
  print('✅ All collections dropped');
"

# Re-run initialization script
echo "📝 Reinitializing database..."
docker exec -i vibecation-mongodb mongosh vibecation < init-mongo.js

echo "✅ Database reset complete!"

