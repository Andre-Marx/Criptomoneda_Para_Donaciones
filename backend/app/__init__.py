import os
#import time
import random
import requests
import socket
import threading
import time
import uuid

from flask import Flask, jsonify, request
from flask_cors import CORS

from backend.blockchain.block import Block
from backend.blockchain.blockchain import Blockchain
from backend.config import MINING_REWARD, P2P_MINING_DIFFICULTY, P2P_ROOT_HOST, P2P_ROOT_PORT, P2P_SOCKET_PORT
from backend.wallet.wallet import Wallet
from backend.wallet.transaction import Transaction
from backend.wallet.transaction_pool import TransactionPool
from backend.socket_network import SocketNetwork, get_lan_ip


# Nombre de la aplicación
app = Flask(__name__)
CORS(app, resources={r'/*': {'origins': '*'}})
blockchain = Blockchain()
wallet = Wallet(blockchain)
recipient_wallet = Wallet(blockchain)
transaction_pool = TransactionPool()
p2p_network = None
chain_lock = threading.Lock()
mining_lock = threading.Lock()
mining_stop_event = threading.Event()
root_network_status_lock = threading.Lock()
root_network_status_cache = {}
ROOT_NETWORK_STATUS_CACHE_TTL = 30
os.environ.setdefault('P2P_ALLOW_DIFFICULTY_JUMP', 'True')

NODE_ID = os.environ.get('NODE_ID', f'{socket.gethostname()}-{str(uuid.uuid4())[:6]}')
mining_state = {
    'status': 'idle',
    'is_mining': False,
    'nonce': 0,
    'hash': '-',
    'difficulty': P2P_MINING_DIFFICULTY,
    'winner': None,
    'winner_address': None,
    'message': 'Listo para competir.',
    'started_at': None,
    'finished_at': None,
    'active_miners': {}
}

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

def nonprofit_wallet_seed(index, organization):
    return f"hopecoin:nonprofit:{index}:{organization['name']}"


nonprofit_organization_wallets = [
    Wallet.from_seed(nonprofit_wallet_seed(index, organization), blockchain)
    for index, organization in enumerate(NONPROFIT_ORGANIZATION_DATA)
]

nonprofit_organizations = [
    {
        **organization,
        'address_wallet': organization_wallet.address
    }
    for organization, organization_wallet in zip(NONPROFIT_ORGANIZATION_DATA, nonprofit_organization_wallets)
]

nonprofit_wallet_by_address = {
    organization_wallet.address: organization_wallet
    for organization_wallet in nonprofit_organization_wallets
}


def get_p2p_mode():
    if os.environ.get('PEER') == 'True':
        return 'peer'

    return os.environ.get('P2P_MODE', 'server').lower()


def get_root_http_url():
    root_host = os.environ.get('ROOT_HTTP_HOST', os.environ.get('P2P_ROOT_HOST', 'localhost'))
    root_port = int(os.environ.get('ROOT_HTTP_PORT', ROOT_PORT))

    return f'http://{root_host}:{root_port}'


def get_root_network_status():
    if get_p2p_mode() != 'peer':
        return None

    with root_network_status_lock:
        cached_status = dict(root_network_status_cache)

    local_p2p_status = p2p_network.status() if p2p_network else {}
    cache_is_fresh = time.time() - cached_status.get('cached_at', 0) <= ROOT_NETWORK_STATUS_CACHE_TTL

    if cached_status and (local_p2p_status.get('connected') or cache_is_fresh):
        return cached_status

    if os.environ.get('P2P_ROOT_STATUS_HTTP_FALLBACK', 'False') != 'True':
        return None

    try:
        result = requests.get(f'{get_root_http_url()}/network/status', timeout=1.5)
        result.raise_for_status()
        root_status = result.json()
        cache_root_network_status(root_status)
        return root_status
    except Exception:
        return None


