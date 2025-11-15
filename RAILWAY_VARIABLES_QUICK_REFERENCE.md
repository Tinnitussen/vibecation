# Railway Variables - Quick Reference

## ⚠️ Important Note About Frontend

**The frontend runs in the user's browser**, so it **cannot** use Railway's internal network. The browser must connect to the backend via its **public URL**. However, the backend can use Railway's internal network to connect to MongoDB.

---

## Service 1: MongoDB

### Service Name
`MongoDB` (use this exact name for service references)

### Variables Tab
```
(No variables needed - Railway provides automatically)
```

### Railway Auto-Provides
- `MONGO_URL` - Full connection string
- `MONGO_HOST` - Hostname
- `MONGO_PORT` - Port
- `MONGO_DATABASE` - Database name

### Settings
- **Public URL**: ❌ **DISABLED** (keep private)
- **Port**: `27017`

---

## Service 2: Backend

### Service Name
`Backend` (use this exact name for service references)

### Variables Tab - Copy These Exactly:

```bash
MONGODB_URL=${{ MongoDB.MONGO_URL }}
AZURE_OPENAI_API_KEY=your-actual-azure-openai-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-02-15-preview
CORS_ORIGINS=https://${{ Frontend.RAILWAY_PUBLIC_DOMAIN }}
PYTHONPATH=/app
```

### Settings
- **Root Directory**: `backend`
- **Dockerfile Path**: `Dockerfile.railway`
- **Port**: `8000`
- **Public URL**: ✅ **ENABLED** (needed for frontend)
- **Generate Domain**: ✅ **ENABLED**

### Notes
- `MONGODB_URL` uses Railway's internal network via service reference
- `CORS_ORIGINS` uses Railway service reference to get frontend's URL automatically
- Backend needs public URL because browser needs to access it

---

## Service 3: Frontend

### Service Name
`Frontend` (use this exact name for service references)

### Variables Tab - Copy This Exactly:

```bash
VITE_API_URL=https://${{ Backend.RAILWAY_PUBLIC_DOMAIN }}
```

### Settings → Build → Build Command Arguments (Optional)
**Note:** Railway automatically passes environment variables as build arguments if they match the `ARG` name in your Dockerfile. So if you set `VITE_API_URL` in Variables tab, Railway will automatically pass it during build.

If Railway UI has a "Build Command Arguments" or "Build Args" field, you can explicitly add:
```bash
VITE_API_URL=$VITE_API_URL
```

But this is usually not needed - Railway does it automatically!

### Settings
- **Root Directory**: `frontend`
- **Dockerfile Path**: `Dockerfile.railway`
- **Port**: `80`
- **Public URL**: ✅ **ENABLED**
- **Generate Domain**: ✅ **ENABLED**

### Notes
- Frontend **must** use backend's **public URL** (browser limitation)
- `VITE_API_URL` is baked into the build at build time
- Use Railway service reference to automatically get backend's public domain

---

## Service Reference Syntax

Railway uses `${{ ServiceName.VARIABLE }}` syntax to reference other services.

### Available Variables Per Service:
- `RAILWAY_PUBLIC_DOMAIN` - Public domain (e.g., `service-name.up.railway.app`)
- `RAILWAY_ENVIRONMENT` - Environment name
- `RAILWAY_SERVICE_NAME` - Service name
- `RAILWAY_PROJECT_NAME` - Project name

### For MongoDB Plugin:
- `MONGO_URL` - Full connection string (includes credentials)

---

## Setup Order

1. **Create MongoDB** first
   - Get service name: `MongoDB`
   - Note: Railway provides `MONGO_URL` automatically

2. **Create Backend** second
   - Use `${{ MongoDB.MONGO_URL }}` for MongoDB connection
   - Enable public URL
   - Get backend's public domain

3. **Create Frontend** third
   - Use `${{ Backend.RAILWAY_PUBLIC_DOMAIN }}` for backend URL
   - Enable public URL

4. **Update Backend CORS** (after frontend is deployed)
   - Update `CORS_ORIGINS` with `${{ Frontend.RAILWAY_PUBLIC_DOMAIN }}`

---

## Sanity Check: All Variables

### ✅ MongoDB Service
- [ ] Service name: `MongoDB`
- [ ] Public URL: **DISABLED**
- [ ] `MONGO_URL` available (auto-provided)

### ✅ Backend Service
- [ ] Service name: `Backend`
- [ ] Root Directory: `backend`
- [ ] Dockerfile: `Dockerfile.railway`
- [ ] Port: `8000`
- [ ] Public URL: **ENABLED**
- [ ] Variables:
  - [ ] `MONGODB_URL=${{ MongoDB.MONGO_URL }}`
  - [ ] `AZURE_OPENAI_API_KEY` (your actual key)
  - [ ] `AZURE_OPENAI_ENDPOINT` (your actual endpoint)
  - [ ] `AZURE_OPENAI_API_VERSION=2024-02-15-preview`
  - [ ] `CORS_ORIGINS=https://${{ Frontend.RAILWAY_PUBLIC_DOMAIN }}`
  - [ ] `PYTHONPATH=/app`

### ✅ Frontend Service
- [ ] Service name: `Frontend`
- [ ] Root Directory: `frontend`
- [ ] Dockerfile: `Dockerfile.railway`
- [ ] Port: `80`
- [ ] Public URL: **ENABLED**
- [ ] Variables:
  - [ ] `VITE_API_URL=https://${{ Backend.RAILWAY_PUBLIC_DOMAIN }}`
- [ ] Build Args:
  - [ ] `VITE_API_URL=$VITE_API_URL`

---

## Common Mistakes to Avoid

### ❌ Don't Use Internal Hostnames in Frontend
```bash
# WRONG - Browser can't access internal network
VITE_API_URL=http://backend.railway.internal:8000

# CORRECT - Use public URL
VITE_API_URL=https://${{ Backend.RAILWAY_PUBLIC_DOMAIN }}
```

### ❌ Don't Use Public URL for MongoDB
```bash
# WRONG - Should use internal network
MONGODB_URL=mongodb://public-url.railway.app:27017

# CORRECT - Use service reference
MONGODB_URL=${{ MongoDB.MONGO_URL }}
```

### ❌ Don't Forget Build Args
Frontend needs `VITE_API_URL` as a build argument, not just an environment variable.

### ❌ Don't Use localhost
```bash
# WRONG - localhost doesn't work in Railway
MONGODB_URL=mongodb://localhost:27017

# CORRECT - Use service reference
MONGODB_URL=${{ MongoDB.MONGO_URL }}
```

---

## Testing Your Setup

1. **Check MongoDB Connection:**
   - Backend logs should show successful MongoDB connection
   - No connection errors in backend service logs

2. **Check Frontend → Backend:**
   - Open frontend URL in browser
   - Check browser console for API errors
   - Verify API calls go to backend's public URL

3. **Check CORS:**
   - If you see CORS errors, verify `CORS_ORIGINS` includes frontend's exact URL
   - Check browser console for CORS error messages

---

## Quick Copy-Paste

### Backend Variables (One Block)
```bash
MONGODB_URL=${{ MongoDB.MONGO_URL }}
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-02-15-preview
CORS_ORIGINS=https://${{ Frontend.RAILWAY_PUBLIC_DOMAIN }}
PYTHONPATH=/app
```

### Frontend Variables (One Block)
```bash
VITE_API_URL=https://${{ Backend.RAILWAY_PUBLIC_DOMAIN }}
```

### Frontend Build Args
```bash
VITE_API_URL=$VITE_API_URL
```

