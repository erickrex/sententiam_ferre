# Sententiam Ferre

A mobile-first collaborative decision-making platform with swipe-style voting and AI-powered character generation. The name comes from Latin, meaning "to cast a vote" or "to pass judgment."

## Overview

Sententiam Ferre helps groups make collective decisions through an intuitive swipe-based voting interface. Built for the BRIA FIBO Hackathon, it showcases deterministic AI image generation for 2D game character creation, where teams can collaboratively design and vote on characters using structured JSON control.

### How It Works

1. **Create a Group** - Invite members or let them request to join
2. **Start a Decision** - Create a character design session with locked parameters
3. **Generate Characters** - Use the step-by-step wizard to create characters via BRIA FIBO
4. **Vote & Create** - Members swipe to vote, and can create new variations mid-voting
5. **Discover Favourites** - Characters meeting approval rules become team favourites

### System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SENTENTIAM FERRE                               │
│                    Collaborative AI Character Generation                     │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────┐     ┌──────────┐     ┌──────────────┐     ┌───────────────────┐
│   User   │────▶│  Group   │────▶│   Decision   │────▶│   Character Item  │
└──────────┘     └──────────┘     └──────────────┘     └───────────────────┘
     │                │                  │                       │
     │                │                  │                       │
     ▼                ▼                  ▼                       ▼
┌──────────┐     ┌──────────┐     ┌──────────────┐     ┌───────────────────┐
│Membership│     │  Locked  │     │  BRIA FIBO   │     │      Votes        │
│ (roles)  │     │  Params  │     │  Generation  │     │  (like/pass)      │
└──────────┘     └──────────┘     └──────────────┘     └───────────────────┘
```

### Voting & Creation Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SWIPE VOTING WITH CREATION                          │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │  Character Card │
                              │    (Current)    │
                              └────────┬────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              │                        │                        │
              ▼                        ▼                        ▼
       ┌──────────┐            ┌──────────────┐          ┌──────────┐
       │  SWIPE   │            │    CREATE    │          │  SWIPE   │
       │  LEFT    │            │   VARIATION  │          │  RIGHT   │
       │  (Nope)  │            │     (✨)     │          │  (Like)  │
       └────┬─────┘            └──────┬───────┘          └────┬─────┘
            │                         │                       │
            ▼                         ▼                       ▼
       ┌──────────┐            ┌──────────────┐          ┌──────────┐
       │  Vote:   │            │   Character  │          │  Vote:   │
       │  Pass    │            │    Wizard    │          │  Like    │
       └────┬─────┘            │  (7 Steps)   │          └────┬─────┘
            │                  └──────┬───────┘               │
            │                         │                       │
            │                         ▼                       │
            │                  ┌──────────────┐               │
            │                  │  BRIA FIBO   │               │
            │                  │  Generation  │               │
            │                  └──────┬───────┘               │
            │                         │                       │
            │                         ▼                       │
            │                  ┌──────────────┐               │
            │                  │  New Item    │               │
            │           ┌─────▶│  Added to    │◀─────┐        │
            │           │      │  Voting Deck │      │        │
            │           │      └──────┬───────┘      │        │
            │           │             │              │        │
            │           │             ▼              │        │
            │           │      ┌──────────────┐      │        │
            │           │      │  User Votes  │      │        │
            │           │      │  on New Item │      │        │
            │           │      └──────────────┘      │        │
            │           │                            │        │
            ▼           │                            │        ▼
       ┌────────────────┴────────────────────────────┴────────────┐
       │                      NEXT CARD                           │
       │              (Continue voting loop)                      │
       └──────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
                         ┌──────────────┐
                         │   All Cards  │
                         │    Voted?    │
                         └──────┬───────┘
                                │
                    ┌───────────┴───────────┐
                    │ Yes                   │ No
                    ▼                       ▼
           ┌──────────────┐         ┌──────────────┐
           │   Check      │         │   Show Next  │
           │   Approval   │         │   Character  │
           │   Rules      │         └──────────────┘
           └──────┬───────┘
                  │
                  ▼
           ┌──────────────┐
           │  Favourites  │
           │  (Approved)  │
           └──────────────┘
```

### Character Wizard Flow (FIBO JSON Control)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CHARACTER WIZARD - FIBO STRUCTURED CONTROL               │
└─────────────────────────────────────────────────────────────────────────────┘

Step 1          Step 2          Step 3          Step 4
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│Describe │────▶│Art Style│────▶│ Camera  │────▶│  Pose   │
│Character│     │ cartoon │     │  front  │     │  idle   │
│  "..."  │     │ pixel   │     │  side   │     │ action  │
└─────────┘     │ vector  │     │  3/4    │     │ jumping │
                └─────────┘     └─────────┘     └─────────┘
                                                     │
     ┌───────────────────────────────────────────────┘
     │
     ▼
Step 5          Step 6          Step 7          Review
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────────┐
│Express- │────▶│ Colors  │────▶│  Back-  │────▶│ FIBO JSON   │
│  ion    │     │ vibrant │     │ ground  │     │ Preview     │
│ neutral │     │ pastel  │     │ transp. │     │ ┌─────────┐ │
│ happy   │     │ muted   │     │ solid   │     │ │{        │ │
└─────────┘     └─────────┘     └─────────┘     │ │ prompt, │ │
                                                │ │ params  │ │
                                                │ │}        │ │
                                                │ └─────────┘ │
                                                └──────┬──────┘
                                                       │
                                                       ▼
                                                ┌─────────────┐
                                                │  Generate   │
                                                │  via BRIA   │
                                                │    FIBO     │
                                                └─────────────┘
```

### Key Concepts

| Concept | Description |
|---------|-------------|
| **Group** | A collection of users who make decisions together |
| **Decision** | A character design session with approval rules |
| **Character Item** | A 2D game character generated via BRIA FIBO |
| **Vote** | A member's preference (like/pass) |
| **Favourite** | A character that met the decision's approval threshold |
| **Locked Params** | Parameters fixed by admin for visual consistency |
| **FIBO JSON** | Structured parameters for deterministic AI generation |

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
- BRIA API Token (for image generation)

### Installation

```bash
# Backend
uv sync
cp .env.example .env  # Edit with your DB credentials and BRIA_API_TOKEN
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
- AI Generation: BRIA FIBO V2 API

## Project Structure

```
├── core/                 # Django app (models, views, serializers)
│   └── services/         # BRIA client, generation processor, prompt builder
├── frontend/src/         # React app
│   ├── components/       # CharacterWizard, SwipeCardStack, etc.
│   ├── machines/         # Wizard state machine & FIBO mappings
│   └── pages/            # VotingPage, ItemManagementPage, etc.
├── sententiam_ferre/     # Django settings
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

- **AI Character Generation** - BRIA FIBO integration with structured JSON control
- **Step-by-Step Wizard** - 7-step character creation with real-time FIBO preview
- **Create While Voting** - Generate new characters mid-voting session
- **Group Collaboration** - Teams vote together on character designs
- **Locked Parameters** - Admins can lock styles for visual consistency
- **Swipe Voting** - Intuitive mobile-first voting interface
- **Automatic Favourites** - Characters meeting approval rules are highlighted
