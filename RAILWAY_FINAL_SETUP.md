# Railway Setup: Final Configuration

## Architecture Summary

```
Browser → Frontend (Public) → Backend (Public URL, but can use internal for MongoDB) → MongoDB (Internal Only)
```

**Key Points:**
- Frontend is publicly accessible
- Backend has a public URL (browser needs it) but uses internal network for MongoDB
- MongoDB is private (internal network only)
- Frontend → Backend: Public URL (browser limitation)
- Backend → MongoDB: Internal network (Railway service reference)

---

## Service Configuration

### 1. MongoDB Service

**Settings:**
- Service Name: `MongoDB`
- Type: Database → MongoDB Plugin
- Public URL: ❌ **DISABLED**

**Variables:**
- None needed (Railway auto-provides `MONGO_URL`)

**Internal Access:**
- Other services can use: `${{ MongoDB.MONGO_URL }}`

---

### 2. Backend Service

**Settings:**
- Service Name: `Backend`
- Source: GitHub Repo
- Root Directory: `backend`
- Dockerfile Path: `Dockerfile.railway`
- Port: `8000`
- Public URL: ✅ **ENABLED**
- Generate Domain: ✅ **ENABLED**

**Variables Tab:**
```bash
MONGODB_URL=${{ MongoDB.MONGO_URL }}
AZURE_OPENAI_API_KEY=your-actual-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-02-15-preview
CORS_ORIGINS=https://${{ Frontend.RAILWAY_PUBLIC_DOMAIN }}
PYTHONPATH=/app
```

**Notes:**
- `MONGODB_URL` uses Railway's internal network (private, secure)
- `CORS_ORIGINS` uses service reference to automatically get frontend's URL
- Backend needs public URL because browser needs to access it

---

### 3. Frontend Service

**Settings:**
- Service Name: `Frontend`
- Source: GitHub Repo
- Root Directory: `frontend`
- Dockerfile Path: `Dockerfile.railway`
- Port: `80`
- Public URL: ✅ **ENABLED**
- Generate Domain: ✅ **ENABLED**

**Variables Tab:**
```bash
VITE_API_URL=https://${{ Backend.RAILWAY_PUBLIC_DOMAIN }}
```

**Settings → Build → Build Command Arguments:**
```bash
VITE_API_URL=$VITE_API_URL
```

**Notes:**
- Frontend **must** use backend's public URL (browser can't use internal network)
- `VITE_API_URL` is baked into the build, so it needs to be a build argument
- Railway service reference automatically resolves to backend's public domain

---

## Railway Service References Explained

Railway allows services to reference each other using `${{ ServiceName.VARIABLE }}` syntax.

### How It Works:

1. **MongoDB → Backend:**
   ```bash
   MONGODB_URL=${{ MongoDB.MONGO_URL }}
   ```
   - Railway resolves this to: `mongodb://user:pass@mongodb.railway.internal:27017/railway`
   - Uses internal network (private, fast, secure)

2. **Backend → Frontend (for CORS):**
   ```bash
   CORS_ORIGINS=https://${{ Frontend.RAILWAY_PUBLIC_DOMAIN }}
   ```
   - Railway resolves this to: `https://frontend-production.up.railway.app`
   - Used for CORS configuration

3. **Frontend → Backend:**
   ```bash
   VITE_API_URL=https://${{ Backend.RAILWAY_PUBLIC_DOMAIN }}
   ```
   - Railway resolves this to: `https://backend-production.up.railway.app`
   - Frontend uses this to make API calls from the browser

---

## Setup Steps in Railway UI

### Step 1: Create MongoDB
1. Click **"+ New"** → **"Database"** → **"Add MongoDB"**
2. Service name will be `MongoDB` (or rename it to this)
3. Go to Settings → Disable Public URL
4. Done! Railway provides `MONGO_URL` automatically

### Step 2: Create Backend
1. Click **"+ New"** → **"GitHub Repo"**
2. Select your repo and branch
3. Settings:
   - Root Directory: `backend`
   - Dockerfile: `Dockerfile.railway`
   - Port: `8000`
   - Enable Public URL
4. Variables: Copy the block from above
5. Deploy

