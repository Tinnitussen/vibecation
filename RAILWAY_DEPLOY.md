# Railway Deployment Guide

## Fixing the VOLUME Error

Railway bans the `VOLUME` keyword in Dockerfiles. If you're getting this error, it's likely because:

1. **Base images contain VOLUME** - Some base images (like `nginx:alpine`) may have VOLUME declarations
2. **Railway is scanning docker-compose** - If Railway tries to parse docker-compose.yml
3. **Railway auto-detection** - Railway might be trying to use docker-compose.yml automatically

**Solution:** 
- Deploy services individually (not using docker-compose) - this is Railway's recommended approach
- Use `Dockerfile.railway` files provided (they're optimized for Railway)
- Make sure Railway doesn't auto-detect docker-compose.yml

---

## Deploying from a Branch via Railway UI

### Prerequisites

1. **GitHub Repository:**
   - Your code must be pushed to GitHub
   - The branch you want to deploy must exist in GitHub
   - No special repository settings needed

2. **Railway Account:**
   - Sign up at [railway.app](https://railway.app)
   - Connect your GitHub account
   - Authorize Railway to access your repositories

### Step-by-Step: Deploy Individual Services

Railway works best when you deploy each service separately (not using docker-compose). Here's how:

#### 1. Create a New Project

1. Go to [railway.app](https://railway.app)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your `vibecation` repository
5. Select the branch you want to deploy from

#### 2. Add MongoDB (Recommended: Use Railway's MongoDB Plugin)

1. In your Railway project, click **"+ New"**
2. Select **"Database"** → **"Add MongoDB"**
3. Railway will create a MongoDB instance automatically
4. Note the connection string (you'll need it for the backend)

#### 3. Deploy Backend Service

1. Click **"+ New"** → **"GitHub Repo"**
2. Select your repository and branch
3. Railway will create a new service
4. In the service settings:
   - **Root Directory:** `backend`
   - **Dockerfile Path:** `Dockerfile.railway` (or `Dockerfile.prod` if railway version doesn't exist)
   - **Port:** `8000`
   - **Important:** Make sure Railway is NOT trying to use docker-compose.yml
5. Go to **Variables** tab and add:
   ```
   MONGODB_URL=<your-mongodb-connection-string-from-step-2>
   AZURE_OPENAI_API_KEY=<your-key>
   AZURE_OPENAI_ENDPOINT=<your-endpoint>
   AZURE_OPENAI_API_VERSION=2024-02-15-preview
   CORS_ORIGINS=https://your-frontend-url.railway.app
   ```
6. Click **"Deploy"**

#### 4. Deploy Frontend Service

1. Click **"+ New"** → **"GitHub Repo"**
2. Select your repository and branch (same as backend)
3. In the service settings:
   - **Root Directory:** `frontend`
   - **Dockerfile Path:** `Dockerfile.railway` (or `Dockerfile.prod` if railway version doesn't exist)
   - **Port:** `80`
   - **Important:** Make sure Railway is NOT trying to use docker-compose.yml
4. Go to **Variables** tab and add:
   ```
   VITE_API_URL=https://your-backend-url.railway.app
   ```
   (Get the backend URL from Railway dashboard after backend deploys)
5. Go to **Settings** → **Build** → **Build Command Arguments**:
   - Add: `--build-arg VITE_API_URL=$VITE_API_URL`
6. Click **"Deploy"**

#### 5. Configure Branch for Each Service

For each service (backend and frontend):

1. Go to the service
2. Click **"Settings"** tab
3. Scroll to **"GitHub"** section
4. Under **"Branch"**, select the branch you want to deploy from
5. Enable **"Auto Deploy"** if you want automatic deployments on push

---

## Alternative: Deploy MongoDB Container (Not Recommended)

If you want to deploy MongoDB as a container instead of using Railway's plugin:

1. Click **"+ New"** → **"GitHub Repo"**
2. Select your repository
3. In service settings:
   - **Dockerfile Path:** Leave blank (we'll use a public image)
   - **Image:** `mongo:7.0`
   - **Port:** `27017`
4. Add environment variable:
   ```
   MONGO_INITDB_DATABASE=vibecation
   ```
5. Go to **Settings** → **Volumes** → **Add Volume**
   - **Mount Path:** `/data/db`
   - This creates persistent storage for MongoDB

**Note:** Railway's MongoDB plugin is easier and includes backups.

---

## Troubleshooting

### "VOLUME keyword is banned" Error

**If you see this error:**

1. **Check your Dockerfiles** - Make sure there's no `VOLUME` line
2. **Deploy services individually** - Don't use docker-compose in Railway
3. **Use Railway volumes** - For MongoDB, use Railway's volume system in Settings

### Branch Not Showing in Railway

1. Make sure the branch is pushed to GitHub
2. Refresh Railway dashboard
3. In service settings, manually type the branch name if it doesn't appear

### Services Can't Connect

1. **MongoDB connection:**
   - Use Railway's MongoDB connection string (not `mongodb://mongodb:27017`)
   - Get it from MongoDB service → Variables → `MONGO_URL`

2. **Frontend to Backend:**
   - Use Railway's public URL for backend (not localhost)
   - Format: `https://your-backend-service.railway.app`
   - Update `VITE_API_URL` in frontend variables

3. **CORS errors:**
   - Add frontend URL to `CORS_ORIGINS` in backend
   - Format: `https://your-frontend.railway.app` (comma-separated if multiple)

### Build Fails

1. Check **Root Directory** is set correctly (`backend` or `frontend`)
2. Verify **Dockerfile Path** is correct (`Dockerfile.prod`)
3. Check build logs in Railway dashboard for specific errors
4. Make sure all files are committed to the branch

---

## Environment Variables Reference

### Backend Service
```
MONGODB_URL=<railway-mongodb-connection-string>
AZURE_OPENAI_API_KEY=<your-key>
AZURE_OPENAI_ENDPOINT=<your-endpoint>
AZURE_OPENAI_API_VERSION=2024-02-15-preview
CORS_ORIGINS=https://your-frontend.railway.app
```

### Frontend Service
```
VITE_API_URL=https://your-backend.railway.app
```

### MongoDB (if using container)
```
MONGO_INITDB_DATABASE=vibecation
```

---

## Getting Your URLs

After deployment:

1. Go to each service in Railway dashboard
2. Click **"Settings"** → **"Networking"**
3. Enable **"Generate Domain"** to get a public URL
4. Or add a custom domain

Your URLs will look like:
- Frontend: `https://vibecation-frontend-production.up.railway.app`
- Backend: `https://vibecation-backend-production.up.railway.app`

---

## Auto-Deploy from Branch

To enable auto-deployment:

1. Go to service → **Settings** → **GitHub**
2. Select your branch
3. Enable **"Auto Deploy"**
4. Now every push to that branch will trigger a deployment

---

## Summary

✅ **Do:**
- Deploy services individually (not docker-compose)
- Use Railway's MongoDB plugin
- Set Root Directory for each service
- Use Railway's public URLs for service communication
- Configure branch in service settings

❌ **Don't:**
- Use `VOLUME` in Dockerfiles
- Use docker-compose in Railway (deploy services separately)
- Use `localhost` or service names for connections (use Railway URLs)
- Forget to set environment variables

