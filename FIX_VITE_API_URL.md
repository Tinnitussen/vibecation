# Fix: Frontend Still Using Wrong API URL

## The Problem

Even after setting `VITE_API_URL` in Railway, the frontend is still making requests to:
```
POST https://vibecation.up.railway.app/vibecation-backend.up.railway.app/users
```

This means the **old build is still being used**. Vite bakes environment variables into the JavaScript at **build time**, not runtime.

## Solution: Rebuild Frontend

### Step 1: Verify Variable is Set Correctly

1. Go to Railway dashboard
2. Open **Frontend** service
3. Go to **Variables** tab
4. Check `VITE_API_URL` value

**It MUST be:**
```bash
https://vibecation-backend.up.railway.app
```

**NOT:**
```bash
vibecation-backend.up.railway.app  ❌ (Missing https://)
```

### Step 2: Trigger a New Build

You need to **rebuild** the frontend so Vite can bake in the new `VITE_API_URL` value.

**Option A: Manual Redeploy**
1. In Frontend service, click **"Deployments"** tab
2. Click **"Redeploy"** or **"Deploy"** button
3. Wait for build to complete

**Option B: Push a Commit**
1. Make a small change to any file (or just add a comment)
2. Commit and push to your branch
3. Railway will auto-deploy if auto-deploy is enabled

**Option C: Force Redeploy**
1. Go to Frontend service → Settings
2. Look for "Redeploy" or "Deploy" option
3. Click it to trigger a new build

### Step 3: Verify Build Logs

After triggering a rebuild:

1. Go to **Deployments** tab in Frontend service
2. Click on the latest deployment
3. Check the build logs
4. Look for: `Building with VITE_API_URL=...`
5. Should show: `VITE_API_URL=https://vibecation-backend.up.railway.app`

### Step 4: Test After Deployment

1. Wait for deployment to complete
2. Open your frontend URL in browser
3. Open **DevTools** → **Console**
4. Type: `console.log(import.meta.env.VITE_API_URL)`
5. Should show: `https://vibecation-backend.up.railway.app`

6. Try signing up again
7. Check **Network** tab
8. Request should be: `POST https://vibecation-backend.up.railway.app/users` ✅

## Why This Happens

Vite replaces `import.meta.env.VITE_API_URL` at **build time**:

```javascript
// At build time, Vite does:
const API_BASE_URL = "https://vibecation-backend.up.railway.app" || 'http://localhost:8000'
```

So if you:
1. Build frontend without `VITE_API_URL` → Uses default
2. Set `VITE_API_URL` later → **Old build still has old value**
3. Must rebuild → New build has new value

## Quick Checklist

- [ ] `VITE_API_URL` is set in Frontend Variables tab
- [ ] Value includes `https://` (not just domain)
- [ ] Value is: `https://vibecation-backend.up.railway.app`
- [ ] Triggered a new build/deployment
- [ ] Build logs show correct `VITE_API_URL`
- [ ] Tested in browser - console shows correct URL
- [ ] API requests go to backend (not frontend)

## Common Mistakes

### ❌ Wrong: Missing Protocol
```bash
VITE_API_URL=vibecation-backend.up.railway.app
```
Result: Treated as relative path

### ❌ Wrong: Trailing Slash
```bash
VITE_API_URL=https://vibecation-backend.up.railway.app/
```
Result: Might cause issues with path joining

### ✅ Correct
```bash
VITE_API_URL=https://vibecation-backend.up.railway.app
```

## Still Not Working?

1. **Clear browser cache** - Old JavaScript might be cached
2. **Hard refresh** - Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
3. **Check build logs** - Verify `VITE_API_URL` was passed correctly
4. **Check browser console** - `import.meta.env.VITE_API_URL` should show backend URL
5. **Check Network tab** - Request URL should be backend, not frontend



