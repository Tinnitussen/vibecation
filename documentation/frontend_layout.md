# Vibecation Frontend Layout

## Overview
This document describes the frontend component structure and layout for the Vibecation travel planner application.

---

## 1. Login Page (`/login`)

### Layout
- **Full-screen centered card layout**
- **Background**: Gradient or travel-themed image

### Components

#### `LoginForm`
- **Type**: Form component
- **Fields**:
  - Username input (text field)
  - Password input (password field with show/hide toggle)
  - Submit button
  - "Forgot password?" link (optional)
- **Validation**: Client-side validation for required fields
- **API Call**: `GET /login?username={username}&password={password}`
- **On Success**: Store `userID` in session/localStorage, redirect to dashboard
- **On Error**: Display error message below form

#### `LoginCard`
- **Type**: Container component
- **Purpose**: Wraps LoginForm in a styled card
- **Styling**: Centered, max-width 400px, shadow, rounded corners
- **Additional Elements**:
  - "Don't have an account? Sign up" link (navigates to `/register`)

---

## 1.5. Registration Page (`/register`)

### Layout
- **Full-screen centered card layout**
- **Background**: Gradient or travel-themed image (same as login)

### Components

#### `RegistrationForm`
- **Type**: Form component
- **Fields**:
  - Username input (text field, required)
    - Validation: Minimum 3 characters, alphanumeric and underscores only
    - Real-time availability check (debounced)
  - Email input (email field, required)
    - Validation: Valid email format
    - Real-time availability check (debounced)
  - Full name input (text field, required)
    - Validation: Minimum 2 characters
  - Password input (password field with show/hide toggle, required)
    - Validation: Minimum 8 characters, must contain uppercase, lowercase, and number
    - Password strength indicator (weak/medium/strong)
  - Confirm password input (password field, required)
    - Validation: Must match password field
  - Terms and conditions checkbox (required)
  - Submit button
- **Validation**: 
  - Client-side validation for all fields
  - Real-time validation feedback
  - Password strength meter
- **API Call**: `POST /users` with `{username, email, name, password}`
- **On Success**: 
  - Show success message
  - Optionally auto-login and redirect to dashboard
  - Or redirect to login page with success message
- **On Error**: Display error message below form (e.g., "Username already taken", "Email already registered")

#### `RegistrationCard`
- **Type**: Container component
- **Purpose**: Wraps RegistrationForm in a styled card
- **Styling**: Centered, max-width 500px, shadow, rounded corners
- **Additional Elements**:
  - "Already have an account? Log in" link (navigates to `/login`)

#### `PasswordStrengthIndicator`
- **Type**: Indicator component
- **Props**: `password` (string)
- **Display**: 
  - Visual bar showing strength (weak/medium/strong)
  - Color-coded (red/yellow/green)
  - Text label indicating strength level
- **Criteria**:
  - Weak: < 8 characters or missing requirements
  - Medium: 8+ characters, meets basic requirements
  - Strong: 8+ characters, uppercase, lowercase, number, special character

#### `FieldAvailabilityIndicator`
- **Type**: Indicator component
- **Props**: `field` (username or email), `value` (string), `isAvailable` (boolean)
- **Display**:
  - Loading spinner while checking
  - Green checkmark if available
  - Red X with message if unavailable
- **Functionality**: Debounced API call to check availability

---

## 2. Trip Dashboard (`/dashboard`)

### Layout
- **Header**: Navigation bar with user profile and logout
- **Main Content**: Grid layout of trip cards
- **Floating Action Button**: "Create New Trip" button (bottom right)

### Components

#### `DashboardHeader`
- **Type**: Navigation bar component
- **Elements**:
  - Logo/Brand name (left)
  - User profile dropdown (right) with:
    - User name/avatar
    - Logout option
- **API Call**: `GET /users/{userID}` for user info

