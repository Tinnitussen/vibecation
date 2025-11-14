# Quick Start Guide

## Prerequisites Check
- ✅ Python 3.8+ installed
- ✅ Node.js 16+ installed  
- ✅ MongoDB running (local or connection string)

## Quick Setup (5 minutes)

### 1. Backend Setup
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment (copy .env.example to .env and edit if needed)
# Default: mongodb://localhost:27017

# Run backend
python run_backend.py
# OR
uvicorn backend.main:app --reload
```

Backend runs on: http://localhost:8000
API Docs: http://localhost:8000/docs

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Frontend runs on: http://localhost:5173

## Verify It Works

1. Open http://localhost:5173 - You should see the Vibecation app
2. Open http://localhost:8000/docs - You should see the Swagger API documentation
3. Try the health endpoint: http://localhost:8000/health

## Common Issues

**MongoDB Connection Error:**
- Make sure MongoDB is running: `mongod` (or use MongoDB Atlas)
- Check your `.env` file has correct `MONGO_URL`

**Port Already in Use:**
- Backend: Change port in `run_backend.py` or use `--port 8001`
- Frontend: Vite will automatically use next available port

**Module Not Found:**
- Make sure virtual environment is activated
- Reinstall: `pip install -r requirements.txt`

