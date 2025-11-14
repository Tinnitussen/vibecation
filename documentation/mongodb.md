# MongoDB Database Schema for Vibecation

## Overview
This document defines the MongoDB database schema, indexes, security measures, and Change Data Capture (CDC) functions for the Vibecation travel planner application.

---

## Database Configuration

### Database Name
```
vibecation
```

### Connection String Format
```
mongodb://localhost:27017/vibecation
```

---

## Collections

### 1. `users`

**Purpose**: Store user accounts and authentication information

**Schema**:
```javascript
{
  _id: ObjectId,                    // MongoDB auto-generated ID
  userID: String,                   // Human-readable unique ID (e.g., "user_001")
  username: String,                 // Unique username
  email: String,                    // Unique email address
  name: String,                     // Full name
  passwordHash: String,             // Bcrypt hashed password (NEVER store plain text)
  salt: String,                     // Salt used for password hashing (if not using bcrypt's built-in salt)
  createdAt: Date,                  // Account creation timestamp
  updatedAt: Date,                  // Last update timestamp
  lastLoginAt: Date,                // Last login timestamp
  isActive: Boolean,                // Account status (default: true)
  passwordResetToken: String,       // Token for password reset (optional)
  passwordResetExpires: Date        // Token expiration (optional)
}
```

**Indexes**:
```javascript
// Unique indexes
db.users.createIndex({ "userID": 1 }, { unique: true })
db.users.createIndex({ "username": 1 }, { unique: true })
db.users.createIndex({ "email": 1 }, { unique: true })

// Performance indexes
db.users.createIndex({ "isActive": 1 })
db.users.createIndex({ "createdAt": -1 })
```

**Password Security**:
- Use **bcrypt** with 12+ salt rounds
- Never store plain text passwords
- Hash passwords before saving: `bcrypt.hash(password, 12)`
- Verify passwords: `bcrypt.compare(plainPassword, passwordHash)`
- Consider implementing password strength requirements (min length, complexity)

**User Creation Function**:
```javascript
async function createUser(username, email, name, password) {
  // Validate input
  if (!username || !email || !name || !password) {
    throw new Error('All fields are required');
  }
  
  // Check if username or email already exists
  const existingUser = await db.users.findOne({
    $or: [{ username: username }, { email: email }]
  });
  
  if (existingUser) {
    if (existingUser.username === username) {
      throw new Error('Username already exists');
    }
    if (existingUser.email === email) {
      throw new Error('Email already registered');
    }
  }
  
  // Validate password strength
  const passwordValidation = validatePasswordStrength(password);
  if (!passwordValidation.valid) {
    throw new Error(passwordValidation.message);
  }
  
  // Generate user ID
  const userID = generateNextID('users');
  
  // Hash password
  const passwordHash = await hashPassword(password);
  
  // Create user document
  const user = {
    userID: userID,
    username: username,
    email: email,
    name: name,
    passwordHash: passwordHash,
    createdAt: new Date(),
    updatedAt: new Date(),
    isActive: true
  };
  
  // Insert user
  const result = await db.users.insertOne(user);
  
  // Log audit event
  await logAuditEvent('users', userID, 'insert', userID, {
    after: { userID: userID, username: username, email: email }
  });
  
  return {
    userID: userID,
    username: username,
    email: email,
    name: name
  };
}
```

**Check Availability Function**:
```javascript
async function checkUserAvailability(username, email) {
  if (!username && !email) {
    throw new Error('Must provide either username or email');
  }
  
  const query = {};
  if (username) {
    query.username = username;
  }
  if (email) {
    query.email = email;
  }
  
  const existingUser = await db.users.findOne(query);
  
  return {
    available: !existingUser,
    field: username ? 'username' : 'email'
  };
}
```

---

### 2. `trips`

**Purpose**: Store trip information and metadata

**Schema**:
```javascript
{
  _id: ObjectId,                    // MongoDB auto-generated ID
  tripID: String,                   // Human-readable unique ID (e.g., "trip_001")
  title: String,                    // Trip title
  description: String,              // Trip description
  ownerID: String,                  // Reference to users.userID (trip creator)
  members: [String],                // Array of userIDs
  startDate: Date,                  // Trip start date
  endDate: Date,                    // Trip end date
  status: String,                   // Enum: "planning", "confirmed", "completed", "cancelled"
  createdAt: Date,
  updatedAt: Date,
  itinerary: {                      // Final confirmed itinerary (optional)
    days: [VibecationDay]           // Array of VibecationDay objects
  }
}
```

