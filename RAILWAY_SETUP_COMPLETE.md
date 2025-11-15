# Complete Railway Setup with Private Network

## Understanding the Architecture

**Important:** The frontend runs in the user's browser, so it **cannot** use Railway's internal network. However, we can optimize the setup:

1. **Frontend → Backend**: Must use public URL (browser limitation)
2. **Backend → MongoDB**: Uses Railway's internal network (private, secure, fast)

---

## Step-by-Step Railway UI Setup

### 1. Create MongoDB Service

**Service Name:** `MongoDB`

1. Click **"+ New"** → **"Database"** → **"Add MongoDB"**
2. Railway creates the service automatically
3. Go to **Settings**:
   - **Public URL**: ❌ **Disable** (keep it private)
4. Go to **Variables** tab:
   - Note the `MONGO_URL` variable (you'll reference it in backend)

**Internal Access:**
- Railway provides: `${{ MongoDB.MONGO_URL }}`
- Or use: `mongodb.railway.internal:27017`

---

### 2. Create Backend Service

**Service Name:** `Backend` (or your preferred name)

1. Click **"+ New"** → **"GitHub Repo"**
2. Select your repository and branch
3. Go to **Settings** tab:
   - **Root Directory:** `backend`
   - **Dockerfile Path:** `Dockerfile.railway`
   - **Port:** `8000`
   - **Public URL**: ✅ **Enable** (needed for frontend)
   - **Generate Domain**: ✅ **Enable**
4. Go to **Settings** → **GitHub**:
   - **Branch:** Select your branch
   - **Auto Deploy**: ✅ Enable (optional)
5. Go to **Variables** tab, add:

```bash
# MongoDB - Use Railway's internal network reference
MONGODB_URL=${{ MongoDB.MONGO_URL }}

# Azure OpenAI
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# CORS - Will be updated after frontend is deployed
# For now, use a placeholder, then update with frontend's actual URL
CORS_ORIGINS=https://your-frontend-service.railway.app

# Python
PYTHONPATH=/app
```

**Important:** 
- `MONGODB_URL` uses Railway's service reference for internal network
- Backend has a public URL because the browser needs to access it
- CORS must allow the frontend's public domain

---

### 3. Create Frontend Service

**Service Name:** `Frontend` (or your preferred name)

1. Click **"+ New"** → **"GitHub Repo"**
2. Select your repository and branch (same as backend)
3. Go to **Settings** tab:
   - **Root Directory:** `frontend`
   - **Dockerfile Path:** `Dockerfile.railway`
   - **Port:** `80`
   - **Public URL**: ✅ **Enable**
   - **Generate Domain**: ✅ **Enable**
4. Go to **Settings** → **Build**:
   - **Build Command Arguments** or **Build Args**:
     ```
     VITE_API_URL=$VITE_API_URL
     ```
5. Go to **Settings** → **GitHub**:
   - **Branch:** Select your branch
   - **Auto Deploy**: ✅ Enable (optional)
6. Go to **Variables** tab, add:

```bash
# Backend URL - Use Railway service reference for backend's public URL
VITE_API_URL=https://${{ Backend.RAILWAY_PUBLIC_DOMAIN }}
```

**Important:**
- Frontend **must** use backend's **public URL** (browser limitation)
- `VITE_API_URL` is baked into the build, so it needs to be set before building
- Use Railway's service reference to automatically get backend's URL

---

### 4. Update CORS in Backend

After frontend is deployed and you have its URL:

1. Go to **Backend** service
2. Go to **Variables** tab
3. Update `CORS_ORIGINS`:
   ```bash
   CORS_ORIGINS=https://${{ Frontend.RAILWAY_PUBLIC_DOMAIN }}
   ```
   Or manually:
   ```bash
   CORS_ORIGINS=https://your-actual-frontend-url.railway.app
   ```
4. Railway will automatically redeploy

---

## Railway Service References

Railway allows you to reference other services using `${{ ServiceName.VARIABLE }}` syntax.

### For MongoDB Connection:
```bash
MONGODB_URL=${{ MongoDB.MONGO_URL }}
```
This automatically resolves to the internal connection string.

### For Backend URL (in Frontend):
```bash
VITE_API_URL=https://${{ Backend.RAILWAY_PUBLIC_DOMAIN }}
```
This automatically gets the backend's public domain.

### For Frontend URL (in Backend CORS):
```bash
CORS_ORIGINS=https://${{ Frontend.RAILWAY_PUBLIC_DOMAIN }}
```
This automatically gets the frontend's public domain.

---

## Complete Variable Reference

### MongoDB Service Variables
```
(Provided automatically by Railway)
MONGO_URL=mongodb://mongo:password@mongodb.railway.internal:27017/railway
```

### Backend Service Variables
```bash
# Internal network connection to MongoDB
MONGODB_URL=${{ MongoDB.MONGO_URL }}

# Your Azure OpenAI credentials
AZURE_OPENAI_API_KEY=sk-...
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# CORS - allow frontend
CORS_ORIGINS=https://${{ Frontend.RAILWAY_PUBLIC_DOMAIN }}

# Python
PYTHONPATH=/app
```

### Frontend Service Variables
```bash
# Backend public URL (browser needs public URL)
VITE_API_URL=https://${{ Backend.RAILWAY_PUBLIC_DOMAIN }}
```

### Frontend Build Args (in Settings → Build)
```bash
VITE_API_URL=$VITE_API_URL
```

---

## Network Architecture

```
┌─────────────┐
│   Browser   │
│  (User)     │
└──────┬──────┘
       │ HTTPS (Public)
       ↓
┌─────────────────────┐
│  Frontend Service   │  ← Public URL: https://frontend.railway.app
│  (nginx)            │
└──────┬──────────────┘
       │ HTTPS (Public - Browser limitation)
       ↓
┌─────────────────────┐
│  Backend Service    │  ← Public URL: https://backend.railway.app
│  (FastAPI)          │  ← Internal: backend.railway.internal:8000
└──────┬──────────────┘
       │ Internal Network (Private, Fast)
       ↓
┌─────────────────────┐
│  MongoDB Service    │  ← Internal: mongodb.railway.internal:27017
│  (Private)          │  ← No public URL
└─────────────────────┘
```

---

## Verification Checklist

### MongoDB Service
- [ ] Service created and running
- [ ] Public URL disabled
- [ ] `MONGO_URL` available in Variables tab
- [ ] Service name is `MongoDB` (or note the exact name)

### Backend Service
- [ ] Root Directory: `backend`
- [ ] Dockerfile: `Dockerfile.railway`
- [ ] Port: `8000`
- [ ] Public URL enabled
- [ ] Variables set:
  - [ ] `MONGODB_URL=${{ MongoDB.MONGO_URL }}`
  - [ ] `AZURE_OPENAI_API_KEY`
  - [ ] `AZURE_OPENAI_ENDPOINT`
  - [ ] `AZURE_OPENAI_API_VERSION`
  - [ ] `CORS_ORIGINS` (update after frontend deploys)
- [ ] Branch selected
- [ ] Service deployed successfully

### Frontend Service
- [ ] Root Directory: `frontend`
- [ ] Dockerfile: `Dockerfile.railway`
- [ ] Port: `80`
- [ ] Public URL enabled
- [ ] Variables set:
  - [ ] `VITE_API_URL=https://${{ Backend.RAILWAY_PUBLIC_DOMAIN }}`
- [ ] Build Args set:
  - [ ] `VITE_API_URL=$VITE_API_URL`
- [ ] Branch selected
- [ ] Service deployed successfully

### Final Steps
- [ ] Update `CORS_ORIGINS` in backend with frontend's URL
- [ ] Test frontend → backend connection
- [ ] Test backend → MongoDB connection
- [ ] Verify all services are running

---

## Troubleshooting

### "Cannot resolve service reference"
- Check service names match exactly (case-sensitive)
- Service must be deployed before referencing it
- Wait a few seconds after creating service

### "Frontend can't reach backend"
- ✅ Use backend's **public URL** in `VITE_API_URL`
- ✅ Check backend's public URL is enabled
- ✅ Verify `CORS_ORIGINS` includes frontend's domain
- ❌ Don't use internal hostnames (browser can't access them)

### "Backend can't reach MongoDB"
- ✅ Use `${{ MongoDB.MONGO_URL }}` service reference
- ✅ Check MongoDB service name matches
- ✅ Verify MongoDB is running
- ✅ Check MongoDB service has public URL disabled (should be private)

### "CORS errors"
- ✅ Add frontend's full public URL to `CORS_ORIGINS`
- ✅ Use `https://` not `http://`
- ✅ No trailing slash
- ✅ Update CORS after frontend is deployed

---

## Quick Copy-Paste Variables

### Backend Variables
```bash
MONGODB_URL=${{ MongoDB.MONGO_URL }}
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-02-15-preview
CORS_ORIGINS=https://${{ Frontend.RAILWAY_PUBLIC_DOMAIN }}
PYTHONPATH=/app
```

### Frontend Variables
```bash
VITE_API_URL=https://${{ Backend.RAILWAY_PUBLIC_DOMAIN }}
```

### Frontend Build Args
```bash
VITE_API_URL=$VITE_API_URL
```



