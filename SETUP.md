# 📋 Detailed Setup Guide

## Prerequisites

- **Miniconda** or **Anaconda** ([download](https://docs.conda.io/projects/miniconda/en/latest/))
- **Python 3.11+** (automatically installed with conda)
- **Git** (optional, only if cloning from repo)
- **Takeaway.com Account** with API access (to get refresh token)

## Step 1: Clone Repository (If Using Git)

```bash
git clone https://github.com/yourusername/takeawaybill.git
cd takeawaybill
```

Or download and extract the ZIP file.

## Step 2: Create Conda Environment

```bash
conda env create -f environment.yaml
```

This creates a Python 3.11 environment named `takeawaybill` with all dependencies:
- Streamlit 1.31.1
- pandas 2.1.3
- numpy
- requests 2.31.0
- PyJWT 2.8.0
- cloudscraper 1.2.71
- python-dotenv 1.0.0

**Verify installation:**

```bash
conda activate takeawaybill
conda list  # Should show all packages above
```

## Step 3: Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```
TAKEAWAY_REFRESH_TOKEN=your_refresh_token_here
```

**How to get the refresh token:**

1. Go to [Takeaway.com Partner Hub](https://partner-hub.justeattakeaway.com)
2. Navigate to **Settings → API Access**
3. Generate OAuth2 credentials (if not already done)
4. Copy the **Refresh Token**
5. Paste into `.env` file

**Note:** Do NOT commit `.env` to git. It's already in `.gitignore`.

## Step 4: Run the Application

**Activate environment:**

```bash
conda activate takeawaybill
```

**Start Streamlit:**

```bash
cd streamlit_app
streamlit run app.py
```

The app will start on **http://localhost:8501**

**Login:**
- Use any username/password (demo mode)
- App validates token against Takeaway.com API

---

## Architecture Overview

### File Structure

```
streamlit_app/
├── app.py                    # Streamlit UI (login, orders, live orders, settings)
├── backend.py                # Pure Python API module (no Streamlit dependencies)
└── .streamlit/
    └── config.toml           # Streamlit configuration
```

### Component Breakdown

**`app.py` (Streamlit Frontend)**
- `AuthManager` class: Session token management
- `login_page()`: User authentication
- `orders_page()`: Historical orders with filtering
- `live_orders_page()`: Real-time order monitoring
- `settings_page()`: Token refresh and logout
- `main()`: App navigation and state management

**`backend.py` (Pure Python Backend)**
- `refresh_tokens()`: OAuth2 token refresh (returns access token)
- `fetch_orders_by_date()`: Parallel order fetching from Takeaway.com API
- `fetch_live_orders()`: Real-time order monitoring with retry logic
- `ThreadWithReturnValue`: Helper for parallel API calls

### Data Flow

```
User Login (app.py)
    ↓
AuthManager stores user session tokens
    ↓
App startup → AuthManager.ensure_api_token()
    ↓
If needed → refresh_tokens() via OAuth2
    ↓
API Request (from app.py)
    ↓
backend.py calls Takeaway.com API with cached token
    ↓
Return data to Streamlit
    ↓
Display in UI (DataFrames, metrics, containers)
```

---

## Managing Python Packages

### Add a New Package

```bash
# Install with conda (preferred)
conda install package_name

# Or with pip (for packages not in conda-forge)
pip install package_name

# Update environment.yaml
conda env export > environment.yaml
```

### Update All Packages

```bash
conda update --all
```

### View Installed Packages

```bash
conda list
```

---

## Useful Conda Commands

```bash
# List all environments
conda env list

# Activate environment
conda activate takeawaybill

# Deactivate environment
conda deactivate

# Remove environment (if needed)
conda env remove --name takeawaybill

# Recreate environment (useful if environment.yaml changes)
conda env create -f environment.yaml --force
```

---

## Troubleshooting

| Issue                            | Solution                                                                                                            |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `conda: command not found`       | Ensure conda is installed and PATH is updated. Run `conda init` and restart terminal.                               |
| `No module named 'streamlit'`    | Activate environment: `conda activate takeawaybill`                                                                 |
| Port 8501 already in use         | `streamlit run app.py --server.port 8502`                                                                           |
| Token refresh fails              | Verify `TAKEAWAY_REFRESH_TOKEN` in `.env` is valid                                                                  |
| Import errors (requests, pandas) | Delete and recreate environment: `conda env remove --name takeawaybill` then `conda env create -f environment.yaml` |
| File not found: `.env`           | Run `cp .env.example .env`                                                                                          |

---

## Development Tips

### Hot Reloading

- **Streamlit auto-reloads** when you save `app.py` or `backend.py`
- Just keep the terminal running and save your changes

### Debugging

Add print statements or use Python debugger:

```python
# In app.py or backend.py
import pdb
pdb.set_trace()  # Execution pauses here
```

### Testing Backend Functions

Test `backend.py` functions directly in Python:

```bash
conda activate takeawaybill
python -c "from streamlit_app.backend import fetch_orders_by_date; orders = fetch_orders_by_date('2024-01-15'); print(orders)"
```

---

## Next Steps

- Read [QUICK_START.md](./QUICK_START.md) for a quick overview
- Check [ENV_SETUP.md](./ENV_SETUP.md) for detailed OAuth2 workflow
- See [README.md](./README.md) for features and architecture
- Explore `streamlit_app/app.py` and `streamlit_app/backend.py` to understand the code

---

## Support

For issues:
1. Check this guide's troubleshooting section
2. Verify `.env` file has correct `TAKEAWAY_REFRESH_TOKEN`
3. Ensure conda environment is activated
4. Check Takeaway.com API credentials in Partner Hub