**Indexes**:
```javascript
// Unique index
db.trips.createIndex({ "tripID": 1 }, { unique: true })

// Performance indexes
db.trips.createIndex({ "ownerID": 1 })
db.trips.createIndex({ "members": 1 })           // For finding trips by member
db.trips.createIndex({ "status": 1 })
db.trips.createIndex({ "startDate": 1, "endDate": 1 })
db.trips.createIndex({ "createdAt": -1 })
db.trips.createIndex({ "ownerID": 1, "status": 1 })  // Compound index for dashboard queries
```

---

### 3. `trip_suggestions`

**Purpose**: Store trip suggestions created by users during brainstorming

**Schema**:
```javascript
{
  _id: ObjectId,                    // MongoDB auto-generated ID
  tripSuggestionID: String,         // Human-readable unique ID (e.g., "suggestion_001")
  tripID: String,                   // Reference to trips.tripID
  userID: String,                   // Reference to users.userID (suggestion creator)
  days: [VibecationDay],            // Array of VibecationDay objects
  status: String,                   // Enum: "draft", "submitted", "archived"
  createdAt: Date,
  updatedAt: Date,
  submittedAt: Date                 // When suggestion was submitted (null if draft)
}
```

**Indexes**:
```javascript
// Unique index
db.trip_suggestions.createIndex({ "tripSuggestionID": 1 }, { unique: true })

// Performance indexes
db.trip_suggestions.createIndex({ "tripID": 1, "userID": 1 })
db.trip_suggestions.createIndex({ "tripID": 1, "status": 1 })
db.trip_suggestions.createIndex({ "userID": 1 })
db.trip_suggestions.createIndex({ "createdAt": -1 })
db.trip_suggestions.createIndex({ "tripID": 1, "submittedAt": -1 })  // For getting all suggestions for a trip
```

---

### 4. `vibecation_days` (Embedded in trip_suggestions, but can be separate for queries)

**Purpose**: Store individual day plans (can be embedded or referenced)

**Schema** (when embedded in trip_suggestions):
```javascript
{
  id: Number,                       // Day number (1, 2, 3, ...)
  description: String,              // Day description
  date: Date,                       // Date of the day
  location: String,                 // Primary location for the day
  activities: [Activity]            // Array of Activity objects
}
```

**Note**: This is typically embedded in `trip_suggestions.days` array, but can be extracted for separate queries if needed.

---

### 5. `activities`

**Purpose**: Store activity information (can be embedded or referenced)

**Schema** (when embedded in VibecationDay):
```javascript
{
  id: Number,                       // Activity ID within the day
  activity_id: String,              // Unique activity identifier
  activity_name: String,            // Activity name
  activity_type: String,            // Enum: "attraction", "travel", "food", "entertainment", "accommodation", "watersport", "sightseeing", "relaxing"
  activity_description: String,     // Activity description
  vigor: String,                    // Enum: "low", "medium", "high"
  location: String,                 // Location name
  from_date_time: Date,             // Start date and time
  to_date_time: Date,               // End date and time
  start_location: String,           // Starting location
  start_lat: Number,                // Starting latitude
  start_lon: Number,                // Starting longitude
  end_location: String,             // Ending location
  end_lat: Number,                  // Ending latitude
  end_lon: Number,                  // Ending longitude
  activities: [Activity]            // Nested sub-activities (recursive)
}
```

**Indexes** (if stored as separate collection):
```javascript
db.activities.createIndex({ "activity_id": 1 }, { unique: true })
db.activities.createIndex({ "activity_type": 1 })
db.activities.createIndex({ "from_date_time": 1, "to_date_time": 1 })
db.activities.createIndex({ "start_lat": 1, "start_lon": 1 })  // Geospatial index
db.activities.createIndex({ "end_lat": 1, "end_lon": 1 })      // Geospatial index
```

---

### 6. `locations`

**Purpose**: Store location information for polls and references

