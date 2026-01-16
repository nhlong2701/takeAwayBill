# AI Coding Agent Instructions for takeAwayBill

## Project Overview

**takeAwayBill** is a lightweight Streamlit application for managing restaurant orders from Takeaway.com. It provides:
- Real-time order monitoring (live orders)
- Historical order viewing with filtering/sorting
- Automatic OAuth2 token management
- CSV export for order data

**Tech Stack:**
- **Frontend:** Streamlit 1.31.1 (Python-based UI)
- **Backend:** Pure Python module (no Flask, no server)
- **Token Management:** OAuth2 with Takeaway.com API
- **External API:** Takeaway.com Partner Hub & Restaurant Portal
- **Environment:** Conda Python 3.11
- **Deployment:** Local development (conda) or Streamlit Cloud

---

## Architecture Overview

### Modular Design

The project uses **clean separation of concerns**:

- **`streamlit_app/app.py`** (≈ 650 lines)
  - Streamlit UI components only
  - Session state management
  - Page navigation (Login, Orders, Live Orders, Settings)
  - Imports backend functions: `from backend import (...)`

- **`streamlit_app/backend.py`** (≈ 350 lines)
  - Pure Python module (zero Streamlit dependencies)
  - API calls to Takeaway.com
  - OAuth2 token management
  - Order aggregation and filtering
  - Fully testable without Streamlit

### Data Flow

```
User Interaction (app.py)
         ↓
    AuthManager (session state)
         ↓
   backend.py API calls
         ↓
Takeaway.com OAuth2 & API
         ↓
   Return JSON data
         ↓
   Streamlit UI display
```

### Key Modules

**`streamlit_app/app.py` - Frontend**

```python
class AuthManager:
    - get_tokens()           # Retrieve from session state
    - save_tokens()          # Store in session state
    - is_token_expired()     # Check JWT expiration
    - login()                # Validate user
    - logout()               # Clear tokens

# Pages
def login_page()             # Authentication UI
def orders_page()            # Historical orders + filtering
def live_orders_page()       # Real-time orders with auto-refresh
def settings_page()          # Token management & logout
def main()                   # Navigation & app entry point
```

**`streamlit_app/backend.py` - Backend**

```python
# Global state
TAKEAWAY_REFRESH_TOKEN = os.getenv("TAKEAWAY_REFRESH_TOKEN")
TAKEAWAY_ACCESS_TOKEN = None

# Token management
def refresh_tokens() -> bool
    # Exchanges refresh token for access token via OAuth2

def get_access_token() -> str
    # Returns current access token, refreshing if needed

# Order fetching
def fetch_orders_by_date(date: str, sortColumn: str, sortDirection: str) -> List[dict]
    # Parallel API calls to Takeaway.com Restaurant Portal
    # Returns historical orders for specified date

def fetch_live_orders() -> List[dict]
    # Calls Takeaway.com Live Orders API with retry logic
    # Returns currently active orders

# Utility
class ThreadWithReturnValue(Thread)
    # Helper for parallel order fetching
```

---

## Development Workflows

### Local Development (Quick Start)

```bash
# First time only
conda env create -f environment.yaml
cp .env.example .env
# Edit .env with TAKEAWAY_REFRESH_TOKEN

# Every session
conda activate takeawaybill
cd streamlit_app && streamlit run app.py
```

**Access:** http://localhost:8501

### Manual Setup (Alternative)

```bash
# Create environment
conda env create -f environment.yaml
conda activate takeawaybill

# Configure
cp .env.example .env
# Edit .env file

# Run
cd streamlit_app
streamlit run app.py
```

### Development Tips

**Hot Reload:** Streamlit auto-reloads when files are saved. Just keep terminal running.

**Debug Backend:** Test functions directly in Python:
```bash
python -c "from backend import fetch_orders_by_date; orders = fetch_orders_by_date('2024-01-15'); print(orders)"
```

**Add Debugging:** Use `print()` statements or Python debugger:
```python
import pdb; pdb.set_trace()  # Pauses execution
```

