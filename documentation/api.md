openapi: 3.0.3
info:
  title: Vibecation Travel Planner API
  description: API for planning and managing travel itineraries
  version: 1.0.0
servers:
  - url: http://localhost:8000
    description: Local development server
  - url: https://api.vibecation.com
    description: Production server

paths:
  /login:
    get:
      summary: User login
      description: Authenticate user and return user ID
      parameters:
        - name: username
          in: query
          required: true
          schema:
            type: string
        - name: password
          in: query
          required: true
          schema:
            type: string
            format: password
      responses:
        '200':
          description: Successful login
          content:
            application/json:
              schema:
                type: object
                properties:
                  userID:
                    type: string
        '401':
          description: Invalid credentials

  /dashboard:
    get:
      summary: Get user dashboard
      description: Retrieve all trips for a user
      parameters:
        - name: userID
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: User trips retrieved successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  yourTrips:
                    type: array
                    items:
                      type: string
                      description: tripID

  /tripinfo:
    get:
      summary: Get trip information
      description: Retrieve detailed information about a specific trip
      parameters:
        - name: tripID
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Trip information retrieved successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  title:
                    type: string
                  members:
                    type: array
                    items:
                      type: string
                      description: userID
                  description:
                    type: string
        '404':
          description: Trip not found

  /createtrip:
    post:
      summary: Create a new trip
      description: Create a new trip with members and title
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - title
                - members
              properties:
                tripID:
                  type: string
                  description: Optional trip ID (auto-generated if not provided)
                members:
                  type: array
                  items:
                    $ref: '#/components/schemas/User'
                title:
                  type: string
      responses:
        '201':
          description: Trip created successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  tripID:
                    type: string
                  message:
                    type: string
        '400':
          description: Invalid request data

  /initial_trip_planner:
    get:
      summary: Generate initial trip plan
      description: Create an initial trip plan based on user query
      parameters:
        - name: tripSuggestionID
          in: query
          required: true
          schema:
            type: string
        - name: tripID
          in: query
          required: true
          schema:
            type: string
        - name: userID
          in: query
          required: true
          schema:
            type: string
        - name: query
          in: query
          required: true
          schema:
            type: string
            description: User's trip planning query/preferences/prompt
      responses:
        '200':
          description: Trip plan generated successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  days:
                    type: array
                    items:
                      $ref: '#/components/schemas/VibecationDay'
        '400':
          description: Invalid parameters

  /iterate_trip_planner:
    get:
      summary: Iterate on existing trip plan
      description: Modify an existing trip plan based on new query
      parameters:
        - name: tripSuggestionID
          in: query
          required: true
          schema:
            type: string
        - name: tripID
          in: query
          required: true
          schema:
            type: string
        - name: userID
          in: query
          required: true
          schema:
            type: string
        - name: query
          in: query
          required: true
          schema:
            type: string
            description: Modification query/preferences
        - name: old_plan
          in: query
          required: true
          schema:
            type: string
            description: JSON string of old plan (array of VibecationDay)
      responses:
        '200':
          description: Trip plan updated successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  days:
                    type: array
                    items:
                      $ref: '#/components/schemas/VibecationDay'
        '400':
          description: Invalid parameters

  /post_trip_suggestion:
    post:
      summary: Submit a trip suggestion
      description: Post a new trip suggestion for a trip
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TripSuggestion'
      responses:
        '201':
          description: Trip suggestion posted successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  tripSuggestionID:
                    type: string
                  message:
                    type: string
        '400':
          description: Invalid request data

  /get_all_trip_suggestions:
    get:
      summary: Get all trip suggestions
      description: Retrieve all suggestions for a specific trip
      parameters:
        - name: tripID
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Trip suggestions retrieved successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  suggestions:
                    type: array
                    items:
                      type: array
                      items:
                        $ref: '#/components/schemas/VibecationDay'
        '404':
          description: Trip not found

  /polls/get/activity:
    get:
      summary: Get activity poll
      description: Retrieve activity poll results for a trip
      parameters:
        - name: tripID
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Activity poll retrieved successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  activities:
                    type: array
                    items:
                      $ref: '#/components/schemas/Activity'
        '404':
          description: Trip not found

  /polls/get/location:
    get:
      summary: Get location poll
      description: Retrieve location poll results for a trip
      parameters:
        - name: tripID
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Location poll retrieved successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  locations:
                    type: array
                    items:
                      $ref: '#/components/schemas/Location'
        '404':
          description: Trip not found

  /polls/get/activity_vigor:
    get:
      summary: Get activity vigor poll
      description: Retrieve activity vigor preferences for a trip
      parameters:
        - name: tripID
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Activity vigor poll retrieved successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  vigor_preferences:
                    type: array
                    items:
                      type: object
                      properties:
                        activity_id:
                          type: string
                        vigor:
                          type: string
                          enum: [low, medium, high]
        '404':
          description: Trip not found

  /polls/get/food_cuisines:
    get:
      summary: Get food cuisine poll
      description: Retrieve food cuisine preferences for a trip
      parameters:
        - name: tripID
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Food cuisine poll retrieved successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  cuisines:
                    type: array
                    items:
                      type: string
        '404':
          description: Trip not found

  /polls/vote/activity:
    post:
      summary: Vote on activity
      description: Submit a vote for an activity in a poll
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - tripID
                - activityID
                - userID
              properties:
                tripID:
                  type: string
                activityID:
                  type: string
                userID:
                  type: string
                vote:
                  type: boolean
                  description: true for upvote, false for downvote
      responses:
        '200':
          description: Vote submitted successfully
        '400':
          description: Invalid request data

  /polls/vote/location:
    post:
      summary: Vote on location
      description: Submit a vote for a location in a poll
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - tripID
                - locationID
                - userID
              properties:
                tripID:
                  type: string
                locationID:
                  type: string
                userID:
                  type: string
                vote:
                  type: boolean
      responses:
        '200':
          description: Vote submitted successfully
        '400':
          description: Invalid request data

  /trips/{tripID}:
    get:
      summary: Get trip details
      description: Retrieve full trip details including itinerary
      parameters:
        - name: tripID
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Trip details retrieved successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Trip'
        '404':
          description: Trip not found

    put:
      summary: Update trip
      description: Update trip information
      parameters:
        - name: tripID
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                title:
                  type: string
                description:
                  type: string
                members:
                  type: array
                  items:
                    type: string
      responses:
        '200':
          description: Trip updated successfully
        '404':
          description: Trip not found

    delete:
      summary: Delete trip
      description: Delete a trip
      parameters:
        - name: tripID
          in: path
          required: true
          schema:
            type: string
      responses:
        '204':
          description: Trip deleted successfully
        '404':
          description: Trip not found

  /trips/{tripID}/members:
    post:
      summary: Add member to trip
      description: Add a new member to a trip
      parameters:
        - name: tripID
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - userID
              properties:
                userID:
                  type: string
      responses:
        '200':
          description: Member added successfully
        '400':
          description: Invalid request data
        '404':
          description: Trip not found

    delete:
      summary: Remove member from trip
      description: Remove a member from a trip
      parameters:
        - name: tripID
          in: path
          required: true
          schema:
            type: string
        - name: userID
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Member removed successfully
        '404':
          description: Trip or member not found

  /trips/{tripID}/itinerary:
    get:
      summary: Get trip itinerary
      description: Retrieve the full itinerary for a trip
      parameters:
        - name: tripID
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Itinerary retrieved successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  itinerary:
                    type: array
                    items:
                      $ref: '#/components/schemas/VibecationDay'
        '404':
          description: Trip not found

    put:
      summary: Update trip itinerary
      description: Update the itinerary for a trip
      parameters:
        - name: tripID
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - days
              properties:
                days:
                  type: array
                  items:
                    $ref: '#/components/schemas/VibecationDay'
      responses:
        '200':
          description: Itinerary updated successfully
        '400':
          description: Invalid request data
        '404':
          description: Trip not found

  /users:
    post:
      summary: Create a new user account
      description: Register a new user with username, email, name, and password
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - username
                - email
                - name
                - password
              properties:
                username:
                  type: string
                  minLength: 3
                  maxLength: 50
                  pattern: '^[a-zA-Z0-9_]+$'
                  description: Username (alphanumeric and underscores only)
                email:
                  type: string
                  format: email
                  description: User email address
                name:
                  type: string
                  minLength: 2
                  maxLength: 100
                  description: Full name
                password:
                  type: string
                  format: password
                  minLength: 8
                  description: Password (minimum 8 characters, must contain uppercase, lowercase, and number)
      responses:
        '201':
          description: User created successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  userID:
                    type: string
                  username:
                    type: string
                  email:
                    type: string
                  name:
                    type: string
                  message:
                    type: string
        '400':
          description: Invalid request data (validation error)
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    type: string
                  details:
                    type: object
        '409':
          description: Conflict - username or email already exists
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    type: string
                  field:
                    type: string
                    description: Field that caused the conflict (username or email)

  /users/check-availability:
    get:
      summary: Check username or email availability
      description: Check if a username or email is available for registration
      parameters:
        - name: username
          in: query
          required: false
          schema:
            type: string
          description: Username to check
        - name: email
          in: query
          required: false
          schema:
            type: string
            format: email
          description: Email to check
      responses:
        '200':
          description: Availability check result
          content:
            application/json:
              schema:
                type: object
                properties:
                  available:
                    type: boolean
                  field:
                    type: string
                    description: Field that was checked (username or email)
        '400':
          description: Invalid request - must provide either username or email

  /users/{userID}:
    get:
      summary: Get user profile
      description: Retrieve user profile information
      parameters:
        - name: userID
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: User profile retrieved successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '404':
          description: User not found

