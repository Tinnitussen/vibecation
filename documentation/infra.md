# Infrastructure & Docker Compose Setup

## Overview
This document describes the Docker Compose configuration for running the Vibecation application stack locally or in development environments.

## Architecture

```
┌─────────────┐
│  Frontend   │ (Port 3000)
│  (React)    │
└──────┬──────┘
       │
       │ HTTP
       │
┌──────▼──────┐
│   Backend   │ (Port 8000)
│  (FastAPI)  │
└──────┬──────┘
       │
       ├──────────────┬──────────────┐
       │              │              │
┌──────▼──────┐ ┌─────▼─────┐ ┌─────▼─────┐
│  MongoDB    │ │   Redis   │ │  (Future) │
│  (27017)    │ │  (6379)   │ │   LLM API │
└─────────────┘ └───────────┘ └───────────┘
```

---

## Docker Compose Configuration

### File: `docker-compose.yml`

```yaml
version: '3.8'

services:
  # MongoDB Database
  mongodb:
    image: mongo:7.0
    container_name: vibecation-mongodb
    restart: unless-stopped
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_ROOT_USERNAME:-admin}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_ROOT_PASSWORD:-changeme}
      MONGO_INITDB_DATABASE: ${MONGO_DATABASE:-vibecation}
    volumes:
      - mongodb_data:/data/db
      - mongodb_config:/data/configdb
      - ./scripts/mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro
    networks:
      - vibecation-network
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/test --quiet
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 40s

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: vibecation-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD:-changeme}
    volumes:
      - redis_data:/data
    networks:
      - vibecation-network
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  # Backend API Service
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: vibecation-backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      # Database
      MONGODB_URL: mongodb://${MONGO_ROOT_USERNAME:-admin}:${MONGO_ROOT_PASSWORD:-changeme}@mongodb:27017/${MONGO_DATABASE:-vibecation}?authSource=admin
      MONGODB_DATABASE: ${MONGO_DATABASE:-vibecation}
      
      # Redis
      REDIS_URL: redis://:${REDIS_PASSWORD:-changeme}@redis:6379/0
      REDIS_HOST: redis
      REDIS_PORT: 6379
      REDIS_PASSWORD: ${REDIS_PASSWORD:-changeme}
      
      # Application
      ENVIRONMENT: ${ENVIRONMENT:-development}
      DEBUG: ${DEBUG:-true}
      SECRET_KEY: ${SECRET_KEY:-change-this-secret-key-in-production}
      API_HOST: 0.0.0.0
      API_PORT: 8000
      
      # CORS
      CORS_ORIGINS: ${CORS_ORIGINS:-http://localhost:3000,http://localhost:3001}
      
      # JWT (if using)
      JWT_SECRET: ${JWT_SECRET:-change-this-jwt-secret}
      JWT_ALGORITHM: ${JWT_ALGORITHM:-HS256}
      JWT_EXPIRATION: ${JWT_EXPIRATION:-3600}
      
      # Azure OpenAI
      AZURE_OPENAI_ENDPOINT: ${AZURE_OPENAI_ENDPOINT:-}
      AZURE_OPENAI_API_KEY: ${AZURE_OPENAI_API_KEY:-}
      AZURE_OPENAI_API_VERSION: ${AZURE_OPENAI_API_VERSION:-2024-02-15-preview}
      AZURE_OPENAI_DEPLOYMENT_NAME: ${AZURE_OPENAI_DEPLOYMENT_NAME:-gpt-4}
      AZURE_OPENAI_MODEL: ${AZURE_OPENAI_MODEL:-gpt-4}
      AZURE_OPENAI_TEMPERATURE: ${AZURE_OPENAI_TEMPERATURE:-0.7}
      AZURE_OPENAI_MAX_TOKENS: ${AZURE_OPENAI_MAX_TOKENS:-2000}
      
      # Legacy LLM API (if not using Azure OpenAI)
      LLM_API_URL: ${LLM_API_URL:-}
      LLM_API_KEY: ${LLM_API_KEY:-}
    volumes:
      - ./backend:/app
      - backend_uploads:/app/uploads
    networks:
      - vibecation-network
    depends_on:
      mongodb:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Frontend Service
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: vibecation-frontend
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      REACT_APP_API_URL: ${REACT_APP_API_URL:-http://localhost:8000}
      REACT_APP_ENVIRONMENT: ${ENVIRONMENT:-development}
      NODE_ENV: ${NODE_ENV:-development}
    volumes:
      - ./frontend:/app
      - /app/node_modules
    networks:
      - vibecation-network
    depends_on:
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

volumes:
  mongodb_data:
    driver: local
  mongodb_config:
    driver: local
  redis_data:
    driver: local
  backend_uploads:
    driver: local

networks:
  vibecation-network:
    driver: bridge
```

