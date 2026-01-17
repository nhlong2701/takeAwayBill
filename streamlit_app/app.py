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
import jwt

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
    st.error(
        "❌ Missing Takeaway.com refresh token. Please set TAKEAWAY_REFRESH_TOKEN in .env file"
    )
    st.stop()


class AuthManager:
    """Manage authentication tokens"""

    def __init__(self):
        self.session_key = "auth_tokens"
        self.api_token_key = "api_access_token"

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

    def get_api_token(self) -> Optional[str]:
        """Get stored API access token from session"""
        return st.session_state.get(self.api_token_key)

    def save_api_token(self, token: str):
        """Save API access token to session"""
        st.session_state[self.api_token_key] = token

    def clear_api_token(self):
        """Clear API token from session"""
        if self.api_token_key in st.session_state:
            del st.session_state[self.api_token_key]

    def is_api_token_expired(self, token: str) -> bool:
        """Check if API JWT token is expired"""
        if not token:
            return True
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            exp = decoded.get("exp")
            if exp:
                # Add 5-minute buffer
                return datetime.fromtimestamp(exp) < (
                    datetime.now() + timedelta(minutes=5)
                )
        except:
            return True
        return False

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

    def logout(self):
        """Logout user"""
        self.clear_tokens()


def ensure_authenticated():
    """Ensure user is authenticated"""
    auth = AuthManager()
    tokens = auth.get_tokens()
    return bool(tokens)


def login_page():
    """Render login page"""
    st.title("🍽️ takeAwayBill")
    st.subheader("Order Management System")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("---")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", use_container_width=True, type="primary"):
            auth = AuthManager()
            if auth.login(username, password):
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Login failed. Please try again.")


def orders_page():
    """Display historical orders"""
    st.header("📋 Historical Orders")

    col1, col2, col3 = st.columns(3)

    with col1:
        selected_date = st.date_input(
            "Select Date",
            value=datetime.now().date(),
            key="orders_date",
            format="DD-MM-YYYY",
        )

    with col2:
        sort_column = st.selectbox(
            "Sort by",
            ["createdAt", "orderCode", "postcode", "price"],
            key="sort_column",
        )

    with col3:
        sort_direction = st.selectbox(
            "Direction", ["asc", "desc"], key="sort_direction"
        )

    if st.button("Fetch Orders", key="fetch_orders"):
        try:
            auth = AuthManager()
            token = auth.get_api_token()
            with st.spinner("Fetching orders..."):
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

            total_orders = len(orders)
            online_paid = len([o for o in orders if o.get("paidOnline") == 1])
            online_revenue = sum(
                [o.get("price", 0) for o in orders if o.get("paidOnline") == 1]
            )
            cash_paid = len([o for o in orders if o.get("paidOnline") == 0])
            cash_revenue = sum(
                [o.get("price", 0) for o in orders if o.get("paidOnline") == 0]
            )

            with col1:
                st.metric("Total Orders", total_orders)
                st.metric("Total Revenue", f"€{online_revenue + cash_revenue:.2f}")

            with col2:
                st.metric("Total Orders Paid Online", online_paid)
                st.metric("Total Online Revenue", f"€{online_revenue:.2f}")

            with col3:
                st.metric("Total Orders Paid Cash", cash_paid)
                st.metric("Total Cash Revenue", f"€{cash_revenue:.2f}")

            # Display table
            st.subheader("Order Details")
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "createdAt": st.column_config.DatetimeColumn("Created At"),
                    "orderCode": "Order Code",
                    "postcode": "Postcode",
                    "price": st.column_config.NumberColumn("Price", format="€%.2f"),
                    "paidOnline": st.column_config.SelectboxColumn(
                        "Paid Online",
                        options=["Cash", "Online"],
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
            statuses = list(set([o.get("status") for o in orders]))
            tabs = st.tabs(
                [
                    f"{status.upper()} ({len([o for o in orders if o.get('status') == status])})"
                    for status in statuses
                ]
            )

            for tab, status in zip(tabs, statuses):
                with tab:
                    status_orders = [o for o in orders if o.get("status") == status]

                    for order in status_orders:
                        with st.container(border=True):
                            col1, col2, col3 = st.columns([2, 2, 1])

                            with col1:
                                st.write(f"**Order:** {order.get('orderCode')}")
                                st.write(
                                    f"**Customer:** {order.get('customer', {}).get('fullName')}"
                                )
                                st.write(
                                    f"**Address:** {order.get('customer', {}).get('street')} {order.get('customer', {}).get('street_number')}"
                                )

                            with col2:
                                st.write(f"**Placed:** {order.get('placedDate')}")
                                st.write(f"**Requested:** {order.get('requestedTime')}")
                                st.write(f"**Payment:** {order.get('paymentType')}")

                            with col3:
                                st.write(f"**Total:** €{order.get('customerTotal', 0)}")
                                st.write(f"**Status:** {status}")

                            # Products
                            if order.get("products"):
                                st.write("**Items:**")
                                for product in order.get("products"):
                                    st.write(
                                        f"  • {product.get('quantity')}x {product.get('name')} - €{product.get('totalAmount')}"
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
            orders_page()
        elif page == "🔴 Live Orders":
            live_orders_page()
        elif page == "⚙️ Settings":
            settings_page()
    else:
        login_page()


if __name__ == "__main__":
    main()