components:
  schemas:
    User:
      type: object
      properties:
        userID:
          type: string
        username:
          type: string
        email:
          type: string
          format: email
        name:
          type: string

    Trip:
      type: object
      properties:
        tripID:
          type: string
        title:
          type: string
        description:
          type: string
        members:
          type: array
          items:
            type: string
            description: userID
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time

    VibecationDay:
      type: object
      properties:
        id:
          type: integer
        description:
          type: string
        activities:
          type: array
          items:
            $ref: '#/components/schemas/Activity'
        location:
          type: string
        date:
          type: string
          format: date
          description: Date of the day in the itinerary

    Activity:
      type: object
      properties:
        id:
          type: integer
        description:
          type: string
        vigor:
          type: string
          enum: [low, medium, high]
          description: Activity intensity level
        location:
          type: string
        type:
          type: string
          enum: [watersport, sightseeing, relaxing, attraction, travel, food, entertainment, accommodation]
          description: Type of activity
        activity_name:
          type: string
        activity_id:
          type: string
        from_date_time:
          type: string
          format: date-time
        to_date_time:
          type: string
          format: date-time
        start_location:
          type: string
        start_lat:
          type: number
          format: float
        start_lon:
          type: number
          format: float
        end_location:
          type: string
        end_lat:
          type: number
          format: float
        end_lon:
          type: number
          format: float

    Location:
      type: object
      properties:
        name:
          type: string
        type:
          type: string
          description: Location type (e.g., city, landmark, restaurant)
        location_id:
          type: string
        lat:
          type: number
          format: float
        lon:
          type: number
          format: float

    TripSuggestion:
      type: object
      required:
        - tripID
        - userID
        - days
      properties:
        tripSuggestionID:
          type: string
        tripID:
          type: string
        userID:
          type: string
        days:
          type: array
          items:
            $ref: '#/components/schemas/VibecationDay'
        created_at:
          type: string
          format: date-time
