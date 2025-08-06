import json
from utils import *
from alpacaWrappers import *
from dotenv import load_dotenv


if __name__ == '__main__':
    if not today_opens():
        print('Today market does not open')
        exit()

    load_dotenv()
    API_KEY = os.getenv("ALPACA_API_KEY")
    SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

    print('Start filling selling limit orders')

    print('Loading beginning day data')
    try:
        with open("last_selection.json", "r") as f:
            data = json.load(f)
            ticker = data["symbol"]
            predicted_change = data["change"]

    except FileNotFoundError:
        print("Error: 'last_selection.json' not found.")
        ticker = None
        predicted_change = None

    except json.JSONDecodeError:
        print("Error: Failed to decode 'last_selection.json'. Please check the file format.")
        ticker = None
        predicted_change = None

    except KeyError as e:
        print(f"Error: Missing expected key in 'last_selection.json': {e}")
        ticker = None
        predicted_change = None

    print('Loading real current positions')
    positions = get_positions(API_KEY, SECRET_KEY)
    if len(positions) == 0 or positions is None:
        print('No positions to sell')
        exit()

    print('Get day trade data')
    quantity = 0
    for position in positions:
        if position.symbol.lower() == ticker.lower():
            quantity = int(position.qty)
            if quantity <= 0:
                raise ValueError("No stocks to sell")
            break

    print('Submit limit order')
    open_price = get_today_open_price(ticker, API_KEY, SECRET_KEY)
    expected_high = round(float(((100 + predicted_change) * open_price) / 100), 2)
    response = submit_limit_order(ticker, int(quantity), expected_high, OrderSide.SELL, TimeInForce.DAY, API_KEY, SECRET_KEY)

    print('Finishing script')