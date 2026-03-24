<div align="center">

# FRAUD`LENS`

### See fraud before it strikes.

**Real-time transaction anomaly detection engine powered by LightGBM + Autoencoder + Isolation Forest ensemble**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![Redis](https://img.shields.io/badge/Redis-Streams-DC382D?style=flat-square&logo=redis&logoColor=white)](https://redis.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-00D4FF?style=flat-square)](LICENSE)

---

`10,000+ TPS` · `<50ms Scoring` · `0.92 AUROC` · `3 ML Models` · `Explainable AI`

</div>

---

## The Problem

Canadian financial institutions lose **$600M+ annually** to fraud. Current rule-based detection systems generate **95%+ false positives**, exhausting fraud analysts and letting sophisticated attacks through. FraudLens fixes this with real-time ML ensemble scoring and explainable decisions.

## What FraudLens Does

🔍 **Real-Time Scoring** — Processes 10,000+ transactions per second with sub-50ms ML inference via ONNX Runtime

🧠 **Three AI Models** — LightGBM (tabular patterns) + Autoencoder (anomaly detection) + Isolation Forest (rare events) working as an ensemble

📊 **Explainable AI** — Every flagged transaction includes SHAP-based feature attributions showing exactly WHY it was flagged

🗺️ **Geographic Intelligence** — Real-time fraud heatmap with Mapbox showing where attacks are happening

⚡ **Analyst Dashboard** — Professional React dashboard with live feed, alert queue, case management, and analytics

🔄 **Feedback Loop** — Analyst decisions feed back into model retraining for continuous improvement

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Transaction  │────▶│   Feature    │────▶│  ML Scoring   │────▶│   Decision   │────▶│   Analyst    │
│  Generator    │     │    Store     │     │   Engine      │     │   Engine     │     │  Dashboard   │
│              │     │              │     │              │     │              │     │              │
│  Synthetic    │     │  Redis       │     │  LightGBM    │     │  APPROVE     │     │  React +     │
│  transactions │     │  (real-time  │     │  Autoencoder │     │  REVIEW      │     │  TypeScript  │
│  + fraud      │     │  features)   │     │  Isolation   │     │  BLOCK       │     │  Recharts    │
│  patterns     │     │  PostgreSQL  │     │  Forest      │     │  + Alerts    │     │  Mapbox      │
│              │     │  (historical)│     │  SHAP        │     │              │     │  WebSocket   │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Python 3.11+, FastAPI, Redis Streams, Celery, SQLAlchemy |
| **Frontend** | React 18, TypeScript, TailwindCSS, Recharts, Mapbox GL JS |
| **ML/AI** | LightGBM, PyTorch (Autoencoder), scikit-learn, SHAP, ONNX Runtime |
| **Database** | PostgreSQL 16, TimescaleDB, Redis |
| **DevOps** | Docker, AWS ECS, Terraform, GitHub Actions, Prometheus + Grafana |

## Quick Start

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/fraudlens.git
cd fraudlens

# Start infrastructure (Postgres + Redis + Adminer)
docker compose up -d

# Start backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Access
# Backend API docs:  http://localhost:8000/docs
# Database UI:       http://localhost:8080
```

## Project Structure

```
fraudlens/
├── backend/              # FastAPI application (Nisarg)
│   ├── app/
│   │   ├── main.py       # App entry point
│   │   ├── config.py     # Settings & environment
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── api/          # Route handlers
│   │   ├── services/     # Business logic
│   │   ├── ml/           # ML inference & SHAP
│   │   └── db/           # Database utilities
│   ├── tests/
│   └── requirements.txt
├── ml/                   # ML training pipeline (Nisarg)
│   ├── notebooks/        # Jupyter exploration
│   ├── training/         # Production training scripts
│   ├── data/             # Datasets (gitignored)
│   └── models/           # Saved artifacts (gitignored)
├── simulator/            # Synthetic data engine (Nisarg)
├── frontend/             # React dashboard (Deep)
├── infra/                # Terraform, monitoring
├── docs/                 # API contract, architecture docs
├── docker-compose.yml    # Postgres + Redis + Adminer
└── README.md
```

## API Documentation

Full API docs available at `http://localhost:8000/docs` when running locally.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/transactions/score` | Score a transaction in real-time |
| `GET` | `/api/v1/transactions` | List transactions with filters |
| `GET` | `/api/v1/transactions/{id}/explain` | Get SHAP explanation |
| `POST` | `/api/v1/feedback` | Submit analyst feedback |
| `GET` | `/api/v1/analytics/summary` | Dashboard metrics |
| `WS` | `/ws/transactions` | Real-time transaction stream |
| `WS` | `/ws/alerts` | Real-time fraud alerts |

## Team

| | Role | Focus |
|---|------|-------|
| **Nisarg** | Backend & ML Engineer | FastAPI, ML pipeline, feature engineering, infrastructure |
| **Deep** | Frontend & UX Engineer | React dashboard, data visualization, user experience |

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**FRAUD`LENS`** — See fraud before it strikes.

</div>
