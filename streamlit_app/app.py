import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

os.environ["TZ"] = "Europe/Berlin"

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
from typing import Optional
import base64
import hashlib
import hmac
import json
import jwt

try:
    import extra_streamlit_components as stx
except ImportError:
    stx = None

# Import backend functions
from streamlit_app.backend import (
    TAKEAWAY_REFRESH_TOKEN,
    fetch_orders_by_date,
    fetch_live_orders,
    refresh_tokens,
)

# Page config
st.set_page_config(
    page_title="takeAwayBill - Order Management",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Verify refresh token is available
if not TAKEAWAY_REFRESH_TOKEN:
    st.error("❌ Missing refresh token. Please set TAKEAWAY_REFRESH_TOKEN in .env file")
    st.stop()


class AuthManager:
    """Manage authentication tokens"""

    def __init__(self):
        self.session_key = "auth_tokens"
        self.api_token_key = "api_access_token"
        self.api_token_exp_key = "api_access_token_exp"
        self.cookie_name = "takeawaybill_auth"
        self.cookie_secret = os.getenv("APP_AUTH_COOKIE_SECRET", "dev-secret")
        self._cookie_manager = None

    def _get_cookie_manager(self):
        if self._cookie_manager is None and stx is not None:
            self._cookie_manager = stx.CookieManager()
        return self._cookie_manager

    def _sign_cookie_payload(self, payload: str) -> str:
        signature = hmac.new(
            self.cookie_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def _encode_cookie_value(self, username: str, expires_at: float) -> str:
        payload = json.dumps({"username": username, "exp": expires_at}, separators=(",", ":"))
        payload_b64 = base64.urlsafe_b64encode(payload.encode("utf-8")).decode("utf-8")
        signature = self._sign_cookie_payload(payload_b64)
        return f"{payload_b64}.{signature}"

    def _decode_cookie_value(self, cookie_value: str) -> Optional[dict]:
        try:
            payload_b64, signature = cookie_value.split(".", 1)
            expected_signature = self._sign_cookie_payload(payload_b64)
            if not hmac.compare_digest(signature, expected_signature):
                return None

            payload_json = base64.urlsafe_b64decode(payload_b64.encode("utf-8")).decode("utf-8")
            payload = json.loads(payload_json)
            if payload.get("exp", 0) < datetime.now().timestamp():
                return None
            return payload
        except Exception:
            return None

    def get_tokens(self) -> dict:
        """Get stored user tokens from session"""
        return st.session_state.get(self.session_key, {})

    def save_tokens(self, access_token: str, refresh_token: str):
        """Save user tokens to session"""
        st.session_state[self.session_key] = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "saved_at": datetime.now().isoformat(),
        }

    def save_remembered_login(self, username: str, days: int = 7):
        """Persist a signed login marker in browser cookies."""
        cookie_manager = self._get_cookie_manager()
        if cookie_manager is None:
            return

        expires_at = datetime.now() + timedelta(days=days)
        cookie_manager.set(
            self.cookie_name,
            self._encode_cookie_value(username, expires_at.timestamp()),
            expires_at=expires_at,
        )

    def load_remembered_login(self) -> Optional[str]:
        """Load remembered username from cookies if signature and expiry are valid."""
        cookie_manager = self._get_cookie_manager()
        if cookie_manager is None:
            return None

        cookie_value = cookie_manager.get(self.cookie_name)
        if not cookie_value:
            return None

        payload = self._decode_cookie_value(cookie_value)
        if not payload:
            return None
        return payload.get("username")

    def clear_remembered_login(self):
        """Remove remembered login cookie."""
        cookie_manager = self._get_cookie_manager()
        if cookie_manager is None:
            return
        cookie_manager.delete(self.cookie_name)

    def get_api_token(self) -> Optional[str]:
        """Get stored API access token from session"""
        return st.session_state.get(self.api_token_key)

    def save_api_token(self, token: str):
        """Save API access token to session"""
        st.session_state[self.api_token_key] = token
        token_exp = self._decode_token_exp(token)
        st.session_state[self.api_token_exp_key] = token_exp

    def clear_api_token(self):
        """Clear API token from session"""
        if self.api_token_key in st.session_state:
            del st.session_state[self.api_token_key]
        if self.api_token_exp_key in st.session_state:
            del st.session_state[self.api_token_exp_key]

    def _decode_token_exp(self, token: str) -> Optional[float]:
        """Decode JWT expiry timestamp without verifying signature."""
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            exp = decoded.get("exp")
            return float(exp) if exp else None
        except Exception:
            return None

    def is_api_token_expired(self, token: str) -> bool:
        """Check if API JWT token is expired"""
        if not token:
            return True

        exp = st.session_state.get(self.api_token_exp_key)
        if exp is None:
            exp = self._decode_token_exp(token)

        if exp is None:
            return True

        # Add small buffer to avoid edge cases during long requests.
        return datetime.fromtimestamp(exp) < (datetime.now() + timedelta(minutes=1))

    def refresh_api_token(self) -> bool:
        """Refresh the API access token"""
        token = refresh_tokens()
        if token:
            self.save_api_token(token)
            return True
        return False

    def ensure_api_token(self) -> bool:
        """Ensure API token is available and valid, refresh if needed"""
        token = self.get_api_token()
        if not token or self.is_api_token_expired(token):
            return self.refresh_api_token()
        return True

    def clear_tokens(self):
        """Clear user tokens from session"""
        if self.session_key in st.session_state:
            del st.session_state[self.session_key]
        self.clear_api_token()

    def login(self, username: str, password: str) -> bool:
        """
        Authenticate user.

        For this app, we just store a simple token in session.
        In production, you might validate against a database.

        Args:
            username: Username
            password: Password

        Returns:
            True if login successful
        """
        # For demo: accept any credentials and store in session
        # In production, validate against Firestore or your user database
        if username and password:
            # Generate a simple JWT-like token for session management
            token_payload = {
                "username": username,
                "iat": datetime.now().timestamp(),
                "exp": (datetime.now() + timedelta(days=7)).timestamp(),
            }
            access_token = jwt.encode(token_payload, "secret", algorithm="HS256")
            self.save_tokens(access_token, "")
            return True
        return False

    def restore_session_from_cookie(self) -> bool:
        """Restore app login session from remembered cookie if available."""
        username = self.load_remembered_login()
        if not username:
            return False

        token_payload = {
            "username": username,
            "iat": datetime.now().timestamp(),
            "exp": (datetime.now() + timedelta(days=7)).timestamp(),
        }
        access_token = jwt.encode(token_payload, "secret", algorithm="HS256")
        self.save_tokens(access_token, "")
        return True

    def logout(self):
        """Logout user"""
        self.clear_tokens()
        self.clear_remembered_login()


def ensure_authenticated():
    """Ensure user is authenticated"""
    auth = AuthManager()
    tokens = auth.get_tokens()
    if tokens:
        return True
    return auth.restore_session_from_cookie()


def login_page():
    """Render login page"""
    st.title("🍽️ takeAwayBill")
    st.subheader("Order Management System")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("---")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        remember_me = st.checkbox("Remember me on this browser", value=True)

        if stx is None:
            st.caption(
                "Install `extra-streamlit-components` to enable persistent login cookies."
            )

        if st.button("Login", use_container_width=True, type="primary"):
            auth = AuthManager()
            if auth.login(username, password):
                if remember_me:
                    auth.save_remembered_login(username)
                else:
                    auth.clear_remembered_login()
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Login failed. Please try again.")


def historical_orders_page():
    """Display historical orders"""
    st.header("📋 Historische Aufträge")

    col1, col2, col3 = st.columns(3)

    with col1:
        selected_date = st.date_input(
            "Datum auswählen",
            value=datetime.now().date(),
            key="orders_date",
            format="DD-MM-YYYY",
        )

    with col2:
        sort_column = st.selectbox(
            "Sortieren",
            ["Datum", "Bestellcode", "Postleitzahl", "Betrag", "Zahlungsart"],
            key="sort_column",
        )

    with col3:
        sort_direction = st.selectbox("Richtung", ["asc", "desc"], key="sort_direction")

    if st.button("Bestellungen abrufen", key="fetch_orders"):
        try:
            auth = AuthManager()
            token = auth.get_api_token()
            with st.spinner("Bestellungen abrufen..."):
                orders = fetch_orders_by_date(
                    token,
                    selected_date.strftime("%Y-%m-%d"),
                    sort_column,
                    sort_direction,
                )
            st.session_state["orders_data"] = orders
        except Exception as e:
            st.error(f"Error fetching orders: {e}")

    # Display orders if available
    if "orders_data" in st.session_state:
        orders = st.session_state["orders_data"]

        if orders:
            df = pd.DataFrame(orders)

            # Display metrics
            col1, col2, col3 = st.columns(3)

            total_orders = len(df)
            total_revenue = df["Betrag"].sum()
            online_paid = len(df[df["Zahlungsart"] == "Online"].index)
            online_revenue = df[df["Zahlungsart"] == "Online"]["Betrag"].sum()
            cash_paid = len(df[df["Zahlungsart"] == "Cash"].index)
            cash_revenue = df[df["Zahlungsart"] == "Cash"]["Betrag"].sum()

            with col1:
                st.metric("Gesamtbestellungen", total_orders)
                st.metric("Gesamtumsatz", f"€{total_revenue:.2f}")

            with col2:
                st.metric("Online bezahlte Bestellungen", online_paid)
                st.metric("Online Umsatz", f"€{online_revenue:.2f}")

            with col3:
                st.metric("Bar bezahlte Bestellungen", cash_paid)
                st.metric("Bar Umsatz", f"€{cash_revenue:.2f}")

            # Display table
            st.subheader("Bestelltabelle")
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Datum": st.column_config.DatetimeColumn(
                        "Datum", format="DD-MM-YYYY HH:mm"
                    ),
                    "Bestellcode": "Bestellcode",
                    "Postleitzahl": "Postleitzahl",
                    "Betrag": st.column_config.NumberColumn("Betrag", format="€%.2f"),
                    "Zahlungsart": st.column_config.SelectboxColumn(
                        "Zahlungsart",
                        options=["Bar", "Online"],
                    ),
                },
            )

            # Download option
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download as CSV",
                data=csv,
                file_name=f"orders_{selected_date}.csv",
                mime="text/csv",
            )
        else:
            st.info("No orders found for the selected date.")