---

## Project-Specific Conventions

### Token Management (Critical)

**OAuth2 Flow:**
1. User provides only `TAKEAWAY_REFRESH_TOKEN` in `.env`
2. `get_access_token()` checks if current access token is expired
3. If expired, calls `/partner-hub.justeattakeaway.com` to refresh
4. Returns fresh access token
5. API calls use this token in request headers

**Frontend:** `app.py` stores tokens in `st.session_state` (temporary, per session)
**Backend:** `backend.py` stores tokens in module-level variables (reusable across calls)

### API Response Format

**Historical Orders** (`fetch_orders_by_date()`):
```json
[
  {
    "orderCode": "12345",
    "createdAt": "2024-01-15T14:30:00Z",
    "postcode": "10115",
    "price": 24.99,
    "paidOnline": 1
  }
]
```

**Live Orders** (`fetch_live_orders()`):
```json
[
  {
    "orderCode": "67890",
    "status": "confirmed",
    "customer": {
      "fullName": "John Doe",
      "street": "Main St",
      "street_number": "123"
    },
    "products": [
      {
        "quantity": 2,
        "name": "Pizza Margherita",
        "totalAmount": 18.99
      }
    ],
    "paymentType": "cash",
    "customerTotal": 24.99,
    "placedDate": "2024-01-15T14:30:00Z",
    "requestedTime": "15:00"
  }
]
```

### Error Handling

- **Expired token:** `get_access_token()` automatically refreshes
- **API failures:** `fetch_live_orders()` retries with exponential backoff
- **Invalid credentials:** `login()` in `app.py` returns False (demo mode accepts any input)

### Timezone & Localization

- **Backend timezone:** `os.environ['TZ'] = 'Europe/Berlin'` (set in `app.py`)
- **Frontend:** Streamlit default locale
- **API timezone:** Takeaway.com returns ISO 8601 timestamps (UTC)

### Threading for Parallel Calls

`backend.py` uses `ThreadWithReturnValue` helper to parallelize order fetching:
```python
# Fetch orders in parallel from multiple venues/franchises
threads = [ThreadWithReturnValue(...) for venue in venues]
[t.start() for t in threads]
results = [t.join() for t in threads]
```

---

## File Structure

### Essential Files

| Purpose | File | Status |
|---------|------|--------|
| Streamlit UI | `streamlit_app/app.py` | Active |
| Backend APIs | `streamlit_app/backend.py` | Active |
| Environment | `environment.yaml` | Active |
| Credentials template | `.env.example` | Active |
| Config | `Makefile` | Optional (manual setup also works) |

### Documentation Files

| Purpose | File | Notes |
|---------|------|-------|
| Quick start | `QUICK_START.md` | Manual setup (3 steps) |
| Detailed setup | `SETUP.md` | Architecture & troubleshooting |
| OAuth2 workflow | `ENV_SETUP.md` | Token management details |
| Features | `README.md` | Overview & project structure |
| AI instructions | `.github/copilot-instructions.md` | This file |

### Files NOT in Repo

- `.env` – Credentials (copy from `.env.example`, never commit)
- `streamlit_app/__pycache__/` – Python cache
- `.streamlit/secrets.toml` – Local Streamlit secrets (not used in this app)

---

## Common Development Tasks

### Adding a New Order Filter

**Location:** `streamlit_app/app.py` → `orders_page()`

Example: Add filter by minimum price
```python
with col1:
    min_price = st.number_input("Min Price", min_value=0.0)

# Filter orders
filtered_orders = [o for o in orders if o['price'] >= min_price]
df = pd.DataFrame(filtered_orders)
```

### Adding a New API Endpoint

**Location:** `streamlit_app/backend.py`

Example: Fetch orders by postcode
```python
def fetch_orders_by_postcode(postcode: str) -> List[dict]:
    """Fetch orders for a specific postcode."""
    access_token = get_access_token()
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.post(
        'https://api.takeaway.com/endpoint',
        json={'postcode': postcode},
        headers=headers
    )
    return response.json()

# Then in app.py, call:
orders = fetch_orders_by_postcode('10115')
```