---

## Environment Variables

### File: `.env.example`

Create a `.env` file in the project root with the following variables:

```bash
# ============================================
# Environment
# ============================================
ENVIRONMENT=development
DEBUG=true
NODE_ENV=development

# ============================================
# MongoDB Database
# ============================================
MONGO_ROOT_USERNAME=admin
MONGO_ROOT_PASSWORD=changeme
MONGO_DATABASE=vibecation

# MongoDB Connection String (auto-generated from above, or set manually)
# MONGODB_URL=mongodb://admin:changeme@mongodb:27017/vibecation?authSource=admin

# ============================================
# Redis Cache
# ============================================
REDIS_PASSWORD=changeme
REDIS_HOST=redis
REDIS_PORT=6379

# Redis Connection String (auto-generated from above, or set manually)
# REDIS_URL=redis://:changeme@redis:6379/0

# ============================================
# Backend API
# ============================================
SECRET_KEY=change-this-secret-key-in-production
API_HOST=0.0.0.0
API_PORT=8000

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# ============================================
# JWT Authentication
# ============================================
JWT_SECRET=change-this-jwt-secret-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600

# ============================================
# Azure OpenAI
# ============================================
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_API_KEY=your-azure-openai-api-key-here
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_MODEL=gpt-4

# Optional: Azure OpenAI configuration
AZURE_OPENAI_TEMPERATURE=0.7
AZURE_OPENAI_MAX_TOKENS=2000
AZURE_OPENAI_TOP_P=1.0

# ============================================
# Frontend
# ============================================
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENVIRONMENT=development

# ============================================
# Legacy LLM API (if not using Azure OpenAI)
# ============================================
# LLM_API_URL=
# LLM_API_KEY=
```

**Important**: 
- Never commit the actual `.env` file to version control. Always use `.env.example` as a template.
- Replace all placeholder values with your actual secrets before running the application.
- For Azure OpenAI, get your endpoint and API key from the Azure Portal.

---

## MongoDB Initialization Script

### File: `scripts/mongo-init.js`

This script initializes the database with indexes and initial setup:

```javascript
// MongoDB initialization script
// This runs automatically when MongoDB container starts for the first time

db = db.getSiblingDB('vibecation');

// Create collections with validation (optional)
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
db.votes.createIndex({ "voteID": 1 }, { unique: true });
db.votes.createIndex({ "pollID": 1, "userID": 1, "optionID": 1 }, { unique: true });
db.votes.createIndex({ "tripID": 1, "userID": 1 });

// Create indexes for locations collection
db.locations.createIndex({ "locationID": 1 }, { unique: true });
db.locations.createIndex({ "lat": 1, "lon": 1 });
db.locations.createIndex({ "name": 1 });

// Create indexes for chat_messages collection
db.chat_messages.createIndex({ "messageID": 1 }, { unique: true });
db.chat_messages.createIndex({ "tripID": 1, "createdAt": -1 });

// Create indexes for audit_logs collection
db.audit_logs.createIndex({ "logID": 1 }, { unique: true });
db.audit_logs.createIndex({ "collectionName": 1, "timestamp": -1 });
db.audit_logs.createIndex({ "userID": 1, "timestamp": -1 });

// Initialize ID counters
db.id_counters.insertMany([
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

print('Database initialized successfully!');
```

