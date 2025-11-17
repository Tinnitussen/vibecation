# How to Set Build Arguments in Railway UI

## Overview

Your `Dockerfile.railway` already has the build argument defined:
```dockerfile
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL
```

Now you need to tell Railway to pass this build argument during the Docker build process.

---

## Method 1: Using Railway UI (Recommended)

### Step-by-Step:

1. **Go to your Frontend service in Railway dashboard**

2. **Click on "Settings" tab** (gear icon or in the sidebar)

3. **Scroll down to "Build" section**

4. **Look for "Build Command Arguments" or "Build Args" field**

5. **Add the build argument:**
   ```
   VITE_API_URL=$VITE_API_URL
   ```
   
   This tells Railway to:
   - Use the build argument name: `VITE_API_URL`
   - Get its value from the environment variable `VITE_API_URL` (which you set in Variables tab)

### Alternative: Direct Value

If Railway doesn't support variable substitution in build args, you can also use Railway's service reference directly:

```
VITE_API_URL=https://${{ Backend.RAILWAY_PUBLIC_DOMAIN }}
```

---

## Method 2: Using railway.json (Alternative)

If Railway UI doesn't have a build args field, you can configure it in `railway.json`:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile.railway",
    "buildArgs": {
      "VITE_API_URL": "${{ Backend.RAILWAY_PUBLIC_DOMAIN }}"
    }
  }
}
```

However, Railway's service references might not work in `railway.json`. Better to use environment variables.

---

## Method 3: Using Environment Variables (Easiest)

Railway automatically passes environment variables as build arguments if they match the `ARG` name in your Dockerfile.

### Setup:

1. **In Frontend service → Variables tab:**
   ```bash
   VITE_API_URL=https://${{ Backend.RAILWAY_PUBLIC_DOMAIN }}
   ```

2. **Railway will automatically:**
   - Pass `VITE_API_URL` as a build argument during Docker build
   - Because your Dockerfile has `ARG VITE_API_URL`

### This is the simplest method!

Railway automatically converts environment variables to build arguments if:
- The variable name matches an `ARG` in your Dockerfile
- The variable is set in the service's Variables tab

---

## Complete Setup for Frontend Service

### Variables Tab:
```bash
VITE_API_URL=https://${{ Backend.RAILWAY_PUBLIC_DOMAIN }}
```

### Settings Tab:
- **Root Directory:** `frontend`
- **Dockerfile Path:** `Dockerfile.railway`
- **Port:** `80`
- **Build Command Arguments:** (Leave empty OR add `VITE_API_URL=$VITE_API_URL` if Railway has this field)

### How It Works:

1. Railway reads `VITE_API_URL` from Variables tab
2. Railway resolves `${{ Backend.RAILWAY_PUBLIC_DOMAIN }}` to the actual backend URL
3. Railway passes `VITE_API_URL` as a build argument to Docker
4. Dockerfile receives it via `ARG VITE_API_URL`
5. Dockerfile sets it as environment variable: `ENV VITE_API_URL=$VITE_API_URL`
6. Vite build process reads it and bakes it into the built files

---

## Verification

After deployment, verify the build argument was used:

1. **Check Railway build logs:**
   - Look for: `--build-arg VITE_API_URL=...`
   - Or: `Building with args: VITE_API_URL=...`

2. **Check built frontend:**
   - Open your frontend URL in browser
   - Open browser DevTools → Console
   - Check network requests - they should go to your backend URL
   - Or check the built JavaScript files for the API URL

3. **Test API calls:**
   - Try logging in or making an API call
   - Check Network tab - requests should go to backend's public URL

---

## Troubleshooting

### Build argument not being passed

**Solution 1:** Make sure the variable name in Railway matches the `ARG` name in Dockerfile:
- Dockerfile: `ARG VITE_API_URL`
- Railway Variable: `VITE_API_URL` ✅

**Solution 2:** If Railway UI has a "Build Args" field, explicitly add:
```
VITE_API_URL=$VITE_API_URL
```

**Solution 3:** Check Railway build logs to see what arguments are being passed

### Build argument is empty

**Check:**
1. Variable is set in Variables tab
2. Service reference is correct: `${{ Backend.RAILWAY_PUBLIC_DOMAIN }}`
3. Backend service is deployed and has a public domain
4. Variable name matches exactly (case-sensitive)

### Vite still using default URL

**Check:**
1. Build logs show the build argument was passed
2. Rebuild the service (Railway might cache the build)
3. Clear browser cache and hard refresh
4. Check built files in browser DevTools → Sources

---

## Railway UI Screenshot Guide

### Where to Find Build Settings:

```
Railway Dashboard
  └── Your Project
      └── Frontend Service
          └── Settings Tab
              ├── Source
              │   ├── Root Directory: frontend
              │   └── Dockerfile Path: Dockerfile.railway
              ├── Build  ← Look here!
              │   ├── Build Command Arguments (if available)
              │   └── Build Args (if available)
              ├── Deploy
              └── Variables Tab ← Set VITE_API_URL here
```

---

## Summary

**Easiest Method:**
1. Set `VITE_API_URL` in **Variables tab** with Railway service reference
2. Railway automatically passes it as build argument (because Dockerfile has `ARG VITE_API_URL`)
3. No additional configuration needed!

**If that doesn't work:**
1. Check if Railway UI has "Build Command Arguments" or "Build Args" field
2. Add: `VITE_API_URL=$VITE_API_URL`
3. Or use direct value: `VITE_API_URL=https://your-backend-url.railway.app`





