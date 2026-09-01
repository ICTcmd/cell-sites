# 🚀 Deploy Now - Quick Commands

## Step 1: Push to GitHub

```bash
cd C:\Users\OJTBEEG\Desktop\cracked\cell-site-system

# Initialize Git
git init
git add .
git commit -m "Initial commit: Cell Site Mapping System"

# Create repo on GitHub: https://github.com/new
# Then run (replace YOUR_USERNAME):
git remote add origin https://github.com/YOUR_USERNAME/cell-site-mapping.git
git branch -M main
git push -u origin main
```

✅ **Your code is now on GitHub!**

---

## Step 2: Deploy Frontend to Vercel

### Option A: Via Vercel Dashboard (Easiest)

1. Go to **https://vercel.com/** and sign in with GitHub
2. Click **"New Project"**
3. Import your `cell-site-mapping` repository
4. Configure:
   - **Root Directory**: `frontend`
   - **Framework**: Next.js (auto-detected)
5. Add **Environment Variables**:
   ```
   NEXT_PUBLIC_API_URL = (leave blank for now)
   NEXT_PUBLIC_MAPBOX_TOKEN = your_mapbox_token
   ```
6. Click **Deploy**

### Option B: Via CLI (Fast)

```bash
cd frontend

# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
vercel

# Deploy to production
vercel --prod
```

✅ **Your frontend is now live at: `https://your-app.vercel.app`**

---

## Step 3: Deploy Backend to Railway

1. Go to **https://railway.app/** and sign in with GitHub
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your `cell-site-mapping` repository
4. Railway will detect the code

### Add PostgreSQL Database:
- Click **"New"** → **"Database"** → **"PostgreSQL"**
- Railway creates and links it automatically

### Configure Backend Service:
- Click on your service
- Go to **"Settings"**
- **Root Directory**: `backend`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Add Environment Variables:
```
DATABASE_URL = ${{Postgres.DATABASE_URL}}
CORS_ORIGINS = https://your-app.vercel.app
CITY_NAME = Manila
COUNTRY = Philippines
BBOX_MIN_LAT = 14.40
BBOX_MAX_LAT = 14.80
BBOX_MIN_LON = 120.90
BBOX_MAX_LON = 121.15
```

### Deploy Database Schema:
- Go to PostgreSQL service → **"Data"** tab
- Click **"Query"**
- Copy/paste contents of `database/schema.sql`
- Click **"Run"**

✅ **Your backend is now live at: `https://your-app.up.railway.app`**

---

## Step 4: Connect Frontend to Backend

1. Go to Vercel dashboard
2. Your project → **"Settings"** → **"Environment Variables"**
3. Edit `NEXT_PUBLIC_API_URL`:
   ```
   https://your-app.up.railway.app/api/v1
   ```
4. Go to **"Deployments"** → Click **"Redeploy"**

---

## Step 5: Test Your Deployment

### Test Backend:
```bash
curl https://your-app.up.railway.app/health
```

Expected response:
```json
{"status":"healthy","timestamp":"2024-..."}
```

### Test Frontend:
- Open `https://your-app.vercel.app`
- You should see the map interface

### Test Android App:
- Edit `CellDataCollector.kt`:
  ```kotlin
  private val apiBaseUrl: String = "https://your-app.up.railway.app/api/v1"
  ```
- Rebuild APK
- Install and test

---

## 🎉 You're Live!

**Your URLs:**
- 🌐 Frontend: `https://your-app.vercel.app`
- 🔌 Backend API: `https://your-app.up.railway.app/api/v1`
- 📚 API Docs: `https://your-app.up.railway.app/docs`

---

## Quick Troubleshooting

### Backend 502 Error?
- Check Railway logs
- Verify PostgreSQL is connected
- Ensure schema.sql was run

### Frontend shows "Failed to fetch"?
- Verify `NEXT_PUBLIC_API_URL` is correct
- Check CORS_ORIGINS in backend includes your Vercel domain
- Test backend health endpoint directly

### Can't push to GitHub?
```bash
# If remote already exists:
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/cell-site-mapping.git
git push -u origin main
```

---

## Alternative Backend Options

### Don't want Railway? Try:

**Render.com (Free):**
1. https://render.com/ → New Web Service
2. Connect GitHub
3. Build: `pip install -r backend/requirements.txt`
4. Start: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`

**Heroku:**
```bash
heroku create cell-site-backend
heroku addons:create heroku-postgresql:mini
git push heroku main
```

---

## Get Your Mapbox Token

1. Create account: https://account.mapbox.com/
2. Go to **"Access tokens"**
3. Copy your **"Default public token"**
4. Use in `NEXT_PUBLIC_MAPBOX_TOKEN`

---

## Costs (All have free tiers!)

- ✅ **Vercel**: Free (100GB bandwidth)
- ✅ **Railway**: $5 free credit/month
- ✅ **GitHub**: Free (public repos)
- ✅ **Mapbox**: Free (50k map loads/month)

**Total: $0 for testing and small deployments!**

---

Need help? Check the logs:
- **Vercel**: Dashboard → Deployments → Function Logs
- **Railway**: Dashboard → Service → Logs (real-time)