#### `TripCard`
- **Type**: Card component
- **Props**: `tripID`, `title`, `description`, `memberCount`, `lastUpdated`
- **Content**:
  - Trip title (heading)
  - Trip description (truncated)
  - Member avatars/count
  - Last updated timestamp
  - Action buttons: "View", "Edit", "Delete" (icon buttons)
- **Click Action**: Navigate to trip detail page
- **API Calls**: 
  - `GET /tripinfo?tripID={tripID}` for trip details
  - `DELETE /trips/{tripID}` for delete action

#### `TripGrid`
- **Type**: Grid container component
- **Layout**: Responsive grid (3 columns desktop, 2 tablet, 1 mobile)
- **Props**: Array of trip IDs
- **API Call**: `GET /dashboard?userID={userID}` to fetch trip list
- **Functionality**: 
  - Maps over trip IDs
  - Fetches trip info for each
  - Renders TripCard for each trip

#### `CreateTripModal`
- **Type**: Modal/Dialog component
- **Trigger**: Floating action button or "Create Trip" button
- **Form Fields**:
  - Trip title (required, text input)
  - Trip description (optional, textarea)
  - Add members (multi-select or tag input for user IDs)
- **Actions**:
  - "Cancel" button (closes modal)
  - "Create Trip" button (submits form)
- **API Call**: `POST /createtrip` with `{title, members, description?}`
- **On Success**: Close modal, refresh trip list, navigate to new trip

#### `EmptyState`
- **Type**: Empty state component
- **Display**: When user has no trips
- **Content**:
  - Illustration/icon
  - "No trips yet" message
  - "Create your first trip" button

---

## 3. Trip Brainstorm Page (`/trips/{tripID}/brainstorm`)

### Layout
- **Split Layout**: 
  - **Left Side (60%)**: Activity cards visualization
  - **Right Side (40%)**: Chat interface

### Components

#### `BrainstormHeader`
- **Type**: Header component
- **Content**:
  - Trip title
  - Breadcrumb navigation
  - "View Suggestions" button (navigates to suggestions page)

#### `ActivityCardsPanel` (Left Side)
- **Type**: Scrollable panel component
- **Layout**: Vertical scrollable list of day groups
- **Sub-components**:

  ##### `DayGroup`
  - **Type**: Section component
  - **Props**: `day` (VibecationDay object)
  - **Header**: Day number, date, location
  - **Content**: List of ActivityCard components

  ##### `ActivityCard`
  - **Type**: Card component
  - **Props**: `activity` (Activity object)
  - **Content**:
    - Activity name (heading)
    - Activity type badge (color-coded: watersport, sightseeing, relaxing, etc.)
    - Vigor indicator (low/medium/high with visual indicator)
    - Description (collapsible)
    - Time range (from_date_time to to_date_time)
    - Location name
    - Map pin icon (if coordinates available)
  - **Styling**: 
    - Border color based on activity type
    - Vigor indicator (bar or icon)
    - Hover effect for interactivity

#### `ChatInterface` (Right Side)
- **Type**: Chat component
- **Layout**: 
  - **Top**: Chat messages area (scrollable)
  - **Bottom**: Input area with send button