### Modifying Token Refresh Logic

**Location:** `streamlit_app/backend.py` → `refresh_tokens()` and `get_access_token()`

Current flow:
1. Check if access token expired (JWT decode)
2. If expired, POST to Takeaway.com token endpoint
3. Store new access token in module variable
4. Return token

**Do NOT modify:**
- `.env` reading (handled by `python-dotenv`)
- Response format (Takeaway.com API response is fixed)

### Adding New Streamlit Pages

**Location:** `streamlit_app/app.py` → Add function + radio option in `main()`

Example: Add analytics page
```python
def analytics_page():
    st.header("📊 Analytics")
    orders = fetch_orders_by_date(...)
    st.bar_chart({...})

# In main():
page = st.sidebar.radio(
    "Navigation",
    ["📋 Orders", "🔴 Live Orders", "📊 Analytics", "⚙️ Settings"],  # ← Add here
)

if page == "📊 Analytics":
    analytics_page()  # ← Add here
```

---

## External API Integration

### Takeaway.com OAuth2 (Partner Hub)

**Endpoint:** `https://partner-hub.justeattakeaway.com/login/v1/refresh-tokens`

**Request:**
```bash
POST /login/v1/refresh-tokens
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token&refresh_token=YOUR_TOKEN&client_id=YOUR_ID&client_secret=YOUR_SECRET
```

**Response:**
```json
{
  "access_token": "...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

**Implementation:** `backend.py` → `refresh_tokens()`

### Takeaway.com Restaurant Portal API

**Endpoint:** `https://api.takeaway.com/v3/restaurants/{restaurantId}/orders`

**Auth:** Bearer token in Authorization header

**Query params:**
- `from` – Start date (ISO 8601)
- `to` – End date (ISO 8601)
- `page` – Pagination

**Response:** JSON array of orders

**Implementation:** `backend.py` → `fetch_orders_by_date()`

### Takeaway.com Live Orders API

**Endpoint:** `https://live-orders-api.takeaway.com/api/orders`

**Auth:** Bearer token + Custom headers

**Response:** JSON array of active orders with detailed structure

**Implementation:** `backend.py` → `fetch_live_orders()`

### Using `cloudscraper` Library

Some Takeaway.com endpoints are protected by Cloudflare. Use `cloudscraper`:

```python
import cloudscraper
scraper = cloudscraper.create_scraper()
response = scraper.get(url, headers=headers)  # Bypasses Cloudflare
```

---

## Testing & Validation

### Test Backend Functions

```bash
conda activate takeawaybill
python -c "
from streamlit_app.backend import get_access_token
token = get_access_token()
print(f'Token: {token[:20]}...')
"
```

### Test OAuth2 Refresh

```bash
python -c "
from streamlit_app.backend import refresh_tokens
success = refresh_tokens()
print(f'Refresh: {success}')
"
```

### Test Order Fetching

```bash
python -c "
from streamlit_app.backend import fetch_orders_by_date
orders = fetch_orders_by_date('2024-01-15')
print(f'Orders: {len(orders)}')
"
```

### Validate .env

```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
token = os.getenv('TAKEAWAY_REFRESH_TOKEN')
print(f'Token exists: {bool(token)}')
print(f'Token length: {len(token) if token else 0}')
"
```

---

## Known Dependencies & Libraries

### Core Dependencies

- **Streamlit 1.31.1** – Frontend framework
- **pandas 2.1.3** – Data manipulation (filtering, sorting, CSV export)
- **numpy** – Numerical operations
- **requests 2.31.0** – HTTP client for API calls
- **cloudscraper 1.2.71** – Bypass Cloudflare protection
- **PyJWT 2.8.0** – JWT token decode (expiration check)
- **python-dotenv 1.0.0** – `.env` file loading

### Import Statements in Code

