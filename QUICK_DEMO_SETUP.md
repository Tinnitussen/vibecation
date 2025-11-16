# Quick Demo Setup: Azure OpenAI Environment Variables

## Problem

The chat prompt isn't working because Azure OpenAI environment variables aren't set in Railway production.

## Quick Fix (5 minutes)

### Step 1: Get Your Azure OpenAI Credentials

You need these 3 values from your Azure OpenAI resource:
1. **API Key** - Found in Azure Portal → Your OpenAI Resource → Keys and Endpoint
2. **Endpoint URL** - Format: `https://your-resource-name.openai.azure.com`
3. **API Version** - Usually `2024-02-15-preview` or `2024-05-01-preview`

### Step 2: Add to Railway Backend Service

1. **Go to Railway Dashboard**
2. **Open your Backend service**
3. **Click "Variables" tab**
4. **Add these 3 variables:**

```bash
AZURE_OPENAI_API_KEY=your-actual-api-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

**Important:**
- Replace `your-actual-api-key-here` with your real API key
- Replace `your-resource-name` with your actual Azure resource name
- Use the API version that matches your Azure OpenAI deployment

### Step 3: Save and Redeploy

1. **Click "Add" or "Save"** for each variable
2. **Railway will automatically redeploy** the backend service
3. **Wait for deployment to complete** (usually 1-2 minutes)

### Step 4: Test Chat

1. Open your app
2. Try the chat prompt
3. Should work now! ✅

## Where to Find Azure OpenAI Credentials

### Option 1: Azure Portal
1. Go to [portal.azure.com](https://portal.azure.com)
2. Navigate to your Azure OpenAI resource
3. Go to **"Keys and Endpoint"** section
4. Copy:
   - **KEY 1** or **KEY 2** (either works)
   - **Endpoint** URL

### Option 2: Azure CLI
```bash
az cognitiveservices account keys list \
  --name your-resource-name \
  --resource-group your-resource-group
```

## Complete Backend Variables Checklist

Your Backend service should have:

```bash
# MongoDB (internal network)
MONGODB_URL=${{ MongoDB.MONGO_URL }}

# Azure OpenAI (for chat)
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# CORS
CORS_ORIGINS=https://vibecation.up.railway.app

# Python
PYTHONPATH=/app
```

## Troubleshooting

### Chat still not working?

1. **Check backend logs:**
   - Go to Backend service → **Deployments** tab
   - Click latest deployment → **View Logs**
   - Look for errors related to Azure OpenAI

2. **Verify variables are set:**
   - Backend service → Variables tab
   - Make sure all 3 Azure OpenAI variables exist
   - Check for typos in variable names

3. **Check API key is valid:**
   - Make sure you copied the full key
   - No extra spaces or quotes
   - Key hasn't expired

4. **Verify endpoint format:**
   - Should start with `https://`
   - Should end with `.openai.azure.com`
   - No trailing slash

5. **Check API version:**
   - Must match your Azure OpenAI deployment version
   - Common: `2024-02-15-preview`, `2024-05-01-preview`, `2024-08-01-preview`

### Common Errors

**"Invalid API key"**
- Check you copied the full key
- No extra spaces
- Key hasn't been regenerated

**"Invalid endpoint"**
- Check URL format
- Make sure it includes `https://`
- Verify resource name is correct

**"API version not supported"**
- Check your Azure OpenAI deployment supports that version
- Try: `2024-05-01-preview` or `2024-08-01-preview`

## Quick Copy-Paste Template

In Railway Backend → Variables tab, add:

```
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

Then fill in your actual values!

## After Setup

Once variables are set and backend redeploys:
- ✅ Chat should work
- ✅ Brainstorm feature should work
- ✅ Trip planning with AI should work

Good luck with your demo! 🚀





