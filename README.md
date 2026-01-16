# takeAwayBill

Order management system for the Goldene Drachen restaurant. Aggregates orders from Takeaway.com's API and provides a dashboard for order tracking and payment management.

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
cd streamlit_app && streamlit run app.py
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
```

## 📁 Project Structure

```
takeAwayBill/
├── streamlit_app/
│   ├── app.py                       # Streamlit UI
│   ├── backend.py                   # API & token logic
│   └── .streamlit/config.toml       # Streamlit config
├── environment.yaml                 # Conda environment
├── .env.example                     # Environment template
├── Makefile                         # Dev commands
└── .github/copilot-instructions.md  # AI agent guide
```

## 🔑 Key Features

✅ **Login/Logout** — User authentication via Firestore  
✅ **Historical Orders** — View, filter, sort, and export orders by date  
✅ **Live Orders** — Real-time order dashboard with status tracking  
✅ **Analytics** — Order counts, payment methods, total revenue  
✅ **Token Management** — Automatic JWT refresh for Takeaway.com API  

## 📚 Documentation

- **[QUICK_START.md](QUICK_START.md)** — Detailed setup options
- **[SETUP.md](SETUP.md)** — Environment & dependency management
- **[.github/copilot-instructions.md](.github/copilot-instructions.md)** — Architecture & patterns for AI agents
- **[streamlit_app/README.md](streamlit_app/README.md)** — Frontend details

## 🔗 API Endpoints

All endpoints require `accessToken` header. Backend validates tokens with Takeaway.com API.

| Method | Endpoint               | Purpose                 |
| ------ | ---------------------- | ----------------------- |
| POST   | `/login`               | Authenticate user       |
| GET    | `/generate-new-tokens` | Refresh access token    |
| GET    | `/logout`              | Logout user             |
| POST   | `/getOrdersByDate`     | Fetch historical orders |
| GET    | `/getLiveOrders`       | Fetch active orders     |

## 🛡️ Configuration

Edit `streamlit_app/.streamlit/secrets.toml`:
```toml
backend_url = "http://localhost:5005"
testing_mode = false
```

Edit `backend/project/__init__.py` line 2 to change timezone:
```python
os.environ['TZ'] = 'Europe/Berlin'
```

## 📦 Tech Stack

- **Backend:** Flask 3.0.0, Python 3.11
- **Frontend:** Streamlit 1.31.1
- **Database:** Firebase Firestore (credentials storage only)
- **APIs:** Takeaway.com Partner Hub & Restaurant Portal
- **Environment:** Conda (Python virtual environment)

## 🐛 Troubleshooting

**Port already in use?**
```bash
lsof -i :5005   # Backend
lsof -i :8501   # Frontend
kill -9 <PID>
```

**Backend won't connect to Firebase?**
- Ensure `backend/project/key.json` exists and is valid
- Check Firestore has `collection/user` and `collection/token` documents

**Frontend can't reach backend?**
- Verify backend is running: `curl http://localhost:5005`
- Update `backend_url` in `streamlit_app/.streamlit/secrets.toml`

## 📞 Support

For architecture questions, see `.github/copilot-instructions.md`  
For setup issues, see `SETUP.md` troubleshooting section