```python
# app.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import jwt
from backend import TAKEAWAY_REFRESH_TOKEN, fetch_orders_by_date, fetch_live_orders, refresh_tokens

# backend.py
import os
import requests
import cloudscraper
import pandas as pd
from threading import Thread
from datetime import datetime, timedelta
from typing import List
import jwt
from dotenv import load_dotenv
```

---

## Deployment Notes

### Local Development (Conda)
- **Default:** `streamlit run app.py`
- **Custom port:** `streamlit run app.py --server.port 8502`

### Streamlit Cloud (if deploying)
1. Push code to GitHub
2. Connect repo to Streamlit Cloud
3. Add secrets in Streamlit Cloud dashboard:
   - `TAKEAWAY_REFRESH_TOKEN`
4. Deploy automatically on git push

### Docker (if desired)
Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN conda env create -f environment.yaml
EXPOSE 8501
CMD ["conda", "run", "-n", "takeawaybill", "streamlit", "run", "streamlit_app/app.py"]
```

---

## Debugging Checklist

When something breaks:

1. **Check `.env` file:**
   - Does it exist?
   - Does `TAKEAWAY_REFRESH_TOKEN` have a value?

2. **Check Conda environment:**
   ```bash
   conda activate takeawaybill
   conda list  # All packages installed?
   ```

3. **Check Takeaway.com API:**
   - Is the refresh token still valid?
   - Can you manually call the token endpoint?

4. **Check imports:**
   ```bash
   python -c "import streamlit; import pandas; from backend import *"
   ```

5. **Check Streamlit:**
   - Is port 8501 free?
   - Try different port: `streamlit run app.py --server.port 8502`

6. **Check logs:**
   - Look at Streamlit console output
   - Add `print()` statements in `backend.py`

---

## Best Practices for AI Agents

### Code Generation

✅ **DO:**
- Keep backend logic in `backend.py` (no Streamlit)
- Use type hints for function parameters
- Add docstrings for all functions
- Handle errors with try/except
- Use list comprehensions for filtering

❌ **DON'T:**
- Mix Streamlit calls in `backend.py`
- Hardcode API URLs (use constants)
- Store sensitive data in code (use `.env`)
- Ignore JWT token expiration
- Make synchronous API calls in loops (use threading)

### Adding Features

1. **Add backend logic first** (`backend.py`)
2. **Then add UI** (`app.py`)
3. **Test backend independently** (Python REPL)
4. **Test end-to-end** (Streamlit UI)

### Code Organization

```python
# Good: Modular
def fetch_orders_by_date(date):
    access_token = get_access_token()  # Reusable
    headers = build_headers(access_token)  # Extracted
    return api_call(url, headers)  # Clean

# Bad: Repetitive
def fetch_orders_by_date(date):
    # Token refresh logic repeated
    # Headers built inline
    # API call not reusable
```

---

## Quick Reference

### Key Files to Edit

| Task | File | Function |
|------|------|----------|
| Add UI page | `app.py` | `def my_page():` + add to `main()` |
| Add API call | `backend.py` | `def fetch_my_data():` |
| Fix token issue | `backend.py` | `refresh_tokens()`, `get_access_token()` |
| Change UI layout | `app.py` | `st.column()`, `st.container()` |
| Add dependency | `environment.yaml` | Add to `pip:` section |

### Environment Variables

Only ONE required variable:
- `TAKEAWAY_REFRESH_TOKEN` – OAuth2 refresh token from Takeaway.com

### Ports

- **Streamlit:** `8501` (configurable)
- **No backend server** (pure Python module)

### Important Classes

- `AuthManager` (app.py) – Session token state
- `ThreadWithReturnValue` (backend.py) – Parallel execution

---

## Support & Resources

- **Streamlit docs:** https://docs.streamlit.io
- **Takeaway.com API:** https://partner-hub.justeattakeaway.com (Partner Hub)
- **PyJWT docs:** https://pyjwt.readthedocs.io
- **Conda docs:** https://docs.conda.io

---

**Last Updated:** January 2025
**Architecture:** Streamlit + Pure Python Backend (No Flask)
**Status:** Production-ready
