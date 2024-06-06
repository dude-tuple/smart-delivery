from flask import Blueprint, request, jsonify
from sqlalchemy import func

from models import db, Delivery, SensorData
from web3_setup import web3, smart_delivery
from config import Config

delivery_bp = Blueprint('delivery_bp', __name__)


@delivery_bp.route('/initializeDelivery', methods=['POST'])
def initialize_delivery():
    data = request.get_json()
    customer_address = Config.CUSTOMER_ADDRESS
    deliverer_address = Config.DELIVERER_ADDRESS
    provider_address = Config.PROVIDER_ADDRESS
    customer_private_key = Config.PRIVATE_KEY_CUSTOMER

    min_temp = data['minTemp']
    max_temp = data['maxTemp']
    min_humidity = data['minHumidity']
    max_humidity = data['maxHumidity']
    product_price = round(float(data['productPrice']), 2)
    delivery_price = round(float(data['deliveryPrice']), 2)
    delivery_id = data['deliveryId']

    # Add the new delivery to the database
    new_delivery = Delivery(
        deliveryId=delivery_id,
        status=Config.ACTIVE,
        min_temp=min_temp,
        max_temp=max_temp,
        min_humidity=min_humidity,
        max_humidity=max_humidity,
        contract_address=Config.CONTRACT_ADDRESS
    )
    db.session.add(new_delivery)
    db.session.commit()

    value_in_wei = web3.to_wei(product_price + delivery_price, 'ether')

    # Build the transaction
    transaction = smart_delivery.functions.startDelivery(
        provider_address,
        deliverer_address,
        int(min_temp) * 100,
        int(max_temp) * 100,
        int(min_humidity) * 100,
        int(max_humidity) * 100,
        web3.to_wei(product_price, 'ether'),
        web3.to_wei(delivery_price, 'ether'),
        delivery_id
    ).build_transaction({
        'from': customer_address,
        'nonce': web3.eth.get_transaction_count(customer_address),
        'value': value_in_wei,
        'gas': 2000000,
        'gasPrice': web3.to_wei('5', 'gwei')
    })

    # Sign the transaction
    signed_tx = web3.eth.account.sign_transaction(transaction, private_key=customer_private_key)

    # Send the transaction
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

    # Wait for the transaction receipt
    web3.eth.wait_for_transaction_receipt(tx_hash)

    return jsonify({"message": "Delivery started", "transaction_hash": tx_hash.hex()}), 201


@delivery_bp.route('/getDeliveries', methods=['GET'])
def get_deliveries():
    deliveries = Delivery.query.filter_by(is_hidden=False, contract_address=Config.CONTRACT_ADDRESS).all()
    results = []

    for delivery in deliveries:
        delivery_details = smart_delivery.functions.getDelivery(delivery.deliveryId).call()
        if delivery_details[0].startswith('0x000') and int(delivery_details[1], 16) == 0:
            db.session.delete(delivery)

        delivery_status = "draft" if delivery_details[11] else ("accepted" if delivery_details[10] else "rejected")
        avg_temp = db.session.query(func.avg(SensorData.temperature)).filter(
            SensorData.deliveryId == delivery.deliveryId).scalar()
        avg_humidity = db.session.query(func.avg(SensorData.humidity)).filter(
            SensorData.deliveryId == delivery.deliveryId).scalar()

        results.append({
            'deliveryId': delivery.deliveryId,
            'provider': delivery_details[0],
            'deliverer': delivery_details[1],
            'customer': delivery_details[2],
            'minTemp': delivery_details[3] / 100,
            'maxTemp': delivery_details[4] / 100,
            'minHumidity': delivery_details[5] / 100,
            'maxHumidity': delivery_details[6] / 100,
            'deliveryPrice': delivery_details[7] / 10**18,
            'productPrice': delivery_details[8] / 10**18,
            'endTime': delivery_details[9],
            'paymentReleased': delivery_details[10],
            'status': delivery_status,
            'avgTemp': avg_temp if avg_temp is not None else 0,
            'avgHumidity': avg_humidity if avg_humidity is not None else 0
        })

    db.session.commit()
    return jsonify(results), 200


@delivery_bp.route('/getActiveDeliveries', methods=['GET'])
def get_active_deliveries():
    active_deliveries = Delivery.query.filter_by(status=Config.ACTIVE, contract_address=Config.CONTRACT_ADDRESS).all()
    results = []

    for delivery in active_deliveries:
        delivery_details = smart_delivery.functions.getDelivery(delivery.deliveryId).call()
        if delivery_details[11]:  # Check if the delivery is active
            results.append({
                'deliveryId': delivery.deliveryId,
                'provider': delivery_details[0],
                'customer': delivery_details[1],
                'minTemp': delivery_details[2],
                'maxTemp': delivery_details[3],
                'minHumidity': delivery_details[4],
                'maxHumidity': delivery_details[5],
                'deposit': delivery_details[6],
                'endTime': delivery_details[7],
                'status': "active"
            })
    return jsonify(results), 200


@delivery_bp.route('/getSensorData/<delivery_id>', methods=['GET'])
def get_sensor_data(delivery_id):
    sensor_data = SensorData.query.filter_by(deliveryId=delivery_id).all()
    results = [
        {
            'temperature': data.temperature,
            'humidity': data.humidity,
            'time': f"time{index + 1}"
        } for index, data in enumerate(sensor_data)
    ]
    return jsonify(results), 200

