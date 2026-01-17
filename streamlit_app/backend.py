"""
takeAwayBill Backend Logic

Handles all API interactions with Takeaway.com, token management,
and order fetching. Separate from Streamlit UI.
"""

import os
from datetime import timedelta
from threading import Thread
from typing import List, Dict

import cloudscraper
import pandas as pd
import requests

# Load refresh token from environment
TAKEAWAY_REFRESH_TOKEN = os.getenv("TAKEAWAY_REFRESH_TOKEN")


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


def _fetch_orders_page(
    token: str, year: int, dayOfYear: int, page: int
) -> pd.DataFrame:
    """
    Fetch a single page of orders from Takeaway.com API.

    Args:
        token: OAuth access token for Takeaway.com API
        year: Year for the query
        dayOfYear: Day of year for the query (1-366)
        page: Page number to fetch

    Returns:
        DataFrame with order data from the specified page
    """
    try:
        result = requests.get(
            f"https://restaurant-portal-api.takeaway.com/api/restaurant/orders"
            f"?period_type=day&year={year}&number={dayOfYear}&page={page}",
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
            "https://partner-hub.justeattakeaway.com/auth/realms/restaurant/protocol/openid-connect/token",
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


def fetch_orders_by_date(
    access_token: str,
    date: str,
    sortColumn: str = "createdAt",
    sortDirection: str = "asc",
) -> List[dict]:
    """
    Fetch historical orders for a specific date.

    Args:
        access_token: OAuth access token for Takeaway.com API
        date: Date in format 'YYYY-MM-DD'
        sortColumn: Column to sort by (default: 'createdAt')
        sortDirection: 'asc' or 'desc' (default: 'asc')

    Returns:
        List of order dictionaries for the specified date

    Raises:
        Exception: If API call fails
    """

    tempDate = pd.to_datetime(date, format="%Y-%m-%d")
    dayOfYear = tempDate.dayofyear
    if tempDate.dayofweek == 6:
        tempDate = tempDate + timedelta(days=1)
    year = tempDate.date().year

    try:
        result = requests.get(
            f"https://restaurant-portal-api.takeaway.com/api/restaurant/orders"
            f"?period_type=day&year={year}&number={dayOfYear}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        totalPages = result.json().get("meta", {}).get("total_pages", 1)

        threads = []
        for page in range(1, totalPages + 1):
            thread = ThreadWithReturnValue(
                target=_fetch_orders_page,
                args=(access_token, year, dayOfYear, page),
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

        billsDf = pd.concat(dfs, ignore_index=True)
        billsDf["Total amount"] = billsDf["amount"].str.replace(",", ".").astype(float)
        billsDf["Paid online"] = billsDf["paid_online"].fillna(False)
        billsDf["Date"] = pd.to_datetime(billsDf["date"], format="%d-%m-%Y %H:%M:%S")

        billsDf = billsDf.loc[
            billsDf["Date"].dt.day == pd.to_datetime(date, format="%Y-%m-%d").day
        ]

        billsDf = billsDf.rename(
            columns={
                "Date": "createdAt",
                "code": "orderCode",
                "city": "postcode",
                "Total amount": "price",
                "Paid online": "paidOnline",
            }
        )

        billsDf["paidOnline"] = billsDf["paidOnline"].astype(int)
        billsDf = billsDf[["createdAt", "orderCode", "postcode", "price", "paidOnline"]]
        billsDf = billsDf.sort_values(by=sortColumn, ascending=(sortDirection == "asc"))

        print(f"Retrieved {len(billsDf)} orders for {date}")
        return billsDf.to_dict(orient="records")

    except Exception as e:
        print(f"Error fetching orders: {str(e)}")
        raise


def fetch_live_orders(access_token: str) -> List[dict]:
    """
    Fetch active/live orders from Takeaway.com.

    Args:
        access_token: OAuth access token for Takeaway.com API

    Returns:
        List of currently active orders with customer and product details

    Raises:
        Exception: If API call fails after retries
    """
    orders: List[dict] = []

    for attempt in range(10):
        try:
            scraper = cloudscraper.create_scraper()
            result = scraper.get(
                "https://live-orders-api.takeaway.com/api/orders",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            for order_data in result.json():
                order = {
                    "placedDate": order_data.get("placed_date"),
                    "requestedTime": order_data.get("requested_time"),
                    "paymentType": order_data.get("payment_type"),
                    "subtotal": order_data.get("subtotal"),
                    "restaurantTotal": order_data.get("restaurant_total"),
                    "customerTotal": order_data.get("customer_total"),
                    "orderCode": order_data.get("public_reference"),
                    "deliveryFee": order_data.get("delivery_fee"),
                    "customer": {
                        "fullName": order_data.get("customer", {}).get("full_name"),
                        "street": order_data.get("customer", {}).get("street"),
                        "streetNumber": order_data.get("customer", {}).get(
                            "street_number"
                        ),
                        "postcode": order_data.get("customer", {}).get("postcode"),
                        "city": order_data.get("customer", {}).get("city"),
                        "extra": (
                            order_data.get("customer", {}).get("extra", [None])[0] or ""
                        ),
                        "phoneNumber": order_data.get("customer", {}).get(
                            "phone_number"
                        ),
                    },
                    "products": [
                        {
                            "quantity": product.get("quantity"),
                            "name": product.get("name"),
                            "totalAmount": product.get("total_amount"),
                            "code": product.get("code"),
                            "specifications": [
                                {
                                    "name": spec.get("name"),
                                    "totalAmount": spec.get("total_amount"),
                                }
                                for spec in product.get("specifications", [])
                            ],
                        }
                        for product in order_data.get("products", [])
                    ],
                    "status": order_data.get("status"),
                }
                orders.append(order)

            orders.sort(key=lambda o: o.get("placedDate", ""), reverse=True)

            print(f"Retrieved {len(orders)} live orders")
            return orders

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt == 9:
                raise

    return []