def get_network():
    global p2p_network

    if p2p_network is None:
        p2p_network = SocketNetwork(
            NODE_ID,
            on_message=handle_network_message,
            mode=get_p2p_mode(),
            host=os.environ.get('P2P_SOCKET_HOST', '0.0.0.0'),
            port=P2P_SOCKET_PORT,
            root_host=os.environ.get('P2P_ROOT_HOST', P2P_ROOT_HOST),
            root_port=int(os.environ.get('P2P_ROOT_PORT', P2P_ROOT_PORT))
        )
        p2p_network.start()

    return p2p_network


def is_root_node():
    return get_p2p_mode() == 'server'


def local_network_status_snapshot():
    network = get_network()

    return {
        **network.status(),
        'lan_ip': get_lan_ip(),
        'api_port': int(os.environ.get('PORT', PORT)),
        'node_id': NODE_ID
    }


def cache_root_network_status(root_status):
    if not root_status:
        return

    with root_network_status_lock:
        root_network_status_cache.clear()
        root_network_status_cache.update({
            **root_status,
            'cached_at': time.time()
        })


def network_state_payload():
    return {
        'type': 'SYNC_STATE',
        'authoritative': True,
        'node_id': NODE_ID,
        'chain': blockchain.to_json(),
        'transactions': transaction_pool.transaction_data(),
        'nonprofit_organizations': nonprofit_organizations,
        'network': local_network_status_snapshot(),
        'mining': mining_status_snapshot()
    }


def broadcast_sync_state():
    if not is_root_node():
        return

    get_network().broadcast(network_state_payload())


def parse_valid_transaction(transaction_json):
    transaction = Transaction.from_json(transaction_json)
    Transaction.is_valid_transaction(transaction)
    return transaction


def replace_transaction_pool(transactions_json):
    transactions = [
        parse_valid_transaction(transaction_json)
        for transaction_json in transactions_json
    ]

    transaction_pool.replace_transactions(transactions)
    transaction_pool.clear_blockchain_transactions(blockchain)


def apply_mining_snapshot(snapshot):
    if not snapshot:
        return

    with mining_lock:
        for miner_id, miner_state in snapshot.get('active_miners', {}).items():
            if miner_id == NODE_ID:
                continue

            mining_state['active_miners'][miner_id] = miner_state

    if snapshot.get('winner'):
        mark_mining_winner(
            snapshot.get('winner'),
            winner_address=snapshot.get('winner_address'),
            block_hash=snapshot.get('hash'),
            nonce=snapshot.get('nonce'),
            difficulty=snapshot.get('difficulty')
        )


def mark_mining_started(message):
    origin_node_id = message.get('origin_node_id') or message.get('node_id')

    if not origin_node_id or origin_node_id == NODE_ID:
        return

    with mining_lock:
        if not mining_state['is_mining'] and mining_state['status'] in ('idle', 'won', 'won_by_peer', 'stopped'):
            mining_state.update({
                'status': 'observing',
                'nonce': 0,
                'hash': '-',
                'difficulty': message.get('difficulty', P2P_MINING_DIFFICULTY),
                'winner': None,
                'winner_address': None,
                'message': 'Competencia de minado iniciada por otro nodo.',
                'started_at': time.time(),
                'finished_at': None,
                'active_miners': {}
            })

    update_peer_mining_state(message)


def update_peer_mining_state(message):
    origin_node_id = message.get('origin_node_id') or message.get('node_id')

    if not origin_node_id or origin_node_id == NODE_ID:
        return

    with mining_lock:
        mining_state['active_miners'][origin_node_id] = {
            'node_id': origin_node_id,
            'status': message.get('status', 'mining'),
            'nonce': message.get('nonce', 0),
            'hash': message.get('hash', '-'),
            'difficulty': message.get('difficulty', P2P_MINING_DIFFICULTY),
            'updated_at': time.time()
        }