### Step 3: Create Frontend
1. Click **"+ New"** → **"GitHub Repo"**
2. Select your repo and branch
3. Settings:
   - Root Directory: `frontend`
   - Dockerfile: `Dockerfile.railway`
   - Port: `80`
   - Enable Public URL
4. Variables: `VITE_API_URL=https://${{ Backend.RAILWAY_PUBLIC_DOMAIN }}`
5. Build Args: `VITE_API_URL=$VITE_API_URL`
6. Deploy

### Step 4: Verify CORS
1. After frontend deploys, check backend variables
2. Verify `CORS_ORIGINS` has frontend's URL
3. If not, Railway should have auto-resolved it via service reference

---

## Network Flow

```
┌─────────────────────────────────────────────────────────┐
│                    User's Browser                       │
│  (Cannot access Railway internal network)                │
└────────────────────┬────────────────────────────────────┘
                     │ HTTPS (Public Internet)
                     ↓
┌─────────────────────────────────────────────────────────┐
│              Frontend Service (Public)                   │
│  URL: https://frontend-production.up.railway.app        │
│  Internal: frontend.railway.internal                    │
└────────────────────┬────────────────────────────────────┘
                     │ HTTPS (Public - Browser limitation)
                     ↓
┌─────────────────────────────────────────────────────────┐
│              Backend Service (Public URL)                │
│  Public URL: https://backend-production.up.railway.app  │
│  Internal: backend.railway.internal:8000                │
└────────────────────┬────────────────────────────────────┘
                     │ Internal Network (Private, Fast)
                     │ mongodb://mongodb.railway.internal:27017
                     ↓
┌─────────────────────────────────────────────────────────┐
│            MongoDB Service (Private)                     │
│  Internal: mongodb.railway.internal:27017               │
│  No Public URL                                           │
└─────────────────────────────────────────────────────────┘
```

---

## Why This Setup?

### ✅ Benefits:
1. **MongoDB is private** - Only accessible via Railway's internal network
2. **Backend uses internal network for MongoDB** - Fast, secure, no public exposure
3. **Frontend can reach backend** - Uses public URL (browser requirement)
4. **Service references** - Automatic URL resolution, no manual updates needed
5. **CORS automatically configured** - Service reference ensures correct frontend URL

### ⚠️ Limitations:
- Frontend **must** use backend's public URL (browser can't access internal network)
- This is a browser security limitation, not a Railway limitation
- The backend → MongoDB connection is still private and secure

---

## Verification

After setup, verify:

1. **MongoDB:**
   - [ ] Service running
   - [ ] Public URL disabled
   - [ ] `MONGO_URL` available in variables

2. **Backend:**
   - [ ] Service running
   - [ ] Public URL enabled and accessible
   - [ ] Variables set correctly
   - [ ] Can connect to MongoDB (check logs)

3. **Frontend:**
   - [ ] Service running
   - [ ] Public URL enabled and accessible
   - [ ] `VITE_API_URL` set correctly
   - [ ] Can make API calls to backend (check browser console)

4. **Integration:**
   - [ ] Frontend loads without errors
   - [ ] API calls work (check Network tab in browser)
   - [ ] No CORS errors
   - [ ] Backend can read/write to MongoDB

---

## Troubleshooting

### Service Reference Not Resolving
- Wait a few seconds after creating the service
- Check service names match exactly (case-sensitive)
- Service must be deployed before it can be referenced

### Frontend Can't Reach Backend
- Verify `VITE_API_URL` uses backend's public URL
- Check backend's public URL is enabled
- Verify CORS allows frontend's domain
- Check browser console for errors

### Backend Can't Reach MongoDB
- Verify `MONGODB_URL` uses service reference: `${{ MongoDB.MONGO_URL }}`
- Check MongoDB service name matches exactly
- Verify MongoDB is running (check service status)
- Check backend logs for connection errors

---

## Files Updated

All Railway configuration is done via the UI. The local files are:
- `Dockerfile.railway` (frontend and backend) - Already created
- `railway.json` - Minimal config
- Documentation files - For reference

No code changes needed - the existing code already uses environment variables correctly!



