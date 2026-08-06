# takeAwayBill

Order management system for restaurants using Takeaway.com's API. A lightweight Streamlit application that provides real-time order monitoring, historical order viewing with filtering/sorting, and automatic OAuth2 token management.

## 🚀 Quick Start

**First time setup:**
```bash
conda env create -f environment.yaml
cp .env.example .env
# Edit .env with your Takeaway.com refresh token
```

**Run the app:**
```bash
conda activate takeawaybill
streamlit run main.py
```

Access: http://localhost:8501

## 📋 What You Need

- **Anaconda/Miniconda** with Python 3.11
- **Takeaway.com refresh token** in `.env` file
- **.env file** with `TAKEAWAY_REFRESH_TOKEN` only
  - Access token is automatically acquired on startup using the refresh token

## 🛠️ Development

**Activate environment:**
```bash
conda activate takeawaybill
```

**Run Streamlit app:**
```bash
cd streamlit_app && streamlit run app.py
# Or from root directory:
streamlit run main.py
```

## 📁 Project Structure

```
takeAwayBill/
├── main.py                          # Main entry point for Streamlit
├── streamlit_app/
│   ├── app.py                       # Streamlit UI & token management
│   ├── backend.py                   # API calls & data processing
│   └── .streamlit/config.toml       # Streamlit config
├── environment.yaml                 # Conda environment
├── .env.example                     # Environment template
├── Makefile                         # Dev commands
└── .github/copilot-instructions.md  # AI agent guide
```

## 🔑 Key Features

✅ **Login/Logout** — User authentication (demo mode)  
✅ **Historical Orders** — View, filter, sort, and export orders by date  
✅ **Live Orders** — Real-time order dashboard with status tracking  
✅ **Analytics** — Order counts, payment methods, total revenue  
✅ **Token Management** — Automatic JWT refresh for Takeaway.com API  
✅ **CSV Export** — Download order data for external analysis  

## 📚 Documentation

- **[QUICK_START.md](QUICK_START.md)** — Detailed setup options
- **[SETUP.md](SETUP.md)** — Environment & dependency management
- **[ENV_SETUP.md](ENV_SETUP.md)** — OAuth2 workflow & token management
- **[.github/copilot-instructions.md](.github/copilot-instructions.md)** — Architecture & patterns for AI agents
- **[streamlit_app/README.md](streamlit_app/README.md)** — Frontend details

## 🔗 API Integration

The app integrates with Takeaway.com's APIs:

| API               | Purpose              | Authentication |
| ----------------- | -------------------- | -------------- |
| Partner Hub       | OAuth2 token refresh | Refresh token  |
| Restaurant Portal | Historical orders    | Access token   |
| Live Orders API   | Real-time orders     | Access token   |

## 🛡️ Configuration

**Environment Variables (.env):**
```bash
TAKEAWAY_REFRESH_TOKEN=your_refresh_token_here
APP_AUTH_COOKIE_SECRET=replace_with_a_long_random_secret
```

**Timezone (optional):**
Edit `streamlit_app/app.py` line 6:
```python
os.environ['TZ'] = 'Europe/Berlin'  # Change as needed
```

## 📦 Tech Stack

- **Frontend:** Streamlit 1.31.1 (Python-based UI)
- **Backend:** Pure Python module (no Flask, no server)
- **Token Management:** OAuth2 with Takeaway.com API
- **Data Processing:** pandas 2.1.3 for filtering/sorting
- **API Client:** requests 2.31.0 + cloudscraper 1.2.71
- **Environment:** Conda Python 3.11
- **Environment:** Conda (Python virtual environment)

## 🐛 Troubleshooting

**Port already in use?**
```bash
lsof -i :8501   # Streamlit app
kill -9 <PID>
```

**Token refresh fails?**
- Check `.env` file has valid `TAKEAWAY_REFRESH_TOKEN`
- Verify token is from Takeaway.com Partner Hub
- Ensure internet connection for API calls

**Import errors?**
- Ensure conda environment is activated: `conda activate takeawaybill`
- Check all packages installed: `conda list`

**App won't start?**
- Verify `.env` file exists and has refresh token
- Check Python version: `python --version` (should be 3.11)

## 📞 Support

For architecture questions, see `.github/copilot-instructions.md`  
For setup issues, see `SETUP.md` troubleshooting section