---

## Dockerfile Examples

### Backend Dockerfile: `backend/Dockerfile`

```dockerfile
# Backend Dockerfile (Python/FastAPI example)
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p /app/uploads

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### Frontend Dockerfile: `frontend/Dockerfile`

```dockerfile
# Frontend Dockerfile (React example)
FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# Run development server
CMD ["npm", "start"]
```

### Frontend Dockerfile (Production): `frontend/Dockerfile.prod`

```dockerfile
# Multi-stage build for production
FROM node:18-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy and build
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

---

## Nginx Configuration (Production Frontend)

### File: `frontend/nginx.conf`

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

---

## Usage

### Starting the Stack

```bash
# Start all services
docker-compose up -d

# Start with build
docker-compose up -d --build

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mongodb
```

### Stopping the Stack

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```

### Accessing Services

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (if using FastAPI)
- **MongoDB**: localhost:27017
- **Redis**: localhost:6379

### Connecting to MongoDB

```bash
# Using mongosh
docker exec -it vibecation-mongodb mongosh -u admin -p changeme

# Or using connection string
mongodb://admin:changeme@localhost:27017/vibecation?authSource=admin
```

### Connecting to Redis

```bash
# Using redis-cli
docker exec -it vibecation-redis redis-cli -a changeme

# Or using connection string
redis://:changeme@localhost:6379/0
```

---

## Development Workflow

### Hot Reload

Both frontend and backend are configured for hot reload during development:
- **Backend**: Uses `--reload` flag in uvicorn
- **Frontend**: Uses `npm start` with volume mounting

### Database Migrations

```bash
# Run migrations (example)
docker-compose exec backend python manage.py migrate

# Or if using Alembic
docker-compose exec backend alembic upgrade head
```

### Running Tests

```bash
# Backend tests
docker-compose exec backend pytest

# Frontend tests
docker-compose exec frontend npm test
```

### Accessing Container Shells

```bash
# Backend shell
docker-compose exec backend bash

# Frontend shell
docker-compose exec frontend sh

# MongoDB shell
docker-compose exec mongodb mongosh -u admin -p changeme
```

---

## Production Considerations

### Security

1. **Change all default passwords** in `.env`
2. **Use strong secrets** for `SECRET_KEY` and `JWT_SECRET`
3. **Enable MongoDB authentication** (already configured)
4. **Use Redis password** (already configured)
5. **Restrict CORS origins** to production domains
6. **Use HTTPS** in production (add reverse proxy)
7. **Enable firewall rules** to restrict database access

### Scaling

```yaml
# Example: Scale backend services
docker-compose up -d --scale backend=3

# Use load balancer (nginx/traefik) in front
```

### Monitoring

Add monitoring services:

```yaml
  # Prometheus (optional)
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  # Grafana (optional)
  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### Backup

```bash
# Backup MongoDB
docker-compose exec mongodb mongodump --out /backup --username admin --password changeme --authenticationDatabase admin

# Backup Redis
docker-compose exec redis redis-cli --rdb /data/dump.rdb -a changeme
```

---

## Troubleshooting

### Services won't start

```bash
# Check logs
docker-compose logs

# Check service status
docker-compose ps

# Restart specific service
docker-compose restart backend
```

### Database connection issues

```bash
# Verify MongoDB is healthy
docker-compose exec mongodb mongosh -u admin -p changeme --eval "db.adminCommand('ping')"

# Check network connectivity
docker-compose exec backend ping mongodb
```

### Port conflicts

If ports are already in use, modify the port mappings in `docker-compose.yml`:

```yaml
ports:
  - "8001:8000"  # Change host port
```

### Volume permissions

```bash
# Fix volume permissions (Linux)
sudo chown -R $USER:$USER ./volumes
```