**Schema**:
```javascript
{
  _id: ObjectId,                    // MongoDB auto-generated ID
  locationID: String,               // Human-readable unique ID (e.g., "loc_001")
  name: String,                     // Location name
  type: String,                     // Enum: "city", "landmark", "restaurant", "hotel", "airport", etc.
  lat: Number,                      // Latitude
  lon: Number,                      // Longitude
  address: String,                  // Full address (optional)
  country: String,                  // Country name (optional)
  city: String,                     // City name (optional)
  createdAt: Date,
  updatedAt: Date
}
```

**Indexes**:
```javascript
// Unique index
db.locations.createIndex({ "locationID": 1 }, { unique: true })

// Performance indexes
db.locations.createIndex({ "name": 1 })
db.locations.createIndex({ "type": 1 })
db.locations.createIndex({ "lat": 1, "lon": 1 })  // Geospatial index for location queries
db.locations.createIndex({ "country": 1, "city": 1 })
```

---

### 7. `polls`

**Purpose**: Store poll information and aggregated results

**Schema**:
```javascript
{
  _id: ObjectId,                    // MongoDB auto-generated ID
  pollID: String,                   // Human-readable unique ID (e.g., "poll_001")
  tripID: String,                   // Reference to trips.tripID
  pollType: String,                 // Enum: "activity", "location", "activity_vigor", "food_cuisine"
  status: String,                   // Enum: "open", "closed", "completed"
  options: [                        // Poll options (varies by type)
    {
      optionID: String,             // Unique option identifier
      optionData: Mixed,            // Activity, Location, or other data
      upvotes: Number,              // Count of upvotes
      downvotes: Number,            // Count of downvotes
      netScore: Number              // Calculated: upvotes - downvotes
    }
  ],
  createdAt: Date,
  updatedAt: Date,
  closedAt: Date,                   // When poll was closed (null if open)
  totalVotes: Number                // Total number of votes cast
}
```

**Indexes**:
```javascript
// Unique index
db.polls.createIndex({ "pollID": 1 }, { unique: true })

// Performance indexes
db.polls.createIndex({ "tripID": 1, "pollType": 1 })
db.polls.createIndex({ "tripID": 1, "status": 1 })
db.polls.createIndex({ "status": 1 })
db.polls.createIndex({ "createdAt": -1 })
```

---

### 8. `votes`

**Purpose**: Store individual user votes on polls

**Schema**:
```javascript
{
  _id: ObjectId,                    // MongoDB auto-generated ID
  voteID: String,                   // Human-readable unique ID (e.g., "vote_001")
  pollID: String,                   // Reference to polls.pollID
  tripID: String,                   // Reference to trips.tripID
  userID: String,                   // Reference to users.userID
  optionID: String,                 // The option being voted on
  voteType: String,                 // Enum: "activity", "location", "activity_vigor", "food_cuisine"
  vote: Boolean,                    // true = upvote, false = downvote (or preference for vigor/cuisine)
  voteValue: Mixed,                 // For vigor: "low"/"medium"/"high", for cuisine: cuisine name
  createdAt: Date,
  updatedAt: Date
}
```

**Indexes**:
```javascript
// Unique index
db.votes.createIndex({ "voteID": 1 }, { unique: true })

// Performance indexes - prevent duplicate votes
db.votes.createIndex({ "pollID": 1, "userID": 1, "optionID": 1 }, { unique: true })
db.votes.createIndex({ "tripID": 1, "userID": 1 })
db.votes.createIndex({ "pollID": 1 })
db.votes.createIndex({ "userID": 1 })
db.votes.createIndex({ "createdAt": -1 })
```

---

### 9. `trip_details`

**Purpose**: Store additional trip configuration details (accommodation, flights, etc.)

