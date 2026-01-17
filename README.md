# Feature Flag Service

A feature flag management system for controlling feature rollouts with percentage-based targeting and real-time updates.

**Live Demo:** https://feature-flag-service-hh6d.vercel.app

---

## What It Does

This service lets you control which features are enabled for different users without redeploying code. You can:

- Turn features on/off instantly
- Roll out features to a percentage of users (e.g., 25% see the new checkout)
- Target specific users while others see the old version
- Track all changes with audit logs

## Tech Stack

**Backend:** FastAPI, PostgreSQL, SQLAlchemy  
**Frontend:** React  
**Deployment:** Vercel (API), Supabase (Database)  
**Testing:** pytest (90%+ coverage)

## Quick Start

### Run Locally

```bash
# Clone the repo
git clone https://github.com/S-entinel/feature-flag-service.git
cd feature-flag-service

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env

# Run the API
uvicorn app.main:app --reload

# In another terminal, run the dashboard
cd dashboard
npm install
npm start
```

Visit:
- API: http://localhost:8000
- Dashboard: http://localhost:3000
- API Docs: http://localhost:8000/docs

### Using the Python SDK

```python
from sdk import FeatureFlagClient

client = FeatureFlagClient("http://localhost:8000")

# Check if a feature is enabled
if client.is_enabled("new-checkout", user_id="user_123"):
    show_new_checkout()
else:
    show_old_checkout()
```

## Key Features

### Percentage Rollouts

Roll out features gradually to reduce risk:

```python
# Enable for 25% of users
{
  "key": "new-feature",
  "enabled": true,
  "rollout_percentage": 25.0
}
```

Users get consistent experiences - the same user always sees the same version.

### API Key Authentication

Write operations (create/update/delete) require authentication. Read operations (flag evaluation) are public for performance.

### Audit Logging

Every change is tracked:
- Who made the change
- What changed
- When it happened

## Architecture

```
Client Apps
     ↓
Python SDK (with local cache)
     ↓
FastAPI Backend
     ↓
PostgreSQL Database
```

The SDK caches flag data locally to minimize API calls and reduce latency.

## API Examples

```bash
# List all flags
curl https://feature-flag-service-eta.vercel.app/flags/

# Evaluate a flag
curl https://feature-flag-service-eta.vercel.app/flags/dark-mode/evaluate?user_id=user123

# Create a flag (requires API key)
curl -X POST https://feature-flag-service-eta.vercel.app/flags/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"key":"new-feature","name":"New Feature","enabled":true}'
```

## Testing

```bash
# Run all tests
pytest

# With coverage report
pytest --cov=app --cov=sdk --cov-report=html
```

Tests include:
- Unit tests for core logic
- Integration tests for database operations
- SDK client tests
- API endpoint tests

## Deployment

The project is deployed using:
- **Vercel** for the FastAPI backend (serverless)
- **Supabase** for PostgreSQL database
- Free tier for both services

Note: The database may pause after inactivity on the free tier. First request can take 3-5 seconds to wake services.

## Project Structure

```
├── app/                 # FastAPI backend
│   ├── api/            # API routes
│   ├── models/         # Database models
│   ├── services/       # Business logic
│   └── main.py         # Application entry
├── dashboard/          # React admin UI
│   └── src/
│       └── components/ # React components
├── sdk/                # Python SDK
│   ├── client.py       # Main client
│   └── cache.py        # Local caching
└── tests/              # Test suite
```

## Why I Built This

I wanted to learn how feature flag systems work and practice building production-grade APIs. This project taught me:

- Building RESTful APIs with FastAPI
- Database design and migrations
- Deploying serverless applications
- Writing a client SDK
- Testing strategies for APIs

## License

MIT