def live_orders_page():
    """Display live orders"""
    st.header("🔴 Live Orders")

    if st.button("Refresh Live Orders", key="refresh_live"):
        try:
            auth = AuthManager()
            token = auth.get_api_token()
            with st.spinner("Fetching live orders..."):
                orders = fetch_live_orders(token)

            # if API returns (orders_list, status_code)
            if isinstance(orders, tuple) and len(orders) >= 1:
                orders = orders[0]

            st.session_state["live_orders"] = orders
        except Exception as e:
            st.error(f"Error: {e}")

    # Auto-refresh with timer
    refresh_interval = st.slider(
        "Auto-refresh interval (seconds)",
        min_value=5,
        max_value=60,
        value=30,
        step=5,
        key="refresh_interval",
    )

    # Display live orders
    if "live_orders" in st.session_state:
        orders = st.session_state["live_orders"]

        if orders:
            st.metric("Active Orders", len(orders))

            # Display orders in tabs by status
            statuses = list(set([(o.get("status") or "unknown") for o in orders]))
            tabs = st.tabs(
                [
                    f"{status.upper()} ({len([o for o in orders if (o.get('status') or 'unknown') == status])})"
                    for status in statuses
                ]
            )

            for tab, status in zip(tabs, statuses):
                with tab:
                    status_orders = [
                        o for o in orders if (o.get("status") or "unknown") == status
                    ]

                    for order in status_orders:
                        with st.container(border=True):
                            col1, col2, col3 = st.columns([2, 2, 1])

                            customer = order.get("customer", {}) or {}

                            with col1:
                                st.write(f"**Order:** {order.get('orderCode')}")
                                st.write(f"**Customer:** {customer.get('fullName')}")

                                # ✅ MINIMAL FIX: streetNumber not street_number
                                st.write(
                                    f"**Address:** {customer.get('street') or ''} {customer.get('streetNumber') or ''}"
                                )

                            with col2:
                                st.write(
                                    f"**Placed:** {order.get('placedDate') or '—'}"
                                )
                                st.write(
                                    f"**Requested:** {order.get('requestedTime') or '—'}"
                                )
                                st.write(
                                    f"**Payment:** {order.get('paymentType') or '—'}"
                                )

                            with col3:
                                st.write(
                                    f"**Total:** €{order.get('customerTotal') or 0}"
                                )
                                st.write(f"**Status:** {status}")

                            # Products
                            if order.get("products"):
                                st.write("**Items:**")
                                for product in order.get("products"):
                                    st.write(
                                        f"  • {product.get('quantity', 0)}x {product.get('name', '—')} - €{product.get('totalAmount') or 0}"
                                    )
        else:
            st.info("No live orders at the moment.")


