# LLM-Orchestrated Multi-Model Traffic Analysis System

An AI-powered traffic scene perception platform that combines multiple YOLO object-detection models with an LLM orchestration layer to deliver real-time vehicle detection, traffic density analysis, violation detection, and natural-language traffic insights — all through a Django REST API backend and a Next.js dashboard frontend.

> BTech Major Project — Computer Vision + LLM Orchestration for Intelligent Traffic Systems

---

## Overview

Traditional traffic analysis systems rely on a single detection model and produce raw numbers with no interpretation. This system takes a different approach:

1. **Multiple YOLO models** (YOLOv8, YOLOv11, YOLOv12) run detection and are benchmarked/compared against each other for accuracy and speed.
2. **An LLM orchestration layer** (Groq / OpenAI / Anthropic) consumes the structured detection output and produces human-readable insights, summaries, and recommendations.
3. **A real-time streaming pipeline** (Django Channels + WebSockets) pushes live detection results to the frontend as video is processed.
4. **A traffic violation detection module** identifies speed violations and helmet non-compliance from uploaded or streamed video.
5. **A Next.js dashboard** visualizes density, vehicle counts, model comparisons, violation history, and LLM-generated insights.

---

## Key Features

- **Multi-model vehicle detection** — YOLOv8s, YOLOv11s, and YOLOv12s with configurable default/fallback models and an ensemble/comparison mode.
- **Traffic density analysis** — per-frame and aggregated density metrics with historical trends.
- **LLM-powered insights** — natural-language summaries and chat-style Q&A over analysis results, with automatic fallback across LLM providers/models.
- **Real-time video streaming & analysis** — WebSocket-based live video processing via Django Channels.
- **Traffic violation detection** — speed estimation/calculation and helmet detection, with violation history and stats.
- **Model comparison suite** — side-by-side accuracy/speed benchmarking across YOLO versions (basic, advanced, and "ultra" comparison modes).
- **Vehicle tracking** — persistent object tracking across frames (custom tracker + enhanced analyzer).
- **Authentication & sessions** — JWT-based auth with MongoDB-backed user/session management.
- **Analytics dashboard** — charts, metrics, reports, and history views built with Recharts and Tailwind.
- **REST API with interactive docs** — OpenAPI schema via drf-spectacular (Swagger UI + Redoc).

---

## Tech Stack

### Backend
| Component | Technology |
|---|---|
| Framework | Django 4.2 + Django REST Framework |
| Real-time | Django Channels, Redis (channel layer) |
| Task queue | Celery + Redis |
| Database | MongoDB (via `pymongo` / `mongoengine`) |
| Computer vision | Ultralytics YOLO (v8 / v11 / v12), OpenCV, PyTorch |
| LLM providers | Groq, OpenAI, Anthropic |
| Auth | djangorestframework-simplejwt, custom MongoDB JWT auth |
| API docs | drf-spectacular (OpenAPI / Swagger / Redoc) |
| Data/analytics | pandas, numpy, scikit-learn, statsmodels, matplotlib, seaborn |

### Frontend
| Component | Technology |
|---|---|
| Framework | Next.js 14 (App Router) + TypeScript |
| Styling | Tailwind CSS |
| State management | Redux Toolkit (`@reduxjs/toolkit`, `react-redux`) |
| Charts | Recharts |
| Animation | Framer Motion |
| Icons / UX | Heroicons, react-hot-toast |

---

## Project Structure

```
LLM-Orchestrated-Multi-Model-Traffic-Analysis-System/
├── backend/
│   ├── apps/
│   │   ├── analysis/           # Core detection, YOLO analyzers, model comparison, LLM services
│   │   ├── analytics/          # Aggregated analytics endpoints
│   │   ├── authentication/     # JWT auth, MongoDB auth, session management
│   │   ├── llm_integration/    # LLM provider abstraction & chat/insight services
│   │   ├── streaming/          # WebSocket consumers for live video
│   │   ├── traffic_violations/ # Speed & helmet violation detection
│   │   └── users/              # User profile management
│   ├── enhanced_models/        # Enhanced analyzer + vehicle tracker
│   ├── models/                 # YOLO model weights + config (traffic_models_config.json)
│   ├── traffic_analysis/       # Django project settings, URLs, ASGI/WSGI
│   ├── traffic_violations_data/# Sample/uploaded violation media
│   ├── download_models.py      # Script to fetch YOLO model weights
│   ├── manage.py
│   ├── run_quiet.py             # Quiet-mode dev server runner
│   └── requirements*.txt
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js App Router pages (dashboard, analysis, tracking,
│   │   │                        # traffic-violations, upload, visualization, reports, etc.)
│   │   ├── components/          # Reusable UI, LLM chat, analysis cards, auth components
│   │   ├── contexts/             # React auth context
│   │   ├── services/              # API clients (analysis, LLM, violations)
│   │   └── utils/                  # Media & storage utilities
│   ├── package.json
│   └── tailwind.config.js
├── package.json                 # Root scripts to run backend + frontend together
└── README.md
```

