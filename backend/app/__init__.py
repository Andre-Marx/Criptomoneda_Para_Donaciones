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
pubsub = PubSub(blockchain, transaction_pool)

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
    pubsub.broadcast_block(block)

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
 
    pubsub.broadcast_transaction(transaction)
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
 
    pubsub.broadcast_transaction(transaction)
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

ROOT_PORT = 5000
PORT = ROOT_PORT

if os.environ.get('PEER') == 'True':
    PORT = random.randint(5001, 6000)
    result = requests.get(f'http://localhost:{ROOT_PORT}/blockchain')
    #print(f'result.json(): {result.json()}')
    print(f'Cadena Actual: {result.json()}')

    result_blockchain = Blockchain.from_json(result.json())

    try:
        blockchain.replace_chain(result_blockchain.chain)
        print('\n -- Cadena local sincronizada con éxito')
    except Exception as e:
        #print(f'\n -- Error de sincronización: {e}')
        print('Bienvenido a la red')

if os.environ.get('SEED_DATA') == 'True':
    for i in range(10):
        blockchain.add_block([
            Transaction(Wallet(blockchain), Wallet(blockchain), random.randint(2,50)).to_json(),
            Transaction(Wallet(blockchain), Wallet(blockchain), random.randint(2,50)).to_json()
        ])

    for i in range(3):
        transaction_pool.set_transaction(Transaction(Wallet(blockchain), Wallet(blockchain), random.randint(2,50)))


# Hacemos que se ejecute
app.run(port = PORT)