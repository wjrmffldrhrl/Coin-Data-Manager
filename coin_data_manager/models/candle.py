from datetime import datetime

from coin_data_manager.util import CandleUnit


class Candle:
    def __init__(
        self,
        market: str,
        unit: CandleUnit,
        _datetime: datetime,
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
        acc_trade_price: float,
        acc_trade_volume: float,
    ):
        self.market = market
        self.unit = unit
        self.datetime = _datetime
        self.open_price = open_price
        self.high_price = high_price
        self.low_price = low_price
        self.close_price = close_price
        self.acc_trade_price = acc_trade_price
        self.acc_trade_volume = acc_trade_volume

    def __hash__(self):
        return hash(self.market) ^ hash(self.unit) ^ hash(self.datetime)

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.market == other.market
            and self.unit == other.unit
            and self.datetime == other.datetime
        )

    def __lt__(self, other):
        return self.datetime < other.datetime

    def __repr__(self):
        return f"{self.market} {self.unit} {self.datetime} {self.close_price}"

    @staticmethod
    def from_response(response: dict, unit):
        try:
            market = response["market"]
            candle_date_time_utc = datetime.strptime(
                response["candle_date_time_utc"], "%Y-%m-%dT%H:%M:%S"
            )
            open_price = response["opening_price"]
            high_price = response["high_price"]
            low_price = response["low_price"]
            close_price = response["trade_price"]
            acc_trade_price = response["candle_acc_trade_price"]
            acc_trade_volume = response["candle_acc_trade_volume"]
        except Exception as e:
            print(response)
            raise e

        return Candle(
            market,
            unit,
            candle_date_time_utc,
            open_price,
            high_price,
            low_price,
            close_price,
            acc_trade_price,
            acc_trade_volume,
        )
