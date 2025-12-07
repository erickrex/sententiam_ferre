# Sententiam Ferre

A mobile-first collaborative decision-making platform with swipe-style voting.

## Quick Start

```bash
./start-dev.sh
```

Or manually:

```bash
# Terminal 1 - Backend
uv run python manage.py runserver

# Terminal 2 - Frontend
cd frontend && npm run dev
```

Access at:
- Frontend: http://localhost:5173
- API: http://localhost:8000/api/v1
- Admin: http://localhost:8000/admin

## Setup

### Prerequisites
- Python 3.12+
- PostgreSQL 14+
- UV (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Node.js 18+

### Installation

```bash
# Backend
uv sync
cp .env.example .env  # Edit with your DB credentials
psql -U postgres -c "CREATE DATABASE sententiam_ferre;"
uv run python manage.py migrate
uv run python manage.py createsuperuser

# Frontend
cd frontend
npm install
cp .env.example .env
```

## Tech Stack

- Backend: Django 5.2, DRF, PostgreSQL
- Frontend: React 18, Vite, React Router

## Project Structure

```
├── core/                 # Django app (models, views, serializers)
├── frontend/src/         # React app (components, pages, services)
├── sententiam_ferre/     # Django settings
├── schema.sql            # DB schema reference
└── start-dev.sh          # Dev startup script
```

## Testing

```bash
# Backend
uv run python manage.py test

# Frontend
cd frontend && npm test
```

## Key Features

- Group-based collaborative decisions
- Swipe voting interface
- Configurable approval rules (unanimous/threshold)
- Automatic favourite detection via DB triggers
- Real-time chat per decision
- Taxonomy/tagging system
- Mobile-first responsive design
