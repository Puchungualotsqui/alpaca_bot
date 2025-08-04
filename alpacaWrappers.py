import pandas as pd
import requests
from datetime import date, timedelta
from typing import Optional
import pytz
from datetime import datetime
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.models import Order

def get_ohlcv(symbol: str, start: date, end: date, API_KEY: str, API_SECRET: str, timeframe: Optional[str] = "1Day") -> pd.DataFrame:
    """
    Fetches historical OHLCV data from Alpaca's IEX feed for a given symbol and date range.

    Parameters:
        symbol (str): Stock ticker symbol (e.g., 'SPY')
        start (date): Start date (inclusive)
        end (date): End date (inclusive)
        API_KEY (str): Alpaca API key
        API_SECRET (str): Alpaca secret key
        timeframe (str): Timeframe (default is '1Day')

    Returns:
        pd.DataFrame: DataFrame containing OHLCV data
    """
    base_url = "https://data.alpaca.markets/v2/stocks/bars"
    headers = {
        "accept": "application/json",
        "APCA-API-KEY-ID": API_KEY,
        "APCA-API-SECRET-KEY": API_SECRET
    }

    all_bars = []
    next_page_token = None

    while True:
        params = {
            "symbols": symbol,
            "timeframe": timeframe,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "limit": 1000,
            "adjustment": "raw",
            "feed": "iex",
            "sort": "asc"
        }

        if next_page_token:
            params["page_token"] = next_page_token

        response = requests.get(base_url, headers=headers, params=params)

        if response.status_code != 200:
            raise Exception(f"Error fetching data: {response.status_code} - {response.text}")

        data = response.json()
        bars = data.get("bars", {}).get(symbol, [])

        all_bars.extend(bars)

        next_page_token = data.get("next_page_token")
        if not next_page_token:
            break  # All pages retrieved

    df = pd.DataFrame(all_bars)
    if not df.empty:
        df['t'] = pd.to_datetime(df['t'])
    return df



def get_last_trading_day(API_KEY: str, SECRET_KEY: str) -> pd.DataFrame:
    # Look back 10 calendar days to ensure we cover holidays/weekends
    start_date = (date.today() - timedelta(days=10)).isoformat()
    end_date = (date.today() - timedelta(days=1)).isoformat() #It should be executed the same day that the trades will be done

    url = f"https://paper-api.alpaca.markets/v2/calendar?start={start_date}&end={end_date}"
    headers = {
        "accept": "application/json",
        "APCA-API-KEY-ID": API_KEY,
        "APCA-API-SECRET-KEY": SECRET_KEY
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Error fetching calendar: {response.status_code} - {response.text}")

    calendar = response.json()
    if not calendar:
        raise Exception("Empty trading calendar response")

    last_trading_day = calendar[-1]["date"]
    return last_trading_day

def submit_market_order(symbol: str, quantity: float, order_type: OrderSide, time_in_force: TimeInForce, API_KEY: str,
                        SECRET_KEY: str, paper: bool = True) -> Optional[Order]:
    trading_client = TradingClient(API_KEY, SECRET_KEY, paper=paper)

    try:
        market_order = MarketOrderRequest(
            symbol=symbol,
            qty=quantity,
            side=order_type,
            time_in_force=time_in_force,
        )
        response = trading_client.submit_order(market_order)
        print(f"Market Order submitted: {response.id}")
        return response
    except Exception as e:
        print(f"Error submitting order: {e}")
        return None

def submit_limit_order(symbol: str, quantity: float, limit_price: float, order_type: OrderSide,
                       time_in_force: TimeInForce, API_KEY: str, SECRET_KEY: str, paper: bool = True):
    trading_client = TradingClient(API_KEY, SECRET_KEY, paper=paper)

    try:
        limit_order_data = LimitOrderRequest(
            symbol=symbol,
            limit_price=limit_price,
            qty=quantity,
            side=order_type,
            time_in_force=time_in_force,
        )
        response = trading_client.submit_order(limit_order_data)
        print(f"Limit Order submitted: {response.id}")
        return response
    except Exception as e:
        print(f"Error submitting order: {e}")
        return None

def get_cash(API_KEY: str, SECRET_KEY: str):
    trading_client = TradingClient(API_KEY, SECRET_KEY)
    account = trading_client.get_account()
    return account.cash

def get_positions(API_KEY: str, SECRET_KEY: str):
    trading_client = TradingClient(API_KEY, SECRET_KEY)
    positions = trading_client.get_all_positions()
    return positions