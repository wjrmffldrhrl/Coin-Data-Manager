from kafka import KafkaConsumer
from json import loads  # topic, broker list
import os

from coin_data_manager.models.candle import Candle
from coin_data_manager.repositories.candle import CandleRepository, AlreadyExistError
from config.config import CONFIG

if __name__ == "__main__":
    market = os.environ["MARKET"]
    env = os.environ["ENV"]
    topic = f"coin-bot.coin-data-manager.{env}.{market}"
    print(f"Consumer init : {topic}")

    database_config = CONFIG["database"]
    kafka_config = CONFIG["kafka"]

    database = database_config["database"]
    host = database_config["host"]
    port = database_config["port"]
    user = database_config["user"]
    password = database_config["password"]

    candle_repository = CandleRepository(database, host, port, user, password)
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=[f"{kafka_config['broker']['host']}:9092"],
        auto_offset_reset="earliest",  # latest, earliest
        # enable_auto_commit=True,
        # group_id="my-group",
        value_deserializer=lambda x: loads(x.decode("utf-8")),
        # consumer_timeout_ms=1000,
    )

    for message in consumer:
        print(f"Offset : {message.offset}")

        candle = Candle(
            market=message.value["market"],
            unit=message.value["unit"],
            _datetime=message.value["datetime"],
            open_price=message.value["open_price"],
            high_price=message.value["high_price"],
            low_price=message.value["low_price"],
            close_price=message.value["close_price"],
            acc_trade_price=message.value["acc_trade_price"],
            acc_trade_volume=message.value["acc_trade_volume"],
        )

        print(candle)
        try:
            candle_repository.add(candle)
        except AlreadyExistError as e:
            print("Already")
