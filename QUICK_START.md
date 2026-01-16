# 🚀 Quick Start Guide

Get the app running in **3 simple steps**.

## 1. Create Conda Environment

```bash
conda env create -f environment.yaml
```

This installs Python 3.11 and all required packages (Streamlit, requests, cloudscraper, pandas, etc.).

## 2. Configure Credentials

```bash
cp .env.example .env
```

Edit `.env` and add your Takeaway.com **refresh token**:

```bash
TAKEAWAY_REFRESH_TOKEN=your_refresh_token_here
```

That's it! Access tokens are automatically acquired using the refresh token.

## 3. Run the App

```bash
conda activate takeawaybill
cd streamlit_app
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## Architecture

**Frontend:** `streamlit_app/app.py` – Streamlit UI (pages: Login, Orders, Live Orders, Settings)

**Backend:** `streamlit_app/backend.py` – Pure Python module for API calls & token management (no Streamlit dependencies)

**Token Management:** OAuth2 with automatic refresh using only the refresh token

---

## Troubleshooting

| Problem                    | Solution                                                          |
| -------------------------- | ----------------------------------------------------------------- |
| `conda: command not found` | Install Miniconda: https://docs.conda.io/en/latest/miniconda.html |
| Import errors              | Ensure environment is activated: `conda activate takeawaybill`    |
| Port 8501 in use           | `streamlit run app.py --server.port 8502`                         |
| Token refresh fails        | Check `.env` file has valid `TAKEAWAY_REFRESH_TOKEN`              |

---

## What's Next?

- Read **[SETUP.md](./SETUP.md)** for detailed configuration
- Check **[ENV_SETUP.md](./ENV_SETUP.md)** for OAuth2 workflow details
- See **[README.md](./README.md)** for full feature overview
