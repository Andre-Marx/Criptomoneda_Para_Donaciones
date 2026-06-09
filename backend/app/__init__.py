import os
#import time
import random
import requests

from flask import Flask, jsonify, request
from flask_cors import CORS

from backend.blockchain.blockchain import Blockchain
from backend.wallet.wallet import Wallet
from backend.wallet.transaction import Transaction
from backend.wallet.transaction_pool import TransactionPool
from backend.pubsub import PubSub


# Nombre de la aplicación
app = Flask(__name__)
CORS(app, resources = {r'/*':{'origins':'http://localhost:3000'}})
blockchain = Blockchain()
wallet = Wallet(blockchain)
recipient_wallet = Wallet(blockchain)
transaction_pool = TransactionPool()
pubsub = None


def get_pubsub():
    global pubsub

    if pubsub is None:
        pubsub = PubSub(blockchain, transaction_pool)

    return pubsub

@app.route('/')
def test():
    return 'Bienvenido a la blockchain'

@app.route('/blockchain')
def route_blockchain():
    return jsonify(blockchain.to_json())

@app.route('/blockchain/range')
def route_blockchain_range():
    # http://localhost:5000/blockchain/range?start=3&end=6
    start = int(request.args.get('start'))
    end = int(request.args.get('end'))

    return jsonify(blockchain.to_json()[::-1][start:end])

@app.route('/blockchain/length')
def route_blockchain_length():
    return jsonify(len(blockchain.chain))


@app.route('/blockchain/mine')
def route_blockchain_mine():
    transaction_data = transaction_pool.transaction_data()
    transaction_data.append(Transaction.reward_transaction(wallet).to_json())
    blockchain.add_block(transaction_data)
    block = blockchain.chain[-1]

    # Se transmite el bloque al resto de nodos
    get_pubsub().broadcast_block(block)

    transaction_pool.clear_blockchain_transactions(blockchain)

    return jsonify(block.to_json())

@app.route('/wallet/transact', methods=['POST'])
def route_wallet_transact():
    transaction_data = request.get_json()
    transaction = transaction_pool.existing_transaction(wallet.address)
 
    if transaction:
        transaction.update(
            wallet,
            transaction_data['recipient'],
            transaction_data['amount']
        )
    else:
        transaction = Transaction(
            wallet,
            transaction_data['recipient'],
            transaction_data['amount']
        )
 
    get_pubsub().broadcast_transaction(transaction)
    transaction_pool.set_transaction(transaction)
 
    return jsonify(transaction.to_json())

@app.route('/wallet/transact_test', methods=['POST'])
def route_wallet_transact_test():
    transaction_data = request.get_json()
    transaction = transaction_pool.existing_transaction(wallet.address)

    if transaction:
        transaction.update(
            wallet,
            transaction_data['recipient'],
            transaction_data['amount']
        )
    else:
        transaction = Transaction(
            wallet,
            recipient_wallet,
            transaction_data['amount']
        )
 
    get_pubsub().broadcast_transaction(transaction)
    transaction_pool.set_transaction(transaction)
 
    return jsonify(transaction.to_json())

@app.route('/wallet/info')
def route_wallet_info():
    return jsonify({'address': wallet.address, 'balance':wallet.balance})

@app.route('/known-addresses')
def route_knon_addresses():
    known_addresses = set()
    for block in blockchain.chain:
        for transaction in block.data:
            known_addresses.update({list(transaction['output'])[-1]})
    return jsonify(list(known_addresses))

@app.route('/transactions')
def route_transactions():
    return jsonify(transaction_pool.transaction_data())

@app.route('/transactions-test')
def route_transactions_test():
    for i in range(4):
        transaction_pool.set_transaction(Transaction(Wallet(blockchain), Wallet(blockchain), random.randint(50,500)))
        #time.sleep(5)

    return jsonify(transaction_pool.transaction_data())

ROOT_PORT = 5000
PORT = ROOT_PORT


def sync_with_root_node():
    try:
        result = requests.get(f'http://localhost:{ROOT_PORT}/blockchain')
        result.raise_for_status()
        #print(f'result.json(): {result.json()}')
        print(f'Cadena Actual: {result.json()}')

        result_blockchain = Blockchain.from_json(result.json())
        blockchain.replace_chain(result_blockchain.chain)
        print('\n -- Cadena local sincronizada con éxito')
    except Exception as e:
        #print(f'\n -- Error de sincronización: {e}')
        print('Bienvenido a la red')


def seed_data():
    for i in range(10):
        blockchain.add_block([
            Transaction(Wallet(blockchain), Wallet(blockchain), random.randint(2,50)).to_json(),
            Transaction(Wallet(blockchain), Wallet(blockchain), random.randint(2,50)).to_json()
        ])

    for i in range(3):
        transaction_pool.set_transaction(Transaction(Wallet(blockchain), Wallet(blockchain), random.randint(2,50)))


def main():
    port = PORT

    if os.environ.get('PEER') == 'True':
        port = random.randint(5001, 6000)
        sync_with_root_node()

    if os.environ.get('SEED_DATA') == 'True':
        seed_data()

    app.run(port=port)


if __name__ == '__main__':
    main()
