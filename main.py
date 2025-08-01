from preProcess import *
from wrappers import *
from alpaca.trading.client import TradingClient
from datetime import date, timedelta
import joblib
from tensorflow.keras.models import load_model
import tensorflow as tf
from dotenv import load_dotenv
import os

if __name__ == '__main__':
    API_KEY = os.getenv("ALPACA_API_KEY")
    SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

    trading_client = TradingClient(API_KEY, SECRET_KEY)
    # Get our account information.
    account = trading_client.get_account()

    # Check if our account is restricted from trading.
    if account.trading_blocked:
        print('Account is currently restricted from trading.')

    today = date.today()
    print(today)
    years = 5
    one_year_ago = today - timedelta(days=(years * 365) + 1)

    df_spy = get_ohlcv(
        symbol="SPY",
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

    scaler = joblib.load('scaler_s&p.pkl')
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


    model = load_model("s&p_high_gru_100days.keras", custom_objects={"ConservativeLoss": ConservativeLoss})
    pred = model.predict(X_pred[-1:])[0][0]

    print(pred)