---

## Prerequisites

- **Node.js** ≥ 18
- **Python** ≥ 3.8
- **MongoDB** (local instance or connection URI)
- **Redis** (for Channels + Celery)
- API keys for at least one LLM provider (Groq, OpenAI, or Anthropic)

---

## Getting Started

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd LLM-Orchestrated-Multi-Model-Traffic-Analysis-System

# Installs root, frontend, and backend dependencies
npm run install:all
```

### 2. Configure environment variables

Create a `.env` file inside `backend/` (values below match the defaults read in `settings.py`):

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# MongoDB
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DB_NAME=traffic_analysis_db
MONGO_USERNAME=
MONGO_PASSWORD=
MONGODB_URI=mongodb://localhost:27017/

# Redis / Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001

# YOLO
YOLO_MODEL_PATH=models/yolov8s.pt
YOLO_DEVICE=cpu   # or cuda:0 for GPU

# LLM
LLM_PROVIDER=groq   # groq | openai | anthropic
GROQ_API_KEY=
GROQ_MODEL=gpt-oss-20b
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
```

### 3. Download YOLO model weights

```bash
npm run models
# or directly:
cd backend && python download_models.py
```

This fetches `yolov8s.pt`, `yolo11s.pt`, and `yolo12s.pt` into `backend/models/`.

### 4. Run database migrations

```bash
cd backend
python manage.py migrate
```

### 5. Start the app

From the project root, run backend and frontend together:

```bash
npm run start
```

This starts:
- **Backend** (Django) on `http://localhost:8000`
- **Frontend** (Next.js) on `http://localhost:3001`

Or run them individually:

```bash
npm run start:backend   # Django on 0.0.0.0:8000
npm run start:frontend  # Next.js on port 3001
```

---

## API Documentation

Once the backend is running, interactive API docs are available at:

- Swagger UI: `http://localhost:8000/api/docs/`
- Redoc: `http://localhost:8000/api/redoc/`
- OpenAPI schema: `http://localhost:8000/api/schema/`

### Core API endpoints

| Endpoint | Purpose |
|---|---|
| `/api/v1/auth/` | Registration, login, JWT session management |
| `/api/v1/analysis/` | Vehicle/traffic detection, model comparison, video analysis |
| `/api/v1/streaming/` | WebSocket-driven live video analysis |
| `/api/v1/llm/` | LLM-generated insights and chat |
| `/api/v1/analytics/` | Aggregated metrics and reporting |
| `/api/v1/users/` | User profile management |
| `/api/v1/traffic-violations/` | Speed & helmet violation detection and history |

---

## Available Scripts (root `package.json`)

| Script | Description |
|---|---|
| `npm run start` / `npm run dev` | Run backend + frontend concurrently |
| `npm run install:all` | Install root, frontend, and backend dependencies |
| `npm run setup` | Install everything + download YOLO models |
| `npm run models` | Download YOLO model weights |
| `npm run build` | Build the frontend for production |
| `npm run build:backend` | Collect Django static files |
| `npm run test` | Run backend test suite |
| `npm run clean` | Remove `node_modules`, `.next`, and Python cache files |

---

## Frontend Pages

The Next.js app includes dedicated views for:

- `dashboard` — overview of system status and recent activity
- `upload` / `video-analysis` — upload and analyze video footage
- `realtime` / `tracking` — live streaming detection and object tracking
- `analysis` / `comprehensive-analysis` — detailed detection results and multi-model comparison
- `density` / `detection` / `metrics` — traffic density and vehicle-count visualizations
- `traffic-violations` — live violation detection, video upload, speed settings, and violation history
- `insights` — LLM-generated natural-language insights and chat
- `reports` / `history` — historical analysis reports
- `visualization` — charts and data visualization
- `login` / `register` / `profile` — authentication and user account management

---

## Notes

- MongoDB is used as the primary data store (via `pymongo`/`mongoengine`) rather than Django's default relational ORM setup.
- The system is designed to gracefully fall back between YOLO model versions and between LLM providers/models if a preferred option is unavailable.
- GPU acceleration is supported by setting `YOLO_DEVICE=cuda:0` (requires a CUDA-enabled PyTorch installation).

---

## License

MIT