**Schema**:
```javascript
{
  _id: ObjectId,                    // MongoDB auto-generated ID
  tripDetailID: String,             // Human-readable unique ID (e.g., "detail_001")
  tripID: String,                   // Reference to trips.tripID (unique)
  accommodation: {
    name: String,
    type: String,                   // Enum: "hotel", "apartment", "hostel", "airbnb", etc.
    checkIn: Date,
    checkOut: Date,
    address: String,
    notes: String
  },
  flights: {
    outbound: {
      departureAirport: String,
      arrivalAirport: String,
      departureDate: Date,
      departureTime: String,
      arrivalDate: Date,
      arrivalTime: String,
      airline: String,
      flightNumber: String,
      bookingReference: String,
      confirmationNumber: String
    },
    return: {
      departureAirport: String,
      arrivalAirport: String,
      departureDate: Date,
      departureTime: String,
      arrivalDate: Date,
      arrivalTime: String,
      airline: String,
      flightNumber: String,
      bookingReference: String,
      confirmationNumber: String
    }
  },
  transportation: {
    rentalCar: {
      hasRentalCar: Boolean,
      company: String,
      model: String,
      pickupDate: Date,
      returnDate: Date,
      bookingReference: String
    },
    publicTransportPasses: [String],
    notes: String
  },
  travelDocuments: {
    passportRequired: Boolean,
    visaRequired: Boolean,
    travelInsurance: {
      hasInsurance: Boolean,
      policyNumber: String,
      provider: String
    },
    emergencyContacts: [{
      name: String,
      relationship: String,
      phone: String,
      email: String
    }]
  },
  budget: {
    totalBudget: Number,
    currency: String,               // Default: "USD"
    breakdown: {
      accommodation: Number,
      food: Number,
      activities: Number,
      transport: Number,
      other: Number
    }
  },
  additionalDetails: {
    packingList: [String],
    importantNotes: String,
    timeZone: String,
    weatherInfo: String              // Can be fetched from external API
  },
  createdAt: Date,
  updatedAt: Date
}
```

**Indexes**:
```javascript
// Unique index - one detail record per trip
db.trip_details.createIndex({ "tripDetailID": 1 }, { unique: true })
db.trip_details.createIndex({ "tripID": 1 }, { unique: true })

// Performance indexes
db.trip_details.createIndex({ "createdAt": -1 })
db.trip_details.createIndex({ "updatedAt": -1 })
```

---

### 10. `chat_messages` (Optional - for chat history)

**Purpose**: Store chat messages from brainstorming sessions

**Schema**:
```javascript
{
  _id: ObjectId,                    // MongoDB auto-generated ID
  messageID: String,                // Human-readable unique ID (e.g., "msg_001")
  tripID: String,                   // Reference to trips.tripID
  userID: String,                   // Reference to users.userID
  tripSuggestionID: String,         // Reference to trip_suggestions.tripSuggestionID
  messageType: String,              // Enum: "user", "system", "assistant"
  content: String,                  // Message content
  metadata: {                       // Additional data
    query: String,                  // Original user query (for user messages)
    responseData: Mixed             // LLM response data (for system messages)
  },
  createdAt: Date
}
```

**Indexes**:
```javascript
// Unique index
db.chat_messages.createIndex({ "messageID": 1 }, { unique: true })

// Performance indexes
db.chat_messages.createIndex({ "tripID": 1, "createdAt": -1 })
db.chat_messages.createIndex({ "tripSuggestionID": 1, "createdAt": -1 })
db.chat_messages.createIndex({ "userID": 1 })
db.chat_messages.createIndex({ "createdAt": -1 })
```

---

### 11. `id_counters` (Helper Collection)

**Purpose**: Generate sequential human-readable IDs

**Schema**:
```javascript
{
  _id: ObjectId,
  collectionName: String,           // Name of collection (e.g., "users", "trips")
  currentValue: Number              // Current counter value
}
```

**Indexes**:
```javascript
db.id_counters.createIndex({ "collectionName": 1 }, { unique: true })
```

**Usage**: This collection is used by the ID generation function to create sequential IDs like "user_001", "trip_001", etc.

---

## Auto-ID Generation Function

### Function: `generateNextID(collectionName)`

**Purpose**: Generate the next sequential ID for a collection

**Implementation** (MongoDB JavaScript):
```javascript
function generateNextID(collectionName) {
  const counter = db.id_counters.findOneAndUpdate(
    { collectionName: collectionName },
    { $inc: { currentValue: 1 } },
    { upsert: true, returnNewDocument: true }
  );
  
  const prefix = collectionName.substring(0, 4); // e.g., "user", "trip"
  const paddedNumber = String(counter.currentValue).padStart(3, '0');
  return `${prefix}_${paddedNumber}`;
}
```

