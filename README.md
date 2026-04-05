# Sourdough Adviser

A sourdough bake logger and AI adviser. Log ingredients, folds, proofs, and oven stages as you bake — then get specific, actionable feedback powered by Claude.

## Stack

- **Backend** — FastAPI + Python
- **Database** — Supabase (Postgres)
- **AI** — Anthropic Claude API
- **Hosting** — Railway
- **Frontend** *(planned)* — React via Lovable
- **Mobile** *(planned)* — Expo + React Native

## Project Structure

```
sourdough-adviser/
├── app/
│   ├── core/config.py          # Environment variables
│   ├── models/bake.py          # Pydantic request/response models
│   ├── routes/
│   │   ├── bakes.py            # Bake CRUD and logging endpoints
│   │   └── adviser.py          # AI advice endpoint
│   ├── services/
│   │   ├── bake_ops.py         # Bake state mutation
│   │   ├── bake_storage.py     # Persistence (local JSON or Supabase)
│   │   └── bake_adviser.py     # Anthropic API calls
│   └── utils/
│       └── bake_utils.py       # Dataclasses and pure calculations
├── tests/
├── .env                        # Local secrets (never committed)
├── requirements.txt
├── railway.toml
└── README.md
```

## Local Setup

```bash
# Clone and create virtual environment
git clone https://github.com/constshiac/sourdough-adviser
cd sourdough-adviser
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Add your ANTHROPIC_API_KEY — Supabase keys optional for local dev

# Run the server
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` to explore and test all endpoints interactively.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/bakes` | Start a new bake |
| `GET` | `/bakes` | List all bakes |
| `GET` | `/bakes/{id}` | Get a single bake |
| `DELETE` | `/bakes/{id}` | Delete a bake |
| `POST` | `/bakes/{id}/ingredients` | Add ingredients |
| `POST` | `/bakes/{id}/folds` | Log a fold |
| `POST` | `/bakes/{id}/stages` | Add pre-shape or final shape |
| `POST` | `/bakes/{id}/proofs` | Add a proof |
| `POST` | `/bakes/{id}/proofs/close` | Close current proof |
| `POST` | `/bakes/{id}/bake-stage` | Log oven stage |
| `POST` | `/bakes/{id}/outcome` | Record outcome scores |
| `POST` | `/adviser/{id}` | Get AI advice for a bake |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key |
| `SUPABASE_URL` | Production only | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Production only | Supabase service role key |

Without Supabase credentials, the app falls back to a local `bake_history.json` file.

## Roadmap

- **Phase 1** ✅ — Core Python logic, local JSON storage, AI adviser
- **Phase 2** 🔄 — FastAPI backend, Supabase database, Railway deployment
- **Phase 3** ⬜ — iPhone app via Expo + React Native
- **Phase 4** ⬜ — Pattern detection, fermentation timing, photo crumb analysis