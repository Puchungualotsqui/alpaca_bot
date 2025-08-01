import pandas as pd
import requests
from datetime import date, timedelta


def get_ohlcv(symbol: str, start: date, end: date, API_KEY: str, API_SECRET: str) -> pd.DataFrame:
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
            "timeframe": "1Day",
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

def get_last_trading_day(api_key, api_secret):
    # Look back 10 calendar days to ensure we cover holidays/weekends
    start_date = (date.today() - timedelta(days=10)).isoformat()
    end_date = date.today().isoformat()

    url = f"https://paper-api.alpaca.markets/v2/calendar?start={start_date}&end={end_date}"
    headers = {
        "accept": "application/json",
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": api_secret
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Error fetching calendar: {response.status_code} - {response.text}")

    calendar = response.json()
    if not calendar:
        raise Exception("Empty trading calendar response")

    last_trading_day = calendar[-1]["date"]
    return last_trading_day

def get_column_name(column_map: dict[str, str], searched: str) -> str:
    col_name = column_map.get(searched, searched) if column_map else searched
    return col_name