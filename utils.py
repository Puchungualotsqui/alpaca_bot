import pandas_market_calendars as mcal
import datetime
from alpacaWrappers import *
import pytz
import os
import logging

# Suppress TensorFlow logs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
logging.getLogger('tensorflow').setLevel(logging.ERROR)

from preProcess import *
from alpaca.trading.client import TradingClient
from datetime import date, timedelta
import joblib
from tensorflow.keras.models import load_model
import tensorflow as tf

def today_opens() -> bool:
    nyse = mcal.get_calendar('NYSE')
    eastern = pytz.timezone("US/Eastern")
    today_et = datetime.now(eastern).date()

    valid_days = nyse.valid_days(start_date=today_et, end_date=today_et)
    return not valid_days.empty

def get_last_close(symbol: str, API_KEY: str, API_SECRET: str) -> float | None:
    end = date.today()
    start = end - timedelta(days=365)

    df = get_ohlcv(symbol, start, end, API_KEY, API_SECRET)
    if not df.empty:
        return float(df.iloc[-1]["c"])
    else:
        return None


def get_prediction(Ticker: str, API_KEY: str, SECRET_KEY: str) -> float:
    trading_client = TradingClient(API_KEY, SECRET_KEY)
    # Get our account information.
    account = trading_client.get_account()

    # Check if our account is restricted from trading.
    if account.trading_blocked:
        print('Account is currently restricted from trading.')

    today = date.today()
    years = 5
    one_year_ago = today - timedelta(days=(years * 365) + 1)

    df_spy = get_ohlcv(
        symbol=Ticker,
        start=one_year_ago,
        end=today,
        API_KEY=API_KEY, API_SECRET=SECRET_KEY
    )

    column_map = {
        "t": "Date",
        "o": "Open",
        "c": "Close",
        "h": "High",
        "l": "Low",
        "v": "Volume",
        "r": "Result"
    }
    df_spy = df_spy.rename(columns=column_map)
    df_spy = df_spy.drop(["n", "vw"], axis=1)

    df_spy = df_spy[['Date'] + [col for col in df_spy.columns if col != 'Date']]
    df_spy['Date'] = pd.to_datetime(df_spy['Date']).dt.date
    last_df_date = df_spy['Date'].iloc[-1]

    last_trading_day = get_last_trading_day(API_KEY, SECRET_KEY)

    if isinstance(last_trading_day, str):
        last_trading_day = datetime.strptime(last_trading_day, "%Y-%m-%d").date()

    if last_trading_day != last_df_date:
        raise ValueError(f"Date mismatch: expected {last_trading_day}, but got {last_df_date}")

    intervals = ["1d", "2d", "3d", "4d", "5d", "2w", "1M", "1y"]

    df_spy = add_past_updown_columns(df_spy, intervals)
    df_spy = add_continuous_columns(df_spy, intervals)
    df_spy = add_multi_RSI(df_spy)
    df_spy = add_multi_heikin_ashi_rsi(df_spy)
    df_spy = add_multi_macd(df_spy)
    df_spy = add_multi_bollinger(df_spy)
    df_spy = df_spy.dropna()
    df_spy = df_spy.drop(["HA_Close"], axis=1)

    cols_to_shift = ['Volume'] + [c for c in df_spy.columns if
                                  c.startswith("Continues") or c.startswith("RSI") or c.startswith(
                                      "Dist") or c.startswith("MACD") or c.startswith("BB")]
    df_spy = shift_columns(df_spy, cols_to_shift)

    scaler_path = f"./models/scaler_{Ticker}.pkl"
    if os.path.exists(scaler_path):
        scaler = joblib.load(scaler_path)
    else:
        scaler = joblib.load(f"./models/scaler.pkl")

    cols_to_scale = ['Volume'] + [c for c in df_spy.columns if
                                  c.startswith("Continues") or c.startswith("RSI") or c.startswith(
                                      "Dist") or c.startswith("MACD") or c.startswith("BB")]
    df_spy[cols_to_scale] = scaler.transform(df_spy[cols_to_scale])

    SEQ_LEN = 90
    feature_cols = [c for c in df_spy.columns if c not in ["Date", "Close", "High", "Low", "Open"]]
    X_pred = create_sequences_for_prediction(df_spy[feature_cols].values, seq_len=SEQ_LEN)

    @tf.keras.utils.register_keras_serializable()
    class ConservativeLoss(tf.keras.losses.Loss):
        def __init__(self, alpha=5, name="conservative_loss"):
            super().__init__(name=name)
            self.alpha = alpha

        def call(self, y_true, y_pred):
            error = y_pred - y_true
            over_penalty = tf.square(tf.maximum(error, 0.0)) * self.alpha
            under_penalty = tf.square(tf.minimum(error, 0.0))
            return tf.reduce_mean(over_penalty + under_penalty)

        def get_config(self):
            return {"alpha": self.alpha}

    model = load_model(f"./models/model_{Ticker}.keras", custom_objects={"ConservativeLoss": ConservativeLoss})
    pred = model.predict(X_pred[-1:], verbose=0)[0][0]
    pred_percentage = pred * 100

    return pred_percentage

def get_today_data(Ticker: str, API_KEY: str, SECRET_KEY: str) -> pd.DataFrame:
    eastern = pytz.timezone("US/Eastern")
    today = datetime.now(tz=eastern).date()
    df = get_ohlcv(Ticker,
                   start=today,
                   end=today + timedelta(days=1),
                   API_KEY=API_KEY,
                   API_SECRET=SECRET_KEY,
                   timeframe="1Min")
    return df

def get_today_open_price(ticker, API_KEY, SECRET_KEY):
    df_today = get_today_data(ticker, API_KEY, SECRET_KEY)

    df_today["t"] = pd.to_datetime(df_today["t"], utc=True)
    df_today["t"] = df_today["t"].dt.tz_convert("US/Eastern")

    eastern = pytz.timezone("US/Eastern")
    start_date = eastern.localize(datetime.combine(date.today(), datetime.min.time()))
    end_date = start_date + timedelta(days=1)

    df_today = df_today.loc[(df_today['t'] >= start_date) & (df_today['t'] <= end_date)]
    first_open = df_today["o"].iloc[0]
    return first_open