- **Sub-components**:

  ##### `ChatMessages`
  - **Type**: Scrollable container
  - **Props**: Array of message objects
  - **Message Types**:
    - **User Message**: User's prompt/query (right-aligned, blue)
    - **System Message**: LLM response with generated activities (left-aligned, gray)
    - **Loading Message**: Spinner/typing indicator while waiting for LLM response

  ##### `ChatInput`
  - **Type**: Input component
  - **Props**: `onSend`, `isLoading`
  - **Elements**:
    - Textarea (auto-resize, placeholder: "Describe your ideal trip...")
    - "Send" button (disabled while loading)
    - "Clear" button (optional)
  - **Functionality**:
    - On send: 
      - If first message: Call `GET /initial_trip_planner?tripID={tripID}&userID={userID}&query={query}&tripSuggestionID={generatedID}`
      - If subsequent: Call `GET /iterate_trip_planner?tripID={tripID}&userID={userID}&query={query}&old_plan={JSON.stringify(currentDays)}&tripSuggestionID={tripSuggestionID}`
    - Update ActivityCardsPanel with new days array
    - Add user message and system response to chat

  ##### `SubmitSuggestionButton`
  - **Type**: Button component
  - **Location**: Below chat input or in header
  - **Props**: `days` (current plan), `tripID`, `userID`, `tripSuggestionID`
  - **Styling**: Primary button, prominent
  - **Functionality**:
    - Disabled if no activities generated
    - On click: 
      - Call `POST /post_trip_suggestion` with `{tripSuggestionID, tripID, userID, days}`
      - Show success notification
      - Optionally navigate to suggestions page

#### `ActivityTypeFilter`
- **Type**: Filter component (optional)
- **Location**: Above ActivityCardsPanel
- **Functionality**: Filter activities by type (watersport, sightseeing, etc.)
- **UI**: Toggle buttons or checkboxes

---

## 4. Suggestions Review & Polling Page (`/trips/{tripID}/suggestions`)

### Layout
- **Header**: Trip title, "Back to Brainstorm" button
- **Main Content**: 
  - **Top Section**: All suggestions overview
  - **Bottom Section**: Polling interface

### Components

#### `SuggestionsHeader`
- **Type**: Header component
- **Content**:
  - Trip title
  - Participant count
  - "Back to Brainstorm" button
  - "View Final Plan" button (enabled when all polls complete)

#### `SuggestionsOverview`
- **Type**: Grid/List component
- **Layout**: Cards or tabs showing each participant's suggestion
- **Sub-components**:

  ##### `ParticipantSuggestionCard`
  - **Type**: Card component
  - **Props**: `userID`, `suggestion` (array of VibecationDay)
  - **Content**:
    - Participant name/avatar
    - Collapsible itinerary preview
    - Summary stats (number of days, activities, locations)
  - **API Call**: `GET /users/{userID}` for participant info

#### `PollingSection`
- **Type**: Section component
- **Layout**: Tabbed interface or accordion for different poll types
- **Sub-components**:

  ##### `ActivityPoll`
  - **Type**: Poll component
  - **Props**: `tripID`, `activities` (from API)
  - **Content**:
    - List of activities with voting buttons
    - Each activity shows:
      - Activity name and description
      - Upvote/Downvote buttons
      - Current vote count
      - User's current vote (highlighted)
  - **API Calls**:
    - `GET /polls/get/activity?tripID={tripID}` to fetch activities
    - `POST /polls/vote/activity` to submit vote
  - **Real-time Updates**: Poll results update when votes are cast

  ##### `LocationPoll`
  - **Type**: Poll component
  - **Props**: `tripID`, `locations` (from API)
  - **Content**: Similar to ActivityPoll but for locations
  - **API Calls**:
    - `GET /polls/get/location?tripID={tripID}`
    - `POST /polls/vote/location`

  ##### `ActivityVigorPoll`
  - **Type**: Poll component
  - **Props**: `tripID`, `vigorPreferences` (from API)
  - **Content**:
    - Activities with vigor level selector (low/medium/high)
    - Visual indicators for vigor levels
    - Shows aggregated preferences
  - **API Call**: `GET /polls/get/activity_vigor?tripID={tripID}`

  ##### `FoodCuisinePoll`
  - **Type**: Poll component
  - **Props**: `tripID`, `cuisines` (from API)
  - **Content**:
    - List of cuisine options
    - Multi-select checkboxes
    - Shows most popular cuisines
  - **API Call**: `GET /polls/get/food_cuisines?tripID={tripID}`

#### `PollProgressIndicator`
- **Type**: Progress component
- **Location**: Top of polling section
- **Content**: 
  - Progress bar showing completion percentage
  - List of completed/incomplete polls
  - "All polls complete" message when done

