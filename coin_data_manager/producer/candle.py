from datetime import datetime, timedelta
from kafka import KafkaProducer
from json import dumps
import time

from coin_data_manager.models.producer import Producer
from coin_data_manager.api.api_caller import UpbitApiCaller
from coin_data_manager.repositories.candle import CandleRepository
from coin_data_manager.repositories.producer import ProducerRepository
from coin_data_manager.util import TooManyRequestsError, CandleUnit


class CandleProducer:
    def __init__(
            self,
            market: str,
            unit: CandleUnit,
            broker_host: str,
            database_config: dict,
            env="dev",
    ):
        self.market = market
        self.unit = unit
        self.env = env
        self.topic = f"coin-bot.coin-data-manager.{env}.{market}"
        self.model = Producer(market, unit.value, datetime.utcnow())
        self.producer = KafkaProducer(
            acks=0,
            compression_type="gzip",
            bootstrap_servers=[f"{broker_host}:9092"],
            value_serializer=lambda x: dumps(x).encode("utf-8"),
        )

        self.producer_repository = ProducerRepository(**database_config)
        self.api_caller = UpbitApiCaller()

    def heartbeat(self):
        self.model.heartbeat = datetime.utcnow()
        self.producer_repository.update(self.model)

    def get_order(self):
        return self.producer_repository.get(self.model).order

    def produce(self):
        print(
            f"""
            Producer init
            Market : {self.market}
            Unit : {self.unit}
            Environment : {self.env}
            Topic : {self.topic}
        """
        )

        self.producer_repository.add(self.model)

        count = 0
        while True:
            order = self.get_order()
            if order == "SHUTDOWN":
                break

            try:
                candles = self.api_caller.get_candles(
                    f"{self.market}",
                    1,
                    self.unit,
                    to=datetime.utcnow().strftime("%Y-%m-%d %H:%M:00"),
                )

                candle = candles[0]
                print(candle.__dict__)
                response = self.producer.send(self.topic, value=candle.__dict__)
                print("response : ", response.get(3))
                self.producer.flush()

                time.sleep(50)
                count += 1
            except TooManyRequestsError as e:
                print(e)
                time.sleep(1)

            if count > 10:
                self.heartbeat()
                count = 0


class BackfillCandleProducer(CandleProducer):

    def __init__(
            self,
            market: str,
            unit: CandleUnit,
            broker_host: str,
            database_config: dict,
            env="dev",
    ):
        super().__init__(
            market=market,
            unit=unit,
            broker_host=broker_host,
            database_config=database_config,
            env=env,
        )

        self.candle_repository = CandleRepository(**database_config)

    def get_date_counts(self):
        return self.candle_repository.get_date_count(self.market)

    def produce(self):
        print(
            f"""
            Backfill producer init
            Market : {self.market}
            Unit : {self.unit}
            Environment : {self.env}
            Topic : {self.topic}
        """
        )

        candle_date_counts = self.get_date_counts()
        for candle_date, count in candle_date_counts:
            if count == 1440:
                continue

            start_datetime = datetime.strptime(f"{candle_date}", "%Y-%m-%d") + timedelta(minutes=200)
            for _ in range(8):
                try:
                    candles = self.api_caller.get_candles(
                        f"{self.market}",
                        200,
                        self.unit,
                        to=start_datetime.strftime("%Y-%m-%d %H:%M:00"),
                    )

                    for candle in candles:
                        print(candle.__dict__)
                        response = self.producer.send(self.topic, value=candle.__dict__)
                        print("response : ", response.get(3))

                    self.producer.flush()

                    start_datetime = start_datetime + timedelta(minutes=200)
                    time.sleep(0.3)
                except TooManyRequestsError as e:
                    print(e)
                    time.sleep(1)
