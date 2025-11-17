# GitHub Actions Workflows

This directory contains GitHub Actions workflows for automated deployment.

## Available Workflows

### 1. `deploy-railway.yml`
Deploys to Railway platform automatically on push to `main` branch.

**Setup:**
1. Get Railway token from [railway.app/account/tokens](https://railway.app/account/tokens)
2. Add to GitHub Secrets: `RAILWAY_TOKEN`
3. Push to `main` → Auto-deploys!

### 2. `deploy-render.yml`
Deploys to Render platform automatically on push to `main` branch.

**Setup:**
1. Get Render API key from [dashboard.render.com/account/api-keys](https://dashboard.render.com/account/api-keys)
2. Get your service ID from Render dashboard
3. Add to GitHub Secrets:
   - `RENDER_API_KEY`
   - `RENDER_SERVICE_ID`
4. Push to `main` → Auto-deploys!

### 3. `deploy-dockerhub.yml`
Builds and pushes Docker images to Docker Hub.

**Setup:**
1. Create Docker Hub account
2. Add to GitHub Secrets:
   - `DOCKERHUB_USERNAME`
   - `DOCKERHUB_TOKEN`
   - `VITE_API_URL` (your backend URL)
3. Images will be pushed to:
   - `{DOCKERHUB_USERNAME}/vibecation-backend:latest`
   - `{DOCKERHUB_USERNAME}/vibecation-frontend:latest`

## How to Add Secrets

1. Go to your GitHub repository
2. Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add each secret with the name and value

## Manual Deployment

You can also trigger workflows manually:
1. Go to Actions tab in GitHub
2. Select the workflow
3. Click "Run workflow"