#### `PollTabNavigation`
- **Type**: Tab component
- **Tabs**: Activities, Locations, Activity Vigor, Food Cuisines
- **Functionality**: Switch between different poll types

---

## 5. Trip Details Configuration Page (`/trips/{tripID}/details`)

### Layout
- **Multi-section form layout**
- **Save button** at bottom (sticky)

### Components

#### `DetailsHeader`
- **Type**: Header component
- **Content**:
  - Trip title
  - "Back to Overview" button
  - Save status indicator

#### `AccommodationSection`
- **Type**: Form section component
- **Fields**:
  - Accommodation name (text input)
  - Accommodation type (select: hotel, apartment, hostel, etc.)
  - Check-in date (date picker)
  - Check-out date (date picker)
  - Address (text input)
  - Notes (textarea)
- **Note**: API endpoints not yet available

#### `TransportationSection`
- **Type**: Form section component
- **Sub-sections**:

  ##### `FlightsSubsection`
  - **Fields**:
    - Outbound flight (departure/arrival airports, date, time, airline, flight number)
    - Return flight (same fields)
    - Booking reference (text input)
    - Confirmation number (text input)

  ##### `GroundTransportSubsection`
  - **Fields**:
    - Rental car (checkbox, details if checked)
    - Public transport passes (multi-select)
    - Other transportation notes (textarea)

#### `TravelDocumentsSection`
- **Type**: Form section component
- **Fields**:
  - Passport requirements (checkbox list)
  - Visa requirements (checkbox list)
  - Travel insurance (checkbox, policy number)
  - Emergency contacts (repeating fields)

#### `BudgetSection`
- **Type**: Form section component
- **Fields**:
  - Total budget (number input with currency)
  - Budget breakdown by category (accommodation, food, activities, transport)
  - Expense tracker (optional, table component)

#### `AdditionalDetailsSection`
- **Type**: Form section component
- **Fields**:
  - Packing list (textarea or tag input)
  - Important notes (textarea)
  - Weather information (read-only, if API available)
  - Time zone information (read-only)

#### `SaveButton`
- **Type**: Button component
- **Location**: Sticky footer or bottom of form
- **Functionality**:
  - Validates form
  - Shows loading state
  - Displays success/error message
  - **Note**: API endpoints not yet available, so this would be a placeholder

---

## 6. Trip Overview Page (`/trips/{tripID}/overview`)

### Layout
- **Hero Section**: Trip title, countdown, key info
- **Main Content**: Itinerary timeline view
- **Sidebar**: Quick actions and trip info

### Components

#### `TripOverviewHeader`
- **Type**: Hero section component
- **Content**:
  - Trip title (large heading)
  - Trip description
  - Trip dates (start - end)
  - Primary destination location

#### `CountdownClock`
- **Type**: Countdown component
- **Props**: `targetDate` (trip start date)
- **Display**:
  - Large, prominent countdown
  - Format: "X days, Y hours, Z minutes until departure"
  - Visual: Circular progress or large numbers
  - Updates in real-time (every minute)
- **States**:
  - **Before trip**: Countdown to start
  - **During trip**: "Day X of Y" or "X days remaining"
  - **After trip**: "Trip completed" or "X days since trip"

#### `ItineraryTimeline`
- **Type**: Timeline component
- **Layout**: Vertical timeline with days as sections
- **Sub-components**:

  ##### `DayTimelineItem`
  - **Type**: Timeline node component
  - **Props**: `day` (VibecationDay object), `dayNumber`
  - **Content**:
    - Day number and date (left side)
    - Location name
    - Activities list (collapsible)
    - Time markers for each activity
  - **Styling**: 
    - Vertical line connecting days
    - Color-coded by day
    - Expandable/collapsible activities

  ##### `ActivityTimelineItem`
  - **Type**: Timeline sub-item component
  - **Props**: `activity` (Activity object)
  - **Content**:
    - Time range (from_date_time to to_date_time)
    - Activity name
    - Activity type icon/badge
    - Location name
    - Brief description (tooltip or expandable)
  - **Click Action**: Show activity details modal

