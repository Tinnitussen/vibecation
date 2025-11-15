# Deployment Guide

This guide covers the easiest and fastest ways to deploy your Vibecation app (MongoDB, FastAPI backend, and React frontend).

## 🚀 Recommended: Railway (Easiest & Fastest)

**Railway** is the easiest option because it:
- Supports docker-compose natively
- Has a generous free tier ($5 credit/month)
- Auto-deploys from GitHub
- Handles SSL certificates automatically
- No credit card required for free tier

### Quick Setup (5 minutes):

1. **Sign up at [railway.app](https://railway.app)** with your GitHub account

2. **Create a new project** and select "Deploy from GitHub repo"

3. **Select your repository**

4. **Add environment variables** in Railway dashboard:
   - `AZURE_OPENAI_API_KEY`
   - `AZURE_OPENAI_ENDPOINT`
   - `AZURE_OPENAI_API_VERSION`
   - `VITE_API_URL` (set to your backend URL, e.g., `https://your-backend.railway.app`)

5. **Configure services:**
   - Railway will detect your `docker-compose.yml`
   - You may need to create separate services for each container:
     - MongoDB service (use `mongo:7.0` image)
     - Backend service (build from `./backend/Dockerfile.prod`)
     - Frontend service (build from `./frontend/Dockerfile.prod`)

6. **Set up networking:**
   - Use Railway's internal networking (services can reference each other by service name)
   - Update `MONGODB_URL` in backend to use Railway's MongoDB service name

### Alternative: Railway with docker-compose

Railway supports docker-compose directly. You can:
- Use `railway up` command
- Or connect your GitHub repo and Railway will auto-deploy

**GitHub Actions Integration:**
See `.github/workflows/deploy-railway.yml` - you'll need to add `RAILWAY_TOKEN` to your GitHub secrets.

---

## 🎨 Alternative: Render (Also Easy)

**Render** is another great option:
- Free tier available
- Supports docker-compose
- Auto-deploys from GitHub
- Free SSL certificates

### Setup:

1. **Sign up at [render.com](https://render.com)**

2. **Create a new "Web Service"** from your GitHub repo

3. **Configure:**
   - Build Command: `docker-compose -f docker-compose.prod.yml build`
   - Start Command: `docker-compose -f docker-compose.prod.yml up`

4. **Add environment variables** in Render dashboard

**GitHub Actions Integration:**
See `.github/workflows/deploy-render.yml` - you'll need `RENDER_API_KEY` and `RENDER_SERVICE_ID` in GitHub secrets.

---

## 🐳 Docker Hub + Any Cloud Provider

If you want more control, you can:

1. **Build and push images to Docker Hub** (see `.github/workflows/deploy-dockerhub.yml`)

2. **Deploy to any cloud provider:**
   - **DigitalOcean App Platform** - Supports docker-compose
   - **AWS ECS/Fargate** - More complex but powerful
   - **Google Cloud Run** - Serverless containers
   - **Azure Container Instances** - Simple container hosting
   - **Fly.io** - Great for Docker apps, free tier

---

## 📋 Pre-Deployment Checklist

### 1. Update Frontend Dockerfile for Production

The production Dockerfile (`frontend/Dockerfile.prod`) builds the React app and serves it with nginx.

### 2. Set Environment Variables

Create a `.env` file or set in your platform:
```bash
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_API_VERSION=2024-02-15-preview
VITE_API_URL=https://your-backend-url.com
```

### 3. Update API URLs

- Frontend needs `VITE_API_URL` pointing to your backend
- Backend needs `MONGODB_URL` pointing to MongoDB (use service name in docker-compose)

### 4. Test Locally

```bash
# Test production build locally
docker-compose -f docker-compose.prod.yml up --build
```

---

## 🔧 Platform-Specific Notes

### Railway
- Services can reference each other by name (e.g., `mongodb://mongodb:27017`)
- Use Railway's MongoDB plugin or deploy MongoDB container
- Set `VITE_API_URL` to your Railway backend URL

### Render
- Render provides MongoDB as a managed service (recommended)
- Or use MongoDB container
- Update `MONGODB_URL` to Render's MongoDB connection string

### DigitalOcean
- Use DigitalOcean's Managed MongoDB (recommended)
- Or deploy MongoDB container
- App Platform supports docker-compose natively

---

## 🚨 Common Issues

### Frontend can't reach backend
- Check CORS settings in `backend/main.py`
- Ensure `VITE_API_URL` is set correctly
- Verify backend URL is accessible

### MongoDB connection issues
- Use service name (not `localhost`) in docker-compose
- Check MongoDB health checks
- Verify network configuration

### Environment variables not working
- Vite requires `VITE_` prefix for client-side variables
- Rebuild frontend after changing `VITE_API_URL`
- Check platform-specific env var requirements

---

## 📚 Additional Resources

- [Railway Documentation](https://docs.railway.app)
- [Render Documentation](https://render.com/docs)
- [Docker Compose Production Best Practices](https://docs.docker.com/compose/production/)

---

## ⚡ Quick Start Commands

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Run production locally
docker-compose -f docker-compose.prod.yml up

# Push to Docker Hub (after setting up secrets)
gh workflow run deploy-dockerhub.yml
```

