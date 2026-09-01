# Cell Site Mapping & Analytics System - Setup Guide

Complete setup instructions for deploying the full stack system.

## Prerequisites

- **PostgreSQL 14+** with PostGIS extension
- **Python 3.9+**
- **Node.js 18+** and npm
- **Android Studio** (for mobile app)
- **Mapbox Account** (free tier works)

## Step-by-Step Setup

### 1. Database Setup

#### Install PostgreSQL and PostGIS

**Windows:**
```bash
# Download from https://www.postgresql.org/download/windows/
# PostGIS installer: https://postgis.net/install/
```

**Create Database:**
```bash
psql -U postgres
CREATE DATABASE cellsite_db;
\q
```

**Run Schema Script:**
```bash
cd database
psql -U postgres -d cellsite_db -f schema.sql
```

Verify tables:
```sql
\c cellsite_db
\dt
-- You should see: field_logs, cell_towers, tower_sectors, external_api_cache
```

### 2. Backend Setup (Python FastAPI)

#### Navigate to Backend Directory
```bash
cd backend
```

#### Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```

#### Configure Environment
```bash
copy .env.example .env
```

Edit `.env` file:
```ini
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/cellsite_db
BBOX_MIN_LAT=14.40
BBOX_MAX_LAT=14.80
BBOX_MIN_LON=120.90
BBOX_MAX_LON=121.15
CITY_NAME=Manila
COUNTRY=Philippines
```

**Important:** Replace bounding box coordinates with your city's coordinates!

#### Run Backend Server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Visit: `http://localhost:8000/docs` to see API documentation

### 3. Android App Setup

#### Open in Android Studio
1. Open Android Studio
2. File → Open → Select `android-collector` folder
3. Wait for Gradle sync

#### Configure Backend URL

Edit `CellDataCollector.kt`:
```kotlin
class CellDataCollector(
    private val context: Context,
    private val apiBaseUrl: String = "http://YOUR_COMPUTER_IP:8000/api/v1"
)
```

**Get your computer's IP:**
```bash
# Windows
ipconfig

# Look for IPv4 Address (e.g., 192.168.1.100)
```

#### Build and Install APK
1. Build → Build Bundle(s) / APK(s) → Build APK(s)
2. Transfer APK to Android device
3. Enable "Install from Unknown Sources"
4. Install APK

#### Grant Permissions
On first run, grant:
- Location (Fine & Background)
- Phone State

### 4. Frontend Dashboard Setup

#### Navigate to Frontend
```bash
cd frontend
```

#### Install Dependencies
```bash
npm install
```

#### Configure Environment
```bash
copy .env.example .env.local
```

Edit `.env.local`:
```ini
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_MAPBOX_TOKEN=YOUR_MAPBOX_TOKEN
```

**Get Mapbox Token:**
1. Create account: https://account.mapbox.com/
2. Copy default public token
3. Paste into `.env.local`

#### Run Development Server
```bash
npm run dev
```

Visit: `http://localhost:3000`

### 5. System Testing

#### Test Backend Health
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy", "timestamp": "2024-01-15T10:30:00Z"}
```

#### Test Android Data Collection

1. Open app on Android device
2. Start collection
3. Walk around outdoors for 5-10 minutes
4. Check backend logs for incoming data

#### Verify Data in Database
```sql
SELECT COUNT(*) FROM field_logs;
SELECT * FROM field_logs ORDER BY timestamp_utc DESC LIMIT 5;
```

#### Run Triangulation
```bash
curl -X POST http://localhost:8000/api/v1/triangulation/batch?min_samples=5
```

#### View on Dashboard
1. Open `http://localhost:3000`
2. You should see tower markers appear
3. Toggle heatmap to see signal coverage

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    ANDROID FIELD COLLECTOR                   │
│  - TelephonyManager (Cell Info)                             │
│  - FusedLocationProvider (GPS)                              │
│  - Batch Upload with Offline Queue                          │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP POST /api/v1/field-logs/batch
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND                           │
│  - Field Log Ingestion                                      │
│  - Triangulation Engine (Weighted Centroid)                 │
│  - External API Integration (OpenCelliD)                    │
│  - GeoJSON Heatmap Generation                               │
└────────────────────┬────────────────────────────────────────┘
                     │ SQLAlchemy ORM
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              POSTGRESQL + POSTGIS DATABASE                   │
│  Tables:                                                     │
│    - field_logs (raw telemetry)                             │
│    - cell_towers (calculated locations)                     │
│    - tower_sectors (directional coverage)                   │
│  Spatial Indexes: GIST on location columns                  │
└────────────────────┬────────────────────────────────────────┘
                     │ REST API (GET /api/v1/towers)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                 REACT/NEXT.JS DASHBOARD                      │
