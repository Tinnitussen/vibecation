# Vibecation - Vacation Planner

A fullstack vacation planning application built with React, FastAPI, and MongoDB.

## Project Structure

```
vibecation/
├── backend/              # FastAPI backend
│   ├── main.py          # FastAPI application entry point
│   ├── database.py      # MongoDB connection setup
│   ├── models.py        # Pydantic models
│   └── routers/         # API route handlers
│       └── trips.py     # Trip management routes
├── frontend/            # React frontend
│   ├── src/
│   │   ├── App.jsx      # Main React component
│   │   ├── App.css      # App styles
│   │   ├── main.jsx     # React entry point
│   │   └── index.css    # Global styles
│   ├── index.html
│   ├── package.json
│   └── vite.config.js   # Vite configuration
├── sample-data/         # Sample JSON data
├── documentation/       # Project documentation
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
└── README.md           # This file
```

## Prerequisites

- Python 3.8+
- Node.js 16+
- MongoDB (running locally or connection string)

## Setup Instructions

### 1. Backend Setup

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
```

Edit `.env` and configure your MongoDB connection:
```
MONGO_URL=mongodb://localhost:27017
MONGO_DB_NAME=vibecation
```

5. Start MongoDB (if running locally):
```bash
# Make sure MongoDB is running on your system
# On Windows with MongoDB installed:
# mongod

# Or use MongoDB Atlas connection string in .env
```

6. Run the FastAPI server:
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 2. Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file (optional, defaults to localhost:8000):
```bash
VITE_API_URL=http://localhost:8000
```

4. Start the development server:
```bash
npm run dev
```

The frontend will be available at http://localhost:5173

## API Endpoints

### Trips
- `GET /api/trips/` - Get all trips
- `GET /api/trips/{trip_id}` - Get a specific trip
- `POST /api/trips/` - Create a new trip
- `PUT /api/trips/{trip_id}` - Update a trip
- `DELETE /api/trips/{trip_id}` - Delete a trip

### Health
- `GET /health` - Health check endpoint
- `GET /` - Root endpoint with API info

## Development

### Backend Development
- The backend uses FastAPI with automatic reload on code changes
- Models are defined in `backend/models.py` using Pydantic
- Database operations use Motor (async MongoDB driver)

### Frontend Development
- The frontend uses Vite for fast development
- React components are in `frontend/src/`
- API calls are made using Axios

## Next Steps

This is a template application. You can now:
1. Add authentication and user management
2. Implement trip creation and editing UI
3. Add activity management features
4. Integrate maps and location services
5. Add calendar and scheduling features
6. Implement sharing and collaboration features

## License

MIT

