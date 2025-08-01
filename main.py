from trade import *
from dotenv import load_dotenv
import os

if __name__ == '__main__':
    load_dotenv()
    API_KEY = os.getenv("ALPACA_API_KEY")
    SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

    print(get_prediction("SPY", API_KEY, SECRET_KEY))