│  - Mapbox GL Interactive Map                                │
│  - Tower Markers (Color-coded by Band/Confidence)           │
│  - Signal Heatmap Layer                                     │
│  - Real-time Statistics                                     │
└─────────────────────────────────────────────────────────────┘
```

## Triangulation Algorithm Explained

The system uses a **weighted centroid** algorithm:

### Formula

```
Tower Location = Σ(GPS_point_i × Weight_i) / Σ(Weight_i)

Where:
Weight_i = (RSRP_i / RSRP_min)^2.5
```

### Why This Works

1. **Signal Strength Decay**: RSRP decreases with distance from tower
2. **Higher RSRP = Closer to Tower**: Measurements with stronger signal get more weight
3. **Weighted Average**: Tower location is the "center of mass" weighted by signal strength

### Confidence Score

Calculated from (0-100):
- **Sample Count** (0-40 pts): More measurements = higher confidence
- **Spatial Clustering** (0-40 pts): Tighter cluster = higher confidence
- **RSRP Consistency** (0-20 pts): Lower variance = higher confidence

## Common Issues & Troubleshooting

### Android App Can't Connect to Backend

**Problem:** Connection refused or timeout

**Solution:**
1. Ensure backend is running: `curl http://localhost:8000/health`
2. Use computer's local IP, not `localhost` or `127.0.0.1`
3. Disable Windows Firewall temporarily for testing
4. Ensure phone and computer on same WiFi network

### No Data Appearing in Dashboard

**Problem:** Map is empty

**Solution:**
1. Check if field logs exist: `SELECT COUNT(*) FROM field_logs;`
2. Run triangulation: `POST /api/v1/triangulation/batch`
3. Verify towers exist: `SELECT COUNT(*) FROM cell_towers;`
4. Check browser console for API errors

### PostGIS Extension Not Found

**Problem:** `ERROR: type "geometry" does not exist`

**Solution:**
```sql
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_topology;
```

### Low Triangulation Confidence

**Problem:** Towers show < 50% confidence

**Solution:**
- Collect more field data (aim for 20+ samples per tower)
- Walk at various distances from tower (100m to 2km)
- Ensure GPS accuracy < 20 meters
- Collect in open areas (avoid buildings that block signal)

## Data Collection Best Practices

1. **Coverage Area**: Walk/drive in grid pattern around target area
2. **Measurement Density**: Aim for 1 measurement every 50-100 meters
3. **Multiple Angles**: Approach each tower from different directions
4. **GPS Quality**: Only collect when GPS accuracy < 30 meters
5. **Time of Day**: Avoid peak hours (network congestion affects signal)
6. **Weather**: Clear weather provides more consistent readings

## Production Deployment

### Backend (FastAPI)

```bash
# Use production WSGI server
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
```

### Frontend (Next.js)

```bash
npm run build
npm run start
```

### Database Backups

```bash
# Automated backup script
pg_dump -U postgres cellsite_db > backup_$(date +%Y%m%d).sql
```

## API Endpoints Reference

### Field Data Collection
- `POST /api/v1/field-logs` - Submit single measurement
- `POST /api/v1/field-logs/batch` - Batch upload
- `GET /api/v1/field-logs` - Query measurements

### Tower Data
- `GET /api/v1/towers` - List all towers
- `GET /api/v1/towers/{enodeb_id}` - Get specific tower
- `GET /api/v1/towers/{tower_id}/sectors` - Get tower sectors

### Triangulation
- `POST /api/v1/triangulation/calculate` - Calculate single tower
- `POST /api/v1/triangulation/batch` - Calculate all towers

### Visualization
- `GET /api/v1/heatmap/signal` - GeoJSON heatmap data

### External Data
- `POST /api/v1/external/seed-opencellid` - Import from OpenCelliD

## License

MIT License - See LICENSE file

## Support

For issues or questions:
- Check API docs: `http://localhost:8000/docs`
- Review logs: Backend terminal and browser console
- Database queries for debugging data flow