def mark_mining_winner(winner_node_id, winner_address=None, block_hash=None, nonce=None, difficulty=None):
    global mining_stop_event

    if not winner_node_id:
        return

    mining_stop_event.set()

    with mining_lock:
        now = time.time()
        final_hash = block_hash or mining_state.get('hash', '-')
        final_nonce = nonce if nonce is not None else mining_state.get('nonce', 0)
        final_difficulty = difficulty or mining_state.get('difficulty', P2P_MINING_DIFFICULTY)

        for miner_id, miner_state in mining_state['active_miners'].items():
            if miner_id != winner_node_id and miner_state.get('status') == 'mining':
                miner_state['status'] = 'stopped'
                miner_state['updated_at'] = now

        mining_state.update({
            'status': 'won' if winner_node_id == NODE_ID else 'won_by_peer',
            'is_mining': False,
            'nonce': final_nonce,
            'hash': final_hash,
            'difficulty': final_difficulty,
            'winner': winner_node_id,
            'winner_address': winner_address,
            'message': f'{winner_node_id} gano la competencia de minado.',
            'finished_at': now
        })
        mining_state['active_miners'][winner_node_id] = {
            'node_id': winner_node_id,
            'status': 'winner',
            'nonce': final_nonce,
            'hash': final_hash,
            'difficulty': final_difficulty,
            'updated_at': now
        }


def accept_network_transaction(transaction_json):
    transaction = parse_valid_transaction(transaction_json)

    if transaction.id in transaction_pool.transaction_map:
        return False

    transaction_pool.set_transaction(transaction)
    return True


def accept_network_block(block_json, winner_node_id=None, winner_address=None):
    global mining_stop_event

    block = Block.from_json(block_json)

    with chain_lock:
        if block.hash in set(map(lambda chain_block: chain_block.hash, blockchain.chain)):
            mark_mining_winner(
                winner_node_id,
                winner_address=winner_address,
                block_hash=block.hash,
                nonce=block.nonce,
                difficulty=block.difficulty
            )
            return False

        if block.last_hash != blockchain.chain[-1].hash:
            return False

        Block.is_valid_block(blockchain.chain[-1], block)
        candidate_chain = blockchain.chain + [block]
        Blockchain.is_valid_transaction_chain(candidate_chain)
        blockchain.chain.append(block)
        transaction_pool.clear_blockchain_transactions(blockchain)

    mark_mining_winner(
        winner_node_id,
        winner_address=winner_address,
        block_hash=block.hash,
        nonce=block.nonce,
        difficulty=block.difficulty
    )
    return True


def accept_network_chain(chain_json, authoritative=False):
    if not chain_json:
        return False

    incoming_blockchain = Blockchain.from_json(chain_json)

    with chain_lock:
        has_same_tip = (
            len(incoming_blockchain.chain) == len(blockchain.chain)
            and incoming_blockchain.chain[-1].hash == blockchain.chain[-1].hash
        )

        if has_same_tip:
            return False

        if authoritative:
            if len(incoming_blockchain.chain) < len(blockchain.chain):
                return False

            Blockchain.is_valid_chain(incoming_blockchain.chain)
            blockchain.chain = incoming_blockchain.chain
        else:
            if len(incoming_blockchain.chain) <= len(blockchain.chain):
                return False

            blockchain.replace_chain(incoming_blockchain.chain)

        transaction_pool.clear_blockchain_transactions(blockchain)

    return True


def accept_network_state(message):
    authoritative = bool(message.get('authoritative'))

    cache_root_network_status(message.get('network'))
    accept_network_chain(message.get('chain', []), authoritative=authoritative)

    if authoritative:
        replace_transaction_pool(message.get('transactions', []))
    else:
        for transaction_json in message.get('transactions', []):
            accept_network_transaction(transaction_json)

    apply_mining_snapshot(message.get('mining'))


