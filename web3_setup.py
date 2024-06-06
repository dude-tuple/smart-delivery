import json
from web3 import Web3
from config import Config

web3 = Web3(Web3.HTTPProvider(Config.GANACHE_URL))

with open('build/contracts/SmartDelivery.json') as f:
    contract_json = json.load(f)
contract_abi = contract_json['abi']
contract_address = contract_json['network']['5777']['address']
smart_delivery = web3.eth.contract(address=contract_address, abi=contract_abi)
