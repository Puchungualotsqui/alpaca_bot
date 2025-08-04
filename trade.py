from alpacaWrappers import *

def sell_in_open(API_KEY: str, SECRET_KEY: str):
    positions = get_positions(API_KEY, SECRET_KEY)
    if len(positions) == 0 or positions is None:
        return []

    responses = []
    for position in positions:
        response = submit_market_order(symbol=position.symbol, quantity=position.qty, order_type=OrderSide.SELL,
                                       time_in_force=TimeInForce.OPG,
                                       API_KEY=API_KEY, SECRET_KEY=SECRET_KEY)
        responses.append(response)
    return responses