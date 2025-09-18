
from binance.client import Client
from binance.exceptions import BinanceAPIException
from typing import List, Dict, Any

def get_client(api_key: str, api_secret: str, testnet: bool=False) -> Client:
    client = Client(api_key, api_secret, testnet=testnet)
    return client

def cancel_all_open_orders(client: Client, symbol: str):
    try:
        client.futures_cancel_all_open_orders(symbol=symbol)
    except BinanceAPIException as e:
        # If there is no open order, ignore
        if 'code' in e.__dict__ and e.code in (-2011, -2013):
            return
        raise

def get_position_amt(client: Client, symbol: str) -> float:
    pos_info = client.futures_position_information(symbol=symbol)
    if not pos_info:
        return 0.0
    # positionAmt may be returned as string
    amt = float(pos_info[0].get('positionAmt', 0) or 0)
    return amt

def market_close_position(client: Client, symbol: str):
    amt = get_position_amt(client, symbol)
    if amt == 0:
        return False
    side = Client.SIDE_SELL if amt > 0 else Client.SIDE_BUY
    qty = abs(amt)
    client.futures_create_order(
        symbol=symbol,
        side=side,
        type=Client.ORDER_TYPE_MARKET,
        quantity=qty
    )
    return True

def close_positions_and_cancel_orders(client: Client, symbols: List[str]) -> Dict[str, Any]:
    result = {"closed": [], "cancelled": [], "errors": {}}
    for sym in symbols:
        # cancel open orders first to avoid rejection
        try:
            cancel_all_open_orders(client, sym)
            result["cancelled"].append(sym)
        except Exception as e:
            result["errors"][sym] = f"cancel_error: {e}"

        try:
            closed = market_close_position(client, sym)
            if closed:
                result["closed"].append(sym)
        except Exception as e:
            result["errors"][sym] = f"close_error: {e}"
    return result
