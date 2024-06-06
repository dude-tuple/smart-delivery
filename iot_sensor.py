import random
import time
from config import Config
from datetime import datetime


class Sensor:
    def __init__(self, delivery_id):
        self.delivery_id = delivery_id

    def read_temperature(self):
        return random.uniform(Config.MIN_TEMP, Config.MAX_TEMP)

    def read_humidity(self):
        return random.uniform(Config.MIN_HUM, Config.MAX_HUM)


class DeliveryProcessor:
    def __init__(self):
        self.data = []

    def aggregate_data(self, sensor_data):
        self.data.append(sensor_data)
        if len(self.data) > 0:
            avg_temp = sum(d['temperature'] for d in self.data) / len(self.data)
            avg_humidity = sum(d['humidity'] for d in self.data) / len(self.data)
            return avg_temp, avg_humidity
        return None, None


def simulate_sensor_readings(delivery_id):
    processor = DeliveryProcessor()
    sensor = Sensor(delivery_id)
    for _ in range(6):  # Simulate 6 sensor readings
        sensor_data = {
            'delivery_id': delivery_id,
            'temperature': sensor.read_temperature(),
            'humidity': sensor.read_humidity(),
            'timestamp': int(datetime.now().timestamp())
        }
        processor.aggregate_data(sensor_data)
        time.sleep(1)  # Simulate time passing between measurements

