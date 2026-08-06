"""
takeAwayBill Backend Logic

Handles all API interactions with Takeaway.com, token management,
and order fetching. Separate from Streamlit UI.
"""

import os
from datetime import timedelta
from threading import Thread
from typing import Dict, List, Optional, Tuple

import cloudscraper
import pandas as pd
import requests
import warnings

# Load refresh token from environment
TAKEAWAY_REFRESH_TOKEN = os.getenv("TAKEAWAY_REFRESH_TOKEN")

TOKEN_URL = (
    "https://partner-hub.justeattakeaway.com/auth/realms/restaurant/"
    "protocol/openid-connect/token"
)
HISTORICAL_ORDERS_URL = (
    "https://restaurant-portal-api.takeaway.com/api/restaurant/orders"
)
LIVE_ORDERS_URL = "https://live-orders-api.takeaway.com/api/orders"
MAX_LIVE_ORDER_RETRIES = 10


class ThreadWithReturnValue(Thread):
    """Thread subclass that captures return value from target function."""

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None):
        """
        Initialize thread with return value capability.

        Args:
            group: Thread group (unused)
            target: Target function to run
            name: Thread name
            args: Arguments for target function
            kwargs: Keyword arguments for target function
        """
        if kwargs is None:
            kwargs = {}
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        """Execute target function and capture return value."""
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def join(self, *args) -> pd.DataFrame:
        """
        Wait for thread to complete and return result.

        Returns:
            DataFrame returned by target function
        """
        Thread.join(self, *args)
        return self._return


def refresh_tokens() -> str:
    """
    Refresh Takeaway.com OAuth access token using refresh token.

    This function exchanges the refresh token for a new access token
    from Takeaway.com's Partner Hub.

    Returns:
        The new access token if successful, None otherwise

    Raises:
        Exception: If token refresh fails
    """
    global TAKEAWAY_REFRESH_TOKEN

    print("Refreshing Takeaway.com access token...")
    scraper = cloudscraper.create_scraper()

    try:
        result = scraper.post(
            TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "client_id": "restaurant-portal",
                "refresh_token": TAKEAWAY_REFRESH_TOKEN,
            },
        )

        try:
            response: Dict = result.json()
        except Exception as json_err:
            print(
                f"Token refresh error: Failed to parse response as JSON - {str(json_err)}"
            )
            print(f"Response status: {result.status_code}")
            print(f"Response content (first 200 chars): {result.text[:200]}")
            return None

        # Check if response is a dict (not a list or string)
        if not isinstance(response, dict):
            print(
                f"Token refresh error: Expected dict response, got {type(response).__name__}"
            )
            return None

        if response.get("access_token"):
            access_token = response.get("access_token")

            # If refresh token rotated, update it
            if response.get("refresh_token"):
                TAKEAWAY_REFRESH_TOKEN = response.get("refresh_token")
                os.environ["TAKEAWAY_REFRESH_TOKEN"] = response.get("refresh_token")

            print("Access token refreshed successfully")
            return access_token

        # Handle error response from Takeaway.com
        error_msg = (
            response.get("error_description")
            or response.get("error")
            or "Unknown error"
        )
        raise Exception(f"Failed to refresh token: {error_msg}")
    except Exception as e:
        print(f"Token refresh error: {str(e)}")
        return None


############## FOR HISTORICAL ORDERS ##############


def _normalize_historical_orders(
    pages: List[pd.DataFrame],
    requested_date: pd.Timestamp,
    sort_column: str,
    sort_direction: str,
) -> pd.DataFrame:
    """Combine pages and shape them into the UI-friendly historical order format."""
    bills_df = pd.concat(pages, ignore_index=True)

    bills_df["Total amount"] = bills_df["amount"].str.replace(",", ".").astype(float)
    bills_df["Paid online"] = bills_df["paid_online"].fillna(False)
    bills_df["Date"] = pd.to_datetime(bills_df["date"], format="%d-%m-%Y %H:%M:%S")

    bills_df = bills_df.loc[bills_df["Date"].dt.day == requested_date.day]
    bills_df = bills_df.rename(
        columns={
            "Date": "createdAt",
            "code": "orderCode",
            "city": "postcode",
            "Total amount": "price",
            "Paid online": "paidOnline",
        }
    )
    bills_df["paidOnline"] = bills_df["paidOnline"].astype(int)
    bills_df["paidOnline"] = bills_df["paidOnline"].map({0: "Cash", 1: "Online"})
    bills_df = bills_df[["createdAt", "orderCode", "postcode", "price", "paidOnline"]]
    bills_df = bills_df.rename(
        columns={
            "createdAt": "Datum",
            "orderCode": "Bestellcode",
            "postcode": "Postleitzahl",
            "price": "Betrag",
            "paidOnline": "Zahlungsart",
        }
    )
    return bills_df.sort_values(by=sort_column, ascending=(sort_direction == "asc"))


