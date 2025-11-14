# Vibecation Travel Planner

A full-stack travel planning application with collaborative trip planning features.

## Project Structure

```
vibecation/
├── backend/          # FastAPI backend
├── frontend/         # React frontend
├── documentation/    # API and design documentation
└── docker-compose.yml
```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Running with Docker

1. Clone the repository
2. Run the following command:

```bash
docker-compose up --build
```

This will start:
- MongoDB on port 27017
- Backend API on port 8000
- Frontend on port 3000

### Accessing the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Local Development

#### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Features Implemented

### Pages 1, 1.5, and 2

- **Login Page** (`/login`): User authentication
- **Registration Page** (`/register`): New user registration with validation
- **Dashboard** (`/dashboard`): Trip management and overview

### API Endpoints

- `GET /login` - User login
- `POST /users` - Create new user
- `GET /users/check-availability` - Check username/email availability
- `GET /users/{userID}` - Get user profile
- `GET /dashboard` - Get user's trips
- `GET /tripinfo` - Get trip information
- `POST /createtrip` - Create new trip
- `DELETE /trips/{tripID}` - Delete trip

## Technology Stack

- **Backend**: FastAPI, Motor (MongoDB async driver), bcrypt
- **Frontend**: React, React Router, Axios, Vite
- **Database**: MongoDB
- **Containerization**: Docker, Docker Compose

## Style Guide

- Main background: Light (#FAFAFA/white)
- Details accent: Neon purple-pink (#FF00FF/#FF1493)
- See `documentation/frontend_layout.md` for complete style schema

