# How to Set Build Arguments in Railway UI

## Quick Answer

**Railway automatically passes environment variables as build arguments** if the variable name matches an `ARG` in your Dockerfile.

Since your `Dockerfile.railway` has:
```dockerfile
ARG VITE_API_URL
```

You just need to:

1. **Go to Frontend service → Variables tab**
2. **Add:**
   ```bash
   VITE_API_URL=https://${{ Backend.RAILWAY_PUBLIC_DOMAIN }}
   ```
3. **That's it!** Railway will automatically pass it as a build argument during Docker build.

---

## Detailed Steps

### Step 1: Set the Environment Variable

1. In Railway dashboard, go to your **Frontend** service
2. Click **"Variables"** tab
3. Click **"+ New Variable"**
4. **Name:** `VITE_API_URL`
5. **Value:** `https://${{ Backend.RAILWAY_PUBLIC_DOMAIN }}`
6. Click **"Add"**

### Step 2: Railway Automatically Uses It

Railway will:
- Read the `VITE_API_URL` variable
- Resolve `${{ Backend.RAILWAY_PUBLIC_DOMAIN }}` to the actual backend URL
- Automatically pass it to Docker as `--build-arg VITE_API_URL=...`
- Your Dockerfile receives it via `ARG VITE_API_URL`

### Step 3: (Optional) Explicit Build Args

If Railway UI has a "Build Command Arguments" or "Build Args" field:

1. Go to **Settings** → **Build** section
2. Look for **"Build Command Arguments"** or **"Build Args"**
3. Add: `VITE_API_URL=$VITE_API_URL`

**But this is usually not needed** - Railway does it automatically!

---

## How It Works

```
Railway Variables Tab
  └── VITE_API_URL=https://${{ Backend.RAILWAY_PUBLIC_DOMAIN }}
      │
      ├── Railway resolves service reference
      │   └── https://backend-production.up.railway.app
      │
      └── Railway passes to Docker build
          └── docker build --build-arg VITE_API_URL=https://backend-production.up.railway.app
              │
              └── Dockerfile receives it
                  └── ARG VITE_API_URL
                  └── ENV VITE_API_URL=$VITE_API_URL
                  └── RUN npm run build
                      │
                      └── Vite reads VITE_API_URL
                          └── Bakes it into built JavaScript files
```

---

## Verification

After deployment:

1. **Check Railway build logs:**
   - Should see: `Building with VITE_API_URL=...`
   - Or: `--build-arg VITE_API_URL=...`

2. **Test in browser:**
   - Open frontend URL
   - Open DevTools → Network tab
   - Make an API call (e.g., login)
   - Check the request URL - should be your backend's public URL

3. **Check built files:**
   - Open DevTools → Sources
   - Look at the built JavaScript
   - Search for your backend URL - it should be baked in

---

## Troubleshooting

### Build argument not working?

1. **Check variable name matches exactly:**
   - Dockerfile: `ARG VITE_API_URL`
   - Railway Variable: `VITE_API_URL` ✅
   - Must match exactly (case-sensitive)

2. **Check service reference:**
   - Make sure Backend service is deployed
   - Service name matches: `Backend`
   - `${{ Backend.RAILWAY_PUBLIC_DOMAIN }}` should resolve

3. **Rebuild the service:**
   - Railway might cache the build
   - Trigger a new deployment
   - Or manually redeploy

4. **Check build logs:**
   - Look for build argument in logs
   - Verify it's being passed correctly

---

## Summary

**You don't need to do anything special!**

Just set `VITE_API_URL` in the Variables tab, and Railway automatically:
- ✅ Passes it as a build argument
- ✅ Resolves service references
- ✅ Makes it available during Docker build

Your Dockerfile is already set up correctly with `ARG VITE_API_URL`, so Railway will automatically use the environment variable as a build argument.





