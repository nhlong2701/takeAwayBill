# Environment Setup

The app requires a `.env` file in the root directory with your Takeaway.com refresh token.

## Quick Setup

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` and add your refresh token:**
   ```bash
   TAKEAWAY_REFRESH_TOKEN=your_actual_refresh_token
   ```

3. **Get your refresh token from Takeaway.com Partner Hub:**
   - Login to: https://partner-hub.justeattakeaway.com
   - Navigate to API credentials/settings
   - Copy your refresh token
   - Paste it into `.env`

4. **On startup**, the app automatically exchanges the refresh token for an access token

## ⚠️ Important

- **Never commit `.env` to Git** — it's in `.gitignore`
- **Never share your refresh token** — it's a secret
- **Keep `.env.example` updated** with new variable names (without values)
- The access token is acquired automatically and stored in memory during the app session

## Variables

| Variable                 | Required | Description                                   |
| ------------------------ | -------- | --------------------------------------------- |
| `TAKEAWAY_REFRESH_TOKEN` | ✅ Yes    | Takeaway.com OAuth refresh token (only this!) |
| `TZ`                     | ❌ No     | Timezone (default: Europe/Berlin)             |

## How It Works

1. App starts and reads `TAKEAWAY_REFRESH_TOKEN` from `.env`
2. On first API call, app exchanges refresh token for access token via Takeaway.com
3. Access token is stored in memory and used for API requests
4. When access token expires, it's automatically refreshed using the refresh token
5. If Takeaway.com returns a new refresh token (token rotation), it's automatically updated

## Troubleshooting

**App won't start with token error:**
```
❌ Missing Takeaway.com refresh token. Please set TAKEAWAY_REFRESH_TOKEN in .env file
```

Solution:
- Check `.env` file exists in project root
- Verify `TAKEAWAY_REFRESH_TOKEN` is set and not empty
- No extra spaces around `=` sign
- Token should be a long string from Partner Hub

**Token refresh fails:**
```
Token refresh error: ...
```

Solution:
- Verify your refresh token is valid and not expired
- Check your internet connection
- Login to Partner Hub again to get a fresh token
- Ensure the token is from the correct API/account

**Backend starts but API calls fail:**
- Tokens may have expired → refresh via API or update in `.env`
- Check Takeaway.com account has active API access