**Usage Examples**:
```javascript
// Generate user ID
const userID = generateNextID("users");  // Returns: "user_001", "user_002", etc.

// Generate trip ID
const tripID = generateNextID("trips");  // Returns: "trip_001", "trip_002", etc.

// Generate suggestion ID
const suggestionID = generateNextID("trip_suggestions");  // Returns: "trip_001", etc.
```

**Alternative**: Use UUID v4 for truly unique IDs:
```javascript
function generateUUID() {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c == 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}
```

---

## Password Security Functions

### Function: `hashPassword(plainPassword)`

**Implementation** (Node.js with bcrypt):
```javascript
const bcrypt = require('bcrypt');

async function hashPassword(plainPassword) {
  const saltRounds = 12; // Recommended: 10-12 rounds
  const hash = await bcrypt.hash(plainPassword, saltRounds);
  return hash;
}
```

### Function: `verifyPassword(plainPassword, passwordHash)`

**Implementation**:
```javascript
async function verifyPassword(plainPassword, passwordHash) {
  const isValid = await bcrypt.compare(plainPassword, passwordHash);
  return isValid;
}
```

### Function: `validatePasswordStrength(password)`

**Implementation**:
```javascript
function validatePasswordStrength(password) {
  const minLength = 8;
  const hasUpperCase = /[A-Z]/.test(password);
  const hasLowerCase = /[a-z]/.test(password);
  const hasNumbers = /\d/.test(password);
  const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);
  
  if (password.length < minLength) {
    return { valid: false, message: `Password must be at least ${minLength} characters` };
  }
  
  if (!hasUpperCase || !hasLowerCase) {
    return { valid: false, message: "Password must contain both uppercase and lowercase letters" };
  }
  
  if (!hasNumbers) {
    return { valid: false, message: "Password must contain at least one number" };
  }
  
  // Optional: require special characters
  // if (!hasSpecialChar) {
  //   return { valid: false, message: "Password must contain at least one special character" };
  // }
  
  return { valid: true, message: "Password is valid" };
}
```

### Best Practices:
1. **Never store plain text passwords** - Always hash before storing
2. **Use bcrypt with 12+ salt rounds** - Balances security and performance
3. **Implement password strength requirements** - Minimum length, complexity
4. **Use HTTPS** - Encrypt passwords in transit
5. **Implement rate limiting** - Prevent brute force attacks
6. **Add password reset functionality** - With secure tokens and expiration
7. **Consider 2FA** - Two-factor authentication for additional security

---

## Change Data Capture (CDC) Functions

### Purpose
CDC functions track changes to documents for:
- Audit logging
- Real-time updates (polling, notifications)
- Data synchronization
- Analytics

### Implementation Options

#### Option 1: MongoDB Change Streams (Recommended)

**Function: `watchCollection(collectionName, callback)`**

```javascript
const { MongoClient } = require('mongodb');

async function watchCollection(collectionName, callback) {
  const client = new MongoClient(connectionString);
  await client.connect();
  
  const collection = client.db('vibecation').collection(collectionName);
  const changeStream = collection.watch();
  
  changeStream.on('change', (change) => {
    callback(change);
  });
  
  return changeStream;
}
```

**Usage Examples**:

```javascript
// Watch trips collection for real-time updates
watchCollection('trips', (change) => {
  console.log('Change detected:', change);
  
  if (change.operationType === 'update') {
    // Notify trip members of changes
    notifyTripMembers(change.documentKey._id, change.updateDescription);
  }
  
  if (change.operationType === 'insert') {
    // New trip created
    logAuditEvent('trip_created', change.fullDocument);
  }
  
  if (change.operationType === 'delete') {
    // Trip deleted
    logAuditEvent('trip_deleted', change.documentKey);
  }
});

// Watch votes collection for real-time poll updates
watchCollection('votes', (change) => {
  if (change.operationType === 'insert' || change.operationType === 'update') {
    // Update poll results in real-time
    updatePollResults(change.fullDocument.pollID);
  }
});
```

#### Option 2: Audit Log Collection

**Collection: `audit_logs`**