def handle_network_message(message, peer_id=None):
    message_type = message.get('type')

    if message.get('origin_node_id') == NODE_ID:
        return

    try:
        if message_type == 'TRANSACTION':
            if accept_network_transaction(message['transaction']) and is_root_node():
                broadcast_sync_state()
        elif message_type == 'MINING_STARTED':
            mark_mining_started(message)
        elif message_type == 'MINING_PROGRESS':
            update_peer_mining_state(message)
        elif message_type == 'BLOCK_MINED':
            accepted = accept_network_block(
                message['block'],
                winner_node_id=message.get('winner_node_id'),
                winner_address=message.get('winner_address')
            )

            if accepted and is_root_node():
                broadcast_sync_state()
        elif message_type == 'MINING_WINNER':
            mark_mining_winner(
                message.get('winner_node_id') or message.get('node_id') or message.get('origin_node_id'),
                winner_address=message.get('winner_address'),
                block_hash=message.get('hash'),
                nonce=message.get('nonce'),
                difficulty=message.get('difficulty')
            )
            if is_root_node():
                broadcast_sync_state()
        elif message_type == 'SYNC_REQUEST' and get_p2p_mode() == 'server':
            get_network().send_to_peer(peer_id, network_state_payload())
        elif message_type == 'SYNC_STATE':
            accept_network_state(message)
        elif message_type == 'PEERS_CHANGED' and is_root_node():
            broadcast_sync_state()
    except Exception as e:
        print(f'\n -- Mensaje P2P ignorado por error: {e}')


def broadcast_block(block, winner_node_id=None, winner_address=None):
    get_network().broadcast({
        'type': 'BLOCK_MINED',
        'block': block.to_json(),
        'winner_node_id': winner_node_id or NODE_ID,
        'winner_address': winner_address or wallet.address
    })


def broadcast_transaction(transaction):
    get_network().broadcast({
        'type': 'TRANSACTION',
        'transaction': transaction.to_json()
    })


def mining_status_snapshot():
    with mining_lock:
        return {
            **mining_state,
            'node_id': NODE_ID,
            'reward': MINING_REWARD
        }


def broadcast_mining_progress(status='mining'):
    snapshot = mining_status_snapshot()
    get_network().broadcast({
        'type': 'MINING_PROGRESS',
        'node_id': NODE_ID,
        'status': status,
        'nonce': snapshot['nonce'],
        'hash': snapshot['hash'],
        'difficulty': snapshot['difficulty']
    })


def mine_competition_block(transaction_data, last_block):
    global mining_stop_event
    last_broadcast_at = 0

    def on_progress(progress):
        nonlocal last_broadcast_at

        now = time.time()
        with mining_lock:
            mining_state.update({
                'nonce': progress['nonce'],
                'hash': progress['hash'],
                'difficulty': progress['difficulty'],
                'message': 'Probando nonces para encontrar un hash valido...'
            })
            mining_state['active_miners'][NODE_ID] = {
                'node_id': NODE_ID,
                'status': 'mining',
                'nonce': progress['nonce'],
                'hash': progress['hash'],
                'difficulty': progress['difficulty'],
                'updated_at': now
            }

        if now - last_broadcast_at >= 1:
            last_broadcast_at = now
            broadcast_mining_progress()

    block = Block.mine_block(
        last_block,
        transaction_data,
        difficulty=P2P_MINING_DIFFICULTY,
        progress_callback=on_progress,
        stop_event=mining_stop_event
    )

    if block is None:
        with mining_lock:
            mining_state.update({
                'status': 'stopped',
                'is_mining': False,
                'message': 'Minado detenido porque otro nodo publico el bloque.'
            })
        return

    with chain_lock:
        if blockchain.chain[-1].hash != last_block.hash:
            with mining_lock:
                mining_state.update({
                    'status': 'stopped',
                    'is_mining': False,
                    'message': 'Otro nodo publico un bloque antes.'
                })
            return

        blockchain.chain.append(block)
        transaction_pool.clear_blockchain_transactions(blockchain)

    with mining_lock:
        mining_state.update({
            'status': 'won',
            'is_mining': False,
            'nonce': block.nonce,
            'hash': block.hash,
            'difficulty': block.difficulty,
            'winner': NODE_ID,
            'winner_address': wallet.address,
            'message': f'{NODE_ID} gano la competencia de minado.',
            'finished_at': time.time()
        })
        mining_state['active_miners'][NODE_ID] = {
            'node_id': NODE_ID,
            'status': 'winner',
            'nonce': block.nonce,
            'hash': block.hash,
            'difficulty': block.difficulty,
            'updated_at': time.time()
        }

    broadcast_block(block, winner_node_id=NODE_ID, winner_address=wallet.address)
    get_network().broadcast({
        'type': 'MINING_WINNER',
        'winner_node_id': NODE_ID,
        'winner_address': wallet.address,
        'hash': block.hash,
        'nonce': block.nonce,
        'difficulty': block.difficulty
    })
    broadcast_sync_state()

