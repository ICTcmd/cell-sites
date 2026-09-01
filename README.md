# 📡 Cell Site Mapping & Analytics System

<div align="center">

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Node](https://img.shields.io/badge/node-18+-green.svg)
![PostgreSQL](https://img.shields.io/badge/postgresql-14+-blue.svg)

**End-to-end solution for mapping and analyzing mobile network tower infrastructure**

[Features](#-features) • [Demo](#-demo) • [Setup](#-quick-start) • [Architecture](#-architecture) • [Accuracy](#-accuracy) • [Deployment](#-deployment)

</div>

---

## 🎯 Overview

A professional-grade system for locating, logging, and visualizing cellular network towers using crowdsourced telemetry data. Built for **Smart Communications (Philippines)** but adaptable to any carrier.

**Key Capabilities:**
- 📱 Android field data collector with GPS + cell network telemetry
- 🧮 Weighted centroid triangulation algorithm (50-300m accuracy)
- 🗺️ Interactive web dashboard with signal heatmaps
- 📊 PostgreSQL + PostGIS spatial database
- 🔌 REST API for external integrations

---

## ✨ Features

### 📱 Mobile Data Collection
- Real-time cell parameters (eNodeB ID, Cell ID, TAC, PCI, Band)
- Signal metrics (RSRP, RSRQ, RSSI, RSSNR, CQI)
- High-precision GPS with accuracy filtering
- Batch upload with offline queue
- Background collection service

### 🧮 Triangulation Engine
- **Weighted centroid algorithm** using signal strength decay
- Confidence scoring (0-100%) based on:
  - Sample count
  - Spatial clustering
  - Signal consistency
- Outlier removal with IQR method
- Supports LTE (4G) and 5G NR networks

### 🗺️ Interactive Dashboard
- Mapbox GL interactive maps
- Tower markers color-coded by:
  - Frequency band (B1, B3, B28, B41, N78)
  - Confidence score
  - Network type (2G/3G/4G/5G)
- Signal strength heatmap layer
- Dead zone analysis
- Real-time statistics

### 🔌 REST API
- OpenAPI/Swagger documentation
- Field log ingestion endpoints
- Tower query and filter
- GeoJSON export
- External API integration (OpenCelliD)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ANDROID FIELD COLLECTOR                   │
│  • TelephonyManager (Cell Info: eNodeB, PCI, TAC, Band)    │
│  • FusedLocationProvider (GPS: Lat/Long, Accuracy)         │
│  • Batch Upload with Offline Queue                          │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP POST /api/v1/field-logs/batch
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND (Python)                  │
│  • Field Log Ingestion & Validation                         │
│  • Triangulation Engine (Weighted Centroid)                 │
│  • External API Integration (OpenCelliD, CellMapper)        │
│  • GeoJSON Heatmap Generation                               │
└────────────────────┬────────────────────────────────────────┘
                     │ SQLAlchemy ORM + GeoAlchemy2
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              POSTGRESQL + POSTGIS DATABASE                   │
│  Tables:                                                     │
│    • field_logs (raw telemetry data)                        │
│    • cell_towers (calculated tower locations)               │
│    • tower_sectors (directional coverage areas)             │
│  Spatial Indexes: GIST on geometry columns                  │
└────────────────────┬────────────────────────────────────────┘
                     │ REST API (JSON)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                 REACT/NEXT.JS DASHBOARD                      │
│  • Mapbox GL Interactive Map                                │
│  • Tower Markers (Frequency Band Color-Coding)              │
│  • Signal Heatmap Overlay                                   │
│  • Filters: Network Type, Band, Confidence                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Accuracy

**Expected Accuracy: 50-300 meters** from actual tower location

| Confidence Score | Typical Accuracy | Recommendation |
|-----------------|------------------|----------------|
| **80-100%** | 50-150m | Excellent - Trust highly |
| **60-80%** | 150-250m | Good - Usable |
| **40-60%** | 250-400m | Fair - Needs more data |
| **<40%** | 300m+ | Poor - Collect more samples |

**Factors Affecting Accuracy:**
- GPS quality (aim for <20m accuracy)
- Sample count (30+ samples recommended)
- Sample distribution (collect from multiple angles)
- Environment (urban vs rural, obstacles)
- Frequency band (higher frequency = better accuracy)

📖 **[Read Full Accuracy Analysis](ACCURACY_ANALYSIS.md)**

---

## 🚀 Quick Start

### Prerequisites
- PostgreSQL 14+ with PostGIS
- Python 3.9+
- Node.js 18+
- Android Studio (for mobile app)
- Mapbox account (free tier)

### 1️⃣ Database Setup
```bash
cd database
psql -U postgres -c "CREATE DATABASE cellsite_db;"
psql -U postgres -d cellsite_db -f schema.sql
```

### 2️⃣ Backend Setup
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your database credentials

uvicorn main:app --reload
```

Visit: `http://localhost:8000/docs` for API documentation

### 3️⃣ Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env.local
# Add your Mapbox token to .env.local

npm run dev
```

Visit: `http://localhost:3000`

### 4️⃣ Android App
1. Open `android-collector` in Android Studio
2. Update API URL in `CellDataCollector.kt`
3. Build APK
4. Install on device and grant permissions

📖 **[Detailed Setup Guide](SETUP_GUIDE.md)**

---

## 🌐 Deployment

### Deploy to Vercel (Frontend)
```bash
cd frontend
npm install -g vercel
vercel login
vercel --prod
```

### Deploy Backend
**Options:**
- **Railway** (Recommended - Free tier)
- **Render.com** (Free tier)
- **DigitalOcean App Platform**
- **AWS EC2 + RDS**

📖 **[Full Deployment Guide](DEPLOYMENT.md)**

---

## 📱 Supported Networks

**Smart Communications (Philippines)**
- MCC: 515
- MNC: 03 (LTE/5G), 05 (Legacy)
- Bands: B1, B3, B5, B7, B8, B28, B41, N78

**Easily adaptable to other carriers** - just update MCC/MNC in configuration.

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|-----------|
| **Mobile App** | Kotlin, Android SDK, TelephonyManager, FusedLocationProvider |
| **Backend** | Python, FastAPI, SQLAlchemy, GeoAlchemy2, NumPy, GeoPandas |
| **Database** | PostgreSQL 14+, PostGIS 3.x |
| **Frontend** | React, Next.js, TypeScript, Mapbox GL JS, Tailwind CSS |
| **Deployment** | Vercel (Frontend), Railway/Render (Backend) |

---

## 📚 API Endpoints

### Field Data Collection
- `POST /api/v1/field-logs` - Submit single measurement
- `POST /api/v1/field-logs/batch` - Batch upload (recommended)
- `GET /api/v1/field-logs` - Query field logs

### Tower Management
- `GET /api/v1/towers` - List all towers
- `GET /api/v1/towers/{enodeb_id}` - Get specific tower
- `GET /api/v1/towers/{tower_id}/sectors` - Get tower sectors

### Triangulation
- `POST /api/v1/triangulation/calculate` - Calculate single tower location
- `POST /api/v1/triangulation/batch` - Process all towers

### Visualization
- `GET /api/v1/heatmap/signal` - Get signal heatmap (GeoJSON)

### External APIs
- `POST /api/v1/external/seed-opencellid` - Import from OpenCelliD

**Full documentation**: `http://localhost:8000/docs`

---

## 📖 Documentation

- [**Setup Guide**](SETUP_GUIDE.md) - Detailed installation instructions
- [**Deployment Guide**](DEPLOYMENT.md) - GitHub & Vercel deployment
- [**Accuracy Analysis**](ACCURACY_ANALYSIS.md) - How accurate is this system?

---

## 🤝 Contributing

Contributions welcome! Please read our contributing guidelines and submit pull requests.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- OpenCelliD for crowdsourced cell tower data
- Mapbox for mapping infrastructure
- FastAPI and Next.js communities

---

## 📧 Contact

For questions or support, open an issue on GitHub.

---

<div align="center">

**Built with ❤️ for the telecom research community**

⭐ Star this repo if you find it useful!

</div>
