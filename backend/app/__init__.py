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
CORS(app, resources={
    r'/*': {
        'origins': [
            'http://localhost:3000',
            'http://127.0.0.1:3000',
            'http://localhost:3001',
            'http://127.0.0.1:3001'
        ]
    }
})
blockchain = Blockchain()
wallet = Wallet(blockchain)
recipient_wallet = Wallet(blockchain)
transaction_pool = TransactionPool()
pubsub = None

NONPROFIT_ORGANIZATION_DATA = [
    {
        'name': 'Estrellas Solidarias',
        'area': 'Educación',
        'mission': 'Iluminar el camino de la educación para niños desfavorecidos, brindándoles acceso a recursos educativos de calidad y oportunidades para un futuro brillante.'
    },
    {
        'name': 'Manos que Sanan',
        'area': 'Salud',
        'mission': 'Proporcionar atención médica y apoyo emocional a comunidades marginadas, promoviendo la salud integral y el bienestar.'
    },
    {
        'name': 'Planeta Verde',
        'area': 'Medio Ambiente',
        'mission': 'Preservar y restaurar la salud del planeta mediante la promoción de prácticas sostenibles, la conservación de la biodiversidad y la conciencia ambiental.'
    },
    {
        'name': 'Sonrisas para Todos',
        'area': 'Salud Mental',
        'mission': 'Abogar por la salud mental positiva, ofreciendo recursos y programas que fomenten el bienestar emocional y destigmatizando las enfermedades mentales.'
    },
    {
        'name': 'Arte Inclusivo',
        'area': 'Cultura y Arte',
        'mission': 'Facilitar el acceso a las artes para todas las comunidades, promoviendo la inclusión y la diversidad a través de programas artísticos y culturales.'
    },
    {
        'name': 'Hogar Esperanza',
        'area': 'Vivienda',
        'mission': 'Combatir la falta de vivienda proporcionando refugio, asistencia y recursos para ayudar a las personas a recuperar la estabilidad en sus vidas.'
    },
    {
        'name': 'Alas de Solidaridad',
        'area': 'Desarrollo Comunitario',
        'mission': 'Empoderar a comunidades marginadas mediante la implementación de proyectos de desarrollo sostenible que promuevan la autosuficiencia y la igualdad.'
    },
    {
        'name': 'Sabores del Cambio',
        'area': 'Seguridad Alimentaria',
        'mission': 'Luchar contra la hambruna y la malnutrición, brindando acceso a alimentos nutritivos y educación sobre prácticas agrícolas sostenibles.'
    },
    {
        'name': 'Notas de Esperanza',
        'area': 'Educación Musical',
        'mission': 'Facilitar el acceso a la educación musical para niños y jóvenes, fomentando la expresión creativa y el desarrollo de habilidades a través de la música.'
    },
    {
        'name': 'Construyendo Puentes',
        'area': 'Derechos Humanos',
        'mission': 'Defender y promover los derechos humanos, construyendo puentes de comprensión y tolerancia a través de la educación, la sensibilización y la promoción de la justicia social.'
    }
]

nonprofit_organizations = [
    {
        **organization,
        'address_wallet': Wallet(blockchain).address
    }
    for organization in NONPROFIT_ORGANIZATION_DATA
]


def get_pubsub():
    global pubsub

    if pubsub is None:
        pubsub = PubSub(blockchain, transaction_pool)

    return pubsub


def broadcast_block(block):
    try:
        get_pubsub().broadcast_block(block)
    except Exception as e:
        print(f'\n -- No se pudo transmitir el bloque por PubSub: {e}')


def broadcast_transaction(transaction):
    try:
        get_pubsub().broadcast_transaction(transaction)
    except Exception as e:
        print(f'\n -- No se pudo transmitir la transacción por PubSub: {e}')

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
    broadcast_block(block)

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
 
    transaction_pool.set_transaction(transaction)
    broadcast_transaction(transaction)
 
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
 
    transaction_pool.set_transaction(transaction)
    broadcast_transaction(transaction)
 
    return jsonify(transaction.to_json())

@app.route('/wallet/info')
def route_wallet_info():
    return jsonify({'address': wallet.address, 'balance':wallet.balance})

@app.route('/nonprofit-organizations')
def route_nonprofit_organizations():
    return jsonify(nonprofit_organizations)

@app.route('/known-addresses')
def route_knon_addresses():
    known_addresses = {
        wallet.address,
        recipient_wallet.address,
        *map(lambda organization: organization['address_wallet'], nonprofit_organizations)
    }
    non_address_output_keys = {
        'amount_received',
        'recipients_public_key',
        'recipients_signature',
        'sender_balance'
    }

    for block in blockchain.chain:
        for transaction in block.data:
            if transaction['input']['address'] != '*--recompensa-oficial-de-mineria--*':
                known_addresses.add(transaction['input']['address'])

            for output_key, output_value in transaction['output'].items():
                if output_key == 'recipients_address':
                    known_addresses.add(output_value)
                elif (
                    output_key not in non_address_output_keys
                    and output_key != '*--recompensa-oficial-de-mineria--*'
                ):
                    known_addresses.add(output_key)

    for transaction in transaction_pool.transaction_data():
        if transaction['input']['address'] != '*--recompensa-oficial-de-mineria--*':
            known_addresses.add(transaction['input']['address'])

        for output_key, output_value in transaction['output'].items():
            if output_key == 'recipients_address':
                known_addresses.add(output_value)
            elif (
                output_key not in non_address_output_keys
                and output_key != '*--recompensa-oficial-de-mineria--*'
            ):
                known_addresses.add(output_key)

    return jsonify(sorted(known_addresses))

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
        first_organization = nonprofit_organizations[i % len(nonprofit_organizations)]
        second_organization = nonprofit_organizations[(i + 1) % len(nonprofit_organizations)]

        blockchain.add_block([
            Transaction(Wallet(blockchain), first_organization['address_wallet'], random.randint(2,50)).to_json(),
            Transaction(Wallet(blockchain), second_organization['address_wallet'], random.randint(2,50)).to_json()
        ])

    for i in range(3):
        organization = nonprofit_organizations[i % len(nonprofit_organizations)]
        transaction_pool.set_transaction(Transaction(Wallet(blockchain), organization['address_wallet'], random.randint(2,50)))


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
