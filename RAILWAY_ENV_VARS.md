# Railway Environment Variables Setup Guide

## Architecture Overview

- **Frontend**: Publicly exposed (browser-accessible)
- **Backend**: Can use internal network for MongoDB, but needs public URL for frontend
- **MongoDB**: Private (internal network only)

**Note:** Since the frontend runs in the browser, it cannot use Railway's internal network. The frontend must connect to the backend via its public URL. However, the backend can use Railway's internal network to connect to MongoDB.

---

## Service 1: MongoDB

### Service Name
`MongoDB` (or whatever you name it)

### Variables Tab

**If using Railway MongoDB Plugin:**
- Railway automatically provides: `MONGO_URL` or `MONGODB_URL`
- No additional variables needed

**If using MongoDB Container:**
```
MONGO_INITDB_DATABASE=vibecation
```

### Internal Network Access
- **Internal Hostname:** `${{ MongoDB.MONGO_URL }}` (Railway reference)
- **Or use:** `mongodb.railway.internal` (if service name is "mongodb")
- **Port:** `27017`

### Settings
- **Public URL:** ❌ Disabled (keep private)
- **Port:** `27017` (internal only)

---

## Service 2: Backend

### Service Name
`Backend` (or `vibecation-backend`)

### Variables Tab

```bash
# MongoDB Connection (using Railway internal network)
MONGODB_URL=${{ MongoDB.MONGO_URL }}

# OR if MongoDB service is named differently, use:
# MONGODB_URL=mongodb://mongodb.railway.internal:27017/vibecation
# Or use the service reference: ${{ MongoDB.MONGO_URL }}

# Azure OpenAI (your credentials)
AZURE_OPENAI_API_KEY=your-azure-openai-api-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# CORS - Allow frontend's public URL
CORS_ORIGINS=https://your-frontend-service.railway.app

# Optional: Python path
PYTHONPATH=/app
```

### Internal Network Access
- **Internal Hostname:** `backend.railway.internal` or `diligent-learning.railway.internal` (your service name)
- **Port:** `8000`

### Settings
- **Root Directory:** `backend`
- **Dockerfile Path:** `Dockerfile.railway`
- **Port:** `8000`
- **Public URL:** ✅ Enabled (needed for frontend in browser)
- **Generate Domain:** ✅ Enabled

### Important Notes
- Backend needs a **public URL** because the frontend (running in browser) needs to access it
- Backend uses **internal network** to connect to MongoDB
- CORS must allow the frontend's public URL

---

## Service 3: Frontend

### Service Name
`Frontend` (or `vibecation-frontend`)

### Variables Tab

```bash
# Backend API URL - Use backend's PUBLIC URL (browser can't use internal network)
VITE_API_URL=https://your-backend-service.railway.app

# Example if your backend service is named "diligent-learning":
# VITE_API_URL=https://diligent-learning-production.up.railway.app
```

### Settings
- **Root Directory:** `frontend`
- **Dockerfile Path:** `Dockerfile.railway`
- **Port:** `80`
- **Public URL:** ✅ Enabled
- **Generate Domain:** ✅ Enabled
- **Build Args:** 
  - Add: `VITE_API_URL=$VITE_API_URL`

### Important Notes
- Frontend runs in the **browser**, so it **cannot** use Railway's internal network
- Must use backend's **public URL** (not internal hostname)
- The `VITE_API_URL` is baked into the build at build time

---

## Railway Service References

Railway provides service references you can use in variables:

### Syntax
```
${{ ServiceName.VARIABLE_NAME }}
```

### Examples

**MongoDB Connection:**
```bash
# If MongoDB service is named "MongoDB"
MONGODB_URL=${{ MongoDB.MONGO_URL }}

# This automatically resolves to the internal connection string
```

**Backend URL (for frontend):**
```bash
# If Backend service is named "Backend"
VITE_API_URL=${{ Backend.RAILWAY_PUBLIC_DOMAIN }}

# OR use the full URL format:
VITE_API_URL=https://${{ Backend.RAILWAY_PUBLIC_DOMAIN }}
```

### Available Railway Variables

