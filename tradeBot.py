from datetime import datetime
# import the trader, brokers, backtesting class
from lumibot.traders import Trader
from lumibot.brokers import Alpaca
from lumibot.backtesting import YahooDataBacktesting
from lumibot.strategies.strategy import Strategy
from alpaca_trade_api import REST
from datetime import timedelta

# import configuration
from config import *
from finbert_utils import *


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
        self.api = REST(
            base_url=ALPACA_CONFIG["ENDPOINT"], key_id=ALPACA_CONFIG["API_KEY"], secret_key=ALPACA_CONFIG["API_SECRET"])

    def position_sizing(self):
        cash = self.get_cash()
        last_price = self.get_last_price(self.param["symbol"])
        quantity = round(cash * self.cash_at_risk / last_price, 0)
        return cash, last_price, quantity

    # gets the news of the last three days
    def get_dates(self):
        today = self.get_datetime()
        three_days_prior = today - timedelta(days=3)
        return today.strftime('%Y-%m-%d'), three_days_prior.strftime('%Y-%m-%d')

    def get_sentiment(self):
        today, three_days_earlier = self.get_dates()
        news = self.api.get_news(
            symbol=self.param["symbol"], start=three_days_earlier, end=today)
        news = [ev.__dict__["_raw"]["headline"] for ev in news]
        prob, sentiment = estimate_sentiment(news)
        return prob, sentiment

    # the on_trading_iteration method will run every time we get a new data

    def on_trading_iteration(self):
        cash, last_price, quantity = self.position_sizing()
        prob, sentiment = self.get_sentiment()
        print(prob, sentiment)

        symbol = self.param["symbol"]
        side = self.param["side"]

        if cash > last_price:
            if sentiment == 'positive' and prob > .999:
                if self.last_trade == "sell":
                    self.sell_all()
                order = self.create_order(
                    symbol, quantity, 'buy', type="bracket", take_profit_price=last_price*1.2, stop_loss_price=last_price*.95)
                self.submit_order(order)
                self.last_trade = "buy"
            elif sentiment == "negetive" and prob > .99:
                if self.last_trade == 'buy':
                    self.sell_all()
                order = self.create_order(
                    symbol, quantity, 'sell', type="bracket", take_profit_price=last_price*.8, stop_loss_price=last_price*1.05)
                self.submit_order(order)
                self.last_trade("buy")


# -------------
trader = Trader()
broker = Alpaca(ALPACA_CONFIG)
startegy = MLstrategie(name='mlstart', broker=broker,
                       parameters={"symbol": "SPY",
                                   "cash_at_risk": .5})

# Backtest this strategy
backtesting_start = datetime(2020, 1, 15)
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
