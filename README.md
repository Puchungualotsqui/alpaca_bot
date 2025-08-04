# Alpaca GRU Deployment Bot

This project automates a **daily stock trading strategy** using **GRU-predicted highs** and **Alpaca API**.  
It fetches historical stock data, predicts the next day's high, and places buy/sell orders on the **market open** and **target price**.

---

## How It Works

1. **Before Market Open (`closed_market.py`)**:
   - Closes all current positions.
   - Predicts next-day high return for a list of tickers.
   - Selects the most promising ticker (highest predicted return over threshold).
   - Buys that stock using available cash at market open (`OPG` order).

2. **After Market Open (`open_market.py`)**:
   - Places a **limit sell order** at the predicted high.

---

## Project Structure

| File                | Purpose                                        |
|---------------------|------------------------------------------------|
| `closed_market.py`  | Executes before market opens (buy logic)      |
| `open_market.py`    | Executes after market opens (sell logic)      |
| `trade.py`          | Closes all current positions                  |
| `utils.py`          | Prediction logic + Alpaca helpers             |
| `alpacaWrappers.py` | Order, data, and account wrappers for Alpaca  |
| `tickers.json`      | List of tickers and threshold values          |
| `models/`           | Contains saved models and scalers             |

---

## Environment Variables

Create a `.env` file in your root directory:

```env
ALPACA_API_KEY=your_api_key
ALPACA_SECRET_KEY=your_secret_key
```

You can use Alpaca's paper trading credentials for testing.

## Setup

```
pip install -r requirements.txt
```

Packages:
```
alpaca-trade-api
pandas
pandas_market_calendars
python-dotenv
tensorflow
joblib
```

## Model Predictions
Each stock in tickers.json must have:
```
{
  "SPY": {
    "threshold": 0.85
  },
  "QQQ": {
    "threshold": 0.90
  }
}
```
- Models should be saved as: ./models/model_{TICKER}.keras
- Scalers as: ./models/scaler_{TICKER}.pkl or fallback to scaler.pkl
## Trading Logic
- Buy: Submits MarketOrder with TimeInForce.OPG at open.
- Sell: Submits LimitOrder with TimeInForce.DAY at predicted high price.

## Notes
- Uses IEX feed for historical data.
- Automatically validates trading calendar (NYSE).
- Logs last selected stock in last_selection.json.

## License

This project is licensed under the  
**Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)**

You may view the source, but you may not modify, redistribute, or use it commercially.

© 2025 Otero Ediciones  
[Read full license](https://creativecommons.org/licenses/by-nc-nd/4.0/)