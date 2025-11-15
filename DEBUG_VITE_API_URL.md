# How to Debug VITE_API_URL in Browser

## Problem

You can't use `import.meta.env` directly in the browser console because it's only available in ES modules.

## Solution: Better Ways to Check

### Method 1: Check Network Tab (Easiest)

1. Open your frontend in browser
2. Open **DevTools** → **Network** tab
3. Try to sign up (or make any API call)
4. Look at the request URL

**Should be:**
```
POST https://vibecation-backend.up.railway.app/users ✅
```

**NOT:**
```
POST https://vibecation.up.railway.app/vibecation-backend.up.railway.app/users ❌
```

### Method 2: Check Built JavaScript Files

1. Open **DevTools** → **Sources** tab
2. Look for files like `index-*.js` or `assets/index-*.js`
3. Open one of the built JavaScript files
4. Press **Ctrl+F** (or Cmd+F) to search
5. Search for: `vibecation-backend` or `VITE_API_URL`

You should see the backend URL baked into the code:
```javascript
const API_BASE_URL = "https://vibecation-backend.up.railway.app"
```

### Method 3: Access Through Window Object (Temporary Debug)

Add this temporarily to your `frontend/src/api/client.js`:

```javascript
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Temporary: Expose to window for debugging
if (typeof window !== 'undefined') {
  window.__API_BASE_URL__ = API_BASE_URL
}

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export default apiClient
```

Then in browser console:
```javascript
console.log(window.__API_BASE_URL__)
```

**Remember to remove this after debugging!**

### Method 4: Check Railway Build Logs

1. Go to Railway dashboard
2. Open **Frontend** service
3. Go to **Deployments** tab
4. Click on the latest deployment
5. Check build logs
6. Look for: `Building with VITE_API_URL=...`
7. Should show: `VITE_API_URL=https://vibecation-backend.up.railway.app`

### Method 5: Add Console Log in Code (Temporary)

Temporarily add to `frontend/src/api/client.js`:

```javascript
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Temporary debug log
console.log('API Base URL:', API_BASE_URL)

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export default apiClient
```

Then check browser console when page loads - you'll see the API URL logged.

**Remember to remove after debugging!**

## Quick Check: Network Tab

**The easiest way is to just check the Network tab:**

1. Open DevTools → Network
2. Try signing up
3. Look at the request URL

If it's:
- `https://vibecation-backend.up.railway.app/users` → ✅ Correct!
- `https://vibecation.up.railway.app/vibecation-backend.up.railway.app/users` → ❌ Wrong (relative path)
- `http://localhost:8000/users` → ❌ Wrong (default value)

## What to Look For

After rebuilding, the Network tab should show:
```
Request URL: https://vibecation-backend.up.railway.app/users
Request Method: POST
Status: 201 Created (or appropriate status)
```

If you still see the wrong URL after rebuilding, then:
1. Check Railway Variables tab - make sure `VITE_API_URL` has `https://`
2. Check build logs - verify it was passed during build
3. Clear browser cache and hard refresh