**Schema**:
```javascript
{
  _id: ObjectId,
  logID: String,                    // Human-readable unique ID
  collectionName: String,           // Collection that was changed
  documentID: String,               // ID of the changed document
  operationType: String,            // Enum: "insert", "update", "delete"
  userID: String,                   // User who made the change
  changes: {                        // What changed
    before: Mixed,                  // Document state before change
    after: Mixed,                   // Document state after change
    updatedFields: [String]         // Fields that were updated
  },
  timestamp: Date,
  ipAddress: String,                // IP address of the request (optional)
  userAgent: String                 // User agent (optional)
}
```

**Indexes**:
```javascript
db.audit_logs.createIndex({ "logID": 1 }, { unique: true })
db.audit_logs.createIndex({ "collectionName": 1, "timestamp": -1 })
db.audit_logs.createIndex({ "documentID": 1, "timestamp": -1 })
db.audit_logs.createIndex({ "userID": 1, "timestamp": -1 })
db.audit_logs.createIndex({ "timestamp": -1 })
```

**Function: `logAuditEvent(collectionName, documentID, operationType, userID, changes)`**

```javascript
async function logAuditEvent(collectionName, documentID, operationType, userID, changes) {
  const logID = generateNextID("audit_logs");
  
  await db.audit_logs.insertOne({
    logID: logID,
    collectionName: collectionName,
    documentID: documentID,
    operationType: operationType,
    userID: userID,
    changes: changes,
    timestamp: new Date()
  });
}
```

#### Option 3: Pre/Post Hooks (Middleware)

**Function: `setupChangeTracking(collectionName)`**

```javascript
// Example using Mongoose middleware (if using Mongoose)
const tripSchema = new Schema({ /* ... */ });

tripSchema.pre('save', function(next) {
  this.updatedAt = new Date();
  next();
});

tripSchema.post('save', async function(doc) {
  await logAuditEvent('trips', doc.tripID, 'update', doc.ownerID, {
    after: doc.toObject()
  });
});

tripSchema.post('remove', async function(doc) {
  await logAuditEvent('trips', doc.tripID, 'delete', doc.ownerID, {
    before: doc.toObject()
  });
});
```

### Recommended CDC Functions

#### 1. Real-time Poll Updates
```javascript
async function setupPollWatcher() {
  watchCollection('votes', async (change) => {
    if (change.operationType === 'insert' || change.operationType === 'update') {
      const vote = change.fullDocument;
      
      // Update poll results
      await db.polls.updateOne(
        { pollID: vote.pollID },
        { 
          $inc: { 
            [`options.$[option].${vote.vote ? 'upvotes' : 'downvotes'}`]: 1,
            totalVotes: 1
          },
          $set: { updatedAt: new Date() }
        },
        { arrayFilters: [{ "option.optionID": vote.optionID }] }
      );
      
      // Recalculate net score
      await recalculatePollScores(vote.pollID);
      
      // Notify trip members of poll update
      await notifyPollUpdate(vote.tripID, vote.pollID);
    }
  });
}
```

#### 2. Trip Member Notifications
```javascript
async function setupTripWatcher() {
  watchCollection('trips', async (change) => {
    if (change.operationType === 'update') {
      const trip = await db.trips.findOne({ _id: change.documentKey._id });
      
      // Notify all trip members of changes
      for (const memberID of trip.members) {
        await sendNotification(memberID, {
          type: 'trip_updated',
          tripID: trip.tripID,
          changes: change.updateDescription.updatedFields
        });
      }
    }
  });
}
```

#### 3. Activity Logging
```javascript
async function logUserActivity(userID, action, details) {
  await db.audit_logs.insertOne({
    logID: generateNextID("audit_logs"),
    collectionName: 'user_activity',
    documentID: userID,
    operationType: action,
    userID: userID,
    changes: { details: details },
    timestamp: new Date()
  });
}
```

---

## Database Initialization Script

