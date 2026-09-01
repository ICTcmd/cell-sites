# Deployment Guide - GitHub & Vercel

## Part 1: Push to GitHub

### Step 1: Initialize Git Repository

```bash
cd C:\Users\OJTBEEG\Desktop\cracked\cell-site-system

# Initialize git
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Cell Site Mapping & Analytics System"
```

### Step 2: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `cell-site-mapping`
3. Description: `Cell tower mapping and analytics system for Smart Communications network`
4. Choose **Public** or **Private**
5. **DO NOT** initialize with README (we already have one)
6. Click **Create repository**

### Step 3: Push to GitHub

```bash
# Add GitHub remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/cell-site-mapping.git

# Push to main branch
git branch -M main
git push -u origin main
```

---

## Part 2: Deploy Frontend to Vercel

### Option A: Deploy via Vercel Dashboard (Easiest)

1. **Go to Vercel**: https://vercel.com/
2. **Sign in** with GitHub
3. Click **"Add New..."** → **"Project"**
4. **Import** your `cell-site-mapping` repository
5. **Configure Project:**
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

6. **Environment Variables** (Add these):
   ```
   NEXT_PUBLIC_API_URL=https://your-backend-url.com/api/v1
   NEXT_PUBLIC_MAPBOX_TOKEN=your_mapbox_token_here
   ```

7. Click **Deploy**

### Option B: Deploy via Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Navigate to frontend
cd frontend

# Login to Vercel
vercel login

# Deploy
vercel

# Follow prompts:
# - Link to existing project? No
# - Project name: cell-site-mapping
# - Directory: ./
# - Override settings? No

# Add environment variables
vercel env add NEXT_PUBLIC_API_URL
vercel env add NEXT_PUBLIC_MAPBOX_TOKEN

# Deploy to production
vercel --prod
```

---

## Part 3: Deploy Backend (Multiple Options)

### Option 1: Railway (Recommended - Free Tier)

1. **Go to**: https://railway.app/
2. **Sign in** with GitHub
3. Click **"New Project"** → **"Deploy from GitHub repo"**
4. Select your repository
5. **Add PostgreSQL database**:
   - Click **"New"** → **"Database"** → **"PostgreSQL"**
6. **Configure backend service**:
   - Root directory: `backend`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
7. **Add environment variables**:
   ```
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   OPENCELLID_API_KEY=your_key
   CORS_ORIGINS=https://your-vercel-app.vercel.app
   ```
8. **Deploy**

### Option 2: Render.com (Free Tier)

1. **Go to**: https://render.com/
2. **New** → **Web Service**
3. Connect GitHub repository
4. **Settings**:
   - Name: `cell-site-backend`
   - Environment: `Python 3`
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
5. **Add PostgreSQL database**:
   - **New** → **PostgreSQL**
   - Connect to web service
6. **Environment Variables**:
   ```
   DATABASE_URL=${{DATABASE_URL}}
   PYTHON_VERSION=3.11.0
   ```
7. **Create Web Service**

### Option 3: DigitalOcean App Platform

1. **Go to**: https://cloud.digitalocean.com/apps
2. **Create App** → **GitHub**
3. Select repository
4. **Configure**:
   - Type: Web Service
   - Source Directory: `backend`
   - Run Command: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app`
5. **Add PostgreSQL managed database**
6. **Environment Variables**
7. **Deploy**

### Option 4: AWS (EC2 + RDS)

**This requires more setup but gives full control:**

```bash
# SSH into EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Install dependencies
sudo apt update
sudo apt install python3-pip postgresql-client

# Clone repository
git clone https://github.com/YOUR_USERNAME/cell-site-mapping.git
cd cell-site-mapping/backend

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install and configure Nginx
sudo apt install nginx

# Setup systemd service for automatic startup
sudo nano /etc/systemd/system/cellsite.service
```

---

## Part 4: Database Setup (Production)

### After deploying backend with database:

```bash
# Connect to your production database
psql $DATABASE_URL

# Run schema
\i database/schema.sql

# Verify
\dt
```

**For Railway/Render:**
- They provide a PostgreSQL connection string
- Use their web console or CLI to run schema.sql

---

## Part 5: Update Frontend with Backend URL

After backend is deployed:

1. Go to Vercel dashboard
2. Your project → **Settings** → **Environment Variables**
3. Update `NEXT_PUBLIC_API_URL` to your backend URL:
   ```
   https://cell-site-backend.railway.app/api/v1
   ```
4. **Redeploy** frontend

---

## Part 6: Update Android App

Edit `CellDataCollector.kt`:
```kotlin
private val apiBaseUrl: String = "https://cell-site-backend.railway.app/api/v1"
```

Rebuild APK and redistribute.

---

## Cost Estimates

### Free Tier Options:
- **Vercel**: Free (Hobby plan) - 100GB bandwidth/month
- **Railway**: $5 credit/month (free tier)
- **Render**: Free tier (limited resources)
- **Supabase**: Free PostgreSQL (500MB storage)

### Paid Options (if you scale):
- **Vercel Pro**: $20/month
- **Railway**: Pay as you go (~$5-20/month)
- **DigitalOcean**: $12/month (droplet + database)

---

## Quick Deployment Commands

```bash
# 1. Initialize and push to GitHub
cd C:\Users\OJTBEEG\Desktop\cracked\cell-site-system
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/cell-site-mapping.git
git push -u origin main

# 2. Deploy frontend to Vercel
cd frontend
npm install -g vercel
vercel login
vercel
vercel --prod

# 3. Copy your backend to Railway/Render via their dashboard
```

---

## Post-Deployment Checklist

- [ ] Frontend loads on Vercel URL
- [ ] Backend API responds at `/health`
- [ ] Database schema deployed
- [ ] Environment variables configured
- [ ] CORS settings allow frontend domain
- [ ] Android app updated with production URL
- [ ] Test end-to-end: Android → Backend → Database → Frontend
- [ ] Monitor logs for errors

---

## Monitoring & Maintenance

### Vercel:
- **Analytics**: Built-in
- **Logs**: Vercel Dashboard → Deployments → Logs

### Railway:
- **Metrics**: CPU, Memory, Network in dashboard
- **Logs**: Real-time in project view

### Database:
- Set up automated backups
- Monitor query performance
- Scale as data grows

---

## Troubleshooting

### "502 Bad Gateway" on backend:
- Check backend logs
- Verify DATABASE_URL is set
- Ensure PostGIS extension installed

### "API request failed" on frontend:
- Check CORS settings in backend
- Verify API URL in frontend environment variables
- Check browser console for exact error

### Android app can't connect:
- Use HTTPS URL (not HTTP)
- Check network permissions
- Verify backend is publicly accessible

---

## Next Steps After Deployment

1. **Test the full flow**: Android → Backend → Frontend
2. **Set up monitoring**: Error tracking (Sentry), analytics
3. **Add authentication**: Protect API endpoints
4. **Scale database**: As data grows, upgrade plan
5. **CDN**: Use Vercel Edge for global performance

Your system is now live! 🚀
