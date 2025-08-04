from trade import *
from utils import *
from dotenv import load_dotenv
import os
import json

if __name__ == '__main__':

    if not today_opens():
        exit()

    load_dotenv()
    API_KEY = os.getenv("ALPACA_API_KEY")
    SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

    responses = sell_in_open(API_KEY, SECRET_KEY)

    predictions = {}
    with open("tickers.json") as f:
        config = json.load(f)

    for symbol, settings in config.items():
        prediction = get_prediction(symbol, API_KEY, SECRET_KEY)

        if prediction < settings["threshold"]:
            continue

        predictions[symbol] = prediction

    stock_of_day = max(predictions, key=predictions.get)
    with open("last_selection.json", "w") as f:
        json.dump({"symbol": stock_of_day, "change": predictions[stock_of_day]}, f)


    current_cash = get_cash(API_KEY, SECRET_KEY)
    last_stock_price = get_last_close(stock_of_day, API_KEY, SECRET_KEY)
    stocks_to_buy = round(current_cash / last_stock_price, 4)

    response = submit_market_order(symbol=stock_of_day, quantity=stocks_to_buy, order_type=OrderSide.BUY,
                                   time_in_force=TimeInForce.OPG,
                                   API_KEY=API_KEY, SECRET_KEY=SECRET_KEY)