```javascript
// Initialize database with indexes and default data

// Create all indexes
async function initializeDatabase() {
  const db = client.db('vibecation');
  
  // Users indexes
  await db.collection('users').createIndexes([
    { key: { userID: 1 }, unique: true },
    { key: { username: 1 }, unique: true },
    { key: { email: 1 }, unique: true },
    { key: { isActive: 1 } },
    { key: { createdAt: -1 } }
  ]);
  
  // Trips indexes
  await db.collection('trips').createIndexes([
    { key: { tripID: 1 }, unique: true },
    { key: { ownerID: 1 } },
    { key: { members: 1 } },
    { key: { status: 1 } },
    { key: { startDate: 1, endDate: 1 } },
    { key: { ownerID: 1, status: 1 } }
  ]);
  
  // Trip suggestions indexes
  await db.collection('trip_suggestions').createIndexes([
    { key: { tripSuggestionID: 1 }, unique: true },
    { key: { tripID: 1, userID: 1 } },
    { key: { tripID: 1, status: 1 } },
    { key: { tripID: 1, submittedAt: -1 } }
  ]);
  
  // Polls indexes
  await db.collection('polls').createIndexes([
    { key: { pollID: 1 }, unique: true },
    { key: { tripID: 1, pollType: 1 } },
    { key: { tripID: 1, status: 1 } }
  ]);
  
  // Votes indexes
  await db.collection('votes').createIndexes([
    { key: { voteID: 1 }, unique: true },
    { key: { pollID: 1, userID: 1, optionID: 1 }, unique: true },
    { key: { tripID: 1, userID: 1 } }
  ]);
  
  // Initialize ID counters
  await db.collection('id_counters').insertMany([
    { collectionName: 'users', currentValue: 0 },
    { collectionName: 'trips', currentValue: 0 },
    { collectionName: 'trip_suggestions', currentValue: 0 },
    { collectionName: 'polls', currentValue: 0 },
    { collectionName: 'votes', currentValue: 0 },
    { collectionName: 'locations', currentValue: 0 },
    { collectionName: 'trip_details', currentValue: 0 },
    { collectionName: 'chat_messages', currentValue: 0 },
    { collectionName: 'audit_logs', currentValue: 0 }
  ]);
  
  console.log('Database initialized successfully');
}
```

---

## Data Validation Rules

### Application-Level Validation
- Validate all required fields before insertion
- Validate data types and formats (email, dates, etc.)
- Validate enum values
- Validate references (userID exists, tripID exists, etc.)

### Database-Level Validation (Optional - using MongoDB schema validation)
```javascript
// Example: Users collection validation
db.createCollection("users", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["userID", "username", "email", "passwordHash"],
      properties: {
        userID: {
          bsonType: "string",
          description: "must be a string and is required"
        },
        username: {
          bsonType: "string",
          minLength: 3,
          maxLength: 50,
          description: "must be a string between 3 and 50 characters"
        },
        email: {
          bsonType: "string",
          pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
          description: "must be a valid email address"
        },
        passwordHash: {
          bsonType: "string",
          minLength: 60, // Bcrypt hashes are 60 characters
          description: "must be a bcrypt hash"
        }
      }
    }
  }
});
```

---

## Backup and Maintenance

### Regular Backups
- Schedule daily backups of all collections
- Keep backups for at least 30 days
- Test restore procedures regularly

### Data Retention
- Archive old trips after completion (move to archive collection)
- Clean up expired password reset tokens
- Archive audit logs older than 1 year

### Performance Monitoring
- Monitor query performance
- Review slow queries regularly
- Update indexes based on query patterns
- Monitor collection sizes and growth

---

## Security Considerations

1. **Authentication**: Use MongoDB authentication (username/password or certificates)
2. **Authorization**: Implement role-based access control (RBAC)
3. **Encryption**: Enable encryption at rest and in transit
4. **Network Security**: Restrict database access to application servers only
5. **Input Validation**: Validate all inputs before database operations
6. **SQL Injection Prevention**: Use parameterized queries (MongoDB drivers handle this)
7. **Rate Limiting**: Implement rate limiting for authentication endpoints
8. **Audit Logging**: Log all sensitive operations (login, password changes, deletions)

---

## Summary

This schema provides:
- ✅ Auto-generated IDs for all collections
- ✅ Secure password storage with bcrypt
- ✅ Comprehensive indexing for performance
- ✅ Change Data Capture (CDC) with Change Streams
- ✅ Audit logging capabilities
- ✅ Real-time update support for polls
- ✅ Scalable structure for future growth

