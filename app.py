from flask import Flask, request, jsonify
from hexbytes import HexBytes
from web3 import Web3
import json
import sqlite3
from flask_cors import CORS
import time
import random

MIN_TEMP = 1
MAX_TEMP = 4
MIN_HUM = 60
MAX_HUM = 80
ACTIVE = 'active'

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Replace these with your actual values from Ganache
PRIVATE_KEY_PROVIDER = '0xf5c3ba7f23a8899f6e076035bf7d3897335b59290754bf9d52b15433f8d64779'
PROVIDER_ADDRESS = '0xD4854f1633c468f5f06c44C636EE13fCbB49037d'
PRIVATE_KEY_DELIVERER = '0xYourPrivateKeyForDeliverer'
DELIVERER_ADDRESS = '0xYourDelivererAddress'
PRIVATE_KEY_CUSTOMER = '0x7cbdedd9b48f0cd64ec51d9b5c682875095603abf27e1e2c0b9661566552b965'
CUSTOMER_ADDRESS = '0x7de54331bD623e331C4303dd87D0656898FA37E9'
CONTRACT_ADDRESS = '0xbcAa75423d05e9c0501d077015F3Ab294adf8E44'

# SQLite setup
conn = sqlite3.connect('identifier.sqlite', check_same_thread=False)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS delivery (
        deliveryId TEXT,
        status TEXT,
        min_temp FLOAT,
        max_temp FLOAT,
        min_humidity FLOAT,
        max_humidity FLOAT
    )   
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS sensor_data (
        deliveryId TEXT,
        temperature REAL,
        humidity REAL,
        timestamp INTEGER
    )
