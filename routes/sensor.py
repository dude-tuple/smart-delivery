from flask import Blueprint, request, jsonify
from models import db, SensorData, Delivery
import random
import time
from web3_setup import web3, smart_delivery
from config import Config

sensor_bp = Blueprint('sensor_bp', __name__)


@sensor_bp.route('/simulateDelivery', methods=['POST'])
def simulate_delivery():
    customer_private_key = Config.PRIVATE_KEY_CUSTOMER
    customer_address = Config.CUSTOMER_ADDRESS
    data = request.get_json()
    delivery_id = data['deliveryId']
    end_time = data['endTime']

    avg_temperature = avg_humidity = 0
    for _ in range(6):
        timestamp = int(time.time())
        temp = random.uniform(Config.MIN_TEMP, Config.MAX_TEMP)
        humidity = random.uniform(Config.MIN_HUM, Config.MAX_HUM)
        avg_temperature += temp / 6
        avg_humidity += humidity / 6
        record = SensorData(deliveryId=delivery_id, temperature=temp, humidity=humidity, timestamp=timestamp)
        db.session.add(record)
        db.session.commit()
        # time.sleep(1)  # Simulate time passing

    transaction = smart_delivery.functions.completeDelivery(
        delivery_id,
        end_time,
        int(avg_temperature * 100),
        int(avg_humidity * 100)
    ).build_transaction({
        'from': customer_address,
        'nonce': web3.eth.get_transaction_count(customer_address),
        'gas': 2000000,
        'gasPrice': web3.to_wei('5', 'gwei')
    })

    signed_tx = web3.eth.account.sign_transaction(transaction, private_key=customer_private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    print(f'Transaction receipt: {receipt}')

    accepted_filter = smart_delivery.events.PaymentReleased().create_filter(fromBlock=receipt['blockNumber'])
    rejected_filter = smart_delivery.events.PaymentRefunded().create_filter(fromBlock=receipt['blockNumber'])

    delivery = Delivery.query.filter_by(deliveryId=delivery_id).first()
    if accepted_filter.get_all_entries() and delivery.deliveryId:
        delivery.status = Config.ACCEPTED
    elif rejected_filter.get_all_entries and delivery.deliveryId:
        delivery.status = Config.REJECTED

    db.session.commit()
    return jsonify({"message": "Delivery simulation completed"}), 200