For each service, Railway provides:
- `RAILWAY_PUBLIC_DOMAIN` - Public domain (e.g., `service-name.up.railway.app`)
- `RAILWAY_ENVIRONMENT` - Environment name
- `RAILWAY_SERVICE_NAME` - Service name
- `RAILWAY_PROJECT_NAME` - Project name

For MongoDB plugin:
- `MONGO_URL` - Full connection string
- `MONGO_HOST` - Hostname
- `MONGO_PORT` - Port
- `MONGO_DATABASE` - Database name

---

## Complete Setup Example

### Step 1: Create MongoDB Service
1. Add MongoDB plugin
2. Service name: `MongoDB`
3. Variables: None needed (auto-provided)
4. Public URL: ❌ Disabled

### Step 2: Create Backend Service
1. Add GitHub repo service
2. Service name: `Backend`
3. Root Directory: `backend`
4. Dockerfile: `Dockerfile.railway`
5. Port: `8000`
6. Variables:
   ```
   MONGODB_URL=${{ MongoDB.MONGO_URL }}
   AZURE_OPENAI_API_KEY=sk-...
   AZURE_OPENAI_ENDPOINT=https://...
   AZURE_OPENAI_API_VERSION=2024-02-15-preview
   CORS_ORIGINS=https://${{ Frontend.RAILWAY_PUBLIC_DOMAIN }}
   ```
7. Public URL: ✅ Enabled
8. Generate Domain: ✅ Enabled

### Step 3: Create Frontend Service
1. Add GitHub repo service
2. Service name: `Frontend`
3. Root Directory: `frontend`
4. Dockerfile: `Dockerfile.railway`
5. Port: `80`
6. Variables:
   ```
   VITE_API_URL=https://${{ Backend.RAILWAY_PUBLIC_DOMAIN }}
   ```
7. Build Args (in Settings → Build):
   ```
   VITE_API_URL=$VITE_API_URL
   ```
8. Public URL: ✅ Enabled
9. Generate Domain: ✅ Enabled

---

## Network Flow Diagram

```
Browser (User)
    ↓ (HTTPS)
Frontend (Public URL: https://frontend.railway.app)
    ↓ (HTTPS - Public)
Backend (Public URL: https://backend.railway.app)
    ↓ (Internal Network - Private)
MongoDB (Internal: mongodb.railway.internal:27017)
```

---

## Troubleshooting

### Frontend can't reach backend
- ✅ Check `VITE_API_URL` is set to backend's **public URL**
- ✅ Check backend's public URL is enabled
- ✅ Check CORS allows frontend's domain
- ❌ Don't use internal hostnames in `VITE_API_URL` (browser can't access them)

### Backend can't reach MongoDB
- ✅ Use `${{ MongoDB.MONGO_URL }}` or internal hostname
- ✅ Check MongoDB service name matches the reference
- ✅ Verify MongoDB is running and healthy
- ✅ Don't use `localhost` or public URLs for MongoDB

### CORS errors
- ✅ Add frontend's public URL to `CORS_ORIGINS`
- ✅ Use `https://` not `http://` for production
- ✅ No trailing slash in CORS origins

---

## Quick Reference: Variable Checklist

### MongoDB Service
- [ ] Service name set (e.g., `MongoDB`)
- [ ] Public URL disabled
- [ ] Connection string available via `${{ MongoDB.MONGO_URL }}`

### Backend Service
- [ ] `MONGODB_URL=${{ MongoDB.MONGO_URL }}`
- [ ] `AZURE_OPENAI_API_KEY` set
- [ ] `AZURE_OPENAI_ENDPOINT` set
- [ ] `AZURE_OPENAI_API_VERSION` set
- [ ] `CORS_ORIGINS` includes frontend's public URL
- [ ] Public URL enabled
- [ ] Root Directory: `backend`
- [ ] Dockerfile: `Dockerfile.railway`

### Frontend Service
- [ ] `VITE_API_URL` set to backend's public URL
- [ ] Build arg `VITE_API_URL=$VITE_API_URL` set
- [ ] Public URL enabled
- [ ] Root Directory: `frontend`
- [ ] Dockerfile: `Dockerfile.railway`