def _fetch_orders_page(
    token: str, year: int, day_of_year: int, page: int
) -> pd.DataFrame:
    """
    Fetch a single page of orders from Takeaway.com API.

    Args:
        token: OAuth access token for Takeaway.com API
        year: Year for the query
        day_of_year: Day of year for the query (1-366)
        page: Page number to fetch

    Returns:
        DataFrame with order data from the specified page
    """
    try:
        result = requests.get(
            f"{HISTORICAL_ORDERS_URL}"
            f"?period_type=day&year={year}&number={day_of_year}&page={page}",
            headers={"Authorization": f"Bearer {token}"},
        )
        response_data = result.json()

        # Handle invalid response structure
        if not isinstance(response_data, dict):
            print(
                f"Error fetching page {page}: Invalid response format (expected dict, got {type(response_data).__name__})"
            )
            return None

        # Check for error response
        if response_data.get("error"):
            print(
                f"Error fetching page {page}: {response_data.get('error_description', response_data.get('error'))}"
            )
            return None

        return pd.DataFrame(response_data.get("data", {}).get("orders", []))
    except Exception as e:
        print(f"Error fetching page {page}: {str(e)}")
        return None


def fetch_orders_by_date(
    access_token: str,
    date: str,
    sort_column: str = "createdAt",
    sort_direction: str = "asc",
) -> List[dict]:
    """
    Fetch historical orders for a specific date.

    Args:
        access_token: OAuth access token for Takeaway.com API
        date: Date in format 'YYYY-MM-DD'
        sort_column: Column to sort by (default: 'createdAt')
        sort_direction: 'asc' or 'desc' (default: 'asc')

    Returns:
        List of order dictionaries for the specified date

    Raises:
        Exception: If API call fails
    """

    requested_date = pd.to_datetime(date, format="%Y-%m-%d")
    day_of_year = requested_date.dayofyear

    # API edge case: Sunday requests are handled by querying the next day.
    query_date = requested_date
    if requested_date.dayofweek == 6:
        query_date = requested_date + timedelta(days=1)
    year = query_date.date().year

    try:
        result = requests.get(
            f"{HISTORICAL_ORDERS_URL}"
            f"?period_type=day&year={year}&number={day_of_year}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        total_pages = result.json().get("meta", {}).get("total_pages", 1)

        # Fetch each page concurrently to reduce total wait time.
        threads = []
        for page in range(1, total_pages + 1):
            thread = ThreadWithReturnValue(
                target=_fetch_orders_page,
                args=(access_token, year, day_of_year, page),
            )
            threads.append(thread)
            thread.start()

        dfs = []
        for thread in threads:
            df = thread.join()
            if df is not None:
                dfs.append(df)

        if not dfs:
            return []

        bills_df = _normalize_historical_orders(
            pages=dfs,
            requested_date=requested_date,
            sort_column=sort_column,
            sort_direction=sort_direction,
        )

        print(f"Retrieved {len(bills_df)} orders for {date}")
        return bills_df.to_dict(orient="records")

    except Exception as e:
        print(f"Error fetching orders: {str(e)}")
        raise


############## FOR LIVE ORDERS ##############


def _map_live_order(order: dict) -> dict:
    """Map a live-order payload into the response schema used by the app."""
    customer = order.get("customer") or {}
    customer_extra = customer.get("extra") or []

    return {
        "placedDate": order.get("placed_date"),
        "requestedTime": order.get("requested_time"),
        "paymentType": order.get("payment_type"),
        "subtotal": order.get("subtotal"),
        "restaurantTotal": order.get("restaurant_total"),
        "customerTotal": order.get("customer_total"),
        "orderCode": order.get("public_reference"),
        "deliveryFree": order.get("delivery_fee"),
        "customer": {
            "fullName": customer.get("full_name"),
            "street": customer.get("street"),
            "streetNumber": customer.get("street_number"),
            "postcode": customer.get("postcode"),
            "city": customer.get("city"),
            "extra": customer_extra[0] if customer_extra else "",
            "phoneNumber": customer.get("phone_number"),
        },
        "products": [
            {
                "quantity": product.get("quantity"),
                "name": product.get("name"),
                "totalAmount": product.get("total_amount"),
                "code": product.get("code"),
                "specifications": [
                    {
                        "name": specification.get("name"),
                        "totalAmount": specification.get("total_amount"),
                    }
                    for specification in product.get("specifications")
                ],
            }
            for product in order.get("products")
        ],
        "status": order.get("status"),
    }


def fetch_live_orders(access_token: str) -> Tuple[List[dict], int]:
    """
    Fetch active/live orders from Takeaway.com.

    Args:
        access_token: OAuth access token for Takeaway.com API

    Returns:
        Tuple of (active orders list, HTTP-like status code)

    Raises:
        Exception: If API call fails after retries
    """
    orders: List[dict] = []
    is_failed = True

    # Retry a few times because this endpoint can be flaky.
    for i in range(MAX_LIVE_ORDER_RETRIES):
        try:
            scraper = cloudscraper.create_scraper()
            result = scraper.get(
                LIVE_ORDERS_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            is_failed = False
        except Exception:
            print(f"failed {i} times")

        if not is_failed:
            # Convert API payload keys to our internal field names.
            orders = [_map_live_order(order) for order in result.json()]
            break

    # Most recent orders first.
    orders = sorted(orders, key=lambda order: order.get("placedDate"), reverse=True)

    if is_failed:
        warnings.warn("Takeaway API call failed after retries", RuntimeWarning)
        return [], 200

    return orders, 200


if __name__ == "__main__":
    # Example usage
    token = refresh_tokens()
    if token:
        orders = fetch_live_orders(token)
        print(orders)