#### `TripInfoSidebar`
- **Type**: Sidebar component
- **Content**:

  ##### `TripMembers`
  - **Type**: List component
  - **Content**: 
    - List of member avatars/names
    - "Add member" button (if user is trip owner)
  - **API Call**: `GET /tripinfo?tripID={tripID}` for members list

  ##### `QuickActions`
  - **Type**: Button group component
  - **Actions**:
    - "Edit Trip" (navigates to edit page)
    - "View Suggestions" (navigates to suggestions page)
    - "Configure Details" (navigates to details page)
    - "Share Trip" (copy link or share modal)
    - "Export Itinerary" (PDF/download)

  ##### `TripStats`
  - **Type**: Stats component
  - **Content**:
    - Total days
    - Total activities
    - Locations visited
    - Budget (if set)

#### `ActivityDetailModal`
- **Type**: Modal component
- **Trigger**: Click on activity in timeline
- **Content**:
  - Full activity details
  - Map view (if coordinates available)
  - Edit button (if user has permissions)
  - Close button

#### `MapView` (Optional)
- **Type**: Map component
- **Location**: Tab or toggle in overview
- **Content**: 
  - Interactive map showing all trip locations
  - Markers for each activity/location
  - Route visualization (if applicable)
- **Library**: Google Maps, Mapbox, or Leaflet

---

## Shared Components

### `NavigationBar`
- **Type**: Global navigation component
- **Content**:
  - Logo (links to dashboard)
  - User menu (profile, settings, logout)
  - Notifications icon (optional)

### `LoadingSpinner`
- **Type**: Loading indicator component
- **Usage**: Show during API calls
- **Variants**: Full page, inline, button-sized

### `ErrorMessage`
- **Type**: Error display component
- **Props**: `message`, `onRetry` (optional)
- **Styling**: Red/error color scheme
- **Content**: Error message with optional retry button

### `SuccessNotification`
- **Type**: Toast/notification component
- **Props**: `message`, `duration`
- **Behavior**: Auto-dismiss after duration
- **Location**: Top-right corner or bottom

### `ConfirmDialog`
- **Type**: Modal component
- **Usage**: Confirm destructive actions (delete trip, remove member)
- **Content**: 
  - Message
  - "Cancel" button
  - "Confirm" button (destructive styling)

---

## Routing Structure

```
/login
/register
/dashboard
/trips/{tripID}
  /brainstorm
  /suggestions
  /details
  /overview
  /edit
```

---

## State Management Recommendations

- **User State**: Current user ID, authentication status
- **Trip State**: Current trip data, trip list
- **Chat State**: Chat messages, current suggestion
- **Poll State**: Poll results, user votes
- **UI State**: Loading states, error messages, modals

---

## Styling Guidelines

- **Color Scheme**: Travel-themed (blues, greens, warm accents)
- **Typography**: Clean, readable sans-serif
- **Spacing**: Consistent spacing scale (4px, 8px, 16px, 24px, 32px)
- **Responsive**: Mobile-first approach
- **Accessibility**: WCAG 2.1 AA compliance
- **Icons**: Consistent icon library (Material Icons, Font Awesome, or custom)

---

## Technology Stack Suggestions

- **Framework**: React, Vue, or Angular
- **State Management**: Redux, Zustand, or Context API
- **Routing**: React Router, Vue Router, or Angular Router
- **UI Library**: Material-UI, Ant Design, or Tailwind CSS
- **Forms**: React Hook Form, Formik, or VeeValidate
- **HTTP Client**: Axios or Fetch API
- **Date/Time**: date-fns, moment.js, or day.js
- **Maps**: Google Maps API, Mapbox, or Leaflet

