from app import app
from config import Config
from models import Delivery, db
from web3_setup import web3, smart_delivery


def clear_old_deliveries():
    nonce = web3.eth.get_transaction_count(Config.ADMIN_ADDRESS)
    txn_dict = smart_delivery.functions.clearOldDeliveries().build_transaction({
        'from': Config.ADMIN_ADDRESS,
        'gas': 2000000,
        'gasPrice': web3.to_wei('1', 'gwei'),
        'nonce': nonce,
    })

    signed_txn = web3.eth.account.sign_transaction(txn_dict, private_key=Config.PRIVATE_KEY_ADMIN)
    tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)

    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    print(f'Transaction receipt: {receipt}')

    event_filter = smart_delivery.events.DeliveryCleared().create_filter(fromBlock=receipt['blockNumber'])
    events = event_filter.get_all_entries()

    deleted_ids = [event['args']['deliveryId'] for event in events]

    with app.app_context():
        # Delete corresponding entries from the database
        for delivery_id in deleted_ids:
            delivery = Delivery.query.filter_by(deliveryId=delivery_id).first()
            if delivery:
                delivery.is_hidden = True

        db.session.commit()
