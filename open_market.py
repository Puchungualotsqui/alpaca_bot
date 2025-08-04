import json
from utils import *
from alpacaWrappers import *
from dotenv import load_dotenv


if __name__ == '__main__':
    if not today_opens():
        exit()

    load_dotenv()
    API_KEY = os.getenv("ALPACA_API_KEY")
    SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

    with open("last_selection.json", "r") as f:
        data = json.load(f)
        ticker = data["symbol"]
        predicted_change = data["change"]

    positions = get_positions(API_KEY, SECRET_KEY)
    if len(positions) == 0 or positions is None:
        exit()

    quantity = 0
    for position in positions:
        if position.symbol.lower() == ticker.lower():
            quantity = position.qty
            if quantity <= 0:
                raise ValueError("No stocks to sell")
            break

    open_price = get_today_open_price(ticker, API_KEY, SECRET_KEY)
    expected_high = ((100 + predicted_change) * open_price) / 100
    response = submit_limit_order(ticker, quantity, expected_high, OrderSide.SELL, TimeInForce.DAY, API_KEY, SECRET_KEY)