---

## Additional Services (Optional)

### Redis Commander (Redis GUI)

```yaml
  redis-commander:
    image: rediscommander/redis-commander:latest
    container_name: vibecation-redis-commander
    environment:
      REDIS_HOSTS: local:redis:6379
      REDIS_PASSWORD: ${REDIS_PASSWORD:-changeme}
    ports:
      - "8081:8081"
    networks:
      - vibecation-network
    depends_on:
      - redis
```

### Mongo Express (MongoDB GUI)

```yaml
  mongo-express:
    image: mongo-express:latest
    container_name: vibecation-mongo-express
    ports:
      - "8082:8081"
    environment:
      ME_CONFIG_MONGODB_ADMINUSERNAME: ${MONGO_ROOT_USERNAME:-admin}
      ME_CONFIG_MONGODB_ADMINPASSWORD: ${MONGO_ROOT_PASSWORD:-changeme}
      ME_CONFIG_MONGODB_URL: mongodb://${MONGO_ROOT_USERNAME:-admin}:${MONGO_ROOT_PASSWORD:-changeme}@mongodb:27017/
    networks:
      - vibecation-network
    depends_on:
      - mongodb
```

---

## File Structure

```
vibecation/
├── docker-compose.yml
├── .env
├── .env.example
├── scripts/
│   └── mongo-init.js
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── ...
├── frontend/
│   ├── Dockerfile
│   ├── Dockerfile.prod
│   ├── nginx.conf
│   ├── package.json
│   └── ...
└── documentation/
    └── infra.md
```

---

## Azure OpenAI Setup

### Getting Azure OpenAI Credentials

1. **Create Azure OpenAI Resource**
   - Go to [Azure Portal](https://portal.azure.com)
   - Create a new "Azure OpenAI" resource
   - Note your resource name and region

2. **Get API Key**
   - Navigate to your Azure OpenAI resource
   - Go to "Keys and Endpoint" section
   - Copy one of the API keys

3. **Get Endpoint URL**
   - In the same "Keys and Endpoint" section
   - Copy the endpoint URL (format: `https://your-resource-name.openai.azure.com/`)

4. **Create Deployment**
   - Go to "Model deployments" section
   - Deploy a model (e.g., gpt-4, gpt-35-turbo)
   - Note the deployment name

5. **Update .env file**
   ```bash
   AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
   AZURE_OPENAI_API_KEY=your-actual-api-key-here
   AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name
   AZURE_OPENAI_MODEL=gpt-4
   ```

### Testing Azure OpenAI Connection

```bash
# Test from backend container
docker-compose exec backend python -c "
import os
from openai import AzureOpenAI

client = AzureOpenAI(
    api_key=os.getenv('AZURE_OPENAI_API_KEY'),
    api_version=os.getenv('AZURE_OPENAI_API_VERSION'),
    azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
)

response = client.chat.completions.create(
    model=os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME'),
    messages=[{'role': 'user', 'content': 'Hello!'}]
)
print(response.choices[0].message.content)
"
```

---

## Quick Start

1. **Clone repository**
   ```bash
   git clone <repository-url>
   cd vibecation
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your values
   # IMPORTANT: Update all secrets, especially:
   # - MongoDB passwords
   # - Redis password
   # - SECRET_KEY and JWT_SECRET
   # - Azure OpenAI credentials (if using)
   ```

3. **Start services**
   ```bash
   docker-compose up -d --build
   ```

4. **Verify services**
   ```bash
   docker-compose ps
   ```

5. **Access application**
   - Frontend: http://localhost:3000
   - Backend: http://localhost:8000
   - API Docs: http://localhost:8000/docs

---

## Notes

- All services use health checks to ensure proper startup order
- Data is persisted in Docker volumes
- Development mode includes hot reload for both frontend and backend
- Production builds should use multi-stage Dockerfiles
- Always use `.env.example` as a template, never commit `.env`

