// MongoDB initialization script
db = db.getSiblingDB('vibecation');

// Create collections
db.createCollection('users');
db.createCollection('trips');
db.createCollection('trip_suggestions');
db.createCollection('polls');
db.createCollection('votes');
db.createCollection('locations');
db.createCollection('trip_details');
db.createCollection('chat_messages');
db.createCollection('audit_logs');
db.createCollection('id_counters');

// Create indexes for users collection
db.users.createIndex({ "userID": 1 }, { unique: true });
db.users.createIndex({ "username": 1 }, { unique: true });
db.users.createIndex({ "email": 1 }, { unique: true });
db.users.createIndex({ "isActive": 1 });
db.users.createIndex({ "createdAt": -1 });

// Create indexes for trips collection
db.trips.createIndex({ "tripID": 1 }, { unique: true });
db.trips.createIndex({ "ownerID": 1 });
db.trips.createIndex({ "members": 1 });
db.trips.createIndex({ "status": 1 });
db.trips.createIndex({ "startDate": 1, "endDate": 1 });
db.trips.createIndex({ "ownerID": 1, "status": 1 });

// Create indexes for trip_suggestions collection
db.trip_suggestions.createIndex({ "tripSuggestionID": 1 }, { unique: true });
db.trip_suggestions.createIndex({ "tripID": 1, "userID": 1 });
db.trip_suggestions.createIndex({ "tripID": 1, "status": 1 });
db.trip_suggestions.createIndex({ "tripID": 1, "submittedAt": -1 });

// Create indexes for polls collection
db.polls.createIndex({ "pollID": 1 }, { unique: true });
db.polls.createIndex({ "tripID": 1, "pollType": 1 });
db.polls.createIndex({ "tripID": 1, "status": 1 });

// Create indexes for votes collection
// Unique index to prevent duplicate votes: one vote per user per option (activity/location)
db.votes.createIndex({ "tripID": 1, "userID": 1, "optionID": 1, "voteType": 1 }, { unique: true });
db.votes.createIndex({ "tripID": 1, "userID": 1 });
db.votes.createIndex({ "tripID": 1, "optionID": 1 });
db.votes.createIndex({ "userID": 1 });
db.votes.createIndex({ "createdAt": -1 });

// Create indexes for locations collection
db.locations.createIndex({ "locationID": 1 }, { unique: true });
db.locations.createIndex({ "lat": 1, "lon": 1 });
db.locations.createIndex({ "name": 1 });

// Create indexes for chat_messages collection
db.chat_messages.createIndex({ "messageID": 1 }, { unique: true });
db.chat_messages.createIndex({ "tripID": 1, "createdAt": -1 });

print("Database initialized successfully!");