''')
conn.commit()

# Web3 setup
web3 = Web3(Web3.HTTPProvider('http://localhost:7545'))
with open('build/contracts/SmartDelivery.json') as f:
    contract_json = json.load(f)
contract_abi = contract_json['abi']
smart_delivery = web3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)


@app.route('/initializeDelivery', methods=['POST'])
def initialize_delivery():
    data = request.get_json()
    customer_address = CUSTOMER_ADDRESS
    min_temp = data['minTemp']
    max_temp = data['maxTemp']
    min_humidity = data['minHumidity']
    max_humidity = data['maxHumidity']
    delivery_id = data['deliveryId']

    transaction = smart_delivery.functions.startDelivery(
        customer_address,
        int(min_temp)*100,
        int(max_temp)*100,
        int(min_humidity)*100,
        int(max_humidity)*100,
        delivery_id
    ).build_transaction({
        'from': PROVIDER_ADDRESS,
        'value': web3.to_wei(1, 'ether'),
        'nonce': web3.eth.get_transaction_count(PROVIDER_ADDRESS),
    })

    c = conn.cursor()
    c.execute(f'INSERT INTO delivery (deliveryId, status, min_temp, max_temp, min_humidity, max_humidity)'
              f' VALUES (?, ?, ?, ?, ?, ?)', (delivery_id, ACTIVE, min_temp, max_temp, min_humidity, max_humidity))
    conn.commit()
    signed_tx = web3.eth.account.sign_transaction(transaction, private_key=PRIVATE_KEY_PROVIDER)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    web3.eth.wait_for_transaction_receipt(tx_hash)
    return jsonify({"message": "Delivery started"}), 201


@app.route('/recordSensorData', methods=['POST'])
def record_sensor_data():
    data = request.get_json()
    sensor_data_record = (data['deliveryId'], data['temperature'], data['humidity'], data['timestamp'])
    c.execute('INSERT INTO sensor_data (deliveryId, temperature, humidity, timestamp) VALUES (?, ?, ?, ?)',
              sensor_data_record)
    conn.commit()
    return jsonify({"message": "Sensor data recorded"}), 201


@app.route('/completeDelivery', methods=['POST'])
def complete_delivery():
    data = request.get_json()
    delivery_id = data['deliveryId']
    end_time = int(data['endTime'])
    avg_temp = data['avgTemp']
    avg_humidity = data['avgHumidity']

    transaction = smart_delivery.functions.completeDelivery(delivery_id, end_time, avg_temp,
                                                            avg_humidity).build_transaction({
        'from': CUSTOMER_ADDRESS,
        'nonce': web3.eth.get_transaction_count(CUSTOMER_ADDRESS),
    })

    signed_txn = web3.eth.account.sign_transaction(transaction, private_key=PRIVATE_KEY_CUSTOMER)
    web3.eth.send_raw_transaction(signed_txn.rawTransaction)

    return jsonify({"message": "Delivery completed"}), 200


@app.route('/getDeliveries', methods=['GET'])
def get_deliveries():
    conn = sqlite3.connect('identifier.sqlite', check_same_thread=False)
    c = conn.cursor()
    c.execute('SELECT deliveryId FROM delivery')
    delivery_ids = [el[0] for el in c.fetchall()]

    deliveries = []
    for delivery_id in delivery_ids:
        delivery = smart_delivery.functions.getDelivery(delivery_id).call()
        delivery_status = "draft" if delivery[9] else ("accepted" if delivery[8] else "rejected")
        deliveries.append({
            'deliveryId': delivery_id,
            'provider': delivery[0],
            'customer': delivery[1],
            'minTemp': delivery[2],
            'maxTemp': delivery[3],
            'minHumidity': delivery[4],
            'maxHumidity': delivery[5],
            'deposit': delivery[6],
            'endTime': delivery[7],
            'status': delivery_status
        })

    return jsonify(deliveries), 200


@app.route('/getActiveDeliveries', methods=['GET'])
def get_active_deliveries():
    conn = sqlite3.connect('identifier.sqlite', check_same_thread=False)
    c = conn.cursor()
    c.execute('SELECT deliveryId FROM delivery WHERE status=?', (ACTIVE,))
    delivery_ids = [el[0] for el in c.fetchall()]

    deliveries = []
    for delivery_id in delivery_ids:
        delivery = smart_delivery.functions.getDelivery(delivery_id).call()
        if delivery[9]:  # Check if the delivery is active
            deliveries.append({
                'deliveryId': delivery_id,
                'provider': delivery[0],
                'customer': delivery[1],
                'minTemp': delivery[2],
                'maxTemp': delivery[3],
                'minHumidity': delivery[4],
                'maxHumidity': delivery[5],
                'deposit': delivery[6],
                'endTime': delivery[7],
                'status': "active"
            })
    return jsonify(deliveries), 200


@app.route('/simulateDelivery', methods=['POST'])
def simulate_delivery():
    data = request.get_json()
    delivery_id = data['deliveryId']
    end_time = data['endTime']

    conn = sqlite3.connect('identifier.sqlite', check_same_thread=False)
    c = conn.cursor()
    c.execute('SELECT * FROM delivery WHERE deliveryId=?', (delivery_id,))
    # Record sensor data
    avg_temperature = avg_humidity = 0
    for _ in range(6):
        timestamp = int(time.time())
        temp = random.uniform(MIN_TEMP, MAX_TEMP)
        humidity = random.uniform(MIN_HUM, MAX_HUM)
        avg_temperature += temp / 6
        avg_humidity += humidity / 6
        record = (delivery_id, temp, humidity, timestamp)
        c.execute('INSERT INTO sensor_data (deliveryId, temperature, humidity, timestamp) VALUES (?, ?, ?, ?)', record)
        conn.commit()
        # time.sleep(1)  # Simulate time passing

    # Complete the delivery
    transaction = smart_delivery.functions.completeDelivery(
        delivery_id,
        end_time,
        int(avg_temperature*100),
        int(avg_humidity*100)
    ).build_transaction({
        'from': CUSTOMER_ADDRESS,
        'nonce': web3.eth.get_transaction_count(CUSTOMER_ADDRESS),
    })

    signed_tx = web3.eth.account.sign_transaction(transaction, private_key=PRIVATE_KEY_CUSTOMER)
    web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return jsonify({"message": "Delivery simulation completed"}), 200


if __name__ == '__main__':
    app.run(port=3000)
