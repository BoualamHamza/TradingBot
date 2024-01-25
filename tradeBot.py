from datetime import datetime
# import the trader, brokers, backtesting class
from lumibot.traders import Trader
from lumibot.brokers import Alpaca
from lumibot.backtesting import YahooDataBacktesting
from lumibot.strategies.strategy import Strategy

# import configuration
from config import *


class MLstrategie(Strategy):
    param = {
        "symbol": "SPY",
        "quantity": 10,
        "side": "buy"
    }

    # when you strat the bot the initialize will run once
    def initialize(self, symbol: str = "", cash_at_risk: float = .5):
        self.sleeptime = "180M"
        self.last_trade = None
        self.cash_at_risk = cash_at_risk

    def position_sizing(self):
        cash = self.get_cash()
        last_price = self.get_last_price(self.param["symbol"])
        quantity = round(cash * self.cash_at_risk / last_price, 0)
        return cash, last_price, quantity

    # the on_trading_iteration method will run every time we get a new data
    def on_trading_iteration(self):
        cash, last_price, quantity = self.position_sizing()
        symbol = self.param["symbol"]
        side = self.param["side"]

        if cash > last_price:
            if self.last_trade == None:
                order = self.create_order(
                    symbol, quantity, side, type="bracket", take_profit_price=last_price*1.2, stop_loss_price=last_price*.95)
                self.submit_order(order)
                self.last_trade = "buy"


# -------------
trader = Trader()
broker = Alpaca(ALPACA_CONFIG)
startegy = MLstrategie(name='mlstart', broker=broker,
                       parameters={"symbol": "SPY",
                                   "cash_at_risk": .5})


# Backtest this strategy
backtesting_start = datetime(2023, 12, 15)
backtesting_end = datetime(2023, 12, 31)


startegy.backtest(
    YahooDataBacktesting,
    backtesting_start,
    backtesting_end,
    parameters={
        "symbol": "SPY",
        "cash_at_risk": .5
    },
)
