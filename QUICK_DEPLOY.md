# 🚀 Quick Deployment Guide

## Fastest Option: Railway (Recommended)

**Time to deploy: ~5 minutes**

### Step 1: Sign up
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your `vibecation` repository

### Step 2: Deploy Services

Railway will auto-detect your docker-compose.yml. You have two options:

#### Option A: Use Railway's MongoDB Plugin (Easiest)
1. Add **MongoDB** plugin from Railway's marketplace
2. Create **Backend** service:
   - Source: Your repo
   - Root Directory: `backend`
   - Dockerfile: `Dockerfile.prod`
   - Port: 8000
3. Create **Frontend** service:
   - Source: Your repo
   - Root Directory: `frontend`
   - Dockerfile: `Dockerfile.prod`
   - Port: 80
   - Build Args: `VITE_API_URL` = your backend URL

#### Option B: Deploy All 3 Containers
1. Railway can deploy docker-compose directly
2. Use `docker-compose.prod.yml` file
3. Set environment variables in Railway dashboard

### Step 3: Set Environment Variables

In Railway dashboard, add these to each service:

**Backend:**
```
MONGODB_URL=mongodb://mongodb:27017 (or Railway MongoDB connection string)
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_API_VERSION=2024-02-15-preview
CORS_ORIGINS=https://your-frontend-url.railway.app
```

**Frontend:**
```
VITE_API_URL=https://your-backend-url.railway.app
```

**MongoDB:**
```
MONGO_INITDB_DATABASE=vibecation
```

### Step 4: Get Your URLs
- Railway will give you URLs like:
  - Frontend: `https://vibecation-frontend.railway.app`
  - Backend: `https://vibecation-backend.railway.app`

### Step 5: Update CORS
Update `CORS_ORIGINS` in backend to include your frontend URL.

---

## Alternative: Render (Also Fast)

**Time to deploy: ~10 minutes**

1. Sign up at [render.com](https://render.com)
2. Create new **Web Service** from GitHub
3. Use `render.yaml` configuration (already created)
4. Render will automatically:
   - Create MongoDB database
   - Deploy backend
   - Deploy frontend
   - Set up networking

---

## GitHub Actions Auto-Deploy

After initial setup, you can enable auto-deployment:

1. Add secrets to GitHub:
   - `RAILWAY_TOKEN` (get from Railway dashboard)
   - Or `RENDER_API_KEY` and `RENDER_SERVICE_ID`

2. Push to `main` branch → Auto-deploys! 🎉

---

## Testing Locally First

Before deploying, test production build:

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Run locally
docker-compose -f docker-compose.prod.yml up
```

Visit:
- Frontend: http://localhost
- Backend: http://localhost:8000

---

## Troubleshooting

**Frontend can't reach backend?**
- Check `VITE_API_URL` is set correctly
- Rebuild frontend after changing env vars
- Check CORS settings in backend

**MongoDB connection failed?**
- Use service name (not localhost) in docker-compose
- Check MongoDB is running and healthy
- Verify connection string format

**Build fails?**
- Check Dockerfile paths are correct
- Verify all files are committed to git
- Check build logs in platform dashboard

---

## Cost Estimate

**Railway Free Tier:**
- $5 credit/month
- Usually enough for small apps
- Pay-as-you-go after

**Render Free Tier:**
- Free for 90 days
- Then $7/month per service
- MongoDB: $0-15/month

---

## Next Steps

1. ✅ Choose platform (Railway recommended)
2. ✅ Deploy services
3. ✅ Set environment variables
4. ✅ Test the deployed app
5. ✅ Set up custom domain (optional)
6. ✅ Enable GitHub Actions for auto-deploy

**You're done! 🎉**

