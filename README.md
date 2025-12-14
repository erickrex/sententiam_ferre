# Sententiam Ferre

A mobile-first collaborative decision-making platform with swipe-style voting. The name comes from Latin, meaning "to cast a vote" or "to pass judgment."

## Overview

Sententiam Ferre helps groups make collective decisions through an intuitive swipe-based voting interface. Whether you're choosing a restaurant with friends, selecting baby names with your partner, or prioritizing features with your team, the platform streamlines the process of finding consensus.

### How It Works

1. **Create a Group** - Invite members or let them request to join
2. **Start a Decision** - Add items to vote on (manually or from a catalog)
3. **Vote** - Members swipe right (like) or left (pass) on each item
4. **Discover Favourites** - Items meeting approval rules automatically become "favourites"

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SENTENTIAM FERRE                               │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────┐     ┌──────────┐     ┌──────────────┐     ┌───────────────────┐
│   User   │────▶│  Group   │────▶│   Decision   │────▶│   Decision Item   │
└──────────┘     └──────────┘     └──────────────┘     └───────────────────┘
     │                │                  │                       │
     │                │                  │                       │
     ▼                ▼                  ▼                       ▼
┌──────────┐     ┌──────────┐     ┌──────────────┐     ┌───────────────────┐
│Membership│     │  Chat    │     │    Rules     │     │      Votes        │
│ (roles)  │     │(per dec.)│     │ - unanimous  │     │  (like/pass/rate) │
└──────────┘     └──────────┘     │ - threshold  │     └─────────┬─────────┘
                                  └──────────────┘               │
                                                                 │
                                         ┌───────────────────────┘
                                         ▼
                              ┌─────────────────────┐
                              │   DB Trigger        │
                              │ (check approval)    │
                              └──────────┬──────────┘
                                         │
                                         ▼
                              ┌─────────────────────┐
                              │   Favourites        │
                              │ (auto-selected)     │
                              └─────────────────────┘

VOTING FLOW:
┌────────┐    ┌─────────┐    ┌──────────┐    ┌───────────┐    ┌────────────┐
│ Swipe  │───▶│  Vote   │───▶│ Trigger  │───▶│  Check    │───▶│ Favourite? │
│ Right  │    │ Saved   │    │  Fires   │    │  Rules    │    │  (yes/no)  │
└────────┘    └─────────┘    └──────────┘    └───────────┘    └────────────┘

APPROVAL RULES:
• Unanimous: ALL members must like the item
• Threshold: X% of members must like (e.g., 60% approval)
```

### Key Concepts

| Concept | Description |
|---------|-------------|
| **Group** | A collection of users who make decisions together |
| **Decision** | A voting session with items and approval rules |
| **Item** | Something to vote on (can be from catalog or custom) |
| **Vote** | A member's preference (like/pass or 1-5 rating) |
| **Favourite** | An item that met the decision's approval threshold |
| **Catalog** | Reusable item templates with taxonomy tags |

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
