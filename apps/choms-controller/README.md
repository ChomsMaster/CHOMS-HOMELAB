# CHOMS Controller

Central API for CHOMS Platform.

## Current status

Version: 0.1.0
Status: Development / Node-02

## Features

- Health endpoint
- Node heartbeat endpoint
- Node inventory endpoint
- PostgreSQL persistence
- Environment-based configuration

## Endpoints

GET  /health
GET  /api/v1/nodes/
POST /api/v1/nodes/heartbeat

## Local development

cd apps/choms-controller
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8090

## Environment

APP_NAME=CHOMS Controller
APP_VERSION=0.1.0
DATABASE_URL=postgresql+psycopg://user:password@127.0.0.1:5432/choms_platform
