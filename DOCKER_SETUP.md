# 🐳 Docker Setup Guide - Cell Site Mapping System

## ✅ Prerequisites

- Docker Desktop installed and running
- 4GB RAM available
- Port 8000 and 5432 available

## 🚀 Quick Start (3 Commands!)

### Step 1: Navigate to Project
```bash
cd C:\Users\OJTBEEG\Desktop\cracked\cell-site-system
```

### Step 2: Start Everything
```bash
docker-compose up -d
```

This will:
- ✅ Download PostgreSQL with PostGIS
- ✅ Create database and run schema.sql automatically
- ✅ Build Python backend
- ✅ Install all dependencies (inside container, not your system!)
- ✅ Start both services

### Step 3: Check Status
```bash
docker-compose ps
```

You should see:
```
NAME                 STATUS
cellsite-db          Up (healthy)
cellsite-backend     Up
```

---

## 🌐 Access Your System

### Backend API
- **URL**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Database
- **Host**: localhost
- **Port**: 5432
- **Database**: cellsite_db
- **User**: postgres
- **Password**: cellsite123

---

## 📱 Connect Android App

Edit `CellDataCollector.kt`:

### If phone is on same WiFi as computer:
```kotlin
private val apiBaseUrl: String = "http://YOUR_COMPUTER_IP:8000/api/v1"
```

**Find your computer IP:**
```bash
# Windows
ipconfig

# Look for IPv4 Address (e.g., 192.168.1.100)
```

### Using ngrok (for internet access):
```bash
# Install ngrok: https://ngrok.com/download
ngrok http 8000
```

Use the ngrok URL in your Android app:
```kotlin
private val apiBaseUrl: String = "https://abc123.ngrok.io/api/v1"
```

---

## 🔧 Useful Docker Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Database only
docker-compose logs -f database
```

### Restart Services
```bash
# Restart everything
docker-compose restart

# Restart backend only
docker-compose restart backend
```

### Stop Everything
```bash
docker-compose down
```

### Stop and Remove Data
```bash
docker-compose down -v
```

### Rebuild After Code Changes
```bash
docker-compose up -d --build
```

---

## 🗄️ Database Management

### Access PostgreSQL Shell
```bash
docker-compose exec database psql -U postgres -d cellsite_db
```

### Run SQL Commands
```sql
-- Check tables
\dt

-- View towers
SELECT * FROM cell_towers;

-- View field logs
SELECT COUNT(*) FROM field_logs;

-- Exit
\q
```

### Backup Database
```bash
docker-compose exec database pg_dump -U postgres cellsite_db > backup.sql
```

### Restore Database
```bash
cat backup.sql | docker-compose exec -T database psql -U postgres -d cellsite_db
```

---

## 🔍 Testing the System

### 1. Check Backend Health
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status":"healthy","timestamp":"2024-..."}
```

### 2. Check Database Connection
```bash
curl http://localhost:8000/
```

Expected response:
```json
{
  "service": "Cell Site Mapping System",
  "version": "v1",
  "status": "operational",
  "city": "Manila",
  "country": "Philippines"
}
```

### 3. View API Documentation
Open browser: http://localhost:8000/docs

---

## 🌍 Expose Backend to Internet (ngrok)

### Option 1: Free ngrok
```bash
# Install ngrok
choco install ngrok

# Or download from https://ngrok.com/download

# Start tunnel
ngrok http 8000
```

You'll get a URL like: `https://abc123.ngrok-free.app`

### Option 2: Update Vercel Frontend
Go to Vercel dashboard → Environment Variables:

**Update:**
```
NEXT_PUBLIC_API_URL = http://YOUR_COMPUTER_IP:8000/api/v1
```

Or with ngrok:
```
NEXT_PUBLIC_API_URL = https://abc123.ngrok-free.app/api/v1
```

**Redeploy frontend** to apply changes.

---

## 📊 System Architecture with Docker

```
┌─────────────────────────────────────────────────────┐
│               YOUR COMPUTER (Docker)                 │
│                                                      │
│  ┌──────────────────┐      ┌──────────────────┐   │
│  │  PostgreSQL      │◄─────┤  FastAPI         │   │
│  │  + PostGIS       │      │  Backend         │   │
│  │  Port: 5432      │      │  Port: 8000      │   │
│  └──────────────────┘      └──────────────────┘   │
│           ▲                         ▲               │
└───────────┼─────────────────────────┼───────────────┘
            │                         │
            │                         │
      ┌─────┴─────────────────────────┴─────┐
      │                                     │
      │                                     │
┌─────▼──────┐                    ┌────────▼─────┐
│  Database  │                    │   Android    │
│   Admin    │                    │     App      │
│   Tools    │                    │  (WiFi/Data) │
└────────────┘                    └──────────────┘
                                         │
                                         │
                                  ┌──────▼──────┐
                                  │   Vercel    │
                                  │  Frontend   │
                                  └─────────────┘
```

---

## ❓ Troubleshooting

### Port Already in Use
```bash
# Windows - Check what's using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID)
taskkill /PID <PID> /F
```

### Database Won't Start
```bash
# Remove old data and restart
docker-compose down -v
docker-compose up -d
```

### Backend Can't Connect to Database
```bash
# Check if database is healthy
docker-compose ps

# View database logs
docker-compose logs database

# Restart backend
docker-compose restart backend
```

### Can't Access from Android
1. Check if computer firewall is blocking port 8000
2. Verify phone and computer are on same WiFi
3. Use `ipconfig` to confirm IP address
4. Try: `http://192.168.1.XXX:8000/health` from phone browser

### Docker Out of Memory
```bash
# Increase Docker memory in Docker Desktop:
# Settings → Resources → Memory → Set to 4GB
```

---

## 🎯 Production Deployment

While Docker is great for local development, for production consider:

1. **Deploy Docker to VPS** (DigitalOcean, AWS, etc.)
2. **Use Docker Hub** to share images
3. **Add SSL** with nginx reverse proxy
4. **Use docker-compose production configs**

---

## 🔄 Update Workflow

When you update code:

```bash
# 1. Pull latest from GitHub
git pull

# 2. Rebuild and restart
docker-compose up -d --build

# 3. Check logs
docker-compose logs -f
```

---

## 💰 Cost

**100% FREE** for local development!

- ✅ Docker Desktop: Free
- ✅ PostgreSQL: Free
- ✅ All dependencies: Free
- ✅ ngrok: Free tier (with random URLs)

---

## ✅ Benefits of Docker Setup

- 🚀 **Fast**: No compilation issues like Render
- 💻 **Local**: Full control, no cloud limits
- 🔧 **Easy**: One command to start everything
- 🗄️ **Database included**: PostgreSQL + PostGIS ready
- 🔄 **Reproducible**: Works on any machine with Docker
- 🆓 **Free**: No hosting costs

---

## 🎉 Ready to Start!

```bash
cd C:\Users\OJTBEEG\Desktop\cracked\cell-site-system
docker-compose up -d
```

Visit: http://localhost:8000/docs

🚀 **Your Cell Site Mapping System is now running!**