@app.route('/')
def test():
    return 'Bienvenido a la blockchain'

@app.route('/health')
def route_health():
    return jsonify({
        'status': 'ok',
        'node_id': NODE_ID,
        'mode': get_p2p_mode(),
        'blockchain_length': len(blockchain.chain),
        'pending_transactions': len(transaction_pool.transaction_data())
    })

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
    global mining_stop_event

    transaction_data = transaction_pool.transaction_data()

    if len(transaction_data) == 0:
        return jsonify({'message': 'No hay transacciones pendientes para minar.'}), 400

    transaction_data.append(Transaction.reward_transaction(wallet).to_json())

    with mining_lock:
        if mining_state['is_mining']:
            already_mining = True
        else:
            already_mining = False

            mining_stop_event = threading.Event()
            mining_state.update({
                'status': 'mining',
                'is_mining': True,
                'nonce': 0,
                'hash': '-',
                'difficulty': P2P_MINING_DIFFICULTY,
                'winner': None,
                'winner_address': None,
                'message': 'Competencia de minado iniciada.',
                'started_at': time.time(),
                'finished_at': None,
                'active_miners': {}
            })
            mining_state['active_miners'][NODE_ID] = {
                'node_id': NODE_ID,
                'status': 'mining',
                'nonce': 0,
                'hash': '-',
                'difficulty': P2P_MINING_DIFFICULTY,
                'updated_at': time.time()
            }

    if already_mining:
        return jsonify(mining_status_snapshot()), 409

    get_network().broadcast({
        'type': 'MINING_STARTED',
        'node_id': NODE_ID,
        'status': 'mining',
        'nonce': 0,
        'hash': '-',
        'difficulty': P2P_MINING_DIFFICULTY
    })

    threading.Thread(
        target=mine_competition_block,
        args=(transaction_data, blockchain.chain[-1]),
        daemon=True
    ).start()

    return jsonify(mining_status_snapshot()), 202


@app.route('/mining/status')
def route_mining_status():
    return jsonify(mining_status_snapshot())


@app.route('/network/status')
def route_network_status():
    status = {
        **local_network_status_snapshot(),
        'mining': mining_status_snapshot()
    }
    root_status = get_root_network_status()

    if root_status:
        status.update({
            'peer_count': root_status.get('peer_count', status.get('peer_count', 0)),
            'peers': root_status.get('peers', status.get('peers', [])),
            'root_node_id': root_status.get('node_id'),
            'root_lan_ip': root_status.get('lan_ip'),
            'root_api_port': root_status.get('api_port')
        })

    return jsonify(status)

