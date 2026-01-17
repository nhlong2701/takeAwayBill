# takeAwayBill - Streamlit Application

A lightweight Streamlit application for restaurant order management using Takeaway.com's API. Provides real-time order monitoring, historical order viewing, and automatic token management.

## Quick Start

### Prerequisites
- Python 3.11 (via Conda environment)
- Takeaway.com refresh token

### Installation & Running

```bash
# From project root
conda env create -f environment.yaml
conda activate takeawaybill
cp .env.example .env
# Edit .env with TAKEAWAY_REFRESH_TOKEN

# Run the app
streamlit run main.py
```

The app will be available at `http://localhost:8501`

### Configuration

**Environment Variables (.env):**
```bash
TAKEAWAY_REFRESH_TOKEN=your_refresh_token_here
```

**Timezone (optional):**
Edit line 6 in `app.py`:
```python
os.environ['TZ'] = 'Europe/Berlin'  # Change as needed
```

### Features

- **Login/Logout** - Simple authentication (demo mode)
- **Historical Orders** - View and filter past orders by date with sorting
- **Live Orders** - Real-time order monitoring with status tracking
- **Analytics** - Quick metrics (total orders, paid online, revenue)
- **Export** - Download order data as CSV
- **Token Management** - Automatic OAuth2 refresh

### Pages

1. **Orders** - Historical order management with date selection, sorting, and filtering
2. **Live Orders** - Real-time active orders with auto-refresh capability
3. **Settings** - API token refresh and user logout

## Architecture

### Components

**`app.py` (Main Application)**
- `AuthManager` class: Manages both user session tokens and API access tokens
- Page functions: `login_page()`, `orders_page()`, `live_orders_page()`, `settings_page()`
- Token caching: API tokens stored in Streamlit session state to persist across reruns
- Automatic token refresh: Checks expiration and refreshes on app startup

**`backend.py` (API Module)**
- Pure Python functions for Takeaway.com API integration
- No Streamlit dependencies - fully testable independently
- Parallel order fetching using threading
- Cloudflare bypass with `cloudscraper`

### Token Management

- **Refresh Token**: Stored in `.env` file (never committed)
- **Access Token**: Automatically acquired on app startup, cached in session state
- **Expiration Check**: JWT decoding with 5-minute buffer for proactive refresh
- **Minimal API Calls**: Token refreshed only when expired or on first startup

## Deployment

For production deployment:

1. Set environment variable `TAKEAWAY_REFRESH_TOKEN`
2. Deploy to Streamlit Cloud or your preferred hosting
3. The app will automatically handle token refresh

## Development

**Hot Reload:** Streamlit auto-reloads on file changes.

**Testing Backend:** Call functions directly:
```python
from backend import fetch_orders_by_date, refresh_tokens
token = refresh_tokens()
orders = fetch_orders_by_date(token, '2024-01-15')
```

**Debugging:** Add `print()` statements or use Python debugger.

## Deployment

For production deployment:

1. Set environment variable `TAKEAWAY_REFRESH_TOKEN`
2. Deploy to Streamlit Cloud or your preferred hosting
3. The app will automatically handle token refresh

## Architecture

- **app.py** - Main Streamlit application with page components and token management
- **backend.py** - Pure Python API module (no Streamlit dependencies)
- **AuthManager** - Handles both user authentication and API token caching
- **Session State** - Stores user tokens, API tokens, and fetched data

## Token Management

The app handles OAuth2 tokens automatically:
- Refresh token stored securely in environment variables
- Access tokens cached in session state to persist across page reruns
- JWT expiration checked with 5-minute buffer for proactive refresh
- Minimal API calls - refresh only on startup or expiration
- Automatic token rotation when Takeaway.com provides new refresh tokens

## Error Handling

- API errors display user-friendly messages
- Token expiration triggers automatic refresh
- Network errors are caught and displayed
- Invalid refresh tokens prevent app startup

## Notes

- All API requests use Bearer token authentication
- Tokens cached in session state (cleared on browser refresh)
- Pure Python backend - no external server dependencies
