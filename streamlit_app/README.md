# takeAwayBill - Streamlit Frontend

A simple, lightweight frontend for takeAwayBill built with Streamlit.

## Quick Start

### Prerequisites
- Python 3.8+
- Backend running on `http://localhost:5005`

### Installation & Running

```bash
# Navigate to the streamlit app directory
cd streamlit_app

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

The app will be available at `http://localhost:8501`

### Configuration

Edit `.streamlit/secrets.toml` to change:
- `backend_url` - Backend API endpoint (default: `http://localhost:5005`)
- `testing_mode` - Enable testing features (default: false)

### Features

- **Login/Logout** - Simple authentication
- **Historical Orders** - View and filter past orders by date
- **Live Orders** - Real-time order monitoring with status tracking
- **Analytics** - Quick metrics (total orders, paid online, revenue)
- **Export** - Download order data as CSV

### Pages

1. **Orders** - Historical order management with sorting and filtering
2. **Live Orders** - Real-time active orders grouped by status
3. **Settings** - Token management and logout

## Deployment

For production deployment:

1. Set environment variables in `.streamlit/secrets.toml`:
   ```toml
   backend_url = "https://your-api-endpoint.com"
   ```

2. Deploy to Streamlit Cloud:
   ```bash
   streamlit deploy
   ```

   Or use Docker:
   ```bash
   docker build -t takeawaybill-frontend .
   docker run -p 8501:8501 takeawaybill-frontend
   ```

## Architecture

- **app.py** - Main Streamlit application with page components
- **AuthManager** - Handles JWT token management and API authentication
- **Session State** - Stores authentication tokens and fetched data in Streamlit session

## Token Management

The app handles JWT tokens automatically:
- Stores tokens in session state (browser memory)
- Checks token expiration before each API call
- Auto-refreshes expired tokens
- Redirects to login if refresh fails

## Error Handling

- API errors display user-friendly messages
- 401 Unauthorized responses trigger re-login
- Network errors are caught and displayed
- Invalid credentials prevent login

## Notes

- All requests include the `accessToken` header
- Tokens are not persisted (cleared on page refresh)
- Compatible with existing Flask backend