@app.route('/wallet/transact', methods=['POST'])
def route_wallet_transact():
    transaction_data = request.get_json()

    try:
        available_balance = transaction_pool.available_balance(blockchain, wallet.address)
        recipient = nonprofit_wallet_by_address.get(
            transaction_data['recipient'],
            transaction_data['recipient']
        )

        transaction = Transaction(
            wallet,
            recipient,
            transaction_data['amount'],
            sender_balance=available_balance
        )
        transaction_pool.set_transaction(transaction)
        broadcast_transaction(transaction)
        broadcast_sync_state()

        return jsonify(transaction.to_json())

    except Exception as e:
        return jsonify({'message': str(e)}), 400

@app.route('/wallet/transact_test', methods=['POST'])
def route_wallet_transact_test():
    transaction_data = request.get_json()
 
    try:
        available_balance = transaction_pool.available_balance(blockchain, wallet.address)
        transaction = Transaction(
            wallet,
            recipient_wallet,
            transaction_data['amount'],
            sender_balance=available_balance
        )
        transaction_pool.set_transaction(transaction)
        broadcast_transaction(transaction)
        broadcast_sync_state()

        return jsonify(transaction.to_json())

    except Exception as e:
        return jsonify({'message': str(e)}), 400

@app.route('/wallet/info')
def route_wallet_info():
    pending_balance = transaction_pool.available_balance(blockchain, wallet.address)

    return jsonify({
        'address': wallet.address,
        'balance': wallet.balance,
        'pending_balance': pending_balance,
        'pending_spend': wallet.balance - pending_balance
    })

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
PORT = int(os.environ.get('PORT', ROOT_PORT))


def sync_with_root_node():
    try:
        root_host = os.environ.get('ROOT_HTTP_HOST', os.environ.get('P2P_ROOT_HOST', 'localhost'))
        root_port = int(os.environ.get('ROOT_HTTP_PORT', ROOT_PORT))
        result = requests.get(f'http://{root_host}:{root_port}/blockchain', timeout=2)
        result.raise_for_status()
        #print(f'result.json(): {result.json()}')
        print(f'Cadena Actual: {result.json()}')

        accept_network_chain(result.json(), authoritative=True)

        transactions_result = requests.get(f'http://{root_host}:{root_port}/transactions', timeout=2)
        transactions_result.raise_for_status()
        replace_transaction_pool(transactions_result.json())
        print('\n -- Cadena local y mempool sincronizados con éxito')
    except Exception as e:
        #print(f'\n -- Error de sincronización: {e}')
        print('Bienvenido a la red')


def seed_data():
    for i in range(10):
        first_organization = nonprofit_organizations[i % len(nonprofit_organizations)]
        second_organization = nonprofit_organizations[(i + 1) % len(nonprofit_organizations)]

        blockchain.add_block([
            Transaction(
                Wallet(blockchain),
                nonprofit_wallet_by_address[first_organization['address_wallet']],
                random.randint(2,50)
            ).to_json(),
            Transaction(
                Wallet(blockchain),
                nonprofit_wallet_by_address[second_organization['address_wallet']],
                random.randint(2,50)
            ).to_json()
        ])

    for i in range(3):
        organization = nonprofit_organizations[i % len(nonprofit_organizations)]
        transaction_pool.set_transaction(Transaction(
            Wallet(blockchain),
            nonprofit_wallet_by_address[organization['address_wallet']],
            random.randint(2,50)
        ))


def main():
    port = PORT
    mode = get_p2p_mode()

    if mode == 'peer':
        if os.environ.get('PORT') is None:
            port = random.randint(5001, 6000)

        sync_with_root_node()

    os.environ['PORT'] = str(port)

    should_seed_root = (
        mode == 'server'
        and os.environ.get('AUTO_SEED_ROOT', 'True') == 'True'
    )

    if os.environ.get('SEED_DATA') == 'True' or should_seed_root:
        seed_data()

    get_network()

    app.run(host=os.environ.get('HOST', '0.0.0.0'), port=port, threaded=True)


if __name__ == '__main__':
    main()