def settings_page():
    """Settings and logout"""
    st.header("⚙️ Settings")

    auth = AuthManager()
    tokens = auth.get_tokens()

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**Logged in at:** {tokens.get('saved_at', 'N/A')}")
        if st.button("Refresh API Tokens", use_container_width=True):
            auth = AuthManager()
            if auth.refresh_api_token():
                st.success("API tokens refreshed!")
                st.rerun()
            else:
                st.error("API token refresh failed")

    with col2:
        st.write(f"**Version:** 1.0.0")
        if st.button("Logout", use_container_width=True, type="secondary"):
            auth.logout()
            st.success("Logged out successfully!")
            time.sleep(1)
            st.rerun()


def main():
    """Main app logic"""

    # Initialize session state
    if "auth_tokens" not in st.session_state:
        st.session_state["auth_tokens"] = {}

    # Sidebar navigation
    if ensure_authenticated():
        auth = AuthManager()
        # Ensure API token is available
        if not auth.ensure_api_token():
            st.error("Failed to authenticate with Takeaway.com API")
            return

        st.sidebar.title("🍽️ takeAwayBill")

        page = st.sidebar.radio(
            "Navigation",
            ["📋 Orders", "🔴 Live Orders", "⚙️ Settings"],
            label_visibility="collapsed",
        )

        if page == "📋 Orders":
            historical_orders_page()
        elif page == "🔴 Live Orders":
            live_orders_page()
        elif page == "⚙️ Settings":
            settings_page()
    else:
        login_page()


if __name__ == "__main__":
    main()
