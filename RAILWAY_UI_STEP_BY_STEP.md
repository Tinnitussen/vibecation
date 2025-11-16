# Railway UI: Deploy Services Individually - Step by Step

## Overview

When deploying to Railway via the UI, you'll create **separate services** for each component (MongoDB, Backend, Frontend) instead of using docker-compose. This is Railway's recommended approach.

---

## Step 1: Create a New Project

1. Go to [railway.app](https://railway.app) and sign in
2. Click **"+ New Project"** (top right or in dashboard)
3. Select **"Deploy from GitHub repo"**
4. If prompted, authorize Railway to access your GitHub account
5. Select your `vibecation` repository
6. Choose the branch you want to deploy from
7. Click **"Deploy Now"** or **"Add Service"**

**Note:** Railway will create your first service automatically. You can delete it or use it - we'll create services manually.

---

## Step 2: Add MongoDB (Recommended: Use Railway's Plugin)

### Option A: Railway MongoDB Plugin (Easiest - Recommended)

1. In your Railway project dashboard, click **"+ New"** button
2. Select **"Database"** from the dropdown
3. Click **"Add MongoDB"**
4. Railway will automatically:
   - Create a MongoDB instance
   - Set up persistent storage
   - Provide a connection string
5. **Important:** Note the connection string - you'll need it for the backend:
   - Click on the MongoDB service
   - Go to **"Variables"** tab
   - Find `MONGO_URL` or `MONGODB_URL` - copy this value

### Option B: MongoDB Container (Alternative)

1. Click **"+ New"** → **"GitHub Repo"**
2. Select your repository and branch
3. In the service that's created:
   - Click on the service name
   - Go to **"Settings"** tab
   - Under **"Source"**, change from "GitHub" to **"Public Image"**
   - Enter image: `mongo:7.0`
   - Set **Port:** `27017`
4. Go to **"Variables"** tab, add:
   ```
   MONGO_INITDB_DATABASE=vibecation
   ```
5. Go to **"Settings"** → **"Volumes"** → **"Add Volume"**
   - Mount Path: `/data/db`
   - This creates persistent storage

---

## Step 3: Deploy Backend Service

1. In your Railway project, click **"+ New"** button
2. Select **"GitHub Repo"**
3. Select your `vibecation` repository
4. Select the branch you want to deploy from
5. Railway will create a new service

### Configure Backend Service:

6. Click on the newly created service (it will have a random name like "vibecation-abc123")
7. Click **"Settings"** tab (gear icon or in the sidebar)

8. **Configure Build Settings:**
   - **Root Directory:** Type `backend`
   - **Dockerfile Path:** Type `Dockerfile.railway` (or `Dockerfile.prod`)
   - **Port:** `8000`
   - Make sure **"Build Command"** and **"Start Command"** are empty (Railway will use Dockerfile)

9. **Configure Branch (if not already set):**
   - Scroll to **"GitHub"** section
   - Under **"Branch"**, select your branch from dropdown
   - Enable **"Auto Deploy"** if you want automatic deployments on push

10. **Add Environment Variables:**
    - Go to **"Variables"** tab
    - Click **"+ New Variable"** for each:
    
    ```
    MONGODB_URL=<paste-your-mongodb-connection-string-here>
    AZURE_OPENAI_API_KEY=<your-azure-openai-key>
    AZURE_OPENAI_ENDPOINT=<your-azure-openai-endpoint>
    AZURE_OPENAI_API_VERSION=2024-02-15-preview
    CORS_ORIGINS=https://your-frontend-url.railway.app
    ```
    
    **Note:** For `CORS_ORIGINS`, you'll need to update this after you deploy the frontend and get its URL.

11. **Enable Public URL:**
    - Go to **"Settings"** → **"Networking"**
    - Toggle **"Generate Domain"** to ON
    - Railway will create a public URL like `https://vibecation-backend-production.up.railway.app`
    - **Copy this URL** - you'll need it for the frontend

12. Click **"Deploy"** or Railway will auto-deploy

---

## Step 4: Deploy Frontend Service

1. In your Railway project, click **"+ New"** button again
2. Select **"GitHub Repo"**
3. Select your `vibecation` repository
4. Select the same branch as backend
5. Railway will create another new service

### Configure Frontend Service:

6. Click on the newly created service
7. Click **"Settings"** tab

8. **Configure Build Settings:**
   - **Root Directory:** Type `frontend`
   - **Dockerfile Path:** Type `Dockerfile.railway` (or `Dockerfile.prod`)
   - **Port:** `80`
   - Make sure **"Build Command"** and **"Start Command"** are empty

9. **Configure Build Arguments:**
   - Go to **"Settings"** → **"Build"**
   - Under **"Build Command Arguments"** or **"Build Args"**, add:
     ```
     VITE_API_URL=$VITE_API_URL
     ```
   - Or in **"Variables"** tab, add:
     ```
     VITE_API_URL=https://your-backend-url.railway.app
     ```
     (Use the backend URL you copied in Step 3)

10. **Add Environment Variables:**
    - Go to **"Variables"** tab
    - Click **"+ New Variable"**:
    ```
    VITE_API_URL=https://your-backend-url.railway.app
    ```
    (Use the actual backend URL from Step 3)

11. **Configure Branch:**
    - Scroll to **"GitHub"** section
    - Under **"Branch"**, select your branch
    - Enable **"Auto Deploy"** if desired

12. **Enable Public URL:**
    - Go to **"Settings"** → **"Networking"**
    - Toggle **"Generate Domain"** to ON
    - Railway will create a public URL like `https://vibecation-frontend-production.up.railway.app`

13. Click **"Deploy"** or Railway will auto-deploy

---

## Step 5: Update CORS in Backend

After frontend is deployed:

1. Go back to your **Backend** service
2. Go to **"Variables"** tab
3. Update `CORS_ORIGINS` to include your frontend URL:
   ```
   CORS_ORIGINS=https://your-frontend-url.railway.app
   ```
4. Railway will automatically redeploy when you save

---

## Visual Guide: Where to Find Settings

### Service Settings Location:
```
Railway Dashboard
  └── Your Project
      └── Service Name (click on it)
          ├── Settings Tab (gear icon)
          │   ├── Source
          │   │   ├── Root Directory ← Set this!
          │   │   └── Dockerfile Path ← Set this!
          │   ├── Build
          │   │   └── Build Command Arguments
          │   ├── Networking
          │   │   └── Generate Domain ← Enable this!
          │   └── GitHub
          │       └── Branch ← Select your branch!
          └── Variables Tab
              └── + New Variable ← Add env vars here!
```

---

## Important Tips

### ✅ Do:
- Set **Root Directory** explicitly (e.g., `backend` or `frontend`)
- Set **Dockerfile Path** explicitly (e.g., `Dockerfile.railway`)
- Use Railway's MongoDB plugin (easier than container)
- Enable **Generate Domain** for public URLs
- Set branch in **Settings → GitHub → Branch**

### ❌ Don't:
- Don't leave Root Directory blank
- Don't let Railway auto-detect docker-compose
- Don't use `localhost` in environment variables
- Don't forget to set `VITE_API_URL` in frontend

---

## Troubleshooting

### "Service not building"
- Check **Root Directory** is set correctly
- Verify **Dockerfile Path** exists in that directory
- Check build logs in Railway dashboard

### "Can't connect to MongoDB"
- Use Railway's MongoDB connection string (not `mongodb://localhost`)
- Get it from MongoDB service → Variables → `MONGO_URL`

### "Frontend can't reach backend"
- Use Railway's public URL for backend (not `localhost:8000`)
- Format: `https://your-backend.railway.app`
- Update `VITE_API_URL` in frontend variables

### "CORS errors"
- Add frontend URL to `CORS_ORIGINS` in backend
- Format: `https://your-frontend.railway.app`
- Comma-separate multiple origins if needed

---

## Summary Checklist

- [ ] Created Railway project from GitHub repo
- [ ] Added MongoDB (plugin or container)
- [ ] Created Backend service with:
  - [ ] Root Directory: `backend`
  - [ ] Dockerfile Path: `Dockerfile.railway`
  - [ ] Port: `8000`
  - [ ] Environment variables set
  - [ ] Public URL enabled
  - [ ] Branch selected
- [ ] Created Frontend service with:
  - [ ] Root Directory: `frontend`
  - [ ] Dockerfile Path: `Dockerfile.railway`
  - [ ] Port: `80`
  - [ ] `VITE_API_URL` set to backend URL
  - [ ] Public URL enabled
  - [ ] Branch selected
- [ ] Updated `CORS_ORIGINS` in backend with frontend URL
- [ ] Tested both services are running

---

## Your Final URLs

After deployment, you'll have:
- **Frontend:** `https://your-frontend.railway.app`
- **Backend:** `https://your-backend.railway.app`
- **API Docs:** `https://your-backend.railway.app/docs`

You can find these URLs in each service's **Settings → Networking** section.





