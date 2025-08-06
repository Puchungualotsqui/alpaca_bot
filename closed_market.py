from trade import *
from utils import *
from dotenv import load_dotenv
import json
import os



if __name__ == '__main__':

    if not today_opens():
        print('Today market does not open')
        exit()

    load_dotenv()
    API_KEY = os.getenv("ALPACA_API_KEY")
    SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

    print('Selling in open')
    responses = sell_in_open(API_KEY, SECRET_KEY)

    print('Getting predictions')
    predictions = {}
    with open("tickers.json") as f:
        config = json.load(f)

    for symbol, settings in config.items():
        prediction = get_prediction(symbol, API_KEY, SECRET_KEY)
        print(f"Prediction for {symbol}: {prediction}. Threshold: {settings['threshold']}")
        if prediction < settings["threshold"]:
            continue

        predictions[symbol] = prediction

    if len(predictions) == 0:
        print('No good predictions')
        exit()

    stock_of_day = max(predictions, key=predictions.get)
    with open("last_selection.json", "w") as f:
        json.dump({"symbol": stock_of_day, "change": float(predictions[stock_of_day])}, f)


    current_cash = float(get_cash(API_KEY, SECRET_KEY))
    print(f"Current cash: {current_cash}")
    last_stock_price = get_last_close(stock_of_day, API_KEY, SECRET_KEY)
    print(f"Last stock price: {last_stock_price}")
    stocks_to_buy = int(current_cash / last_stock_price)
    print(f'Buying {stocks_to_buy} of {stock_of_day}. Last close was: {last_stock_price}')
    response = submit_market_order(symbol=stock_of_day, quantity=stocks_to_buy, order_type=OrderSide.BUY,
                                   time_in_force=TimeInForce.OPG,
                                   API_KEY=API_KEY, SECRET_KEY=SECRET_KEY)
    print('Finishing script')